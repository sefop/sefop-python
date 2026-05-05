"""Core optimization orchestrator for the MIP cargo optimization model.

This module is the main entry point for solving a cargo-loading problem.
It builds a Pyomo ConcreteModel by assembling variables, constraints, and
objectives from the ``components`` sub-package, delegates the solve to a
pluggable solver technology (see ``solvers`` sub-package), and extracts
the solution into domain-level ``Recommendation`` objects.

Typical call chain:
    API request → preprocessing → **this module** → post-processing → response
"""

import logging
import os
from datetime import datetime

import pyomo.environ as pyo

from app.application.strategy.mip.optimization.components.constraint_client_implies_cargo import ConstraintClientImpliesCargo
from app.application.strategy.mip.optimization.components.constraint_forbid_cargo import ConstraintForbidCargo
from app.application.strategy.mip.optimization.components.constraint_limit_volume import ConstraintLimitVolume
from app.application.strategy.mip.optimization.components.constraint_limit_weight import ConstraintLimitWeight
from app.application.strategy.mip.optimization.components.objective_client_diversity import ObjectiveClientDiversity
from app.application.strategy.mip.optimization.components.objective_revenue import ObjectiveRevenue
from app.application.strategy.mip.optimization.components.variable_select_cargo import VariableSelectCargo
from app.application.strategy.mip.optimization.components.variable_select_client import VariableSelectClient
from app.application.strategy.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver
from app.application.strategy.mip.optimization.solvers.highs_solver import HighsSolver
from app.application.strategy.mip.optimization.solvers.xpress_solver import XpressSolver
from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData
from app.domain.cargo_request import CargoRequest
from app.domain.recommendation import Recommendation

logger = logging.getLogger(__name__)

# Threshold for interpreting binary decision-variable values returned by the
# solver. MIP solvers use floating-point arithmetic, so a variable meant to
# be 1 may come back as 0.9999 (or 0 as 0.0001). Values ≥ 0.5 are treated
# as "selected" (1); values < 0.5 are treated as "not selected" (0).
# Valid range: 0.0 – 1.0 (0.5 is the standard convention).
BINARY_THRESHOLD = 0.5

# Maps a solver name string (as used by Pyomo's SolverFactory) to the
# corresponding adapter class. The optimization code looks up this registry
# to decide which solver back-end to use at runtime.
# To add a new solver technology: create a class that extends
# BaseTechnologySolver, then add an entry here with its Pyomo solver name.
_SOLVER_REGISTRY: dict[str, type[BaseTechnologySolver]] = {
    "appsi_highs": HighsSolver,
    "xpress_direct": XpressSolver,
}


class Optimization:
    """Builds a Pyomo optimization model, solves it, and extracts a Recommendation.

    Subphase 1: Build the model (variables, constraints, objective).
    Subphase 2: Solve the model with the given technology.
    Subphase 3: Extract the recommendation
    """

    def __init__(
        self,
        solver_name: str = "appsi_highs",
        export_lp: bool = False,
        output_folder: str = "output",
    ) -> None:
        if solver_name not in _SOLVER_REGISTRY:
            raise ValueError(
                f"Unknown solver '{solver_name}'. Available: {list(_SOLVER_REGISTRY.keys())}"
            )
        self._technology_solver = _SOLVER_REGISTRY[solver_name]()
        self._export_lp = export_lp
        self._output_folder = output_folder

    def run(self, preprocessed_data: PreProcessedData) -> Recommendation | None:
        """Build model, solve, and extract recommendation."""
        # Subphase 1: Build model
        model = self._build_model(preprocessed_data)

        # Subphase 1.5: Export LP file (optional)
        if self._export_lp:
            self._write_lp(model)

        # Subphase 2: Solve model
        result = self._technology_solver.solve(model)
        status = str(result.solver.termination_condition)
        logger.info("MIP solver terminated with status: %s", status)
        if status not in ("optimal", "feasible"):
            logger.warning("No feasible solution found (status=%s)", status)
            return None

        # Subphase 3: Extract recommendation
        return self._extract_recommendation(model, preprocessed_data)

    def _write_lp(self, model: pyo.ConcreteModel) -> None:
        """Write the Pyomo model to an LP file in a timestamped folder."""
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        folder = os.path.join(self._output_folder, timestamp)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "model.lp")
        model.write(path, format="lp", io_options={"symbolic_solver_labels": True})
        logger.info("Exported LP model to %s", path)

    def _build_model(self, preprocessed_data: PreProcessedData) -> pyo.ConcreteModel:
        """Subphase 1: Build the complete Pyomo model."""
        model = pyo.ConcreteModel(name="CargoOptimization")

        # Variables
        VariableSelectCargo().add_to_model(model, preprocessed_data)
        VariableSelectClient().add_to_model(model, preprocessed_data)

        # Constraints
        ConstraintLimitWeight().add_to_model(model, preprocessed_data)
        ConstraintLimitVolume().add_to_model(model, preprocessed_data)
        ConstraintForbidCargo().add_to_model(model, preprocessed_data)
        ConstraintClientImpliesCargo().add_to_model(model, preprocessed_data)

        # Objective
        revenue_expr = ObjectiveRevenue().build_expression(model, preprocessed_data)
        diversity_expr = ObjectiveClientDiversity().build_expression(model)
        model.objective = pyo.Objective(
            expr=revenue_expr + diversity_expr,
            sense=pyo.maximize,
        )

        logger.info(
            "Built model: %d cargo items, %d clients",
            len(preprocessed_data.allowed_ids) + len(preprocessed_data.forbidden_ids),
            len(list(model.client_names)),
        )
        return model

    def _extract_recommendation(
        self, model: pyo.ConcreteModel, preprocessed_data: PreProcessedData
    ) -> Recommendation:
        """Convert Pyomo solution to a domain Recommendation."""
        cargo_map = preprocessed_data.cargo_map

        selected: list[CargoRequest] = []
        non_selected: list[CargoRequest] = []

        for cid in preprocessed_data.allowed_ids:
            value = pyo.value(model.select_cargo[cid])
            if value >= BINARY_THRESHOLD:
                selected.append(cargo_map[cid])
            else:
                non_selected.append(cargo_map[cid])

        for cid in preprocessed_data.forbidden_ids:
            non_selected.append(cargo_map[cid])

        logger.info(
            "Extracted recommendation: %d selected, %d non-selected",
            len(selected),
            len(non_selected),
        )
        return Recommendation(selected=selected, non_selected=non_selected)

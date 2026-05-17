"""Solver adapter that delegates to the HiGHS optimizer via highspy.

HiGHS is an open-source, high-performance solver for LP and MIP problems.
This adapter translates an OptimizationModel into the highspy Python API
directly — no Pyomo dependency. It is the only file in this project that
imports highspy.
"""

from __future__ import annotations

import logging

import highspy
import numpy as np

from optimization.strategy.mip.optimization.model_abstraction.model_solution import ModelSolution, SolutionStatus
from optimization.strategy.mip.optimization.model_abstraction.optimization_model import OptimizationModel
from optimization.strategy.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver

logger = logging.getLogger(__name__)

# Floating-point values returned by MIP solvers for binary/integer variables
# are not always exact (e.g. 0.9999 instead of 1). Values are rounded to the
# nearest integer when extracting the solution.
_FEASIBLE_STATUSES = {
    highspy.HighsModelStatus.kOptimal,
    highspy.HighsModelStatus.kObjectiveBound,
    highspy.HighsModelStatus.kObjectiveTarget,
    highspy.HighsModelStatus.kSolutionLimit,
}


class HighsSolver(BaseTechnologySolver):
    """Solver adapter for HiGHS using the highspy Python bindings.

    Translates the solver-agnostic ``OptimizationModel`` into HiGHS calls:
    variables → ``addVar`` / ``changeColIntegrality``,
    constraints → ``addRow``,
    objective → ``changeColCost`` / ``changeObjectiveSense``.
    """

    def solve(self, model: OptimizationModel) -> ModelSolution:
        """Translate and solve the model with HiGHS.

        Args:
            model: The solver-agnostic optimization model.

        Returns:
            ModelSolution with status and variable values, or None values
            if no feasible solution was found.
        """
        h = highspy.Highs()
        h.silent()

        # Map variable name → column index for building constraints
        col_index: dict[str, int] = {}

        # Step 1: add variables
        for i, var in enumerate(model.variables):
            ub = var.upper_bound if var.upper_bound is not None else highspy.kHighsInf
            h.addVar(var.lower_bound, ub)
            if var.var_type in ("integer", "binary"):
                h.changeColIntegrality(i, highspy.HighsVarType.kInteger)
            col_index[var.name] = i

        # Step 2: set objective coefficients
        for var_name, coeff in model.objective_expression.terms.items():
            h.changeColCost(col_index[var_name], coeff)

        if model.objective_sense == "maximize":
            h.changeObjectiveSense(highspy.ObjSense.kMaximize)
        else:
            h.changeObjectiveSense(highspy.ObjSense.kMinimize)

        # Step 3: add constraints
        for constraint in model.constraints:
            indices = [col_index[name] for name in constraint.lhs.terms]
            coeffs = list(constraint.lhs.terms.values())

            if constraint.sign == "<=":
                row_lb, row_ub = -highspy.kHighsInf, constraint.rhs
            elif constraint.sign == ">=":
                row_lb, row_ub = constraint.rhs, highspy.kHighsInf
            else:  # "="
                row_lb, row_ub = constraint.rhs, constraint.rhs

            h.addRow(row_lb, row_ub, len(indices), np.array(indices, dtype=np.int32), np.array(coeffs, dtype=np.float64))

        # Step 4: solve
        h.run()
        status = h.getModelStatus()
        logger.info("HiGHS terminated with status: %s", status)

        if status not in _FEASIBLE_STATUSES:
            if status == highspy.HighsModelStatus.kInfeasible:
                mapped_status = SolutionStatus.INFEASIBLE
            elif status in (highspy.HighsModelStatus.kUnbounded, highspy.HighsModelStatus.kUnboundedOrInfeasible):
                mapped_status = SolutionStatus.UNBOUNDED
            else:
                mapped_status = SolutionStatus.ERROR
            return ModelSolution(status=mapped_status, variable_values=None)

        sol = h.getSolution()
        values = {var.name: sol.col_value[i] for i, var in enumerate(model.variables)}
        return ModelSolution(status=SolutionStatus.OPTIMAL, variable_values=values)

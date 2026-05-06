"""Solver adapter placeholder for FICO Xpress.

This is a template showing how to add a new solver technology:
1. Create a subclass of BaseTechnologySolver.
2. Implement solve() using the solver's Python API.
3. Register it in the _SOLVER_REGISTRY dict in optimization.py.

TODO: implement using the xpress Python package.
"""

from __future__ import annotations

from application.strategy.mip.optimization.model_abstraction.model_solution import ModelSolution
from application.strategy.mip.optimization.model_abstraction.optimization_model import OptimizationModel
from application.strategy.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver


class XpressSolver(BaseTechnologySolver):
    """Solver adapter placeholder for FICO Xpress."""

    def solve(self, model: OptimizationModel) -> ModelSolution:
        raise NotImplementedError("XpressSolver is not yet implemented")

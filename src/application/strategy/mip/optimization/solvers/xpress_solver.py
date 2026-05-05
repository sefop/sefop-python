"""Solver adapter that delegates to FICO Xpress.

Xpress is a commercial LP/MIP solver. This module is provided as a
template showing how to add a new solver technology to the system — create
a subclass of ``BaseTechnologySolver`` and register it in the solver
registry in ``optimization.py``.
"""

from typing import Any

import pyomo.environ as pyo

from app.application.strategy.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver


class XpressSolver(BaseTechnologySolver):
    """Solver adapter for FICO Xpress.

    This is a placeholder to demonstrate how easy it is to add a new
    solver technology. Install the ``xpress`` Python package and
    configure Pyomo to use it.
    """

    def solve(self, model: pyo.ConcreteModel) -> Any:
        solver = pyo.SolverFactory("xpress_direct")
        return solver.solve(model, tee=True)

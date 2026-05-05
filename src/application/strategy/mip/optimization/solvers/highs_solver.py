"""Solver adapter that delegates to the HiGHS optimizer.

HiGHS is an open-source, high-performance solver for linear programming (LP)
and mixed-integer programming (MIP). This adapter uses Pyomo's APPSI
(Auto-Persistent Solver Interface), which keeps the solver in memory between
calls for better performance compared to the classic file-based interface.
"""

from typing import Any

import pyomo.environ as pyo

from app.application.strategy.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver


class HighsSolver(BaseTechnologySolver):
    """Solver adapter for HiGHS via the Pyomo APPSI interface.

    HiGHS is an open-source, high-performance LP/MIP solver. APPSI
    (Auto-Persistent Solver Interface) is Pyomo's in-memory interface that
    avoids writing temporary files, giving faster solve times than the
    classic ``SolverFactory("highs")`` path.
    """

    def solve(self, model: pyo.ConcreteModel) -> Any:
        solver = pyo.SolverFactory("appsi_highs")
        return solver.solve(model, tee=True)

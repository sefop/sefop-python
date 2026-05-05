"""Abstract base class (interface) that every solver adapter must implement.

The optimization orchestrator in ``optimization.py`` talks to solvers only
through this interface. That means you can swap HiGHS for Xpress (or any
future solver) without changing the optimization logic — just provide a new
subclass of ``BaseTechnologySolver``.
"""

from abc import ABC, abstractmethod
from typing import Any

import pyomo.environ as pyo


class BaseTechnologySolver(ABC):
    """Base class for solver technology adapters.

    Think of this as a *contract* (formally, an Abstract Base Class / ABC):
    it declares that every solver adapter **must** provide a ``solve(model)``
    method, but it does not contain any solving logic itself. This lets the
    optimization code call ``solver.solve(model)`` without knowing or caring
    whether the underlying engine is HiGHS, Xpress, or something else.

    To add a new solver, subclass this class and implement ``solve``.
    """

    @abstractmethod
    def solve(self, model: pyo.ConcreteModel) -> Any:
        """Solve the given Pyomo model and return the solver results."""

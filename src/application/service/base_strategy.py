"""Contract that every optimization solver must follow.

The rest of the application talks to solvers through this interface, never
through a concrete class like ``HiGHSSolver`` directly. That makes it easy
to swap one solver for another (e.g., HiGHS → Gurobi) without touching
any of the calling code.
"""

from abc import ABC, abstractmethod

from domain.recommendation import Recommendation
from domain.request import Request


class BaseStrategy(ABC):
    """
    An abstract base class (ABC) is like a contract: it declares a set of
    methods that every solver **must** implement, but says nothing about
    *how*. Any class that inherits from ``BaseStrategy`` is forced to provide
    a ``solve()`` method, so the rest of the system can call ``solve()``
    without caring whether HiGHS, Gurobi, or a hand-written heuristic is
    doing the work behind the scenes.

    Implementations provide different solving strategies (MIP, heuristic, etc.).
    """

    @abstractmethod
    def solve(self, request: Request) -> Recommendation | None:
        """Solves the optimization problem related to this request.

        Args:
            request: The knapsack request.

        Returns:
            The best recommendation found, or None if no feasible solution exists.
        """

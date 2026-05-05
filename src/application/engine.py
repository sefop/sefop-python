"""Central orchestrator that drives the knapsack optimization pipeline.

This module owns the top-level workflow: select the right solver based on
problem size, run it, and return the result.

Key design concept — "strategy selection":
    Engine decides internally which solver to use. Small problems (few products)
    are routed to the MIP solver for an optimal solution; larger problems are
    routed to the greedy heuristic for speed. Callers never need to know which
    solver ran.
"""
from __future__ import annotations

import logging

from application.service.base_strategy import BaseStrategy
from application.strategy.heuristic.greedy_calories import GreedyCalories
from domain.recommendation import Recommendation
from domain.request import Request

logger = logging.getLogger(__name__)

# Problems with at most this many products are solved with MIP (exact).
# Larger problems are routed to the greedy heuristic for speed.
MAX_PRODUCTS_FOR_MIP = 50


class Engine:
    """Orchestrates the knapsack optimization pipeline.

    Selects a solver strategy based on problem size, runs it, and returns
    the result. The caller receives a Recommendation or None — no solver
    details leak out.
    """

    def __init__(self, max_products_for_mip: int = MAX_PRODUCTS_FOR_MIP) -> None:
        self._heuristic = GreedyCalories()
        self._max_products_for_mip = max_products_for_mip

    def run(self, request: Request) -> Recommendation | None:
        """Select a solver and run the optimization.

        Args:
            request: The knapsack request to solve.

        Returns:
            The best Recommendation found, or None if no feasible solution exists.
        """
        strategy = self._select_strategy(request)
        logger.info(
            "Selected %s for %d products",
            type(strategy).__name__,
            len(request.products),
        )
        return strategy.solve(request)

    def _select_strategy(self, request: Request) -> BaseStrategy:
        """Choose MIP or greedy heuristic based on number of products."""
        if len(request.products) <= self._max_products_for_mip:
            # TODO: replace with MipStrategy() once implemented
            return self._heuristic
        return self._heuristic

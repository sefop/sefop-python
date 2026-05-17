"""Mixed-Integer Programming (MIP) solver for the knapsack problem.

This module contains the exact-optimisation solver. It delegates to three
internal stages — preprocess, optimize, postprocess — each of which can be
extended independently. When the problem is small enough for MIP to solve
in a reasonable time, this solver is preferred over the greedy heuristic
because it guarantees an optimal (calorie-maximising) selection.

It plugs into the system as one of the solver strategies that Engine can
choose between (the other being GreedyCalories).
"""

from __future__ import annotations

import logging

from services.base_strategy import BaseStrategy
from optimization.strategy.mip.optimization.optimization import Optimization
from optimization.strategy.mip.postprocess.postprocess import PostProcess
from optimization.strategy.mip.preprocess.preprocess import PreProcess
from domain.recommendation import Recommendation
from domain.request import Request

logger = logging.getLogger(__name__)


class MipStrategy(BaseStrategy):
    """Mixed-Integer Programming Strategy.

    Orchestrates a 3-step pipeline: preprocess → optimize → postprocess.
    All solver-technology details are encapsulated in the optimization package.
    """

    def __init__(self, solver_name: str = "highs") -> None:
        self._pre_process = PreProcess()
        self._optimization = Optimization(solver_name=solver_name)
        self._post_process = PostProcess()

    def solve(self, request: Request) -> Recommendation | None:
        """Run the full MIP solver pipeline.

        Args:
            request: The knapsack request to solve.

        Returns:
            The optimal Recommendation, or None if no feasible solution exists.
        """
        # Phase 1: Preprocess
        preprocessed_data = self._pre_process.run(request)

        # Phase 2: Optimize (build model → solve → extract Recommendation)
        recommendation = self._optimization.run(preprocessed_data)
        if recommendation is None:
            logger.warning("MIP found no feasible solution")
            return None

        # Phase 3: Post-process
        return self._post_process.run(recommendation)

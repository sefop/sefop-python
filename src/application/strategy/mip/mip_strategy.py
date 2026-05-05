"""Mixed-Integer Programming (MIP) solver for cargo optimization.

This module contains the exact-optimization solver.  It delegates to three
internal stages — preprocess, optimize, postprocess — each of which can be
extended independently.  When the problem is small enough for MIP to solve
in a reasonable time, this solver is preferred because it guarantees an
optimal (revenue-maximizing) cargo selection.

It plugs into the system as one of the solver strategies that Engine can
choose between (the other being the heuristic solver).
"""

import logging

from app.application.service.base_strategy import BaseStrategy
from app.application.strategy.mip.optimization.optimization import Optimization
from app.application.strategy.mip.postprocess.postprocess import PostProcess
from app.application.strategy.mip.preprocess.preprocess import PreProcess
from app.domain.recommendation import Recommendation
from app.domain.request import Request

logger = logging.getLogger(__name__)


class MipStrategy(BaseStrategy):
    """Mixed-Integer Programming solver.

    Orchestrates a 3-step pipeline: preprocess → optimize → postprocess.
    All solver-technology details are encapsulated in the optimization package.
    """

    def __init__(
        self,
        solver_technology: str = "appsi_highs",
        export_lp: bool = False,
        output_folder: str = "output",
    ) -> None:
        self._pre_process = PreProcess()
        self._optimization = Optimization(
            solver_name=solver_technology,
            export_lp=export_lp,
            output_folder=output_folder,
        )
        self._post_process = PostProcess()

    def solve(self, request: Request) -> list[Recommendation]:
        """Run the full MIP Solver pipeline."""
        # Phase 1: Preprocess
        preprocessed_data = self._pre_process.run(request)
        if not preprocessed_data.allowed_ids:
            logger.warning("No allowed cargo items after preprocessing")
            return [Recommendation(
                selected=[],
                non_selected=list(request.cargo_requests),
            )]

        # Phase 2: Optimize (build model + solve + transform solutions to business recommendation)
        recommendation = self._optimization.run(preprocessed_data)
        if recommendation is None:
            return []

        # Phase 3: Post-process
        return [self._post_process.run(recommendation)]

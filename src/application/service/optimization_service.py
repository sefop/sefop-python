"""Orchestrates the full "solve a knapsack request" workflow.

This is the main entry point that calling code (e.g., a CLI command) uses to
run an optimization. It coordinates loading data and running the solver, so
callers don't need to manage those steps themselves.
"""

import logging

from application.service.base_data_loader import BaseDataLoader
from application.service.base_strategy import BaseStrategy
from application.service.optimization_response import OptimizationResponse

logger = logging.getLogger(__name__)


class OptimizationService:
    """Orchestrates the "load → solve → respond" pipeline for one request.

    In software engineering this is called a *use case* — a single,
    self-contained action the system offers to the outside world. Here the
    action is: "given a request ID, fetch the data, run the solver, and
    return a result." The service itself contains no optimization math; it
    just wires together a data loader and a strategy.
    """

    def __init__(self, request_loader: BaseDataLoader, strategy: BaseStrategy) -> None:
        self._request_loader = request_loader
        self._strategy = strategy

    def solve(self, request_id: str) -> OptimizationResponse:
        """Load a request and run the optimization pipeline.

        Args:
            request_id: Identifier of the request to solve.

        Returns:
            An OptimizationResponse with the recommendation or an error message.
        """
        logger.info("Solving request: %s", request_id)

        request = self._request_loader.load(request_id)
        if request is None:
            logger.warning("Request not found: %s", request_id)
            return OptimizationResponse.failure(f"Request '{request_id}' not found")

        recommendation = self._strategy.solve(request)
        if recommendation is None:
            logger.warning("No feasible solution for request: %s", request_id)
            return OptimizationResponse.failure("No feasible solution found")

        logger.info("Request %s solved successfully", request_id)
        return OptimizationResponse.success(recommendation)

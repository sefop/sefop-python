"""Data container that carries request data into the MIP model.

Defines the boundary between the preprocessing stage and the optimization
stage. Keeping them separate makes each independently extensible.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.request import Request


@dataclass(frozen=True)
class PreProcessedData:
    """Preprocessed data ready for MIP model construction.

    Attributes:
        request: The original knapsack request.
    """

    request: Request

"""Data container that carries preprocessed cargo data into the MIP model.

This module defines the immutable structure that the preprocessing stage
produces and the optimization stage consumes.  It keeps the boundary
between the two stages explicit: everything the optimizer needs is in
one object rather than scattered across loose variables.
"""

from dataclasses import dataclass

from app.domain.cargo_request import CargoRequest
from app.domain.request import Request


@dataclass(frozen=True)
class PreProcessedData:
    """Preprocessed data ready for MIP model construction.

    Attributes:
        request: The original optimization request.
        cargo_map: Mapping of cargo ID to CargoRequest.
        allowed_ids: IDs of cargo items eligible for selection.
        forbidden_ids: IDs of cargo items excluded (invalid weight/volume).
    """

    request: Request
    cargo_map: dict[str, CargoRequest]
    allowed_ids: list[str]
    forbidden_ids: list[str]

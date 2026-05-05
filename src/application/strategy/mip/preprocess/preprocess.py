"""Preprocessing stage that prepares raw request data for the MIP model.

This module sits at the start of the MIP solver pipeline.  Its job is to
partition cargo into "allowed" (eligible for optimization) and "forbidden"
(excluded up front), and to build lookup structures the optimizer needs.

Extend the PreProcess class here to add custom filtering, data enrichment,
or parameter tuning before the model is built.
"""

from app.domain.cargo_request import CargoRequest
from app.domain.request import Request
from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData


class PreProcess:
    """Preprocessing step before MIP model construction.

    Override this class to add custom preprocessing logic such as
    data enrichment, cargo filtering, or parameter tuning.
    """

    def run(self, request: Request) -> PreProcessedData:
        """Partition cargo into allowed and forbidden based on validity.

        Cargo with non-positive weight or volume is forbidden.
        """
        cargo_map: dict[str, CargoRequest] = {}
        allowed_ids: list[str] = []
        forbidden_ids: list[str] = []

        for cargo in request.cargo_requests:
            cargo_map[cargo.id] = cargo
            if cargo.weight_kg > 0 and cargo.volume_m3 > 0:
                allowed_ids.append(cargo.id)
            else:
                forbidden_ids.append(cargo.id)

        return PreProcessedData(
            request=request,
            cargo_map=cargo_map,
            allowed_ids=allowed_ids,
            forbidden_ids=forbidden_ids,
        )

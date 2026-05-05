"""Constraint enforcing the aircraft's maximum volume capacity.

Part of the MIP cargo optimization model assembled in ``optimization.py``.
"""

import pyomo.environ as pyo

from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData


class ConstraintLimitVolume:
    """Total selected cargo volume must not exceed aircraft capacity:

        ∑(i ∈ I_a) v_i · x_i ≤ V

    Where:
    - I_a is the set of allowed cargo items
    - v_i is the volume in m³ of cargo item i
    - x_i is 1 if cargo item i is selected, 0 otherwise
    - V is the maximum volume capacity of the aircraft in m³.
    """

    def add_to_model(self, model: pyo.ConcreteModel, preprocessed_data: PreProcessedData) -> None:
        aircraft = preprocessed_data.request.aircraft
        cargo_map = preprocessed_data.cargo_map

        model.volume_limit = pyo.Constraint(
            expr=sum(
                cargo_map[cid].volume_m3 * model.select_cargo[cid]
                for cid in preprocessed_data.allowed_ids
            ) <= aircraft.max_volume_m3
        )

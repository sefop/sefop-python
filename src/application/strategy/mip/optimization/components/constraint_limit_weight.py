"""Constraint enforcing the aircraft's maximum weight capacity.

Part of the MIP cargo optimization model assembled in ``optimization.py``.
"""

import pyomo.environ as pyo

from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData


class ConstraintLimitWeight:
    """Total selected cargo weight must not exceed aircraft capacity:

        ∑(i ∈ I_a) w_i · x_i ≤ W

    Where:
    - I_a is the set of allowed cargo items
    - w_i is the weight in kg of cargo item i
    - x_i is 1 if cargo item i is selected, 0 otherwise
    - W is the maximum weight capacity of the aircraft in kg.
    """

    def add_to_model(self, model: pyo.ConcreteModel, preprocessed_data: PreProcessedData) -> None:
        aircraft = preprocessed_data.request.aircraft
        cargo_map = preprocessed_data.cargo_map

        model.weight_limit = pyo.Constraint(
            expr=sum(
                cargo_map[cid].weight_kg * model.select_cargo[cid]
                for cid in preprocessed_data.allowed_ids
            ) <= aircraft.max_weight_kg
        )

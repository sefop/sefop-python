"""Constraint that forces forbidden cargo items to be excluded from selection.

Part of the MIP cargo optimization model assembled in ``optimization.py``.
"""

import pyomo.environ as pyo

from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData


class ConstraintForbidCargo:
    """Forbidden cargo items must not be selected:

        x_i = 0  ∀ i ∈ I_f

    Where:
    - I_f is the set of forbidden cargo items (invalid weight or volume)
    - x_i is 1 if cargo item i is selected, 0 otherwise.
    """

    def add_to_model(self, model: pyo.ConcreteModel, preprocessed_data: PreProcessedData) -> None:
        forbidden_ids = preprocessed_data.forbidden_ids
        model.forbid_cargo = pyo.Constraint(
            forbidden_ids,
            rule=lambda m, cid: m.select_cargo[cid] == 0,
        )

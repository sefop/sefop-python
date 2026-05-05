"""Binary decision variable indicating whether each cargo item is selected.

Part of the MIP cargo optimization model assembled in ``optimization.py``.
"""

import pyomo.environ as pyo

from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData


class VariableSelectCargo:
    """Binary decision variable for each cargo item:

        x_i ∈ {0, 1}  ∀ i ∈ I

    Where:
    - I = I_a ∪ I_f is the set of all cargo items (allowed and forbidden)
    - x_i is 1 if cargo item i is selected, 0 otherwise.
    """

    def add_to_model(self, model: pyo.ConcreteModel, preprocessed_data: PreProcessedData) -> None:
        model.select_cargo = pyo.Var(
            preprocessed_data.allowed_ids + preprocessed_data.forbidden_ids,
            domain=pyo.Binary,
        )

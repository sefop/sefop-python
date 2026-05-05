"""Binary helper variable indicating whether each unique client is selected.

Part of the MIP cargo optimization model assembled in ``optimization.py``.
"""

import pyomo.environ as pyo

from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData


class VariableSelectClient:
    """Binary helper variable for each unique client:

        y_c ∈ {0, 1}  ∀ c ∈ C

    Where:
    - C is the set of unique client names derived from allowed cargo items I_a
    - y_c is 1 if client c is considered selected, 0 otherwise.
    """

    def add_to_model(self, model: pyo.ConcreteModel, preprocessed_data: PreProcessedData) -> None:
        client_names = sorted({
            preprocessed_data.cargo_map[cid].client_name
            for cid in preprocessed_data.allowed_ids
        })
        model.client_names = pyo.Set(initialize=client_names)
        model.select_client = pyo.Var(model.client_names, domain=pyo.Binary)

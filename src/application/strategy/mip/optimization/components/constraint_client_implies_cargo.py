"""Constraint linking client selection to cargo selection.

A client is considered "selected" only when all of their cargo items are
selected. Part of the MIP cargo optimization model assembled in
``optimization.py``.
"""

import pyomo.environ as pyo

from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData


class ConstraintClientImpliesCargo:
    """A client can only be selected if all of their cargo items are selected:

        y_c ≤ x_i  ∀ c ∈ C, ∀ i ∈ I_c

    Where:
    - C is the set of unique clients
    - I_c is the set of allowed cargo items belonging to client c
    - y_c is 1 if client c is selected, 0 otherwise
    - x_i is 1 if cargo item i is selected, 0 otherwise.
    """

    def add_to_model(self, model: pyo.ConcreteModel, preprocessed_data: PreProcessedData) -> None:
        cargo_map = preprocessed_data.cargo_map

        # Build (client, cargo_id) pairs for allowed cargo
        pairs = [
            (cargo_map[cid].client_name, cid)
            for cid in preprocessed_data.allowed_ids
        ]

        model.client_implies_cargo = pyo.Constraint(
            pairs,
            rule=lambda m, client, cid: m.select_client[client] <= m.select_cargo[cid],
        )

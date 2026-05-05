"""Client diversity objective component that rewards selecting more unique clients.

Part of the MIP cargo optimization model assembled in ``optimization.py``.
"""

import pyomo.environ as pyo

from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData

# Scaling factor for the client diversity term in the combined objective.
# At 10.0, each additional unique client contributes a bonus equivalent to
# $10 of revenue. Increase to favor serving more clients; decrease to favor
# pure revenue maximization.
# Unit: USD-equivalent per client. Valid range: ≥ 0.
CLIENT_DIVERSITY_WEIGHT = 10.0


class ObjectiveClientDiversity:
    """Client diversity component of the objective function:

        β · ∑(c ∈ C) y_c

    Where:
    - C is the set of unique clients
    - y_c is 1 if client c is selected, 0 otherwise
    - β is the diversity weight (CLIENT_DIVERSITY_WEIGHT = 10.0).

    This encourages selecting cargo from different clients rather than
    concentrating on a single client.
    """

    def build_expression(
        self, model: pyo.ConcreteModel,
    ) -> pyo.Expression:
        return CLIENT_DIVERSITY_WEIGHT * sum(
            model.select_client[client]
            for client in model.client_names
        )

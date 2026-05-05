"""Revenue objective component that maximizes total cargo revenue.

Part of the MIP cargo optimization model assembled in ``optimization.py``.
"""

import pyomo.environ as pyo

from app.application.strategy.mip.preprocess.pre_processed_data import PreProcessedData

# Scaling factor for the revenue term in the combined objective function.
# At 1.0, revenue is measured in raw USD. Adjust this relative to
# CLIENT_DIVERSITY_WEIGHT (in objective_client_diversity.py) to control the
# revenue-vs-diversity trade-off.
# Unit: dimensionless multiplier. Valid range: > 0.
REVENUE_WEIGHT = 1.0


class ObjectiveRevenue:
    """Revenue component of the objective function:

        α · ∑(i ∈ I_a) r_i · x_i

    Where:
    - I_a is the set of allowed cargo items
    - r_i is the revenue in USD of cargo item i
    - x_i is 1 if cargo item i is selected, 0 otherwise
    - α is the revenue weight (REVENUE_WEIGHT = 1.0).
    """

    def build_expression(
        self, model: pyo.ConcreteModel, preprocessed_data: PreProcessedData
    ) -> pyo.Expression:
        cargo_map = preprocessed_data.cargo_map
        return REVENUE_WEIGHT * sum(
            cargo_map[cid].revenue_usd * model.select_cargo[cid]
            for cid in preprocessed_data.allowed_ids
        )

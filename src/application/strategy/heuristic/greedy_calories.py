"""Greedy heuristic that maximises calories for a knapsack request.

Products are ranked by calorie density (calories per kg). The algorithm
works through the ranked list and takes as many units of each product as
the remaining weight and budget allow.
"""

from math import floor

from application.service.base_strategy import BaseStrategy
from domain.recommendation import Recommendation
from domain.request import Request


class GreedyCalories(BaseStrategy):
    """Greedy knapsack solver that prioritises calorie-dense products.

    This is a *heuristic* — it does not guarantee the mathematically
    optimal solution, but it runs in linear time and produces good results
    in practice for the calorie-maximisation objective.
    """

    def solve(self, request: Request) -> Recommendation | None:
        """Greedily select products ranked by calories per kg.

        Args:
            request: The knapsack request with products and constraints.

        Returns:
            A Recommendation with the selected quantities, or None if no
            product fits within the weight and budget constraints.
        """
        sorted_products = sorted(
            request.products,
            key=lambda p: p.calories / p.weight_kg,
            reverse=True,
        )

        remaining_weight = request.max_weight_kg
        remaining_budget = request.max_budget_usd
        quantities: dict = {}

        for product in sorted_products:
            max_by_weight = floor(remaining_weight / product.weight_kg)
            max_by_budget = floor(remaining_budget / product.price_usd)
            qty = min(max_by_weight, max_by_budget)
            if qty >= 1:
                quantities[product] = qty
                remaining_weight -= qty * product.weight_kg
                remaining_budget -= qty * product.price_usd

        if not quantities:
            return None

        return Recommendation(request=request, quantities=quantities)

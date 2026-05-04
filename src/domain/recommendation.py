from __future__ import annotations
from dataclasses import dataclass, field
from domain.product import Product
from domain.request import Request


@dataclass(frozen=True)
class Recommendation:
    request: Request
    quantities: dict[Product, int]
    total_calories: int = field(init=False)
    total_cost_usd: float = field(init=False)
    total_weight_kg: float = field(init=False)

    def __post_init__(self) -> None:
        if not self.quantities:
            raise ValueError("quantities must be non-empty")
        allowed = set(self.request.products)
        for product, qty in self.quantities.items():
            if product not in allowed:
                raise ValueError(f"product '{product.name}' is not in request")
            if qty < 1:
                raise ValueError(f"quantity for '{product.name}' must be >= 1")
        calories = sum(p.calories * q for p, q in self.quantities.items())
        cost = sum(p.price_usd * q for p, q in self.quantities.items())
        weight = sum(p.weight_kg * q for p, q in self.quantities.items())
        object.__setattr__(self, "total_calories", calories)
        object.__setattr__(self, "total_cost_usd", cost)
        object.__setattr__(self, "total_weight_kg", weight)
        if cost > self.request.max_budget_usd:
            raise ValueError(
                f"total cost {cost} exceeds budget {self.request.max_budget_usd}"
            )
        if weight > self.request.max_weight_kg:
            raise ValueError(
                f"total weight {weight} exceeds limit {self.request.max_weight_kg}"
            )

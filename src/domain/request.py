from __future__ import annotations
from dataclasses import dataclass
from domain.product import Product


@dataclass(frozen=True)
class Request:
    max_weight_kg: float
    max_budget_usd: float
    products: list[Product]

    def __post_init__(self) -> None:
        if self.max_weight_kg <= 0:
            raise ValueError("max_weight_kg must be > 0")
        if self.max_budget_usd <= 0:
            raise ValueError("max_budget_usd must be > 0")
        if not self.products:
            raise ValueError("products must be a non-empty list")
        names = [p.name for p in self.products]
        if len(names) != len(set(names)):
            raise ValueError("duplicate product names are not allowed")

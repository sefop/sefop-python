from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    name: str
    price_usd: float
    weight_kg: float
    calories: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be a non-empty string")
        if self.price_usd <= 0:
            raise ValueError("price_usd must be > 0")
        if self.weight_kg <= 0:
            raise ValueError("weight_kg must be > 0")
        if self.calories <= 0:
            raise ValueError("calories must be > 0")

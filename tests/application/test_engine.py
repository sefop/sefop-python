import pytest
from domain.product import Product
from domain.request import Request
from application.engine import Engine


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


def test__engine__when_request_is_solvable__returns_recommendation(banana):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana])
    engine = Engine()

    # ACT
    result = engine.run(request)

    # ASSERT
    assert result is not None
    assert result.total_calories > 0


def test__engine__when_no_product_fits__returns_none():
    # ARRANGE — budget too tight to buy anything
    expensive = Product(name="expensive", price_usd=100.0, weight_kg=1.0, calories=100)
    request = Request(max_weight_kg=10.0, max_budget_usd=0.01, products=[expensive])
    engine = Engine()

    # ACT
    result = engine.run(request)

    # ASSERT
    assert result is None

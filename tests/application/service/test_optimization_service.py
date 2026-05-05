from unittest.mock import MagicMock

import pytest
from domain.product import Product
from domain.recommendation import Recommendation
from domain.request import Request
from application.service.base_data_loader import BaseDataLoader
from application.service.base_strategy import BaseStrategy
from application.service.optimization_service import OptimizationService


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def request_(banana) -> Request:
    return Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana])


@pytest.fixture
def recommendation(request_, banana) -> Recommendation:
    return Recommendation(request=request_, quantities={banana: 1})


def test__optimization_service__when_loader_returns_none__returns_failure():
    # ARRANGE
    loader = MagicMock(spec=BaseDataLoader)
    loader.load.return_value = None
    strategy = MagicMock(spec=BaseStrategy)
    service = OptimizationService(request_loader=loader, strategy=strategy)

    # ACT
    response = service.solve("req-1")

    # ASSERT
    assert response.status == "FAILURE"
    assert "req-1" in response.message
    strategy.solve.assert_not_called()


def test__optimization_service__when_strategy_returns_none__returns_failure(request_):
    # ARRANGE
    loader = MagicMock(spec=BaseDataLoader)
    loader.load.return_value = request_
    strategy = MagicMock(spec=BaseStrategy)
    strategy.solve.return_value = None
    service = OptimizationService(request_loader=loader, strategy=strategy)

    # ACT
    response = service.solve("req-1")

    # ASSERT
    assert response.status == "FAILURE"
    assert response.recommendation is None


def test__optimization_service__when_strategy_succeeds__returns_success(request_, recommendation):
    # ARRANGE
    loader = MagicMock(spec=BaseDataLoader)
    loader.load.return_value = request_
    strategy = MagicMock(spec=BaseStrategy)
    strategy.solve.return_value = recommendation
    service = OptimizationService(request_loader=loader, strategy=strategy)

    # ACT
    response = service.solve("req-1")

    # ASSERT
    assert response.status == "SUCCESS"
    assert response.recommendation is recommendation

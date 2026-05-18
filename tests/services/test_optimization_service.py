"""Integration tests for OptimizationService."""

import pytest

from services.json_data_loader import JsonDataLoader
from services.optimization_service import OptimizationService


@pytest.mark.integration
def test__optimization_service__when_request_exists__returns_success():
    """ARRANGE: Load a real request from data/1/data.json."""
    loader = JsonDataLoader(folder_path="data")
    service = OptimizationService(request_loader=loader)

    # ACT
    response = service.solve("1")

    # ASSERT — The service should successfully load and optimize the request
    assert response.status == "SUCCESS"
    assert response.recommendation is not None
    assert response.recommendation.total_calories > 0


def test__optimization_service__when_request_not_found__returns_failure():
    """ARRANGE: Attempt to load a request ID that doesn't exist."""
    loader = JsonDataLoader(folder_path="data")
    service = OptimizationService(request_loader=loader)

    # ACT
    response = service.solve("nonexistent-id-999")

    # ASSERT — Should return a FAILURE status with an appropriate message
    assert response.status == "FAILURE"
    assert response.recommendation is None
    assert "nonexistent-id-999" in response.message

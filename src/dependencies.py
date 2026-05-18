"""Composition root — assembles the optimization pipeline.

This is the one place in the codebase that wires together external
dependencies. Swapping JsonDataLoader for a database loader, or adjusting
the Engine's strategy selection threshold, is a one-line change here.
"""
from __future__ import annotations

from services.optimization_service import OptimizationService
from services.json_data_loader import JsonDataLoader
from services.settings import Settings


def create_optimization_service() -> OptimizationService:
    """Build and return a fully-configured OptimizationService.

    The service creates its own Engine internally. The data loader is the
    only external dependency that needs to be wired.
    """
    settings = Settings()
    loader = JsonDataLoader(folder_path=settings.folder_path)
    return OptimizationService(request_loader=loader)

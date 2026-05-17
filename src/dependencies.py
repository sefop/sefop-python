"""Composition root — assembles the full optimization pipeline.

This is the one place in the codebase that knows about every layer. All other
modules depend only on abstractions (ports); only this module wires concrete
implementations to those abstractions.

Benefit: swapping JsonDataLoader for a database loader, or HiGHS for another
solver, is a one-line change here — nothing else needs to change.
"""
from __future__ import annotations

from services.engine import Engine
from services.optimization_service import OptimizationService
from services.json_data_loader import JsonDataLoader
from services.settings import Settings


def create_optimization_service() -> OptimizationService:
    """Build and return a fully-wired OptimizationService."""
    settings = Settings()
    loader = JsonDataLoader(folder_path=settings.folder_path)
    engine = Engine()
    return OptimizationService(request_loader=loader, strategy=engine)

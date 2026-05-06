"""Solver-agnostic representation of a decision variable.

Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelVariable:
    """A single decision variable in the optimization model.

    Attributes:
        name: Unique identifier used to reference the variable in expressions.
        var_type: ``"integer"``, ``"binary"``, or ``"continuous"``.
        lower_bound: Minimum allowed value (default 0.0).
        upper_bound: Maximum allowed value; ``None`` means unbounded.
    """

    name: str
    var_type: str
    lower_bound: float = 0.0
    upper_bound: float | None = None

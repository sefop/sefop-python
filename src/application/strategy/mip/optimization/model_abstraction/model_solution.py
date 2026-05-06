"""Solver output returned by BaseTechnologySolver.

Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSolution:
    """Raw output from a solver run.

    Attributes:
        status: Solver termination status, e.g. ``"optimal"``, ``"feasible"``,
            ``"infeasible"``.
        variable_values: Map of variable name → solution value.
            ``None`` when the problem has no feasible solution.
    """

    status: str
    variable_values: dict[str, float] | None

"""Complete solver-agnostic representation of a MIP optimization problem.

Assembles variables, constraints, and objective into a single object that
``BaseTechnologySolver`` implementations consume.
Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

from application.strategy.mip.optimization.model_abstraction.linear_constraint import LinearConstraint
from application.strategy.mip.optimization.model_abstraction.linear_expression import LinearExpression
from application.strategy.mip.optimization.model_abstraction.model_variable import ModelVariable


@dataclass
class OptimizationModel:
    """Complete MIP problem definition.

    Attributes:
        variables: Decision variables that appear in constraints and objective.
        constraints: Linear constraints the solution must satisfy.
        objective_expression: Linear expression to optimise.
        objective_sense: ``"maximize"`` or ``"minimize"``.
    """

    variables: list[ModelVariable]
    constraints: list[LinearConstraint]
    objective_expression: LinearExpression
    objective_sense: str

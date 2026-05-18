"""Thin wrapper over the ``parse-lp`` library.

This module isolates the rest of the comparer from the concrete parser
implementation.  Every other module in the ``lp_comparer`` package
operates exclusively on the dataclasses defined here
(:class:`ParsedLpModel`, :class:`VariableInfo`, etc.), never on
``parse-lp`` types directly.  If the parser library is replaced in the
future, only this file needs to change.
"""

from dataclasses import dataclass, field
from pathlib import Path

from parse_lp import LpParser


@dataclass
class VariableInfo:
    """Parsed representation of an LP variable.

    Attributes:
        name: Variable name as it appears in the LP file.
        var_type: Variable type string as returned by the parser (e.g.
            ``"DoubleBound(0.0, 1.0)"``, ``"Binary"``,
            ``"Integer"``).  The raw string is kept so that bound
            information encoded by the parser is preserved without
            needing a separate bounds field.
    """

    name: str
    var_type: str


@dataclass
class ObjectiveInfo:
    """Parsed representation of an LP objective.

    Attributes:
        name: Objective name as it appears in the LP file.
        coefficients: Mapping of variable name → coefficient value.
    """

    name: str
    coefficients: dict[str, float] = field(default_factory=dict)


@dataclass
class ConstraintInfo:
    """Parsed representation of an LP constraint.

    Attributes:
        name: Constraint name as it appears in the LP file.
        operator: Sense of the constraint (``"LTE"``, ``"GTE"``,
            ``"EQ"``).
        rhs: Right-hand side value of the constraint.
        coefficients: Mapping of variable name → coefficient value.
    """

    name: str
    operator: str
    rhs: float
    coefficients: dict[str, float] = field(default_factory=dict)


@dataclass
class ParsedLpModel:
    """Normalised representation of a parsed LP model.

    Attributes:
        name: Model name.
        sense: Optimisation sense (``"maximize"`` or ``"minimize"``).
        variables: Mapping of variable name → :class:`VariableInfo`.
        objectives: Mapping of objective name → :class:`ObjectiveInfo`.
        constraints: Mapping of constraint name → :class:`ConstraintInfo`.
    """

    name: str
    sense: str
    variables: dict[str, VariableInfo] = field(default_factory=dict)
    objectives: dict[str, ObjectiveInfo] = field(default_factory=dict)
    constraints: dict[str, ConstraintInfo] = field(default_factory=dict)


def parse_lp_file(path: Path) -> ParsedLpModel:
    """Parse an LP file and return a normalised :class:`ParsedLpModel`.

    Args:
        path: Path to the ``.lp`` file to parse.

    Returns:
        A :class:`ParsedLpModel` with all variables, objectives, and
        constraints indexed by name for order-agnostic comparison.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the LP file cannot be parsed.
    """
    parser = LpParser(str(path))
    parser.parse()

    # Index by name so the comparer can do O(1) lookups and
    # set-difference operations that are independent of file ordering.
    variables = {
        name: VariableInfo(name=name, var_type=info["var_type"])
        for name, info in parser.variables.items()
    }

    objectives: dict[str, ObjectiveInfo] = {}
    for obj in parser.objectives:
        obj_name = obj["name"]
        coefficients = {
            coef["name"]: coef["value"] for coef in obj["coefficients"]
        }
        objectives[obj_name] = ObjectiveInfo(name=obj_name, coefficients=coefficients)

    constraints: dict[str, ConstraintInfo] = {}
    for con in parser.constraints:
        con_name = con["name"]
        coefficients = {
            coef["name"]: coef["value"] for coef in con["coefficients"]
        }
        constraints[con_name] = ConstraintInfo(
            name=con_name,
            operator=con["operator"],
            rhs=con["rhs"],
            coefficients=coefficients,
        )

    return ParsedLpModel(
        name=parser.name,
        sense=parser.sense,
        variables=variables,
        objectives=objectives,
        constraints=constraints,
    )

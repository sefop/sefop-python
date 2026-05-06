from application.strategy.mip.optimization.model_abstraction.linear_constraint import LinearConstraint
from application.strategy.mip.optimization.model_abstraction.linear_expression import LinearExpression


def test__linear_constraint__stores_fields_correctly():
    # ARRANGE
    expr = LinearExpression()
    expr.add(0.12, "banana")

    # ACT
    constraint = LinearConstraint(name="weight_limit", lhs=expr, sign="<=", rhs=5.0)

    # ASSERT
    assert constraint.name == "weight_limit"
    assert constraint.lhs is expr
    assert constraint.sign == "<="
    assert constraint.rhs == 5.0

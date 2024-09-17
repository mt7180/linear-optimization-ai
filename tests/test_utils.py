import pytest
import types

from llm_optimizer.utils.helpers import parse_rule, ExpressionNotSafeError


def test_parse_rule_expression():
    # expression = "lambda model, i: sum(model.staff[model.DAYS[(i + j) % 7]] for j in range(5)) >= model.demand[model.DAYS[i]]"
    # allowed_vars = {"model.DAYS", "model.staff", "model.demand"}
    expr_str = "x + 2"
    allowed_vars = {"x"}

    rule = parse_rule(expr_str, allowed_vars)

    assert isinstance(rule, dict)
    assert all(key in rule.keys() for key in ("func", "args"))
    assert isinstance(rule["func"], types.FunctionType)
    assert isinstance(rule["args"], set)


def test_parse_rule_function():
    func_str = "lambda a,b: a + b"
    allowed_vars = {"a", "b"}

    rule = parse_rule(func_str, allowed_vars)

    assert isinstance(rule, dict)
    assert all(key in rule.keys() for key in ("func", "args"))
    assert isinstance(rule["func"], types.FunctionType)
    assert isinstance(rule["args"], set)


def test_parse_rule_pyo_expr():
    expr_str = "sum(m.x[(d+ working_day)%7]  for working_day in m.wd)  >= m.epsilon[d]"
    allowed_vars = {"m.x", "m.wd", "m.epsilon", "d"}

    rule = parse_rule(expr_str, allowed_vars)

    assert isinstance(rule, dict)
    assert all(key in rule.keys() for key in ("func", "args"))
    assert isinstance(rule["func"], types.FunctionType)
    assert isinstance(rule["args"], set)


def test_parse_rule_missing_vars():
    expr_str = "x + 2"
    allowed_vars = {}

    with pytest.raises(ExpressionNotSafeError):
        parse_rule(expr_str, allowed_vars)


def test_parse_rule_unallowed_operation():
    expr_str = "__import__('os').system('ls')"
    allowed_vars = {}

    with pytest.raises(ExpressionNotSafeError):
        parse_rule(expr_str, allowed_vars)

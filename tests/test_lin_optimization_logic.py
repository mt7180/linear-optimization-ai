import json
import pyomo.environ as pyo
from pydantic import ValidationError
from unittest.mock import MagicMock

import pytest

from llm_optimizer.models.llm import LinearOptimizationModel
from llm_optimizer.calculations.lin_optimization_logic import (
    construct_pyomo_model,
    solve,
    RuleError,
)


def test_construct_pyomo_model(mock_llm_response):
    model = construct_pyomo_model(mock_llm_response)
    assert isinstance(model, pyo.ConcreteModel)
    assert hasattr(model, "my_objective")


def test_construct_pyomo_model_wrong_input_type():
    with pytest.raises(TypeError):
        construct_pyomo_model(dict())


def test_construct_pyomo_model_no_objective(llm_response_format):
    input = llm_response_format(objective="null")

    with pytest.raises(ValidationError):
        construct_pyomo_model(LinearOptimizationModel(**json.loads(input)))


def test_construct_pyomo_model_wrong_optimization_sense(llm_response_format):
    input = llm_response_format(
        objective="""{
        "indexes": null,
        "expr": "model.x",
        "rule": null,
        "optimization_sense": "wrong_value",
        "doc": ""
    }"""
    )

    print(input)

    with pytest.raises(ValidationError):
        construct_pyomo_model(LinearOptimizationModel(**json.loads(input)))


def test_construct_pyomo_model_no_objective_rule(llm_response_format):
    input = llm_response_format(
        objective="""{
        "indexes": null,
        "expr": null,
        "rule": null,
        "optimization_sense": "maximize",
        "doc": ""
    }"""
    )

    with pytest.raises(RuleError):
        construct_pyomo_model(LinearOptimizationModel(**json.loads(input)))


def test_construct_pyomo_model_no_var(llm_response_format):
    input = llm_response_format(variables="[]")

    with pytest.raises(ValueError):
        construct_pyomo_model(LinearOptimizationModel(**json.loads(input)))


def test_solve_isolated(monkeypatch):
    mock_solver = MagicMock()
    mock_results = MagicMock()
    mock_results.write = MagicMock()
    mock_solver.solve.return_value = mock_results

    monkeypatch.setattr(pyo, "SolverFactory", MagicMock(return_value=mock_solver))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(within=pyo.NonNegativeReals)
    model.obj = pyo.Objective(expr=model.x)

    results, solved_model = solve(model)

    mock_solver.solve.assert_called_once_with(model)
    assert isinstance(solved_model, pyo.ConcreteModel)
    assert solved_model == model
    assert results == mock_results


@pytest.mark.integration
def test_solve_integrated(mock_llm_response):
    pyomo_model = construct_pyomo_model(mock_llm_response)
    results, solution = solve(pyomo_model)

    assert solution is not None
    assert isinstance(solution, pyo.ConcreteModel)
    assert hasattr(solution, "my_objective")
    assert results.solver.status == pyo.SolverStatus.ok
    assert results.solver.termination_condition == pyo.TerminationCondition.optimal

import pyomo.environ as pyo
from unittest.mock import MagicMock, patch

from llm_optimizer.calculations.lin_optimization_logic import (
    construct_pyomo_model,
    solve,
)


def test_construct_pyomo_model(mock_llm_response):
    model = construct_pyomo_model(mock_llm_response)
    assert isinstance(model, pyo.ConcreteModel)
    assert hasattr(model, "my_objective")


@patch("pyomo.environ.SolverFactory")
def test_solve(mock_solver_factory):
    mock_solver = MagicMock()
    mock_results = MagicMock()
    mock_solver_factory.return_value = mock_solver
    mock_solver.solve.return_value = mock_results

    model = pyo.ConcreteModel()
    model.x = pyo.Var(within=pyo.NonNegativeReals)
    model.obj = pyo.Objective(expr=model.x)
    results, solution = solve(model)

    assert mock_solver.solve.called
    assert isinstance(solution, pyo.ConcreteModel)
    assert solution == model
    mock_results.write.assert_called_once()

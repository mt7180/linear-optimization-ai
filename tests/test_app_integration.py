import pyomo.environ as pyo

from llm_optimizer.calculations.lin_optimization_logic import (
    construct_pyomo_model,
    solve,
)


def test_integration_successful(mock_llm_response):
    pyomo_model = construct_pyomo_model(mock_llm_response)
    results, solution = solve(pyomo_model)

    assert solution is not None
    assert isinstance(solution, pyo.ConcreteModel)
    assert hasattr(solution, "my_objective")
    assert results.solver.status == pyo.SolverStatus.ok
    assert results.solver.termination_condition == pyo.TerminationCondition.optimal

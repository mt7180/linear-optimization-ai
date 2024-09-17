import pyomo.environ as pyo
import pytest

from llm_optimizer.llm.communication_instructor import ask_llm_for_pyomo_model
from llm_optimizer.calculations.lin_optimization_logic import construct_pyomo_model, solve


def test_integration_successful(structured_llm_response):
    
    pyomo_model = construct_pyomo_model(structured_llm_response)
    results, solution = solve(pyomo_model)

    assert solution is not None
    assert isinstance(solution, pyo.ConcreteModel)
    assert hasattr(solution, "my_objective")
    assert results.solver.status == pyo.SolverStatus.ok
    assert results.solver.termination_condition == pyo.TerminationCondition.optimal
     
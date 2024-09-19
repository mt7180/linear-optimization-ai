import json
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from llm_optimizer.models.llm import LinearOptimizationModel


@pytest.fixture()
def at():
    yield AppTest.from_file("src/llm_optimizer/app.py").run()


@pytest.fixture
def mock_llm_response():
    cwd = Path(__file__).parent
    with open(cwd / "mock_llm_response.json", "r") as file:
        llm_pyomo_model = LinearOptimizationModel(**json.load(file))
    return llm_pyomo_model


@pytest.fixture
def llm_response_format():
    def factory(
        objective="""{
            "indexes": null,
            "expr": "model.x",
            "rule": null,
            "optimization_sense": "maximize",
            "doc": ""
        }""",
        variables="""[
                {
                    "name": "x",
                    "indexes": [],
                    "domain": null,
                    "doc": ""
                }
            ]""",
    ):
        return f"""
            {{
                "mathematical_formulation": "",
                "objective": {objective},
                "sets": [],
                "parameters": [],
                "variables": {variables},
                "constraints": [],
                "problem_str": ""
            }}
        """

    return factory

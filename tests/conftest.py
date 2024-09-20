import instructor
import json
import openai
import os
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import MagicMock

from llm_optimizer.models.llm import LinearOptimizationModel
from llm_optimizer.models.base import AppSettings


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


@pytest.fixture
def openai_client():
    SETTINGS = AppSettings()
    os.environ["OPENAI_API_KEY"] = SETTINGS.OPENAI_API_KEY
    return instructor.from_openai(
        openai.OpenAI(api_key=SETTINGS.OPENAI_API_KEY),
        mode=instructor.Mode.JSON,
    )


@pytest.fixture
def mock_openai_chat_completion(llm_response_format):
    def mock_create(**kwargs):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=llm_response_format()))
        ]
        return mock_response

    return mock_create

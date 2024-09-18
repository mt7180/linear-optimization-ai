import json
from pathlib import Path
import pytest

from llm_optimizer.models.llm import LinearOptimizationModel

from streamlit.testing.v1 import AppTest


@pytest.fixture()
def at():
    yield AppTest.from_file("src/llm_optimizer/app.py").run()


@pytest.fixture
def mock_llm_response():
    cwd = Path(__file__).parent
    with open(cwd / "mock_llm_response.json", "r") as file:
        llm_pyomo_model = LinearOptimizationModel(**json.load(file))
    return llm_pyomo_model

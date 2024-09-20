import instructor
import json
import openai
import pytest
from unittest.mock import MagicMock, ANY

from llm_optimizer.llm.communication_instructor import (
    get_llm_pyomo_model,
    ask_llm_for_pyomo_model,
)
from llm_optimizer.models.llm import LinearOptimizationModel


def test_get_llm_pyomo_model_add_problem_str(
    openai_client, monkeypatch, llm_response_format
):
    instructor_return_value = LinearOptimizationModel(
        **json.loads(llm_response_format())
    )
    mock_create = MagicMock(return_value=instructor_return_value)
    monkeypatch.setattr(openai_client.chat.completions, "create", mock_create)

    response = get_llm_pyomo_model(openai_client, "problem description", False)

    mock_create.assert_called_once_with(
        max_retries=ANY,
        model="gpt-4o",
        response_model=LinearOptimizationModel,
        max_tokens=ANY,
        temperature=ANY,
        messages=ANY,
    )
    assert response.problem_str == "problem description"


def test_get_llm_pyomo_model_no_user_input(openai_client):
    with pytest.raises(ValueError):
        get_llm_pyomo_model(openai_client, "", False)


def test_ask_llm_for_pyomo_model_invalid_llm_client(monkeypatch):
    invalid_openai_client = MagicMock(
        return_value=instructor.from_openai(
            openai.OpenAI(api_key="wrong_key"),
            mode=instructor.Mode.JSON,
        )
    )

    monkeypatch.setattr(instructor, "from_openai", invalid_openai_client)
    response = ask_llm_for_pyomo_model("problem description", False)

    invalid_openai_client.assert_called_once()
    assert response.error_message is not None


def test_ask_llm_for_pyomo_model_no_problem_formulation():
    response = ask_llm_for_pyomo_model(problem_formulation="")

    assert response.error_message is not None


def test_ask_llm_for_pyomo_model_negative_retries():
    with pytest.raises(ValueError):
        ask_llm_for_pyomo_model("problem description", max_retries=-1)

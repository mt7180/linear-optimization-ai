from unittest.mock import MagicMock, ANY
from streamlit.testing.v1 import AppTest


def test_app_start(at):
    assert not at.exception


def test_app_title(at):
    assert "Linear Optimization Assistant" in at.title[0].value


def test_app_input_area(at):
    assert len(at.text_area) > 0


def test_app_no_input(at):
    at.button[0].click().run()

    assert len(at.error) > 0
    assert at.error[0].value == "no input given"


def test_app_with_input(monkeypatch, mock_llm_response):
    text_input = "The llm will not be called here."

    mock_ask_llm = MagicMock(return_value=mock_llm_response)
    monkeypatch.setattr(
        "llm_optimizer.llm.communication_instructor.ask_llm_for_pyomo_model",
        mock_ask_llm,
    )  # structured_llm_response)

    at_mocked = AppTest.from_file("src/llm_optimizer/app.py").run()

    at_mocked.text_area[0].set_value(text_input)
    at_mocked.button[0].click().run()

    mock_ask_llm.assert_called_once_with(
        text_input, validate_input=ANY, max_retries=ANY, mock=False
    )
    assert len(at_mocked.markdown) > 0
    assert at_mocked.success[0].value == "Found an optimal solution!"

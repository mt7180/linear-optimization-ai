from httpx import HTTPStatusError
import inspect
import instructor
import instructor.exceptions
import openai
import os
from pydantic import ValidationError

import logging

from llm_optimizer.models.llm import LinearOptimizationModel, ValidationAnswer
from llm_optimizer.models.base import AppSettings


SETTINGS = AppSettings()
os.environ["OPENAI_API_KEY"] = SETTINGS.OPENAI_API_KEY

logging.getLogger("openai._base_client").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


def get_llm_pyomo_model(
    client: instructor.Instructor,
    user_input: str,
    validate_input: bool = True,
    llm_prompt_settings: dict = dict(temperature=0.2, max_tokens=2048),
) -> LinearOptimizationModel:
    if not user_input:
        raise ValueError("No problem formulation given")

    if validate_input:
        is_optimization_problem = validate_optimization_problem(user_input, client)
        logging.debug(
            f"The user input describes a valid linear optimization problem: {is_optimization_problem}"
        )

        if not is_optimization_problem.valid:
            raise ValidationError(
                f"Optimization problem not valid, reason: {is_optimization_problem.reason}"
            )

    prompt = inspect.cleandoc(f'''
        You are an AI assistant tasked with transfering a clients linear 
        optimization task into a mathematical formulation and a 
        python/ pyomo code snippet. Please use
        only the following pyomo modeling components to carefully define
        the pyomo model for the given optimization task. Please try to
        make the model as compact and pythonic as possible while staying 
        mathematically correct. Use the `pyomo.Param()` only if absolutely necessary.

        pyomo modeling components: """                     
        - A pyomo ConcreteModel, the pyomo model instance needs to be named `model`.               
        - `pyomo.Set()`               
        - `pyomo.Var()`                    
        - `pyomo.Param()` 
        - `pyomo.Constraint()`                    
        - for any rule only python lambda functions should be used.
        """
        
        Please be thorough and provide the response in the given response format. 
        Remember to start pyomo indexes with 1, not 0.
                                                
        optimization task: """
        {user_input}
        """
    ''')

    pyomo_model: LinearOptimizationModel = client.chat.completions.create(
        max_retries=1,
        model="gpt-4o",
        response_model=LinearOptimizationModel,
        max_tokens=llm_prompt_settings.get("max_tokens", 1024),
        temperature=llm_prompt_settings.get("temperature", 0.2),
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    pyomo_model.problem_str = user_input

    return pyomo_model


def validate_optimization_problem(
    user_input: str, client: instructor.Instructor
) -> ValidationAnswer:
    prompt = inspect.cleandoc(f'''
    Your job is to validate the given input and check wether it can be mathematically modeled
    by an optimization model whose requirements and objective are represented 
    by linear relationships (linear optimization) or not.
    input: """
    {user_input}
    """
    ''')

    return client.chat.completions.create(
        max_retries=1,
        model="gpt-3.5-turbo",
        response_model=ValidationAnswer,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )


def ask_llm_for_pyomo_model(
    problem_formulation: str,
    validate_input: bool = True,
    max_retries: int = 1,
    mock: bool = False,
) -> LinearOptimizationModel:
    if max_retries < 0:
        raise ValueError

    if mock:
        import json
        from pathlib import Path

        cwd = Path(__file__).parent.parent.parent.parent
        with open(cwd / "tests" / "mock_llm_response_complex.json", "r") as file:
            mocked_response = LinearOptimizationModel(**json.load(file))

        return mocked_response

    client: instructor.Instructor = instructor.from_openai(
        openai.OpenAI(api_key=SETTINGS.OPENAI_API_KEY),
        mode=instructor.Mode.JSON,  # .TOOLS,
    )

    llm_prompt_settings = {
        "temperature": 0.2,
        "max_tokens": 2048,
    }

    for _ in range(max_retries):
        try:
            llm_pyomo_model = get_llm_pyomo_model(
                client,
                problem_formulation,
                validate_input=validate_input,
                llm_prompt_settings=llm_prompt_settings,
            )
            logging.debug(llm_pyomo_model.model_dump_json(indent=2))
        except (
            HTTPStatusError,
            instructor.exceptions.InstructorRetryException,
            ValidationError,
            ValueError,
        ) as e:
            llm_pyomo_model = LinearOptimizationModel.empty()
            llm_pyomo_model.error_message = str(e)
        else:
            break

    return llm_pyomo_model


if __name__ == "__main__":
    post_office_optimization_task = """A post office requires a different number of
    full-time employees on each day of the week. The number of full-time employees
    required for each day is: Monday= 17, Tuesday= 13, Wednesday= 15, Thursday= 19, Friday= 14, Saturday= 16, Sunday= 11.
    Each full-time employee must work 5 consecutive days and then has 2 days off.
    Minimize the total number of full-time employees you need to hire. 
    """
    pie_eating_contest = """Max is in a pie eating contest that lasts 1 hour. Each torte
    that he eats takes 2 minutes. Each apple pie that he eats takes 3 minutes. 
    He receives 4 points for each torte and 5 points for each pie.
    What should Max eat so as to get the most points?
    """

    print(
        ask_llm_for_pyomo_model(
            post_office_optimization_task,
            validate_input=False,
            max_retries=1,
            mock=True,
        ).model_dump_json(indent=2)
    )

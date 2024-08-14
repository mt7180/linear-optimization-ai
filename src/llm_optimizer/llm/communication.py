import marvin

from src.llm_optimizer.models.llm import MaybeLinearOptimizationModel, LinearOptimizationModel
from src.llm_optimizer.models.base import AppSettings

@marvin.fn
def extract_pyomo_model(task: str) -> LinearOptimizationModel:
    """returns a pyomo model (ConcreteModel) for the linear optimization problem defined in `task` as result.
    If it is not possible to correctly formulate the pyomo model with the given return type of the function, formulate an error_message. 
    """

@marvin.fn
def pyomo_code_snippet(task: str) -> str:
    """returns a python/ pyomo code snippet to solve the following linear optimization task by using a ConcreteModel:
    {{task}}
    """

if __name__ == "__main__":
    import os

    settings = AppSettings()
    marvin.settings.openai.api_key = settings.MARVIN_OPENAI_API_KEY

    post_office_optimization_task = """Union rules at a post office state that each 
        full-time employee must work 5 consecutive days and then receives 2 days off.
        Number of full-time employees required per day:
        Monday: 17, Tuesday: 13, Wednesday: 15, Thursday: 19, Friday: 14, Saturday: 16, Sunday: 11
        Minimize the number of fulltime employees who must be hired.
    """

    post_office_model_str = pyomo_code_snippet(post_office_optimization_task)
    print(post_office_model_str)
    # post_office_model:MaybePyomoLinearOptimizationModel = marvin.extract(post_office_model_str, MaybePyomoLinearOptimizationModel) #extract_pyomo_model(post_office_model_str)
    post_office_model: LinearOptimizationModel = extract_pyomo_model(post_office_optimization_task)
    print(post_office_model.model_dump_json())



#    objective=
# ObjectiveFunction(expr='sum(EmployeeDays[i] for i in range(7))', optimization_sense=<OptimizationSense.minimize: 'minimize'>) sets=[PyomoSet(name='Days', initialize=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])] parameters=[PyomoParameter(name='RequiredEmployees', indexes=['Days'], initialize={'Monday': 17, 'Tuesday': 13, 'Wednesday': 15, 'Thursday': 19, 'Friday': 14, 'Saturday': 16, 'Sunday': 11}, within='NonNegativeIntegers')] vars=[PyomoVar(name='EmployeeDays', domain='Days', within='NonNegativeIntegers')]


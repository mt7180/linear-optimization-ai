from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class ValidationAnswer(BaseModel):
    valid: bool
    reason: Optional[str] = Field(default="", description="explanation, why `valid` is `False` (if it is False)")


class OptimizationSense(Enum):
    maximize = "maximize"
    minimize = "minimize"

class RuleError(Exception):
    pass
    

class Rule(BaseModel):
    lambda_arguments: list[str] = Field(..., description="lambda function arguments")
    lambda_body: str = Field(..., description="lambda function body") #, variables must be attributes of the `model` instance and/ or function arguments")
    

class PyomoSet(BaseModel):
    name: str
    initialize: set[int] = Field(..., description="A list containing the initial members of the Set")
    doc: str = Field(..., description="short description")


class PyomoVar(BaseModel):
    name: str
    index: Optional[str] = Field(..., description="Optional index (a pyomo set name)")
    domain: Optional[str] = Field(...,description="name of a pyomo Set that defines valid values for this var")
   # within: Optional[str] = Field(default=None)
    doc: str = Field(..., description="short description")


class PyomoParam(BaseModel):
    name: str
    indexes: list[str] = Field(...,min_items=1,description="a list of minimum 1 pyomo set name, by which the parameter is indexed.")
    initialize: dict[int,Any] = Field(..., description="data dict for parameter initialization with `index` values as keys.") # or rule: rule is currently not possible
    within: Optional[str]
    doc: str = Field(..., description="short description")

class PyomoConstraint(BaseModel):
    name: str
    idxs: list[str] = Field(...,description="set of required indexes for the constraint expression, if a constraint rule is defined")
    #expr: Optional[str] = Field(default=None, description="constraint expression, variables must be attributes of the `model` instance")
    rule: Rule = Field(..., description="pyomo constraint rule")
    doc: str = Field(..., description="short description")


class ObjectiveFunction(BaseModel):
    indexes: Optional[list[str]] = Field(default=[],description="list of pyomo set names by which parameter is indexed")
    expr: Optional[str] = Field(default="",description="expression for the objective, variables must be attributes of the `model` instance")
    rule: Optional[str] = Field(default="", description="pyomo objective rule")
    optimization_sense: OptimizationSense

class LinearOptimizationModel(BaseModel):
    # summary_string_representation: str = Field(...,description="code snippet of the full pyomo model summarizing the given linear optimization problem")
    objective: ObjectiveFunction = Field(..., description="objective function of the pyomo model")
    sets: list[PyomoSet] = Field(..., description="list of pyomo sets")
    parameters: list[PyomoParam] = Field(..., description="list of indexed pyomo parameters, providing additional data to the pyomo model") # in order to find an optimal assignment of values to the decision variables")
    variables: list[PyomoVar] = Field(..., description="pyomo variables for the pyomo objective/ model")
    constraints: list[PyomoConstraint] = Field(...,description="list of pyomo model constraints, each defined as `pyo.Constraint()'")
    #error_message: str = Field(..., description="Error message, if it is not possible to correctly formulate the pyomo model with the given return type structure")

class MaybeLinearOptimizationModel(BaseModel):
    result: Optional[LinearOptimizationModel] = Field(default=None, description="pyomo linear optimization model")
    error_message: str = Field(..., description="Error message, stating why it is not possible to match the given return type structure of `result` and what is missing")

    def __bool__(self):
        return self.result is not None
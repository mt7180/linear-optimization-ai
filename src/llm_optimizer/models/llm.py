from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class OptimizationSense(Enum):
    maximize = "maximize"
    minimize = "minimize"
    

class PyomoSet(BaseModel):
    name: str
    initialize: list[Any] = Field(..., description="iterable as initial values")
    doc: str = Field(..., description="short description")


class PyomoVar(BaseModel):
    name: str
    index: Optional[str] = Field(description="Optional index (pyomo set name)")
    domain: Optional[str] = Field(...,description="name of a Set that defines valid values for this var")
   # within: Optional[str] = Field(default=None)
    doc: str = Field(..., description="short description")


class PyomoParameter(BaseModel):
    name: str
    indexes: list[str] = Field(...,description="list of pyomo set names by which parameter is indexed")
    initialize: dict = Field(...,description=" dictionary for setting up this parameter") # or rule: rule is currently not possible
    within: str
    doc: str = Field(..., description="short description")

class PyomoConstraint(BaseModel):
    name: str
    idxs: set[str] = Field(..., description="set of required indexes for the constraint expression")
    expr: str = Field(..., description=" constraint expression, variables must be attributes of the `model` object or indexes given in ìdxs field")
    doc: str = Field(..., description="short description")

class ObjectiveFunction(BaseModel):
    expr: str = Field(
        ..., description="pyomo expression for the objective, variables must be attributes of the `model` object",
    )
    optimization_sense: OptimizationSense


class LinearOptimizationModel(BaseModel):
    objective: ObjectiveFunction
    sets: list[PyomoSet]
    parameters: Optional[list[PyomoParameter]] = Field(default=[])
    variables: list[PyomoVar]
    constraints: list[PyomoConstraint] = Field(...,description="")
    error_message: str = Field(..., description="Error message, if it is not possible to correctly formulate the pyomo model with the given return type structure")

class MaybeLinearOptimizationModel(BaseModel):
    result: Optional[LinearOptimizationModel] = Field(default=None, description="pyomo linear optimization model")
    error_message: str = Field(..., description="Error message, if it is not possible to match the given return type structure of `result`")

    def __bool__(self):
        return self.result is not None
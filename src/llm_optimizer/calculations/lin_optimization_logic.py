import logging
import pyomo.environ as pyo
import re

from src.llm_optimizer.models.llm import LinearOptimizationModel
from src.llm_optimizer.utils.helpers import parse_rule


def create_concrete_model():
    return pyo.ConcreteModel()

def create_set(model, name, initialize, doc=''):
    logging.debug(f"creating set {name}")
    setattr(model, name, pyo.Set(initialize=initialize, doc=doc))

def create_var(model, name, index,domain, doc=''):
    setattr(model, name, pyo.Var(get_domain(model, index),domain=get_domain(model, domain), doc=doc))

def create_param(model, name, indexes, initialize, within, doc=''):
    setattr(model, name, pyo.Param(*[get_domain(model, index) for index in indexes], initialize=initialize, within=get_domain(model, within), doc=doc ))

def get_objective_expr(expr_str):
    pattern = r"model\.\w+"
    variables = re.findall(pattern, expr_str)
    return parse_rule(expr_str, variables)

def get_domain(model, domain_str):
    domain_str = str(domain_str)
    allowed_domains = {
        "NonNegativeIntegers": pyo.NonNegativeIntegers,
        "NonNegativeReals":pyo.NonNegativeReals,
        "NonPositiveIntegers":pyo.NonPositiveIntegers,
        "NonPositiveReals":pyo.NonPositiveReals,
        "Integers":pyo.Integers,
        "Reals":pyo.Reals,
    }
    domain = allowed_domains.get(domain_str)
    if not domain:
        domain = getattr(model,domain_str.split(".")[-1], [None])
    return domain

def create_constraint(idx_strs, model, name, rule, doc):
    #todo: implement index
    #model.constraints.add(rule=rule)
    idxs = (getattr(model, "model."+idx) for idx in idx_strs)
    setattr(model, name, pyo.Constraint(*idxs, rule=rule, doc=doc))


def construct_pyomo_model(llm_pyomo_model: LinearOptimizationModel):
    model = create_concrete_model()
    for pyo_set in llm_pyomo_model.sets:
        logging.debug(f"creating set: {pyo_set}")
        create_set(model, *pyo_set.model_dump().values())
    for pyo_var in llm_pyomo_model.variables:
        logging.debug(f"creating var: {pyo_var}")
        create_var(model, *pyo_var.model_dump().values())
    for pyo_param in llm_pyomo_model.parameters:
        logging.debug(f"creating param: {pyo_param}")
        create_param(model, *pyo_param.model_dump().values())
   # model.constraints = pyo.ConstraintList()
    for pyo_constr in llm_pyomo_model.constraints:
        indexes = set(pyo_constr.idxs)
        allowed_vars={"model." +attr.name for attr in model.component_objects()} | {*{comp_key for comp in model.component_objects() for comp_key in comp.keys() if comp_key}} | indexes
        logging.debug(f"creating constraint {pyo_constr.expr} with allowed vars: {allowed_vars}")
        expr = parse_rule(pyo_constr.expr, allowed_vars)
        create_constraint(indexes, model, pyo_constr.name, expr=expr, doc=pyo_constr.doc)
    
    objective_expr = get_objective_expr(llm_pyomo_model.objective.expr)
    objective_sense = pyo.maximize if llm_pyomo_model.objective.optimization_sense == "maximize" else pyo.minimize
    model.objective = pyo.Objective(expr=objective_expr, sense=objective_sense)
    logging.debug(model.pprint())
    return model
    

if __name__ == "__main__":
    import json
    from pathlib import Path
    #llm_output = """{"objective":{"expr":"sum(employees[i] for i in days)","optimization_sense":"minimize"},"sets":[{"name":"days","initialize":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],"doc":"Days of the week"}],"parameters":[],"vars":[{"name":"employees","domain":"NonNegativeIntegers","within":"Reals","doc":"Number of full-time employees starting on each day"}],"constraints":[{"name":"monday_constraint","rule":"employees['Monday'] + employees['Saturday'] + employees['Friday'] + employees['Sunday'] + employees['Thursday'] >= 17","doc":"Monday requirement"},{"name":"tuesday_constraint","rule":"employees['Tuesday'] + employees['Sunday'] + employees['Monday'] + employees['Saturday'] + employees['Friday'] >= 13","doc":"Tuesday requirement"},{"name":"wednesday_constraint","rule":"employees['Wednesday'] + employees['Monday'] + employees['Tuesday'] + employees['Sunday'] + employees['Saturday'] >= 15","doc":"Wednesday requirement"},{"name":"thursday_constraint","rule":"employees['Thursday'] + employees['Tuesday'] + employees['Wednesday'] + employees['Monday'] + employees['Sunday'] >= 19","doc":"Thursday requirement"},{"name":"friday_constraint","rule":"employees['Friday'] + employees['Wednesday'] + employees['Thursday'] + employees['Tuesday'] + employees['Monday'] >= 14","doc":"Friday requirement"},{"name":"saturday_constraint","rule":"employees['Saturday'] + employees['Thursday'] + employees['Friday'] + employees['Wednesday'] + employees['Tuesday'] >= 16","doc":"Saturday requirement"},{"name":"sunday_constraint","rule":"employees['Sunday'] + employees['Friday'] + employees['Saturday'] + employees['Thursday'] + employees['Wednesday'] >= 11","doc":"Sunday requirement"}]}
    #"""

    logging.basicConfig(level=logging.DEBUG)

    cwd = Path(__file__).parent
    with open(cwd / 'mock_llm_response.json', 'r') as file:
        llm_pyomo_model = LinearOptimizationModel(**json.load(file))

    model = construct_pyomo_model(llm_pyomo_model)
    model.pprint()
    optimizer = pyo.SolverFactory('appsi_highs')
    result = optimizer.solve(model)
    result.write()
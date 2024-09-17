import logging
import pyomo.environ as pyo
import re

from llm_optimizer.models.llm import LinearOptimizationModel
from llm_optimizer.utils.helpers import parse_rule
from llm_optimizer.models.llm import RuleError


def create_concrete_model():
    return pyo.ConcreteModel()


def create_set(model, name, initialize, doc=""):
    logging.debug(f"creating set {name}")
    setattr(model, name, pyo.Set(initialize=initialize, doc=doc))


def create_var(model, name, indexes, domain, doc=""):
    setattr(
        model,
        name,
        pyo.Var(
            *[get_index(model, index) for index in (indexes or []) if index],
            domain=get_domain(domain),
            doc=doc,
        ),
    )


def create_param(model, name, indexes, initialize, within, doc=""):
    setattr(
        model,
        name,
        pyo.Param(
            *[get_index(model, index) for index in (indexes or []) if index],
            initialize=initialize,
            within=get_domain(within),
            doc=doc,
        ),
    )


def get_objective_rule(expr_str):
    pattern = r"model\.\w+"
    variables = re.findall(pattern, expr_str)
    return parse_rule(expr_str, variables)


def get_domain(domain_str):
    domain_str = str(domain_str)
    allowed_domains = {
        "NonNegativeIntegers": pyo.NonNegativeIntegers,
        "NonNegativeReals": pyo.NonNegativeReals,
        "NonPositiveIntegers": pyo.NonPositiveIntegers,
        "NonPositiveReals": pyo.NonPositiveReals,
        "Integers": pyo.Integers,
        "Reals": pyo.Reals,
    }
    domain = allowed_domains.get(domain_str)
    return domain


def get_index(model: pyo.ConcreteModel, index_str: str) -> pyo.Set:
    # works also if index_str not with `model.``
    return getattr(model, index_str.split(".")[-1])


def create_constraint(idx_strs, model, name, rule, doc):
    logging.debug(f"creating constraint {idx_strs=} {name}")
    idxs = (getattr(model, idx) for idx in idx_strs)
    setattr(model, name, pyo.Constraint(*idxs, rule=rule["func"], doc=doc))


def construct_pyomo_model(
    llm_pyomo_model: LinearOptimizationModel,
) -> pyo.ConcreteModel:
    model: pyo.ConcreteModel = create_concrete_model()
    for pyo_set in llm_pyomo_model.sets:
        logging.debug(f"creating set: {pyo_set}")
        create_set(model, *pyo_set.model_dump().values())
    for pyo_var in llm_pyomo_model.variables:
        logging.debug(f"creating var: {pyo_var}")
        create_var(model, *pyo_var.model_dump().values())
    for pyo_param in llm_pyomo_model.parameters:
        logging.debug(f"creating param: {pyo_param}")
        create_param(model, *pyo_param.model_dump().values())
    for pyo_constr in llm_pyomo_model.constraints:
        allowed_vars = {"model." + attr.name for attr in model.component_objects()} | {
            *{
                comp_key
                for comp in model.component_objects()
                for comp_key in comp.keys()
                if comp_key
            }
        }

        logging.debug(
            f"creating constraint {pyo_constr.rule} with allowed vars: {allowed_vars}"
        )

        if getattr(pyo_constr, "expr", None):
            rule = parse_rule(pyo_constr.expr, allowed_vars)
            create_constraint([], model, pyo_constr.name, rule=rule, doc=pyo_constr.doc)
        elif getattr(pyo_constr, "rule", None):
            rule_str = (
                "lambda "
                + ", ".join(pyo_constr.rule.lambda_arguments)
                + ": "
                + pyo_constr.rule.lambda_body
            )
            logging.debug("check: " + rule_str + ", " + str(pyo_constr.idxs))
            rule = parse_rule(
                rule_str, allowed_vars | set(pyo_constr.rule.lambda_arguments)
            )
            create_constraint(
                pyo_constr.idxs, model, pyo_constr.name, rule=rule, doc=pyo_constr.doc
            )
        else:
            raise RuleError("Constraint must have either rule or expression.")

    logging.debug(
        f"creating objective {llm_pyomo_model.objective.expr or llm_pyomo_model.objective.rule}"
    )

    if getattr(llm_pyomo_model.objective, "expr", None):
        objective_rule = get_objective_rule(llm_pyomo_model.objective.expr)
    elif getattr(llm_pyomo_model.objective, "rule", None):
        objective_rule = get_objective_rule(llm_pyomo_model.objective.rule)
    else:
        raise RuleError("Objective must have either rule or expression.")

    objective_sense = (
        pyo.maximize
        if llm_pyomo_model.objective.optimization_sense.value == "maximize"
        else pyo.minimize
    )
    model.my_objective = pyo.Objective(
        rule=objective_rule["func"], sense=objective_sense
    )
    # model
    return model


def solve(pyomo_model: pyo.ConcreteModel) -> pyo.ConcreteModel:
    optimizer = pyo.SolverFactory("appsi_highs")
    logging.debug("starting to solve ...")
    results = optimizer.solve(pyomo_model)
    logging.debug(results.write())
    return results, pyomo_model


if __name__ == "__main__":
    import json
    from pathlib import Path

    logging.basicConfig(level=logging.DEBUG)

    cwd = Path(__file__).parent
    with open(cwd / "mock_instructor.json", "r") as file:
        llm_pyomo_model = LinearOptimizationModel(**json.load(file))

    model = construct_pyomo_model(llm_pyomo_model)
    solve(model)
    model.pprint()

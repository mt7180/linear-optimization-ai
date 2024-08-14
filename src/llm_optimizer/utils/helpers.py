import ast
import logging

class ExpressionNotSafeError(Exception):
    pass

def check_if_expression_is_safe(expr, allowed_vars):
    allowed_vars = set(allowed_vars)
    allowed_math_functions = {'sum'}
   
    allowed_node_types = {
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.Eq, ast.Gt, ast.Lt, ast.GtE, ast.LtE, ast.Compare, ast.Call, ast.Tuple, #ast.Load,
        ast.List, ast.Constant, ast.Expr, ast.Attribute, ast.GeneratorExp, 
        ast.comprehension, ast.Subscript, ast.IfExp
    }
    allowed_vars.add('Constraint.Skip')
    iteration_vars = set()

    def _check_node(node):
        if type(node) not in allowed_node_types:
            logging.debug(f"Node type '{type(node)}' not allowed.")
            return False
        
        if isinstance(node, ast.BinOp) or isinstance(node, ast.UnaryOp):
            logging.debug("checking operations ...")
            return _check_node(node.left) and _check_node(node.right)

        if isinstance(node, ast.Call):
            logging.debug(f"checking function calls (e.g., sum): {node.func.value}")
            logging.debug(f"{node.func.id} ...")
            return (
                isinstance(node.func, ast.Name) and
                node.func.id in allowed_math_functions and
                all(_check_node(arg) for arg in node.args)
            )
        
        if isinstance(node, ast.Name):
            logging.debug(f"checking variable: ")
            logging.debug("{node.id}")
            return node.id in allowed_vars or node.id in iteration_vars
        
        if isinstance(node, ast.Attribute):
            logging.debug(f"checking attributes: ")
            full_name = f"{node.value.id}.{node.attr}"
            logging.debug(f" {full_name} ...")
            return full_name in allowed_vars

        if isinstance(node, ast.Constant):
            logging.debug("checking literals: {node.value} ...")
            return  isinstance(node.value, (int, float)) or node.value in allowed_vars
            
        if isinstance(node, ast.Compare):
            logging.debug("checking comparision ...")
            return (
                _check_node(node.left) and
                all(isinstance(op, (ast.Eq, ast.Gt, ast.Lt, ast.GtE, ast.LtE)) for op in node.ops) and
                all(_check_node(comp) for comp in node.comparators)
            )
        
        if isinstance(node, (ast.List, ast.Tuple)):
            logging.debug("checking list and tuple literal ...")
            return all(_check_node(el) for el in node.elts)
        
        if isinstance(node, ast.ListComp) or isinstance(node, ast.GeneratorExp):
            # Gather all iteration variables
            for gen in node.generators:
                if isinstance(gen.target, ast.Name):
                    iteration_vars.add(gen.target.id)
                elif isinstance(gen.target, (ast.Tuple, ast.List)):
                    for elt in gen.target.elts:
                        if isinstance(elt, ast.Name):
                            iteration_vars.add(elt.id)
        
        if isinstance(node, ast.Subscript):
            logging.debug("checking subscripts like x[k] ...")
            return _check_node(node.value) and _check_node(node.slice)
        
       
        if isinstance(node, ast.IfExp):
            logging.debug("checking 'if-else' expressions ...")
            return (
                _check_node(node.test) and
                _check_node(node.body) and
                _check_node(node.orelse)
            )

        return True
    
    try:
    
        ast_tree = ast.parse(expr, mode='eval')
        return _check_node(ast_tree.body)
    except Exception as e:
        print(f"Exception occured while checking the expression: {e}")
        return False

def parse_rule(expression: str, allowed_vars: list[str]):
    """check and eval mathematical expression e.g. for pyomo rule"""
    logging.debug(f"{expression=}, {allowed_vars}")

    if "lambda" in expression:
        expr_left, expr_right = expression.split(":", 1)
        lambda_args = [arg.strip() for arg in expr_left[expr_left.find("lambda")+6:].strip().split(",")]
        expression = expr_right.strip()
    else: lambda_args=["model"]
        
    expression_is_safe = check_if_expression_is_safe(expression, allowed_vars | set(lambda_args))
    if not expression_is_safe:
        raise ExpressionNotSafeError()
    print("set: ", set(lambda_args) - {"model"})
    return {
        "func": eval("lambda " + ",".join(lambda_args) + ":" + expression),
        "idx": set(lambda_args) - {"model"},
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    allowed_vars = {'m.x', 'm.wd', 'm.epsilon', 'd'}
    expression = "sum(m.x[(d+ working_day)%7]  for working_day in m.wd)  >= m.epsilon[d]"

    expression2 = "lambda model, i: sum(model.staff[model.DAYS[(i + j) % 7]] for j in range(5)) >= model.demand[model.DAYS[i]]"
    allowed_vars2 = {"model.DAYS", "model.staff", "model.demand"}

    rule = parse_rule(expression2, allowed_vars2)
    
    print(type(rule))


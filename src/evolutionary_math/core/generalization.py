"""Mathematical generalization, parameter lifting, and theorem subsumption.

Enables the discovery engine to lift concrete numerical target families (e.g. k(k + 110))
into generalized parametric meta-theorems (e.g. k(k + m)), verify them formally for all
parameter values, and subsume infinite concrete instances from flooding the knowledge base.
"""

import re
from typing import Optional, Tuple, Dict, Any, List, Set
import sympy as sp

from evolutionary_math.core.ast import (
    ExprNode,
    OperatorNode,
    VariableNode,
    ConstantNode,
    expr_factory,
    from_sympy,
)
from evolutionary_math.core.canonicalizer import canonicalize


def identify_parameter_variables(expr: ExprNode, bound_vars: Optional[Set[str]] = None) -> List[str]:
    """Identify free parameter variables in an expression.
    
    Parameters apply to:
    1. Parametric summation families (e.g. sum_k=1..n(k*(k+m)) where 'm' is a parameter).
    2. Lifted meta-theorems containing recognized parameter symbols ('c', 'm', 'p')
       alongside problem domain variables ('a', 'b', 'x', 'y', etc.).
    Standard domain variables alone are domain arguments, NOT meta-theoretic parameters.
    """
    # 1. Summation family
    if isinstance(expr, OperatorNode) and expr.op == "sum":
        bound = bound_vars or {"k", "n"}
        return sorted(list(expr.variables - bound))

    # 2. Lifted meta-theorems: recognized parameter symbols combined with domain variables
    PARAM_SYMBOLS = {"m", "c", "p"}
    found_params = expr.variables & PARAM_SYMBOLS
    if found_params and len(expr.variables) > len(found_params):
        return sorted(list(found_params))

    return []


def extract_parametric_family(target: ExprNode) -> Optional[Tuple[ExprNode, str, int]]:
    """Attempt to lift a concrete target containing a numeric offset/scalar into a generalized parametric family.

    Returns:
        (generalized_target, parameter_name, concrete_value) if liftable, else None.
    """
    # 1. Summation Families
    if isinstance(target, OperatorNode) and target.op == "sum":
        term_ast = target.children[0]
        n_ast = target.children[1]

        # 1.1 Pattern: k * (k + C) or (k + C) * k -> k * (k + m)
        if isinstance(term_ast, OperatorNode) and term_ast.op == "*":
            children = [term_ast.children[0], term_ast.children[1]]
            k_child = None
            plus_child = None
            if isinstance(children[0], VariableNode) and children[0].name == "k":
                k_child = children[0]
                plus_child = children[1]
            elif isinstance(children[1], VariableNode) and children[1].name == "k":
                k_child = children[1]
                plus_child = children[0]

            if k_child is not None and isinstance(plus_child, OperatorNode) and plus_child.op == "+":
                p0, p1 = plus_child.children[0], plus_child.children[1]
                c_val = None
                if isinstance(p0, VariableNode) and p0.name == "k" and isinstance(p1, ConstantNode):
                    c_val = int(p1.value)
                elif isinstance(p1, VariableNode) and p1.name == "k" and isinstance(p0, ConstantNode):
                    c_val = int(p0.value)

                if c_val is not None and c_val >= 1:
                    gen_term = expr_factory.op(
                        "*",
                        expr_factory.variable("k"),
                        expr_factory.op("+", expr_factory.variable("k"), expr_factory.variable("m")),
                    )
                    return expr_factory.op("sum", gen_term, n_ast), "m", c_val

        # 1.2 Pattern: (k + C) or (C + k) -> (k + m)
        if isinstance(term_ast, OperatorNode) and term_ast.op == "+":
            p0, p1 = term_ast.children[0], term_ast.children[1]
            c_val = None
            if isinstance(p0, VariableNode) and p0.name == "k" and isinstance(p1, ConstantNode):
                c_val = int(p1.value)
            elif isinstance(p1, VariableNode) and p1.name == "k" and isinstance(p0, ConstantNode):
                c_val = int(p0.value)

            if c_val is not None and c_val >= 1:
                gen_term = expr_factory.op("+", expr_factory.variable("k"), expr_factory.variable("m"))
                return expr_factory.op("sum", gen_term, n_ast), "m", c_val

        # 1.3 Pattern: C * k or k * C (for C > 2) -> c * k
        if isinstance(term_ast, OperatorNode) and term_ast.op == "*":
            p0, p1 = term_ast.children[0], term_ast.children[1]
            c_val = None
            if isinstance(p0, ConstantNode) and isinstance(p1, VariableNode) and p1.name == "k":
                c_val = int(p0.value)
            elif isinstance(p1, ConstantNode) and isinstance(p0, VariableNode) and p0.name == "k":
                c_val = int(p1.value)

            if c_val is not None and c_val > 2:
                gen_term = expr_factory.op("*", expr_factory.variable("c"), expr_factory.variable("k"))
                return expr_factory.op("sum", gen_term, n_ast), "c", c_val

        return None

    # 2. Algebraic Scalar Multiple Family: C * var or var * C (for C >= 3) -> c * var
    if isinstance(target, OperatorNode) and target.op == "*":
        p0, p1 = target.children[0], target.children[1]
        c_val = None
        var_node = None
        if isinstance(p0, ConstantNode) and isinstance(p1, VariableNode):
            c_val = int(p0.value)
            var_node = p1
        elif isinstance(p1, ConstantNode) and isinstance(p0, VariableNode):
            c_val = int(p1.value)
            var_node = p0

        if c_val is not None and c_val >= 3 and var_node is not None:
            gen_target = expr_factory.op("*", expr_factory.variable("c"), var_node)
            return gen_target, "c", c_val

    # 3. Algebraic Power Family: var ^ C (for C >= 3) -> var ^ p
    if isinstance(target, OperatorNode) and target.op == "^":
        base, exp = target.children[0], target.children[1]
        if isinstance(base, VariableNode) and isinstance(exp, ConstantNode):
            c_val = int(exp.value)
            if c_val >= 3:
                gen_target = expr_factory.op("^", base, expr_factory.variable("p"))
                return gen_target, "p", c_val

    return None


def find_subsumption_match(
    concrete_target: ExprNode,
    general_target: ExprNode,
    param_vars: List[str],
) -> Optional[Dict[str, Any]]:
    """Test if concrete_target is an instance of general_target by matching parameter variables.

    Returns the substitution dictionary (e.g. {'m': 110}) if concrete_target is subsumed, else None.
    """
    if not param_vars:
        return None

    try:
        # Top-level AST structural gate: mismatched operators cannot subsume each other
        if isinstance(concrete_target, OperatorNode) and isinstance(general_target, OperatorNode):
            if concrete_target.op != general_target.op:
                return None

        sp_concrete = concrete_target.to_sympy()
        sp_gen = general_target.to_sympy()

        # Both must agree on mathematical category (e.g. Sum vs algebraic expression)
        if isinstance(sp_concrete, sp.Sum) != isinstance(sp_gen, sp.Sum):
            return None

        # Construct SymPy Wild patterns for all parameter variables
        wild_map = {p: sp.Wild(p, exclude=[sp.Symbol("k"), sp.Symbol("n")]) for p in param_vars}
        
        # Replace parameter symbols in general target with Wilds
        sp_pattern = sp_gen.subs({sp.Symbol(p): wild_map[p] for p in param_vars})

        # Match against concrete target
        matched = sp_concrete.match(sp_pattern)
        if matched is None:
            # Also try matching on inner summation terms if both are Sums
            if isinstance(sp_concrete, sp.Sum) and isinstance(sp_pattern, sp.Sum):
                matched = sp_concrete.args[0].match(sp_pattern.args[0])

        if matched is not None:
            # Validate that every parameter variable was assigned a valid CONSTANT value
            extracted: Dict[str, Any] = {}
            for p in param_vars:
                w = wild_map[p]
                if w in matched:
                    val = matched[w]
                    # Ensure wild was not left unbounded
                    if any(isinstance(a, sp.Wild) for a in sp.preorder_traversal(val)):
                        continue
                    # Parameter substitutions must be pure constants, never expressions of free variables
                    if hasattr(val, "free_symbols") and len(val.free_symbols) > 0:
                        continue
                    if hasattr(val, "is_Integer") and val.is_Integer:
                        extracted[p] = int(val)
                    elif hasattr(val, "is_number") and val.is_number:
                        extracted[p] = float(val)
                    elif not getattr(val, "free_symbols", None):
                        extracted[p] = val

            if len(extracted) == len(param_vars):
                return extracted

    except Exception:
        pass

    return None


def instantiate_generalized_formula(
    general_formula: ExprNode,
    parameter_substitution: Dict[str, Any],
) -> ExprNode:
    """Instantiate a generalized parametric formula with concrete parameter values."""
    sp_f = general_formula.to_sympy()
    sub_dict = {sp.Symbol(k): v for k, v in parameter_substitution.items()}
    sp_concrete = sp_f.subs(sub_dict)
    sp_factored = sp.factor(sp_concrete)
    return canonicalize(from_sympy(sp_factored))

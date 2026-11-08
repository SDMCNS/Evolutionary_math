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
    """Identify free parameter variables in an expression (excluding bound indices like 'k' and 'n')."""
    bound = bound_vars or {"k", "n"}
    return sorted(list(expr.variables - bound))


def extract_parametric_family(target: ExprNode) -> Optional[Tuple[ExprNode, str, int]]:
    """Attempt to lift a concrete target containing a numeric offset/scalar into a generalized parametric family.

    Returns:
        (generalized_target, parameter_name, concrete_value) if liftable, else None.
    """
    if not (isinstance(target, OperatorNode) and target.op == "sum"):
        return None

    term_ast = target.children[0]
    n_ast = target.children[1]

    # 1. Pattern: k * (k + C) or (k + C) * k -> k * (k + m)
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

    # 2. Pattern: (k + C) or (C + k) -> (k + m)
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

    # 3. Pattern: C * k or k * C (for C > 2) -> c * k
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
        sp_concrete = concrete_target.to_sympy()
        sp_gen = general_target.to_sympy()

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
            # Validate that every parameter variable was assigned a valid value
            extracted: Dict[str, Any] = {}
            for p in param_vars:
                w = wild_map[p]
                if w in matched:
                    val = matched[w]
                    # Ensure wild was not left unbounded
                    if not any(isinstance(a, sp.Wild) for a in sp.preorder_traversal(val)):
                        if hasattr(val, "is_Integer") and val.is_Integer:
                            extracted[p] = int(val)
                        elif hasattr(val, "is_number") and val.is_number:
                            extracted[p] = float(val)
                        else:
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

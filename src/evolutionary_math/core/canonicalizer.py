"""Expression canonicalizer, constant folder, and triviality detector."""

from fractions import Fraction
from typing import Union
from evolutionary_math.core.types import MathType
from evolutionary_math.core.ast import ExprNode, ConstantNode, VariableNode, OperatorNode, LemmaNode, SequenceTermNode, expr_factory
from evolutionary_math.core.operators import OperatorRegistry


def _is_const_val(node: ExprNode, val: Union[int, float]) -> bool:
    """Check if node is a ConstantNode with exact value val."""
    if isinstance(node, ConstantNode):
        return node.value == val
    return False


def canonicalize(expr: ExprNode) -> ExprNode:
    """Recursively canonicalize an expression.

    Applies:
    1. Bottom-up child canonicalization
    2. Constant folding
    3. Algebraic identity simplification (x+0 -> x, x*0 -> 0, x-x -> 0, etc.)
    4. Commutative canonical ordering (ensuring (x + 1) == (1 + x))
    """
    if isinstance(expr, (ConstantNode, VariableNode)):
        return expr

    if isinstance(expr, LemmaNode):
        canon_arg = canonicalize(expr.arg)
        if expr.definition is not None:
            canon_def = canonicalize(expr.definition)
            if isinstance(canon_def, VariableNode):
                # Identity function f(x) = x -> directly unwrap to canon_arg!
                return canon_arg
            elif isinstance(canon_def, ConstantNode):
                # Constant function f(x) = c -> directly unwrap to constant c!
                return canon_def
            return expr_factory.lemma(expr.lemma_id, canon_arg, canon_def, expr.math_type)
        return expr_factory.lemma(expr.lemma_id, canon_arg, expr.definition, expr.math_type)

    if isinstance(expr, SequenceTermNode):
        canon_idx = canonicalize(expr.index_expr)
        return expr_factory.seq_term(expr.seq_name, canon_idx, expr.math_type)

    if isinstance(expr, OperatorNode):
        # 1. Canonicalize all children first
        canon_children = tuple(canonicalize(c) for c in expr.children)

        # 2. Check for complete constant folding
        if all(isinstance(c, ConstantNode) for c in canon_children):
            try:
                env = {}
                res = expr.eval_numerical(env)
                if isinstance(res, (int, float, Fraction)):
                    if isinstance(res, float) and res.is_integer():
                        res = int(res)
                    return expr_factory.constant(res)
            except Exception:
                pass  # Fallback to symbolic simplification

        op = expr.op

        # 3. Algebraic identities
        if op == "+":
            left, right = canon_children
            if _is_const_val(left, 0):
                return right
            if _is_const_val(right, 0):
                return left
            # Associative constant folding: (A + c1) + c2 -> A + (c1 + c2)
            if isinstance(left, OperatorNode) and left.op == "+" and isinstance(left.children[1], ConstantNode) and isinstance(right, ConstantNode):
                new_const = expr_factory.constant(left.children[1].value + right.value)
                return canonicalize(expr_factory.op("+", left.children[0], new_const))
            # Commutative canonical sorting: ensure deterministic ordering
            if OperatorRegistry.is_commutative(op):
                if _node_sort_key(left) > _node_sort_key(right):
                    left, right = right, left
            return expr_factory.op("+", left, right)

        elif op == "-":
            left, right = canon_children
            if left == right:
                return expr_factory.constant(0)
            if _is_const_val(right, 0):
                return left
            if _is_const_val(left, 0):
                return expr_factory.op("neg", right)
            return expr_factory.op("-", left, right)

        elif op == "*":
            left, right = canon_children
            if _is_const_val(left, 0) or _is_const_val(right, 0):
                return expr_factory.constant(0)
            if _is_const_val(left, 1):
                return right
            if _is_const_val(right, 1):
                return left
            # Associative constant folding: (A * c1) * c2 -> A * (c1 * c2)
            if isinstance(left, OperatorNode) and left.op == "*" and isinstance(left.children[1], ConstantNode) and isinstance(right, ConstantNode):
                new_const = expr_factory.constant(left.children[1].value * right.value)
                return canonicalize(expr_factory.op("*", left.children[0], new_const))
            # Commutative canonical sorting
            if OperatorRegistry.is_commutative(op):
                if _node_sort_key(left) > _node_sort_key(right):
                    left, right = right, left
            return expr_factory.op("*", left, right)

        elif op == "/":
            left, right = canon_children
            if _is_const_val(left, 0) and not _is_const_val(right, 0):
                return expr_factory.constant(0)
            if _is_const_val(right, 1):
                return left
            if left == right:
                return expr_factory.constant(1)
            return expr_factory.op("/", left, right)

        elif op == "^":
            base, exp = canon_children
            if _is_const_val(exp, 0):
                return expr_factory.constant(1)
            if _is_const_val(exp, 1):
                return base
            if _is_const_val(base, 1):
                return expr_factory.constant(1)
            if _is_const_val(base, 0) and isinstance(exp, ConstantNode) and exp.value > 0:
                return expr_factory.constant(0)
            return expr_factory.op("^", base, exp)

        elif op == "neg":
            child = canon_children[0]
            if _is_const_val(child, 0):
                return expr_factory.constant(0)
            if isinstance(child, OperatorNode) and child.op == "neg":
                return child.children[0]
            return expr_factory.op("neg", child)

        elif op == "sum":
            term, upper = canon_children
            # sum_k=1..n(0) -> 0
            if _is_const_val(term, 0):
                return expr_factory.constant(0)
            return expr_factory.op("sum", term, upper)

        elif op == "sin":
            child = canon_children[0]
            if _is_const_val(child, 0):
                return expr_factory.constant(0)
            return expr_factory.op("sin", child)

        elif op == "cos":
            child = canon_children[0]
            if _is_const_val(child, 0):
                return expr_factory.constant(1)
            return expr_factory.op("cos", child)

        elif op == "tan":
            child = canon_children[0]
            if _is_const_val(child, 0):
                return expr_factory.constant(0)
            return expr_factory.op("tan", child)

        elif op == "sqrt":
            child = canon_children[0]
            if _is_const_val(child, 0):
                return expr_factory.constant(0)
            if _is_const_val(child, 1):
                return expr_factory.constant(1)
            return expr_factory.op("sqrt", child)

        elif op == "abs":
            child = canon_children[0]
            if _is_const_val(child, 0):
                return expr_factory.constant(0)
            return expr_factory.op("abs", child)

        return expr_factory.op(op, *canon_children)

    return expr


def _node_sort_key(node: ExprNode) -> tuple:
    """Sort key for canonical commutative ordering (variables and operators before constants)."""
    if isinstance(node, VariableNode):
        return (0, node.name)
    elif isinstance(node, LemmaNode):
        return (1, node.lemma_id)
    elif isinstance(node, OperatorNode):
        return (2, node.op, node.node_count, str(node))
    elif isinstance(node, ConstantNode):
        return (3, str(node.value))
    return (4, str(node))


def is_trivial_tautology(lhs: ExprNode, rhs: ExprNode) -> bool:
    """Check if the conjectured relationship LHS = RHS is a trivial tautology.

    A tautology occurs when:
    1. Canonicalized LHS is structurally identical to canonicalized RHS (e.g. x = x, x+1 = 1+x).
    2. The difference canonicalizes to 0.
    """
    canon_l = canonicalize(lhs)
    canon_r = canonicalize(rhs)

    if canon_l == canon_r:
        return True

    # Check (lhs - rhs)
    diff = canonicalize(expr_factory.op("-", canon_l, canon_r))
    if isinstance(diff, ConstantNode) and diff.value == 0:
        return True

    return False


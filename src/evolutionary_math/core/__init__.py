"""Core mathematical representations and AST structures."""

from evolutionary_math.core.types import MathType
from evolutionary_math.core.ast import ExprNode, ConstantNode, VariableNode, OperatorNode, LemmaNode, expr_factory, expr_from_dict
from evolutionary_math.core.operators import OperatorRegistry, OpSignature
from evolutionary_math.core.canonicalizer import canonicalize, is_trivial_tautology

__all__ = [
    "MathType",
    "ExprNode",
    "ConstantNode",
    "VariableNode",
    "OperatorNode",
    "LemmaNode",
    "expr_factory",
    "expr_from_dict",
    "OperatorRegistry",
    "OpSignature",
    "canonicalize",
    "is_trivial_tautology",
]


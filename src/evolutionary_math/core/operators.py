"""Operator signatures, properties, and registry."""

from dataclasses import dataclass
from typing import Callable, Tuple, Optional
from evolutionary_math.core.types import MathType


@dataclass(frozen=True)
class OpSignature:
    """Signature and algebraic properties of an operator."""
    symbol: str
    arity: int
    arg_types: Tuple[MathType, ...]
    return_type: MathType
    is_commutative: bool = False
    is_associative: bool = False
    identity_element: Optional[float] = None
    absorbing_element: Optional[float] = None


class OperatorRegistry:
    """Registry of standard mathematical operators."""

    _OPERATORS = {
        "+": OpSignature(
            symbol="+",
            arity=2,
            arg_types=(MathType.REAL, MathType.REAL),
            return_type=MathType.REAL,
            is_commutative=True,
            is_associative=True,
            identity_element=0.0,
        ),
        "-": OpSignature(
            symbol="-",
            arity=2,
            arg_types=(MathType.REAL, MathType.REAL),
            return_type=MathType.REAL,
            is_commutative=False,
            is_associative=False,
        ),
        "*": OpSignature(
            symbol="*",
            arity=2,
            arg_types=(MathType.REAL, MathType.REAL),
            return_type=MathType.REAL,
            is_commutative=True,
            is_associative=True,
            identity_element=1.0,
            absorbing_element=0.0,
        ),
        "/": OpSignature(
            symbol="/",
            arity=2,
            arg_types=(MathType.REAL, MathType.REAL),
            return_type=MathType.RATIONAL,
            is_commutative=False,
            is_associative=False,
        ),
        "^": OpSignature(
            symbol="^",
            arity=2,
            arg_types=(MathType.REAL, MathType.INTEGER),
            return_type=MathType.REAL,
            is_commutative=False,
            is_associative=False,
        ),
        "neg": OpSignature(
            symbol="neg",
            arity=1,
            arg_types=(MathType.REAL,),
            return_type=MathType.REAL,
        ),
        "sum": OpSignature(
            symbol="sum",
            arity=2,  # (term_expr, upper_bound_expr), implicit lower bound = 1 over variable 'k'
            arg_types=(MathType.REAL, MathType.INTEGER),
            return_type=MathType.REAL,
        ),
        "sin": OpSignature(
            symbol="sin",
            arity=1,
            arg_types=(MathType.REAL,),
            return_type=MathType.REAL,
        ),
        "cos": OpSignature(
            symbol="cos",
            arity=1,
            arg_types=(MathType.REAL,),
            return_type=MathType.REAL,
        ),
        "tan": OpSignature(
            symbol="tan",
            arity=1,
            arg_types=(MathType.REAL,),
            return_type=MathType.REAL,
        ),
        "sqrt": OpSignature(
            symbol="sqrt",
            arity=1,
            arg_types=(MathType.REAL,),
            return_type=MathType.REAL,
        ),
        "abs": OpSignature(
            symbol="abs",
            arity=1,
            arg_types=(MathType.REAL,),
            return_type=MathType.REAL,
        ),
    }

    @classmethod
    def get(cls, symbol: str) -> OpSignature:
        if symbol not in cls._OPERATORS:
            raise KeyError(f"Operator '{symbol}' not recognized.")
        return cls._OPERATORS[symbol]

    @classmethod
    def register(cls, signature: OpSignature) -> None:
        cls._OPERATORS[signature.symbol] = signature

    @classmethod
    def is_commutative(cls, symbol: str) -> bool:
        op = cls._OPERATORS.get(symbol)
        return op.is_commutative if op else False

    @classmethod
    def is_associative(cls, symbol: str) -> bool:
        op = cls._OPERATORS.get(symbol)
        return op.is_associative if op else False


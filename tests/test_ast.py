"""Unit tests for AST and DAG representations."""

import numpy as np
from fractions import Fraction
import sympy as sp

from evolutionary_math.core.ast import (
    ConstantNode,
    VariableNode,
    OperatorNode,
    expr_factory,
)
from evolutionary_math.core.types import MathType


def test_constant_node_creation():
    c1 = expr_factory.constant(5)
    assert isinstance(c1, ConstantNode)
    assert c1.value == 5
    assert c1.math_type == MathType.INTEGER
    assert c1.eval_numerical({}) == 5
    assert c1.to_sympy() == sp.Integer(5)
    assert c1.to_sexpr() == "5"


def test_variable_node_creation():
    v = expr_factory.variable("n", MathType.INTEGER)
    assert isinstance(v, VariableNode)
    assert v.name == "n"
    assert v.eval_numerical({"n": 10}) == 10
    assert v.variables == frozenset(["n"])


def test_dag_maximal_sharing():
    """Ensure identical subexpressions share the exact same object reference."""
    expr_factory.clear()
    n1 = expr_factory.variable("n")
    n2 = expr_factory.variable("n")
    assert n1 is n2

    c1 = expr_factory.constant(42)
    c2 = expr_factory.constant(42)
    assert c1 is c2

    # (n + 42)
    sum1 = expr_factory.op("+", n1, c1)
    sum2 = expr_factory.op("+", n2, c2)
    assert sum1 is sum2


def test_numerical_vectorized_evaluation():
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)
    # expr = (n * (n + 1)) / 2
    n_plus_1 = expr_factory.op("+", n, one)
    prod = expr_factory.op("*", n, n_plus_1)
    triangular = expr_factory.op("/", prod, two)

    vec = np.array([1, 2, 3, 4, 5])
    res = triangular.eval_numerical({"n": vec})
    expected = np.array([1.0, 3.0, 6.0, 10.0, 15.0])
    np.testing.assert_allclose(res, expected)


def test_summation_operator():
    k = expr_factory.variable("k")
    n = expr_factory.variable("n")
    # sum_{k=1}^n (k)
    sum_expr = expr_factory.op("sum", k, n)

    assert sum_expr.eval_numerical({"n": 1}) == 1
    assert sum_expr.eval_numerical({"n": 4}) == 10
    assert sum_expr.eval_numerical({"n": 10}) == 55

    # Vectorized evaluation
    res = sum_expr.eval_numerical({"n": np.array([1, 2, 3, 4])})
    np.testing.assert_allclose(res, np.array([1.0, 3.0, 6.0, 10.0]))


def test_from_sympy_and_parse_expr_str():
    from evolutionary_math.core.ast import from_sympy, parse_expr_str

    # Test polynomial parsing
    node = parse_expr_str("n * (n + 1) * (2*n + 1) / 6")
    sp_expr = node.to_sympy()
    expected = sp.sympify("n * (n + 1) * (2*n + 1) / 6")
    assert sp.simplify(sp_expr - expected) == 0

    # Test numerical evaluation
    val = node.eval_numerical({"n": 4})
    assert val == 30.0  # 1^2 + 2^2 + 3^2 + 4^2 = 1 + 4 + 9 + 16 = 30

    # Test powers and subtractions
    node2 = parse_expr_str("2*k - 1")
    assert node2.eval_numerical({"k": 3}) == 5



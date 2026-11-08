"""Unit tests for expression canonicalization and triviality detection."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.core.canonicalizer import canonicalize, is_trivial_tautology


def test_constant_folding():
    c1 = expr_factory.constant(1)
    c2 = expr_factory.constant(2)
    # (1 + 2) -> 3
    add_node = expr_factory.op("+", c1, c2)
    canon = canonicalize(add_node)
    assert canon.value == 3

    # (2 * 5) -> 10
    c5 = expr_factory.constant(5)
    mul_node = expr_factory.op("*", c2, c5)
    assert canonicalize(mul_node).value == 10

    # (2 ^ 3) -> 8
    c3 = expr_factory.constant(3)
    pow_node = expr_factory.op("^", c2, c3)
    assert canonicalize(pow_node).value == 8


def test_algebraic_identity_simplifications():
    x = expr_factory.variable("x")
    zero = expr_factory.constant(0)
    one = expr_factory.constant(1)

    # x + 0 -> x
    assert canonicalize(expr_factory.op("+", x, zero)) == x
    assert canonicalize(expr_factory.op("+", zero, x)) == x

    # x * 0 -> 0
    assert canonicalize(expr_factory.op("*", x, zero)).value == 0
    assert canonicalize(expr_factory.op("*", zero, x)).value == 0

    # x * 1 -> x
    assert canonicalize(expr_factory.op("*", x, one)) == x

    # x - x -> 0
    assert canonicalize(expr_factory.op("-", x, x)).value == 0

    # x / 1 -> x
    assert canonicalize(expr_factory.op("/", x, one)) == x

    # x ^ 1 -> x, x ^ 0 -> 1
    assert canonicalize(expr_factory.op("^", x, one)) == x
    assert canonicalize(expr_factory.op("^", x, zero)).value == 1


def test_commutative_canonical_sorting():
    x = expr_factory.variable("x")
    one = expr_factory.constant(1)

    # (x + 1) vs (1 + x)
    expr1 = canonicalize(expr_factory.op("+", x, one))
    expr2 = canonicalize(expr_factory.op("+", one, x))
    assert expr1 == expr2
    assert expr1 is expr2


def test_trivial_tautology_detector():
    x = expr_factory.variable("x")
    one = expr_factory.constant(1)

    # x == x is trivial
    assert is_trivial_tautology(x, x)

    # x + 1 == 1 + x is trivial
    e1 = expr_factory.op("+", x, one)
    e2 = expr_factory.op("+", one, x)
    assert is_trivial_tautology(e1, e2)

    # x + 0 == x is trivial
    zero = expr_factory.constant(0)
    e3 = expr_factory.op("+", x, zero)
    assert is_trivial_tautology(e3, x)

    # Non-trivial: sum(k, n) == n*(n+1)/2 is NOT a trivial tautology
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    sum_k = expr_factory.op("sum", k, n)
    triangular = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), expr_factory.constant(2))
    assert not is_trivial_tautology(sum_k, triangular)


def test_identity_lemma_unwrapping():
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    # L_id has definition: n (identity function)
    lemma_id = expr_factory.lemma("L_ident", expr_factory.op("+", n, one), n)
    canon = canonicalize(lemma_id)
    # Should unwrap L_ident(n + 1) directly to (n + 1)!
    assert str(canon) == "(n + 1)"
    assert canon == expr_factory.op("+", n, one)


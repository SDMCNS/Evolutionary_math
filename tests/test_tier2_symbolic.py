"""Unit tests for Tier 2 deterministic symbolic verification."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evaluation.tier2_symbolic import Tier2SymbolicVerifier


def test_algebraic_zero_equivalence():
    verifier = Tier2SymbolicVerifier()
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    # (n + 1)^2
    lhs = expr_factory.op("^", expr_factory.op("+", n, one), two)

    # n^2 + 2n + 1
    n_squared = expr_factory.op("^", n, two)
    two_n = expr_factory.op("*", two, n)
    rhs = expr_factory.op("+", expr_factory.op("+", n_squared, two_n), one)

    res = verifier.verify(lhs, rhs)
    assert res.is_verified
    assert res.proof_method == "algebraic_zero_equivalence"
    assert res.runtime_ms < 50.0


def test_faulhaber_degree_1_induction():
    """Verify sum_{k=1}^n (k) = n*(n+1)/2 via induction."""
    verifier = Tier2SymbolicVerifier()
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    sum_k = expr_factory.op("sum", k, n)
    rhs = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two)

    res = verifier.verify(sum_k, rhs)
    assert res.is_verified
    assert "induction" in res.proof_method
    assert res.runtime_ms < 50.0


def test_faulhaber_degree_2_induction():
    """Verify sum_{k=1}^n (k^2) = n*(n+1)*(2n+1)/6 via induction."""
    verifier = Tier2SymbolicVerifier()
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)
    six = expr_factory.constant(6)

    k_squared = expr_factory.op("^", k, two)
    sum_k2 = expr_factory.op("sum", k_squared, n)

    # n * (n + 1) * (2*n + 1) / 6
    factor1 = n
    factor2 = expr_factory.op("+", n, one)
    factor3 = expr_factory.op("+", expr_factory.op("*", two, n), one)
    numerator = expr_factory.op("*", expr_factory.op("*", factor1, factor2), factor3)
    rhs = expr_factory.op("/", numerator, six)

    res = verifier.verify(sum_k2, rhs)
    assert res.is_verified
    assert "induction" in res.proof_method
    assert res.runtime_ms < 50.0


def test_telescoping_rational_sum_induction():
    """Verify sum_{k=1}^n (1 / (k*(k+1))) = n / (n + 1) via induction."""
    verifier = Tier2SymbolicVerifier()
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)

    # Term: 1 / (k * (k + 1))
    k_plus_1 = expr_factory.op("+", k, one)
    denom = expr_factory.op("*", k, k_plus_1)
    term = expr_factory.op("/", one, denom)
    sum_telescoping = expr_factory.op("sum", term, n)

    # RHS: n / (n + 1)
    n_plus_1 = expr_factory.op("+", n, one)
    rhs = expr_factory.op("/", n, n_plus_1)

    res = verifier.verify(sum_telescoping, rhs)
    assert res.is_verified
    assert "induction" in res.proof_method
    assert res.runtime_ms < 50.0


def test_invalid_summation_rejection():
    """Ensure invalid formulas are not verified."""
    verifier = Tier2SymbolicVerifier()
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    two = expr_factory.constant(2)

    sum_k = expr_factory.op("sum", k, n)
    # false rhs: n^2
    rhs = expr_factory.op("^", n, two)

    res = verifier.verify(sum_k, rhs)
    assert not res.is_verified


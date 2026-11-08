"""Unit tests for Tier 1 fast numerical falsification."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evaluation.tier1_numerical import Tier1NumericalEvaluator


def test_tier1_falsification_speed_and_accuracy():
    evaluator = Tier1NumericalEvaluator()

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    sum_k = expr_factory.op("sum", k, n)

    # True identity: sum_k = n*(n+1)/2
    true_rhs = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two)
    res_true = evaluator.evaluate(sum_k, true_rhs)

    assert not res_true.is_falsified
    assert res_true.score == 1.0
    assert res_true.max_residual == 0.0
    assert res_true.runtime_ms < 5.0  # Runs in single-digit ms

    # False identity: sum_k = n^2
    false_rhs = expr_factory.op("^", n, two)
    res_false = evaluator.evaluate(sum_k, false_rhs)

    assert res_false.is_falsified
    assert res_false.max_residual > 0
    assert res_false.score < 0.8
    assert res_false.runtime_ms < 5.0


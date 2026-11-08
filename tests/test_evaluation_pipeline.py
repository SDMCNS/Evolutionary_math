"""Unit tests for the end-to-end cascading evaluation pipeline."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evaluation.pipeline import EvaluationPipeline, EvaluationStatus


def test_pipeline_rejects_trivial_tautologies():
    pipeline = EvaluationPipeline()
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)

    # n + 1 == 1 + n
    lhs = expr_factory.op("+", n, one)
    rhs = expr_factory.op("+", one, n)

    res = pipeline.evaluate(lhs, rhs)
    assert res.status == EvaluationStatus.REJECTED_TRIVIAL
    assert not res.is_verified
    assert res.fitness_score == 0.0


def test_pipeline_halts_at_tier1_for_falsified_candidate():
    pipeline = EvaluationPipeline()
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    two = expr_factory.constant(2)

    sum_k = expr_factory.op("sum", k, n)
    wrong_rhs = expr_factory.op("^", n, two)

    res = pipeline.evaluate(sum_k, wrong_rhs)
    assert res.status == EvaluationStatus.FALSIFIED
    assert not res.is_verified
    assert res.tier1_result is not None
    assert res.tier2_result is None  # Tier 2 was never executed, saving compute!
    assert res.total_runtime_ms < 10.0


def test_pipeline_verifies_true_identity():
    pipeline = EvaluationPipeline()
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    sum_k = expr_factory.op("sum", k, n)
    true_rhs = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two)

    res = pipeline.evaluate(sum_k, true_rhs)
    assert res.status == EvaluationStatus.SYMBOLICALLY_VERIFIED
    assert res.is_verified
    assert res.fitness_score == 1.0
    assert res.proof_method is not None
    assert res.tier1_result is not None
    assert res.tier2_result is not None
    assert res.total_runtime_ms < 150.0  # Entire cascading verification under 150 ms (including cold start)

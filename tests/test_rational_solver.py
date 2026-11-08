"""Unit tests for ExactPolynomialSolver finite difference detection."""

import pytest
from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evolution.rational_solver import ExactPolynomialSolver
from evolutionary_math.evaluation.pipeline import EvaluationPipeline


def test_solve_sum_k():
    k = expr_factory.variable("k")
    n = expr_factory.variable("n")
    target = expr_factory.op("sum", k, n)

    cands = ExactPolynomialSolver.solve(target)
    assert len(cands) > 0

    pipeline = EvaluationPipeline()
    res = pipeline.evaluate(cands[0], target)
    assert res.is_verified


def test_solve_sum_k_squared():
    k = expr_factory.variable("k")
    n = expr_factory.variable("n")
    k_sq = expr_factory.op("^", k, expr_factory.constant(2))
    target = expr_factory.op("sum", k_sq, n)

    cands = ExactPolynomialSolver.solve(target)
    assert len(cands) > 0

    pipeline = EvaluationPipeline()
    verified_any = False
    for cand in cands:
        res = pipeline.evaluate(cand, target)
        if res.is_verified:
            verified_any = True
            break
    assert verified_any


def test_solve_sum_odd():
    k = expr_factory.variable("k")
    n = expr_factory.variable("n")
    odd = expr_factory.op("-", expr_factory.op("*", expr_factory.constant(2), k), expr_factory.constant(1))
    target = expr_factory.op("sum", odd, n)

    cands = ExactPolynomialSolver.solve(target)
    assert len(cands) > 0
    pipeline = EvaluationPipeline()
    res = pipeline.evaluate(cands[0], target)
    assert res.is_verified


def test_non_polynomial_target_returns_empty():
    k = expr_factory.variable("k")
    n = expr_factory.variable("n")
    # 1/(k*(k+1)) is non-polynomial
    term = expr_factory.op("/", expr_factory.constant(1), expr_factory.op("*", k, expr_factory.op("+", k, expr_factory.constant(1))))
    target = expr_factory.op("sum", term, n)

    cands = ExactPolynomialSolver.solve(target)
    assert len(cands) == 0


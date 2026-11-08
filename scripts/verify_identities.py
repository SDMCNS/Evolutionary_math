"""Demonstrator script showcasing Phase 0 deterministic verification pipeline on core mathematical identities."""

import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import time
from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evaluation.pipeline import EvaluationPipeline


def run_benchmark():
    pipeline = EvaluationPipeline()

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)
    six = expr_factory.constant(6)
    four = expr_factory.constant(4)

    benchmarks = [
        (
            "Trivial Tautology (Anti-Triviality Check)",
            expr_factory.op("+", n, one),
            expr_factory.op("+", one, n),
        ),
        (
            "Faulhaber Degree 1: sum_{k=1}^n k = n(n+1)/2",
            expr_factory.op("sum", k, n),
            expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two),
        ),
        (
            "Faulhaber Degree 2: sum_{k=1}^n k^2 = n(n+1)(2n+1)/6",
            expr_factory.op("sum", expr_factory.op("^", k, two), n),
            expr_factory.op(
                "/",
                expr_factory.op(
                    "*",
                    expr_factory.op("*", n, expr_factory.op("+", n, one)),
                    expr_factory.op("+", expr_factory.op("*", two, n), one),
                ),
                six,
            ),
        ),
        (
            "Faulhaber Degree 3: sum_{k=1}^n k^3 = [n(n+1)/2]^2 = n^2(n+1)^2/4",
            expr_factory.op("sum", expr_factory.op("^", k, expr_factory.constant(3)), n),
            expr_factory.op(
                "/",
                expr_factory.op(
                    "*",
                    expr_factory.op("^", n, two),
                    expr_factory.op("^", expr_factory.op("+", n, one), two),
                ),
                four,
            ),
        ),
        (
            "Telescoping Rational Sum: sum_{k=1}^n 1/(k(k+1)) = n/(n+1)",
            expr_factory.op("sum", expr_factory.op("/", one, expr_factory.op("*", k, expr_factory.op("+", k, one))), n),
            expr_factory.op("/", n, expr_factory.op("+", n, one)),
        ),
        (
            "False Conjecture (Falsification Filter Test): sum_{k=1}^n k = n^2",
            expr_factory.op("sum", k, n),
            expr_factory.op("^", n, two),
        ),
    ]

    print("=" * 80)
    print("EVOLUTIONARY MATHEMATICAL DISCOVERY ENGINE - PHASE 0 VERIFICATION HARNESS")
    print("=" * 80)

    for name, lhs, rhs in benchmarks:
        print(f"\n[Evaluating]: {name}")
        print(f"  LHS: {lhs}")
        print(f"  RHS: {rhs}")
        res = pipeline.evaluate(lhs, rhs)
        print(f"  Status:       {res.status.name}")
        print(f"  Verified:     {res.is_verified}")
        print(f"  Proof Method: {res.proof_method}")
        print(f"  Total Time:   {res.total_runtime_ms:.3f} ms")
        print(f"  Details:      {res.details}")

    print("\n" + "=" * 80)
    print("ALL HARNESS CHECKS COMPLETED.")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()


"""Unit tests for Lean 4 theorem and proof script generation."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.storage.knowledge_base import StoredTheorem
from evolutionary_math.utils.lean_exporter import expr_to_lean4, generate_lean4_proof_file


def test_expr_to_lean4_translation():
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    # (n * (n + 1)) / 2
    n_plus_1 = expr_factory.op("+", n, one)
    prod = expr_factory.op("*", n, n_plus_1)
    triangular = expr_factory.op("/", prod, two)

    lean_str = expr_to_lean4(triangular)
    assert lean_str == "((n * (n + 1)) / 2)"


def test_generate_lean4_proof_file():
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    target = expr_factory.op("sum", k, n)
    rhs = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, expr_factory.constant(1))), expr_factory.constant(2))

    th = StoredTheorem(
        id="66ecf83a1234",
        target_str=str(target),
        discovery_str=str(rhs),
        sexpr=rhs.to_sexpr(),
        proof_method="mathematical_induction",
        generation=1,
        timestamp=1000.0,
        experiment_id="test",
        definition_ast=rhs,
        name="Triangular Number Formula",
        clean_target="sum_k=1..n(k)",
        clean_formula="n*(n+1)/2",
        explanation="Triangular numbers",
    )

    code = generate_lean4_proof_file([th])
    assert "import Mathlib" in code
    assert "theorem thm_66ecf8" in code
    assert "open BigOperators" in code

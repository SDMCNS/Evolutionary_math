"""Unit tests for formatting utilities: LaTeX, ASCII tree, and Mermaid graph."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.storage.knowledge_base import KnowledgeBase
from evolutionary_math.evolution.individual import Individual
from evolutionary_math.evaluation.pipeline import PipelineResult, EvaluationStatus
from evolutionary_math.utils.formatting import to_latex, to_ascii_tree, export_knowledge_base_mermaid, export_knowledge_base_markdown


def test_to_latex():
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    # Triangular number: n*(n+1)/2
    prod = expr_factory.op("*", n, expr_factory.op("+", n, one))
    triangular = expr_factory.op("/", prod, two)

    latex_str = to_latex(triangular)
    assert r"\frac" in latex_str
    assert r"\cdot" in latex_str

    # Summation: sum_{k=1}^n k
    sum_k = expr_factory.op("sum", k, n)
    sum_latex = to_latex(sum_k)
    assert r"\sum_{k=1}^{n}" in sum_latex

    # Lemma call: L1(n)
    lemma_call = expr_factory.lemma("L1", n, triangular)
    lemma_latex = to_latex(lemma_call)
    assert r"\mathrm{L1}\left(n\right)" in lemma_latex


def test_to_ascii_tree():
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    expr = expr_factory.op("+", n, one)

    tree_str = to_ascii_tree(expr)
    assert "Op: +" in tree_str
    assert "Var: n" in tree_str
    assert "Const: 1" in tree_str


def test_mermaid_export():
    kb = KnowledgeBase(":memory:")
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)

    # Theorem 1
    th1_ast = expr_factory.op("+", n, one)
    ind1 = Individual(
        candidate=th1_ast,
        generation=5,
        evaluation_result=PipelineResult(
            status=EvaluationStatus.SYMBOLICALLY_VERIFIED,
            fitness_score=1.0,
            is_verified=True,
            proof_method="induction",
            total_runtime_ms=1.0,
        ),
    )
    kb.store_discovery(ind1, expr_factory.op("sum", k, n))

    # Theorem 2 depending on Theorem 1
    lemma_call = expr_factory.lemma(f"L_{ind1.id[:4]}", n, th1_ast)
    th2_ast = expr_factory.op("*", lemma_call, expr_factory.constant(2))
    ind2 = Individual(
        candidate=th2_ast,
        generation=1,
        evaluation_result=PipelineResult(
            status=EvaluationStatus.SYMBOLICALLY_VERIFIED,
            fitness_score=1.0,
            is_verified=True,
            proof_method="induction",
            total_runtime_ms=1.0,
        ),
    )
    kb.store_discovery(ind2, expr_factory.op("sum", expr_factory.op("^", k, expr_factory.constant(2)), n))

    mermaid_code = export_knowledge_base_mermaid(kb)
    assert "graph TD" in mermaid_code
    assert "composes" in mermaid_code

    # Test Markdown export
    md = export_knowledge_base_markdown(kb)
    assert "# Mathematical Knowledge Base Discoveries" in md
    assert "## Summary Catalog" in md
    assert "## Detailed Discovery Profiles" in md
    assert "graph TD" in md

    kb.close()


def test_human_readable_math_formatting():
    from evolutionary_math.utils.formatting import (
        format_clean_target,
        format_clean_formula,
        format_expanded_formula,
        infer_theorem_name,
        format_complete_latex,
    )

    # 1. Target formatting
    assert format_clean_target("sum_k=1..n(k)") == "∑_{k=1}^n k"
    assert format_clean_target("sum_k=1..n(1)") == "∑_{k=1}^n 1"
    assert format_clean_target("sum_k=1..n(((2 * k) - 1))") == "∑_{k=1}^n (2k - 1)"
    assert format_clean_target("sum_k=1..n((1 / (k * (k + 1))))") == "∑_{k=1}^n 1 / (k(k + 1))"
    assert format_clean_target("sum_k=1..n((k^3))") == "∑_{k=1}^n k³"
    # Compound targets previously truncated
    assert format_clean_target("sum_k=1..n(((k * (k + 1)) * (k + 2)))") == "∑_{k=1}^n k(k + 1)(k + 2)"
    assert format_clean_target("sum_k=1..n((((2 * k) - 1)^2))") == "∑_{k=1}^n (2k - 1)²"
    assert format_clean_target("sum_k=1..n((k + m))") == "∑_{k=1}^n (k + m)"

    # 2. Theorem naming
    assert infer_theorem_name("sum_k=1..n(k)") == "Triangular Number Formula (Sum of 1..n)"
    assert infer_theorem_name("sum_k=1..n((k^3))") == "Nicomachus's Theorem (Sum of First n Cubes)"
    assert infer_theorem_name("sum_k=1..n(((2 * k) - 1))") == "Sum of Consecutive Odd Numbers"
    assert infer_theorem_name("sum_k=1..n((1 / (k * (k + 1))))") == "Harmonic Telescoping Series 1/(k(k+1))"
    assert infer_theorem_name("sum_k=1..n((((2 * k) - 1)^2))") == "Sum of Squares of Consecutive Odd Numbers"
    assert infer_theorem_name("sum_k=1..n(((2 * k)^2))") == "Sum of Squares of Consecutive Even Numbers"
    assert infer_theorem_name("sum_k=1..n(((k * (k + 1)) * (k + 2)))") == "Sum of Products of 3 Consecutive Integers (4-Simplex / Pentatope Numbers)"
    assert infer_theorem_name("sum_k=1..n((1 / (((2 * k) - 1) * ((2 * k) + 1))))") == "Telescoping Series of Odd Factor Products 1/((2k-1)(2k+1))"

    # 2b. Intuition explanation accuracy
    from evolutionary_math.advisory.client import MockAdvisoryClient
    mock_adviser = MockAdvisoryClient()
    exp_odd_sq = mock_adviser.explain_discovery(
        target_str="sum_k=1..n((((2 * k) - 1)^2))",
        discovery_str="n*(2*n - 1)*(2*n + 1)/3",
        latex_str="",
        proof_method="mathematical_induction"
    )
    assert "equals n²" not in exp_odd_sq
    assert "squares of the first n consecutive odd numbers" in exp_odd_sq

    # 3. Clean and expanded formulas
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)
    tri_ast = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two)
    
    clean = format_clean_formula(tri_ast)
    assert "n" in clean and "2" in clean

    # Composite lemma expansion: L_square(tri_ast)
    sq_ast = expr_factory.op("^", n, two)
    lemma_sq = expr_factory.lemma("L_sq", tri_ast, sq_ast)
    expanded = format_expanded_formula(lemma_sq)
    assert "4" in expanded  # (n(n+1)/2)^2 expands with denominator 4
    assert "n" in expanded

    # 4. Complete LaTeX
    latex_eq = format_complete_latex(expr_factory.op("sum", n, n), tri_ast)
    assert r"\sum" in latex_eq
    assert "=" in latex_eq



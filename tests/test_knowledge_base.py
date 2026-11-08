"""Unit tests for the SQLite Knowledge Base."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evaluation.pipeline import PipelineResult, EvaluationStatus
from evolutionary_math.evolution.individual import Individual
from evolutionary_math.storage.knowledge_base import KnowledgeBase


def test_knowledge_base_store_and_retrieve():
    kb = KnowledgeBase(":memory:")

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    target_lhs = expr_factory.op("sum", k, n)
    # rhs = n*(n+1)/2
    rhs = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two)

    eval_result = PipelineResult(
        status=EvaluationStatus.SYMBOLICALLY_VERIFIED,
        fitness_score=1.0,
        is_verified=True,
        proof_method="mathematical_induction",
        total_runtime_ms=8.5,
    )

    ind = Individual(
        candidate=rhs,
        generation=12,
        fitness_vector=(1.0, 0.7, 0.9),
        evaluation_result=eval_result,
    )

    stored = kb.store_discovery(ind, target_lhs, experiment_id="test_exp")
    assert stored.id == ind.id
    assert stored.proof_method == "mathematical_induction"

    all_theorems = kb.get_all_theorems()
    assert len(all_theorems) == 1
    assert all_theorems[0].discovery_str == str(rhs)

    # Check is_known with identical expression
    assert kb.is_known(rhs)
    # Check is_known with non-stored expression
    assert not kb.is_known(expr_factory.op("+", n, two))


def test_knowledge_base_explanation_persistence():
    kb = KnowledgeBase(":memory:")

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    two = expr_factory.constant(2)
    one = expr_factory.constant(1)

    target_lhs = expr_factory.op("sum", expr_factory.op("-", expr_factory.op("*", two, k), one), n)
    rhs = expr_factory.op("^", n, two)

    eval_result = PipelineResult(
        status=EvaluationStatus.SYMBOLICALLY_VERIFIED,
        fitness_score=1.0,
        is_verified=True,
        proof_method="mathematical_induction",
        total_runtime_ms=5.0,
    )

    ind = Individual(
        candidate=rhs,
        generation=3,
        fitness_vector=(1.0, 0.9, 0.95),
        evaluation_result=eval_result,
    )

    explanation = "Sum of first n odd numbers forms an n×n square using L-shaped gnomons."
    stored = kb.store_discovery(ind, target_lhs, experiment_id="test_exp", explanation=explanation)
    assert stored.explanation == explanation

    all_theorems = kb.get_all_theorems()
    assert len(all_theorems) == 1
    assert all_theorems[0].explanation == explanation


def test_store_discovery_strips_introns():
    kb = KnowledgeBase(":memory:")

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    two = expr_factory.constant(2)
    four = expr_factory.constant(4)

    target_lhs = expr_factory.op("sum", k, n)

    # Bloated expression: ((n + (n / n)) + (4 * (n - n))) * (n / 2)
    n_div_n = expr_factory.op("/", n, n)
    n_minus_n = expr_factory.op("-", n, n)
    four_zero = expr_factory.op("*", four, n_minus_n)
    n_plus_one = expr_factory.op("+", n, n_div_n)
    bloated_inner = expr_factory.op("+", n_plus_one, four_zero)
    bloated_rhs = expr_factory.op("*", bloated_inner, expr_factory.op("/", n, two))

    eval_result = PipelineResult(
        status=EvaluationStatus.SYMBOLICALLY_VERIFIED,
        fitness_score=1.0,
        is_verified=True,
        proof_method="mathematical_induction",
        total_runtime_ms=8.0,
    )

    ind = Individual(
        candidate=bloated_rhs,
        generation=31,
        fitness_vector=(1.0, 0.4, 0.5),
        evaluation_result=eval_result,
    )

    stored = kb.store_discovery(ind, target_lhs, experiment_id="test_intron")
    # Verify that stored discovery_str and definition_ast are clean and intron-free!
    assert "n / n" not in stored.discovery_str
    assert "n - n" not in stored.discovery_str
    assert stored.discovery_str == "((n + 1) * (n / 2))"
    assert stored.definition_ast.node_count < bloated_rhs.node_count


def test_knowledge_base_rich_schema_and_view():
    kb = KnowledgeBase(":memory:")

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    two = expr_factory.constant(2)
    one = expr_factory.constant(1)

    target_lhs = expr_factory.op("sum", expr_factory.op("-", expr_factory.op("*", two, k), one), n)
    rhs = expr_factory.op("^", n, two)

    eval_result = PipelineResult(
        status=EvaluationStatus.SYMBOLICALLY_VERIFIED,
        fitness_score=1.0,
        is_verified=True,
        proof_method="mathematical_induction",
        total_runtime_ms=5.0,
    )

    ind = Individual(
        candidate=rhs,
        generation=1,
        fitness_vector=(1.0, 0.9, 0.95),
        evaluation_result=eval_result,
    )

    stored = kb.store_discovery(ind, target_lhs, experiment_id="test_rich")
    
    # Verify rich fields
    assert stored.name == "Sum of Consecutive Odd Numbers"
    assert stored.clean_target == "∑_{k=1}^n (2k - 1)"
    assert "n" in stored.clean_formula
    assert stored.latex is not None and "=" in stored.latex
    assert stored.explanation is not None and len(stored.explanation) > 20

    # Query v_discoveries SQL view
    cursor = kb.conn.cursor()
    cursor.execute("SELECT id, name, target, formula, proof_method, explanation FROM v_discoveries WHERE id = ?", (stored.id,))
    row = cursor.fetchone()
    assert row is not None
    assert row["name"] == "Sum of Consecutive Odd Numbers"
    assert row["target"] == "∑_{k=1}^n (2k - 1)"
    assert row["proof_method"] == "mathematical_induction"

    kb.close()



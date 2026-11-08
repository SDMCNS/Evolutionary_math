"""Unit tests for lemma promotion and cumulative knowledge discovery."""

import random
from evolutionary_math.core.ast import expr_factory
from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.grammar.generator import ExpressionGenerator
from evolutionary_math.evaluation.pipeline import EvaluationPipeline, EvaluationStatus
from evolutionary_math.storage.knowledge_base import KnowledgeBase
from evolutionary_math.evolution.individual import Individual


def test_grammar_lemma_promotion_and_generation():
    grammar = Grammar.default_summation_rhs_grammar()
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    # Definition of Lemma 1: n*(n+1)/2
    def_ast = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two)
    grammar.promote_lemma("L_sum_k", def_ast, weight=5.0)

    assert "L_sum_k" in grammar.promoted_lemmas
    rules = grammar.get_rules("EXPR")
    lemma_rules = [r for r in rules if r.rule_type == "lemma"]
    assert len(lemma_rules) == 1
    assert lemma_rules[0].symbol == "L_sum_k"

    # Generator should now generate expressions containing L_sum_k
    gen = ExpressionGenerator(grammar, rng=random.Random(42))
    found_lemma = False
    for _ in range(50):
        tree = gen.generate(max_depth=3, method="grow")
        if "L_sum_k" in tree.to_sexpr():
            found_lemma = True
            break
    assert found_lemma


def test_nicomachus_identity_verification_with_promoted_lemma():
    """Verify sum_{k=1}^n k^3 = L_sum_k(n)^2 symbolically using the promoted lemma."""
    pipeline = EvaluationPipeline()

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)
    three = expr_factory.constant(3)

    # LHS: sum_{k=1}^n k^3
    sum_k3 = expr_factory.op("sum", expr_factory.op("^", k, three), n)

    # Promoted lemma: L_sum_k(n) = n*(n+1)/2
    def_ast = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two)
    lemma_expr = expr_factory.lemma("L_sum_k", n, def_ast)

    # RHS: (L_sum_k(n) ^ 2)
    rhs = expr_factory.op("^", lemma_expr, two)

    res = pipeline.evaluate(sum_k3, rhs)
    assert res.status == EvaluationStatus.SYMBOLICALLY_VERIFIED
    assert res.is_verified
    assert res.proof_method is not None


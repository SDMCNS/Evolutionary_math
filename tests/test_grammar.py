"""Unit tests for grammar rules and expression generation."""

import random
from evolutionary_math.grammar.rules import Grammar, ProductionRule
from evolutionary_math.grammar.generator import ExpressionGenerator
from evolutionary_math.core.ast import ExprNode


def test_grammar_creation_and_rules():
    g = Grammar.default_summation_rhs_grammar(variables=["n"])
    expr_rules = g.get_rules("EXPR")
    assert len(expr_rules) > 5

    # Test weight adjustment
    g.adjust_rule_weight("EXPR", "+", 2.0)
    adjusted_rule = [r for r in g.get_rules("EXPR") if r.symbol == "+"][0]
    assert adjusted_rule.weight == 4.0


def test_generator_grow_and_full():
    rng = random.Random(42)
    g = Grammar.default_summation_rhs_grammar(variables=["n"])
    gen = ExpressionGenerator(g, rng=rng)

    tree_grow = gen.generate(max_depth=3, method="grow")
    assert isinstance(tree_grow, ExprNode)
    assert tree_grow.depth <= 4

    tree_full = gen.generate(max_depth=3, method="full")
    assert isinstance(tree_full, ExprNode)
    assert tree_full.depth <= 4


def test_ramped_half_and_half():
    rng = random.Random(123)
    g = Grammar.default_summation_rhs_grammar(variables=["n"])
    gen = ExpressionGenerator(g, rng=rng)

    pop = gen.ramped_half_and_half(population_size=20, min_depth=2, max_depth=4)
    assert len(pop) == 20
    assert all(isinstance(ind, ExprNode) for ind in pop)


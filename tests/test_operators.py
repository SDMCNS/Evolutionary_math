"""Unit tests for genetic operators."""

import random
from evolutionary_math.core.ast import expr_factory
from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.grammar.generator import ExpressionGenerator
from evolutionary_math.evolution.operators import GeneticOperators


def test_subtree_crossover():
    rng = random.Random(42)
    g = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(g, rng=rng)
    ops = GeneticOperators(gen, rng=rng)

    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    # parent 1: (n + 1) * 2
    p1 = expr_factory.op("*", expr_factory.op("+", n, one), two)
    # parent 2: (n - 2)
    p2 = expr_factory.op("-", n, two)

    c1, c2 = ops.crossover(p1, p2)
    assert c1 is not None
    assert c2 is not None
    assert c1.node_count >= 1
    assert c2.node_count >= 1


def test_subtree_mutation():
    rng = random.Random(42)
    g = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(g, rng=rng)
    ops = GeneticOperators(gen, rng=rng)

    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    expr = expr_factory.op("+", n, one)

    mutant = ops.subtree_mutation(expr, max_depth=2)
    assert mutant is not None
    assert isinstance(mutant.node_count, int)


def test_constant_perturbation():
    rng = random.Random(42)
    g = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(g, rng=rng)
    ops = GeneticOperators(gen, rng=rng)

    n = expr_factory.variable("n")
    two = expr_factory.constant(2)
    expr = expr_factory.op("*", n, two)

    perturbed = ops.constant_perturbation(expr)
    assert perturbed is not None


def test_hoist_mutation():
    rng = random.Random(42)
    g = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(g, rng=rng)
    ops = GeneticOperators(gen, rng=rng)

    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)
    # ((n + 1) * 2)
    expr = expr_factory.op("*", expr_factory.op("+", n, one), two)

    hoisted = ops.hoist_mutation(expr)
    assert hoisted.depth <= expr.depth


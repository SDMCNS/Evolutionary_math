"""Unit tests for the AdvisoryController and parameter adaptation."""

import random
from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.grammar.generator import ExpressionGenerator
from evolutionary_math.evolution.island import Island
from evolutionary_math.advisory.client import MockAdvisoryClient
from evolutionary_math.advisory.controller import AdvisoryController


def test_advisory_controller_trigger_on_stagnation():
    grammar = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(grammar, rng=random.Random(42))
    island = Island(island_id=0, population_size=10, generator=gen, rng=random.Random(42))
    island.initialize()

    client = MockAdvisoryClient()
    controller = AdvisoryController(client=client, stagnation_threshold=3, cooldown_generations=2)

    # Generation 1: stagnation = 0 -> no trigger
    res1 = controller.check_and_apply_guidance(generation=1, islands=[island], grammar=grammar)
    assert res1 is None

    # Artificially increment stagnation
    controller.stagnation_counter = 3
    res2 = controller.check_and_apply_guidance(generation=4, islands=[island], grammar=grammar)
    assert res2 is not None
    assert res2.regime_selection in ("EXPLORATION", "EXPLOITATION", "BALANCED")
    assert len(controller.advisory_history) == 1


def test_advisory_controller_graceful_fallback():
    grammar = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(grammar, rng=random.Random(42))
    island = Island(island_id=0, population_size=10, generator=gen, rng=random.Random(42))
    island.initialize()

    # None client simulates disabled or offline LLM
    controller = AdvisoryController(client=None, stagnation_threshold=1)
    controller.stagnation_counter = 5

    res = controller.check_and_apply_guidance(generation=2, islands=[island], grammar=grammar)
    assert res is None  # Does not crash, cleanly returns None


def test_advisory_controller_target_reset():
    grammar = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(grammar, rng=random.Random(42))
    island = Island(island_id=0, population_size=10, generator=gen, rng=random.Random(42))
    island.initialize()

    client = MockAdvisoryClient()
    controller = AdvisoryController(client=client, stagnation_threshold=3, cooldown_generations=5)

    # Trigger advisory on generation 30 of target 1
    controller.best_validity_observed = 0.5
    controller.stagnation_counter = 5
    res1 = controller.check_and_apply_guidance(generation=30, islands=[island], grammar=grammar)
    assert res1 is not None
    assert controller.last_advisory_generation == 30

    # Target 2 starts: generation drops back down to 1
    # Auto-reset should detect generation < last_advisory_generation and reset cooldown
    controller.check_and_apply_guidance(generation=1, islands=[island], grammar=grammar)
    assert controller.last_advisory_generation == -999

    controller.stagnation_counter = 2
    res2 = controller.check_and_apply_guidance(generation=4, islands=[island], grammar=grammar)
    assert res2 is not None
    assert controller.last_advisory_generation == 4


def test_advisory_controller_async_mode():
    grammar = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(grammar, rng=random.Random(42))
    island = Island(island_id=0, population_size=10, generator=gen, rng=random.Random(42))
    island.initialize()

    client = MockAdvisoryClient()
    controller = AdvisoryController(client=client, stagnation_threshold=2, cooldown_generations=2, async_mode=True)

    # Initialize baseline validity
    controller.best_validity_observed = 0.5
    controller.stagnation_counter = 1

    # Step at generation 2 triggers async advisory in background
    res_async_dispatched = controller.check_and_apply_guidance(generation=2, islands=[island], grammar=grammar)
    # Dispatched in background -> immediately returns None so evolution continues
    assert res_async_dispatched is None
    assert controller._pending_future is not None

    # Wait for the future to finish
    controller._pending_future.result(timeout=2.0)

    # Next generation boundary detects completion and applies advice
    res_completed = controller.check_and_apply_guidance(generation=3, islands=[island], grammar=grammar)
    assert res_completed is not None
    assert controller._pending_future is None
    assert controller.last_advisory_generation == 3


def test_advisory_controller_subtree_injection():
    grammar = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(grammar, rng=random.Random(42))
    island = Island(island_id=1, population_size=10, regime="exploration", generator=gen, rng=random.Random(42))
    island.initialize()

    client = MockAdvisoryClient()
    controller = AdvisoryController(client=client, stagnation_threshold=1, cooldown_generations=1)
    controller.best_validity_observed = 0.5
    controller.stagnation_counter = 5

    # Check advice application
    res = controller.check_and_apply_guidance(generation=2, islands=[island], grammar=grammar)
    assert res is not None
    assert len(res.suggested_subtrees) > 0

    # Verify that suggested subtrees were injected into island's population
    operators = [ind.operator_applied for ind in island.population]
    assert "advisory_seed" in operators


def test_island_operator_weights_isolation():
    # Verify Island.REGIME_WEIGHTS is not globally mutated by advisory application
    baseline_crossover = Island.REGIME_WEIGHTS["balanced"]["crossover"]

    grammar = Grammar.default_summation_rhs_grammar()
    gen = ExpressionGenerator(grammar, rng=random.Random(42))
    island = Island(island_id=0, population_size=10, generator=gen, rng=random.Random(42))
    island.initialize()

    client = MockAdvisoryClient()
    controller = AdvisoryController(client=client, stagnation_threshold=1, cooldown_generations=1)
    controller.best_validity_observed = 0.5
    controller.stagnation_counter = 5

    controller.check_and_apply_guidance(generation=2, islands=[island], grammar=grammar)
    assert island.operator_weights is not None
    # Class-level dictionary remains unmodified
    assert Island.REGIME_WEIGHTS["balanced"]["crossover"] == baseline_crossover



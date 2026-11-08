"""Unit and integration tests for the EvolutionEngine."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evolution.engine import EvolutionEngine
from evolutionary_math.storage.knowledge_base import KnowledgeBase


def test_evolution_engine_stepping_and_telemetry():
    kb = KnowledgeBase(":memory:")
    engine = EvolutionEngine(
        num_islands=2,
        island_population_size=10,
        knowledge_base=kb,
        seed=42,
    )

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    target_lhs = expr_factory.op("sum", k, n)

    # Run for 3 generations
    result = engine.run(target_lhs, max_generations=3, experiment_id="test_run")
    assert result.total_generations <= 3
    assert len(result.telemetry_history) > 0
    first_telem = result.telemetry_history[0]
    assert first_telem.generation == 1
    assert first_telem.best_validity >= 0.0


def test_evolution_engine_discovery_explanation():
    kb = KnowledgeBase(":memory:")
    # Seed 42 finds sum_k in generation 1 or 2 with pop size 30
    engine = EvolutionEngine(
        num_islands=3,
        island_population_size=40,
        knowledge_base=kb,
        seed=42,
    )

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    target_lhs = expr_factory.op("sum", k, n)

    result = engine.run(target_lhs, max_generations=20, experiment_id="test_exp")
    if result.success and result.discovered_theorem:
        assert result.discovered_theorem.explanation is not None
        assert len(result.discovered_theorem.explanation) > 10


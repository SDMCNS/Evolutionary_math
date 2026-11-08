"""Integration tests for the EvolutionEngine with active AdvisoryController."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evolution.engine import EvolutionEngine
from evolutionary_math.advisory.client import MockAdvisoryClient
from evolutionary_math.advisory.controller import AdvisoryController
from evolutionary_math.storage.knowledge_base import KnowledgeBase


def test_engine_with_active_advisory():
    kb = KnowledgeBase(":memory:")
    client = MockAdvisoryClient()
    controller = AdvisoryController(
        client=client,
        stagnation_threshold=2,
        cooldown_generations=1,
    )

    engine = EvolutionEngine(
        num_islands=2,
        island_population_size=15,
        knowledge_base=kb,
        advisory_controller=controller,
        seed=42,
    )

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    target_lhs = expr_factory.op("sum", k, n)

    # Run for 6 generations
    result = engine.run(target_lhs, max_generations=6, experiment_id="advisory_test")
    assert result.total_generations <= 6
    assert len(result.telemetry_history) > 0

    # Ensure advisory interventions were tracked
    if result.advisory_interventions_count > 0:
        interventions = [t for t in result.telemetry_history if t.advisory_intervention is not None]
        assert len(interventions) > 0
        assert "[" in interventions[0].advisory_intervention


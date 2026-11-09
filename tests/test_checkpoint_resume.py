"""Tests for checkpointing, active population preservation, and interrupt-resume capability."""

import pytest
import time
from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evolution.island import Island
from evolutionary_math.grammar.generator import ExpressionGenerator
from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.storage.knowledge_base import KnowledgeBase
from evolutionary_math.evolution.engine import EvolutionEngine, EngineRunResult
from evolutionary_math.campaign.runner import AutonomousDiscoveryCampaign


def test_island_serialize_and_restore():
    grammar = Grammar()
    gen = ExpressionGenerator(grammar)
    island1 = Island(island_id=0, population_size=10, regime="exploration", generator=gen)
    island1.initialize(min_depth=2, max_depth=3)
    island1.generation = 12

    # Serialize
    data = island1.serialize()
    assert data["island_id"] == 0
    assert data["generation"] == 12
    assert len(data["population"]) == 10
    assert "candidate_ast" in data["population"][0]

    # Restore into a fresh island
    island2 = Island(island_id=1, population_size=10, regime="balanced", generator=gen)
    island2.restore(data)

    assert island2.generation == 12
    assert island2.regime == "exploration"
    assert len(island2.population) == 10
    assert str(island2.population[0].candidate) == str(island1.population[0].candidate)


def test_knowledge_base_checkpoint_crud():
    kb = KnowledgeBase(":memory:")
    
    assert not kb.has_checkpoint("target:test")
    
    kb.save_checkpoint(
        checkpoint_key="target:test",
        target_str="sum_k=1..n(k^5)",
        clean_target="∑_{k=1}^n k⁵",
        domain_mode="algebra",
        current_generation=14,
        max_generations=50,
        experiment_id="exp_test",
        islands_data=[{"island_id": 0, "population": []}],
        meta={"high_water_validity": 0.88, "total_evaluations": 2240},
    )
    
    assert kb.has_checkpoint("target:test")
    cp = kb.load_checkpoint("target:test")
    assert cp is not None
    assert cp["current_generation"] == 14
    assert cp["clean_target"] == "∑_{k=1}^n k⁵"
    assert cp["meta"]["high_water_validity"] == 0.88
    
    deleted = kb.delete_checkpoint("target:test")
    assert deleted is True
    assert not kb.has_checkpoint("target:test")
    
    kb.close()


def test_engine_checkpoint_and_auto_resume():
    kb = KnowledgeBase(":memory:")
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    # Higher power sum that won't be solved in 3 generations
    target = expr_factory.op("sum", expr_factory.op("^", k, expr_factory.constant(6)), n)
    
    engine1 = EvolutionEngine(
        knowledge_base=kb,
        num_islands=2,
        island_population_size=10,
        enable_polynomial_solver=False,
    )
    
    # Run 4 generations
    res1 = engine1.run(target, max_generations=4, resume=True)
    assert res1.total_generations == 4
    assert not res1.success
    
    cp_key = f"target:{str(target)}"
    assert kb.has_checkpoint(cp_key)
    cp = kb.load_checkpoint(cp_key)
    assert cp["current_generation"] == 4
    
    # Run a second engine instance resuming for up to 8 generations
    engine2 = EvolutionEngine(
        knowledge_base=kb,
        num_islands=2,
        island_population_size=10,
        enable_polynomial_solver=False,
    )
    
    res2 = engine2.run(target, max_generations=8, resume=True)
    # Total generations reached is 8, having resumed from generation 5!
    assert res2.total_generations == 8
    
    # Check that fresh flag discards previous checkpoint
    engine3 = EvolutionEngine(
        knowledge_base=kb,
        num_islands=2,
        island_population_size=10,
        enable_polynomial_solver=False,
    )
    res3 = engine3.run(target, max_generations=3, resume=False)
    assert res3.total_generations == 3
    
    kb.close()


def test_graceful_interrupt_handling():
    kb = KnowledgeBase(":memory:")
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    target = expr_factory.op("sum", expr_factory.op("^", k, expr_factory.constant(8)), n)
    
    engine = EvolutionEngine(
        knowledge_base=kb,
        num_islands=2,
        island_population_size=10,
        enable_polynomial_solver=False,
    )
    
    # Simulate user pressing Ctrl+C on generation 3
    def interrupt_callback(telem):
        if telem.generation >= 3:
            raise KeyboardInterrupt("Simulated Ctrl+C")
            
    res = engine.run(target, max_generations=20, callback=interrupt_callback, resume=True)
    assert res.interrupted is True
    assert res.total_generations == 3
    
    # Verify that working population was saved at generation 3
    cp_key = f"target:{str(target)}"
    assert kb.has_checkpoint(cp_key)
    cp = kb.load_checkpoint(cp_key)
    assert cp["current_generation"] == 3
    assert len(cp["islands_data"]) == 2
    
    # Resume search from generation 4 without interrupt
    engine_resumed = EvolutionEngine(
        knowledge_base=kb,
        num_islands=2,
        island_population_size=10,
        enable_polynomial_solver=False,
    )
    res2 = engine_resumed.run(target, max_generations=6, resume=True)
    assert res2.interrupted is False
    assert res2.total_generations == 6
    
    kb.close()


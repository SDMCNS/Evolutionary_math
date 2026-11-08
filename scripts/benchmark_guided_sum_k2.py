"""Benchmark on a challenging target: sum_{k=1}^n k^2 with active LLM advisory guidance."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evolution.engine import EvolutionEngine, DiscoveryTelemetry
from evolutionary_math.advisory.client import MockAdvisoryClient
from evolutionary_math.advisory.controller import AdvisoryController
from evolutionary_math.storage.knowledge_base import KnowledgeBase


def main():
    kb = KnowledgeBase(":memory:")

    client = MockAdvisoryClient(confidence=0.95)
    controller = AdvisoryController(
        client=client,
        stagnation_threshold=5,
        epoch_interval=15,
        cooldown_generations=3,
    )

    engine = EvolutionEngine(
        num_islands=4,
        island_population_size=50,
        migration_interval=5,
        num_migrants=3,
        knowledge_base=kb,
        advisory_controller=controller,
        seed=555,
    )

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    two = expr_factory.constant(2)

    # Target: sum_{k=1}^n k^2
    target_lhs = expr_factory.op("sum", expr_factory.op("^", k, two), n)

    print("=" * 80)
    print("CHALLENGING TARGET DEMONSTRATOR: Faulhaber Degree 2 sum_{k=1}^n k^2")
    print("=" * 80)
    print(f"Target:               {target_lhs}")
    print(f"Goal:                 Discover n(n+1)(2n+1)/6 with LLM Advisory Guidance")
    print("-" * 80)

    def telemetry_logger(telem: DiscoveryTelemetry):
        if telem.advisory_intervention or telem.generation % 5 == 0 or telem.best_validity > 0.8:
            intervention_str = f"\n  >>> ⚡ ADVISORY INTERVENTION: {telem.advisory_intervention}" if telem.advisory_intervention else ""
            print(
                f"[Gen {telem.generation:3d}] Best Validity: {telem.best_validity:.4f} | "
                f"Evaluations: {telem.total_individuals_evaluated:5d} | "
                f"Leading: {telem.best_candidate_str}{intervention_str}"
            )

    result = engine.run(
        target_lhs=target_lhs,
        max_generations=60,
        experiment_id="sum_k2_guided",
        callback=telemetry_logger,
    )

    print("-" * 80)
    if result.success and result.discovered_theorem:
        th = result.discovered_theorem
        print("\n🏆 DISCOVERY CONFIRMED & FORMALLY VERIFIED!")
        print(f"  Target:                 {th.target_str}")
        print(f"  Discovered Closed Form: {th.discovery_str}")
        print(f"  Proof Method:           {th.proof_method}")
        print(f"  Generations:            {result.total_generations}")
        print(f"  Total Time:             {result.total_time_sec:.3f} s")
        print(f"  Advisory Interventions: {result.advisory_interventions_count}")
    else:
        print(f"\nSearch terminated at generation {result.total_generations}. Best candidates were retained.")
        print(f"Advisory interventions triggered: {result.advisory_interventions_count}")

    print("\n" + "=" * 80)
    print("ADVISORY INTERVENTIONS APPLIED DURING SEARCH")
    print("=" * 80)
    for i, adv in enumerate(controller.advisory_history, start=1):
        print(f"Intervention #{i}:")
        print(f"  Regime:     {adv.regime_selection} (Confidence: {adv.confidence:.2f})")
        print(f"  Diagnosis:  {adv.diagnosis}")
        print(f"  Weights:    {adv.operator_weight_adjustments}")
        print(f"  Biases:     {adv.grammar_biases}")


if __name__ == "__main__":
    main()


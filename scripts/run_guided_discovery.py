"""Demonstration of Phase 2 LLM Advisory Guidance in the Evolutionary Discovery Loop."""

import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evolution.engine import EvolutionEngine, DiscoveryTelemetry
from evolutionary_math.advisory.client import MockAdvisoryClient
from evolutionary_math.advisory.controller import AdvisoryController
from evolutionary_math.storage.knowledge_base import KnowledgeBase


def main():
    kb = KnowledgeBase("guided_discoveries.db")

    # Configure the air-gapped advisory interface
    # (Here we use MockAdvisoryClient; can be swapped with OpenAICompatibleAdvisoryClient for local Ollama)
    client = MockAdvisoryClient(confidence=0.92)
    controller = AdvisoryController(
        client=client,
        stagnation_threshold=6,
        epoch_interval=20,
        cooldown_generations=4,
    )

    engine = EvolutionEngine(
        num_islands=4,
        island_population_size=40,
        migration_interval=5,
        num_migrants=3,
        knowledge_base=kb,
        advisory_controller=controller,
        seed=314,
    )

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")

    # Target: sum_{k=1}^n k
    target_lhs = expr_factory.op("sum", k, n)

    print("=" * 80)
    print("EVOLUTIONARY MATHEMATICAL DISCOVERY ENGINE - PHASE 2 GUIDED DEMONSTRATOR")
    print("=" * 80)
    print(f"Target:               {target_lhs}")
    print(f"Advisory Provider:    MockAdvisoryClient (Rule-based strategic meta-adviser)")
    print(f"Air-Gap Policy:       Strict JSON Schema (AdvisoryResponse)")
    print(f"Stagnation Threshold: 6 generations without validity improvement")
    print("-" * 80)

    def telemetry_logger(telem: DiscoveryTelemetry):
        intervention_str = f" | ⚡ INTERVENTION: {telem.advisory_intervention}" if telem.advisory_intervention else ""
        if telem.advisory_intervention or telem.generation % 5 == 0 or telem.best_validity > 0.95:
            print(
                f"[Gen {telem.generation:3d}] Best Validity: {telem.best_validity:.4f} | "
                f"Evaluations: {telem.total_individuals_evaluated:5d} | "
                f"Leading: {telem.best_candidate_str}{intervention_str}"
            )

    result = engine.run(
        target_lhs=target_lhs,
        max_generations=100,
        experiment_id="guided_sum_k",
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
        print(f"  Knowledge Base ID:      {th.id}")
    else:
        print(f"\nSearch concluded without formal verification in {result.total_generations} generations.")

    print("\n" + "=" * 80)
    print("ADVISORY INTERVENTIONS LOG")
    print("=" * 80)
    for i, adv in enumerate(controller.advisory_history, start=1):
        print(f"Intervention #{i}:")
        print(f"  Regime:     {adv.regime_selection} (Confidence: {adv.confidence:.2f})")
        print(f"  Diagnosis:  {adv.diagnosis}")
        print(f"  Weights:    {adv.operator_weight_adjustments}")
        print(f"  Biases:     {adv.grammar_biases}")

    kb.close()


if __name__ == "__main__":
    main()


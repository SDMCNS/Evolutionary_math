"""Flagship Phase 3 Demonstrator: Cumulative Mathematical Knowledge Discovery.

Demonstrates:
1. Target 1: Autonomously discovering and verifying sum_{k=1}^n k = n(n+1)/2.
2. Automated Lemma Promotion: Encapsulating the verified theorem into an ADF (L_sum_k).
3. Target 2: Autonomously discovering Nicomachus's Theorem: sum_{k=1}^n k^3 = (L_sum_k(n))^2.
4. Dependency Tracking: Recording lemma dependencies in the persistent SQLite knowledge base.
"""

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
    db_file = "cumulative_discoveries.db"
    kb = KnowledgeBase(db_file)

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    two = expr_factory.constant(2)
    three = expr_factory.constant(3)

    print("=" * 80)
    print("EVOLUTIONARY MATHEMATICAL DISCOVERY ENGINE - PHASE 3 CUMULATIVE DISCOVERY")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # STAGE 1: Discover Base Lemma (Faulhaber Degree 1)
    # -------------------------------------------------------------------------
    target1_lhs = expr_factory.op("sum", k, n)
    print(f"\n[STAGE 1] Discovering foundational lemma for: {target1_lhs}")

    engine1 = EvolutionEngine(
        num_islands=4,
        island_population_size=40,
        migration_interval=5,
        num_migrants=3,
        knowledge_base=kb,
        auto_promote_lemmas=True,
        seed=101,
    )

    res1 = engine1.run(target_lhs=target1_lhs, max_generations=50, experiment_id="stage1_sum_k")
    assert res1.success and res1.discovered_theorem is not None
    th1 = res1.discovered_theorem
    print(f"  ✅ Base Lemma Discovered: {th1.target_str} = {th1.discovery_str}")
    print(f"  Proof Method: {th1.proof_method} (Generation {res1.total_generations})")

    # -------------------------------------------------------------------------
    # STAGE 2: Automated Lemma Promotion into Grammar
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[STAGE 2] Automated Lemma Promotion (ADF Encapsulation)")
    print("-" * 80)

    # Re-use the engine's updated grammar which now contains the promoted lemma
    lemma_name = f"L_{th1.id[:4]}"
    print(f"  Encapsulating Theorem [{th1.id}] into Grammar as building block: '{lemma_name}(n)'")
    promoted = kb.promote_lemmas_to_grammar(engine1.grammar, top_k=1, weight=4.0)
    print(f"  Active Grammar Promoted Lemmas: {list(engine1.grammar.promoted_lemmas.keys())}")

    # -------------------------------------------------------------------------
    # STAGE 3: Attack Complex Target (Faulhaber Degree 3: sum k^3)
    # -------------------------------------------------------------------------
    target2_lhs = expr_factory.op("sum", expr_factory.op("^", k, three), n)
    print("\n" + "-" * 80)
    print(f"[STAGE 3] Attacking Complex Target: {target2_lhs}")
    print(f"Leveraging promoted building blocks from Stage 1...")
    print("-" * 80)

    # Advisory controller to assist the search
    advisory_client = MockAdvisoryClient(confidence=0.95)
    advisory_controller = AdvisoryController(client=advisory_client, stagnation_threshold=5)

    engine2 = EvolutionEngine(
        grammar=engine1.grammar,  # Carry forward enriched grammar!
        num_islands=4,
        island_population_size=50,
        migration_interval=5,
        num_migrants=3,
        knowledge_base=kb,
        advisory_controller=advisory_controller,
        auto_promote_lemmas=True,
        seed=777,
    )

    def telemetry_logger(telem: DiscoveryTelemetry):
        if telem.advisory_intervention or telem.generation % 5 == 0 or telem.best_validity > 0.90:
            print(
                f"  [Gen {telem.generation:2d}] Validity: {telem.best_validity:.4f} | "
                f"Evals: {telem.total_individuals_evaluated:5d} | "
                f"Leading: {telem.best_candidate_str}"
            )

    res2 = engine2.run(
        target_lhs=target2_lhs,
        max_generations=60,
        experiment_id="stage3_sum_k3",
        callback=telemetry_logger,
    )

    print("-" * 80)
    if res2.success and res2.discovered_theorem:
        th2 = res2.discovered_theorem
        print("\n🏆 CUMULATIVE DISCOVERY CONFIRMED & FORMALLY PROVEN!")
        print(f"  Target:           {th2.target_str}")
        print(f"  Discovered Form:  {th2.discovery_str}")
        print(f"  Proof Method:     {th2.proof_method}")
        print(f"  Generations:      {res2.total_generations}")
        print(f"  Discovery Time:   {res2.total_time_sec:.3f} s")
        print(f"  Dependencies:     {th2.dependency_ids}")
    else:
        print(f"\nSearch concluded in {res2.total_generations} generations.")

    # -------------------------------------------------------------------------
    # Knowledge Base Inspection & Lineage
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PERSISTENT KNOWLEDGE BASE THEOREM REPOSITORY (cumulative_discoveries.db)")
    print("=" * 80)
    all_theorems = kb.get_all_theorems()
    for t in all_theorems:
        dep_str = f" [Dependencies: {', '.join(t.dependency_ids)}]" if t.dependency_ids else " [Foundational]"
        print(f"• Theorem [{t.id}] | {t.target_str} = {t.discovery_str}{dep_str} | via {t.proof_method}")

    kb.close()


if __name__ == "__main__":
    main()


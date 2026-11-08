"""Autonomous mathematical discovery demonstration script using the multi-island evolutionary engine."""

import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import time
from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evolution.engine import EvolutionEngine, DiscoveryTelemetry
from evolutionary_math.storage.knowledge_base import KnowledgeBase


def main():
    kb = KnowledgeBase("discoveries.db")

    engine = EvolutionEngine(
        num_islands=4,
        island_population_size=50,
        migration_interval=5,
        num_migrants=3,
        knowledge_base=kb,
        seed=101,
    )

    n = expr_factory.variable("n")
    k = expr_factory.variable("k")

    # Target 1: sum_{k=1}^n k
    target_lhs = expr_factory.op("sum", k, n)

    print("=" * 80)
    print("AUTONOMOUS MATHEMATICAL DISCOVERY ENGINE - PHASE 1 DISCOVERY DEMONSTRATOR")
    print("=" * 80)
    print(f"[Run 1] Target Problem Space: Find closed form for: {target_lhs}")
    print(f"Topology: 4 Islands, PopSize=50 per island (Total Pop=200), Migration Interval=5 gen")
    print(f"Selection: Multi-Objective NSGA-II (Validity, Simplicity/MDL, Novelty)")
    print("-" * 80)

    def telemetry_logger(telem: DiscoveryTelemetry):
        if telem.generation % 5 == 0 or telem.best_validity > 0.95:
            print(
                f"[Gen {telem.generation:3d}] Best Validity: {telem.best_validity:.4f} | "
                f"Pareto Front Size: {telem.pareto_front_size:2d} | "
                f"Evaluations: {telem.total_individuals_evaluated:5d} | "
                f"Elapsed: {telem.elapsed_time_sec:5.2f}s | "
                f"Leading Candidate: {telem.best_candidate_str}"
            )

    result = engine.run(
        target_lhs=target_lhs,
        max_generations=150,
        experiment_id="sum_k_experiment",
        callback=telemetry_logger,
    )

    print("-" * 80)
    if result.success and result.discovered_theorem:
        th = result.discovered_theorem
        print("\n🏆 DISCOVERY CONFIRMED AND FORMALLY VERIFIED!")
        print(f"  Target:           {th.target_str}")
        print(f"  Discovered Form:  {th.discovery_str}")
        print(f"  Proof Method:     {th.proof_method}")
        print(f"  Generations:      {result.total_generations}")
        print(f"  Discovery Time:   {result.total_time_sec:.3f} s")
        print(f"  Knowledge Base ID:{th.id}")
    else:
        print(f"\nSearch concluded without formal verification in {result.total_generations} generations.")

    # Target 2: Telescoping rational sum sum_{k=1}^n 1/(k(k+1))
    one = expr_factory.constant(1)
    k_plus_1 = expr_factory.op("+", k, one)
    denom = expr_factory.op("*", k, k_plus_1)
    term = expr_factory.op("/", one, denom)
    target2_lhs = expr_factory.op("sum", term, n)

    print("\n" + "=" * 80)
    print(f"[Run 2] Target Problem Space: Find closed form for: {target2_lhs}")
    print("-" * 80)

    engine2 = EvolutionEngine(
        num_islands=4,
        island_population_size=50,
        migration_interval=5,
        num_migrants=3,
        knowledge_base=kb,
        seed=202,
    )

    result2 = engine2.run(
        target_lhs=target2_lhs,
        max_generations=150,
        experiment_id="telescoping_experiment",
        callback=telemetry_logger,
    )

    print("-" * 80)
    if result2.success and result2.discovered_theorem:
        th = result2.discovered_theorem
        print("\n🏆 DISCOVERY CONFIRMED AND FORMALLY VERIFIED!")
        print(f"  Target:           {th.target_str}")
        print(f"  Discovered Form:  {th.discovery_str}")
        print(f"  Proof Method:     {th.proof_method}")
        print(f"  Generations:      {result2.total_generations}")
        print(f"  Discovery Time:   {result2.total_time_sec:.3f} s")
        print(f"  Knowledge Base ID:{th.id}")
    else:
        print(f"\nSearch concluded without formal verification in {result2.total_generations} generations.")

    # Inspect persistent knowledge base
    print("\n" + "=" * 80)
    print("PERSISTENT KNOWLEDGE BASE CONTENTS (SQLite: discoveries.db)")
    print("=" * 80)
    theorems = kb.get_all_theorems()
    for t in theorems:
        print(f"Theorem [{t.id}] | Target: {t.target_str} = {t.discovery_str} | Method: {t.proof_method}")

    kb.close()


if __name__ == "__main__":
    main()

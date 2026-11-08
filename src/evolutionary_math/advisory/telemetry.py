"""Telemetry packer: summarizes evolutionary populations into structured payloads."""

from typing import List, Dict, Set
from evolutionary_math.evolution.individual import Individual
from evolutionary_math.evolution.island import Island
from evolutionary_math.advisory.schema import AdvisoryRequest, CandidateSignature


class TelemetryPacker:
    """Summarizes multi-island population state into structured LLM advisory requests."""

    @staticmethod
    def pack(
        generation: int,
        islands: List[Island],
        stagnation_counter: int,
        domain: str = "summation_identities",
        known_lemmas_count: int = 0,
        recent_operator_success_rates: Dict[str, float] = None,
        top_k: int = 5,
    ) -> AdvisoryRequest:
        all_individuals: List[Individual] = [
            ind for island in islands for ind in island.population
        ]
        if not all_individuals:
            return AdvisoryRequest(
                generation=generation,
                domain=domain,
                stagnation_counter=stagnation_counter,
                population_metrics={"size": 0.0, "top_validity": 0.0},
                top_candidate_signatures=[],
                recent_operator_success_rates=recent_operator_success_rates or {},
                known_lemmas_count=known_lemmas_count,
            )

        # Sort by validity descending, then simplicity descending
        sorted_inds = sorted(all_individuals, key=lambda ind: (ind.validity, ind.simplicity), reverse=True)

        # Top K unique candidate signatures
        seen_exprs: Set[str] = set()
        top_signatures: List[CandidateSignature] = []
        for ind in sorted_inds:
            s = str(ind.candidate)
            if s not in seen_exprs:
                seen_exprs.add(s)
                top_signatures.append(
                    CandidateSignature(
                        expr_str=s,
                        validity=float(ind.validity),
                        simplicity=float(ind.simplicity),
                        node_count=int(ind.candidate.node_count),
                    )
                )
                if len(top_signatures) >= top_k:
                    break

        # Compute aggregate population metrics
        total_count = len(all_individuals)
        mean_nodes = sum(ind.candidate.node_count for ind in all_individuals) / total_count
        pareto_front_size = sum(1 for ind in all_individuals if ind.rank == 1)
        top_validity = float(sorted_inds[0].validity)

        metrics = {
            "population_size": float(total_count),
            "top_validity": top_validity,
            "mean_node_count": float(round(mean_nodes, 2)),
            "pareto_front_size": float(pareto_front_size),
        }

        return AdvisoryRequest(
            generation=generation,
            domain=domain,
            stagnation_counter=stagnation_counter,
            population_metrics=metrics,
            top_candidate_signatures=top_signatures,
            recent_operator_success_rates=recent_operator_success_rates or {
                "crossover": 0.25,
                "subtree_mutation": 0.25,
                "constant_perturbation": 0.25,
                "hoist": 0.25,
            },
            known_lemmas_count=known_lemmas_count,
        )


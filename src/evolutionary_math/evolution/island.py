"""Island population running a localized evolutionary search policy."""

import random
from typing import List, Set, Optional, Dict, Any
from evolutionary_math.core.ast import ExprNode
from evolutionary_math.core.canonicalizer import canonicalize
from evolutionary_math.evaluation.pipeline import EvaluationPipeline
from evolutionary_math.grammar.generator import ExpressionGenerator
from evolutionary_math.evolution.individual import Individual
from evolutionary_math.evolution.operators import GeneticOperators
from evolutionary_math.evolution.fitness import evaluate_individual_fitness, _extract_subexpr_sexprs
from evolutionary_math.evolution.selection import (
    tournament_select,
    nsga2_select_next_generation,
    fast_non_dominated_sort,
)


class Island:
    """An evolutionary island managing a local sub-population and search regime."""

    REGIME_WEIGHTS: Dict[str, Dict[str, float]] = {
        "balanced": {
            "crossover": 0.40,
            "subtree_mutation": 0.35,
            "constant_perturbation": 0.15,
            "hoist": 0.10,
        },
        "exploration": {
            "crossover": 0.25,
            "subtree_mutation": 0.55,
            "constant_perturbation": 0.10,
            "hoist": 0.10,
        },
        "exploitation": {
            "crossover": 0.35,
            "subtree_mutation": 0.15,
            "constant_perturbation": 0.40,
            "hoist": 0.10,
        },
    }

    def __init__(
        self,
        island_id: int,
        population_size: int = 50,
        regime: str = "balanced",
        generator: Optional[ExpressionGenerator] = None,
        rng: Optional[random.Random] = None,
    ):
        self.island_id = island_id
        self.population_size = population_size
        self.regime = regime
        self.rng = rng or random.Random()
        self.generator = generator or ExpressionGenerator(rng=self.rng)
        self.operators = GeneticOperators(self.generator, rng=self.rng)
        self.population: List[Individual] = []
        self.generation: int = 0
        self.discovered_theorems: List[Individual] = []
        self.operator_weights: Optional[Dict[str, float]] = None

    def inject_individual(self, candidate: ExprNode, operator_applied: str = "inject") -> Individual:
        """Inject an external seed or candidate into the population, replacing the weakest individual."""
        ind = Individual(
            candidate=canonicalize(candidate),
            generation=self.generation,
            operator_applied=operator_applied,
        )
        if len(self.population) < self.population_size:
            self.population.append(ind)
        else:
            weakest_idx = min(range(len(self.population)), key=lambda i: self.population[i].validity)
            self.population[weakest_idx] = ind
        return ind

    def initialize(self, min_depth: int = 2, max_depth: int = 4) -> None:
        """Initialize island population using ramped half-and-half generator."""
        exprs = self.generator.ramped_half_and_half(self.population_size, min_depth=min_depth, max_depth=max_depth)
        self.population = [
            Individual(candidate=expr, generation=0, operator_applied="init")
            for expr in exprs
        ]

    def evaluate_population(self, target_lhs: ExprNode, pipeline: EvaluationPipeline) -> None:
        """Evaluate all individuals in the population."""
        # Collect existing subexpressions for novelty computation
        all_subexprs: Set[str] = set()
        for ind in self.population:
            all_subexprs.update(_extract_subexpr_sexprs(ind.candidate))

        for ind in self.population:
            if ind.evaluation_result is None:
                fit_vec, eval_res = evaluate_individual_fitness(
                    ind.candidate, target_lhs, pipeline, all_subexprs
                )
                ind.fitness_vector = fit_vec
                ind.evaluation_result = eval_res
                if ind.is_verified:
                    self.discovered_theorems.append(ind)

    def step(self, target_lhs: ExprNode, pipeline: EvaluationPipeline) -> Optional[Individual]:
        """Advance the island by one evolutionary generation.

        Returns verified individual if discovered, else None.
        """
        self.generation += 1
        self.evaluate_population(target_lhs, pipeline)

        # Check for immediate discovery
        for ind in self.population:
            if ind.is_verified:
                return ind

        # Generate offspring
        offspring: List[Individual] = []
        if self.operator_weights is not None:
            weights = self.operator_weights
        else:
            weights = self.REGIME_WEIGHTS.get(self.regime, self.REGIME_WEIGHTS["balanced"])
        op_choices = list(weights.keys())
        op_probs = list(weights.values())

        while len(offspring) < self.population_size:
            op = self.rng.choices(op_choices, weights=op_probs, k=1)[0]
            parent1 = tournament_select(self.population, tournament_size=3, rng=self.rng)

            if op == "crossover":
                parent2 = tournament_select(self.population, tournament_size=3, rng=self.rng)
                c1, c2 = self.operators.crossover(parent1.candidate, parent2.candidate)
                offspring.append(Individual(
                    candidate=canonicalize(c1),
                    generation=self.generation,
                    parent_ids=(parent1.id, parent2.id),
                    operator_applied="crossover",
                ))
                if len(offspring) < self.population_size:
                    offspring.append(Individual(
                        candidate=canonicalize(c2),
                        generation=self.generation,
                        parent_ids=(parent1.id, parent2.id),
                        operator_applied="crossover",
                    ))
            elif op == "subtree_mutation":
                child = self.operators.subtree_mutation(parent1.candidate)
                offspring.append(Individual(
                    candidate=canonicalize(child),
                    generation=self.generation,
                    parent_ids=(parent1.id,),
                    operator_applied="subtree_mutation",
                ))
            elif op == "constant_perturbation":
                child = self.operators.constant_perturbation(parent1.candidate)
                offspring.append(Individual(
                    candidate=canonicalize(child),
                    generation=self.generation,
                    parent_ids=(parent1.id,),
                    operator_applied="constant_perturbation",
                ))
            elif op == "hoist":
                child = self.operators.hoist_mutation(parent1.candidate)
                offspring.append(Individual(
                    candidate=canonicalize(child),
                    generation=self.generation,
                    parent_ids=(parent1.id,),
                    operator_applied="hoist",
                ))

        # Evaluate offspring
        all_subexprs = set()
        for ind in self.population:
            all_subexprs.update(_extract_subexpr_sexprs(ind.candidate))

        for child in offspring:
            fit_vec, eval_res = evaluate_individual_fitness(
                child.candidate, target_lhs, pipeline, all_subexprs
            )
            child.fitness_vector = fit_vec
            child.evaluation_result = eval_res
            if child.is_verified:
                self.discovered_theorems.append(child)
                return child

        # NSGA-II Elitist selection from Parents + Offspring
        combined = self.population + offspring
        self.population = nsga2_select_next_generation(combined, self.population_size)
        return None

    def get_emigrants(self, count: int = 3) -> List[Individual]:
        """Select top individuals from Front 1 to migrate to neighboring islands."""
        fronts = fast_non_dominated_sort(self.population)
        if fronts:
            return fronts[0][:count]
        return self.population[:count]

    def accept_immigrants(self, immigrants: List[Individual]) -> None:
        """Incorporate immigrants into the island population."""
        # Replace the lowest ranked individuals
        self.population.sort(key=lambda ind: (ind.rank, -ind.crowding_distance), reverse=True)
        for i, imm in enumerate(immigrants):
            if i < len(self.population):
                self.population[i] = imm

    def serialize(self) -> Dict[str, Any]:
        """Serialize island population and state to a JSON-compatible dictionary."""
        pop_data = []
        for ind in self.population:
            pop_data.append({
                "id": ind.id,
                "candidate_ast": ind.candidate.to_dict(),
                "candidate_str": str(ind.candidate),
                "generation": ind.generation,
                "parent_ids": list(ind.parent_ids),
                "operator_applied": ind.operator_applied,
                "fitness_vector": list(ind.fitness_vector),
                "rank": ind.rank,
                "crowding_distance": ind.crowding_distance,
            })
        return {
            "island_id": self.island_id,
            "population_size": self.population_size,
            "regime": self.regime,
            "generation": self.generation,
            "population": pop_data,
        }

    def restore(
        self,
        data: Dict[str, Any],
        pipeline: Optional[EvaluationPipeline] = None,
        target_lhs: Optional[ExprNode] = None,
    ) -> None:
        """Restore island population and state from serialized data."""
        from evolutionary_math.core.ast import expr_from_dict
        from evolutionary_math.evolution.individual import Individual
        from evolutionary_math.evolution.fitness import _extract_subexpr_sexprs

        self.island_id = data.get("island_id", self.island_id)
        self.regime = data.get("regime", self.regime)
        self.generation = data.get("generation", 0)

        restored_pop = []
        for item in data.get("population", []):
            try:
                cand = expr_from_dict(item["candidate_ast"])
                ind = Individual(
                    candidate=cand,
                    generation=item.get("generation", 0),
                    id=item.get("id") or None,
                    parent_ids=tuple(item.get("parent_ids", ())),
                    operator_applied=item.get("operator_applied", None),
                    fitness_vector=tuple(item.get("fitness_vector", (0.0, 0.0, 0.0))),
                    rank=item.get("rank", 0),
                    crowding_distance=item.get("crowding_distance", 0.0),
                )
                restored_pop.append(ind)
            except Exception:
                continue

        if restored_pop:
            if pipeline is not None and target_lhs is not None:
                all_subexprs = set()
                for ind in restored_pop:
                    all_subexprs.update(_extract_subexpr_sexprs(ind.candidate))
                for ind in restored_pop:
                    fit_vec, eval_res = evaluate_individual_fitness(
                        ind.candidate, target_lhs, pipeline, all_subexprs
                    )
                    ind.fitness_vector = fit_vec
                    ind.evaluation_result = eval_res
            self.population = restored_pop
            self.population_size = len(restored_pop)



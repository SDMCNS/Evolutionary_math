"""Multi-island evolutionary discovery coordinator with ring migration and telemetry."""

import time
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from evolutionary_math.core.ast import ExprNode
from evolutionary_math.evaluation.pipeline import EvaluationPipeline
from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.grammar.generator import ExpressionGenerator
from evolutionary_math.evolution.individual import Individual
from evolutionary_math.evolution.island import Island
from evolutionary_math.storage.knowledge_base import KnowledgeBase, StoredTheorem, SearchBranchRecord
from evolutionary_math.utils.formatting import format_clean_formula
from evolutionary_math.advisory.controller import AdvisoryController
from evolutionary_math.advisory.schema import AdvisoryResponse
from evolutionary_math.evolution.rational_solver import ExactPolynomialSolver
from evolutionary_math.core.domains import get_domain_profile


@dataclass
class DiscoveryTelemetry:
    """Generation-level search telemetry."""
    generation: int
    best_validity: float
    pareto_front_size: int
    total_individuals_evaluated: int
    elapsed_time_sec: float
    best_candidate_str: str
    advisory_intervention: Optional[str] = None


@dataclass
class EngineRunResult:
    """Summary result of an evolutionary discovery run."""
    success: bool
    discovered_theorem: Optional[StoredTheorem]
    total_generations: int
    total_time_sec: float
    telemetry_history: List[DiscoveryTelemetry] = field(default_factory=list)
    advisory_interventions_count: int = 0


class EvolutionEngine:
    """Coordinates multi-island evolutionary search, migration, and verification."""

    def __init__(
        self,
        grammar: Optional[Grammar] = None,
        num_islands: int = 3,
        island_population_size: int = 40,
        migration_interval: int = 10,
        num_migrants: int = 2,
        pipeline: Optional[EvaluationPipeline] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        advisory_controller: Optional[AdvisoryController] = None,
        mode: str = "algebra",
        auto_promote_lemmas: bool = True,
        enable_polynomial_solver: bool = True,
        seed: Optional[int] = None,
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.mode = mode
        profile = get_domain_profile(mode)
        self.grammar = grammar or profile.create_grammar()
        self.pipeline = pipeline or profile.create_pipeline()
        self.kb = knowledge_base or KnowledgeBase(":memory:")
        self.advisory_controller = advisory_controller
        self.auto_promote_lemmas = auto_promote_lemmas
        self.enable_polynomial_solver = enable_polynomial_solver and profile.enable_discrete_solver
        self.migration_interval = migration_interval
        self.num_migrants = num_migrants

        # Promote any pre-existing verified lemmas from knowledge base into grammar
        if self.auto_promote_lemmas:
            self.kb.promote_lemmas_to_grammar(self.grammar)

        # Initialize islands with heterogeneous regimes
        regimes = ["balanced", "exploration", "exploitation"]
        self.islands: List[Island] = []
        for i in range(num_islands):
            regime = regimes[i % len(regimes)]
            island_rng = random.Random(self.rng.randint(0, 1000000))
            gen = ExpressionGenerator(self.grammar, rng=island_rng)
            island = Island(
                island_id=i,
                population_size=island_population_size,
                regime=regime,
                generator=gen,
                rng=island_rng,
            )
            self.islands.append(island)

    def run(
        self,
        target_lhs: ExprNode,
        max_generations: int = 200,
        experiment_id: str = "exp",
        callback: Optional[Any] = None,
    ) -> EngineRunResult:
        """Run the autonomous evolutionary discovery loop."""
        start_time = time.perf_counter()

        # 0. Check if target is already subsumed by an existing generalized theorem in KB
        subsuming = self.kb.find_subsuming_theorem(target_lhs)
        if subsuming is not None:
            gen_th, param_sub = subsuming
            from evolutionary_math.core.generalization import instantiate_generalized_formula
            concrete_formula = instantiate_generalized_formula(gen_th.definition_ast, param_sub)
            from evolutionary_math.evolution.individual import Individual
            ind = Individual(candidate=concrete_formula, generation=0)
            from evolutionary_math.evaluation.tier2_symbolic import Tier2Result
            ind.evaluation_result = Tier2Result(
                is_verified=True,
                proof_method=f"subsumed_by_{gen_th.id[:8]}",
                simplified_difference="0",
                runtime_ms=(time.perf_counter() - start_time) * 1000.0,
            )
            rec = SearchBranchRecord(
                id=f"sub_{gen_th.id[:6]}",
                experiment_id=experiment_id,
                target_str=str(target_lhs),
                generation=0,
                candidate_str=str(concrete_formula),
                clean_formula=str(concrete_formula),
                validity=1.0,
                status="breakthrough",
                operator="subsumption",
                reason=f"Subsumed as instance of general theorem {gen_th.name or gen_th.id} with {param_sub}",
                timestamp=time.time(),
            )
            self.kb.record_branch(rec)
            run_res = EngineRunResult(
                success=True,
                discovered_theorem=gen_th,
                total_generations=0,
                total_time_sec=time.perf_counter() - start_time,
                telemetry_history=[],
                advisory_interventions_count=0,
            )
            self.kb.record_target_attempt(target_lhs, run_res, domain_mode=self.mode, experiment_id=experiment_id)
            return run_res

        # 0b. Auto-generalization: If target belongs to an unproven parametric family, solve & prove generalized meta-theorem
        from evolutionary_math.core.generalization import extract_parametric_family
        family_info = extract_parametric_family(target_lhs)
        if family_info is not None and self.enable_polynomial_solver:
            gen_tgt, param_name, c_val = family_info
            gen_solutions = ExactPolynomialSolver.solve(gen_tgt)
            if gen_solutions:
                gen_sol = gen_solutions[0]
                eval_res = self.pipeline.evaluate(gen_tgt, gen_sol)
                if eval_res.is_verified:
                    from evolutionary_math.evolution.individual import Individual
                    from evolutionary_math.core.generalization import instantiate_generalized_formula
                    ind_gen = Individual(candidate=gen_sol, generation=0)
                    ind_gen.evaluation_result = eval_res
                    gen_th = self.kb.store_discovery(
                        individual=ind_gen,
                        target_lhs=gen_tgt,
                        experiment_id=experiment_id,
                    )
                    concrete_formula = instantiate_generalized_formula(gen_sol, {param_name: c_val})
                    ind_concrete = Individual(candidate=concrete_formula, generation=0)
                    ind_concrete.evaluation_result = eval_res
                    rec = SearchBranchRecord(
                        id=f"gen_{gen_th.id[:6]}",
                        experiment_id=experiment_id,
                        target_str=str(target_lhs),
                        generation=0,
                        candidate_str=str(concrete_formula),
                        clean_formula=str(concrete_formula),
                        validity=1.0,
                        status="breakthrough",
                        operator="generalization",
                        reason=f"Solved via generalized meta-theorem {gen_th.name or gen_th.id} ({param_name}={c_val})",
                        timestamp=time.time(),
                    )
                    self.kb.record_branch(rec)
                    run_res = EngineRunResult(
                        success=True,
                        discovered_theorem=gen_th,
                        total_generations=0,
                        total_time_sec=time.perf_counter() - start_time,
                        telemetry_history=[],
                        advisory_interventions_count=0,
                    )
                    self.kb.record_target_attempt(target_lhs, run_res, domain_mode=self.mode, experiment_id=experiment_id)
                    return run_res

        if self.advisory_controller is not None:
            self.advisory_controller.reset_for_target()

        # 1. Initialize all islands
        for island in self.islands:
            island.initialize(min_depth=2, max_depth=4)

        # 1b. Exact polynomial finite difference solver (discrete calculus)
        if self.enable_polynomial_solver and self.islands:
            poly_candidates = ExactPolynomialSolver.solve(target_lhs)
            for cand in poly_candidates:
                self.islands[0].inject_individual(cand, operator_applied="discrete_calculus_solve")

        telemetry_history: List[DiscoveryTelemetry] = []
        target_str = str(target_lhs)
        search_branches: List[SearchBranchRecord] = []
        high_water_validity = -1.0
        last_milestone_id: Optional[str] = None
        last_milestone_str: Optional[str] = None
        total_evaluations = 0
        advisory_interventions = 0

        for gen in range(1, max_generations + 1):
            discovered: Optional[Individual] = None

            # 2. Step each island
            for island in self.islands:
                disc = island.step(target_lhs, self.pipeline)
                total_evaluations += island.population_size
                if disc and disc.is_verified and discovered is None:
                    discovered = disc

            # 3. Check for strategic advisory intervention if enabled
            intervention_note: Optional[str] = None
            if self.advisory_controller is not None:
                advice = self.advisory_controller.check_and_apply_guidance(
                    generation=gen,
                    islands=self.islands,
                    grammar=self.grammar,
                    known_lemmas_count=len(self.kb.get_all_theorems()),
                )
                if advice is not None:
                    advisory_interventions += 1
                    intervention_note = f"[{advice.regime_selection}] {advice.diagnosis[:60]}..."

            # 4. Gather generation telemetry
            all_individuals = [ind for island in self.islands for ind in island.population]
            best_ind = max(all_individuals, key=lambda ind: ind.validity)
            pareto_count = sum(1 for ind in all_individuals if ind.rank == 1)
            elapsed = time.perf_counter() - start_time

            # Record milestone improvement if validity advanced
            if best_ind.validity > high_water_validity + 0.005:
                high_water_validity = best_ind.validity
                rec = SearchBranchRecord(
                    id=best_ind.id,
                    experiment_id=experiment_id,
                    target_str=target_str,
                    generation=gen,
                    candidate_str=str(best_ind.candidate),
                    clean_formula=format_clean_formula(best_ind.candidate),
                    validity=best_ind.validity,
                    status="milestone",
                    operator=best_ind.operator_applied,
                    parent_id=last_milestone_id,
                    parent_str=last_milestone_str,
                    reason=f"Validity advanced to {best_ind.validity:.4f}",
                    timestamp=time.time(),
                )
                search_branches.append(rec)
                last_milestone_id = best_ind.id
                last_milestone_str = str(best_ind.candidate)

            # Sample key falsified counterexamples to log failed branches
            falsified = [
                ind for ind in all_individuals 
                if ind.validity < 0.99 and ind.evaluation_result and not ind.evaluation_result.is_verified
            ]
            if falsified and (gen % 4 == 1 or gen == 1 or gen == max_generations):
                f_sample = max(falsified, key=lambda ind: ind.validity)
                fail_reason = "Falsified on test domain"
                if f_sample.evaluation_result and f_sample.evaluation_result.tier1_result:
                    fail_reason = f"Fails test domain (residual {f_sample.evaluation_result.tier1_result.max_residual:.2f})"
                rec_fail = SearchBranchRecord(
                    id=f_sample.id,
                    experiment_id=experiment_id,
                    target_str=target_str,
                    generation=gen,
                    candidate_str=str(f_sample.candidate),
                    clean_formula=format_clean_formula(f_sample.candidate),
                    validity=f_sample.validity,
                    status="falsified",
                    operator=f_sample.operator_applied,
                    parent_id=last_milestone_id,
                    parent_str=last_milestone_str,
                    reason=fail_reason,
                    timestamp=time.time(),
                )
                search_branches.append(rec_fail)

            if intervention_note:
                rec_adv = SearchBranchRecord(
                    id=f"adv_{gen}_{time.time_ns() % 10000}",
                    experiment_id=experiment_id,
                    target_str=target_str,
                    generation=gen,
                    candidate_str="",
                    clean_formula="",
                    validity=best_ind.validity,
                    status="intervention",
                    operator="advisory",
                    parent_id=last_milestone_id,
                    parent_str=last_milestone_str,
                    reason=intervention_note,
                    timestamp=time.time(),
                )
                search_branches.append(rec_adv)

            telem = DiscoveryTelemetry(
                generation=gen,
                best_validity=best_ind.validity,
                pareto_front_size=pareto_count,
                total_individuals_evaluated=total_evaluations,
                elapsed_time_sec=elapsed,
                best_candidate_str=str(best_ind.candidate),
                advisory_intervention=intervention_note,
            )
            telemetry_history.append(telem)

            if callback:
                callback(telem)

            # 5. Check for breakthrough discovery
            if discovered is not None:
                # Generate plain-English intuitive explanation
                client = self.advisory_controller.client if self.advisory_controller else None
                if client is None:
                    from evolutionary_math.advisory.client import MockAdvisoryClient
                    client = MockAdvisoryClient()

                try:
                    from evolutionary_math.utils.formatting import to_latex
                    latex_str = to_latex(discovered.candidate)
                except Exception:
                    latex_str = str(discovered.candidate)

                proof_method = (discovered.evaluation_result.proof_method or "unknown") if discovered.evaluation_result else "symbolic_induction"
                deps = list(self.kb._extract_dependencies(discovered.candidate))

                try:
                    explanation = client.explain_discovery(
                        target_str=str(target_lhs),
                        discovery_str=str(discovered.candidate),
                        latex_str=latex_str,
                        proof_method=proof_method,
                        dependencies=deps,
                    )
                except Exception:
                    explanation = f"Identity {target_lhs} = {discovered.candidate} verified via {proof_method}."

                stored = self.kb.store_discovery(
                    discovered, target_lhs, experiment_id=experiment_id, explanation=explanation
                )
                if self.auto_promote_lemmas and stored.definition_ast is not None:
                    lemma_name = f"L_{stored.id[:4]}"
                    self.grammar.promote_lemma(lemma_name, stored.definition_ast)

                # Record breakthrough in history
                rec_bt = SearchBranchRecord(
                    id=discovered.id,
                    experiment_id=experiment_id,
                    target_str=target_str,
                    generation=gen,
                    candidate_str=str(discovered.candidate),
                    clean_formula=format_clean_formula(discovered.candidate),
                    validity=1.0,
                    status="breakthrough",
                    operator=discovered.operator_applied,
                    parent_id=last_milestone_id,
                    parent_str=last_milestone_str,
                    reason=f"Formally proven via {proof_method}",
                    timestamp=time.time(),
                )
                search_branches.append(rec_bt)
                self.kb.record_branches(search_branches)

                run_res = EngineRunResult(
                    success=True,
                    discovered_theorem=stored,
                    total_generations=gen,
                    total_time_sec=elapsed,
                    telemetry_history=telemetry_history,
                    advisory_interventions_count=advisory_interventions,
                )
                if self.kb is not None:
                    self.kb.record_target_attempt(target_lhs, run_res, domain_mode=self.mode, experiment_id=experiment_id)
                return run_res

            # 6. Periodic Ring Migration between islands
            if gen % self.migration_interval == 0 and len(self.islands) > 1:
                self._migrate_ring()

        # Reached max generations without formal verification
        self.kb.record_branches(search_branches)
        elapsed = time.perf_counter() - start_time
        run_res = EngineRunResult(
            success=False,
            discovered_theorem=None,
            total_generations=max_generations,
            total_time_sec=elapsed,
            telemetry_history=telemetry_history,
            advisory_interventions_count=advisory_interventions,
        )
        if self.kb is not None:
            self.kb.record_target_attempt(target_lhs, run_res, domain_mode=self.mode, experiment_id=experiment_id)
        return run_res

    def _migrate_ring(self) -> None:
        """Execute unidirectional ring migration among islands: 0 -> 1 -> 2 -> ... -> 0."""
        n = len(self.islands)
        emigrants_list = [island.get_emigrants(self.num_migrants) for island in self.islands]

        for i in range(n):
            next_island_idx = (i + 1) % n
            # Create fresh copies of migrating individuals
            migrants = [
                Individual(
                    candidate=em.candidate,
                    generation=em.generation,
                    parent_ids=(em.id,),
                    operator_applied="migrant",
                    fitness_vector=em.fitness_vector,
                    evaluation_result=em.evaluation_result,
                )
                for em in emigrants_list[i]
            ]
            self.islands[next_island_idx].accept_immigrants(migrants)


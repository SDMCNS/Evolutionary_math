"""Autonomous mathematical discovery campaign runner."""

import time
from typing import Optional, Callable, List
from evolutionary_math.core.ast import ExprNode
from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.evolution.engine import EvolutionEngine, EngineRunResult, DiscoveryTelemetry
from evolutionary_math.storage.knowledge_base import KnowledgeBase, StoredTheorem
from evolutionary_math.core.domains import get_domain_profile
from evolutionary_math.advisory.controller import AdvisoryController
from evolutionary_math.campaign.agenda import ProblemSpaceAgenda


class AutonomousDiscoveryCampaign:
    """Orchestrates an open-ended autonomous discovery loop across an evolving agenda of problem spaces."""

    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        agenda: Optional[ProblemSpaceAgenda] = None,
        advisory_controller: Optional[AdvisoryController] = None,
        num_islands: int = 4,
        island_population_size: int = 40,
        generations_per_target: int = 50,
        mode: str = "algebra",
        seed: Optional[int] = 42,
    ):
        self.kb = knowledge_base or KnowledgeBase("autonomous_discoveries.db")
        self.agenda = agenda or ProblemSpaceAgenda(mode=mode)
        self.advisory_controller = advisory_controller
        self.num_islands = num_islands
        self.island_population_size = island_population_size
        self.generations_per_target = generations_per_target
        self.mode = mode
        self.seed = seed

        profile = get_domain_profile(mode)
        self.grammar = profile.create_grammar()
        # Promote any pre-existing knowledge from prior sessions
        self.kb.promote_lemmas_to_grammar(self.grammar)

        self.discovered_theorems: List[StoredTheorem] = []

    def run(
        self,
        max_theorems: Optional[int] = None,
        on_breakthrough: Optional[Callable[[StoredTheorem, EngineRunResult], None]] = None,
        on_telemetry: Optional[Callable[[ExprNode, DiscoveryTelemetry], None]] = None,
    ) -> List[StoredTheorem]:
        """Launch the autonomous discovery campaign.

        If max_theorems is None, the campaign runs continuously/indefinitely across an infinite target stream.
        """
        start_time = time.perf_counter()
        target_stream = self.agenda.generate_targets()

        target_idx = 0
        for target in target_stream:
            target_idx += 1
            if max_theorems is not None and len(self.discovered_theorems) >= max_theorems:
                break

            # Skip targets that have already been proven and recorded
            if self.kb.is_target_solved(target):
                continue

            # 1. Update grammar with all currently known lemmas
            self.kb.promote_lemmas_to_grammar(self.grammar)

            # 2. Configure engine for this target
            engine_seed = (self.seed + target_idx * 17) if self.seed is not None else None
            engine = EvolutionEngine(
                grammar=self.grammar,
                num_islands=self.num_islands,
                island_population_size=self.island_population_size,
                migration_interval=5,
                knowledge_base=self.kb,
                advisory_controller=self.advisory_controller,
                mode=self.mode,
                auto_promote_lemmas=True,
                seed=engine_seed,
            )

            def telemetry_wrapper(telem: DiscoveryTelemetry):
                if on_telemetry:
                    on_telemetry(target, telem)

            # 3. Execute evolutionary search
            result = engine.run(
                target_lhs=target,
                max_generations=self.generations_per_target,
                experiment_id=f"campaign_target_{target_idx}",
                callback=telemetry_wrapper if on_telemetry else None,
            )

            # 4. Handle breakthrough
            if result.success and result.discovered_theorem is not None:
                th = result.discovered_theorem
                self.discovered_theorems.append(th)

                # Immediately promote new lemma into campaign grammar for subsequent targets
                lemma_name = f"L_{th.id[:4]}"
                if th.definition_ast is not None:
                    self.grammar.promote_lemma(lemma_name, th.definition_ast)

                if on_breakthrough:
                    on_breakthrough(th, result)

        return self.discovered_theorems


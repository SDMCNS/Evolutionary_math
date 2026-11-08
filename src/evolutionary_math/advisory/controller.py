"""Advisory controller managing LLM triggering, boundary validation, and parameter adaptation."""

import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Optional, Dict
from evolutionary_math.core.ast import parse_expr_str
from evolutionary_math.evolution.island import Island
from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.advisory.schema import AdvisoryRequest, AdvisoryResponse
from evolutionary_math.advisory.client import BaseAdvisoryClient

logger = logging.getLogger(__name__)


class AdvisoryController:
    """Manages the air-gapped advisory interface between the evolutionary engine and the LLM."""

    def __init__(
        self,
        client: Optional[BaseAdvisoryClient] = None,
        stagnation_threshold: int = 8,
        epoch_interval: int = 25,
        cooldown_generations: int = 5,
        async_mode: bool = False,
    ):
        self.client = client
        self.stagnation_threshold = stagnation_threshold
        self.epoch_interval = epoch_interval
        self.cooldown_generations = cooldown_generations
        self.async_mode = async_mode

        self.last_advisory_generation: int = -999
        self.stagnation_counter: int = 0
        self.best_validity_observed: float = -1.0
        self.advisory_history: List[AdvisoryResponse] = []

        self._executor = ThreadPoolExecutor(max_workers=1) if async_mode else None
        self._pending_future: Optional[Future] = None

    def reset_for_target(self) -> None:
        """Reset target-specific search telemetry and cooldown timers for a fresh problem space."""
        self.last_advisory_generation = -999
        self.stagnation_counter = 0
        self.best_validity_observed = -1.0
        self._pending_future = None

    def check_and_apply_guidance(
        self,
        generation: int,
        islands: List[Island],
        grammar: Grammar,
        known_lemmas_count: int = 0,
        recent_operator_success_rates: Optional[Dict[str, float]] = None,
    ) -> Optional[AdvisoryResponse]:
        """Evaluate if strategic intervention is warranted, query advisory client, and adapt search parameters."""
        if self.client is None:
            return None

        # Check if an asynchronous advisory call has completed
        if self._pending_future is not None:
            if self._pending_future.done():
                try:
                    response = self._pending_future.result()
                except Exception as e:
                    logger.warning(f"Async advisory call raised error: {e}")
                    response = None
                self._pending_future = None

                if response is not None:
                    self._apply_advice(response, islands, grammar)
                    self.last_advisory_generation = generation
                    self.stagnation_counter = 0
                    self.advisory_history.append(response)
                    return response
            else:
                # Still running in background: allow evolution to continue unhindered
                return None

        # Detect new target run if generation reset
        if generation < self.last_advisory_generation:
            self.reset_for_target()

        # 1. Update stagnation counter
        current_best = max((ind.validity for island in islands for ind in island.population), default=0.0)
        if self.best_validity_observed < 0.0:
            self.best_validity_observed = current_best
            self.stagnation_counter = 0
        elif current_best > self.best_validity_observed + 0.01:
            self.best_validity_observed = current_best
            self.stagnation_counter = 0
        else:
            self.stagnation_counter += 1

        # 2. Check triggering conditions
        since_last = generation - self.last_advisory_generation
        if since_last < self.cooldown_generations:
            return None

        should_trigger = (
            self.stagnation_counter >= self.stagnation_threshold
            or (generation > 0 and generation % self.epoch_interval == 0)
        )

        if not should_trigger:
            return None

        # 3. Formulate structured request
        from evolutionary_math.advisory.telemetry import TelemetryPacker
        request: AdvisoryRequest = TelemetryPacker.pack(
            generation=generation,
            islands=islands,
            stagnation_counter=self.stagnation_counter,
            known_lemmas_count=known_lemmas_count,
            recent_operator_success_rates=recent_operator_success_rates or {},
        )

        # 4. Request advice through air-gap (non-blocking if async_mode is enabled)
        if self.async_mode and self._executor is not None:
            self._pending_future = self._executor.submit(self.client.request_advice, request)
            return None

        # Synchronous execution
        try:
            response = self.client.request_advice(request)
        except Exception as e:
            logger.warning(f"Advisory client raised error: {e}")
            response = None

        if response is None:
            return None

        # 5. Apply validated strategic advice
        self._apply_advice(response, islands, grammar)
        self.last_advisory_generation = generation
        self.stagnation_counter = 0
        self.advisory_history.append(response)
        return response

    def _apply_advice(self, response: AdvisoryResponse, islands: List[Island], grammar: Grammar) -> None:
        """Apply LLM recommendations to islands and grammar rules."""
        # 1. Adjust grammar rule weights
        for bias in response.grammar_biases:
            symbol = int(bias.symbol) if bias.symbol.isdigit() else bias.symbol
            grammar.adjust_rule_weight(bias.head, symbol, bias.multiplier)

        # 2. Adjust operator weights
        weights_dict = {
            "subtree_mutation": response.operator_weight_adjustments.subtree_mutation,
            "crossover": response.operator_weight_adjustments.crossover,
            "constant_perturbation": response.operator_weight_adjustments.constant_perturbation,
            "hoist": response.operator_weight_adjustments.hoist,
        }
        # Normalize weights
        total_w = sum(weights_dict.values())
        if total_w > 0:
            norm_weights = {k: v / total_w for k, v in weights_dict.items()}
        else:
            norm_weights = Island.REGIME_WEIGHTS["balanced"]

        # Apply to each island's active regime
        for island in islands:
            island.operator_weights = dict(norm_weights)
            # If advisory suggests a specific regime, update exploratory/exploitative island
            if response.regime_selection == "EXPLORATION":
                if island.island_id % 2 == 1:
                    island.regime = "exploration"
            elif response.regime_selection == "EXPLOITATION":
                if island.island_id % 2 == 1:
                    island.regime = "exploitation"

        # 3. Inject suggested candidate subtrees as immigrant seeds into exploratory islands
        if response.suggested_subtrees:
            for expr_s in response.suggested_subtrees:
                try:
                    cand_node = parse_expr_str(expr_s)
                    for island in islands:
                        if island.regime == "exploration" or len(islands) == 1:
                            island.inject_individual(cand_node, operator_applied="advisory_seed")
                except Exception as e:
                    logger.debug(f"Failed to parse and inject suggested subtree '{expr_s}': {e}")



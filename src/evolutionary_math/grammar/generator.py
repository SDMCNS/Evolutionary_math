"""Grammar-guided expression generator with grow, full, and ramped half-and-half initialization."""

import random
from typing import Optional, List
from evolutionary_math.core.ast import ExprNode, expr_factory
from evolutionary_math.grammar.rules import Grammar, ProductionRule


class ExpressionGenerator:
    """Generates valid mathematical ASTs using a grammar and derivation strategy."""

    def __init__(self, grammar: Grammar, rng: Optional[random.Random] = None):
        self.grammar = grammar
        self.rng = rng or random.Random()

    def generate(self, max_depth: int = 4, method: str = "grow") -> ExprNode:
        """Generate an expression tree using the specified method ('grow' or 'full')."""
        return self._generate_node(self.grammar.start_symbol, current_depth=1, max_depth=max_depth, method=method)

    def _generate_node(self, head: str, current_depth: int, max_depth: int, method: str) -> ExprNode:
        rules = self.grammar.get_rules(head)
        if not rules:
            # Fallback to general terminal
            rules = self.grammar.get_rules("TERMINAL")
            if not rules:
                return expr_factory.constant(1)

        # Force terminal selection if max_depth reached
        if current_depth >= max_depth:
            terminal_rules = [r for r in rules if len(r.body) == 0]
            if not terminal_rules:
                terminal_rules = self.grammar.get_rules("TERMINAL")
            if terminal_rules:
                rule = self._select_rule(terminal_rules)
            else:
                return expr_factory.constant(1)
        else:
            if method == "full":
                # In full method, prefer recursive rules with children until max_depth
                non_terminal_rules = [r for r in rules if len(r.body) > 0]
                if non_terminal_rules:
                    rule = self._select_rule(non_terminal_rules)
                else:
                    rule = self._select_rule(rules)
            else:  # "grow"
                rule = self._select_rule(rules)

        # Build ExprNode based on production rule
        if rule.rule_type == "const":
            return expr_factory.constant(rule.symbol, rule.math_type)
        elif rule.rule_type == "var":
            return expr_factory.variable(str(rule.symbol), rule.math_type)
        elif rule.rule_type == "lemma":
            lemma_id = str(rule.symbol)
            lemma_def = self.grammar.get_lemma_definition(lemma_id)
            if lemma_def is None:
                return expr_factory.variable("n")
            arg_node = self._generate_node(rule.body[0], current_depth + 1, max_depth, method)
            return expr_factory.lemma(lemma_id, arg_node, lemma_def, math_type=rule.math_type)
        elif rule.rule_type == "op":
            children = tuple(
                self._generate_node(child_head, current_depth + 1, max_depth, method)
                for child_head in rule.body
            )
            return expr_factory.op(str(rule.symbol), *children, math_type=rule.math_type)
        else:
            raise ValueError(f"Unknown rule type: {rule.rule_type}")

    def _select_rule(self, rules: List[ProductionRule]) -> ProductionRule:
        weights = [r.weight for r in rules]
        total_weight = sum(weights)
        if total_weight <= 0:
            return self.rng.choice(rules)
        return self.rng.choices(rules, weights=weights, k=1)[0]

    def ramped_half_and_half(self, population_size: int, min_depth: int = 2, max_depth: int = 5) -> List[ExprNode]:
        """Generate a diverse population using ramped half-and-half initialization."""
        population: List[ExprNode] = []
        depths = list(range(min_depth, max_depth + 1))
        per_depth = max(1, population_size // len(depths))

        for d in depths:
            for i in range(per_depth):
                method = "full" if i % 2 == 0 else "grow"
                expr = self.generate(max_depth=d, method=method)
                population.append(expr)

        # Fill remaining slots
        while len(population) < population_size:
            d = self.rng.choice(depths)
            method = self.rng.choice(["grow", "full"])
            population.append(self.generate(max_depth=d, method=method))

        return population[:population_size]


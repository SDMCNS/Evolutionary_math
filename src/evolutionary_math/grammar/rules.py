"""Context-Free Grammar and production rules for strongly-typed expressions."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Union, Optional
from evolutionary_math.core.types import MathType
from evolutionary_math.core.ast import ExprNode


@dataclass(frozen=True)
class ProductionRule:
    """A grammar production rule."""
    head: str  # e.g., "EXPR", "TERM", "VAR", "CONST"
    rule_type: str  # "op", "var", "const", "lemma"
    symbol: Union[str, int, float]  # "+", "n", 2, "lemma_1", etc.
    body: Tuple[str, ...] = ()  # Child non-terminals, e.g. ("EXPR", "EXPR")
    weight: float = 1.0
    math_type: MathType = MathType.REAL


class Grammar:
    """Context-Free Grammar managing production rules, dynamic weights, and promoted lemmas."""

    def __init__(self, start_symbol: str = "EXPR"):
        self.start_symbol = start_symbol
        self._rules_by_head: Dict[str, List[ProductionRule]] = {}
        self._lemmas: Dict[str, ExprNode] = {}

    def add_rule(self, rule: ProductionRule) -> None:
        if rule.head not in self._rules_by_head:
            self._rules_by_head[rule.head] = []
        self._rules_by_head[rule.head].append(rule)

    def get_rules(self, head: str) -> List[ProductionRule]:
        return self._rules_by_head.get(head, [])

    @property
    def rules(self) -> List[ProductionRule]:
        """Return a flat list of all registered production rules across all non-terminals."""
        return [r for head_rules in self._rules_by_head.values() for r in head_rules]

    def promote_lemma(self, lemma_id: str, definition: ExprNode, weight: float = 2.0) -> None:
        """Promote a verified theorem into an active grammar building block (ADF)."""
        self._lemmas[lemma_id] = definition
        rule = ProductionRule(
            head="EXPR",
            rule_type="lemma",
            symbol=lemma_id,
            body=("EXPR",),
            weight=weight,
            math_type=definition.math_type,
        )
        self.add_rule(rule)

    def get_lemma_definition(self, lemma_id: str) -> Optional[ExprNode]:
        return self._lemmas.get(lemma_id)

    @property
    def promoted_lemmas(self) -> Dict[str, ExprNode]:
        return dict(self._lemmas)

    def adjust_rule_weight(self, head: str, symbol: Union[str, int, float], multiplier: float) -> None:
        """Adjust production rule weight (used for LLM guidance or adaptive heuristics)."""
        rules = self.get_rules(head)
        for i, r in enumerate(rules):
            if r.symbol == symbol:
                new_rule = ProductionRule(
                    head=r.head,
                    rule_type=r.rule_type,
                    symbol=r.symbol,
                    body=r.body,
                    weight=max(0.01, r.weight * multiplier),
                    math_type=r.math_type,
                )
                rules[i] = new_rule

    @classmethod
    def default_summation_rhs_grammar(cls, variables: Optional[List[str]] = None) -> "Grammar":
        """Pre-configured grammar tailored for discovering closed-form summation formulas."""
        g = cls(start_symbol="EXPR")
        vars_list = variables or ["n"]

        # Recursive Operators on EXPR
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="+", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="-", body=("EXPR", "EXPR"), weight=1.5))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="*", body=("EXPR", "EXPR"), weight=2.5))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="/", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="^", body=("EXPR", "INT_CONST"), weight=1.0))

        # Direct Terminals from EXPR
        for v in vars_list:
            g.add_rule(ProductionRule(head="EXPR", rule_type="var", symbol=v, body=(), weight=3.0))

        for c in [1, 2, 3, 4, 5, 6]:
            g.add_rule(ProductionRule(head="EXPR", rule_type="const", symbol=c, body=(), weight=2.0, math_type=MathType.INTEGER))

        # Integer exponents for powers (INT_CONST)
        for exp_val in [2, 3, 4]:
            g.add_rule(ProductionRule(head="INT_CONST", rule_type="const", symbol=exp_val, body=(), weight=1.0, math_type=MathType.INTEGER))

        # Terminal fallback set (used when max depth is reached)
        for v in vars_list:
            g.add_rule(ProductionRule(head="TERMINAL", rule_type="var", symbol=v, body=(), weight=2.0))
        for c in [1, 2, 3, 4, 5, 6]:
            g.add_rule(ProductionRule(head="TERMINAL", rule_type="const", symbol=c, body=(), weight=1.0, math_type=MathType.INTEGER))

        return g

    @classmethod
    def default_trigonometry_grammar(cls, variables: Optional[List[str]] = None) -> "Grammar":
        """Pre-configured grammar tailored for discovering trigonometric identities."""
        g = cls(start_symbol="EXPR")
        vars_list = variables or ["x"]

        # Binary operators
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="+", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="-", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="*", body=("EXPR", "EXPR"), weight=2.5))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="/", body=("EXPR", "EXPR"), weight=1.5))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="^", body=("EXPR", "INT_CONST"), weight=1.5))

        # Unary trigonometric functions
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="sin", body=("EXPR",), weight=3.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="cos", body=("EXPR",), weight=3.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="tan", body=("EXPR",), weight=1.5))

        # Terminals
        for v in vars_list:
            g.add_rule(ProductionRule(head="EXPR", rule_type="var", symbol=v, body=(), weight=3.0))
        for c in [1, 2]:
            g.add_rule(ProductionRule(head="EXPR", rule_type="const", symbol=c, body=(), weight=2.0, math_type=MathType.INTEGER))

        # Powers (squared is foundational in trig)
        g.add_rule(ProductionRule(head="INT_CONST", rule_type="const", symbol=2, body=(), weight=2.0, math_type=MathType.INTEGER))

        # Terminal fallbacks
        for v in vars_list:
            g.add_rule(ProductionRule(head="TERMINAL", rule_type="var", symbol=v, body=(), weight=2.0))
        for c in [1, 2]:
            g.add_rule(ProductionRule(head="TERMINAL", rule_type="const", symbol=c, body=(), weight=1.0, math_type=MathType.INTEGER))

        return g

    @classmethod
    def default_geometry_grammar(cls, variables: Optional[List[str]] = None) -> "Grammar":
        """Pre-configured grammar tailored for metric geometry, areas, and Euclidean relations."""
        g = cls(start_symbol="EXPR")
        vars_list = variables or ["a", "b"]

        # Binary operators
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="+", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="-", body=("EXPR", "EXPR"), weight=1.5))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="*", body=("EXPR", "EXPR"), weight=2.5))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="/", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="^", body=("EXPR", "INT_CONST"), weight=2.0))

        # Unary radical
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="sqrt", body=("EXPR",), weight=2.5))

        # Terminals
        for v in vars_list:
            g.add_rule(ProductionRule(head="EXPR", rule_type="var", symbol=v, body=(), weight=3.0))
        for c in [1, 2, 3, 4]:
            g.add_rule(ProductionRule(head="EXPR", rule_type="const", symbol=c, body=(), weight=2.0, math_type=MathType.INTEGER))

        # Powers
        for exp_val in [2, 3]:
            g.add_rule(ProductionRule(head="INT_CONST", rule_type="const", symbol=exp_val, body=(), weight=1.0, math_type=MathType.INTEGER))

        # Fallbacks
        for v in vars_list:
            g.add_rule(ProductionRule(head="TERMINAL", rule_type="var", symbol=v, body=(), weight=2.0))
        for c in [1, 2]:
            g.add_rule(ProductionRule(head="TERMINAL", rule_type="const", symbol=c, body=(), weight=1.0, math_type=MathType.INTEGER))

        return g

    @classmethod
    def default_calculus_grammar(cls, variables: Optional[List[str]] = None) -> "Grammar":
        """Pre-configured grammar tailored for continuous analysis and functions."""
        g = cls(start_symbol="EXPR")
        vars_list = variables or ["x"]

        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="+", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="-", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="*", body=("EXPR", "EXPR"), weight=2.5))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="/", body=("EXPR", "EXPR"), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="^", body=("EXPR", "INT_CONST"), weight=1.5))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="sin", body=("EXPR",), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="cos", body=("EXPR",), weight=2.0))
        g.add_rule(ProductionRule(head="EXPR", rule_type="op", symbol="sqrt", body=("EXPR",), weight=1.5))

        for v in vars_list:
            g.add_rule(ProductionRule(head="EXPR", rule_type="var", symbol=v, body=(), weight=3.0))
        for c in [1, 2, 3]:
            g.add_rule(ProductionRule(head="EXPR", rule_type="const", symbol=c, body=(), weight=1.5, math_type=MathType.INTEGER))

        for exp_val in [2, 3]:
            g.add_rule(ProductionRule(head="INT_CONST", rule_type="const", symbol=exp_val, body=(), weight=1.0, math_type=MathType.INTEGER))

        for v in vars_list:
            g.add_rule(ProductionRule(head="TERMINAL", rule_type="var", symbol=v, body=(), weight=2.0))
        for c in [1, 2]:
            g.add_rule(ProductionRule(head="TERMINAL", rule_type="const", symbol=c, body=(), weight=1.0, math_type=MathType.INTEGER))

        return g

    @classmethod
    def for_mode(cls, mode: str, variables: Optional[List[str]] = None) -> "Grammar":
        """Factory creating the appropriate grammar for a specified domain mode."""
        clean_mode = (mode or "algebra").lower().strip()
        if clean_mode in ("trig", "trigonometry"):
            return cls.default_trigonometry_grammar(variables=variables)
        elif clean_mode in ("geom", "geometry"):
            return cls.default_geometry_grammar(variables=variables)
        elif clean_mode in ("calc", "calculus", "analysis"):
            return cls.default_calculus_grammar(variables=variables)
        else:
            return cls.default_summation_rhs_grammar(variables=variables)



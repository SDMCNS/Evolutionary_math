"""Tier 2: Deterministic symbolic verification via SymPy, zero-equivalence, and induction."""

import time
from dataclasses import dataclass
from typing import Optional
import sympy as sp

from evolutionary_math.core.ast import ExprNode, OperatorNode, get_sympy_symbol


@dataclass(frozen=True)
class Tier2Result:
    """Result of Tier 2 symbolic verification."""
    is_verified: bool
    proof_method: Optional[str]
    simplified_difference: Optional[str]
    runtime_ms: float
    error_message: Optional[str] = None


class Tier2SymbolicVerifier:
    """Deterministic symbolic verification engine using SymPy algebraic simplification and induction."""

    def __init__(self, induction_variable: str = "n"):
        self.induction_variable = induction_variable

    def verify(self, lhs: ExprNode, rhs: ExprNode) -> Tier2Result:
        """Attempt to formally establish that LHS = RHS using symbolic computation."""
        start_time = time.perf_counter()

        try:
            # 1. Convert to SymPy expressions
            sp_lhs = lhs.to_sympy()
            sp_rhs = rhs.to_sympy()

            # 2. Check for Inductive Proof on Summation Identities first
            if isinstance(lhs, OperatorNode) and lhs.op == "sum":
                induction_res = self._verify_summation_induction(lhs, rhs)
                if induction_res.is_verified:
                    return induction_res

            # 3. Check for trigonometric zero-equivalence first if trig functions are present
            sp_lhs_eval = sp_lhs.doit() if hasattr(sp_lhs, "doit") else sp_lhs
            has_trig = sp_lhs.has(sp.sin, sp.cos, sp.tan) or sp_rhs.has(sp.sin, sp.cos, sp.tan)
            if has_trig:
                try:
                    trig_diff = sp.trigsimp(sp_lhs_eval - sp_rhs)
                    if trig_diff == 0:
                        runtime = (time.perf_counter() - start_time) * 1000.0
                        return Tier2Result(
                            is_verified=True,
                            proof_method="trigonometric_zero_equivalence",
                            simplified_difference="0",
                            runtime_ms=runtime,
                        )
                except Exception:
                    pass

            # 4. Check for direct algebraic zero-equivalence: simplify(LHS - RHS) == 0
            diff = sp.simplify(sp_lhs_eval - sp_rhs)
            if diff == 0:
                runtime = (time.perf_counter() - start_time) * 1000.0
                return Tier2Result(
                    is_verified=True,
                    proof_method="algebraic_zero_equivalence",
                    simplified_difference="0",
                    runtime_ms=runtime,
                )

            # Try rational simplification (together / cancel / expand)
            expanded_diff = sp.together(sp.cancel(sp_lhs - sp_rhs))
            if expanded_diff == 0:
                runtime = (time.perf_counter() - start_time) * 1000.0
                return Tier2Result(
                    is_verified=True,
                    proof_method="rational_cancellation",
                    simplified_difference="0",
                    runtime_ms=runtime,
                )

            runtime = (time.perf_counter() - start_time) * 1000.0
            return Tier2Result(
                is_verified=False,
                proof_method=None,
                simplified_difference=str(diff),
                runtime_ms=runtime,
            )

        except Exception as e:
            runtime = (time.perf_counter() - start_time) * 1000.0
            return Tier2Result(
                is_verified=False,
                proof_method=None,
                simplified_difference=None,
                runtime_ms=runtime,
                error_message=str(e),
            )

    def _verify_summation_induction(self, sum_node: OperatorNode, rhs_node: ExprNode) -> Tier2Result:
        """Formally verify sum_{k=1}^n(term(k)) = RHS(n) via mathematical induction.

        Proof structure:
        Base Case:
            Check sum_{k=1}^1(term(k)) == RHS(1).
        Inductive Step:
            Assume sum_{k=1}^n(term(k)) == RHS(n).
            Show RHS(n) - RHS(n-1) == term(n).
        """
        start_time = time.perf_counter()

        term_ast = sum_node.children[0]
        n_sym = get_sympy_symbol(self.induction_variable)
        k_sym = get_sympy_symbol("k")

        sp_term = term_ast.to_sympy()
        sp_rhs = rhs_node.to_sympy()

        # 1. Base Step (n = 1): term(1) == RHS(1)
        term_at_1 = sp_term.subs(k_sym, 1)
        rhs_at_1 = sp_rhs.subs(n_sym, 1)
        base_diff = sp.simplify(term_at_1 - rhs_at_1)

        if base_diff != 0:
            runtime = (time.perf_counter() - start_time) * 1000.0
            return Tier2Result(
                is_verified=False,
                proof_method=None,
                simplified_difference=f"Base step failed at n=1: {term_at_1} != {rhs_at_1}",
                runtime_ms=runtime,
            )

        # 2. Inductive Step: RHS(n) - RHS(n - 1) - term(n) == 0
        rhs_prev = sp_rhs.subs(n_sym, n_sym - 1)
        term_at_n = sp_term.subs(k_sym, n_sym)

        step_diff = sp.simplify(sp_rhs - rhs_prev - term_at_n)
        if step_diff == 0:
            runtime = (time.perf_counter() - start_time) * 1000.0
            return Tier2Result(
                is_verified=True,
                proof_method="mathematical_induction",
                simplified_difference="0",
                runtime_ms=runtime,
            )

        # Try rational simplification on inductive step
        step_diff_together = sp.together(sp.cancel(sp_rhs - rhs_prev - term_at_n))
        if step_diff_together == 0:
            runtime = (time.perf_counter() - start_time) * 1000.0
            return Tier2Result(
                is_verified=True,
                proof_method="mathematical_induction_rational",
                simplified_difference="0",
                runtime_ms=runtime,
            )

        runtime = (time.perf_counter() - start_time) * 1000.0
        return Tier2Result(
            is_verified=False,
            proof_method=None,
            simplified_difference=f"Inductive step failed: diff = {step_diff}",
            runtime_ms=runtime,
        )

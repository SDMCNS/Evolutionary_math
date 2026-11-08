"""Exact rational polynomial solver using discrete calculus finite difference tables."""

import logging
from typing import List, Optional, Tuple
import sympy as sp
from fractions import Fraction

from evolutionary_math.core.ast import ExprNode, OperatorNode, from_sympy, expr_factory
from evolutionary_math.core.canonicalizer import canonicalize

logger = logging.getLogger(__name__)


class ExactPolynomialSolver:
    """Detects and solves polynomial closed forms for summation targets via finite differences or symbolic summation.

    By the Fundamental Theorem of Discrete Calculus, if a target function sequence Y[n]
    has constant d-th order differences (Delta^d Y = c != 0 and Delta^(d+1) Y = 0),
    the closed form is guaranteed to be a polynomial of degree d.
    """

    @classmethod
    def solve(
        cls,
        target_lhs: ExprNode,
        max_degree: int = 5,
        num_samples: int = 8,
    ) -> List[ExprNode]:
        """Attempt to derive an exact rational polynomial closed form for target_lhs.

        Returns a list of candidate ExprNodes (factored and expanded) if a polynomial
        signature is verified, or an empty list if non-polynomial.
        """
        # 1. Fast symbolic polynomial summation (handles both numeric and parameterized variables like m, c)
        if isinstance(target_lhs, OperatorNode) and target_lhs.op == "sum":
            try:
                term_ast = target_lhs.children[0]
                sp_term = term_ast.to_sympy()
                k_sym = sp.Symbol("k")
                n_sym = sp.Symbol("n")
                if sp_term.is_polynomial(k_sym):
                    sp_sum = sp.Sum(sp_term, (k_sym, 1, n_sym)).doit()
                    candidates: List[ExprNode] = []
                    for sp_cand in [sp.factor(sp_sum), sp.expand(sp_sum)]:
                        try:
                            node = from_sympy(sp_cand)
                            canon_node = canonicalize(node)
                            if canon_node not in candidates:
                                candidates.append(canon_node)
                        except Exception:
                            pass
                    if candidates:
                        return candidates
            except Exception as e:
                logger.debug(f"Direct symbolic polynomial summation failed: {e}")

        try:
            # 2. Sample target sequence at n = 0, 1, 2, ..., num_samples
            # For lower-bounded summations k=1..n, n=0 corresponds to the empty sum (0).
            y_vals: List[float] = [0.0]
            for n_val in range(1, num_samples + 1):
                res = target_lhs.eval_numerical({"n": n_val})
                if isinstance(res, (int, float, Fraction)):
                    y_vals.append(float(res))
                else:
                    return []
        except Exception as e:
            logger.debug(f"Numerical sampling failed for {target_lhs}: {e}")
            return []

        # 2. Compute forward finite difference table
        diff_table: List[List[float]] = [y_vals]
        for _ in range(max_degree + 1):
            prev = diff_table[-1]
            if len(prev) < 2:
                break
            curr = [prev[i + 1] - prev[i] for i in range(len(prev) - 1)]
            diff_table.append(curr)

        # 3. Check for constant non-zero d-th difference and zero (d+1)-th difference
        detected_degree: Optional[int] = None
        for d in range(1, min(max_degree + 1, len(diff_table) - 1)):
            order_d = diff_table[d]
            order_next = diff_table[d + 1] if d + 1 < len(diff_table) else []

            if len(order_d) >= 2:
                # Check if order_d is non-zero constant
                first_val = order_d[0]
                is_const = all(abs(v - first_val) < 1e-5 for v in order_d)
                is_non_zero = abs(first_val) > 1e-5

                # Check if next order vanishes
                vanishes = len(order_next) >= 1 and all(abs(v) < 1e-5 for v in order_next)

                if is_const and is_non_zero and vanishes:
                    detected_degree = d
                    break

        if detected_degree is None:
            return []

        # 4. Perform exact rational polynomial interpolation over d + 1 points
        pts: List[Tuple[int, sp.Rational]] = []
        for i in range(detected_degree + 1):
            val = y_vals[i]
            r_val = int(round(val)) if abs(val - round(val)) < 1e-6 else sp.Rational(Fraction(str(val)))
            pts.append((i, sp.Rational(r_val)))

        n_sym = sp.Symbol("n")
        try:
            poly = sp.interpolate(pts, n_sym)
            poly_factored = sp.factor(poly)
            poly_expanded = sp.expand(poly)
        except Exception as e:
            logger.debug(f"Interpolation failed: {e}")
            return []

        candidates: List[ExprNode] = []
        for sp_cand in [poly_factored, poly_expanded]:
            try:
                node = from_sympy(sp_cand)
                canon_node = canonicalize(node)
                if canon_node not in candidates:
                    candidates.append(canon_node)
            except Exception as e:
                logger.debug(f"SymPy to ExprNode conversion failed for {sp_cand}: {e}")

        return candidates


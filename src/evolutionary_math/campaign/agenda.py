"""Mathematical Problem Space Explorer and Exploration Agenda Generator."""

from typing import List, Generator, Optional
from evolutionary_math.core.ast import ExprNode, expr_factory


class ProblemSpaceAgenda:
    """Generates an evolving stream of mathematical target problem spaces for autonomous discovery."""

    def __init__(self, mode: str = "algebra"):
        self.mode = mode.lower()
        self._custom_queue: List[ExprNode] = []

    def queue_target(self, target: ExprNode) -> None:
        """Enqueue an explicit exploration target."""
        self._custom_queue.append(target)

    def generate_targets(self, continuous: bool = True) -> Generator[ExprNode, None, None]:
        """Stream an evolving sequence of mathematical targets.

        If continuous=True, yields an infinite progression of higher-order power sums,
        telescoping series, and recurrence invariants.
        """
        n = expr_factory.variable("n")
        k = expr_factory.variable("k")
        one = expr_factory.constant(1)
        two = expr_factory.constant(2)
        three = expr_factory.constant(3)

        # 1. First yield any queued custom targets
        while self._custom_queue:
            yield self._custom_queue.pop(0)

        if self.mode == "trigonometry":
            from evolutionary_math.core.ast import parse_expr_str
            trig_targets = [
                "sin(x)^2 + cos(x)^2",
                "sin(m*x)^2 + cos(m*x)^2",
                "tan(x) * cos(x)",
                "1 - cos(x)^2",
                "1 - sin(x)^2",
                "sin(2*x)",
                "cos(2*x)",
                "tan(x)",
                "sin(x) / cos(x)",
            ]
            for s in trig_targets:
                yield parse_expr_str(s)
            
            # Continuous rotation across distinct trigonometric identities (not numerical increments)
            diverse_trig = [
                "cos(2*x) + 2*sin(x)^2",
                "cos(2*x) - cos(x)^2 + sin(x)^2",
                "tan(x) * (1 - sin(x)^2)",
            ]
            idx = 0
            while continuous:
                yield parse_expr_str(diverse_trig[idx % len(diverse_trig)])
                idx += 1
            return

        if self.mode == "geometry":
            from evolutionary_math.core.ast import parse_expr_str
            geom_targets = [
                "2 * (a + b)",
                "c * (a + b)",
                "a * b",
                "(a * b) / 2",
                "sqrt(a^2 + b^2)",
                "sqrt(a^2)",
            ]
            for s in geom_targets:
                yield parse_expr_str(s)
            
            # Continuous rotation across distinct geometric metrics
            diverse_geom = [
                "a^2 + b^2",
                "2 * a * b",
                "(a + b)^2 - (a^2 + b^2)",
            ]
            idx = 0
            while continuous:
                yield parse_expr_str(diverse_geom[idx % len(diverse_geom)])
                idx += 1
            return

        if self.mode == "calculus":
            from evolutionary_math.core.ast import parse_expr_str
            calc_targets = [
                "x^2 - x",
                "x^3 - x^2",
                "2 * x + 1",
            ]
            for s in calc_targets:
                yield parse_expr_str(s)
            p = 4
            while continuous:
                yield parse_expr_str(f"x^{p} - x")
                p += 1
            return

        # Level 1: Linear and Constant Sums (Algebra Mode)
        # Target: sum_{k=1}^n 1 = n
        yield expr_factory.op("sum", one, n)

        # Target: sum_{k=1}^n k = n(n+1)/2 (Triangular numbers)
        yield expr_factory.op("sum", k, n)

        # Target: sum_{k=1}^n (2k - 1) = n^2 (Sum of odd integers)
        two_k = expr_factory.op("*", two, k)
        odd_k = expr_factory.op("-", two_k, one)
        yield expr_factory.op("sum", odd_k, n)

        # Target: sum_{k=1}^n (2k) = n*(n+1) (Sum of even integers)
        yield expr_factory.op("sum", two_k, n)

        # Level 2: Generalized Linear Shift Family
        # Target: sum_{k=1}^n (k + m) = n(n + 2m + 1)/2 for arbitrary parameter m
        m_var = expr_factory.variable("m")
        k_plus_m = expr_factory.op("+", k, m_var)
        yield expr_factory.op("sum", k_plus_m, n)

        # Level 3: Telescoping Rational Sums
        # Target: sum_{k=1}^n 1 / (k*(k+1)) = n / (n+1)
        k_plus_1 = expr_factory.op("+", k, one)
        denom1 = expr_factory.op("*", k, k_plus_1)
        yield expr_factory.op("sum", expr_factory.op("/", one, denom1), n)

        # Target: sum_{k=1}^n 1 / ((k+1)*(k+2))
        k_plus_2 = expr_factory.op("+", k, two)
        denom2 = expr_factory.op("*", k_plus_1, k_plus_2)
        yield expr_factory.op("sum", expr_factory.op("/", one, denom2), n)

        # Level 4: Higher-Order Powers
        # Target: sum_{k=1}^n k^2 (Faulhaber Degree 2)
        yield expr_factory.op("sum", expr_factory.op("^", k, two), n)

        # Level 5: Generalized Pronic Family (Catches all k(k + m) in one general proof)
        # Target: sum_{k=1}^n k*(k + m) = n(n+1)(2n + 3m + 1)/6
        prod_k_m = expr_factory.op("*", k, k_plus_m)
        yield expr_factory.op("sum", prod_k_m, n)

        # Target: sum_{k=1}^n k^3 (Nicomachus's Theorem: (sum k)^2)
        yield expr_factory.op("sum", expr_factory.op("^", k, three), n)

        # Level 6: Higher Simplicial Factor Products (Tetrahedral and Pentatope numbers)
        prod_k = expr_factory.op("*", k, k_plus_1)
        prod_tetra = expr_factory.op("*", prod_k, k_plus_2)
        yield expr_factory.op("sum", prod_tetra, n)

        k_plus_3 = expr_factory.op("+", k, three)
        prod_penta = expr_factory.op("*", prod_tetra, k_plus_3)
        yield expr_factory.op("sum", prod_penta, n)

        # Level 7: Scaled Power Families
        c_var = expr_factory.variable("c")
        yield expr_factory.op("sum", expr_factory.op("*", c_var, k), n)

        # Level 8: Higher Powers (Faulhaber Polynomials)
        four = expr_factory.constant(4)
        yield expr_factory.op("sum", expr_factory.op("^", k, four), n)

        five = expr_factory.constant(5)
        yield expr_factory.op("sum", expr_factory.op("^", k, five), n)

        # Level 9: Centered & Odd/Even Quadratic Progressions
        odd_sq = expr_factory.op("^", odd_k, two)
        yield expr_factory.op("sum", odd_sq, n)

        even_sq = expr_factory.op("^", two_k, two)
        yield expr_factory.op("sum", even_sq, n)

        # Level 10: Compound Telescoping Series
        two_k_plus_1 = expr_factory.op("+", two_k, one)
        odd_prod = expr_factory.op("*", odd_k, two_k_plus_1)
        yield expr_factory.op("sum", expr_factory.op("/", one, odd_prod), n)
        yield expr_factory.op("sum", expr_factory.op("/", one, prod_tetra), n)

        # 11. Open-ended diverse rotation for continuous discovery across distinct degrees
        if not continuous:
            return

        p = 6
        while True:
            # Rotate through higher degree power sums k^p
            p_const = expr_factory.constant(p)
            yield expr_factory.op("sum", expr_factory.op("^", k, p_const), n)
            p += 1



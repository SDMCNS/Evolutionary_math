"""Mathematical Problem Space Explorer and Exploration Agenda Generator."""

from typing import List, Generator, Optional
from evolutionary_math.core.ast import ExprNode, expr_factory


class ProblemSpaceAgenda:
    """Generates an evolving stream of mathematical target problem spaces for autonomous discovery."""

    def __init__(self, mode: str = "algebra", shape_seed: Optional[str] = None):
        self.mode = mode.lower()
        self.shape_seed = shape_seed.lower() if shape_seed else None
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
                "tan(x) * cos(x)",
                "1 - cos(x)^2",
                "1 - sin(x)^2",
                "sin(2*x)",
                "cos(2*x)",
                "tan(x)",
                "sin(x) / cos(x)",
                "cos(2*x) + 2*sin(x)^2",
                "cos(2*x) - cos(x)^2 + sin(x)^2",
                "tan(x) * (1 - sin(x)^2)",
                "cos(x)^4 - sin(x)^4",
            ]
            for s in trig_targets:
                yield parse_expr_str(s)
            
            # Continuous advanced trigonometric identities (qualitative relations, not integer increments)
            if continuous:
                advanced_trig = [
                    "sin(3*x)",
                    "cos(3*x)",
                    "(1 - cos(2*x)) / 2",
                    "(1 + cos(2*x)) / 2",
                    "(1 + tan(x)^2) * cos(x)^2",
                    "sin(a + b) + sin(a - b)",
                    "cos(a - b) - cos(a + b)",
                ]
                for s in advanced_trig:
                    yield parse_expr_str(s)
            return

        if self.mode == "geometry":
            from evolutionary_math.core.seeds import get_geometric_seed, list_geometric_seeds

            # If a specific physical shape seed was designated, focus evolution on its observable goals
            if self.shape_seed:
                seed = get_geometric_seed(self.shape_seed)
                if seed:
                    for g in seed.goals:
                        yield g.target_ast
                    return

            from evolutionary_math.core.ast import parse_expr_str
            geom_targets = [
                "2 * (a + b)",                       # Rectangle perimeter
                "a + b + c",                         # Triangle perimeter
                "(a + b + c) / 2",                   # Triangle semi-perimeter
                "a * b",                             # Rectangle area
                "(a * h) / 2",                       # Triangle area
                "((a + b) * h) / 2",                 # Trapezoid area
                "(d1 * d2) / 2",                     # Rhombus area
                "a * h",                             # Parallelogram area
                "sqrt(a^2 + b^2)",                   # Euclidean hypotenuse
                "a^2 + b^2",                         # Sum of squares
                "a^2 + b^2 + c^2",                   # 3D norm squared
                "(x2 - x1)^2 + (y2 - y1)^2",         # 2D distance squared
                "a * b * c",                         # Cuboid volume
                "2 * ((a * b) + ((b * c) + (c * a)))", # Cuboid surface area
                "6 * (a^2)",                         # Cube surface area
                "4 * (a + b + c)",                   # Cuboid edge sum
                "(a + b)^2 - (a^2 + b^2)",           # Expansion cross term (2ab)
                "(a + b)^2 - (a - b)^2",             # 4ab identity
                "(a + b) * (a - b)",                 # Difference of squares
                "(a - b) * (a^2 + ((a * b) + b^2))", # Difference of cubes
                "(a + b) * (a^2 - ((a * b) - b^2))", # Sum of cubes
                "(x1 + x2) / 2",                     # Midpoint coordinate
                "(x1 * x2) + (y1 * y2)",             # 2D dot product
                "(x1 * y2) - (x2 * y1)",             # 2D cross product magnitude
                "(a^2 + b^2) * (c^2 + d^2) - (a*c - b*d)^2", # Brahmagupta identity
                "(a + b + c)^2 - (a^2 + (b^2 + c^2))",        # Multinomial cross terms
                "(((a + b) / 2)^2) - (a * b)",       # AM-GM square difference
            ]
            for s in geom_targets:
                yield parse_expr_str(s)
            
            # Continuous advanced composite invariants (distinct qualitative structures)
            if continuous:
                advanced_geom = [
                    "(a + b + c) * ((a * b) + ((b * c) + (c * a))) - (a * b * c)",
                    "(x1 - x2)^2 + ((y1 - y2)^2 + (z1 - z2)^2)",
                    "(a - b)^2 + ((b - c)^2 + (c - a)^2)",
                ]
                for s in advanced_geom:
                    yield parse_expr_str(s)
            return

        if self.mode == "calculus":
            from evolutionary_math.core.ast import parse_expr_str
            calc_targets = [
                "(x + h)^2 - x^2",
                "((x + h)^2 - x^2) / h",
                "((x + h)^3 - x^3) / h",
                "(x^2 - 1) / (x - 1)",
                "(x^3 - 1) / (x - 1)",
                "(x^4 - 1) / (x - 1)",
                "2 * x + 1",
                "3 * x^2 + 2 * x",
            ]
            for s in calc_targets:
                yield parse_expr_str(s)
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

        # 11. Continuous discovery across higher order distinct degrees
        if not continuous:
            return

        for p in range(6, 9):
            p_const = expr_factory.constant(p)
            yield expr_factory.op("sum", expr_factory.op("^", k, p_const), n)
        return

    def get_curriculum_targets(self) -> List[ExprNode]:
        """Return the finite sequence of core curriculum targets for the active mode."""
        return list(self.generate_targets(continuous=False))




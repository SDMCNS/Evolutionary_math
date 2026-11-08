"""Tier 1: Fast numerical falsification filter and continuous residual scoring."""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
import numpy as np

# Suppress floating-point overflow/underflow warnings in vectorized genetic search
np.seterr(all="ignore")

from evolutionary_math.core.ast import ExprNode


@dataclass(frozen=True)
class Tier1Result:
    """Result of Tier 1 numerical evaluation."""
    is_falsified: bool
    score: float  # [0.0, 1.0], where 1.0 means exact numerical match on all test points
    max_residual: float
    mean_residual: float
    sample_points_tested: int
    runtime_ms: float
    error_message: Optional[str] = None


class Tier1NumericalEvaluator:
    """Fast vectorized numerical evaluator serving as a falsification sieve."""

    DEFAULT_TEST_POINTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 50, 100]

    def __init__(
        self,
        test_points: Optional[Union[List[Union[int, float]], np.ndarray]] = None,
        variable_name: str = "n",
        tolerance: float = 1e-9,
        gamma: float = 0.5,
    ):
        self.test_points = np.array(test_points if test_points is not None else self.DEFAULT_TEST_POINTS, dtype=np.float64)
        self.variable_name = variable_name
        self.tolerance = tolerance
        self.gamma = gamma

    def evaluate(self, lhs: ExprNode, rhs: ExprNode) -> Tier1Result:
        """Evaluate LHS vs RHS across test domain."""
        start_time = time.perf_counter()
        n_points = len(self.test_points)

        try:
            free_vars = (lhs.variables | rhs.variables) - {"k"}
            if not free_vars:
                free_vars = {self.variable_name}

            env = {}
            for v in free_vars:
                env[v] = self.test_points

            lhs_vals = lhs.eval_numerical(env)
            rhs_vals = rhs.eval_numerical(env)

            # Ensure outputs are numpy arrays
            if not isinstance(lhs_vals, np.ndarray):
                lhs_vals = np.full(n_points, float(lhs_vals))
            if not isinstance(rhs_vals, np.ndarray):
                rhs_vals = np.full(n_points, float(rhs_vals))

            # Check for NaN / Inf
            valid_mask = np.isfinite(lhs_vals) & np.isfinite(rhs_vals)
            if not np.all(valid_mask):
                runtime = (time.perf_counter() - start_time) * 1000.0
                return Tier1Result(
                    is_falsified=True,
                    score=0.0,
                    max_residual=float("inf"),
                    mean_residual=float("inf"),
                    sample_points_tested=n_points,
                    runtime_ms=runtime,
                    error_message="Evaluation produced NaN or Infinite values.",
                )

            residuals = np.abs(lhs_vals - rhs_vals)
            max_res = float(np.max(residuals))
            mean_res = float(np.mean(residuals))

            # Continuous fitness score using scale-invariant relative residuals
            # Perfect match across all points yields 1.0, while maintaining smooth gradients
            rel_residuals = residuals / (np.abs(lhs_vals) + 1.0)
            point_scores = 1.0 / (1.0 + 2.0 * rel_residuals)
            score = float(np.mean(point_scores)) if max_res > self.tolerance else 1.0

            is_falsified = max_res > self.tolerance

            runtime = (time.perf_counter() - start_time) * 1000.0
            return Tier1Result(
                is_falsified=is_falsified,
                score=score,
                max_residual=max_res,
                mean_residual=mean_res,
                sample_points_tested=n_points,
                runtime_ms=runtime,
            )

        except Exception as e:
            runtime = (time.perf_counter() - start_time) * 1000.0
            return Tier1Result(
                is_falsified=True,
                score=0.0,
                max_residual=float("inf"),
                mean_residual=float("inf"),
                sample_points_tested=n_points,
                runtime_ms=runtime,
                error_message=str(e),
            )


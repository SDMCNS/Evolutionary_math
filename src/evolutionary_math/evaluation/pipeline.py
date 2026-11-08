"""Cascading evaluation pipeline integrating Tier 1 numerical falsification and Tier 2 symbolic verification."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from evolutionary_math.core.ast import ExprNode
from evolutionary_math.core.canonicalizer import canonicalize, is_trivial_tautology
from evolutionary_math.evaluation.tier1_numerical import Tier1NumericalEvaluator, Tier1Result
from evolutionary_math.evaluation.tier2_symbolic import Tier2SymbolicVerifier, Tier2Result


class EvaluationStatus(Enum):
    """Classification status of a candidate mathematical relationship."""
    REJECTED_TRIVIAL = auto()
    FALSIFIED = auto()
    NUMERICALLY_PLAUSIBLE = auto()
    SYMBOLICALLY_VERIFIED = auto()
    EVALUATION_ERROR = auto()


@dataclass(frozen=True)
class PipelineResult:
    """Comprehensive evaluation result across all verification tiers."""
    status: EvaluationStatus
    fitness_score: float  # [0.0, 1.0]
    is_verified: bool
    proof_method: Optional[str]
    total_runtime_ms: float
    tier1_result: Optional[Tier1Result] = None
    tier2_result: Optional[Tier2Result] = None
    details: Optional[str] = None


class EvaluationPipeline:
    """Deterministic cascading verification pipeline.

    Flow:
    1. Canonicalization & Triviality Check: Discard vacuous tautologies.
    2. Tier 1 (Numerical Sieve): Fast falsification (< 1 ms). If falsified, halt immediately.
    3. Tier 2 (Symbolic Engine): Exact algebraic zero-equivalence & induction verification.
    """

    def __init__(
        self,
        tier1_evaluator: Optional[Tier1NumericalEvaluator] = None,
        tier2_verifier: Optional[Tier2SymbolicVerifier] = None,
    ):
        self.tier1 = tier1_evaluator or Tier1NumericalEvaluator()
        self.tier2 = tier2_verifier or Tier2SymbolicVerifier()

    def evaluate(self, lhs: ExprNode, rhs: ExprNode) -> PipelineResult:
        """Run the candidate relationship LHS = RHS through the cascading pipeline."""
        # Step 1: Canonicalize and check for trivial tautology
        if is_trivial_tautology(lhs, rhs):
            return PipelineResult(
                status=EvaluationStatus.REJECTED_TRIVIAL,
                fitness_score=0.0,
                is_verified=False,
                proof_method=None,
                total_runtime_ms=0.1,
                details="Rejected: Candidate is a vacuous tautology or syntactically identical.",
            )

        canon_lhs = canonicalize(lhs)
        canon_rhs = canonicalize(rhs)

        # Step 2: Tier 1 - Fast Numerical Sieve
        t1_res = self.tier1.evaluate(canon_lhs, canon_rhs)
        if t1_res.is_falsified:
            return PipelineResult(
                status=EvaluationStatus.FALSIFIED,
                fitness_score=t1_res.score,
                is_verified=False,
                proof_method=None,
                total_runtime_ms=t1_res.runtime_ms,
                tier1_result=t1_res,
                details=f"Falsified numerically: max residual {t1_res.max_residual:.4e}",
            )

        # Step 3: Tier 2 - Symbolic Verification
        # Only reached if Tier 1 passed with residual within tolerance!
        t2_res = self.tier2.verify(canon_lhs, canon_rhs)
        total_time = t1_res.runtime_ms + t2_res.runtime_ms

        if t2_res.is_verified:
            return PipelineResult(
                status=EvaluationStatus.SYMBOLICALLY_VERIFIED,
                fitness_score=1.0,
                is_verified=True,
                proof_method=t2_res.proof_method,
                total_runtime_ms=total_time,
                tier1_result=t1_res,
                tier2_result=t2_res,
                details=f"Formally verified via {t2_res.proof_method}.",
            )
        else:
            return PipelineResult(
                status=EvaluationStatus.NUMERICALLY_PLAUSIBLE,
                fitness_score=t1_res.score,
                is_verified=False,
                proof_method=None,
                total_runtime_ms=total_time,
                tier1_result=t1_res,
                tier2_result=t2_res,
                details=f"Numerically plausible on {t1_res.sample_points_tested} points, but symbolic verification unconfirmed.",
            )


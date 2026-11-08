"""Pydantic schemas defining the strictly air-gapped LLM advisory contract."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class OperatorWeights(BaseModel):
    """Normalized probability distribution for genetic operators."""
    subtree_mutation: float = Field(default=0.35, ge=0.0, le=1.0)
    crossover: float = Field(default=0.40, ge=0.0, le=1.0)
    constant_perturbation: float = Field(default=0.15, ge=0.0, le=1.0)
    hoist: float = Field(default=0.10, ge=0.0, le=1.0)


class GrammarBias(BaseModel):
    """Multiplier for a grammar production rule."""
    head: str = Field(..., description="Grammar non-terminal head, e.g. EXPR or TERMINAL")
    symbol: str = Field(..., description="Grammar production symbol, e.g. +, *, n, 2")
    multiplier: float = Field(..., ge=0.1, le=5.0, description="Weight scaling factor [0.1, 5.0]")


class AdvisoryResponse(BaseModel):
    """Machine-readable strategic recommendation returned by the LLM."""
    diagnosis: str = Field(..., description="Succinct mathematical explanation of search dynamics and stagnation causes.")
    regime_selection: str = Field(
        default="BALANCED",
        description="Search regime to apply.",
        pattern="^(EXPLORATION|EXPLOITATION|BALANCED|SIMPLIFICATION)$",
    )
    operator_weight_adjustments: OperatorWeights = Field(default_factory=OperatorWeights)
    grammar_biases: List[GrammarBias] = Field(default_factory=list)
    pruning_recommendations: List[str] = Field(default_factory=list)
    suggested_subtrees: List[str] = Field(
        default_factory=list,
        description="Candidate mathematical subtrees or formulas (e.g. '(2 * n) + 1') to inject into the population."
    )
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)


class CandidateSignature(BaseModel):
    """Compressed telemetry summary of a top candidate."""
    expr_str: str
    validity: float
    simplicity: float
    node_count: int


class AdvisoryRequest(BaseModel):
    """Structured telemetry payload delivered to the LLM."""
    generation: int
    domain: str
    stagnation_counter: int
    population_metrics: Dict[str, float]
    top_candidate_signatures: List[CandidateSignature]
    recent_operator_success_rates: Dict[str, float]
    known_lemmas_count: int


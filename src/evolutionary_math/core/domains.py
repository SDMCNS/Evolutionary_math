"""Mathematical Domain Modes and Specialization Profiles."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import numpy as np

from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.evaluation.pipeline import EvaluationPipeline
from evolutionary_math.evaluation.tier1_numerical import Tier1NumericalEvaluator
from evolutionary_math.evaluation.tier2_symbolic import Tier2SymbolicVerifier


class DomainMode(str, Enum):
    """Supported mathematical domain focus modes."""
    ALGEBRA = "algebra"
    TRIGONOMETRY = "trigonometry"
    GEOMETRY = "geometry"
    CALCULUS = "calculus"


@dataclass
class DomainProfile:
    """Specialization profile configuring grammar, evaluation metrics, and target presets for a domain."""
    mode: str
    name: str
    description: str
    default_variables: List[str]
    test_points: List[float]
    enable_discrete_solver: bool
    preset_targets: List[str]
    allowed_operators: List[str] = field(default_factory=list)

    def create_grammar(self, variables: Optional[List[str]] = None) -> Grammar:
        """Construct the Context-Free Grammar configured for this domain mode."""
        vars_to_use = variables or self.default_variables
        return Grammar.for_mode(self.mode, variables=vars_to_use)

    def create_pipeline(self, variables: Optional[List[str]] = None) -> EvaluationPipeline:
        """Construct the cascading verification pipeline tailored to this domain's test domain."""
        vars_to_use = (variables or self.default_variables)[0]
        t1 = Tier1NumericalEvaluator(
            test_points=self.test_points,
            variable_name=vars_to_use,
        )
        t2 = Tier2SymbolicVerifier(induction_variable=vars_to_use)
        return EvaluationPipeline(tier1_evaluator=t1, tier2_verifier=t2)


# Built-in Domain Profiles
PROFILES: Dict[str, DomainProfile] = {
    "algebra": DomainProfile(
        mode="algebra",
        name="Algebra & Discrete Series",
        description="Discrete calculus, series summation, power sums, pronic products, and integer sequences.",
        default_variables=["n"],
        test_points=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 15.0, 20.0, 50.0, 100.0],
        enable_discrete_solver=True,
        allowed_operators=["+", "-", "*", "/", "^", "sum"],
        preset_targets=["sum_k", "sum_k2", "sum_k3", "sum_k4", "sum_odd", "sum_even", "sum_pronic", "telescoping"],
    ),
    "trigonometry": DomainProfile(
        mode="trigonometry",
        name="Trigonometry & Angle Identities",
        description="Trigonometric relations, Pythagorean identities, double-angle formulas, and product-to-sum equations.",
        default_variables=["x"],
        test_points=[0.1, 0.4, 0.78539816, 1.04719755, 1.25, 1.5707963, 1.8, 2.35619449, 3.14159265],  # Angles in radians
        enable_discrete_solver=False,
        allowed_operators=["+", "-", "*", "/", "^", "sin", "cos", "tan"],
        preset_targets=["trig_pythagorean", "trig_sin_double", "trig_cos_double", "trig_tan_sec", "trig_cos_half"],
    ),
    "geometry": DomainProfile(
        mode="geometry",
        name="Metric Geometry & Euclidean Relations",
        description="Metric identities, Euclidean distance, Pythagorean hypotenuse, polygon areas, and perimeters.",
        default_variables=["a", "b"],
        test_points=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0],  # Strictly positive side lengths
        enable_discrete_solver=False,
        allowed_operators=["+", "-", "*", "/", "^", "sqrt"],
        preset_targets=["geom_pythagorean", "geom_triangle_area", "geom_rectangle_area", "geom_box_volume"],
    ),
    "calculus": DomainProfile(
        mode="calculus",
        name="Continuous Analysis & Functions",
        description="Continuous functions, radicals, trigonometric compositions, and continuous power equations.",
        default_variables=["x"],
        test_points=[0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0],
        enable_discrete_solver=False,
        allowed_operators=["+", "-", "*", "/", "^", "sin", "cos", "sqrt"],
        preset_targets=["calc_poly", "calc_trig_poly"],
    ),
}


def get_domain_profile(mode: Optional[str] = None) -> DomainProfile:
    """Retrieve the domain profile for a specified mode string, defaulting to algebra."""
    if not mode:
        return PROFILES["algebra"]
    clean = mode.lower().strip()
    if clean in ("trig", "trigonometry"):
        return PROFILES["trigonometry"]
    elif clean in ("geom", "geometry"):
        return PROFILES["geometry"]
    elif clean in ("calc", "calculus", "analysis"):
        return PROFILES["calculus"]
    elif clean in ("algebra", "discrete"):
        return PROFILES["algebra"]
    else:
        raise ValueError(f"Unknown domain mode '{mode}'. Choose from: {', '.join(PROFILES.keys())}")


def list_domain_profiles() -> List[DomainProfile]:
    """Return all available domain profiles."""
    return list(PROFILES.values())


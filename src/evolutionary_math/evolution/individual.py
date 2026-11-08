"""Individual representation in the evolutionary population."""

import uuid
from dataclasses import dataclass, field
from typing import Optional, Tuple
from evolutionary_math.core.ast import ExprNode
from evolutionary_math.evaluation.pipeline import PipelineResult


@dataclass
class Individual:
    """An individual candidate in an evolutionary population."""
    candidate: ExprNode
    generation: int = 0
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent_ids: Tuple[str, ...] = ()
    operator_applied: Optional[str] = None

    # Multi-objective fitness vector: (validity, simplicity, novelty)
    # Higher is better for all objectives!
    fitness_vector: Tuple[float, ...] = (0.0, 0.0, 0.0)
    evaluation_result: Optional[PipelineResult] = None

    # NSGA-II metadata
    rank: int = 0
    crowding_distance: float = 0.0

    @property
    def is_verified(self) -> bool:
        return self.evaluation_result.is_verified if self.evaluation_result else False

    @property
    def validity(self) -> float:
        return self.fitness_vector[0] if len(self.fitness_vector) > 0 else 0.0

    @property
    def simplicity(self) -> float:
        return self.fitness_vector[1] if len(self.fitness_vector) > 1 else 0.0

    @property
    def novelty(self) -> float:
        return self.fitness_vector[2] if len(self.fitness_vector) > 2 else 0.0

    def dominates(self, other: "Individual") -> bool:
        """Check if self Pareto-dominates other.

        self dominates other if self is >= in all objectives and strictly > in at least one.
        """
        at_least_as_good = True
        strictly_better = False
        for f_self, f_other in zip(self.fitness_vector, other.fitness_vector):
            if f_self < f_other:
                return False
            if f_self > f_other:
                strictly_better = True
        return strictly_better and at_least_as_good

    def __repr__(self) -> str:
        return f"<Ind [{self.id}] fit={self.fitness_vector} expr={self.candidate}>"


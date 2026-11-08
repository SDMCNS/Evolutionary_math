"""Multi-objective fitness evaluation: validity, simplicity (MDL), and novelty."""

from typing import Set, Tuple, List
from evolutionary_math.core.ast import ExprNode
from evolutionary_math.evaluation.pipeline import EvaluationPipeline, PipelineResult


def compute_simplicity(expr: ExprNode) -> float:
    """Compute simplicity score based on Minimum Description Length (MDL).

    Penalizes node count and tree depth while keeping score normalized in (0.0, 1.0].
    """
    node_count = expr.node_count
    depth = expr.depth
    return 1.0 / (1.0 + 0.08 * node_count + 0.04 * depth)


def compute_novelty(expr: ExprNode, population_subexprs: Set[str]) -> float:
    """Compute novelty score based on syntactic sub-expression uniqueness against the population pool."""
    subexprs = _extract_subexpr_sexprs(expr)
    if not subexprs or not population_subexprs:
        return 1.0

    unseen = len(subexprs - population_subexprs)
    return float(unseen / len(subexprs))


def _extract_subexpr_sexprs(node: ExprNode) -> Set[str]:
    result = {node.to_sexpr()}
    for c in node.children:
        result.update(_extract_subexpr_sexprs(c))
    return result


def evaluate_individual_fitness(
    candidate: ExprNode,
    target_lhs: ExprNode,
    pipeline: EvaluationPipeline,
    population_subexprs: Set[str],
) -> Tuple[Tuple[float, float, float], PipelineResult]:
    """Compute the multi-objective fitness vector (validity, simplicity, novelty) and evaluation result."""
    eval_result = pipeline.evaluate(target_lhs, candidate)

    # 1. Validity score
    validity = eval_result.fitness_score

    # 2. Simplicity score
    simplicity = compute_simplicity(candidate)

    # 3. Novelty score
    novelty = compute_novelty(candidate, population_subexprs)

    fitness_vector = (validity, simplicity, novelty)
    return fitness_vector, eval_result


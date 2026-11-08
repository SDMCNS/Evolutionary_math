"""Genetic operators: crossover, subtree mutation, constant perturbation, and hoist."""

import random
from typing import List, Tuple, Optional
from evolutionary_math.core.ast import ExprNode, ConstantNode, VariableNode, OperatorNode, LemmaNode, expr_factory
from evolutionary_math.grammar.generator import ExpressionGenerator


def _collect_paths(node: ExprNode, current_path: Tuple[int, ...] = ()) -> List[Tuple[Tuple[int, ...], ExprNode]]:
    """Collect all paths to subtrees within an AST."""
    paths = [(current_path, node)]
    for i, child in enumerate(node.children):
        paths.extend(_collect_paths(child, current_path + (i,)))
    return paths


def _replace_at_path(node: ExprNode, path: Tuple[int, ...], replacement: ExprNode) -> ExprNode:
    """Immutably replace the subtree at path with replacement."""
    if not path:
        return replacement

    if isinstance(node, LemmaNode):
        if path[0] == 0:
            new_arg = _replace_at_path(node.arg, path[1:], replacement)
            return expr_factory.lemma(node.lemma_id, new_arg, node.definition, node.math_type)
        return node

    if not isinstance(node, OperatorNode):
        return node

    target_idx = path[0]
    sub_path = path[1:]

    new_children = list(node.children)
    if target_idx < len(new_children):
        new_children[target_idx] = _replace_at_path(new_children[target_idx], sub_path, replacement)

    return expr_factory.op(node.op, *new_children, math_type=node.math_type)


class GeneticOperators:
    """Suite of genetic operators for mathematical AST evolution."""

    def __init__(self, generator: ExpressionGenerator, rng: Optional[random.Random] = None):
        self.generator = generator
        self.rng = rng or random.Random()

    def crossover(self, parent1: ExprNode, parent2: ExprNode) -> Tuple[ExprNode, ExprNode]:
        """Subtree crossover: swap a randomly selected subtree between parents."""
        paths1 = _collect_paths(parent1)
        paths2 = _collect_paths(parent2)

        if not paths1 or not paths2:
            return parent1, parent2

        p1_path, sub1 = self.rng.choice(paths1)
        p2_path, sub2 = self.rng.choice(paths2)

        child1 = _replace_at_path(parent1, p1_path, sub2)
        child2 = _replace_at_path(parent2, p2_path, sub1)
        return child1, child2

    def subtree_mutation(self, parent: ExprNode, max_depth: int = 3) -> ExprNode:
        """Replace a randomly selected subtree with a fresh random subtree from grammar."""
        paths = _collect_paths(parent)
        if not paths:
            return parent

        path, _ = self.rng.choice(paths)
        new_subtree = self.generator.generate(max_depth=max_depth, method="grow")
        return _replace_at_path(parent, path, new_subtree)

    def constant_perturbation(self, parent: ExprNode) -> ExprNode:
        """Perturb integer or rational constants within the expression."""
        paths = _collect_paths(parent)
        const_paths = [p for p, n in paths if isinstance(n, ConstantNode)]

        if not const_paths:
            # If no constants exist, introduce one via subtree mutation
            return self.subtree_mutation(parent, max_depth=2)

        path = self.rng.choice(const_paths)
        old_node = _get_at_path(parent, path)
        if isinstance(old_node, ConstantNode):
            current_val = old_node.value
            if isinstance(current_val, int):
                # Small step or candidate replacement from small integers
                delta = self.rng.choice([-1, 1, 2, -2])
                new_val = current_val + delta
                if new_val == 0:  # Avoid introducing 0 if perturbing denominators
                    new_val = 1
                new_node = expr_factory.constant(new_val)
                return _replace_at_path(parent, path, new_node)

        return parent

    def hoist_mutation(self, parent: ExprNode) -> ExprNode:
        """Hoist mutation: replace the parent root with a randomly chosen sub-expression (simplification)."""
        paths = _collect_paths(parent)
        # Select non-root subtrees with depth > 1
        non_root_paths = [p for p, n in paths if len(p) > 0 and n.node_count > 1]
        if not non_root_paths:
            # If no non-trivial subtrees, select any non-root
            non_root_paths = [p for p, n in paths if len(p) > 0]

        if not non_root_paths:
            return parent

        path = self.rng.choice(non_root_paths)
        sub = _get_at_path(parent, path)
        return sub or parent


def _get_at_path(node: ExprNode, path: Tuple[int, ...]) -> Optional[ExprNode]:
    current = node
    for idx in path:
        if isinstance(current, OperatorNode) and idx < len(current.children):
            current = current.children[idx]
        elif isinstance(current, LemmaNode) and idx == 0:
            current = current.arg
        else:
            return None
    return current


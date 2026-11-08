"""NSGA-II multi-objective selection, non-dominated sorting, and crowding distance."""

import random
from typing import List, Dict, Optional
from evolutionary_math.evolution.individual import Individual


def fast_non_dominated_sort(population: List[Individual]) -> List[List[Individual]]:
    """Partition population into Pareto fronts F_1, F_2, ... using NSGA-II non-dominated sorting."""
    fronts: List[List[Individual]] = [[]]
    sp_dict: Dict[str, List[Individual]] = {ind.id: [] for ind in population}
    np_dict: Dict[str, int] = {ind.id: 0 for ind in population}

    for p in population:
        for q in population:
            if p.dominates(q):
                sp_dict[p.id].append(q)
            elif q.dominates(p):
                np_dict[p.id] += 1

        if np_dict[p.id] == 0:
            p.rank = 1
            fronts[0].append(p)

    i = 0
    while len(fronts[i]) > 0:
        next_front: List[Individual] = []
        for p in fronts[i]:
            for q in sp_dict[p.id]:
                np_dict[q.id] -= 1
                if np_dict[q.id] == 0:
                    q.rank = i + 2
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    # Remove the last empty front
    if len(fronts) > 0 and len(fronts[-1]) == 0:
        fronts.pop()

    return fronts


def assign_crowding_distance(front: List[Individual], num_objectives: int = 3) -> None:
    """Calculate and assign crowding distance for each individual in a single Pareto front."""
    l = len(front)
    if l == 0:
        return

    for ind in front:
        ind.crowding_distance = 0.0

    if l <= 2:
        for ind in front:
            ind.crowding_distance = float("inf")
        return

    for m in range(num_objectives):
        # Sort front by objective m
        front.sort(key=lambda ind: ind.fitness_vector[m])

        front[0].crowding_distance = float("inf")
        front[-1].crowding_distance = float("inf")

        obj_min = front[0].fitness_vector[m]
        obj_max = front[-1].fitness_vector[m]
        obj_range = obj_max - obj_min

        if obj_range > 1e-12:
            for i in range(1, l - 1):
                prev_val = front[i - 1].fitness_vector[m]
                next_val = front[i + 1].fitness_vector[m]
                front[i].crowding_distance += (next_val - prev_val) / obj_range


def crowded_comparison(ind1: Individual, ind2: Individual) -> int:
    """Compare two individuals based on NSGA-II crowded comparison operator.

    Returns -1 if ind1 is better, 1 if ind2 is better, 0 if equal.
    """
    if ind1.rank < ind2.rank:
        return -1
    elif ind1.rank > ind2.rank:
        return 1
    else:
        # Same rank, prefer higher crowding distance (diversity)
        if ind1.crowding_distance > ind2.crowding_distance:
            return -1
        elif ind1.crowding_distance < ind2.crowding_distance:
            return 1
        return 0


def tournament_select(population: List[Individual], tournament_size: int = 3, rng: Optional[random.Random] = None) -> Individual:
    """Select the best individual from a tournament pool."""
    r = rng or random.Random()
    candidates = r.sample(population, min(tournament_size, len(population)))
    best = candidates[0]
    for c in candidates[1:]:
        if crowded_comparison(c, best) < 0:
            best = c
    return best


def nsga2_select_next_generation(
    combined_population: List[Individual],
    target_size: int,
    num_objectives: int = 3,
) -> List[Individual]:
    """Select the best target_size individuals from combined parents + offspring."""
    fronts = fast_non_dominated_sort(combined_population)
    next_gen: List[Individual] = []

    for front in fronts:
        assign_crowding_distance(front, num_objectives)
        if len(next_gen) + len(front) <= target_size:
            next_gen.extend(front)
        else:
            # Need to select partial front based on crowding distance
            needed = target_size - len(next_gen)
            front.sort(key=lambda ind: ind.crowding_distance, reverse=True)
            next_gen.extend(front[:needed])
            break

    return next_gen


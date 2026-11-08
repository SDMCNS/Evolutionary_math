"""Unit tests for multi-objective NSGA-II selection."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.evolution.individual import Individual
from evolutionary_math.evolution.selection import (
    fast_non_dominated_sort,
    assign_crowding_distance,
    nsga2_select_next_generation,
)


def test_pareto_dominance():
    n = expr_factory.variable("n")
    # Ind 1 dominates Ind 2 because it is strictly better in validity and >= in others
    ind1 = Individual(candidate=n, fitness_vector=(1.0, 0.8, 0.5))
    ind2 = Individual(candidate=n, fitness_vector=(0.5, 0.8, 0.5))
    ind3 = Individual(candidate=n, fitness_vector=(0.8, 0.9, 0.2))

    assert ind1.dominates(ind2)
    assert not ind2.dominates(ind1)
    # ind1 vs ind3: ind1 is better in val/nov, ind3 is better in sim -> neither dominates
    assert not ind1.dominates(ind3)
    assert not ind3.dominates(ind1)


def test_fast_non_dominated_sort():
    n = expr_factory.variable("n")
    ind1 = Individual(candidate=n, fitness_vector=(1.0, 1.0, 1.0))
    ind2 = Individual(candidate=n, fitness_vector=(0.8, 0.8, 0.8))
    ind3 = Individual(candidate=n, fitness_vector=(0.5, 0.5, 0.5))

    fronts = fast_non_dominated_sort([ind1, ind2, ind3])
    assert len(fronts) == 3
    assert fronts[0] == [ind1]
    assert fronts[1] == [ind2]
    assert fronts[2] == [ind3]


def test_nsga2_selection_elitism():
    n = expr_factory.variable("n")
    pop = [
        Individual(candidate=n, fitness_vector=(1.0, 0.5, 0.5)),
        Individual(candidate=n, fitness_vector=(0.5, 1.0, 0.5)),
        Individual(candidate=n, fitness_vector=(0.1, 0.1, 0.1)),
        Individual(candidate=n, fitness_vector=(0.0, 0.0, 0.0)),
    ]

    selected = nsga2_select_next_generation(pop, target_size=2)
    assert len(selected) == 2
    # The top two non-dominated individuals must be selected
    fit_sums = [sum(ind.fitness_vector) for ind in selected]
    assert all(s > 1.0 for s in fit_sums)


"""Unit tests for Grounded Physical & Geometric Seeds (Environmental Framework)."""

import pytest
from evolutionary_math.core.seeds import (
    GeometricSeed,
    get_geometric_seed,
    list_geometric_seeds,
)
from evolutionary_math.campaign.agenda import ProblemSpaceAgenda


def test_seed_registry_catalog():
    """Verify all built-in physical shape seeds are registered and accessible."""
    seeds = list_geometric_seeds()
    seed_ids = [s.id for s in seeds]

    assert "rectangle" in seed_ids
    assert "right_triangle" in seed_ids
    assert "general_triangle" in seed_ids
    assert "trapezoid" in seed_ids
    assert "circle" in seed_ids
    assert "cuboid" in seed_ids


def test_rectangle_seed_features():
    """Verify rectangle seed possesses observable features and parallel/perpendicular properties."""
    rect = get_geometric_seed("rectangle")
    assert rect is not None
    assert rect.name == "Rectangle"
    assert rect.dimension == 2
    assert "a" in rect.observable_features
    assert "b" in rect.observable_features
    assert "P" in rect.observable_features
    assert "A" in rect.observable_features

    # Check physical constraints
    has_parallel = any("parallel" in p.lower() for p in rect.geometric_properties)
    has_perp = any("perpendicular" in p.lower() for p in rect.geometric_properties)
    assert has_parallel is True
    assert has_perp is True

    # Check goal lookup
    area_goal = rect.get_goal("area")
    assert area_goal is not None
    assert str(area_goal.target_ast) == "(a * b)" or "a * b" in str(area_goal.target_ast)

    diag_goal = rect.get_goal("diagonal")
    assert diag_goal is not None
    assert "sqrt" in str(diag_goal.target_ast)


def test_right_triangle_seed_features():
    """Verify right triangle seed features perpendicular legs and Pythagorean goal."""
    rt = get_geometric_seed("right_triangle")
    assert rt is not None
    assert rt.name == "Right Triangle"
    assert "c" in rt.observable_features
    assert any("perpendicular" in p.lower() for p in rt.geometric_properties)

    # Lookup by feature symbol
    hyp_goal = rt.get_goal("c")
    assert hyp_goal is not None
    assert "sqrt" in str(hyp_goal.target_ast)

    # Lookup by name substring
    hyp_goal2 = rt.get_goal("hypotenuse")
    assert hyp_goal2 is not None
    assert hyp_goal2.name == hyp_goal.name


def test_cuboid_3d_seed():
    """Verify 3D cuboid environment features orthogonal axes and volume/surface area."""
    cuboid = get_geometric_seed("cuboid")
    assert cuboid is not None
    assert cuboid.dimension == 3
    assert "V" in cuboid.observable_features
    assert "SA" in cuboid.observable_features

    vol_goal = cuboid.get_goal("volume")
    assert vol_goal is not None
    assert "a * b * c" in vol_goal.target_expr_str


def test_agenda_shape_seed_scoping():
    """Verify that ProblemSpaceAgenda focuses strictly on a shape seed when designated."""
    agenda_rt = ProblemSpaceAgenda(mode="geometry", shape_seed="right_triangle")
    targets = list(agenda_rt.generate_targets(continuous=False))
    assert len(targets) == 3

    target_strs = [str(t) for t in targets]
    assert any("sqrt" in s for s in target_strs)
    assert any("/ 2" in s for s in target_strs)


def test_unknown_seed_lookup():
    """Verify get_geometric_seed returns None for nonexistent seeds."""
    assert get_geometric_seed("nonexistent_shape_123") is None

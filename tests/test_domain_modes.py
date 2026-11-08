"""Unit tests for Domain Modes (algebra, trigonometry, geometry, calculus)."""

import pytest
import numpy as np
import sympy as sp
from evolutionary_math.core.ast import parse_expr_str, expr_factory
from evolutionary_math.core.domains import (
    DomainMode,
    DomainProfile,
    get_domain_profile,
    list_domain_profiles,
)
from evolutionary_math.grammar.rules import Grammar
from evolutionary_math.evaluation.tier1_numerical import Tier1NumericalEvaluator
from evolutionary_math.evaluation.tier2_symbolic import Tier2SymbolicVerifier
from evolutionary_math.evolution.engine import EvolutionEngine
from evolutionary_math.campaign.agenda import ProblemSpaceAgenda
from evolutionary_math.cli import get_target_expression, EXAMPLE_TARGETS


def test_domain_profiles_catalog():
    """Verify that all standard mathematical domains are registered and accessible."""
    profiles = list_domain_profiles()
    modes = [p.mode for p in profiles]
    assert "algebra" in modes
    assert "trigonometry" in modes
    assert "geometry" in modes
    assert "calculus" in modes

    trig_profile = get_domain_profile(DomainMode.TRIGONOMETRY)
    assert trig_profile.mode == "trigonometry"
    assert "sin" in trig_profile.allowed_operators
    assert "cos" in trig_profile.allowed_operators
    assert "x" in trig_profile.default_variables
    assert trig_profile.enable_discrete_solver is False

    geom_profile = get_domain_profile("geometry")
    assert geom_profile.mode == "geometry"
    assert "sqrt" in geom_profile.allowed_operators
    assert "a" in geom_profile.default_variables
    assert "b" in geom_profile.default_variables
    assert geom_profile.enable_discrete_solver is False

    with pytest.raises(ValueError):
        get_domain_profile("quantum_field_theory")


def test_grammar_for_mode():
    """Verify that grammar rules are tailored to domain modes."""
    g_trig = Grammar.for_mode("trigonometry")
    rules_trig = {r.symbol for r in g_trig.rules}
    assert "sin" in rules_trig
    assert "cos" in rules_trig
    assert "tan" in rules_trig
    assert "x" in rules_trig

    g_geom = Grammar.for_mode("geometry")
    rules_geom = {r.symbol for r in g_geom.rules}
    assert "sqrt" in rules_geom
    assert "a" in rules_geom
    assert "b" in rules_geom

    g_calc = Grammar.for_mode("calculus")
    rules_calc = {r.symbol for r in g_calc.rules}
    assert "x" in rules_calc


def test_tier1_numerical_trig_and_geom():
    """Verify Tier 1 numerical evaluator handles radians and multi-variable evaluations."""
    trig_profile = get_domain_profile("trigonometry")
    evaluator_trig = Tier1NumericalEvaluator(
        variable_name="x",
        test_points=trig_profile.test_points,
    )

    lhs_trig = parse_expr_str("sin(x)^2 + cos(x)^2")
    rhs_trig = parse_expr_str("1")
    res_trig = evaluator_trig.evaluate(lhs_trig, rhs_trig)
    assert res_trig.is_falsified is False
    assert res_trig.score == 1.0

    geom_profile = get_domain_profile("geometry")
    evaluator_geom = Tier1NumericalEvaluator(
        variable_name="a",
        test_points=geom_profile.test_points,
    )
    lhs_geom = parse_expr_str("2 * (a + b)")
    rhs_geom = parse_expr_str("2*a + 2*b")
    res_geom = evaluator_geom.evaluate(lhs_geom, rhs_geom)
    assert res_geom.is_falsified is False
    assert res_geom.score == 1.0


def test_tier2_symbolic_trig_verification():
    """Verify that Tier 2 symbolic verifier establishes trigonometric zero-equivalence."""
    verifier = Tier2SymbolicVerifier(induction_variable="x")

    # 1. Pythagorean identity: sin^2(x) + cos^2(x) = 1
    lhs = parse_expr_str("sin(x)^2 + cos(x)^2")
    rhs = parse_expr_str("1")
    res = verifier.verify(lhs, rhs)
    assert res.is_verified is True
    assert res.proof_method == "trigonometric_zero_equivalence"

    # 2. Sine double angle: sin(2x) = 2*sin(x)*cos(x)
    lhs_double = parse_expr_str("sin(2*x)")
    rhs_double = parse_expr_str("2 * sin(x) * cos(x)")
    res_double = verifier.verify(lhs_double, rhs_double)
    assert res_double.is_verified is True
    assert res_double.proof_method == "trigonometric_zero_equivalence"

    # 3. Invalid identity rejection: sin(x) == cos(x)
    lhs_bad = parse_expr_str("sin(x)")
    rhs_bad = parse_expr_str("cos(x)")
    res_bad = verifier.verify(lhs_bad, rhs_bad)
    assert res_bad.is_verified is False


def test_tier2_symbolic_geometry_verification():
    """Verify that Tier 2 symbolic verifier handles multi-variable geometric identities."""
    verifier = Tier2SymbolicVerifier(induction_variable="a")

    lhs = parse_expr_str("2 * (a + b)")
    rhs = parse_expr_str("2*a + 2*b")
    res = verifier.verify(lhs, rhs)
    assert res.is_verified is True
    assert res.proof_method == "algebraic_zero_equivalence"


def test_engine_mode_configuration():
    """Ensure EvolutionEngine configures domain-specific grammar, pipeline, and solver."""
    engine_trig = EvolutionEngine(mode="trigonometry")
    assert engine_trig.mode == "trigonometry"
    assert engine_trig.enable_polynomial_solver is False
    symbols = {r.symbol for r in engine_trig.grammar.rules}
    assert "sin" in symbols

    engine_geom = EvolutionEngine(mode="geometry")
    assert engine_geom.mode == "geometry"
    assert engine_geom.enable_polynomial_solver is False
    symbols_geom = {r.symbol for r in engine_geom.grammar.rules}
    assert "sqrt" in symbols_geom


def test_problem_space_agenda_by_mode():
    """Ensure ProblemSpaceAgenda streams domain-appropriate targets."""
    agenda_trig = ProblemSpaceAgenda(mode="trigonometry")
    targets_trig = []
    stream_trig = agenda_trig.generate_targets(continuous=False)
    for _ in range(3):
        targets_trig.append(next(stream_trig))

    trig_vars = set()
    for t in targets_trig:
        trig_vars.update(t.variables)
    assert "x" in trig_vars
    assert "k" not in trig_vars

    agenda_geom = ProblemSpaceAgenda(mode="geometry")
    targets_geom = []
    stream_geom = agenda_geom.generate_targets(continuous=False)
    for _ in range(3):
        targets_geom.append(next(stream_geom))

    geom_vars = set()
    for t in targets_geom:
        geom_vars.update(t.variables)
    assert "a" in geom_vars or "b" in geom_vars
    assert "k" not in geom_vars


def test_cli_target_expression_resolution():
    """Ensure CLI correctly parses both algebra summations and continuous domain targets."""
    # Algebra preset
    t_alg = get_target_expression("sum_k", mode="algebra")
    assert t_alg.op == "sum"

    # Trigonometry preset
    t_trig = get_target_expression("trig_pythagorean", mode="trigonometry")
    assert t_trig.op != "sum"
    assert "x" in t_trig.variables

    # Custom trig string without preset
    t_custom_trig = get_target_expression("sin(x)**2 + cos(x)**2", mode="trigonometry")
    assert t_custom_trig.op != "sum"

    # Custom algebra string (summand over k)
    t_custom_alg = get_target_expression("k^2 + 2*k", mode="algebra")
    assert t_custom_alg.op == "sum"

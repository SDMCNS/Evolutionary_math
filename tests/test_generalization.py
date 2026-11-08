"""Unit tests for mathematical generalization, parameter lifting, and theorem subsumption."""

import pytest
import sympy as sp
from evolutionary_math.core.ast import parse_expr_str, expr_factory
from evolutionary_math.core.generalization import (
    extract_parametric_family,
    find_subsumption_match,
    instantiate_generalized_formula,
    identify_parameter_variables,
)
from evolutionary_math.evaluation.tier2_symbolic import Tier2SymbolicVerifier
from evolutionary_math.evolution.rational_solver import ExactPolynomialSolver
from evolutionary_math.evolution.engine import EvolutionEngine
from evolutionary_math.evolution.individual import Individual
from evolutionary_math.storage.knowledge_base import KnowledgeBase


def test_extract_parametric_family():
    """Verify lifting numeric constants into free parameters m and c."""
    # 1. Pronic shift family: k * (k + 110) -> k * (k + m)
    t_pronic = parse_expr_str("sum_k=1..n(k * (k + 110))")
    gen_info = extract_parametric_family(t_pronic)
    assert gen_info is not None
    gen_tgt, param_name, c_val = gen_info
    assert param_name == "m"
    assert c_val == 110
    assert "m" in gen_tgt.variables
    assert "k" in gen_tgt.variables

    # 2. Linear shift family: (k + 25) -> (k + m)
    t_linear = parse_expr_str("sum_k=1..n(k + 25)")
    gen_info2 = extract_parametric_family(t_linear)
    assert gen_info2 is not None
    gen_tgt2, param_name2, c_val2 = gen_info2
    assert param_name2 == "m"
    assert c_val2 == 25

    # 3. Scaled sum family: 7 * k -> c * k
    t_scaled = parse_expr_str("sum_k=1..n(7 * k)")
    gen_info3 = extract_parametric_family(t_scaled)
    assert gen_info3 is not None
    gen_tgt3, param_name3, c_val3 = gen_info3
    assert param_name3 == "c"
    assert c_val3 == 7

    # 4. Pure power (not a parametric shift): k^2 -> None
    t_power = parse_expr_str("sum_k=1..n(k^2)")
    assert extract_parametric_family(t_power) is None


def test_find_subsumption_match():
    """Verify pattern matching detects instances of generalized theorems."""
    gen_target = parse_expr_str("sum_k=1..n(k * (k + m))")
    param_vars = ["m"]

    # Match m = 110
    target_110 = parse_expr_str("sum_k=1..n(k * (k + 110))")
    match_110 = find_subsumption_match(target_110, gen_target, param_vars)
    assert match_110 is not None
    assert match_110["m"] == 110

    # Match m = 2
    target_2 = parse_expr_str("sum_k=1..n(k * (k + 2))")
    match_2 = find_subsumption_match(target_2, gen_target, param_vars)
    assert match_2 is not None
    assert match_2["m"] == 2

    # Non-matching target: k^3
    target_k3 = parse_expr_str("sum_k=1..n(k^3)")
    assert find_subsumption_match(target_k3, gen_target, param_vars) is None


def test_instantiate_generalized_formula():
    """Verify substituting parameter values into general closed form."""
    # General formula for sum_{k=1}^n k(k + m): n*(n + 1)*(2*n + 3*m + 1)/6
    gen_formula = parse_expr_str("n * (n + 1) * (2*n + 3*m + 1) / 6")

    # Instance m = 110 -> n*(n + 1)*(2*n + 331)/6
    f_110 = instantiate_generalized_formula(gen_formula, {"m": 110})
    expected_110 = parse_expr_str("n * (n + 1) * (2*n + 331) / 6")
    diff_110 = sp.simplify(f_110.to_sympy() - expected_110.to_sympy())
    assert diff_110 == 0

    # Instance m = 2 -> n*(n + 1)*(2*n + 7)/6
    f_2 = instantiate_generalized_formula(gen_formula, {"m": 2})
    expected_2 = parse_expr_str("n * (n + 1) * (2*n + 7) / 6")
    diff_2 = sp.simplify(f_2.to_sympy() - expected_2.to_sympy())
    assert diff_2 == 0


def test_formal_induction_of_generalized_meta_theorem():
    """Verify that Tier 2 induction engine proves general formula for symbolic parameter m."""
    gen_target = parse_expr_str("sum_k=1..n(k * (k + m))")
    gen_formula = parse_expr_str("n * (n + 1) * (2*n + 3*m + 1) / 6")

    verifier = Tier2SymbolicVerifier(induction_variable="n")
    res = verifier.verify(gen_target, gen_formula)
    assert res.is_verified is True
    assert res.proof_method == "mathematical_induction"


def test_knowledge_base_subsumption_prevention(tmp_path):
    """Verify knowledge base recognizes instances and avoids duplicate theorem rows."""
    db_path = str(tmp_path / "test_kb_subsumption.db")
    kb = KnowledgeBase(db_path)

    gen_target = parse_expr_str("sum_k=1..n(k * (k + m))")
    gen_formula = parse_expr_str("n * (n + 1) * (2*n + 3*m + 1) / 6")

    ind = Individual(candidate=gen_formula, generation=0)
    from evolutionary_math.evaluation.tier2_symbolic import Tier2Result
    ind.evaluation_result = Tier2Result(is_verified=True, proof_method="mathematical_induction", simplified_difference="0", runtime_ms=1.0)

    # 1. Store generalized master theorem
    th = kb.store_discovery(ind, gen_target, experiment_id="test")
    assert th.is_generalized is True
    assert "m" in th.parameter_vars

    # 2. Check that specific instances are now recognized as ALREADY SOLVED
    target_110 = parse_expr_str("sum_k=1..n(k * (k + 110))")
    assert kb.is_target_solved(target_110) is True

    target_2 = parse_expr_str("sum_k=1..n(k * (k + 2))")
    assert kb.is_target_solved(target_2) is True

    # 3. Find subsuming theorem
    subsuming = kb.find_subsuming_theorem(target_110)
    assert subsuming is not None
    master_th, sub_dict = subsuming
    assert master_th.id == th.id
    assert sub_dict["m"] == 110

    kb.close()


def test_engine_auto_generalization(tmp_path):
    """Verify engine automatically solves the general family when given a concrete iteration."""
    db_path = str(tmp_path / "test_engine_auto_gen.db")
    kb = KnowledgeBase(db_path)

    engine = EvolutionEngine(knowledge_base=kb)
    target_110 = parse_expr_str("sum_k=1..n(k * (k + 110))")

    # First run on k*(k + 110): engine auto-generalizes to k*(k + m), solves and stores master theorem!
    res = engine.run(target_110, max_generations=10)
    assert res.success is True
    assert res.total_generations == 0
    assert "m" in res.discovered_theorem.target_str

    # Second run on k*(k + 111): immediately subsumed by existing master theorem without a duplicate entry!
    theorems_before = len(kb.get_all_theorems())
    target_111 = parse_expr_str("sum_k=1..n(k * (k + 111))")
    res2 = engine.run(target_111, max_generations=10)
    assert res2.success is True
    assert res2.total_generations == 0
    theorems_after = len(kb.get_all_theorems())
    assert theorems_after == theorems_before  # No duplicate rows created!

    kb.close()


def test_consolidate_parametric_families(tmp_path):
    """Verify consolidating a database flooded with k*(k+1), k*(k+2), k*(k+3) into 1 general theorem."""
    db_path = str(tmp_path / "test_consolidate.db")
    kb = KnowledgeBase(db_path)

    # Artificially insert 3 concrete iterations
    for m_val in [1, 2, 3]:
        t = parse_expr_str(f"sum_k=1..n(k * (k + {m_val}))")
        sols = ExactPolynomialSolver.solve(t)
        ind = Individual(candidate=sols[0], generation=0)
        ind.evaluation_result = Tier2SymbolicVerifier().verify(t, sols[0])
        kb.store_discovery(ind, t, experiment_id="flood")

    assert len(kb.get_all_theorems()) == 3

    # Consolidate!
    consolidated_count = kb.consolidate_parametric_families()
    assert consolidated_count == 3

    theorems = kb.get_all_theorems()
    assert len(theorems) == 1
    master_th = theorems[0]
    assert master_th.is_generalized is True
    assert "m" in master_th.target_str
    assert "k * (k + m)" in master_th.target_str or "k*(k + m)" in master_th.target_str

    kb.close()

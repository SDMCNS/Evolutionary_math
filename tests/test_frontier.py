"""Tests for mathematical research frontier and exploration effort tracking."""

import pytest
import sqlite3
import os
from evolutionary_math.core.ast import expr_factory
from evolutionary_math.storage.knowledge_base import KnowledgeBase, TargetEffortRecord, SearchBranchRecord
from evolutionary_math.evolution.engine import DiscoveryTelemetry
from evolutionary_math.utils.formatting import export_frontier_markdown
from evolutionary_math.campaign.agenda import ProblemSpaceAgenda


def test_target_registry_schema_and_record():
    kb = KnowledgeBase(":memory:")
    
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    target = expr_factory.op("sum", expr_factory.op("^", k, expr_factory.constant(5)), n)
    
    # First attempt: failure / timeout
    telem = DiscoveryTelemetry(
        generation=45,
        best_validity=0.88,
        pareto_front_size=5,
        total_individuals_evaluated=45 * 160,
        elapsed_time_sec=2.5,
        best_candidate_str="((n * (n + 1)) / 2)",
        advisory_intervention=None,
    )
    
    kb.record_target_attempt(
        target=target,
        result=telem,
        domain_mode="algebra",
        experiment_id="exp_01",
    )
    
    rec = kb.get_target_effort(str(target))
    assert rec is not None
    assert rec.status == "UNSOLVED"
    assert rec.attempts_count == 1
    assert rec.total_generations == 45
    assert rec.best_validity == 0.88
    assert rec.domain_mode == "algebra"
    
    # Second attempt: improved validity
    telem2 = DiscoveryTelemetry(
        generation=50,
        best_validity=0.999,
        pareto_front_size=8,
        total_individuals_evaluated=50 * 160,
        elapsed_time_sec=3.0,
        best_candidate_str="((n^2 * (n + 1)^2 * (2*n^2 + 2*n - 1)) / 12)",
        advisory_intervention="algebraic_expansion",
    )
    
    kb.record_target_attempt(
        target=target,
        result=telem2,
        domain_mode="algebra",
        experiment_id="exp_02",
    )
    
    rec2 = kb.get_target_effort(str(target))
    assert rec2.attempts_count == 2
    assert rec2.total_generations == 95
    assert rec2.total_evaluations == (45 * 160) + (50 * 160)
    assert rec2.best_validity == 0.999
    assert rec2.advisory_interventions_count == 1
    assert rec2.status == "UNSOLVED"
    
    unsolved = kb.get_unsolved_targets()
    assert len(unsolved) == 1
    assert unsolved[0].target_str == str(target)
    
    kb.close()


def test_sync_target_registry_from_history():
    kb = KnowledgeBase(":memory:")
    
    # Insert raw search history
    with kb.conn:
        kb.conn.execute("""
            INSERT INTO search_history 
            (id, experiment_id, target_str, generation, candidate_str, clean_formula, validity, status, operator, reason, timestamp)
            VALUES 
            ('br_1', 'exp_test', 'sum_k=1..n(k^4)', 10, 'n*(n+1)/2', 'n*(n+1)/2', 0.85, 'milestone', 'init', 'Good start', 100.0),
            ('br_2', 'exp_test', 'sum_k=1..n(k^4)', 30, 'n^3/3', 'n^3/3', 0.92, 'milestone', 'mutation', 'Closer', 105.0)
        """)
        
    synced = kb.sync_target_registry_from_history()
    assert synced >= 1
    
    rec = kb.get_target_effort("sum_k=1..n(k^4)")
    assert rec is not None
    assert rec.status == "UNSOLVED"
    assert rec.best_validity == 0.92
    assert rec.total_generations == 30
    
    kb.close()


def test_export_frontier_markdown():
    kb = KnowledgeBase(":memory:")
    n = expr_factory.variable("n")
    k = expr_factory.variable("k")
    target = expr_factory.op("sum", expr_factory.op("^", k, expr_factory.constant(7)), n)
    
    telem = DiscoveryTelemetry(
        generation=40,
        best_validity=0.75,
        pareto_front_size=4,
        total_individuals_evaluated=40 * 100,
        elapsed_time_sec=2.0,
        best_candidate_str="n*(n+1)",
        advisory_intervention=None,
    )
    kb.record_target_attempt(target, telem, "algebra", "exp_md")
    
    agenda = ProblemSpaceAgenda(mode="algebra")
    md = export_frontier_markdown(kb, agenda=agenda, limit=10)
    
    assert "# Active Mathematical Research Frontier" in md
    assert "Open / Unsolved Problems" in md
    assert "0.7500" in md or "75.00%" in md
    assert "∑" in md
    
    kb.close()


def test_fishbone_unsolved_target_svg():
    from evolutionary_math.utils.fishbone import generate_fishbone_svg, SearchBranchRecord
    
    branches = [
        SearchBranchRecord(
            id="f1",
            experiment_id="exp_u",
            target_str="sum_k=1..n(k^5)",
            generation=10,
            candidate_str="n*(n+1)/2",
            clean_formula="n*(n+1)/2",
            validity=0.85,
            status="milestone",
            operator="crossover",
            reason="Leading candidate",
        ),
        SearchBranchRecord(
            id="f2",
            experiment_id="exp_u",
            target_str="sum_k=1..n(k^5)",
            generation=20,
            candidate_str="n^2",
            clean_formula="n^2",
            validity=0.40,
            status="falsified",
            operator="mutation",
            reason="Falsified at n=2",
        )
    ]
    
    svg = generate_fishbone_svg(branches, title="Unsolved Search Target")
    assert "<svg" in svg
    assert "OPEN TARGET (UNSOLVED)" in svg
    assert "85.00%" in svg

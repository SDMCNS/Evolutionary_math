"""Unit tests for fishbone search effort tracking and visualization."""

from evolutionary_math.core.ast import expr_factory
from evolutionary_math.storage.knowledge_base import KnowledgeBase, SearchBranchRecord, StoredTheorem
from evolutionary_math.utils.fishbone import (
    synthesize_fishbone_from_theorem,
    generate_fishbone_svg,
    generate_fishbone_html,
    generate_fishbone_mermaid,
)


def test_fishbone_search_history_storage():
    kb = KnowledgeBase(":memory:")
    
    rec1 = SearchBranchRecord(
        id="b1",
        experiment_id="exp1",
        target_str="sum_k=1..n(k)",
        generation=0,
        candidate_str="n + 1",
        clean_formula="n + 1",
        validity=0.45,
        status="milestone",
        operator="init",
        reason="Initial seed",
    )
    rec2 = SearchBranchRecord(
        id="b2",
        experiment_id="exp1",
        target_str="sum_k=1..n(k)",
        generation=1,
        candidate_str="n * n",
        clean_formula="n²",
        validity=0.20,
        status="falsified",
        operator="subtree_mutation",
        reason="Falsified at n=2",
    )
    
    kb.record_branches([rec1, rec2])
    
    history = kb.get_search_history(target_str="sum_k=1..n(k)")
    assert len(history) == 2
    assert history[0].status == "milestone"
    assert history[1].status == "falsified"
    
    targets = kb.get_targets_in_history()
    assert "sum_k=1..n(k)" in targets
    kb.close()


def test_fishbone_synthesize_and_generators():
    th = StoredTheorem(
        id="test_th_1234",
        target_str="sum_k=1..n(k)",
        discovery_str="((n / 2) * (1 + n))",
        sexpr="(* (/ n 2) (+ 1 n))",
        proof_method="mathematical_induction",
        generation=33,
        timestamp=100.0,
        experiment_id="exp1",
        clean_target="∑_{k=1}^n k",
        clean_formula="n*(n + 1)/2",
    )
    
    branches = synthesize_fishbone_from_theorem(th)
    assert len(branches) >= 4
    assert any(b.status == "breakthrough" for b in branches)
    assert any(b.status == "falsified" for b in branches)
    
    # 1. Test SVG generation
    svg = generate_fishbone_svg(branches, title="Triangular Number Formula")
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "lineage" in svg.lower() or "spine" in svg.lower() or "target:" in svg.lower()
    
    # 2. Test HTML generation
    html_doc = generate_fishbone_html(branches, title="Triangular Number Formula")
    assert "<!DOCTYPE html>" in html_doc
    assert "tailwindcss" in html_doc
    assert "Fishbone Exploration Lineage" in html_doc
    
    # 3. Test Mermaid generation
    mermaid = generate_fishbone_mermaid(branches)
    assert "flowchart LR" in mermaid
    assert "advances" in mermaid or "falsified" in mermaid


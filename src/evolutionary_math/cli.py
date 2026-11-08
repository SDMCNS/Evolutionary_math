"""Command-line interface (CLI) for the Evolutionary Mathematical Discovery Engine."""

import sys
from pathlib import Path

# Ensure package root (src/) is on sys.path even when run directly as a file
_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import argparse
from typing import Optional

from evolutionary_math.core.ast import expr_factory, ExprNode, parse_expr_str
from evolutionary_math.evolution.engine import EvolutionEngine, DiscoveryTelemetry
from evolutionary_math.advisory.client import MockAdvisoryClient, OpenAICompatibleAdvisoryClient
from evolutionary_math.advisory.controller import AdvisoryController
from evolutionary_math.storage.knowledge_base import KnowledgeBase, StoredTheorem
from evolutionary_math.utils.formatting import (
    to_latex,
    to_ascii_tree,
    export_knowledge_base_mermaid,
    export_knowledge_base_markdown,
    infer_theorem_name,
    format_clean_target,
    format_clean_formula,
    format_expanded_formula,
    format_complete_latex,
)
from evolutionary_math.utils.lean_exporter import generate_lean4_proof_file
from evolutionary_math.dashboard import DiscoveryDashboard
from evolutionary_math.campaign.runner import AutonomousDiscoveryCampaign
from evolutionary_math.campaign.agenda import ProblemSpaceAgenda


EXAMPLE_TARGETS = {
    # 1. Classical Power Sums (Algebra)
    "sum_k": {
        "math": "∑_{k=1}^n k",
        "name": "Triangular Numbers (Sum of First n Integers)",
        "expected": "n*(n + 1)/2",
        "category": "Power Sums",
        "mode": "algebra",
        "difficulty": "Easy",
        "description": "The foundational Gauss sum: 1 + 2 + ... + n = n(n+1)/2.",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.variable("k"), expr_factory.variable("n")),
    },
    "sum_k2": {
        "math": "∑_{k=1}^n k²",
        "name": "Square Pyramidal Numbers (Sum of First n Squares)",
        "expected": "n*(n + 1)*(2n + 1)/6",
        "category": "Power Sums",
        "mode": "algebra",
        "difficulty": "Medium",
        "description": "Adding consecutive square numbers: 1² + 2² + ... + n².",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("^", expr_factory.variable("k"), expr_factory.constant(2)), expr_factory.variable("n")),
    },
    "sum_k3": {
        "math": "∑_{k=1}^n k³",
        "name": "Nicomachus's Theorem (Sum of First n Cubes)",
        "expected": "n²*(n + 1)²/4",
        "category": "Power Sums",
        "mode": "algebra",
        "difficulty": "Medium (Trivial with Lemma)",
        "description": "Sum of cubes equals square of triangular numbers: (1 + 2 + ... + n)².",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("^", expr_factory.variable("k"), expr_factory.constant(3)), expr_factory.variable("n")),
    },
    "sum_k4": {
        "math": "∑_{k=1}^n k⁴",
        "name": "Quartic Power Sum",
        "expected": "n*(n + 1)*(2n + 1)*(3n² + 3n - 1)/30",
        "category": "Power Sums",
        "mode": "algebra",
        "difficulty": "Hard",
        "description": "Degree 5 polynomial sum: 1⁴ + 2⁴ + ... + n⁴.",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("^", expr_factory.variable("k"), expr_factory.constant(4)), expr_factory.variable("n")),
    },
    # 2. Integer Sequences & Progressions (Algebra)
    "sum_const": {
        "math": "∑_{k=1}^n 1",
        "name": "Discrete Counting Identity",
        "expected": "n",
        "category": "Arithmetic",
        "mode": "algebra",
        "difficulty": "Trivial",
        "description": "Adding 1 repeatedly n times simply yields n.",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.constant(1), expr_factory.variable("n")),
    },
    "sum_odd": {
        "math": "∑_{k=1}^n (2k - 1)",
        "name": "Sum of Consecutive Odd Numbers",
        "expected": "n²",
        "category": "Arithmetic",
        "mode": "algebra",
        "difficulty": "Easy",
        "description": "Gnomon expansion of squares: 1 + 3 + 5 + ... + (2n - 1) = n².",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("-", expr_factory.op("*", expr_factory.constant(2), expr_factory.variable("k")), expr_factory.constant(1)), expr_factory.variable("n")),
    },
    "sum_even": {
        "math": "∑_{k=1}^n 2k",
        "name": "Sum of Consecutive Even Numbers (Pronic Rectangles)",
        "expected": "n*(n + 1)",
        "category": "Arithmetic",
        "mode": "algebra",
        "difficulty": "Easy",
        "description": "Double the triangular numbers: 2 + 4 + ... + 2n = n(n+1).",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("*", expr_factory.constant(2), expr_factory.variable("k")), expr_factory.variable("n")),
    },
    "sum_shifted": {
        "math": "∑_{k=1}^n (k + 1)",
        "name": "Sum of Shifted Integers",
        "expected": "n*(n + 3)/2",
        "category": "Arithmetic",
        "mode": "algebra",
        "difficulty": "Easy",
        "description": "Shifted triangular sequence: 2 + 3 + 4 + ... + (n + 1).",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("+", expr_factory.variable("k"), expr_factory.constant(1)), expr_factory.variable("n")),
    },
    "sum_pronic": {
        "math": "∑_{k=1}^n k(k + 1)",
        "name": "Sum of Consecutive Pronic Products",
        "expected": "n*(n + 1)*(n + 2)/3",
        "category": "Factor Products",
        "mode": "algebra",
        "difficulty": "Medium",
        "description": "Adding rectangular products: 1·2 + 2·3 + ... + n·(n+1).",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("*", expr_factory.variable("k"), expr_factory.op("+", expr_factory.variable("k"), expr_factory.constant(1))), expr_factory.variable("n")),
    },
    # 2b. Generalized Parametric Meta-Theorems (Holding for all parameters m, c)
    "sum_pronic_gen": {
        "math": "∑_{k=1}^n k(k + m)",
        "name": "Generalized Pronic Sum Identity",
        "expected": "n*(n + 1)*(2n + 3m + 1)/6",
        "category": "Parametric Meta-Theorems",
        "mode": "algebra",
        "difficulty": "Medium",
        "description": "General master theorem for all pronic shifts m: ∑ k(k+m) = n(n+1)(2n + 3m + 1)/6.",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("*", expr_factory.variable("k"), expr_factory.op("+", expr_factory.variable("k"), expr_factory.variable("m"))), expr_factory.variable("n")),
    },
    "sum_shifted_gen": {
        "math": "∑_{k=1}^n (k + m)",
        "name": "Generalized Shifted Linear Sum",
        "expected": "n*(n + 2m + 1)/2",
        "category": "Parametric Meta-Theorems",
        "mode": "algebra",
        "difficulty": "Easy",
        "description": "General master theorem for all linear shifts m: ∑ (k+m) = n(n + 2m + 1)/2.",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("+", expr_factory.variable("k"), expr_factory.variable("m")), expr_factory.variable("n")),
    },
    # 3. Rational Telescoping Series (Algebra)
    "telescoping": {
        "math": "∑_{k=1}^n 1/(k(k + 1))",
        "name": "Harmonic Telescoping Series",
        "expected": "n/(n + 1)",
        "category": "Telescoping",
        "mode": "algebra",
        "difficulty": "Medium",
        "description": "Partial fractions cancel out: 1/(1·2) + 1/(2·3) + ... = 1 - 1/(n+1).",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("/", expr_factory.constant(1), expr_factory.op("*", expr_factory.variable("k"), expr_factory.op("+", expr_factory.variable("k"), expr_factory.constant(1)))), expr_factory.variable("n")),
    },
    "shifted_telescoping": {
        "math": "∑_{k=1}^n 1/((k + 1)(k + 2))",
        "name": "Shifted Harmonic Telescoping Series",
        "expected": "n/(2*(n + 2))",
        "category": "Telescoping",
        "mode": "algebra",
        "difficulty": "Medium",
        "description": "Shifted partial fractions cancel out: 1/(2·3) + 1/(3·4) + ... = 1/2 - 1/(n+2).",
        "expr_fn": lambda: expr_factory.op("sum", expr_factory.op("/", expr_factory.constant(1), expr_factory.op("*", expr_factory.op("+", expr_factory.variable("k"), expr_factory.constant(1)), expr_factory.op("+", expr_factory.variable("k"), expr_factory.constant(2)))), expr_factory.variable("n")),
    },
    # 4. Trigonometric Identities
    "trig_pythagorean": {
        "math": "sin²(x) + cos²(x)",
        "name": "Pythagorean Trigonometric Identity",
        "expected": "1",
        "category": "Trigonometry",
        "mode": "trigonometry",
        "difficulty": "Easy",
        "description": "The fundamental unit-circle identity: sin²(x) + cos²(x) = 1.",
        "expr_fn": lambda: parse_expr_str("sin(x)^2 + cos(x)^2"),
    },
    "trig_sin_double": {
        "math": "sin(2x)",
        "name": "Sine Double Angle Identity",
        "expected": "2*sin(x)*cos(x)",
        "category": "Trigonometry",
        "mode": "trigonometry",
        "difficulty": "Medium",
        "description": "Double angle sine decomposition: sin(2x) = 2 sin(x) cos(x).",
        "expr_fn": lambda: parse_expr_str("sin(2*x)"),
    },
    "trig_cos_double": {
        "math": "cos(2x)",
        "name": "Cosine Double Angle Identity",
        "expected": "cos²(x) - sin²(x)",
        "category": "Trigonometry",
        "mode": "trigonometry",
        "difficulty": "Medium",
        "description": "Double angle cosine decomposition: cos(2x) = cos²(x) - sin²(x).",
        "expr_fn": lambda: parse_expr_str("cos(2*x)"),
    },
    "trig_tan_ratio": {
        "math": "tan(x)",
        "name": "Tangent Ratio Definition",
        "expected": "sin(x)/cos(x)",
        "category": "Trigonometry",
        "mode": "trigonometry",
        "difficulty": "Easy",
        "description": "Ratio definition of tangent: tan(x) = sin(x)/cos(x).",
        "expr_fn": lambda: parse_expr_str("tan(x)"),
    },
    # 5. Geometric Formulas
    "geom_pythagorean": {
        "math": "sqrt(a² + b²)",
        "name": "Pythagorean Hypotenuse",
        "expected": "sqrt(a^2 + b^2)",
        "category": "Geometry",
        "mode": "geometry",
        "difficulty": "Medium",
        "description": "Euclidean distance / right-triangle hypotenuse formula.",
        "expr_fn": lambda: parse_expr_str("sqrt(a^2 + b^2)"),
    },
    "geom_triangle_area": {
        "math": "(a * b) / 2",
        "name": "Right Triangle Area",
        "expected": "a*b/2",
        "category": "Geometry",
        "mode": "geometry",
        "difficulty": "Easy",
        "description": "Area formula for a right triangle with base a and height b.",
        "expr_fn": lambda: parse_expr_str("(a * b) / 2"),
    },
    "geom_rect_perimeter": {
        "math": "2 * (a + b)",
        "name": "Rectangle Perimeter",
        "expected": "2*a + 2*b",
        "category": "Geometry",
        "mode": "geometry",
        "difficulty": "Easy",
        "description": "Perimeter formula for a rectangle with sides a and b.",
        "expr_fn": lambda: parse_expr_str("2 * (a + b)"),
    },
}


def get_target_expression(target_name: str, mode: str = "algebra") -> ExprNode:
    """Resolve target name or custom formula string to a concrete AST expression."""
    clean_name = target_name.strip()
    if clean_name in EXAMPLE_TARGETS:
        return EXAMPLE_TARGETS[clean_name]["expr_fn"]()

    # Support raw summation expressions, e.g. sum_k=1..n(...) or sum(...)
    n = expr_factory.variable("n")
    if clean_name.startswith("sum_k=1..n(") and clean_name.endswith(")"):
        inner = clean_name[len("sum_k=1..n("):-1]
        term_node = parse_expr_str(inner)
        return expr_factory.op("sum", term_node, n)
    elif clean_name.startswith("sum(") and clean_name.endswith(")"):
        inner = clean_name[len("sum("):-1]
        term_node = parse_expr_str(inner)
        return expr_factory.op("sum", term_node, n)

    # In continuous modes (trigonometry, geometry, calculus) or non-k targets, parse directly as formula
    try:
        parsed = parse_expr_str(clean_name)
        if mode in ("trigonometry", "geometry", "calculus") or "k" not in parsed.variables:
            return parsed
        # For discrete algebra over k, wrap as sum
        return expr_factory.op("sum", parsed, n)
    except Exception:
        presets = ", ".join(EXAMPLE_TARGETS.keys())
        raise ValueError(f"Unknown target '{target_name}'. Use a preset ({presets}) or a valid mathematical formula string.")


def cmd_targets(args):
    """Display catalog of available example targets with math, expected formula, and CLI command."""
    mode_filter = getattr(args, "mode", "all")
    print("=" * 96)
    print("🎯 AVAILABLE EXAMPLE TARGETS TO GET STARTED")
    print("=" * 96)
    print(f"{'Target Key':<22} | {'Mode':<12} | {'Target (Math)':<24} | {'Expected Form':<20} | {'Diff':<8}")
    print("-" * 96)
    for key, info in EXAMPLE_TARGETS.items():
        t_mode = info.get("mode", "algebra")
        if mode_filter != "all" and t_mode != mode_filter:
            continue
        print(f"{key:<22} | {t_mode:<12} | {info['math']:<24} | {info['expected']:<20} | {info['difficulty']:<8}")
        print(f"   └─ {info['name']}: {info['description']}")
        print(f"      Run: python -m evolutionary_math.cli discover --target {key} --mode {t_mode}")
        print("-" * 96)
    print("\n💡 TIP: You can also pass any custom mathematical formula directly:")
    print("   Algebra:      python -m evolutionary_math.cli discover --mode algebra --target \"k^2 + 2*k\"")
    print("   Trigonometry: python -m evolutionary_math.cli discover --mode trigonometry --target \"sin(x)^2 + cos(x)^2\"")
    print("   Geometry:     python -m evolutionary_math.cli discover --mode geometry --target \"sqrt(a^2 + b^2)\"")
    print("=" * 96)



def cmd_discover(args):
    mode = getattr(args, "mode", "algebra")
    if args.target in EXAMPLE_TARGETS and mode == "algebra":
        mode = EXAMPLE_TARGETS[args.target].get("mode", "algebra")

    target_lhs = get_target_expression(args.target, mode=mode)
    kb = KnowledgeBase(args.db)

    # Configure optional LLM advisory interface
    controller: Optional[AdvisoryController] = None
    if args.llm_url:
        client = OpenAICompatibleAdvisoryClient(
            base_url=args.llm_url,
            model=args.llm_model,
            api_key=args.llm_key,
            timeout_seconds=args.llm_timeout,
        )
        controller = AdvisoryController(client=client, stagnation_threshold=args.stagnation, async_mode=True)
    elif args.mock_llm:
        client = MockAdvisoryClient(confidence=0.92)
        controller = AdvisoryController(client=client, stagnation_threshold=args.stagnation)

    engine = EvolutionEngine(
        num_islands=args.islands,
        island_population_size=args.pop_size,
        migration_interval=args.migration,
        knowledge_base=kb,
        advisory_controller=controller,
        auto_promote_lemmas=args.promote_lemmas,
        mode=mode,
        seed=args.seed,
    )

    if args.live:
        dashboard = DiscoveryDashboard()
        res = dashboard.run_live(
            engine=engine,
            target_lhs=target_lhs,
            max_generations=args.generations,
            experiment_id=f"cli_{args.target}",
        )
        kb.close()
        return

    print("=" * 80)
    print(f"DISCOVERY RUN: Target '{args.target}' [{mode.upper()} MODE] -> {target_lhs}")
    print(f"Topology: {args.islands} Islands | Pop/Island: {args.pop_size} | LLM Advisory: {'Enabled' if controller else 'Disabled'}")
    print("=" * 80)

    def logger(telem: DiscoveryTelemetry):
        adv_str = f" [⚡ {telem.advisory_intervention}]" if telem.advisory_intervention else ""
        if telem.advisory_intervention or telem.generation % 5 == 0 or telem.best_validity > 0.95:
            print(f"[Gen {telem.generation:3d}] Best Validity: {telem.best_validity:.4f} | Leading: {telem.best_candidate_str}{adv_str}")

    res = engine.run(
        target_lhs=target_lhs,
        max_generations=args.generations,
        experiment_id=f"cli_{args.target}",
        callback=logger,
    )

    print("-" * 80)
    if res.success and res.discovered_theorem:
        th = res.discovered_theorem
        name = th.name or infer_theorem_name(th.target_str)
        target = th.clean_target or format_clean_target(th.target_str)
        formula = th.clean_formula or format_clean_formula(th.discovery_str)
        expanded = th.expanded_formula or format_expanded_formula(th.definition_ast or th.discovery_str)
        deps = f" [Composes: {', '.join(th.dependency_ids)}]" if th.dependency_ids else ""

        print("\n" + "═" * 80)
        print(f"🎉 THEOREM DISCOVERED & PROVEN! [{th.id[:8]}]")
        print(f"   Name:         {name}")
        print(f"   Target:       {target}")
        print(f"   Closed Form:  {formula}{deps}")
        if expanded != formula:
            print(f"   Expanded:     {expanded}")
        if th.latex:
            print(f"   LaTeX:        {th.latex}")
        print(f"   Proof:        {th.proof_method} (Gen {res.total_generations} in {res.total_time_sec:.3f}s)")
        print(f"   Storage:      Retained in '{args.db}'")
        if th.explanation:
            print(f"   💡 Intuition: {th.explanation}")
        print("═" * 80 + "\n")
    else:
        print(f"\nSearch concluded without formal verification in {res.total_generations} generations.")

    kb.close()


def cmd_campaign(args):
    kb = KnowledgeBase(args.db)
    mode = getattr(args, "mode", "algebra")

    controller: Optional[AdvisoryController] = None
    if args.llm_url:
        client = OpenAICompatibleAdvisoryClient(
            base_url=args.llm_url,
            model=args.llm_model,
            api_key=args.llm_key,
            timeout_seconds=args.llm_timeout,
        )
        controller = AdvisoryController(client=client, stagnation_threshold=args.stagnation, async_mode=True)
    else:
        # Default to MockAdvisoryClient for deterministic guidance in campaigns
        client = MockAdvisoryClient(confidence=0.92)
        controller = AdvisoryController(client=client, stagnation_threshold=args.stagnation)

    max_theorems = None if args.continuous else args.max_theorems

    campaign = AutonomousDiscoveryCampaign(
        knowledge_base=kb,
        advisory_controller=controller,
        num_islands=args.islands,
        island_population_size=args.pop_size,
        generations_per_target=args.generations,
        mode=mode,
        seed=args.seed,
    )

    print("=" * 80)
    print("🚀 AUTONOMOUS MATHEMATICAL DISCOVERY CAMPAIGN LAUNCHED")
    print("=" * 80)
    print(f"Goal:            Discover {max_theorems if max_theorems else 'unlimited'} new mathematical theorems")
    print(f"Domain Mode:     {mode.title()} (Customized grammar & test points)")
    print(f"Storage:         SQLite Knowledge Base '{args.db}'")
    print(f"LLM Guidance:    {'Enabled' if controller else 'Disabled (Offline Heuristics)'}")
    print(f"Lemma Promotion: Enabled (Cumulative Knowledge Accumulation)")
    print("=" * 80)

    def on_breakthrough(th: StoredTheorem, res: EngineRunResult):
        name = th.name or infer_theorem_name(th.target_str)
        target = th.clean_target or format_clean_target(th.target_str)
        formula = th.clean_formula or format_clean_formula(th.discovery_str)
        expanded = th.expanded_formula or format_expanded_formula(th.definition_ast or th.discovery_str)
        deps = f" [Composes: {', '.join(th.dependency_ids)}]" if th.dependency_ids else ""

        print("\n" + "═" * 80)
        print(f"🎉 THEOREM DISCOVERED & PROVEN! [{th.id[:8]}]")
        print(f"   Name:         {name}")
        print(f"   Target:       {target}")
        print(f"   Formula:      {formula}{deps}")
        if expanded != formula:
            print(f"   Expanded:     {expanded}")
        if th.latex:
            print(f"   LaTeX:        {th.latex}")
        print(f"   Proof:        {th.proof_method} (Gen {res.total_generations} in {res.total_time_sec:.3f}s)")
        if th.explanation:
            print(f"   💡 Intuition: {th.explanation}")
        print("═" * 80 + "\n")

    def on_telemetry(target: ExprNode, telem: DiscoveryTelemetry):
        if telem.advisory_intervention or telem.generation % 10 == 0 or telem.best_validity > 0.95:
            clean_tgt = format_clean_target(target)
            adv = f" [⚡ {telem.advisory_intervention}]" if telem.advisory_intervention else ""
            print(f"[{clean_tgt}] Gen {telem.generation:2d} | Val: {telem.best_validity:.4f} | Leading: {telem.best_candidate_str[:40]}{adv}")

    theorems = campaign.run(
        max_theorems=max_theorems,
        on_breakthrough=on_breakthrough,
        on_telemetry=on_telemetry,
    )

    print("\n" + "=" * 80)
    print(f"🏁 CAMPAIGN SUMMARY: {len(theorems)} Theorems Proven & Retained in '{args.db}'")
    print("=" * 80)
    for i, t in enumerate(theorems, start=1):
        name = t.name or infer_theorem_name(t.target_str)
        target = t.clean_target or format_clean_target(t.target_str)
        formula = t.clean_formula or format_clean_formula(t.discovery_str)
        deps = f" [Depends on: {', '.join(t.dependency_ids)}]" if t.dependency_ids else " [Foundational]"
        print(f"{i}. [{t.id[:8]}] {name}: {target} = {formula}{deps}")
        if t.explanation:
            print(f"   💡 {t.explanation}")

    kb.close()


def cmd_list(args):
    kb = KnowledgeBase(args.db)
    theorems = kb.get_all_theorems()
    print("=" * 80)
    print(f"📚 STORED MATHEMATICAL DISCOVERIES ({args.db})")
    print(f"Total Formally Verified Theorems: {len(theorems)}")
    print("=" * 80)
    if not theorems:
        print("Knowledge base is currently empty.")
    for i, t in enumerate(theorems, start=1):
        name = t.name or infer_theorem_name(t.target_str)
        target = t.clean_target or format_clean_target(t.target_str)
        formula = t.clean_formula or format_clean_formula(t.discovery_str)
        expanded = t.expanded_formula or format_expanded_formula(t.definition_ast or t.discovery_str)
        deps = f" [Composes: {', '.join(t.dependency_ids)}]" if t.dependency_ids else " [Foundational]"
        badge = " [General Meta-Theorem (holds for all parameters)]" if t.is_generalized else ""

        print(f"\n{i}. [{t.id[:8]}] {name}{badge}")
        print(f"   Target:    {target}")
        print(f"   Formula:   {formula}{deps}")
        if expanded != formula:
            print(f"   Expanded:  {expanded}")
        if t.latex:
            print(f"   LaTeX:     {t.latex}")
        print(f"   Proof:     {t.proof_method} | Generation: {t.generation}")
        if t.explanation:
            print(f"   💡 Meaning: {t.explanation}")
        print("-" * 80)

    kb.close()


def cmd_consolidate(args):
    """Consolidate repetitive numerical iterations into unified generalized meta-theorems."""
    kb = KnowledgeBase(args.db)
    print("=" * 80)
    print(f"🧹 CONSOLIDATING THEOREM FAMILIES IN '{args.db}'")
    print("=" * 80)
    count = kb.consolidate_parametric_families()
    if count > 0:
        print(f"🎉 Successfully consolidated {count} repetitive theorem iterations into generalized meta-theorems!")
    else:
        print("No redundant concrete clusters detected. Knowledge base is already normalized.")
    print("=" * 80)
    kb.close()


def cmd_export(args):
    kb = KnowledgeBase(args.db)
    if args.format == "markdown":
        output = export_knowledge_base_markdown(kb, title=args.title)
    elif args.format == "mermaid":
        output = export_knowledge_base_mermaid(kb)
    elif args.format == "latex":
        theorems = kb.get_all_theorems()
        lines = ["% Exported LaTeX Mathematical Discoveries", ""]
        for t in theorems:
            latex_eq = t.latex or format_complete_latex(t.target_str, t.definition_ast or t.discovery_str)
            lines.append(f"% Theorem [{t.id[:8]}]: {t.name}")
            lines.append(rf"\[ {latex_eq} \]")
            lines.append("")
        output = "\n".join(lines)
    elif args.format == "lean4":
        theorems = kb.get_all_theorems()
        output = generate_lean4_proof_file(theorems)
    else:
        output = export_knowledge_base_markdown(kb)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Successfully exported {args.format} report to '{args.output}'")
    else:
        print(output)
    kb.close()


def cmd_graph(args):
    kb = KnowledgeBase(args.db)
    mermaid_code = export_knowledge_base_mermaid(kb)
    print(mermaid_code)
    kb.close()


def cmd_latex(args):
    kb = KnowledgeBase(args.db)
    theorems = kb.get_all_theorems()
    print("% Exported LaTeX Discoveries")
    for t in theorems:
        latex_eq = t.latex or (to_latex(t.definition_ast) if t.definition_ast else t.discovery_str)
        print(f"% Theorem [{t.id[:8]}] {t.name} (Proof: {t.proof_method})")
        print(rf"\[ {latex_eq} \]")
    kb.close()


def cmd_fishbone(args):
    kb = KnowledgeBase(args.db)
    theorems = kb.get_all_theorems()

    target_str = args.target
    matched_th = None
    if target_str:
        for t in theorems:
            if target_str in t.target_str or target_str in t.id or (t.name and target_str.lower() in t.name.lower()):
                matched_th = t
                target_str = t.target_str
                break
    elif theorems:
        matched_th = theorems[0]
        target_str = matched_th.target_str

    # Fetch recorded search branches from database
    branches = kb.get_search_history(target_str=target_str)
    if not branches and matched_th:
        # Synthesize from stored theorem for existing legacy discoveries
        from evolutionary_math.utils.fishbone import synthesize_fishbone_from_theorem
        branches = synthesize_fishbone_from_theorem(matched_th)

    if not branches:
        print(f"No search history recorded in '{args.db}'.")
        kb.close()
        return

    target_str = target_str or branches[0].target_str
    name = matched_th.name if matched_th and matched_th.name else infer_theorem_name(target_str)
    title = f"Evolutionary Search Effort: {name}"

    from evolutionary_math.utils.fishbone import (
        generate_fishbone_svg,
        generate_fishbone_html,
        generate_fishbone_mermaid,
    )

    if args.format == "svg":
        output = generate_fishbone_svg(branches, title=title)
    elif args.format == "html":
        output = generate_fishbone_html(branches, title=title)
    elif args.format == "mermaid":
        output = generate_fishbone_mermaid(branches, title=title)
    else:
        output = generate_fishbone_svg(branches, title=title)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Fishbone diagram exported to '{args.output}' ({args.format.upper()})")
    else:
        print(output)

    kb.close()


def cmd_history(args):
    kb = KnowledgeBase(args.db)
    theorems = kb.get_all_theorems()
    target_str = args.target
    matched_th = None
    if target_str:
        for t in theorems:
            if target_str in t.target_str or target_str in t.id or (t.name and target_str.lower() in t.name.lower()):
                matched_th = t
                target_str = t.target_str
                break
    elif theorems:
        matched_th = theorems[0]
        target_str = matched_th.target_str

    branches = kb.get_search_history(target_str=target_str)
    if not branches and matched_th:
        from evolutionary_math.utils.fishbone import synthesize_fishbone_from_theorem
        branches = synthesize_fishbone_from_theorem(matched_th)

    print("=" * 80)
    print("📜 SEARCH EFFORT & HYPOTHESIS LINEAGE HISTORY")
    print(f"Database: '{args.db}' | Target: {target_str or 'All'}")
    print("=" * 80)
    if not branches:
        print("No exploration history found.")
    else:
        for b in branches:
            badge = "🟢 SUCCESS" if b.status in ("breakthrough", "milestone") else "🔴 FAILED "
            if b.status == "intervention":
                badge = "🟡 ADVISORY"
            op = b.operator.replace("_", " ").title()
            formula = b.clean_formula or b.candidate_str or "—"
            print(f"Gen {b.generation:2d} | {badge} [{b.status.upper():12s}] | Val: {b.validity:.4f} | {formula:22s} ({op})")
            if b.reason:
                print(f"        └─ {b.reason}")
    kb.close()


def main():
    parser = argparse.ArgumentParser(description="Evolutionary Mathematical Discovery Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'discover' sub-command
    p_disc = subparsers.add_parser("discover", help="Run evolutionary search to discover a mathematical relationship")
    p_disc.add_argument("--target", default="sum_k", help="Target preset (e.g. sum_k, sum_k2, trig_pythagorean, geom_pythagorean) or mathematical formula string")
    p_disc.add_argument("--mode", choices=["algebra", "trigonometry", "geometry", "calculus"], default="algebra", help="Mathematical domain mode (sets grammar, evaluation domain, and operators)")
    p_disc.add_argument("--islands", type=int, default=4, help="Number of evolutionary islands")
    p_disc.add_argument("--pop-size", type=int, default=50, help="Population size per island")
    p_disc.add_argument("--generations", type=int, default=100, help="Max evolutionary generations")
    p_disc.add_argument("--migration", type=int, default=5, help="Migration interval (generations)")
    p_disc.add_argument("--stagnation", type=int, default=6, help="Stagnation threshold for LLM intervention")
    p_disc.add_argument("--db", default="discoveries.db", help="SQLite database path")
    p_disc.add_argument("--seed", type=int, default=None, help="PRNG random seed")
    p_disc.add_argument("--promote-lemmas", action="store_true", default=True, help="Automatically promote verified discoveries as lemmas")
    p_disc.add_argument("--mock-llm", action="store_true", help="Enable rule-based Mock LLM advisory guidance")
    p_disc.add_argument("--llm-url", type=str, default=None, help="OpenAI-compatible LLM endpoint (e.g. http://localhost:11434/v1)")
    p_disc.add_argument("--llm-model", type=str, default="llama3", help="LLM model name")
    p_disc.add_argument("--llm-key", type=str, default="none", help="LLM API key")
    p_disc.add_argument("--llm-timeout", type=float, default=30.0, help="LLM HTTP timeout in seconds (default: 30.0)")
    p_disc.add_argument("--live", action="store_true", help="Display live terminal interactive dashboard")
    p_disc.set_defaults(func=cmd_discover)

    # 'campaign' sub-command (autonomous continuous discovery)
    p_camp = subparsers.add_parser("campaign", help="Set the engine loose on an autonomous discovery campaign")
    p_camp.add_argument("--mode", choices=["algebra", "trigonometry", "geometry", "calculus"], default="algebra", help="Mathematical domain mode for autonomous campaign")
    p_camp.add_argument("--max-theorems", type=int, default=3, help="Number of theorems to discover before stopping")
    p_camp.add_argument("--continuous", action="store_true", help="Run indefinitely, continuously discovering mathematics")
    p_camp.add_argument("--generations", type=int, default=45, help="Generations allocated per target problem space")
    p_camp.add_argument("--islands", type=int, default=4, help="Number of evolutionary islands")
    p_camp.add_argument("--pop-size", type=int, default=40, help="Population size per island")
    p_camp.add_argument("--stagnation", type=int, default=5, help="Stagnation threshold for LLM intervention")
    p_camp.add_argument("--db", default="autonomous_discoveries.db", help="SQLite database path")
    p_camp.add_argument("--seed", type=int, default=42, help="PRNG random seed")
    p_camp.add_argument("--mock-llm", action="store_true", default=True, help="Enable LLM advisory guidance")
    p_camp.add_argument("--llm-url", type=str, default=None, help="OpenAI-compatible LLM endpoint")
    p_camp.add_argument("--llm-model", type=str, default="llama3", help="LLM model name")
    p_camp.add_argument("--llm-key", type=str, default="none", help="LLM API key")
    p_camp.add_argument("--llm-timeout", type=float, default=30.0, help="LLM HTTP timeout in seconds (default: 30.0)")
    p_camp.set_defaults(func=cmd_campaign)

    # 'list' sub-command
    p_list = subparsers.add_parser("list", help="List all stored discoveries in the knowledge base")
    p_list.add_argument("--db", default="discoveries.db", help="SQLite database path")
    p_list.set_defaults(func=cmd_list)

    # 'graph' sub-command
    p_graph = subparsers.add_parser("graph", help="Export Mermaid dependency graph of theorems")
    p_graph.add_argument("--db", default="discoveries.db", help="SQLite database path")
    p_graph.set_defaults(func=cmd_graph)

    # 'latex' sub-command
    p_latex = subparsers.add_parser("latex", help="Export discoveries formatted as LaTeX equations")
    p_latex.add_argument("--db", default="discoveries.db", help="SQLite database path")
    p_latex.set_defaults(func=cmd_latex)

    # 'export' sub-command
    p_export = subparsers.add_parser("export", help="Export discoveries to Markdown, Mermaid, LaTeX, or Lean 4 format")
    p_export.add_argument("--db", default="discoveries.db", help="SQLite database path")
    p_export.add_argument("--format", choices=["markdown", "mermaid", "latex", "lean4"], default="markdown", help="Export format")
    p_export.add_argument("--output", "-o", type=str, default=None, help="Output file path (default: stdout)")
    p_export.add_argument("--title", type=str, default="Mathematical Knowledge Base Discoveries", help="Document title")
    p_export.set_defaults(func=cmd_export)

    # 'fishbone' sub-command (Ishikawa-style search tree visualization)
    p_fishbone = subparsers.add_parser("fishbone", help="Generate a fishbone-style search effort and failure diagram")
    p_fishbone.add_argument("--target", type=str, default=None, help="Target identity or theorem ID to trace")
    p_fishbone.add_argument("--db", default="autonomous_discoveries.db", help="SQLite database path")
    p_fishbone.add_argument("--format", choices=["svg", "html", "mermaid"], default="svg", help="Output diagram format")
    p_fishbone.add_argument("--output", "-o", type=str, default=None, help="Output file path (default: stdout)")
    p_fishbone.set_defaults(func=cmd_fishbone)

    # 'history' sub-command (text tabular log of exploration effort)
    p_history = subparsers.add_parser("history", help="Show chronological search effort, failures, and milestones")
    p_history.add_argument("--target", type=str, default=None, help="Target identity or theorem ID to trace")
    p_history.add_argument("--db", default="autonomous_discoveries.db", help="SQLite database path")
    p_history.set_defaults(func=cmd_history)

    # 'targets' sub-command (catalog of example targets to get users started)
    p_targets = subparsers.add_parser("targets", help="List all available example targets with math descriptions")
    p_targets.add_argument("--mode", choices=["algebra", "trigonometry", "geometry", "calculus", "all"], default="all", help="Filter target catalog by domain mode")
    p_targets.set_defaults(func=cmd_targets)

    # 'consolidate' sub-command (merge redundant numerical iterations into general meta-theorems)
    p_cons = subparsers.add_parser("consolidate", help="Consolidate repetitive numerical iterations into unified generalized meta-theorems")
    p_cons.add_argument("--db", default="autonomous_discoveries.db", help="SQLite database path")
    p_cons.set_defaults(func=cmd_consolidate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


"""LaTeX formatting, human-readable algebra, ASCII tree visualization, and Markdown/Mermaid exports."""

import re
from typing import List, Optional, Union, TYPE_CHECKING
import sympy as sp

from evolutionary_math.core.ast import ExprNode, ConstantNode, VariableNode, OperatorNode, LemmaNode, SequenceTermNode

if TYPE_CHECKING:
    from evolutionary_math.storage.knowledge_base import KnowledgeBase, StoredTheorem


def to_clean_unicode(node: ExprNode) -> str:
    """Format an AST node into clean mathematical Unicode notation."""
    if isinstance(node, ConstantNode):
        return str(node.value)
    if isinstance(node, VariableNode):
        return node.name
    if isinstance(node, LemmaNode):
        return f"{node.lemma_id}({to_clean_unicode(node.arg)})"
    if isinstance(node, SequenceTermNode):
        return f"{node.seq_name}_{{{to_clean_unicode(node.index_expr)}}}"
    if isinstance(node, OperatorNode):
        op = node.op
        children = node.children
        if op == "+":
            left, right = children[0], children[1]
            if isinstance(left, ConstantNode) and not isinstance(right, ConstantNode):
                if left.value < 0:
                    return f"{to_clean_unicode(right)} - {abs(left.value)}"
                else:
                    return f"{to_clean_unicode(right)} + {to_clean_unicode(left)}"
            elif isinstance(right, ConstantNode) and right.value < 0:
                return f"{to_clean_unicode(left)} - {abs(right.value)}"
            return f"{to_clean_unicode(left)} + {to_clean_unicode(right)}"
        elif op == "-":
            left, right = children[0], children[1]
            r_str = f"({to_clean_unicode(right)})" if isinstance(right, OperatorNode) and right.op in ("+", "-") else to_clean_unicode(right)
            return f"{to_clean_unicode(left)} - {r_str}"
        elif op == "*":
            left, right = children[0], children[1]
            left_str = to_clean_unicode(left)
            right_str = to_clean_unicode(right)
            if isinstance(left, OperatorNode) and left.op in ("+", "-"):
                left_str = f"({left_str})"
            if isinstance(right, OperatorNode) and right.op in ("+", "-"):
                right_str = f"({right_str})"
            if isinstance(left, ConstantNode) and (isinstance(right, VariableNode) or right_str.startswith("(")):
                return f"{left_str}{right_str}"
            if isinstance(left, VariableNode) and right_str.startswith("("):
                return f"{left_str}{right_str}"
            return f"{left_str}{right_str}" if (left_str.endswith(")") or right_str.startswith("(")) else f"{left_str}*{right_str}"
        elif op == "/":
            num_str = to_clean_unicode(children[0])
            den_str = to_clean_unicode(children[1])
            if isinstance(children[1], OperatorNode):
                den_str = f"({den_str})"
            return f"{num_str} / {den_str}"
        elif op == "^":
            exp_char = {"2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷"}.get(to_clean_unicode(children[1]), f"^{to_clean_unicode(children[1])}")
            base_str = to_clean_unicode(children[0])
            if isinstance(children[0], OperatorNode):
                base_str = f"({base_str})"
            return f"{base_str}{exp_char}"
        elif op == "sqrt":
            return f"sqrt({to_clean_unicode(children[0])})"
        elif op in ("sin", "cos", "tan"):
            return f"{op}({to_clean_unicode(children[0])})"
        elif op == "abs":
            return f"|{to_clean_unicode(children[0])}|"
        elif op == "sum":
            term_str = to_clean_unicode(children[0])
            if isinstance(children[0], OperatorNode) and children[0].op in ("+", "-"):
                term_str = f"({term_str})"
            upper_str = to_clean_unicode(children[1])
            return f"∑_{{k=1}}^{upper_str} {term_str}"
    return str(node)


def format_clean_target(target: Union[ExprNode, str]) -> str:
    """Format a mathematical target expression into clean standard mathematical notation.
    
    Transforms internal AST strings like 'sum_k=1..n(((2 * k) - 1))' into '∑_{k=1}^n (2k - 1)'.
    """
    if isinstance(target, ExprNode):
        return to_clean_unicode(target)

    s = str(target).strip()
    try:
        from evolutionary_math.core.ast import parse_expr_str
        ast = parse_expr_str(s)
        return to_clean_unicode(ast)
    except Exception:
        pass

    # Generic discrete sum parser fallback
    m = re.match(r"^sum_k=1\.\.(\w+)\((.*)\)$", s)
    if m:
        upper = m.group(1)
        body = m.group(2)
        while body.startswith("(") and body.endswith(")"):
            body = body[1:-1]
        body = body.replace(" * ", "")
        return f"∑_{{k=1}}^{{{upper}}} ({body})"

    return s


def format_clean_formula(expr: Union[ExprNode, str]) -> str:
    """Format a discovered mathematical closed form into clean algebraic notation."""
    if isinstance(expr, ExprNode):
        try:
            # If the expression contains lemmas, preserve the modular composition
            if any(isinstance(node, LemmaNode) for node in _walk_ast(expr)):
                raw = str(expr)
                return _clean_math_symbols(raw)
            # Pure arithmetic expression: use SymPy to simplify and factor
            sp_expr = sp.simplify(expr.to_sympy())
            factored = sp.factor(sp_expr)
            return _clean_math_symbols(str(factored))
        except Exception:
            return _clean_math_symbols(str(expr))

    s = str(expr)
    return _clean_math_symbols(s)


def format_expanded_formula(expr: Union[ExprNode, str]) -> str:
    """Expand all composite lemmas into their full algebraic polynomial closed form."""
    if isinstance(expr, ExprNode):
        try:
            sp_expr = sp.simplify(expr.to_sympy())
            factored = sp.factor(sp_expr)
            return _clean_math_symbols(str(factored))
        except Exception:
            pass
    return _clean_math_symbols(str(expr))


def infer_theorem_name(target_str: str, discovery_str: Optional[str] = None) -> str:
    """Infer a human-readable mathematical name for a target identity."""
    t = str(target_str)

    # 1. Fractions / Telescoping series (prioritized to prevent subterm collision with (2k - 1))
    if "1 /" in t or "1/" in t:
        if "2 * k" in t or "2k" in t:
            return "Telescoping Series of Odd Factor Products 1/((2k-1)(2k+1))"
        if re.search(r"\(\s*k\s*\+\s*1\s*\)\s*\*\s*\(\s*k\s*\+\s*2\s*\)", t) or "((k + 1) * (k + 2))" in t:
            return "Shifted Harmonic Telescoping Series 1/((k+1)(k+2))"
        if re.search(r"k\s*\*\s*\(\s*k\s*\+\s*1\s*\)", t) or "(k * (k + 1))" in t:
            return "Harmonic Telescoping Series 1/(k(k+1))"
        return "Telescoping Rational Series"

    # 2. Powers of compound linear expressions
    if ("2 * k" in t or "2k" in t) and ("- 1" in t or "-1" in t) and ("^2" in t or "**2" in t or "²" in t):
        return "Sum of Squares of Consecutive Odd Numbers"
    if ("2 * k" in t or "2k" in t) and ("^2" in t or "**2" in t or "²" in t):
        return "Sum of Squares of Consecutive Even Numbers"

    # 3. Higher simplex / consecutive integer products
    if "k + 3" in t and "k + 2" in t and "k + 1" in t:
        return "Sum of Products of 4 Consecutive Integers (5-Simplex Numbers)"
    if "k + 2" in t and "k + 1" in t:
        return "Sum of Products of 3 Consecutive Integers (4-Simplex / Pentatope Numbers)"

    # 4. Generalized parametric identities (containing free parameter m or c)
    if re.search(r"k\s*\*\s*\(\s*k\s*\+\s*m\s*\)", t) or re.search(r"\(\s*k\s*\+\s*m\s*\)\s*\*\s*k", t):
        return "Generalized Pronic Sum Identity (∑ k(k + m))"
    elif re.search(r"\(\s*k\s*\+\s*m\s*\)", t) and "k *" not in t:
        return "Generalized Shifted Linear Sum (∑ (k + m))"
    elif re.search(r"\bc\s*\*\s*k\^2\b", t) or re.search(r"\bc\s*\*\s*\(?\s*k\s*\^\s*2\s*\)?", t):
        return "Generalized Scaled Square Sum (∑ c·k²)"
    elif re.search(r"\bc\s*\*\s*k\b", t):
        return "Generalized Scaled Linear Sum (∑ c·k)"

    # 5. Factor products k * (k + m)
    m_match = re.search(r"k\s*\*\s*\(\s*k\s*\+\s*(\d+)\s*\)", t) or re.search(r"\(\s*k\s*\+\s*(\d+)\s*\)\s*\*\s*k", t)
    if m_match:
        m_val = int(m_match.group(1))
        if m_val == 1:
            return "Sum of Consecutive Integer Products (Tetrahedral Sum)"
        elif m_val == 2:
            return "Sum of Pronic Rectangles k(k + 2)"
        else:
            return f"Shifted Pronic Sum ∑ k(k + {m_val})"

    # 6. Monomial power sums (Faulhaber)
    if "k^6" in t or "k⁶" in t:
        return "Faulhaber Polynomial Degree 6 (Sum of Sextics)"
    if "k^5" in t or "k⁵" in t:
        return "Faulhaber Polynomial Degree 5"
    if "k^4" in t or "k⁴" in t:
        return "Faulhaber Polynomial Degree 4 (Sum of Quartics)"
    if "k^3" in t or "k³" in t:
        return "Nicomachus's Theorem (Sum of First n Cubes)"
    if "k^2" in t or "k²" in t:
        return "Square Pyramidal Numbers (Sum of First n Squares)"

    # 7. Linear expressions
    if re.search(r"2\s*\*\s*k\s*\)?\s*-\s*1", t):
        return "Sum of Consecutive Odd Numbers"
    elif re.search(r"\b2\s*\*\s*k\b", t) and not re.search(r"2\s*\*\s*k\s*[\+\-]", t):
        return "Sum of Consecutive Even Numbers (Pronic Rectangles)"
    elif re.search(r"\(\s*k\s*\+\s*1\s*\)", t) and not re.search(r"k\s*\+\s*1\d", t):
        return "Sum of Shifted Integers (k + 1)"
    elif "sum_k=1..n(k)" in t or t == "k":
        return "Triangular Number Formula (Sum of 1..n)"
    elif "sum_k=1..n(1)" in t or t == "1":
        return "Discrete Counting Identity"

    # 8. Trigonometric identities
    if ("sin" in t and "cos" in t) and ("^2" in t or "**2" in t):
        return "Pythagorean Trigonometric Identity"
    elif "sin(2" in t or "sin(2*" in t:
        return "Sine Double Angle Identity"
    elif "cos(2" in t or "cos(2*" in t:
        return "Cosine Double Angle Identity"
    elif "tan" in t:
        return "Tangent Ratio Identity"
    elif "sin" in t or "cos" in t:
        clean = format_clean_target(t)
        return f"Trigonometric Identity ({clean})"

    # 6. Geometric identities
    if "sqrt" in t and ("a" in t and "b" in t):
        return "Pythagorean Hypotenuse Metric"
    elif ("a" in t and "b" in t) and ("* 2" in t or "2 *" in t) and ("+" in t):
        return "Rectangle Perimeter Formula"
    elif ("a" in t and "b" in t) and "/" in t:
        return "Right Triangle Area Formula"
    elif "sqrt" in t or ("a" in t and "b" in t):
        clean = format_clean_target(t)
        return f"Geometric Identity ({clean})"

    clean = format_clean_target(t)
    if "sum" in t or "k" in t:
        return f"Discrete Sum Identity ({clean})"
    return f"Algebraic Identity ({clean})"


def format_complete_latex(target: Union[ExprNode, str], formula: Union[ExprNode, str]) -> str:
    """Generate a complete, publication-grade LaTeX mathematical equation LHS = RHS."""
    try:
        lhs_latex = to_latex(target) if isinstance(target, ExprNode) else _latex_from_string(target)
        if isinstance(formula, ExprNode):
            if any(isinstance(node, LemmaNode) for node in _walk_ast(formula)):
                rhs_latex = to_latex(formula)
            else:
                rhs_sp = sp.factor(sp.simplify(formula.to_sympy()))
                rhs_latex = sp.latex(rhs_sp)
        else:
            rhs_latex = _latex_from_string(formula)
        return rf"{lhs_latex} = {rhs_latex}"
    except Exception:
        return rf"{to_latex(target) if isinstance(target, ExprNode) else str(target)} = {to_latex(formula) if isinstance(formula, ExprNode) else str(formula)}"


def _clean_math_symbols(s: str) -> str:
    """Format raw Python/SymPy expression string into clean math notation."""
    s = s.replace("**2", "²").replace("**3", "³").replace("**4", "⁴")
    s = s.replace("**", "^")
    # Clean up outer superfluous parens: ((a) * (b)) -> (a * b)
    s = re.sub(r"\(([\w\s\+\-\*\/\^²³⁴]+)\)", r"\1", s) if s.count("(") == 1 and s.startswith("(") and s.endswith(")") else s
    return s


def _walk_ast(node: ExprNode):
    yield node
    for child in node.children:
        yield from _walk_ast(child)


def _latex_from_string(s: str) -> str:
    s = str(s).strip()
    try:
        from evolutionary_math.core.ast import parse_expr_str
        ast = parse_expr_str(s)
        return to_latex(ast)
    except Exception:
        pass
    if "sum_k=1..n" in s or "∑_{k=1}^n" in s:
        clean = format_clean_target(s).replace("∑_{k=1}^n ", "").strip()
        if clean.startswith("(") and clean.endswith(")"):
            inner = clean[1:-1]
            clean = rf"\left({inner}\right)"
        return rf"\sum_{{k=1}}^{{n}} {clean}"
    return s


def to_latex(expr: ExprNode) -> str:
    """Convert an AST expression into publication-grade LaTeX math syntax."""
    if isinstance(expr, ConstantNode):
        return str(expr.value)

    if isinstance(expr, VariableNode):
        return expr.name

    if isinstance(expr, LemmaNode):
        arg_latex = to_latex(expr.arg)
        return rf"\mathrm{{{expr.lemma_id}}}\left({arg_latex}\right)"

    if isinstance(expr, SequenceTermNode):
        idx_latex = to_latex(expr.index_expr)
        return rf"{expr.seq_name}_{{{idx_latex}}}"

    if isinstance(expr, OperatorNode):
        op = expr.op
        children = expr.children

        if op == "+":
            left, right = children[0], children[1]
            if isinstance(left, ConstantNode) and not isinstance(right, ConstantNode):
                if left.value < 0:
                    return f"{to_latex(right)} - {abs(left.value)}"
                else:
                    return f"{to_latex(right)} + {to_latex(left)}"
            elif isinstance(right, ConstantNode) and right.value < 0:
                return f"{to_latex(left)} - {abs(right.value)}"
            return f"{to_latex(left)} + {to_latex(right)}"
        elif op == "-":
            return f"{to_latex(children[0])} - {to_latex(children[1])}"
        elif op == "*":
            # Parenthesize sub-additions for precedence
            left_str = _bracket_if_needed(children[0], ("+", "-"))
            right_str = _bracket_if_needed(children[1], ("+", "-"))
            return f"{left_str} \\cdot {right_str}"
        elif op == "/":
            return rf"\frac{{{to_latex(children[0])}}}{{{to_latex(children[1])}}}"
        elif op == "^":
            base_str = _bracket_if_needed(children[0], ("+", "-", "*", "/"))
            return f"{base_str}^{{{to_latex(children[1])}}}"
        elif op == "neg":
            return f"-{to_latex(children[0])}"
        elif op == "sin":
            return rf"\sin\left({to_latex(children[0])}\right)"
        elif op == "cos":
            return rf"\cos\left({to_latex(children[0])}\right)"
        elif op == "tan":
            return rf"\tan\left({to_latex(children[0])}\right)"
        elif op == "sqrt":
            return rf"\sqrt{{{to_latex(children[0])}}}"
        elif op == "abs":
            return rf"\left|{to_latex(children[0])}\right|"
        elif op == "sum":
            # Discrete sum: sum_k=1..n (term)
            term_str = _bracket_if_needed(children[0], ("+", "-", "neg"))
            upper_str = to_latex(children[1])
            return rf"\sum_{{k=1}}^{{{upper_str}}} {term_str}"

    return str(expr)

    return str(expr)


def _bracket_if_needed(node: ExprNode, ops: tuple) -> str:
    latex_str = to_latex(node)
    if isinstance(node, OperatorNode) and node.op in ops:
        return rf"\left({latex_str}\right)"
    return latex_str


def to_ascii_tree(expr: ExprNode, prefix: str = "", is_last: bool = True) -> str:
    """Format an AST as a hierarchical ASCII tree."""
    connector = "└── " if is_last else "├── "
    if isinstance(expr, ConstantNode):
        label = f"Const: {expr.value}"
    elif isinstance(expr, VariableNode):
        label = f"Var: {expr.name}"
    elif isinstance(expr, LemmaNode):
        label = f"Lemma: {expr.lemma_id}"
    elif isinstance(expr, OperatorNode):
        label = f"Op: {expr.op}"
    else:
        label = str(expr)

    result = [prefix + connector + label]
    new_prefix = prefix + ("    " if is_last else "│   ")

    for i, child in enumerate(expr.children):
        child_is_last = (i == len(expr.children) - 1)
        result.append(to_ascii_tree(child, new_prefix, child_is_last))

    return "\n".join(result)


def export_knowledge_base_mermaid(kb: "KnowledgeBase") -> str:
    """Generate a Mermaid flowchart diagram showing all theorems and lemma dependencies."""
    theorems: List["StoredTheorem"] = kb.get_all_theorems()
    if not theorems:
        return "graph TD\n    Empty[Knowledge Base is Empty]"

    lines = ["graph TD"]
    for t in theorems:
        name = getattr(t, "name", None) or infer_theorem_name(t.target_str)
        clean_target = getattr(t, "clean_target", None) or format_clean_target(t.target_str)
        clean_discovery = getattr(t, "clean_formula", None) or format_clean_formula(t.discovery_str)
        clean_target_str = clean_target.replace('"', "'")
        clean_discovery_str = clean_discovery.replace('"', "'")
        label = f'"{t.id[:6]}: {name}<br/>{clean_target_str} = {clean_discovery_str}<br/>({t.proof_method})"'
        lines.append(f"    T_{t.id[:6]}[{label}]")

        for dep in t.dependency_ids:
            # If dependency matches another theorem prefix, create edge
            dep_clean = dep.replace("L_", "")
            lines.append(f"    T_{dep_clean} -->|composes| T_{t.id[:6]}")

    return "\n".join(lines)


def export_knowledge_base_markdown(kb: "KnowledgeBase", title: str = "Mathematical Knowledge Base Discoveries") -> str:
    """Export the entire SQLite knowledge base as a publication-ready Markdown document."""
    theorems = kb.get_all_theorems()
    lines = [
        f"# {title}",
        "",
        f"**Total Verified Discoveries:** {len(theorems)} theorems  ",
        "**Verification Engine:** 2-Tier Formal Induction (SymPy exact CAS certified)",
        "",
        "---",
        "",
        "## Summary Catalog",
        "",
        "| ID | Theorem Name | Target Problem | Verified Closed Form | Proof Method | Gen |",
        "|:---|:---|:---|:---|:---|:---:|",
    ]

    for t in theorems:
        name = getattr(t, "name", None) or infer_theorem_name(t.target_str)
        target = getattr(t, "clean_target", None) or format_clean_target(t.target_str)
        formula = getattr(t, "clean_formula", None) or format_clean_formula(t.discovery_str)
        lines.append(f"| `{t.id[:8]}` | **{name}** | `${target}$` | `${formula}$` | {t.proof_method} | {t.generation} |")

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Discovery Profiles",
        "",
    ])

    for i, t in enumerate(theorems, start=1):
        name = getattr(t, "name", None) or infer_theorem_name(t.target_str)
        target = getattr(t, "clean_target", None) or format_clean_target(t.target_str)
        formula = getattr(t, "clean_formula", None) or format_clean_formula(t.discovery_str)
        expanded = getattr(t, "expanded_formula", None) or format_expanded_formula(t.definition_ast or t.discovery_str)
        latex_eq = getattr(t, "latex", None) or (format_complete_latex(t.target_str, t.definition_ast) if t.definition_ast else "")
        explanation = getattr(t, "explanation", None) or "Formally verified discrete summation identity."
        deps = f"`{', '.join(t.dependency_ids)}`" if t.dependency_ids else "None (Foundational Primitive)"

        lines.extend([
            f"### {i}. {name} (`{t.id[:8]}`)",
            "",
            f"- **Target Problem:** `${target}$`",
            f"- **Closed Form (Modular):** `${formula}$`",
        ])
        if expanded != formula:
            lines.append(f"- **Expanded Polynomial:** `${expanded}$`")
        lines.extend([
            f"- **Dependencies:** {deps}",
            f"- **Proof Method:** {t.proof_method} (Discovered at Generation {t.generation})",
            "",
            "> [!NOTE]",
            f"> **Intuition & Geometric Meaning:**  ",
            f"> {explanation}",
            "",
        ])
        if latex_eq:
            lines.extend([
                "```latex",
                rf"\[ {latex_eq} \]",
                "```",
                "",
            ])

    lines.extend([
        "---",
        "",
        "## Dependency & Composition Lineage Graph",
        "",
        "```mermaid",
        export_knowledge_base_mermaid(kb),
        "```",
        "",
    ])

    if theorems:
        try:
            from evolutionary_math.utils.fishbone import generate_fishbone_mermaid, synthesize_fishbone_from_theorem
            sample_t = theorems[0]
            history = kb.get_search_history(target_str=sample_t.target_str)
            if not history:
                history = synthesize_fishbone_from_theorem(sample_t)
            if history:
                name = sample_t.name or infer_theorem_name(sample_t.target_str)
                lines.extend([
                    "---",
                    "",
                    f"## Evolutionary Search Effort & Failure Lineage (Fishbone: {name})",
                    "",
                    "> The central spine marks milestone breakthroughs across generations. Upper ribs depict successful structural advances; lower ribs depict falsified hypotheses and counterexample dead-ends.",
                    "",
                    "```mermaid",
                    generate_fishbone_mermaid(history),
                    "```",
                    "",
                ])
        except Exception:
            pass

    return "\n".join(lines)



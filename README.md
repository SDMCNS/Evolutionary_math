# Evolutionary Math (Proof of Concept)

> **Evolutionary_math**: A Python library and CLI that starts with a foundational mathematical vocabulary and progressively evolves its mathematical knowledge through trial and error, using evolutionary algorithms to explore, generate, and prove potentially novel mathematical theorems — entirely locally.

*This repository is a personal Proof of Concept (PoC) exploring autonomous mathematical discovery, deterministic symbolic verification, and local AI-assisted heuristic guidance.*

---

## Complete Documentation (`docs/`)
Comprehensive documentation is available in the [`docs/`](docs/) directory:
- 💡 [In Plain English: How It Works](docs/how_it_works_plain_english.md)
- 📖 [Documentation Index](docs/index.md)
- 🏗️ [System Architecture](docs/architecture.md)
- 💻 [Library Developer Guide & API Reference](docs/library_guide.md)
- 📐 [Methodology & Mathematical Foundations](docs/methodology.md)
- 🔬 [Abilities, Benchmarks & Theoretical Limitations](docs/abilities_and_limits.md)
- ⌨️ [Command-Line Interface (CLI) Reference](docs/cli_reference.md)

---

## Architectural Principles
1. **Deterministic computation does the work.** The LLM provides evolutionary guidance.
2. **Multi-tiered verification:**
   - **Tier 1:** Fast numerical falsification (< 0.2 ms).
   - **Tier 2:** Symbolic simplification, zero-equivalence, and mathematical induction (< 10 ms).
   - **Tier 3:** SMT counterexample searching.
   - **Tier 4:** Formal proof certification.
3. **Canonicalization & Anti-Triviality:** Expressions are normalized and checked for vacuous tautology prior to promotion.
4. **Multi-Objective Selection (NSGA-II):** Optimizes across `(Validity, Simplicity/MDL, Novelty)`.
5. **Island Topology:** Heterogeneous islands (Balanced, Exploration, Exploitation) with ring migration.
6. **Air-Gapped LLM Advisory Guidance:**
   - Triggers upon population stagnation or epoch boundaries.
   - Operates strictly through a Pydantic-validated JSON contract (`AdvisoryResponse`).
   - Dynamically biases grammar production rules and mutates operator distributions.
   - Supports local models via OpenAI-compatible endpoints (Ollama, vLLM, LM Studio) with 100% offline fallback.
7. **Automated Lemma Promotion & Cumulative Knowledge Accumulation (Phase 3):**
   - Verified discoveries are encapsulated into Automatically Defined Functions (ADFs) and promoted into grammar production rules.
   - The system reuses previously discovered lemmas to solve higher-order problems (e.g. leveraging $\sum k = \frac{n(n+1)}{2}$ to discover Nicomachus's Theorem $\sum k^3 = (\sum k)^2$ in 1 generation).
   - Tracks mathematical theorem lineages and dependency graphs in SQLite.
8. **Hybrid Discrete Calculus Solver:**
   - Incorporates an exact finite-difference solver to compute forward differences $\Delta^d Y$.
   - If differences vanish at order $d+1$, the closed form is derived via exact rational interpolation and factored, bypassing the combinatorial bottleneck for polynomial summations (e.g. $\sum k^2 = \frac{n(n+1)(2n+1)}{6}$ solved in $< 0.2$s).
9. **Advisory Subtree / Seed Injection:**
   - Strategic LLM recommendations can return `suggested_subtrees` (e.g. `(2*n + 1)`), which are canonicalized and seeded directly into exploratory islands.
10. **Zero-Intron Bloat Control:**
   - All offspring generated via crossover or mutation pass through algebraic identity canonicalization ($x+0 \to x, x \cdot 1 \to x, x-x \to 0, c_1 \odot c_2 \to c_3$), keeping expression depths compact.

---

## Directory Structure
```
evolutionary_math/
├── pyproject.toml
├── src/evolutionary_math/
│   ├── core/               # Strongly-typed AST, DAG maximal sharing, LemmaNode, canonicalizer
│   │   ├── ast.py
│   │   ├── canonicalizer.py
│   │   ├── operators.py
│   │   └── types.py
│   ├── grammar/            # CFG production rules & expression derivation (grow/full/ramped)
│   │   ├── generator.py
│   │   └── rules.py
│   ├── evaluation/         # Multi-tiered verification pipeline
│   │   ├── pipeline.py
│   │   ├── tier1_numerical.py
│   │   └── tier2_symbolic.py
│   ├── evolution/          # Multi-island GA, genetic operators, NSGA-II selection
│   │   ├── engine.py
│   │   ├── fitness.py
│   │   ├── individual.py
│   │   ├── island.py
│   │   ├── operators.py
│   │   └── selection.py
│   ├── advisory/           # Strictly air-gapped LLM meta-heuristic interface
│   │   ├── client.py       # Base, Mock, and OpenAICompatible HTTP clients
│   │   ├── controller.py   # Stagnation detection, schema validation, parameter adaptation
│   │   ├── schema.py       # Pydantic schemas (AdvisoryRequest / AdvisoryResponse)
│   │   └── telemetry.py    # Population summarizer and telemetry packer
│   └── storage/            # Persistent SQLite knowledge base with dependency tracking
│       └── knowledge_base.py
├── scripts/
│   ├── run_cumulative_discovery.py # Phase 3 flagship: Lemma promotion & Nicomachus's Theorem
│   ├── run_guided_discovery.py     # Phase 2: Discovery loop with active LLM advisory guidance
│   ├── benchmark_guided_sum_k2.py  # Phase 2: Higher-order target benchmark with dynamic intervention
│   ├── run_discovery.py            # Phase 1: Autonomous unguided discovery loop
│   └── verify_identities.py        # Phase 0: Verification harness across classical identities
└── tests/                          # 61 comprehensive unit & integration tests
```

---

## Quick Start & CLI

### 1. Mathematical Domain Modes (`--mode`)
Focus the activities of the engine across distinct mathematical branches:
- **`algebra` (default):** Discrete calculus, series summation $\sum_{k=1}^n P(k)$, power sums, pronic products, integer progressions.
- **`trigonometry`:** Unit circle relations, angle identities ($\sin, \cos, \tan$), double angles, product-to-sum equations over radian test points.
- **`geometry`:** Metric geometry, Euclidean hypotenuse $\sqrt{a^2 + b^2}$, triangle areas $(a \cdot b)/2$, perimeters $2(a + b)$.
- **`calculus`:** Continuous analysis, radicals, function approximations, power differences.

### 2. View Built-in Example Targets Catalog
```powershell
# View all available targets across all domains
python src/evolutionary_math/cli.py targets

# Filter targets by domain mode
python src/evolutionary_math/cli.py targets --mode trigonometry
python src/evolutionary_math/cli.py targets --mode geometry
```
Displays presets across algebra, trigonometry, and geometry:

| Target Key | Domain | Problem Space | Expected Form | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| `sum_k` | Algebra | $\sum_{k=1}^n k$ | $\frac{n(n+1)}{2}$ | `python src/evolutionary_math/cli.py discover --target sum_k` |
| `sum_k2` | Algebra | $\sum_{k=1}^n k^2$ | $\frac{n(n+1)(2n+1)}{6}$ | `python src/evolutionary_math/cli.py discover --target sum_k2` |
| `sum_k3` | Algebra | $\sum_{k=1}^n k^3$ | $\frac{n^2(n+1)^2}{4}$ | `python src/evolutionary_math/cli.py discover --target sum_k3` |
| `trig_pythagorean` | Trigonometry | $\sin^2(x) + \cos^2(x)$ | $1$ | `python src/evolutionary_math/cli.py discover --target trig_pythagorean --mode trigonometry` |
| `trig_sin_double` | Trigonometry | $\sin(2x)$ | $2\sin(x)\cos(x)$ | `python src/evolutionary_math/cli.py discover --target trig_sin_double --mode trigonometry` |
| `trig_cos_double` | Trigonometry | $\cos(2x)$ | $\cos^2(x) - \sin^2(x)$ | `python src/evolutionary_math/cli.py discover --target trig_cos_double --mode trigonometry` |
| `geom_pythagorean` | Geometry | $\sqrt{a^2 + b^2}$ | $\sqrt{a^2 + b^2}$ | `python src/evolutionary_math/cli.py discover --target geom_pythagorean --mode geometry` |
| `geom_rect_perimeter` | Geometry | $2(a + b)$ | $2a + 2b$ | `python src/evolutionary_math/cli.py discover --target geom_rect_perimeter --mode geometry` |

You can also pass **any custom formula directly**:
```powershell
# Algebra custom summation
python src/evolutionary_math/cli.py discover --mode algebra --target "k^2 + 2*k"

# Trigonometric custom identity
python src/evolutionary_math/cli.py discover --mode trigonometry --target "sin(x)^2 + cos(x)^2"

# Geometric custom formula
python src/evolutionary_math/cli.py discover --mode geometry --target "2 * (a + b)"
```

### 3. Run All Tests (78 Tests)
```powershell
python -m pytest tests/ -v
```

### 4. Parametric Meta-Theorems & Database Consolidation (`consolidate`)
Instead of generating hundreds of redundant theorems differing only by an incrementing number (e.g. $\sum k(k + 1), \sum k(k + 2), \dots, \sum k(k + 110)$), the engine lifts the numeric offset into a symbolic parameter $m$, formally proves the **generalized master theorem** across all $n$ and $m$:
$$\sum_{k=1}^n k(k + m) = \frac{n(n + 1)(2n + 3m + 1)}{6}$$
All concrete instances ($m=1, 2, \dots, 110, \dots$) are automatically **subsumed** and solved instantly without generating duplicate rows in the database.

To consolidate existing databases and purge repetitive concrete iterations:
```powershell
python src/evolutionary_math/cli.py consolidate --db autonomous_discoveries.db
```

### 4. Run Autonomous Continuous Discovery Campaign
```powershell
# Continuous campaign in algebra domain
python src/evolutionary_math/cli.py campaign --mode algebra --continuous --db research.db

# Continuous campaign in trigonometry domain
python src/evolutionary_math/cli.py campaign --mode trigonometry --continuous --db trig_research.db

# Continuous campaign with local LM Studio / Ollama guidance
python src/evolutionary_math/cli.py campaign --continuous --llm-url http://localhost:1234/v1 --llm-model qwen/qwen3.5-9b
```

### 3. List Stored Discoveries & Plain-English Intuition
```powershell
python src/evolutionary_math/cli.py list --db research.db
```

### 4. Visualize the Cumulative Lemma Graph
```powershell
python src/evolutionary_math/cli.py graph --db research.db
```

---

## Standalone Python Demonstrators

### 1. Cumulative Discovery (Phase 3 Flagship)
```powershell
python scripts/run_cumulative_discovery.py
```
Autonomously discovers $\sum k = \frac{n(n+1)}{2}$, encapsulates it into lemma `L_XXXX(n)`, uses that lemma to prove $\sum k^3 = [L_{XXXX}(n)]^2$ in 1 generation, and saves the dependency graph to SQLite!

### 2. LLM-Guided Discovery (Phase 2)
```powershell
python scripts/run_guided_discovery.py
```

### 3. Verification Harness (Phase 0)
```powershell
python scripts/verify_identities.py
```

---

## Inspecting & Exporting Discoveries

The engine transforms internal AST representations into standard mathematical notation, textbook algebraic closed forms, and plain-English geometric intuitions.

### 1. Structured Terminal Catalog
```powershell
python src/evolutionary_math/cli.py list --db autonomous_discoveries.db
```
Displays a catalog of theorems featuring named identities, standard $\sum$ summation notation, modular lemma calls, expanded polynomials, and geometric explanations.

### 2. Exporting Publication-Ready Markdown & LaTeX Reports
```powershell
# Export complete discovery report with LaTeX equations and Mermaid diagrams
python src/evolutionary_math/cli.py export --db autonomous_discoveries.db --format markdown -o DISCOVERIES.md

# Export pure LaTeX equations
python src/evolutionary_math/cli.py export --db autonomous_discoveries.db --format latex
```

### 3. Direct SQLite Inspection with `v_discoveries`
All SQLite databases include the `v_discoveries` view. Opening the database in any SQLite viewer or query tool:
```sql
SELECT id, name, target, formula, expanded_formula, proof_method, explanation 
FROM v_discoveries;
```
Yields textbook mathematical rows without raw S-expressions or opaque hashes.

### 4. Search Effort History & Fishbone Lineage Diagrams
Track the complete history of evolutionary attempts, milestone breakthroughs, and falsified counterexamples:
```powershell
# View tabular chronological search history
python src/evolutionary_math/cli.py history --db autonomous_discoveries.db --target 66ecf83a

# Export fishbone diagram in SVG, HTML, or Mermaid
python src/evolutionary_math/cli.py fishbone --db autonomous_discoveries.db --target 66ecf83a --format svg -o fishbone.svg
python src/evolutionary_math/cli.py fishbone --db autonomous_discoveries.db --target 66ecf83a --format html -o fishbone.html
python src/evolutionary_math/cli.py fishbone --db autonomous_discoveries.db --target 66ecf83a --format mermaid
```

# System Architecture

This document provides a comprehensive technical breakdown of the subsystems composing the **Evolutionary Mathematical Discovery Engine**.

---

## 1. Subsystem Architecture Overview

The codebase is organized into clean, decoupled layers under `src/evolutionary_math/`:

```
evolutionary_math/
├── core/               # Mathematical representations, ASTs, canonicalization
├── grammar/            # CFG production rules & expression derivation
├── evaluation/         # Multi-tiered verification pipeline (Numerical + Symbolic)
├── evolution/          # Multi-island GA, genetic operators, NSGA-II selection
├── advisory/           # Strictly air-gapped LLM guidance interface
├── campaign/           # Autonomous discovery campaign runner & agenda
├── storage/            # Persistent SQLite theorem & lineage repository
└── utils/              # LaTeX, Lean 4 exporter, ASCII tree, dashboard
```

---

## 2. Mathematical Representation Engine (`core/`)

### Strongly-Typed AST & Hash-Consed DAGs (`core/ast.py`)
Mathematical expressions are represented as immutable nodes organized into Directed Acyclic Graphs (DAGs) rather than naive recursive trees:

- **`ConstantNode`**: Exact scalars (`int`, `float`, `Fraction`).
- **`VariableNode`**: Named symbolic variables (e.g. `n`, `k`) with mathematical domains (`INTEGER`, `REAL`).
- **`OperatorNode`**: Arity-validated operators (`+`, `-`, `*`, `/`, `^`, `sum`, `neg`).
- **`LemmaNode`**: Represents the invocation of a previously verified theorem (Automatically Defined Function).
- **`ExpressionFactory` (`expr_factory`)**: Implements hash-consing. If an identical node has already been created, `expr_factory` returns the existing instance in $O(1)$ memory. This guarantees that structural identity testing ($A \equiv B$) is an instant reference comparison (`A is B`).

### Algebraic Canonicalization & Triviality Sieve (`core/canonicalizer.py`)
To prevent the evolutionary search from falling into the **Triviality Trap** (optimizing trivial tautologies such as $x \cdot 0 = 0$, $x - x = 0$, or $x + 1 = 1 + x$), expressions are passed through `canonicalize()`:
1. **Constant Folding:** Evaluates constant subtrees (e.g. $2^3 \to 8$).
2. **Algebraic Reductions:** Replaces identity elements ($x + 0 \to x$, $x \cdot 1 \to x$, $x - x \to 0$, $x / 1 \to x$).
3. **Commutative Sorting:** Reorders arguments of commutative operators (`+`, `*`) canonically so that $(x + 1) \equiv (1 + x)$ share the exact same DAG node.
4. **Tautology Detection (`is_trivial_tautology`)**: Falsifies candidates where $\text{LHS} \equiv \text{RHS}$ or $\text{LHS} - \text{RHS} = 0$ prior to consuming verification resources.

---

## 3. Multi-Tiered Verification Pipeline (`evaluation/`)

The evaluation pipeline guarantees mathematical truth through a strict fail-fast cascade:

```
[Candidate Relationship: LHS = RHS]
                │
                ▼
┌───────────────────────────────┐
│     Anti-Triviality Sieve     │ ── Trivial Tautology ──> [REJECTED_TRIVIAL (Score: 0.0)]
└───────────────────────────────┘
                │ Non-Trivial
                ▼
┌───────────────────────────────┐
│   Tier 1: Numerical Sieve     │ ── Mismatch Found ──> [FALSIFIED (Score: exp(-γ·residual))]
│     Vectorized over Z         │    (< 0.2 ms)
└───────────────────────────────┘
                │ Residual == 0 across all points
                ▼
┌───────────────────────────────┐
│  Tier 2: Symbolic Induction   │ ── Proof Succeeded ─> [SYMBOLICALLY_VERIFIED (Score: 1.0)]
│      SymPy Base + Step        │    (< 10 ms)
└───────────────────────────────┘
                │ Unconfirmed
                ▼
    [NUMERICALLY_PLAUSIBLE]
```

1. **Tier 1 (Numerical Sieve - `tier1_numerical.py`):**
   - Evaluates LHS and RHS over vectorized test inputs $n \in \{1, 2, 3, 4, 5, 7, 10, 15, 20, 50, 100\}$.
   - If $\max |L(n) - R(n)| > 10^{-9}$, candidate is decisively falsified in $< 0.15$ ms.
   - Computes continuous residual fitness: $f = \frac{1}{|\mathcal{D}|}\sum \exp(-\gamma |L(n_i) - R(n_i)|) \in [0.0, 1.0]$.
2. **Tier 2 (Symbolic Verification - `tier2_symbolic.py`):**
   - **Algebraic Zero-Equivalence:** Checks $\text{simplify}(L(n) - R(n)) \equiv 0$.
   - **Mathematical Induction for Summations:** For candidate $\sum_{k=1}^n \text{term}(k) = R(n)$:
     - **Base Step:** Verifies $\text{term}(1) = R(1)$.
     - **Inductive Step:** Verifies $\text{simplify}(R(n) - R(n-1) - \text{term}(n)) \equiv 0$.
     - When both steps hold, the relationship is formally proven $\forall n \in \mathbb{N}_{\ge 1}$.

---

## 4. Hybrid Discrete Calculus & Rational Polynomial Solver (`evolution/rational_solver.py`)

To eliminate the combinatorial bottleneck of discovering high-order polynomial constants (e.g. finding the denominator 6 and factor $(2n+1)$ in $\sum k^2$), the engine integrates a **Discrete Calculus Finite-Difference Solver**:

```
[Target Summation: LHS = ∑ f(k)]
                │
                ▼
┌───────────────────────────────────────────────┐
│       Numerical Sampling Y = [y_0, ..., y_m]  │
└───────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────┐
│     Forward Difference Table (Δ, Δ², Δ³, ...) │
└───────────────────────────────────────────────┘
                │
         Is Δ^d constant non-zero?
        ┌───────┴───────┐
       Yes              No
        ▼               ▼
┌──────────────────┐  ┌─────────────────────────┐
│ Degree d Poly    │  │ Pure Genetic Evolutionary│
│ Interpolation    │  │ Search (Islands + Lem.) │
│ (Factored Form)  │  └─────────────────────────┘
└────────┬─────────┘
         │
         ▼
[Candidate Injected & Verified via Formal Induction]
```

1. **Finite-Difference Table:** Evaluates target values $Y[0\dots m]$ and computes forward differences:
   $$\Delta Y_n = Y_{n+1} - Y_n, \quad \Delta^{k+1} Y_n = \Delta^k Y_{n+1} - \Delta^k Y_n$$
2. **Degree Invariant Detection:** By the Fundamental Theorem of Discrete Calculus, if $\Delta^d Y$ is constant and non-zero while $\Delta^{d+1} Y = 0$, the closed form is guaranteed to be a polynomial of degree $d$.
3. **Exact Rational Interpolation:** Computes the exact polynomial via rational Lagrange interpolation and factors it over $\mathbb{Q}$.
4. **Inductive Verification:** Candidates are immediately subjected to Tier 2 algebraic difference equations and Tier 3 formal mathematical induction.

---

## 5. Multi-Island Evolutionary Core (`evolution/`)

### Grammar-Guided Genetic Programming (`grammar/`)
- A Context-Free Grammar (CFG) dictates allowable derivations, eliminating invalid syntaxes or type mismatches.
- Derivations use `ramped_half_and_half`, alternating between `grow` and `full` methods across depth levels to ensure initial structural diversity.

### Multi-Objective NSGA-II Selection (`evolution/selection.py`)
Candidates are evaluated against a 3-dimensional Pareto vector:
$$\mathbf{F}(C) = \langle f_{\text{validity}}, f_{\text{simplicity}}, f_{\text{novelty}} \rangle$$
- **Non-Dominated Sorting:** Partitions population into Pareto fronts $\mathcal{F}_1, \mathcal{F}_2, \dots$.
- **Crowding Distance:** Rewards candidates in less crowded regions of the objective space.
- **Elitism:** Preserves non-dominated frontiers across generations.

### Island Topology & Ring Migration (`evolution/island.py`, `evolution/engine.py`)
- Populations are split across multiple isolated islands with heterogeneous search regimes:
  - **Balanced Island:** 40% crossover, 35% mutation, 15% perturbation, 10% hoist.
  - **Exploration Island:** 55% subtree mutation, 25% crossover, 10% perturbation, 10% hoist.
  - **Exploitation Island:** 40% constant perturbation, 35% crossover, 15% mutation, 10% hoist.
- **Ring Migration:** Every $M$ generations (default 5), top non-dominated emigrants migrate unidirectionally ($0 \to 1 \to 2 \to 3 \to 0$), preventing genetic isolation.

---

## 6. Air-Gapped LLM Advisory Interface (`advisory/`)

The LLM is strictly decoupled from proof evaluation and candidate synthesis:

```
[Evolutionary Engine] ──(Population Telemetry)──> [Advisory Controller]
                                                         │
                                                  JSON Schema Air-Gap
                                                         ▼
[Dynamic Search Adaptation] <──(Advisory Response)── [LLM Provider]
- Operator Weights Clamped                             (Local Ollama / vLLM)
- Grammar Rule Biases
- Subtree/Template Injection
- Regime Shift
```

1. **Triggering Criteria:** The controller calls the LLM **only** when stagnation is detected ($N$ generations without validity improvement) or at scheduled epoch boundaries, respecting a cooldown interval.
2. **Strict Schema Boundary (`schema.py`):** The LLM must reply with strict JSON matching `AdvisoryResponse`. It is prohibited from claiming proof verdicts.
3. **Candidate Subtree / Template Injection:** When strategic advice identifies a missing algebraic factor (e.g. `(2*n + 1)`), it is returned in `suggested_subtrees`, parsed into AST canonical form, and seeded as immigrant individuals into the exploration islands.
4. **100% Graceful Fallback:** If the LLM is offline, times out, or returns invalid syntax, the system logs a warning and proceeds with deterministic heuristics.

---

## 7. Persistent Knowledge Base & Audit Lineage (`storage/`, `utils/`)

- Backed by SQLite (`theorems` table).
- Stores the theorem ID, canonical S-expression, human-readable formula, proof method, generation, discovery timestamp, full serialized AST dictionary (`ast_json`), and explicit dependency graph (`dependencies_json`).
- Automatically promotes verified theorems into grammar building blocks across sessions.


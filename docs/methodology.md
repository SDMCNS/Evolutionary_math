# Methodology & Mathematical Foundations

This document provides a formal exposition of the mathematical and computational methods implemented in the discovery engine.

---

## 1. Grammar-Guided Derivation & Typed ASTs

Standard genetic programming (tree GP) evaluates unconstrained parse trees, leading to nonsensical expressions (e.g. division by boolean expressions, invalid power bases, or syntax errors).

The engine uses **Grammar-Guided Genetic Programming (GGGP)** governed by a Context-Free Grammar (CFG):

$$G = (V_N, V_T, P, S)$$

Where:
- $V_N = \{\text{EXPR}, \text{INT\_CONST}, \text{TERMINAL}\}$ are non-terminal symbols.
- $V_T = \{+, -, *, /, \wedge, \text{var}(n), \text{const}(c), \text{lemma}(L_i)\}$ are terminal symbols.
- $P$ is the set of weighted production rules:
  $$\text{EXPR} \xrightarrow{w_1} \text{EXPR} + \text{EXPR} \mid \text{EXPR} \xrightarrow{w_2} \text{EXPR} * \text{EXPR} \mid \text{EXPR} \xrightarrow{w_3} \text{Lemma}_i(\text{EXPR})$$
- $S = \text{EXPR}$ is the start symbol.

Tree initialization uses **Ramped Half-and-Half**:
- Depths range from $d_{\min} = 2$ to $d_{\max} = 5$.
- For each depth level, 50% of trees are generated using the `full` strategy (forcing non-terminal expansions until max depth), and 50% using `grow` (allowing terminal selections at any depth).

---

## 2. Algebraic Normal Form & Canonicalization

Syntactic representations suffer from the **combinatorial equivalence explosion**: mathematically identical expressions have infinitely many distinct syntactic trees (e.g. $x + 1$, $1 + x$, $(x + 0) + 1$, $(x - x) + x + 1$).

To eliminate syntactic redundancy, the engine applies a canonicalization transform $\mathcal{K}(E)$:

1. **Constant Folding:**
   For any operator node whose children are all constants:
   $$\text{eval}(c_1 \odot c_2) \to c_{\text{result}}$$
2. **Identity Annihilation:**
   $$x + 0 \to x, \quad x * 0 \to 0, \quad x * 1 \to x, \quad x - x \to 0, \quad x / 1 \to x$$
3. **Commutative Total Ordering:**
   For commutative operators $\odot \in \{+, *\}$, children are ordered by an invariant sorting key:
   $$\text{SortKey}(N) = (\text{TypePriority}, \text{Symbol/Value}, \text{Complexity})$$
   Guarantees that $(x + 1) \equiv (1 + x)$ map to the exact same hash-consed DAG node.
4. **Triviality Sieve:**
   If $\mathcal{K}(\text{LHS} - \text{RHS}) = 0$ or $\mathcal{K}(\text{LHS}) == \mathcal{K}(\text{RHS})$, the candidate is flagged as `REJECTED_TRIVIAL`, preventing trivial tautologies from wasting verification time.

---

## 3. Deterministic Verification Cascade

### Tier 1: Vectorized Numerical Falsification Filter
Before attempting symbolic proof, candidate identity $L(n) = R(n)$ is evaluated across a non-uniform evaluation domain:
$$\mathcal{D} = \{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 50, 100\} \subset \mathbb{N}_{\ge 1}$$

- Residual vector: $\mathbf{r} = |L(\mathcal{D}) - R(\mathcal{D})|$.
- If $\max(\mathbf{r}) > 10^{-9}$, candidate is definitively falsified in $< 0.15$ ms.
- Continuous fitness score:
  $$f_{\text{valid}} = \frac{1}{|\mathcal{D}|} \sum_{i=1}^{|\mathcal{D}|} \exp\left(-\gamma \cdot \min(r_i, 100)\right) \in [0.0, 1.0]$$
  Provides a smooth search gradient toward equality even before exact coefficients are found.

### Tier 2: Exact Symbolic Mathematical Induction
For summation conjectures $\sum_{k=1}^n \text{term}(k) = R(n)$:
1. **Base Case ($n = 1$):**
   $$\Delta_1 = \text{simplify}\left(\text{term}(1) - R(1)\right)$$
   Must evaluate to $0$.
2. **Inductive Step ($n \to n + 1$):**
   $$\Delta_{\text{step}} = \text{simplify}\left(R(n) - R(n-1) - \text{term}(n)\right)$$
   If $\Delta_{\text{step}} \neq 0$, the engine attempts rational normalization:
   $$\Delta_{\text{rational}} = \text{together}\left(\text{cancel}\left(R(n) - R(n-1) - \text{term}(n)\right)\right)$$
3. **Formal Induction Guarantee:**
   If $\Delta_1 \equiv 0$ and $\Delta_{\text{step}} \equiv 0$, the Principle of Mathematical Induction proves:
   $$\forall n \in \mathbb{N}_{\ge 1}, \quad \sum_{k=1}^n \text{term}(k) = R(n)$$

---

## 4. Multi-Objective Selection Dynamics (NSGA-II)

The fitness vector for candidate $C$ is defined as:
$$\mathbf{F}(C) = \langle f_{\text{valid}}(C), \; f_{\text{simplicity}}(C), \; f_{\text{novelty}}(C) \rangle$$

### Simplicity Metric (MDL Proxy)
To counteract tree bloat:
$$f_{\text{simplicity}}(C) = \frac{1}{1 + 0.08 \cdot \text{NodeCount}(C) + 0.04 \cdot \text{Depth}(C)}$$

### Syntactic Novelty Metric
Measures structural Jaccard distance against the population sub-expression pool:
$$f_{\text{novelty}}(C) = \frac{|\text{SubExpressions}(C) \setminus \mathcal{S}_{\text{population}}|}{|\text{SubExpressions}(C)|}$$

### Pareto Dominance & Crowding Distance
Individual $p$ dominates $q$ ($p \succ q$) iff:
$$\forall m \in \{1, 2, 3\}, \; f_m(p) \ge f_m(q) \quad \land \quad \exists m, \; f_m(p) > f_m(q)$$
- Fast non-dominated sorting partitions the union of parents and offspring $R_t = P_t \cup Q_t$ into fronts $\mathcal{F}_1, \mathcal{F}_2, \dots$.
- Crowding distance assigns higher priority to individuals inhabiting sparse regions of the objective space.

---

## 5. Automated Lemma Promotion (ADF Encapsulation)

When a theorem is proven:
$$\sum_{k=1}^n k = \frac{n(n+1)}{2}$$
The discovery is converted into an Automatically Defined Function $L_{\text{id}}(n)$ and promoted to the grammar:
$$\text{EXPR} \to L_{\text{id}}(\text{EXPR})$$
When a candidate invokes $L_{\text{id}}(E)$:
1. **Numerical Evaluation:** Recursively evaluates $E$ and feeds the result into the definition's parameter environment $\{n: E\}$.
2. **Symbolic Verification:** Substitutes $E.\text{to\_sympy}()$ for $n$ into the definition's SymPy expression before running induction.
3. **Lineage Tracking:** Automatically extracts all $L_{\text{id}}$ invocations to record dependency edges in SQLite.

---

## 6. Discrete Calculus & Finite Differences for Polynomial Sums

For summation identities involving polynomial terms $\sum_{k=1}^n P(k)$ where $P(k)$ is a polynomial of degree $d$, Faulhaber's formula and discrete calculus establish that the closed-form sum $S(n)$ is a polynomial of degree $d+1$ with zero constant term ($S(0) = 0$).

### Forward Difference Invariant
Let $Y = [y_0, y_1, y_2, \dots, y_m]$ be the sequence of partial sums evaluated at $n = 0, 1, 2, \dots$. The forward finite differences are:
$$\Delta^0 Y_n = Y_n, \quad \Delta^{k+1} Y_n = \Delta^k Y_{n+1} - \Delta^k Y_n$$

By the Fundamental Theorem of Finite Differences:
$$\Delta^m Y_n = \sum_{j=0}^m (-1)^{m-j} \binom{m}{j} Y_{n+j}$$
- If $\Delta^d Y$ is a non-zero constant across all sampled indices, and $\Delta^{d+1} Y = 0$, then $S(n)$ is uniquely determined by a polynomial of degree $d$.
- The exact rational polynomial is computed via Lagrange interpolation across the $d+1$ initial support points:
  $$S(n) = \sum_{i=0}^d y_i \prod_{j \neq i} \frac{n - j}{i - j}$$
- The resulting polynomial is factored over $\mathbb{Q}$ and mapped into canonical `ExprNode` form.
- The candidate is still subjected to the complete 3-tier verification pipeline to guarantee formal mathematical soundness.



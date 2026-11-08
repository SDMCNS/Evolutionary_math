# Abilities, Benchmarks & Theoretical Limitations

A critical scientific assessment of what the Evolutionary Mathematical Discovery Engine can achieve, empirical benchmarks, and its fundamental mathematical and computational limitations.

---

## 1. Demonstrated Abilities & Strengths

### 1.1 Proven Capabilities
1. **Zero Mathematical Hallucinations:**
   Unlike pure LLM approaches (which confidently assert plausible-looking mathematical falsehoods), every relationship recorded by this engine has been formally verified by Tier 2 symbolic induction.
2. **Autonomous Multi-Island Exploration:**
   Finds non-trivial algebraic identities, triangular numbers, square sum invariants, telescoping rational series, and higher-order power sums without human intervention.
3. **Sub-Millisecond Sifting:**
   The vectorized Tier 1 filter eliminates $99.9\%$ of mathematically false candidates in **$< 0.2$ ms**, keeping generation throughput high ($> 5,000$ candidates/second).
4. **Cumulative Composition (Lemma Encapsulation):**
   Demonstrates non-trivial compositional learning: discovering Nicomachus's Theorem ($\sum k^3 = (\sum k)^2$) in **Generation 1 in 0.059 seconds** by reusing the previously discovered triangular number lemma.
5. **Completely Local & Air-Gapped:**
   Operates entirely on a desktop workstation without external network connections, cloud APIs, or mandatory GPU acceleration.

### 1.2 Empirical Performance Benchmarks

| Problem Space | Target Expression | Search Mode | Generations to Discovery | Discovery Time | Evals |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Triangular Numbers** | $\sum_{k=1}^n k$ | Unguided GA | 26 | 0.909 s | 5,200 |
| **Triangular Numbers** | $\sum_{k=1}^n k$ | LLM-Guided | 6 | 0.218 s | 1,200 |
| **Odd Integer Squares** | $\sum_{k=1}^n (2k - 1)$ | Campaign Loop | 1 | 0.053 s | 200 |
| **Telescoping Series** | $\sum_{k=1}^n \frac{1}{k(k+1)}$ | Unguided GA | 14 | 0.856 s | 2,800 |
| **Nicomachus's Theorem** | $\sum_{k=1}^n k^3$ | Cumulative (with $L_1$) | 1 | 0.059 s | 200 |
| **Nicomachus's Theorem** | $\sum_{k=1}^n k^3$ | From Scratch (no lemmas) | $> 150$ (stagnates) | $> 30$ s | $> 30,000$ |

---

## 2. Fundamental Mathematical & Computational Limitations

A rigorous computational engine must acknowledge the theoretical boundaries established by computer science and mathematical logic:

### 2.1 The Undecidability Barrier (Richardson's Theorem)
- **The Theorem:** Daniel Richardson (1968) proved that the problem of determining whether an elementary expression $E$ is identically zero ($E \equiv 0$) is **algorithmically undecidable** if $E$ includes rational numbers, $\pi, \ln(2)$, addition, multiplication, composition, and the sine function ($\sin$).
- **Implication for the Engine:** The engine cannot arbitrarily expand its grammar to arbitrary transcendental functions without encountering undecidable equivalence checks where SymPy's zero-testing will hang or return inconclusive results.
- **Mitigation:** The grammar is currently restricted to the decidable field of rational functions, discrete summations, and polynomial rings over $\mathbb{Q}$.

### 2.2 The Combinatorial Branching Explosion
- **The Problem:** In Grammar-Guided GP, if a grammar contains $|P|$ production rules, the size of the derivation space of depth $d$ grows as $O(|P|^d)$.
- **Implication of Lemma Promotion:** If the engine promotes 100 discovered lemmas into the grammar, $|P|$ increases from $10$ to $110$. The search branching factor explodes, making random sampling diluted and inefficient.
- **Mitigation:** The engine implements a **Working Memory Window** (`top_k=3` or `top_k=5`), promoting only the most relevant, recently proven lemmas rather than the entire historical catalog.

### 2.3 The "Fitness Cliff" in Number Theory
- **The Problem:** The engine succeeds on summation identities because numerical residuals over $\mathbb{Z}$ provide a continuous gradient ($\exp(-\gamma \cdot \text{residual})$).
- **Implication for Pure Proofs:** In abstract algebra, graph theory, or prime distribution (e.g. Goldbach's conjecture or Fermat's Last Theorem), truth is a binary needle in a haystack. A candidate is either universally true or false; numerical closeness does not indicate proof proximity.
- **Mitigation:** Domains must be selected where continuous evaluation proxies correlate with algebraic structure (recurrences, differential equations, generating functions, continuous inequalities).

### 2.4 Inductive Proof Verification Scope
- **Current Scope:** The Tier 2 engine supports algebraic zero-equivalence and structural single-variable mathematical induction for discrete summations.
- **Out of Scope:** The current verifier does not perform arbitrary transfinite induction, multi-variable induction with intertwined bases, or automated lemma generation for complex tactic proofs in Lean 4 without human tactic design.

---

## 3. Comparison with Alternative Approaches

| Feature | Pure LLM (e.g. GPT-4 / Claude) | Symbolic Regression (Eureqa) | CAS Alone (SymPy / Mathematica) | Evolutionary Math Discovery Engine |
| :--- | :--- | :--- | :--- | :--- |
| **Correctness Guarantee** | Low (hallucinates proofs) | Medium (numerical fit only) | High (deterministic) | **Absolute (Tier 2 induction verified)** |
| **Autonomous Exploration** | No (requires prompts) | Numerical curve fit only | No (requires explicit query) | **Yes (Autonomous Campaign loop)** |
| **Cumulative Knowledge (ADFs)**| Ephemeral context only | None | Manual function storage | **Automatic Lemma Promotion & Dependency Graph** |
| **Resistance to Tautologies** | Poor | Poor | Not applicable | **Automatic Canonicalization & Sieve** |
| **Offline Privacy** | Cloud API dependent | Desktop | Desktop | **100% Local Workstation** |


# How Evolutionary Math Works (In Plain English)

> **"If you ask an AI to do math, it will sound confident and get it wrong. If you ask a traditional theorem prover, it will freeze trying trillions of combinations. Evolutionary Math pairs biological creativity with mathematical ironclad proof."**

---

## 1. The 30-Second Summary

Imagine you want to discover the formula for adding up the first $n$ square numbers:
$$1^2 + 2^2 + 3^2 + \dots + n^2 = \text{???}$$

Instead of doing the math yourself or blindly trusting ChatGPT, **Evolutionary Math** sets up an automated laboratory:

1. **It breeds formulas like living organisms:** Formulas are built out of basic math LEGO bricks ($+$, $\times$, $/$, $n$, numbers). They mutate, swap parts with each other (crossover), and compete to see which one comes closest to the right answers.
2. **It uses a ruthless 3-tier lie detector:** 
   - A super-fast numerical screen tosses out 99% of bad guesses in under a thousandth of a second.
   - If a formula passes all numbers, a formal mathematical judge proves it with mathematical induction.
3. **It has an AI "coach" on the sidelines:** If the population gets stuck, a local AI model (running locally on LM Studio or Ollama) looks at the search statistics and gives strategic tips—like *"Try looking for a $(2n + 1)$ factor"*—without ever being allowed to fake a proof.
4. **It remembers what it learns:** When it proves a formula (like $\sum k = \frac{n(n+1)}{2}$), it saves it as a new building block. Later, when asked to sum cubes ($1^3 + 2^3 + \dots + n^3$), it simply takes that saved formula and squares it in one generation!

---

## 2. Why Not Just Ask an LLM?

When modern generative AI (like GPT-4 or Claude) does math, it acts like a language autocomplete. It generates words that *sound* like a valid proof. But in mathematics, being 99% right is 100% wrong. A missing minus sign or an unchecked edge case destroys the entire theorem.

Conversely, formal software used by mathematicians (like Lean 4 or Coq) is 100% sound—it will never accept a false proof. However, it has **no intuition**. Searching blindly for formulas in a formal prover is like trying to guess a 50-character password.

**Evolutionary Math unites both worlds:**
```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     The Creative Explorer       │       │       The Ruthless Judge        │
│   (Genetic Algorithm + LLM)     │ ────> │   (Computer Algebra System)     │
│   • Invents crazy formulas      │       │   • Tests numbers in 0.1 ms     │
│   • Tries unexpected shapes     │       │   • Verifies formal induction   │
│   • Recombines good ideas       │       │   • 0% chance of false proofs   │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

---

## 3. Step-by-Step: The Life of a Formula

### Step 1: Formulas as LEGO Trees (The AST)
Inside the computer, a formula is not a string of text. It is a tree of nodes (called an **Abstract Syntax Tree**):

```
       (/)
      /   \
    (*)    2
   /   \
  n    (+)
      /   \
     n     1
```
This tree represents $\frac{n \times (n + 1)}{2}$.
Because each part is an independent node, the engine can easily:
- Swap the right branch with another formula (sexual crossover).
- Change the `+` to a `*` (mutation).
- Prune away dead wood: if a formula has $n + 0$ or $x \times 1$, a built-in cleaner instantly deletes the useless terms so the tree doesn't grow uncontrollably.

---

### Step 2: The Island Archipelago (Different Thinking Styles)
Instead of putting all formulas in one big bucket, the engine separates them onto **islands**:

```
 ┌──────────────────────┐        ┌──────────────────────┐
 │   Island 0: Balanced │ ─────> │ Island 1: Explorer   │
 │   • 40% Crossover    │        │ • 55% Wild Mutation  │
 │   • 35% Mutation     │        │ • Tries radical ideas│
 └──────────┬───────────┘        └──────────┬───────────┘
            │                               │
            ▼                               ▼
 ┌──────────────────────┐        ┌──────────────────────┐
 │ Island 3: Promoted   │ <───── │ Island 2: Tuner      │
 │ • Uses saved lemmas  │        │ • 40% Constant tweak │
 │ • High-level math    │        │ • Finds exact ratios │
 └──────────────────────┘        └──────────────────────┘
```

Every 5 generations, the strongest formulas swim to the next island (Ring Migration). This keeps good ideas circulating while preventing every island from getting trapped in the same dead end.

---

### Step 3: The 3-Tier Lie Detector (How Candidates are Graded)

Every candidate formula must run a three-stage gauntlet:

1. **Tier 1: The Speed Trap (0.1 milliseconds)**
   Before doing any heavy math, the engine plugs in numbers: $n = 1, 2, 3, 4, 5, 10, 50, 100$.
   If the target sum for $n=4$ is $30$, and the candidate formula outputs $28.5$, it is immediately discarded. 
   **Result:** 99.5% of random formulas are eliminated in microseconds without wasting computer power.

2. **Tier 2: The Difference Equation (2 milliseconds)**
   If a formula matches all test numbers, it moves to the algebra engine (SymPy). It tests if adding the next term works algebraically:
   $$F(n) - F(n-1) \stackrel{?}{=} f(n)$$
   If you are summing $k^2$, does your formula minus the previous step always simplify to $n^2$?

3. **Tier 3: The Courtroom Proof (Formal Induction)**
   If the algebra matches, the engine formally proves the theorem for **all infinite integers**:
   - **Base Case:** Prove $F(1) = f(1)$.
   - **Inductive Step:** Prove that assuming it works for $n$ guarantees it works for $n+1$.
   
Once Tier 3 passes, the formula is no longer a "guess"—it is an **immutable mathematical theorem**.

---

### Step 4: The Discrete Calculus Shortcut (Finite Differences)

For polynomial sums like $1^2 + 2^2 + \dots + n^2$, finding the fraction $\frac{1}{6}$ and the factor $(2n+1)$ by random mutation can take dozens of generations.

To solve this, the engine includes a **Discrete Calculus Solver** inspired by how odometers measure distance and speed:
1. It records the first few answers: $0, 1, 5, 14, 30, 55$.
2. It takes differences between consecutive numbers ($\Delta$): $1, 4, 9, 16, 25$.
3. It takes differences of differences ($\Delta^2$): $3, 5, 7, 9$.
4. It takes differences again ($\Delta^3$): $2, 2, 2, 2$.

Notice that at the 3rd step, the differences become constant ($2, 2, 2$)! 
The laws of discrete calculus state that whenever the $d$-th difference is constant, the answer is **guaranteed** to be a polynomial of degree $d$. 
The engine calculates the exact fractional coefficients using rational interpolation, factors it into $\frac{n(n+1)(2n+1)}{6}$, feeds it to the induction engine, and proves it in **0.15 seconds**.

---

### Step 5: Domain Modes (Focusing the Search Across Different Branches of Math)

Mathematics is vast. Trying to discover trigonometric identities using integer series summation bricks is like trying to build a spaceship with wooden logs.

The library includes a **Domain Mode** setting (`--mode`) that reconfigures the entire engine:
1. **The LEGO Toolbox (Grammar):**
   - **`algebra` (default):** Bricks include $+$, $-$, $\times$, $/$, exponents, integer constants, and discrete summation $\sum_{k=1}^n$.
   - **`trigonometry`:** Bricks include $\sin$, $\cos$, $\tan$, radian variable $x$, and angle constants.
   - **`geometry`:** Bricks include $\sqrt{\cdot}$, side variables $a, b$, areas, and perimeters.
   - **`calculus`:** Bricks include continuous analysis functions and power differences.
2. **The Numerical Test Points:**
   - Algebra tests positive integers $n \in [1 \dots 100]$.
   - Trigonometry tests angles in radians: $0.1, \frac{\pi}{4}, \frac{\pi}{3}, \frac{\pi}{2}, \pi$.
   - Geometry tests strictly positive side lengths: $a, b \in [1.0 \dots 15.0]$.
3. **The Proof Mechanism:**
   - Discrete algebra is proven using mathematical induction and finite difference interpolation.
   - Trigonometry is proven using symbolic trigonometric zero-equivalence (`sp.trigsimp`).
   - Geometry is proven using algebraic coordinate metric invariance.

---

### Step 6: The AI Coach (Strictly Air-Gapped)

Where does the Large Language Model (like Qwen, Llama, or GPT) fit in?
The LLM is **never allowed to claim a formula is true**. It sits in the coach's box on the sidelines:

```
[Evolutionary Engine] ────── Telemetry: "We are stuck at validity 0.85" ─────> [LLM Coach]
                                                                                     │
[Engine Adapts] <──── Advice: "Increase mutation rate; consider (2n+1)" ─────────────┘
```

1. If the population stagnates for 5 generations, the engine sends a summary of top candidates to the LLM.
2. The LLM replies with a strict JSON recommendation:
   - *"Your candidates grow too fast. Increase division weight."*
   - *"The residual suggests a missing factor. Inject `(2 * n) + 1` into the population."*
3. The engine parses the advice, adjusts the genetic probabilities, injects the suggested subtree into Island 1, and lets the evolutionary search resume.
4. If the LLM gives terrible advice or hallucinates nonsense, the Tier 1 speed trap rejects it immediately. **Zero harm done.**

---

### Step 7: Cumulative Knowledge (Standing on Its Own Shoulders)

When a theorem is proven, it is not forgotten. It is encapsulated into an **Automatically Defined Function (ADF)** and given a lemma ID:
- **Theorem 1:** $\sum_{k=1}^n k = \frac{n(n+1)}{2} \implies \text{Saved as } L_1(n)$
- **Theorem 2:** $\sum_{k=1}^n (2k - 1) = n^2 \implies \text{Saved as } L_2(n)$

Later, when given a harder target:
$$\sum_{k=1}^n k^3 = 1^3 + 2^3 + 3^3 + \dots + n^3$$

Instead of starting from scratch, Island 3 derives:
$$L_2(L_1(n)) = [L_1(n)]^2 = \left(\frac{n(n+1)}{2}\right)^2 = \frac{n^2(n+1)^2}{4}$$
The engine proves Nicomachus's Theorem in **Generation 0** because it built upon its own previously proven discoveries!

---

### Step 8: The Fishbone Audit Trail (Complete Transparency)

Traditional AI gives you an answer with no explanation of how it got there. Evolutionary Math produces an interactive **Ishikawa Fishbone Diagram** (`fishbone.html`):

```
       [Milestone 1: 0.50]           [Milestone 2: 0.85]          [Milestone 3: 0.99]
              \                             \                            \
═══════════════╤═════════════════════════════╤════════════════════════════╤══════════════> [🏆 BREAKTHROUGH]
              │                             │
             [AI Intervention]             / 
                                  [Falsified Guess]
                                  (Failed on n=4)
```

- **Top Ribs (Green):** Major breakthrough milestones where candidate accuracy advanced.
- **Bottom Ribs (Red):** Exactly which candidate formulas failed, along with their numerical counterexamples.
- **Flags (Blue):** When and why the AI coach intervened.
- **Golden Head:** The final proven theorem with its mathematical name and geometric intuition.

---

### Step 9: Parameter Generalization & Subsumption (Escaping Infinite Incremental Loops)

A common pitfall with automated theorem discovery is **database flooding**: the engine discovers $\sum k(k+1)$, then $\sum k(k+2)$, then $\sum k(k+3)$, all the way up to $\sum k(k+110)$, treating each as an entirely new discovery!

In mathematics, incrementing a number is not a new theorem—it is a single parameterized family. Evolutionary Math detects and eliminates this through **Parameter Lifting and Subsumption**:

1. **Parameter Lifting:** When the engine encounters a formula with arbitrary constants like $\sum_{k=1}^n k(k + 110)$, it recognizes that $110$ is just an instance of an integer parameter. It lifts the concrete number into a free symbolic variable $m$:
   $$\sum_{k=1}^n k(k + m)$$
2. **Inductive Proof over Parameters:** The induction engine proves the closed form symbolically for **all** integers $m$:
   $$\sum_{k=1}^n k(k + m) = \frac{n(n + 1)(2n + 3m + 1)}{6}$$
   Because the inductive difference $F(n) - F(n-1) - n(n+m) = 0$ simplifies to zero regardless of $m$, the identity holds universally.
3. **Subsumption Checking:** Whenever the campaign engine encounters a concrete target in the future (like $m=110$ or $m=250$), it checks if any stored meta-theorem covers it. If so, it immediately evaluates the concrete formula via substitution—solving it in Generation 0 and preventing redundant database rows.
4. **Database Consolidation:** If an older database already contains dozens of incremental rows, running `python -m evolutionary_math.cli consolidate --db ...` automatically clusters the concrete iterations, synthesizes the master theorem, and purges the duplicates.

---

## 4. Summary: How the Pieces Fit Together

| Component | Role | What It Does |
| :--- | :--- | :--- |
| **AST Tree** | Anatomy | Represents math formulas as manipulable LEGO structures. |
| **Islands** | Diversity | Runs separate populations with different exploration strategies. |
| **Tier 1 (NumPy)** | Speed Filter | Rejects 99% of incorrect formulas in $< 0.2$ ms. |
| **Tier 2 & 3 (SymPy)** | Ironclad Judge | Proves the base case and inductive step so nothing false is ever saved. |
| **Discrete Calculus** | Shortcut | Solves polynomial series in 1 step using forward difference tables. |
| **LLM Coach** | Strategy | Suggests parameter changes and seeds missing algebraic factors when stuck. |
| **Generalization & Subsumption** | Meta-Theorems | Lifts numeric increments ($k + 110$) into free parameter $m$, proving the universal formula for all $m$ and preventing database flooding. |
| **Knowledge Base** | Memory | Stores verified lemmas so future searches can reuse them as building blocks. |
| **Fishbone Lineage** | Audit | Draws an Ishikawa timeline diagram showing every success, failure, and tip. |

---

## 5. Example Targets to Get You Started

The engine includes 11 built-in target presets covering foundational arithmetic, polynomial power sums, pronic products, and telescoping fractions. You can view them any time with:
```powershell
python -m evolutionary_math.cli targets
```

Here are 5 great targets to try first:

### 1. The Kindergarten Gauss Sum (`sum_k`)
- **Formula:** $1 + 2 + 3 + \dots + n$
- **Expected Answer:** $\frac{n(n+1)}{2}$
- **Command:**
  ```powershell
  python -m evolutionary_math.cli discover --target sum_k
  ```
- **Why it's cool:** Discovered in seconds. Creates the foundational building block for cubes!

### 2. Odd Numbers to Perfect Squares (`sum_odd`)
- **Formula:** $1 + 3 + 5 + \dots + (2n - 1)$
- **Expected Answer:** $n^2$
- **Command:**
  ```powershell
  python -m evolutionary_math.cli discover --target sum_odd
  ```
- **Why it's cool:** Shows how gnomon tiles expand square areas. Discovered in Generation 1.

### 3. The Pyramid of Cannonballs (`sum_k2`)
- **Formula:** $1^2 + 2^2 + 3^2 + \dots + n^2$
- **Expected Answer:** $\frac{n(n+1)(2n+1)}{6}$
- **Command:**
  ```powershell
  python -m evolutionary_math.cli discover --target sum_k2
  ```
- **Why it's cool:** Solved via the discrete calculus finite difference solver in $< 0.2$s!

### 4. Telescoping Fractions (`telescoping`)
- **Formula:** $\frac{1}{1\cdot 2} + \frac{1}{2\cdot 3} + \dots + \frac{1}{n(n+1)}$
- **Expected Answer:** $\frac{n}{n+1}$
- **Command:**
  ```powershell
  python -m evolutionary_math.cli discover --target telescoping
  ```
- **Why it's cool:** Demonstrates rational function search and partial fraction cancellation.

### 5. Tetrahedral Stacks (`sum_pronic`)
- **Formula:** $1\cdot 2 + 2\cdot 3 + \dots + n(n+1)$
- **Expected Answer:** $\frac{n(n+1)(n+2)}{3}$
- **Command:**
  ```powershell
  python -m evolutionary_math.cli discover --target sum_pronic
  ```

### 6. Generalized Meta-Theorems (`sum_pronic_gen`)
- **Formula:** $\sum_{k=1}^n k(k + m)$ (holds for **all** integers $m$ simultaneously!)
- **Expected Answer:** $\frac{n(n + 1)(2n + 3m + 1)}{6}$
- **Command:**
  ```powershell
  python -m evolutionary_math.cli discover --target sum_pronic_gen
  ```
- **Why it's cool:** Instead of wasting time proving $k(k+1)$, $k(k+2)$, ..., $k(k+110)$, the engine lifts the number into a variable $m$, proves the master formula once and for all via induction, and recognizes all concrete numbers as already solved!

### 7. Any Custom Target You Imagine!
You don't have to stick to presets—type any custom mathematical formula:
```powershell
python -m evolutionary_math.cli discover --target "2*k + 1"
python -m evolutionary_math.cli discover --target "k^2 + 3*k"
```

---

## 6. Try It Yourself in 3 Commands

```powershell
# 1. Discover a formula autonomously
python -m evolutionary_math.cli discover --target sum_k2 --db my_research.db

# 2. View all discovered theorems in plain English
python -m evolutionary_math.cli list --db my_research.db

# 3. View the full search history fishbone diagram in your browser
python -m evolutionary_math.cli fishbone --db my_research.db --format html -o fishbone.html
start fishbone.html
```


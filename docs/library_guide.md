# Python Library Developer Guide

This guide explains how to use `evolutionary_math` as a Python library in your own research scripts, applications, and computational experiments.

---

## 1. Installation

Install the package in editable development mode from the workspace root:

```powershell
cd c:\Projects\libraries\evolutionary_math
pip install -e .
```

Verify your installation:
```python
import evolutionary_math
print(evolutionary_math.__version__)  # Output: 0.1.0
```

---

## 2. Core API Reference

### 2.1 Building Mathematical Expressions (`core.ast`)

Expressions must be constructed using `expr_factory` to guarantee maximal DAG sub-expression sharing and hash-consing:

```python
from evolutionary_math.core.ast import expr_factory

# 1. Terminals
n = expr_factory.variable("n")
k = expr_factory.variable("k")
one = expr_factory.constant(1)
two = expr_factory.constant(2)

# 2. Binary Operators (+, -, *, /, ^)
n_plus_1 = expr_factory.op("+", n, one)
prod = expr_factory.op("*", n, n_plus_1)
triangular = expr_factory.op("/", prod, two)

# 3. Summation Operator: sum_{k=1}^n (term)
# Note: Lower bound is 1, upper bound is the second argument, index variable is 'k'
sum_k = expr_factory.op("sum", k, n)

# 4. Numerical Evaluation
print("Triangular(10) =", triangular.eval_numerical({"n": 10}))  # 55.0
```

### 2.2 Numerical & Symbolic Verification (`evaluation.pipeline`)

To test or verify any mathematical identity:

```python
from evolutionary_math.evaluation.pipeline import EvaluationPipeline, EvaluationStatus

pipeline = EvaluationPipeline()

# Test candidate: sum_{k=1}^n k == n*(n+1)/2
result = pipeline.evaluate(sum_k, triangular)

print("Status:      ", result.status)         # EvaluationStatus.SYMBOLICALLY_VERIFIED
print("Verified:    ", result.is_verified)     # True
print("Proof Method:", result.proof_method)    # mathematical_induction
print("Runtime:     ", result.total_runtime_ms, "ms")
```

### 2.3 Running an Evolutionary Search (`evolution.engine`)

To discover a closed-form formula for a given target:

```python
from evolutionary_math.evolution.engine import EvolutionEngine
from evolutionary_math.storage.knowledge_base import KnowledgeBase

kb = KnowledgeBase("my_research.db")

engine = EvolutionEngine(
    num_islands=4,
    island_population_size=50,
    migration_interval=5,
    knowledge_base=kb,
    auto_promote_lemmas=True,
    seed=42,
)

# Run discovery
target = expr_factory.op("sum", k, n)
run_result = engine.run(target_lhs=target, max_generations=50)

if run_result.success:
    th = run_result.discovered_theorem
    print(f"Discovered: {th.target_str} = {th.discovery_str}")
    print(f"Proven via: {th.proof_method}")
```

### 2.4 Enabling LLM Advisory Guidance (`advisory`)

To attach an air-gapped LLM adviser to the evolutionary loop:

```python
from evolutionary_math.advisory.controller import AdvisoryController
from evolutionary_math.advisory.client import OpenAICompatibleAdvisoryClient, MockAdvisoryClient

# Option A: Connect to local Ollama / vLLM / LM Studio
llm_client = OpenAICompatibleAdvisoryClient(
    base_url="http://localhost:1234/v1",
    model="qwen/qwen3.5-9b",
)

# Option B: Use the offline deterministic mock adviser
# llm_client = MockAdvisoryClient(confidence=0.92)

adviser = AdvisoryController(
    client=llm_client,
    stagnation_threshold=6,  # Trigger after 6 stagnant generations
    cooldown_generations=3,  # Prevent rapid consecutive calls
)

# Pass adviser to the engine
engine = EvolutionEngine(
    knowledge_base=kb,
    advisory_controller=adviser,
)
```

### 2.5 Running an Autonomous Discovery Campaign (`campaign.runner`)

To set the engine loose on an evolving stream of problem spaces:

```python
from evolutionary_math.campaign.runner import AutonomousDiscoveryCampaign
from evolutionary_math.campaign.agenda import ProblemSpaceAgenda

campaign = AutonomousDiscoveryCampaign(
    knowledge_base=kb,
    num_islands=4,
    island_population_size=40,
    generations_per_target=45,
    seed=101,
)

def on_breakthrough(theorem, run_result):
    print(f"🏆 Breakthrough [{theorem.id}]: {theorem.target_str} = {theorem.discovery_str}")

theorems = campaign.run(max_theorems=5, on_breakthrough=on_breakthrough)
```

### 2.6 Plain-English Mathematical Exposition (`StoredTheorem.explanation`)

Whenever an identity is verified and stored in the knowledge base, an intuitive plain-English conceptual explanation is automatically generated and attached to the theorem:

```python
if run_result.success:
    th = run_result.discovered_theorem
    print(f"Discovered: {th.target_str} = {th.discovery_str}")
    print(f"Proven via: {th.proof_method}")
    print(f"Intuition:  {th.explanation}")
    # Output:
    # Intuition: This is the classical triangular number formula: 1 + 2 + ... + n = n(n+1)/2. 
    # Visually, pairing two identical step-pyramids of dots creates an n × (n+1) rectangle of n(n+1) dots; 
    # dividing this rectangle in half gives the exact sum of the first n positive integers.
```

If a connected local LLM is available, it queries the model with strict formatting to generate geometric and algebraic intuition. If offline or in fallback mode, `MockAdvisoryClient` provides deterministic historical and geometric explanations.


---

## 3. Storage & Theorem Repository API (`storage.knowledge_base`)

Query, inspect, and retrieve theorems stored in SQLite:

```python
from evolutionary_math.storage.knowledge_base import KnowledgeBase

kb = KnowledgeBase("my_research.db")

# Retrieve all stored theorems
all_theorems = kb.get_all_theorems()
for t in all_theorems:
    print(f"ID: {t.id} | Formula: {t.discovery_str} | Dependencies: {t.dependency_ids}")

# Check if an expression is already known
is_already_proven = kb.is_known(triangular)
```

---

## 4. Visualization & Formatting Utilities (`utils`)

```python
from evolutionary_math.utils.formatting import to_latex, to_ascii_tree, export_knowledge_base_mermaid
from evolutionary_math.utils.lean_exporter import generate_lean4_proof_file

# 1. LaTeX output
print(to_latex(triangular))
# Output: \frac{n \cdot \left(1 + n\right)}{2}

# 2. ASCII Tree visualization
print(to_ascii_tree(triangular))

# 3. Mermaid Dependency Diagram
mermaid_code = export_knowledge_base_mermaid(kb)

# 4. Lean 4 Formal Proof Script Export
lean4_code = generate_lean4_proof_file(all_theorems)
with open("Theorems.lean", "w", encoding="utf-8") as f:
    f.write(lean4_code)
```


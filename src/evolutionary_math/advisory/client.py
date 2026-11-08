"""Advisory client interface, mock client, and OpenAI-compatible local LLM client."""

import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional
import urllib.request
import urllib.error

from evolutionary_math.advisory.schema import (
    AdvisoryRequest,
    AdvisoryResponse,
    OperatorWeights,
    GrammarBias,
)

logger = logging.getLogger(__name__)


class BaseAdvisoryClient(ABC):
    """Abstract client interface for the evolutionary advisory loop and theorem exposition."""

    @abstractmethod
    def request_advice(self, request: AdvisoryRequest) -> Optional[AdvisoryResponse]:
        """Request strategic evolutionary guidance. Returns None if client is offline or fails."""
        pass

    @abstractmethod
    def explain_discovery(
        self,
        target_str: str,
        discovery_str: str,
        latex_str: str,
        proof_method: str,
        dependencies: Optional[list] = None,
    ) -> str:
        """Generate a plain-English intuitive explanation of a verified discovery."""
        pass


class MockAdvisoryClient(BaseAdvisoryClient):
    """Deterministic, rule-based advisory client for reproducible tests and offline runs."""

    def __init__(self, confidence: float = 0.90):
        self.confidence = confidence

    def request_advice(self, request: AdvisoryRequest) -> Optional[AdvisoryResponse]:
        stagnation = request.stagnation_counter
        top_val = request.population_metrics.get("top_validity", 0.0)

        # Strategic heuristic diagnosis
        if stagnation >= 5 and top_val > 0.80:
            # High validity but stagnant: needs constant tuning or simplification to close the gap
            regime = "EXPLOITATION"
            weights = OperatorWeights(
                crossover=0.20,
                subtree_mutation=0.15,
                constant_perturbation=0.50,
                hoist=0.15,
            )
            biases = [
                GrammarBias(head="EXPR", symbol="*", multiplier=1.5),
                GrammarBias(head="EXPR", symbol="/", multiplier=1.5),
            ]
            diagnosis = "Population is close to target closed form. Emphasizing constant perturbation to discover exact polynomial coefficients."
            suggested = ["(2 * n) + 1", "n * (n + 1)"]
        elif stagnation >= 5 and top_val <= 0.80:
            # Low validity and stagnant: trapped in local minimum, needs exploration
            regime = "EXPLORATION"
            weights = OperatorWeights(
                crossover=0.25,
                subtree_mutation=0.55,
                constant_perturbation=0.10,
                hoist=0.10,
            )
            biases = [
                GrammarBias(head="EXPR", symbol="n", multiplier=2.0),
                GrammarBias(head="EXPR", symbol="+", multiplier=1.8),
                GrammarBias(head="EXPR", symbol="*", multiplier=1.5),
            ]
            diagnosis = "Population stuck in suboptimal basin. Injecting structural diversity via increased subtree mutation and linear factor bias."
            suggested = ["(2 * n) + 1"]
        else:
            regime = "BALANCED"
            weights = OperatorWeights(
                crossover=0.40,
                subtree_mutation=0.35,
                constant_perturbation=0.15,
                hoist=0.10,
            )
            biases = []
            diagnosis = "Search progressing normally. Maintaining balanced evolutionary operator distribution."
            suggested = []

        return AdvisoryResponse(
            diagnosis=diagnosis,
            regime_selection=regime,
            operator_weight_adjustments=weights,
            grammar_biases=biases,
            pruning_recommendations=["Prune candidates with node count > 25"],
            suggested_subtrees=suggested,
            confidence=self.confidence,
        )

    def explain_discovery(
        self,
        target_str: str,
        discovery_str: str,
        latex_str: str,
        proof_method: str,
        dependencies: Optional[list] = None,
    ) -> str:
        """Generate intuitive, plain-English explanations for mathematical discoveries."""
        from evolutionary_math.utils.formatting import format_clean_formula
        deps_note = f" by composing previous lemmas ({', '.join(dependencies)})" if dependencies else ""
        clean_f = format_clean_formula(discovery_str)

        # 1. Fractions / Telescoping series (prioritized to avoid subterm collision)
        if "1 /" in target_str or "1/" in target_str:
            if "2 * k" in target_str or "2k" in target_str:
                return (
                    f"This is a telescoping rational series with odd factor denominators: "
                    f"1/(1·3) + 1/(3·5) + ... + 1/((2n-1)(2n+1)) = {clean_f}{deps_note}. "
                    f"Using partial fractions, each term splits into 1/2·(1/(2k-1) - 1/(2k+1)). "
                    f"When summed, all intermediate terms cancel out in pairs, leaving only 1/2·(1 - 1/(2n+1)) = {clean_f}."
                )
            elif "(k + 1) * (k + 2)" in target_str or "((k + 1) * (k + 2))" in target_str or "k + 2" in target_str:
                return (
                    f"This is a shifted telescoping series: 1/(2·3) + 1/(3·4) + ... + 1/((n+1)(n+2)) = {clean_f}{deps_note}. "
                    f"Decomposing each term via partial fractions into (1/(k+1) - 1/(k+2)) causes all interior terms to cancel out, "
                    f"leaving only the boundary terms 1/2 - 1/(n+2) = {clean_f}."
                )
            elif "1 / (k * (k + 1))" in target_str or "(k * (k + 1))" in target_str:
                return (
                    f"This is a classic telescoping series: 1/(1·2) + 1/(2·3) + ... + 1/(n·(n+1)) = {clean_f}{deps_note}. "
                    f"Using partial fractions, each term splits into (1/k - 1/(k+1)). "
                    f"When summed, all intermediate terms cancel out in pairs, leaving only the first and last parts: 1 - 1/(n+1) = {clean_f}."
                )

        # 2. Powers of compound linear expressions
        if ("2 * k" in target_str or "2k" in target_str) and ("- 1" in target_str or "-1" in target_str) and ("^2" in target_str or "**2" in target_str or "²" in target_str):
            return (
                f"Summing the squares of the first n consecutive odd numbers (1² + 3² + 5² + ... + (2n-1)²) equals {clean_f}{deps_note}. "
                f"Geometrically, this formula computes the discrete volume of stacked odd square slabs, appearing in octahedral coordinate geometries."
            )
        elif ("2 * k" in target_str or "2k" in target_str) and ("^2" in target_str or "**2" in target_str or "²" in target_str):
            return (
                f"Summing the squares of the first n consecutive even numbers (2² + 4² + 6² + ... + (2n)²) equals 4 ∑ k² = {clean_f}{deps_note}, "
                f"scaling the classical square pyramidal numbers by a factor of 4."
            )

        # 3. Higher simplex / consecutive integer products
        if "k + 3" in target_str and "k + 2" in target_str and "k + 1" in target_str:
            return (
                f"Summing products of 4 consecutive integers k(k+1)(k+2)(k+3) yields {clean_f}{deps_note}. "
                f"In discrete combinatorics and simplicial geometry, this formula computes 5-dimensional simplex numbers via the hockey-stick summation identity on Pascal's triangle."
            )
        elif "k + 2" in target_str and "k + 1" in target_str:
            return (
                f"Summing products of 3 consecutive integers k(k+1)(k+2) = k³ + 3k² + 2k yields {clean_f}{deps_note}. "
                f"In discrete geometry, these correspond to 4-simplex (pentatope) numbers, counting points in 4-dimensional triangular lattices."
            )

        # 4. Generalized parametric families (meta-theorems holding for all m or c)
        if re.search(r"k\s*\*\s*\(\s*k\s*\+\s*m\s*\)", target_str) or re.search(r"\(\s*k\s*\+\s*m\s*\)\s*\*\s*k", target_str):
            return (
                f"This is the generalized pronic sum theorem: ∑ k(k + m) = {clean_f}{deps_note}. "
                f"Instead of generating separate theorems for each specific number (k+1, k+2, ..., k+110), "
                f"this master theorem parameterizes the shift as variable m. It establishes that summing k(k + m) "
                f"decomposes into the sum of squares plus m times the triangular numbers: ∑ k² + m ∑ k. "
                f"The proof holds universally across all positive integers n and all parameter shifts m."
            )
        elif re.search(r"\(\s*k\s*\+\s*m\s*\)", target_str) and not re.search(r"k\s*\*", target_str):
            return (
                f"This is the generalized shifted linear sum theorem: ∑ (k + m) = {clean_f}{deps_note}. "
                f"It proves that adding a uniform shift m across n integers shifts the triangular sum by exactly m·n. "
                f"The proof holds universally across all positive integers n and all parameter shifts m."
            )
        elif re.search(r"\bc\s*\*\s*k\b", target_str):
            return (
                f"This is the generalized scaled linear sum theorem: ∑ c·k = {clean_f}{deps_note}. "
                f"By the distributive property of discrete summation, scaling every term by constant c scales the triangular sum by exactly c."
            )

        # 5. Factor products k * (k + m)
        m_match = re.search(r"k\s*\*\s*\(\s*k\s*\+\s*(\d+)\s*\)", target_str) or re.search(r"\(\s*k\s*\+\s*(\d+)\s*\)\s*\*\s*k", target_str)
        if m_match:
            m_val = int(m_match.group(1))
            if m_val == 1:
                return (
                    f"Summing consecutive integer products k(k+1) = k² + k combines the sum of squares and triangular numbers{deps_note}, "
                    f"yielding {clean_f}. In discrete geometry, this formula counts the number of points in tetrahedral stacks."
                )
            else:
                return (
                    f"Summing shifted products k(k + {m_val}) = k² + {m_val}k decomposes into the sum of squares plus "
                    f"{m_val} times the triangular sum{deps_note}, yielding {clean_f}. "
                    f"In discrete geometry, this formula counts points in multi-layered prism stacks."
                )

        # 6. Monomial power sums (Faulhaber)
        if "k^6" in target_str or "k⁶" in target_str:
            return (
                f"This is Faulhaber's formula for the sum of the first n sixth powers: 1⁶ + 2⁶ + ... + n⁶ = {clean_f}{deps_note}, "
                f"derived via Bernoulli numbers and Euler-Maclaurin summation."
            )
        elif "k^5" in target_str or "k⁵" in target_str:
            return f"This is Faulhaber's formula for the sum of the first n fifth powers: 1⁵ + 2⁵ + ... + n⁵ = {clean_f}{deps_note}."
        elif "k^4" in target_str or "k⁴" in target_str:
            return f"This is Faulhaber's formula for the sum of the first n fourth powers (quartics): 1⁴ + 2⁴ + ... + n⁴ = {clean_f}{deps_note}."
        elif "(k^3)" in target_str or "k^3" in target_str or "k³" in target_str:
            return (
                f"This is Nicomachus's Theorem: the sum of the first n cubes (1³ + 2³ + ... + n³) is exactly equal to "
                f"the square of the sum of the first n integers: [n(n+1)/2]²{deps_note}. "
                f"Intuitively, partitioning a large square of side n(n+1)/2 yields geometric regions whose areas match consecutive cubic blocks."
            )
        elif "(k^2)" in target_str or "k^2" in target_str or "k²" in target_str:
            return (
                f"This is the square pyramidal number formula: 1² + 2² + ... + n² = n(n+1)(2n+1)/6{deps_note}. "
                f"Geometrically, it represents the exact number of close-packed spheres required to construct a square-based pyramid of height n."
            )

        # 7. Linear expressions
        if re.search(r"2\s*\*\s*k\s*\)?\s*-\s*1", target_str):
            return (
                f"Summing the first n consecutive odd numbers (1 + 3 + 5 + ... + (2n-1)) always equals n²{deps_note}. "
                f"Geometrically, each successive odd number adds an L-shaped border (gnomon) around an existing "
                f"square of unit tiles, expanding an n×n square into an (n+1)×(n+1) square."
            )
        elif "(2 * k)" in target_str and "-" not in target_str and "+" not in target_str:
            return (
                f"Summing the first n positive even numbers (2 + 4 + ... + 2n) equals n² + n = n(n+1){deps_note}. "
                f"This is exactly double the n-th triangular number, forming an oblong (or pronic) rectangle of dimensions n × (n+1)."
            )
        elif re.search(r"\(\s*k\s*\+\s*1\s*\)", target_str) and not re.search(r"k\s*\+\s*1\d", target_str):
            return (
                f"The sum of (k + 1) from 1 to n shifts the standard triangular sum by adding 1 to each of the n terms{deps_note}, "
                f"yielding {clean_f}."
            )
        elif target_str == "sum_k=1..n(k)" or target_str == "k":
            return (
                f"This is the classical triangular number formula: 1 + 2 + ... + n = n(n+1)/2{deps_note}. "
                f"Visually, pairing two identical step-pyramids of dots creates an n × (n+1) rectangle of n(n+1) dots; "
                f"dividing this rectangle in half gives the exact sum of the first n positive integers."
            )
        elif target_str == "sum_k=1..n(1)" or target_str == "1":
            return f"Adding the number 1 repeatedly n times simply yields n. This represents the foundational discrete counting identity."

        # Trigonometric explanations
        if ("sin" in target_str and "cos" in target_str) and ("^2" in target_str or "**2" in target_str):
            return (
                f"This is the fundamental Pythagorean trigonometric identity: sin²(x) + cos²(x) = 1. "
                f"Geometrically, on the Cartesian unit circle of radius 1, any angle x specifies a point (cos(x), sin(x)); "
                f"the Pythagorean theorem on the right triangle formed with the origin establishes that the squared hypotenuse "
                f"(cos²(x) + sin²(x)) always equals 1."
            )
        elif "sin(2" in target_str or "sin(2*" in target_str:
            return (
                f"This is the sine double-angle identity: sin(2x) = 2·sin(x)·cos(x). "
                f"It is derived from the angle-addition formula sin(α + β) where α = β = x."
            )
        elif "cos(2" in target_str or "cos(2*" in target_str:
            return (
                f"This is the cosine double-angle identity: cos(2x) = cos²(x) - sin²(x). "
                f"It decomposes frequency-doubled oscillations into quadratic components of the fundamental frequency."
            )

        # Geometric explanations
        if "sqrt" in target_str and ("a" in target_str and "b" in target_str):
            return (
                f"This is the Pythagorean distance formula: sqrt(a² + b²). "
                f"In Euclidean geometry, it computes the exact length of the hypotenuse for any right-angled triangle with legs a and b."
            )
        elif ("a" in target_str and "b" in target_str) and ("* 2" in target_str or "2 *" in target_str):
            return (
                f"This is the perimeter formula for a rectangle: 2(a + b) = 2a + 2b, "
                f"summing the lengths of all four boundary edges."
            )

        from evolutionary_math.utils.formatting import format_clean_target
        clean_t = format_clean_target(target_str)
        verif_domain = "across all positive integers" if "induction" in proof_method.lower() else "symbolically across the continuous domain"
        return (
            f"The engine established that {clean_t} equals {clean_f}{deps_note}. "
            f"The identity was formally verified {verif_domain} using {proof_method}."
        )


class OpenAICompatibleAdvisoryClient(BaseAdvisoryClient):
    """Air-gapped advisory client targeting any OpenAI-compatible endpoint (Ollama, vLLM, LM Studio)."""

    SYSTEM_PROMPT = (
        "You are an executive meta-heuristic adviser to an evolutionary mathematical discovery engine.\n"
        "Your ONLY role is to evaluate aggregate population telemetry and recommend search parameter adjustments.\n"
        "You must NEVER attempt to prove theorems, output raw equations, or certify validity.\n"
        "Respond with a single JSON object conforming strictly to the AdvisoryResponse schema:\n"
        "{\n"
        '  "diagnosis": "...",\n'
        '  "regime_selection": "EXPLORATION" | "EXPLOITATION" | "BALANCED" | "SIMPLIFICATION",\n'
        '  "operator_weight_adjustments": {\n'
        '    "subtree_mutation": float,\n'
        '    "crossover": float,\n'
        '    "constant_perturbation": float,\n'
        '    "hoist": float\n'
        "  },\n"
        '  "grammar_biases": [{"head": "EXPR", "symbol": "+", "multiplier": 1.5}],\n'
        '  "pruning_recommendations": ["..."],\n'
        '  "suggested_subtrees": ["(2 * n) + 1"],\n'
        '  "confidence": float\n'
        "}"
    )

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434/v1",
        model: str = "llama3",
        api_key: str = "none",
        timeout_seconds: float = 30.0,
    ):
        # Normalize localhost to 127.0.0.1 on Windows to avoid dual-stack IPv6 SYN timeout
        clean_url = base_url.rstrip("/")
        if "://localhost" in clean_url:
            clean_url = clean_url.replace("://localhost", "://127.0.0.1")
        self.base_url = clean_url
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def request_advice(self, request: AdvisoryRequest) -> Optional[AdvisoryResponse]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        user_content = request.model_dump_json(indent=2)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "AdvisoryResponse",
                    "strict": True,
                    "schema": AdvisoryResponse.model_json_schema(),
                },
            },
            "max_tokens": 1024,
            "temperature": 0.2,
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    if resp.status != 200:
                        logger.warning(f"Advisory endpoint returned HTTP {resp.status}")
                        return None
                    resp_json = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as http_err:
                # If endpoint rejected response_format with 400, retry once without it
                if "response_format" in payload and http_err.code == 400:
                    del payload["response_format"]
                    req_data = json.dumps(payload).encode("utf-8")
                    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                        resp_json = json.loads(resp.read().decode("utf-8"))
                else:
                    raise http_err

            choice_msg = resp_json["choices"][0]["message"]
            raw_content = choice_msg.get("content") or choice_msg.get("reasoning_content") or ""
            
            # Strip markdown code fences if present
            clean_choice = raw_content.strip()
            if clean_choice.startswith("```json"):
                clean_choice = clean_choice[7:]
            elif clean_choice.startswith("```"):
                clean_choice = clean_choice[3:]
            if clean_choice.endswith("```"):
                clean_choice = clean_choice[:-3]
            clean_choice = clean_choice.strip()

            # Extract outer JSON object if model outputs preamble or thoughts
            if "{" in clean_choice and "}" in clean_choice:
                start = clean_choice.find("{")
                end = clean_choice.rfind("}") + 1
                clean_choice = clean_choice[start:end]

            parsed_dict = json.loads(clean_choice)
            if isinstance(parsed_dict, dict):
                # Clamp any negative operator weight values if model treated them as deltas
                weights = parsed_dict.get("operator_weight_adjustments")
                if isinstance(weights, dict):
                    for k, v in list(weights.items()):
                        if isinstance(v, (int, float)):
                            weights[k] = max(0.01, min(float(abs(v)), 1.0))
                # Uppercase regime if present
                reg = parsed_dict.get("regime_selection")
                if isinstance(reg, str):
                    parsed_dict["regime_selection"] = reg.strip().upper()

            return AdvisoryResponse.model_validate(parsed_dict)

        except Exception as e:
            logger.warning(f"Advisory request failed: {e}. Falling back to deterministic heuristics.")
            return None

    def explain_discovery(
        self,
        target_str: str,
        discovery_str: str,
        latex_str: str,
        proof_method: str,
        dependencies: Optional[list] = None,
    ) -> str:
        """Query LLM for an intuitive, plain-English conceptual explanation of the theorem."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        deps_context = f"Composed previous lemmas: {', '.join(dependencies)}" if dependencies else "Foundational proof"
        prompt = (
            f"You are a mathematical expositor. Explain the following mathematical theorem in 2-3 concise, "
            f"engaging, plain-English sentences for a human researcher:\n"
            f"- Problem/Target: {target_str}\n"
            f"- Discovered Closed Form: {discovery_str}\n"
            f"- LaTeX: {latex_str}\n"
            f"- Proof Method: {proof_method}\n"
            f"- Context: {deps_context}\n\n"
            f"Focus on the intuitive, geometric, or conceptual meaning of why this identity holds."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You explain mathematical identities intuitively in 2-3 sentences."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 512,
            "temperature": 0.3,
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if resp.status == 200:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    msg = resp_json["choices"][0]["message"]
                    explanation = (msg.get("content") or "").strip()
                    if explanation:
                        return explanation
        except Exception as e:
            logger.warning(f"Failed to fetch LLM explanation: {e}. Falling back to default exposition.")

        # Fallback to MockAdvisoryClient deterministic generator
        mock = MockAdvisoryClient()
        return mock.explain_discovery(target_str, discovery_str, latex_str, proof_method, dependencies)

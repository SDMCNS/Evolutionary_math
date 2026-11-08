"""Unit tests for advisory JSON schemas and validation."""

import pytest
from pydantic import ValidationError
from evolutionary_math.advisory.schema import (
    AdvisoryRequest,
    AdvisoryResponse,
    OperatorWeights,
    GrammarBias,
    CandidateSignature,
)


def test_operator_weights_validation():
    w = OperatorWeights(subtree_mutation=0.3, crossover=0.4, constant_perturbation=0.2, hoist=0.1)
    assert w.crossover == 0.4

    with pytest.raises(ValidationError):
        # Out of bounds (> 1.0)
        OperatorWeights(crossover=1.5)


def test_grammar_bias_validation():
    bias = GrammarBias(head="EXPR", symbol="+", multiplier=2.5)
    assert bias.multiplier == 2.5

    with pytest.raises(ValidationError):
        # Multiplier too small (< 0.1)
        GrammarBias(head="EXPR", symbol="+", multiplier=0.01)


def test_advisory_response_schema():
    payload = {
        "diagnosis": "Search stagnated near quadratic target.",
        "regime_selection": "EXPLOITATION",
        "operator_weight_adjustments": {
            "subtree_mutation": 0.2,
            "crossover": 0.2,
            "constant_perturbation": 0.5,
            "hoist": 0.1,
        },
        "grammar_biases": [
            {"head": "EXPR", "symbol": "*", "multiplier": 1.5}
        ],
        "pruning_recommendations": ["Prune depth > 5"],
        "confidence": 0.88,
    }

    resp = AdvisoryResponse.model_validate(payload)
    assert resp.regime_selection == "EXPLOITATION"
    assert resp.confidence == 0.88
    assert len(resp.grammar_biases) == 1


def test_invalid_regime_rejected():
    payload = {
        "diagnosis": "Invalid regime",
        "regime_selection": "INVALID_REGIME",
        "confidence": 0.5,
    }
    with pytest.raises(ValidationError):
        AdvisoryResponse.model_validate(payload)


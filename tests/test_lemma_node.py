"""Unit tests for LemmaNode and AST serialization."""

import sympy as sp
import numpy as np
from evolutionary_math.core.ast import expr_factory, expr_from_dict, LemmaNode


def test_lemma_node_creation_and_eval():
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    # Lemma definition: triangular numbers n*(n+1)/2
    def_ast = expr_factory.op("/", expr_factory.op("*", n, expr_factory.op("+", n, one)), two)
    lemma_node = expr_factory.lemma("L_sum_k", n, def_ast)

    assert isinstance(lemma_node, LemmaNode)
    assert lemma_node.eval_numerical({"n": 4}) == 10.0
    assert lemma_node.eval_numerical({"n": 10}) == 55.0

    # Vectorized evaluation
    res = lemma_node.eval_numerical({"n": np.array([1, 2, 3, 4])})
    np.testing.assert_allclose(res, np.array([1.0, 3.0, 6.0, 10.0]))

    # SymPy conversion
    sp_expr = lemma_node.to_sympy()
    n_sym = sp.Symbol("n")
    assert sp.simplify(sp_expr - n_sym * (n_sym + 1) / 2) == 0


def test_ast_dict_serialization_roundtrip():
    n = expr_factory.variable("n")
    one = expr_factory.constant(1)
    two = expr_factory.constant(2)

    # ((n + 1) * 2)
    expr = expr_factory.op("*", expr_factory.op("+", n, one), two)
    d = expr.to_dict()
    reconstructed = expr_from_dict(d)
    assert expr == reconstructed
    assert expr is reconstructed  # Hash-consing ensures identical instance

    # LemmaNode roundtrip
    lemma_node = expr_factory.lemma("L1", n, expr)
    d_lemma = lemma_node.to_dict()
    recon_lemma = expr_from_dict(d_lemma)
    assert lemma_node == recon_lemma
    assert lemma_node is recon_lemma


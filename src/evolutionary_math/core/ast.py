"""Strongly-typed Abstract Syntax Tree and DAG representation of mathematical expressions."""

from abc import ABC, abstractmethod
from fractions import Fraction
from typing import Dict, Tuple, Set, Any, Union, Optional
import sympy as sp
import numpy as np

# Suppress floating-point overflow/underflow warnings in vectorized genetic search
np.seterr(all="ignore")

from evolutionary_math.core.types import MathType
from evolutionary_math.core.operators import OperatorRegistry


_SP_SYMBOLS: Dict[str, sp.Symbol] = {}


def get_sympy_symbol(name: str) -> sp.Symbol:
    """Retrieve or create a canonical SymPy symbol to ensure consistent assumption matching."""
    if name not in _SP_SYMBOLS:
        _SP_SYMBOLS[name] = sp.Symbol(name)
    return _SP_SYMBOLS[name]


class ExprNode(ABC):
    """Abstract base class for all expression nodes in the AST/DAG."""

    __slots__ = ("_hash", "_depth", "_node_count", "_variables", "math_type")

    def __init__(self, math_type: MathType):
        self.math_type = math_type
        self._hash: Optional[int] = None
        self._depth: Optional[int] = None
        self._node_count: Optional[int] = None
        self._variables: Optional[frozenset[str]] = None

    @property
    @abstractmethod
    def children(self) -> Tuple["ExprNode", ...]:
        """Return tuple of direct child nodes."""
        pass

    @property
    def depth(self) -> int:
        """Compute the maximum depth of the expression tree."""
        if self._depth is None:
            if not self.children:
                self._depth = 1
            else:
                self._depth = 1 + max(c.depth for c in self.children)
        return self._depth

    @property
    def node_count(self) -> int:
        """Total number of nodes in the expression subtree."""
        if self._node_count is None:
            self._node_count = 1 + sum(c.node_count for c in self.children)
        return self._node_count

    @property
    def variables(self) -> frozenset[str]:
        """Set of variable names present in this expression."""
        if self._variables is None:
            vars_set: Set[str] = set()
            for c in self.children:
                vars_set.update(c.variables)
            self._variables = frozenset(vars_set)
        return self._variables

    @abstractmethod
    def eval_numerical(self, env: Dict[str, Any]) -> Any:
        """Evaluate numerically given variable bindings (supports floats, ints, numpy arrays)."""
        pass

    @abstractmethod
    def to_sympy(self) -> sp.Expr:
        """Convert the AST to a native SymPy expression for exact symbolic manipulation."""
        pass

    @abstractmethod
    def to_sexpr(self) -> str:
        """Serialize to Lisp-style S-expression."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize AST node to JSON-compatible dictionary."""
        pass

    @abstractmethod
    def _compute_hash(self) -> int:
        pass

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = self._compute_hash()
        return self._hash

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass


class ConstantNode(ExprNode):
    """Represents an exact scalar constant (integer or rational)."""

    __slots__ = ("value",)
    __hash__ = ExprNode.__hash__

    def __init__(self, value: Union[int, float, Fraction], math_type: Optional[MathType] = None):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if math_type is None:
            if isinstance(value, int):
                math_type = MathType.INTEGER
            elif isinstance(value, Fraction):
                math_type = MathType.RATIONAL
            else:
                math_type = MathType.REAL
        super().__init__(math_type)
        self.value = value

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return ()

    @property
    def variables(self) -> frozenset[str]:
        return frozenset()

    def eval_numerical(self, env: Dict[str, Any]) -> Any:
        return self.value

    def to_sympy(self) -> sp.Expr:
        if isinstance(self.value, int):
            return sp.Integer(self.value)
        if isinstance(self.value, Fraction):
            return sp.Rational(self.value.numerator, self.value.denominator)
        return sp.Float(self.value)

    def to_sexpr(self) -> str:
        return str(self.value)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "const", "val": self.value}

    def _compute_hash(self) -> int:
        return hash((ConstantNode, self.value, self.math_type))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ConstantNode) and self.value == other.value and self.math_type == other.math_type

    def __repr__(self) -> str:
        return str(self.value)


class VariableNode(ExprNode):
    """Represents an atomic variable terminal (e.g., n, k, x)."""

    __slots__ = ("name",)
    __hash__ = ExprNode.__hash__

    def __init__(self, name: str, math_type: MathType = MathType.REAL):
        super().__init__(math_type)
        self.name = name

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return ()

    @property
    def variables(self) -> frozenset[str]:
        return frozenset([self.name])

    def eval_numerical(self, env: Dict[str, Any]) -> Any:
        if self.name not in env:
            raise KeyError(f"Variable '{self.name}' not provided in evaluation environment.")
        return env[self.name]

    def to_sympy(self) -> sp.Symbol:
        return get_sympy_symbol(self.name)

    def to_sexpr(self) -> str:
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "var", "name": self.name}

    def _compute_hash(self) -> int:
        return hash((VariableNode, self.name, self.math_type))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, VariableNode) and self.name == other.name and self.math_type == other.math_type

    def __repr__(self) -> str:
        return self.name


class OperatorNode(ExprNode):
    """Represents an operator applied to one or more operand expressions."""

    __slots__ = ("op", "_children")
    __hash__ = ExprNode.__hash__

    def __init__(self, op: str, children: Tuple[ExprNode, ...], math_type: Optional[MathType] = None):
        signature = OperatorRegistry.get(op)
        if len(children) != signature.arity:
            raise ValueError(
                f"Operator '{op}' expects {signature.arity} arguments, but received {len(children)}."
            )
        target_type = math_type or signature.return_type
        super().__init__(target_type)
        self.op = op
        self._children = children

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self._children

    def eval_numerical(self, env: Dict[str, Any]) -> Any:
        if self.op == "+":
            return self._children[0].eval_numerical(env) + self._children[1].eval_numerical(env)
        elif self.op == "-":
            return self._children[0].eval_numerical(env) - self._children[1].eval_numerical(env)
        elif self.op == "*":
            return self._children[0].eval_numerical(env) * self._children[1].eval_numerical(env)
        elif self.op == "/":
            denom = self._children[1].eval_numerical(env)
            # Handle division by zero safely
            if isinstance(denom, np.ndarray):
                with np.errstate(divide="ignore", invalid="ignore"):
                    res = self._children[0].eval_numerical(env) / denom
                    return np.nan_to_num(res, nan=1e9, posinf=1e9, neginf=-1e9)
            else:
                if denom == 0:
                    return float("inf")
                return self._children[0].eval_numerical(env) / denom
        elif self.op == "^":
            base = self._children[0].eval_numerical(env)
            exp = self._children[1].eval_numerical(env)
            # Clip runaway exponents to prevent integer hang or overflow warnings during search
            if isinstance(exp, (int, float)):
                exp = float(np.clip(exp, -50.0, 50.0))
            elif isinstance(exp, np.ndarray):
                exp = np.clip(exp, -50.0, 50.0)
            return base ** exp
        elif self.op == "neg":
            return -self._children[0].eval_numerical(env)
        elif self.op == "sum":
            # Discrete sum: sum(term, n) where index variable 'k' ranges from 1 to n
            # children[0] is the term expression (involving k), children[1] is upper bound n
            upper_val = self._children[1].eval_numerical(env)
            if isinstance(upper_val, np.ndarray):
                results = []
                for idx, u in enumerate(upper_val):
                    u_int = int(u)
                    if u_int < 1:
                        results.append(0.0)
                    else:
                        sub_env = {}
                        for var_k, val_arr in env.items():
                            if isinstance(val_arr, np.ndarray) and len(val_arr) == len(upper_val):
                                sub_env[var_k] = val_arr[idx]
                            else:
                                sub_env[var_k] = val_arr
                        sub_env["k"] = np.arange(1, u_int + 1)
                        term_vals = self._children[0].eval_numerical(sub_env)
                        if isinstance(term_vals, np.ndarray):
                            results.append(float(np.sum(term_vals)))
                        else:
                            results.append(float(term_vals * u_int))
                return np.array(results)
            else:
                u_int = int(upper_val)
                if u_int < 1:
                    return 0
                total = 0
                sub_env = dict(env)
                for k in range(1, u_int + 1):
                    sub_env["k"] = k
                    total += self._children[0].eval_numerical(sub_env)
                return total
        elif self.op == "sin":
            return np.sin(self._children[0].eval_numerical(env))
        elif self.op == "cos":
            return np.cos(self._children[0].eval_numerical(env))
        elif self.op == "tan":
            res = np.tan(self._children[0].eval_numerical(env))
            if isinstance(res, np.ndarray):
                return np.nan_to_num(res, nan=1e9, posinf=1e9, neginf=-1e9)
            return res
        elif self.op == "sqrt":
            arg = self._children[0].eval_numerical(env)
            if isinstance(arg, np.ndarray):
                return np.sqrt(np.maximum(0.0, arg))
            return np.sqrt(max(0.0, float(arg)))
        elif self.op == "abs":
            return np.abs(self._children[0].eval_numerical(env))
        else:
            raise NotImplementedError(f"Numerical evaluation for operator '{self.op}' is not implemented.")

    def to_sympy(self) -> sp.Expr:
        args = [c.to_sympy() for c in self._children]
        if self.op == "+":
            return sp.Add(*args)
        elif self.op == "-":
            return args[0] - args[1]
        elif self.op == "*":
            return sp.Mul(*args)
        elif self.op == "/":
            return args[0] / args[1]
        elif self.op == "^":
            return sp.Pow(args[0], args[1])
        elif self.op == "neg":
            return -args[0]
        elif self.op == "sum":
            k = get_sympy_symbol("k")
            return sp.Sum(args[0], (k, 1, args[1]))
        elif self.op == "sin":
            return sp.sin(args[0])
        elif self.op == "cos":
            return sp.cos(args[0])
        elif self.op == "tan":
            return sp.tan(args[0])
        elif self.op == "sqrt":
            return sp.sqrt(args[0])
        elif self.op == "abs":
            return sp.Abs(args[0])
        else:
            raise NotImplementedError(f"SymPy conversion for operator '{self.op}' is not implemented.")

    def to_sexpr(self) -> str:
        child_strs = " ".join(c.to_sexpr() for c in self._children)
        return f"({self.op} {child_strs})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "op", "op": self.op, "args": [c.to_dict() for c in self._children]}

    def _compute_hash(self) -> int:
        return hash((OperatorNode, self.op, self._children, self.math_type))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, OperatorNode)
            and self.op == other.op
            and self._children == other._children
            and self.math_type == other.math_type
        )

    def __repr__(self) -> str:
        if self.op in ("+", "-", "*", "/"):
            return f"({self._children[0]} {self.op} {self._children[1]})"
        elif self.op == "^":
            return f"({self._children[0]}^{self._children[1]})"
        elif self.op == "neg":
            return f"(-{self._children[0]})"
        elif self.op in ("sin", "cos", "tan", "sqrt", "abs"):
            return f"{self.op}({self._children[0]})"
        elif self.op == "sum":
            return f"sum_k=1..{self._children[1]}({self._children[0]})"
        return self.to_sexpr()


class LemmaNode(ExprNode):
    """Represents the invocation of a previously verified lemma / Automatically Defined Function (ADF)."""

    __slots__ = ("lemma_id", "definition", "_children")
    __hash__ = ExprNode.__hash__

    def __init__(
        self,
        lemma_id: str,
        arg: ExprNode,
        definition: ExprNode,
        math_type: Optional[MathType] = None,
    ):
        super().__init__(math_type or definition.math_type)
        self.lemma_id = lemma_id
        self.definition = definition
        self._children = (arg,)

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self._children

    @property
    def arg(self) -> ExprNode:
        return self._children[0]

    def eval_numerical(self, env: Dict[str, Any]) -> Any:
        arg_val = self.arg.eval_numerical(env)
        sub_env = dict(env)
        sub_env["n"] = arg_val
        return self.definition.eval_numerical(sub_env)

    def to_sympy(self) -> sp.Expr:
        arg_sp = self.arg.to_sympy()
        n_sym = get_sympy_symbol("n")
        def_sp = self.definition.to_sympy()
        return def_sp.subs(n_sym, arg_sp)

    def to_sexpr(self) -> str:
        return f"({self.lemma_id} {self.arg.to_sexpr()})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "lemma",
            "lemma_id": self.lemma_id,
            "arg": self.arg.to_dict(),
            "def": self.definition.to_dict(),
        }

    def _compute_hash(self) -> int:
        return hash((LemmaNode, self.lemma_id, self.arg, self.definition, self.math_type))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, LemmaNode)
            and self.lemma_id == other.lemma_id
            and self.arg == other.arg
            and self.definition == other.definition
            and self.math_type == other.math_type
        )

    def __repr__(self) -> str:
        return f"{self.lemma_id}({self.arg})"


class SequenceTermNode(ExprNode):
    """Represents a term in a recurrence sequence, e.g. F(n), F(n+1), F(k)."""

    __slots__ = ("seq_name", "_children")
    __hash__ = ExprNode.__hash__

    _FIB_MEMO: Dict[int, int] = {0: 0, 1: 1}

    def __init__(self, seq_name: str, index_expr: ExprNode, math_type: Optional[MathType] = None):
        super().__init__(math_type or MathType.INTEGER)
        self.seq_name = seq_name
        self._children = (index_expr,)

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self._children

    @property
    def index_expr(self) -> ExprNode:
        return self._children[0]

    @classmethod
    def _fib(cls, n: int) -> int:
        """Fast memoized Fibonacci computation."""
        if n < 0:
            # F_{-n} = (-1)^(n+1) * F_n
            sign = -1 if n % 2 == 0 else 1
            return sign * cls._fib(-n)
        if n in cls._FIB_MEMO:
            return cls._FIB_MEMO[n]
        # Fast doubling or iteration
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        cls._FIB_MEMO[n] = a
        return a

    def eval_numerical(self, env: Dict[str, Any]) -> Any:
        idx_val = self.index_expr.eval_numerical(env)
        if isinstance(idx_val, np.ndarray):
            results = []
            for val in idx_val:
                ival = int(round(val))
                if self.seq_name == "F":
                    results.append(float(self._fib(ival)))
                elif self.seq_name == "L":  # Lucas sequence: L_n = F_{n-1} + F_{n+1}
                    results.append(float(self._fib(ival - 1) + self._fib(ival + 1)))
                else:
                    results.append(float(ival))
            return np.array(results)
        else:
            ival = int(round(idx_val))
            if self.seq_name == "F":
                return self._fib(ival)
            elif self.seq_name == "L":
                return self._fib(ival - 1) + self._fib(ival + 1)
            return ival

    def to_sympy(self) -> sp.Expr:
        idx_sp = self.index_expr.to_sympy()
        if self.seq_name == "F":
            return sp.fibonacci(idx_sp)
        elif self.seq_name == "L":
            return sp.lucas(idx_sp)
        return sp.Function(self.seq_name)(idx_sp)

    def to_sexpr(self) -> str:
        return f"({self.seq_name} {self.index_expr.to_sexpr()})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "seq_term",
            "seq_name": self.seq_name,
            "index": self.index_expr.to_dict(),
        }

    def _compute_hash(self) -> int:
        return hash((SequenceTermNode, self.seq_name, self.index_expr, self.math_type))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, SequenceTermNode)
            and self.seq_name == other.seq_name
            and self.index_expr == other.index_expr
            and self.math_type == other.math_type
        )

    def __repr__(self) -> str:
        return f"{self.seq_name}({self.index_expr})"


class ExpressionFactory:
    """Hash-consing factory for maximal sub-expression sharing (DAG creation)."""

    def __init__(self):
        self._cache: Dict[Tuple, ExprNode] = {}

    def constant(self, value: Union[int, float, Fraction], math_type: Optional[MathType] = None) -> ConstantNode:
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        key = ("const", value, math_type)
        if key not in self._cache:
            self._cache[key] = ConstantNode(value, math_type)
        return self._cache[key]  # type: ignore

    def variable(self, name: str, math_type: MathType = MathType.REAL) -> VariableNode:
        key = ("var", name, math_type)
        if key not in self._cache:
            self._cache[key] = VariableNode(name, math_type)
        return self._cache[key]  # type: ignore

    def op(
        self,
        op_symbol: str,
        *children: ExprNode,
        math_type: Optional[MathType] = None,
    ) -> OperatorNode:
        key = ("op", op_symbol, children, math_type)
        if key not in self._cache:
            self._cache[key] = OperatorNode(op_symbol, children, math_type)
        return self._cache[key]  # type: ignore

    def lemma(
        self,
        lemma_id: str,
        arg: ExprNode,
        definition: ExprNode,
        math_type: Optional[MathType] = None,
    ) -> LemmaNode:
        key = ("lemma", lemma_id, arg, definition, math_type)
        if key not in self._cache:
            self._cache[key] = LemmaNode(lemma_id, arg, definition, math_type)
        return self._cache[key]  # type: ignore

    def seq_term(
        self,
        seq_name: str,
        index_expr: ExprNode,
        math_type: Optional[MathType] = None,
    ) -> SequenceTermNode:
        key = ("seq_term", seq_name, index_expr, math_type)
        if key not in self._cache:
            self._cache[key] = SequenceTermNode(seq_name, index_expr, math_type)
        return self._cache[key]  # type: ignore

    def clear(self) -> None:
        self._cache.clear()


expr_factory = ExpressionFactory()


def expr_from_dict(d: Dict[str, Any]) -> ExprNode:
    """Reconstruct an immutable AST node from a serialized dictionary."""
    node_type = d.get("type")
    if node_type == "const":
        return expr_factory.constant(d["val"])
    elif node_type == "var":
        return expr_factory.variable(d["name"])
    elif node_type == "op":
        children = tuple(expr_from_dict(c) for c in d["args"])
        return expr_factory.op(d["op"], *children)
    elif node_type == "lemma":
        arg = expr_from_dict(d["arg"])
        defn = expr_from_dict(d["def"])
        return expr_factory.lemma(d["lemma_id"], arg, defn)
    elif node_type == "seq_term":
        idx = expr_from_dict(d["index"])
        return expr_factory.seq_term(d["seq_name"], idx)
    else:
        raise ValueError(f"Unknown serialized AST node type: {node_type}")


def from_sympy(expr: sp.Expr) -> ExprNode:
    """Convert a SymPy expression tree into a strongly-typed ExprNode DAG."""
    if isinstance(expr, sp.Symbol):
        return expr_factory.variable(str(expr.name))
    elif isinstance(expr, sp.Integer):
        return expr_factory.constant(int(expr))
    elif isinstance(expr, sp.Rational):
        if expr.q == 1:
            return expr_factory.constant(int(expr.p))
        return expr_factory.op("/", expr_factory.constant(int(expr.p)), expr_factory.constant(int(expr.q)))
    elif isinstance(expr, sp.Float):
        f = float(expr)
        if f.is_integer():
            return expr_factory.constant(int(f))
        return expr_factory.constant(f)
    elif isinstance(expr, sp.Pow):
        if expr.exp == sp.Rational(1, 2):
            return expr_factory.op("sqrt", from_sympy(expr.base))
        if expr.exp.is_negative:
            pos_exp = -expr.exp
            den = from_sympy(sp.Pow(expr.base, pos_exp))
            return expr_factory.op("/", expr_factory.constant(1), den)
        return expr_factory.op("^", from_sympy(expr.base), from_sympy(expr.exp))
    elif isinstance(expr, sp.sin):
        return expr_factory.op("sin", from_sympy(expr.args[0]))
    elif isinstance(expr, sp.cos):
        return expr_factory.op("cos", from_sympy(expr.args[0]))
    elif isinstance(expr, sp.tan):
        return expr_factory.op("tan", from_sympy(expr.args[0]))
    elif isinstance(expr, sp.Abs):
        return expr_factory.op("abs", from_sympy(expr.args[0]))
    elif isinstance(expr, sp.Add):
        args = list(expr.args)
        res = from_sympy(args[0])
        for a in args[1:]:
            res = expr_factory.op("+", res, from_sympy(a))
        return res
    elif isinstance(expr, sp.Mul):
        num_args = []
        den_args = []
        for a in expr.args:
            if isinstance(a, sp.Rational) and a.q != 1:
                if a.p != 1:
                    num_args.append(sp.Integer(a.p))
                den_args.append(sp.Integer(a.q))
            elif isinstance(a, sp.Pow) and a.exp.is_negative:
                den_args.append(sp.Pow(a.base, -a.exp))
            else:
                num_args.append(a)

        if not num_args:
            num_node = expr_factory.constant(1)
        else:
            num_node = from_sympy(num_args[0])
            for a in num_args[1:]:
                num_node = expr_factory.op("*", num_node, from_sympy(a))

        if not den_args:
            return num_node
        else:
            den_node = from_sympy(den_args[0])
            for a in den_args[1:]:
                den_node = expr_factory.op("*", den_node, from_sympy(a))
            return expr_factory.op("/", num_node, den_node)
    else:
        raise ValueError(f"Unsupported SymPy expression type: {type(expr)}")


def parse_expr_str(s: str) -> ExprNode:
    """Parse a mathematical formula string into a canonical ExprNode."""
    clean_s = s.strip()
    if clean_s.startswith("sum_k=1..n(") and clean_s.endswith(")"):
        inner = clean_s[len("sum_k=1..n("):-1]
        return expr_factory.op("sum", parse_expr_str(inner), expr_factory.variable("n"))
    elif clean_s.startswith("sum(") and clean_s.endswith(")"):
        inner = clean_s[len("sum("):-1]
        parts = [p.strip() for p in inner.rsplit(",", 1)]
        if len(parts) == 2 and parts[1] == "n":
            return expr_factory.op("sum", parse_expr_str(parts[0]), expr_factory.variable("n"))
        return expr_factory.op("sum", parse_expr_str(inner), expr_factory.variable("n"))

    clean_s = clean_s.replace("^", "**")
    sp_expr = sp.sympify(clean_s)
    return from_sympy(sp_expr)


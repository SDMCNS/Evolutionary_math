"""Persistent Mathematical Knowledge Base backed by SQLite."""

import sqlite3
import json
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, TYPE_CHECKING
from pathlib import Path

from evolutionary_math.core.ast import ExprNode, LemmaNode, expr_from_dict
from evolutionary_math.core.canonicalizer import canonicalize
from evolutionary_math.grammar.rules import Grammar

if TYPE_CHECKING:
    from evolutionary_math.evolution.individual import Individual


@dataclass
class StoredTheorem:
    """A mathematically verified discovery stored in the knowledge base."""
    id: str
    target_str: str
    discovery_str: str
    sexpr: str
    proof_method: str
    generation: int
    timestamp: float
    experiment_id: str
    ast_dict: Optional[Dict[str, Any]] = None
    definition_ast: Optional[ExprNode] = None
    dependency_ids: List[str] = field(default_factory=list)
    explanation: Optional[str] = None
    name: Optional[str] = None
    clean_target: Optional[str] = None
    clean_formula: Optional[str] = None
    expanded_formula: Optional[str] = None
    latex: Optional[str] = None
    is_generalized: bool = False
    parameter_vars: List[str] = field(default_factory=list)


@dataclass
class SearchBranchRecord:
    """A single exploration step / branch in the evolutionary search effort."""
    id: str
    experiment_id: str
    target_str: str
    generation: int
    candidate_str: str
    clean_formula: str
    validity: float
    status: str  # "breakthrough", "milestone", "falsified", "stagnant", "intervention"
    operator: str  # "init", "crossover", "subtree_mutation", "constant_perturbation", "hoist", "lemma"
    parent_id: Optional[str] = None
    parent_str: Optional[str] = None
    reason: Optional[str] = None
    timestamp: float = 0.0


@dataclass
class TargetEffortRecord:
    """Persistent record of an attempted mathematical target space and exploration effort."""
    target_str: str
    clean_target: str
    domain_mode: str
    status: str                         # "SOLVED", "UNSOLVED"
    attempts_count: int
    total_generations: int
    total_evaluations: int
    total_time_sec: float
    best_validity: float
    best_candidate_str: Optional[str] = None
    best_clean_formula: Optional[str] = None
    failure_reason: Optional[str] = None
    advisory_interventions_count: int = 0
    first_attempted: float = 0.0
    last_attempted: float = 0.0
    last_experiment_id: Optional[str] = None


class KnowledgeBase:
    """SQLite-backed persistent store for mathematical discoveries, proofs, and lineages."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS theorems (
                    id TEXT PRIMARY KEY,
                    target_str TEXT NOT NULL,
                    discovery_str TEXT NOT NULL,
                    sexpr TEXT NOT NULL,
                    canonical_sexpr TEXT NOT NULL,
                    proof_method TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    experiment_id TEXT NOT NULL,
                    ast_json TEXT,
                    dependencies_json TEXT,
                    explanation TEXT,
                    name TEXT,
                    clean_target TEXT,
                    clean_formula TEXT,
                    expanded_formula TEXT,
                    latex TEXT,
                    is_generalized INTEGER DEFAULT 0,
                    parameter_vars TEXT
                )
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_canonical_sexpr ON theorems(canonical_sexpr)
            """)

            # Ensure backward-compatible schema migrations for existing databases
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(theorems)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            for col in ["ast_json", "dependencies_json", "explanation", "name", "clean_target", "clean_formula", "expanded_formula", "latex", "parameter_vars"]:
                if col not in existing_cols:
                    self.conn.execute(f"ALTER TABLE theorems ADD COLUMN {col} TEXT")
            if "is_generalized" not in existing_cols:
                self.conn.execute("ALTER TABLE theorems ADD COLUMN is_generalized INTEGER DEFAULT 0")

            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_is_generalized ON theorems(is_generalized)
            """)

            # Create clean human-readable SQL View for SQLite clients & dashboards
            self.conn.execute("""
                CREATE VIEW IF NOT EXISTS v_discoveries AS
                SELECT 
                    id,
                    COALESCE(name, 'Theorem ' || id) AS name,
                    COALESCE(clean_target, target_str) AS target,
                    COALESCE(clean_formula, discovery_str) AS formula,
                    COALESCE(expanded_formula, discovery_str) AS expanded_formula,
                    proof_method,
                    generation,
                    COALESCE(explanation, 'Verified mathematical identity.') AS explanation,
                    latex
                FROM theorems
            """)

            # Search history effort table (tracking milestones, branches, failures, and interventions)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    target_str TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    candidate_str TEXT NOT NULL,
                    clean_formula TEXT NOT NULL,
                    validity REAL NOT NULL,
                    status TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    parent_id TEXT,
                    parent_str TEXT,
                    reason TEXT,
                    timestamp REAL NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_target ON search_history(target_str, generation)
            """)

            # Target registry table (tracking lifecycle, status, and cumulative effort for all attempted problem spaces)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS target_registry (
                    target_str TEXT PRIMARY KEY,
                    clean_target TEXT NOT NULL,
                    domain_mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts_count INTEGER NOT NULL DEFAULT 1,
                    total_generations INTEGER NOT NULL DEFAULT 0,
                    total_evaluations INTEGER NOT NULL DEFAULT 0,
                    total_time_sec REAL NOT NULL DEFAULT 0.0,
                    best_validity REAL NOT NULL DEFAULT 0.0,
                    best_candidate_str TEXT,
                    best_clean_formula TEXT,
                    failure_reason TEXT,
                    advisory_interventions_count INTEGER NOT NULL DEFAULT 0,
                    first_attempted REAL NOT NULL,
                    last_attempted REAL NOT NULL,
                    last_experiment_id TEXT
                )
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_target_status ON target_registry(status)
            """)
            self.conn.execute("""
                CREATE VIEW IF NOT EXISTS v_unsolved_targets AS
                SELECT 
                    clean_target,
                    domain_mode,
                    attempts_count,
                    total_generations,
                    total_evaluations,
                    ROUND(total_time_sec, 2) AS total_time_sec,
                    ROUND(best_validity, 4) AS best_validity,
                    best_clean_formula,
                    failure_reason,
                    datetime(last_attempted, 'unixepoch') AS last_attempted_at
                FROM target_registry
                WHERE status = 'UNSOLVED'
                ORDER BY best_validity DESC, total_evaluations DESC
            """)

            # Active working checkpoints table (persists in-flight populations and state across interrupts)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_key TEXT PRIMARY KEY,
                    target_str TEXT NOT NULL,
                    clean_target TEXT,
                    domain_mode TEXT NOT NULL,
                    current_generation INTEGER NOT NULL,
                    max_generations INTEGER NOT NULL,
                    experiment_id TEXT,
                    islands_data TEXT NOT NULL,
                    meta_json TEXT,
                    timestamp REAL NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoint_target ON checkpoints(target_str)
            """)

        # Auto-enrich legacy records with intuitive representations
        self.enrich_all_theorems()
        self.sync_target_registry_from_history()

    def record_branch(self, branch: SearchBranchRecord) -> None:
        """Record an exploration attempt or milestone into persistent search history."""
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO search_history
                (id, experiment_id, target_str, generation, candidate_str, clean_formula, validity, status, operator, parent_id, parent_str, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    branch.id,
                    branch.experiment_id,
                    branch.target_str,
                    branch.generation,
                    branch.candidate_str,
                    branch.clean_formula,
                    branch.validity,
                    branch.status,
                    branch.operator,
                    branch.parent_id,
                    branch.parent_str,
                    branch.reason,
                    branch.timestamp or time.time(),
                ),
            )

    def record_branches(self, branches: List[SearchBranchRecord]) -> None:
        """Batch record multiple exploration attempts."""
        if not branches:
            return
        with self.conn:
            self.conn.executemany(
                """
                INSERT OR REPLACE INTO search_history
                (id, experiment_id, target_str, generation, candidate_str, clean_formula, validity, status, operator, parent_id, parent_str, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        b.id,
                        b.experiment_id,
                        b.target_str,
                        b.generation,
                        b.candidate_str,
                        b.clean_formula,
                        b.validity,
                        b.status,
                        b.operator,
                        b.parent_id,
                        b.parent_str,
                        b.reason,
                        b.timestamp or time.time(),
                    )
                    for b in branches
                ],
            )

    def get_search_history(
        self,
        target_str: Optional[str] = None,
        experiment_id: Optional[str] = None,
        limit: int = 500,
    ) -> List[SearchBranchRecord]:
        """Retrieve recorded search effort history for visualization."""
        cursor = self.conn.cursor()
        query = "SELECT id, experiment_id, target_str, generation, candidate_str, clean_formula, validity, status, operator, parent_id, parent_str, reason, timestamp FROM search_history"
        params = []
        conditions = []
        if target_str:
            conditions.append("target_str = ?")
            params.append(target_str)
        if experiment_id:
            conditions.append("experiment_id = ?")
            params.append(experiment_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY generation ASC, validity DESC, timestamp ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            SearchBranchRecord(
                id=r["id"],
                experiment_id=r["experiment_id"],
                target_str=r["target_str"],
                generation=r["generation"],
                candidate_str=r["candidate_str"],
                clean_formula=r["clean_formula"],
                validity=r["validity"],
                status=r["status"],
                operator=r["operator"],
                parent_id=r["parent_id"],
                parent_str=r["parent_str"],
                reason=r["reason"],
                timestamp=r["timestamp"],
            )
            for r in rows
        ]

    def get_targets_in_history(self) -> List[str]:
        """Retrieve distinct targets present in the search history."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT target_str FROM search_history ORDER BY target_str")
        return [r[0] for r in cursor.fetchall()]

    def record_target_attempt(
        self,
        target: Any,
        result: Any,
        domain_mode: str = "algebra",
        experiment_id: str = "default",
    ) -> TargetEffortRecord:
        """Record or update cumulative exploration effort for an attempted mathematical target space."""
        from evolutionary_math.utils.formatting import format_clean_target, format_clean_formula

        t_str = str(target)
        c_target = format_clean_target(target)
        now = time.time()

        is_solved = getattr(result, "success", False) or self.is_target_solved(target)
        status = "SOLVED" if is_solved else "UNSOLVED"

        if hasattr(result, "best_candidate_str") and not hasattr(result, "telemetry_history"):
            # Direct DiscoveryTelemetry object
            generations = getattr(result, "generation", 0)
            time_sec = getattr(result, "elapsed_time_sec", 0.0)
            advisory_count = 1 if getattr(result, "advisory_intervention", None) else 0
            evaluations = getattr(result, "total_individuals_evaluated", generations * 160)
            best_val = getattr(result, "best_validity", 0.0)
            best_cand = getattr(result, "best_candidate_str", None)
        else:
            # EngineRunResult object
            generations = getattr(result, "total_generations", 0)
            time_sec = getattr(result, "total_time_sec", 0.0)
            advisory_count = getattr(result, "advisory_interventions_count", 0)

            telemetry = getattr(result, "telemetry_history", [])
            if telemetry:
                evaluations = sum(t.total_individuals_evaluated for t in telemetry)
                best_telem = max(telemetry, key=lambda t: t.best_validity)
                best_val = best_telem.best_validity
                best_cand = best_telem.best_candidate_str
            else:
                evaluations = generations * 40 * 3
                best_val = 1.0 if is_solved else 0.0
                th = getattr(result, "discovered_theorem", None)
                best_cand = th.discovery_str if th else None

        best_clean = format_clean_formula(best_cand) if best_cand else None
        fail_reason = "Formally verified" if is_solved else f"Reached generation limit ({generations}) without formal proof"

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM target_registry WHERE target_str = ?", (t_str,))
        existing = cursor.fetchone()

        if existing:
            new_attempts = existing["attempts_count"] + 1
            new_gens = existing["total_generations"] + generations
            new_evals = existing["total_evaluations"] + evaluations
            new_time = existing["total_time_sec"] + time_sec
            new_advisory = existing["advisory_interventions_count"] + advisory_count

            if best_val >= existing["best_validity"]:
                final_val = best_val
                final_cand = best_cand
                final_clean = best_clean
                final_fail = fail_reason
            else:
                final_val = existing["best_validity"]
                final_cand = existing["best_candidate_str"]
                final_clean = existing["best_clean_formula"]
                final_fail = existing["failure_reason"]

            final_status = "SOLVED" if (existing["status"] == "SOLVED" or is_solved) else "UNSOLVED"

            with self.conn:
                self.conn.execute("""
                    UPDATE target_registry
                    SET status = ?, attempts_count = ?, total_generations = ?, total_evaluations = ?,
                        total_time_sec = ?, best_validity = ?, best_candidate_str = ?, best_clean_formula = ?,
                        failure_reason = ?, advisory_interventions_count = ?, last_attempted = ?, last_experiment_id = ?
                    WHERE target_str = ?
                """, (
                    final_status, new_attempts, new_gens, new_evals, new_time,
                    final_val, final_cand, final_clean, final_fail, new_advisory,
                    now, experiment_id, t_str
                ))
            first_att = existing["first_attempted"]
        else:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO target_registry
                    (target_str, clean_target, domain_mode, status, attempts_count, total_generations,
                     total_evaluations, total_time_sec, best_validity, best_candidate_str, best_clean_formula,
                     failure_reason, advisory_interventions_count, first_attempted, last_attempted, last_experiment_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    t_str, c_target, domain_mode, status, 1, generations,
                    evaluations, time_sec, best_val, best_cand, best_clean,
                    fail_reason, advisory_count, now, now, experiment_id
                ))
            first_att = now
            final_status = status
            new_attempts = 1
            new_gens = generations
            new_evals = evaluations
            new_time = time_sec
            final_val = best_val
            final_cand = best_cand
            final_clean = best_clean
            final_fail = fail_reason
            new_advisory = advisory_count

        return TargetEffortRecord(
            target_str=t_str,
            clean_target=c_target,
            domain_mode=domain_mode,
            status=final_status,
            attempts_count=new_attempts,
            total_generations=new_gens,
            total_evaluations=new_evals,
            total_time_sec=new_time,
            best_validity=final_val,
            best_candidate_str=final_cand,
            best_clean_formula=final_clean,
            failure_reason=final_fail,
            advisory_interventions_count=new_advisory,
            first_attempted=first_att,
            last_attempted=now,
            last_experiment_id=experiment_id,
        )

    def sync_target_registry_from_history(self) -> int:
        """Backfill target_registry from historical search_history and verified theorems."""
        from evolutionary_math.utils.formatting import format_clean_target, format_clean_formula

        cursor = self.conn.cursor()

        # 1. Sync all solved theorems
        cursor.execute("SELECT target_str, clean_target, generation, timestamp, experiment_id FROM theorems")
        solved_rows = cursor.fetchall()
        for r in solved_rows:
            t_str = r["target_str"]
            c_target = r["clean_target"] or format_clean_target(t_str)
            mode = "trigonometry" if any(w in t_str for w in ["sin", "cos", "tan"]) else ("geometry" if any(w in t_str for w in ["sqrt", "a", "b"]) else "algebra")
            cursor.execute("SELECT 1 FROM target_registry WHERE target_str = ?", (t_str,))
            if cursor.fetchone():
                with self.conn:
                    self.conn.execute("UPDATE target_registry SET status = 'SOLVED', best_validity = 1.0, failure_reason = 'Formally verified' WHERE target_str = ?", (t_str,))
            else:
                with self.conn:
                    self.conn.execute("""
                        INSERT INTO target_registry
                        (target_str, clean_target, domain_mode, status, attempts_count, total_generations,
                         total_evaluations, total_time_sec, best_validity, best_candidate_str, best_clean_formula,
                         failure_reason, advisory_interventions_count, first_attempted, last_attempted, last_experiment_id)
                        VALUES (?, ?, ?, 'SOLVED', 1, ?, ?, ?, 1.0, ?, ?, 'Formally verified', 0, ?, ?, ?)
                    """, (
                        t_str, c_target, mode, r["generation"], r["generation"] * 160,
                        float(r["generation"]) * 0.05, c_target, c_target,
                        r["timestamp"] or time.time(), r["timestamp"] or time.time(), r["experiment_id"]
                    ))

        # 2. Sync all historical search targets from search_history
        cursor.execute("""
            SELECT 
                target_str,
                COUNT(DISTINCT experiment_id) AS attempts,
                MAX(generation) AS max_gen,
                MAX(validity) AS max_val,
                MIN(timestamp) AS min_ts,
                MAX(timestamp) AS max_ts,
                experiment_id
            FROM search_history
            GROUP BY target_str
        """)
        hist_rows = cursor.fetchall()
        synced_count = 0

        for r in hist_rows:
            t_str = r["target_str"]
            c_target = format_clean_target(t_str)
            mode = "trigonometry" if any(w in t_str for w in ["sin", "cos", "tan"]) else ("geometry" if any(w in t_str for w in ["sqrt", "a", "b"]) else "algebra")

            # Find best candidate and failure reason from search_history
            cursor.execute("""
                SELECT candidate_str, clean_formula, reason, status
                FROM search_history
                WHERE target_str = ? AND validity = ?
                LIMIT 1
            """, (t_str, r["max_val"]))
            best_row = cursor.fetchone()
            best_cand = best_row["candidate_str"] if best_row else None
            best_clean = (best_row["clean_formula"] if best_row else None) or (format_clean_formula(best_cand) if best_cand else None)
            reason = (best_row["reason"] if best_row else None) or f"Falsified (highest validity: {r['max_val']:.4f})"

            is_solved = self.is_target_solved(t_str)
            if best_row and (
                "formally proven" in (best_row["reason"] or "").lower()
                or "subsumed" in (best_row["reason"] or "").lower()
                or (best_row["status"] or "") == "breakthrough"
            ):
                is_solved = True

            status = "SOLVED" if is_solved else "UNSOLVED"

            cursor.execute("SELECT 1 FROM target_registry WHERE target_str = ?", (t_str,))
            if cursor.fetchone():
                if is_solved:
                    with self.conn:
                        self.conn.execute("""
                            UPDATE target_registry 
                            SET status = 'SOLVED', best_validity = 1.0, failure_reason = ? 
                            WHERE target_str = ?
                        """, (reason, t_str))
                continue

            max_gen = r["max_gen"] or 50
            evals = max_gen * 160 * max(1, r["attempts"])
            time_est = max_gen * 0.04 * max(1, r["attempts"])

            with self.conn:
                self.conn.execute("""
                    INSERT INTO target_registry
                    (target_str, clean_target, domain_mode, status, attempts_count, total_generations,
                     total_evaluations, total_time_sec, best_validity, best_candidate_str, best_clean_formula,
                     failure_reason, advisory_interventions_count, first_attempted, last_attempted, last_experiment_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                """, (
                    t_str, c_target, mode, status, max(1, r["attempts"]), max_gen,
                    evals, time_est, r["max_val"], best_cand, best_clean,
                    reason, r["min_ts"] or time.time(), r["max_ts"] or time.time(), r["experiment_id"]
                ))
            synced_count += 1

        return synced_count

    def get_unsolved_targets(
        self,
        domain_mode: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TargetEffortRecord]:
        """Retrieve all unsolved target problem spaces ordered by best validity and effort."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM target_registry WHERE status = 'UNSOLVED'"
        params: List[Any] = []
        if domain_mode:
            query += " AND domain_mode = ?"
            params.append(domain_mode.lower())
        query += " ORDER BY best_validity DESC, total_evaluations DESC"
        if limit:
            query += f" LIMIT {int(limit)}"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_target_record(r) for r in rows]

    def get_all_target_records(
        self,
        domain_mode: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TargetEffortRecord]:
        """Retrieve all registered target spaces (both solved and unsolved)."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM target_registry"
        clauses = []
        params: List[Any] = []
        if domain_mode:
            clauses.append("domain_mode = ?")
            params.append(domain_mode.lower())
        if status:
            clauses.append("status = ?")
            params.append(status.upper())
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY status ASC, best_validity DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [self._row_to_target_record(r) for r in rows]

    def get_target_effort(self, target_str: str) -> Optional[TargetEffortRecord]:
        """Retrieve effort record for a specific target string."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM target_registry WHERE target_str = ?", (str(target_str),))
        row = cursor.fetchone()
        return self._row_to_target_record(row) if row else None

    def _row_to_target_record(self, r: sqlite3.Row) -> TargetEffortRecord:
        return TargetEffortRecord(
            target_str=r["target_str"],
            clean_target=r["clean_target"],
            domain_mode=r["domain_mode"],
            status=r["status"],
            attempts_count=r["attempts_count"],
            total_generations=r["total_generations"],
            total_evaluations=r["total_evaluations"],
            total_time_sec=r["total_time_sec"],
            best_validity=r["best_validity"],
            best_candidate_str=r["best_candidate_str"],
            best_clean_formula=r["best_clean_formula"],
            failure_reason=r["failure_reason"],
            advisory_interventions_count=r["advisory_interventions_count"],
            first_attempted=r["first_attempted"],
            last_attempted=r["last_attempted"],
            last_experiment_id=r["last_experiment_id"],
        )

    def save_checkpoint(
        self,
        checkpoint_key: str,
        target_str: str,
        clean_target: str,
        domain_mode: str,
        current_generation: int,
        max_generations: int,
        experiment_id: str,
        islands_data: List[Dict[str, Any]],
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist in-flight population and search state to checkpoints table."""
        now = time.time()
        islands_json = json.dumps(islands_data)
        meta_json = json.dumps(meta or {})
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO checkpoints
                (checkpoint_key, target_str, clean_target, domain_mode, current_generation, max_generations, experiment_id, islands_data, meta_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint_key, target_str, clean_target, domain_mode,
                current_generation, max_generations, experiment_id,
                islands_json, meta_json, now
            ))

    def load_checkpoint(self, checkpoint_key: str) -> Optional[Dict[str, Any]]:
        """Load in-flight checkpoint state by key."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM checkpoints WHERE checkpoint_key = ?", (checkpoint_key,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "checkpoint_key": row["checkpoint_key"],
            "target_str": row["target_str"],
            "clean_target": row["clean_target"],
            "domain_mode": row["domain_mode"],
            "current_generation": row["current_generation"],
            "max_generations": row["max_generations"],
            "experiment_id": row["experiment_id"],
            "islands_data": json.loads(row["islands_data"]),
            "meta": json.loads(row["meta_json"]) if row["meta_json"] else {},
            "timestamp": row["timestamp"],
        }

    def delete_checkpoint(self, checkpoint_key: str) -> bool:
        """Remove a checkpoint (e.g. after successful proof)."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE checkpoint_key = ?", (checkpoint_key,))
            return cursor.rowcount > 0

    def has_checkpoint(self, checkpoint_key: str) -> bool:
        """Check if a checkpoint exists for the specified key."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM checkpoints WHERE checkpoint_key = ? LIMIT 1", (checkpoint_key,))
        return cursor.fetchone() is not None

    def clear_all_checkpoints(self) -> int:
        """Clear all stored checkpoints."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM checkpoints")
            return cursor.rowcount

    def enrich_all_theorems(self, force: bool = False) -> int:
        """Backfill existing database records with human-readable names, clean notation, expanded polynomials, and explanations."""
        from evolutionary_math.advisory.client import MockAdvisoryClient
        from evolutionary_math.utils.formatting import (
            infer_theorem_name,
            format_clean_target,
            format_clean_formula,
            format_expanded_formula,
            format_complete_latex,
        )

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, target_str, discovery_str, ast_json, name, clean_target, clean_formula, expanded_formula, latex, explanation, proof_method, dependencies_json FROM theorems")
        rows = cursor.fetchall()
        updated_count = 0
        mock_client = MockAdvisoryClient()

        for r in rows:
            needs_update = force
            th_id = r["id"]
            target_str = r["target_str"]
            discovery_str = r["discovery_str"]
            ast_dict = json.loads(r["ast_json"]) if r["ast_json"] else None
            def_ast = expr_from_dict(ast_dict) if ast_dict else None
            deps = json.loads(r["dependencies_json"]) if r["dependencies_json"] else []

            name = r["name"]
            inferred_name = infer_theorem_name(target_str, discovery_str)
            if not name or name != inferred_name or force:
                name = inferred_name
                needs_update = True

            clean_target = r["clean_target"]
            inferred_target = format_clean_target(target_str)
            if not clean_target or clean_target != inferred_target or force:
                clean_target = inferred_target
                needs_update = True

            clean_formula = r["clean_formula"]
            inferred_formula = format_clean_formula(def_ast or discovery_str)
            if not clean_formula or clean_formula != inferred_formula or force:
                clean_formula = inferred_formula
                needs_update = True

            expanded_formula = r["expanded_formula"]
            inferred_expanded = format_expanded_formula(def_ast or discovery_str)
            if not expanded_formula or expanded_formula != inferred_expanded or force:
                expanded_formula = inferred_expanded
                needs_update = True

            latex_str = r["latex"]
            inferred_latex = format_complete_latex(target_str, def_ast or discovery_str)
            if not latex_str or latex_str != inferred_latex or needs_update:
                latex_str = inferred_latex
                needs_update = True

            explanation = r["explanation"]
            if not explanation or needs_update or "sum_k=1..n" in explanation or "(((" in explanation:
                explanation = mock_client.explain_discovery(
                    target_str=target_str,
                    discovery_str=clean_formula,
                    latex_str=latex_str,
                    proof_method=r["proof_method"],
                    dependencies=deps,
                )
                needs_update = True

            if needs_update:
                with self.conn:
                    self.conn.execute("""
                        UPDATE theorems 
                        SET name = ?, clean_target = ?, clean_formula = ?, expanded_formula = ?, latex = ?, explanation = ?
                        WHERE id = ?
                    """, (name, clean_target, clean_formula, expanded_formula, latex_str, explanation, th_id))
                updated_count += 1

        return updated_count

    def store_discovery(
        self,
        individual: "Individual",
        target_lhs: ExprNode,
        experiment_id: str = "default",
        explanation: Optional[str] = None,
    ) -> StoredTheorem:
        """Store a formally verified discovery with its full AST definition, dependencies, and explanation."""
        if not individual.is_verified or individual.evaluation_result is None:
            raise ValueError("Only mathematically verified individuals can be stored as theorems.")

        from evolutionary_math.utils.formatting import (
            infer_theorem_name,
            format_clean_target,
            format_clean_formula,
            format_expanded_formula,
            format_complete_latex,
        )

        canon_expr = canonicalize(individual.candidate)
        proof_method = individual.evaluation_result.proof_method or "unknown"
        ast_dict = canon_expr.to_dict()

        # Identify parameter variables (free variables beyond bound indices)
        from evolutionary_math.core.generalization import identify_parameter_variables
        param_vars = identify_parameter_variables(target_lhs)
        is_gen = len(param_vars) > 0

        # Extract dependency IDs from the canonicalized expression (eliminating dead introns)
        deps = self._extract_dependencies(canon_expr)

        target_str = str(target_lhs)
        discovery_str = str(canon_expr)
        name = infer_theorem_name(target_str, discovery_str)
        clean_target = format_clean_target(target_lhs)
        clean_formula = format_clean_formula(canon_expr)
        expanded_formula = format_expanded_formula(canon_expr)
        latex_str = format_complete_latex(target_lhs, canon_expr)

        if not explanation:
            from evolutionary_math.advisory.client import MockAdvisoryClient
            explanation = MockAdvisoryClient().explain_discovery(
                target_str=target_str,
                discovery_str=clean_formula,
                latex_str=latex_str,
                proof_method=proof_method,
                dependencies=list(deps),
            )

        theorem = StoredTheorem(
            id=individual.id,
            target_str=target_str,
            discovery_str=discovery_str,
            sexpr=canon_expr.to_sexpr(),
            proof_method=proof_method,
            generation=individual.generation,
            timestamp=time.time(),
            experiment_id=experiment_id,
            ast_dict=ast_dict,
            definition_ast=canon_expr,
            dependency_ids=list(deps),
            explanation=explanation,
            name=name,
            clean_target=clean_target,
            clean_formula=clean_formula,
            expanded_formula=expanded_formula,
            latex=latex_str,
            is_generalized=is_gen,
            parameter_vars=param_vars,
        )

        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO theorems 
                (id, target_str, discovery_str, sexpr, canonical_sexpr, proof_method, generation, timestamp, experiment_id, ast_json, dependencies_json, explanation, name, clean_target, clean_formula, expanded_formula, latex, is_generalized, parameter_vars)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    theorem.id,
                    theorem.target_str,
                    theorem.discovery_str,
                    theorem.sexpr,
                    canon_expr.to_sexpr(),
                    theorem.proof_method,
                    theorem.generation,
                    theorem.timestamp,
                    theorem.experiment_id,
                    json.dumps(ast_dict),
                    json.dumps(theorem.dependency_ids),
                    theorem.explanation,
                    theorem.name,
                    theorem.clean_target,
                    theorem.clean_formula,
                    theorem.expanded_formula,
                    theorem.latex,
                    1 if is_gen else 0,
                    json.dumps(param_vars),
                ),
            )
        return theorem

    def get_all_theorems(self) -> List[StoredTheorem]:
        """Retrieve all verified discoveries."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, target_str, discovery_str, sexpr, proof_method, generation, timestamp, experiment_id, ast_json, dependencies_json, explanation, name, clean_target, clean_formula, expanded_formula, latex, is_generalized, parameter_vars FROM theorems")
        rows = cursor.fetchall()
        theorems: List[StoredTheorem] = []
        for r in rows:
            ast_dict = json.loads(r["ast_json"]) if r["ast_json"] else None
            deps = json.loads(r["dependencies_json"]) if r["dependencies_json"] else []
            def_ast = expr_from_dict(ast_dict) if ast_dict else None
            is_gen = bool(r["is_generalized"]) if "is_generalized" in r.keys() else False
            param_vars = json.loads(r["parameter_vars"]) if "parameter_vars" in r.keys() and r["parameter_vars"] else []
            theorems.append(
                StoredTheorem(
                    id=r["id"],
                    target_str=r["target_str"],
                    discovery_str=r["discovery_str"],
                    sexpr=r["sexpr"],
                    proof_method=r["proof_method"],
                    generation=r["generation"],
                    timestamp=r["timestamp"],
                    experiment_id=r["experiment_id"],
                    ast_dict=ast_dict,
                    definition_ast=def_ast,
                    dependency_ids=deps,
                    explanation=r["explanation"],
                    name=r["name"],
                    clean_target=r["clean_target"],
                    clean_formula=r["clean_formula"],
                    expanded_formula=r["expanded_formula"],
                    latex=r["latex"],
                    is_generalized=is_gen,
                    parameter_vars=param_vars,
                )
            )
        return theorems

    def promote_lemmas_to_grammar(self, grammar: Grammar, top_k: int = 3, weight: float = 2.0) -> List[str]:
        """Load stored theorems and promote them as active Automatically Defined Functions (ADFs) in grammar."""
        theorems = self.get_all_theorems()
        promoted_ids: List[str] = []

        for th in theorems[:top_k]:
            if th.definition_ast is not None:
                lemma_name = f"L_{th.id[:4]}"
                grammar.promote_lemma(lemma_name, th.definition_ast, weight=weight)
                promoted_ids.append(lemma_name)

        return promoted_ids

    def _extract_dependencies(self, node: ExprNode) -> Set[str]:
        deps: Set[str] = set()
        if isinstance(node, LemmaNode):
            deps.add(node.lemma_id)
        for c in node.children:
            deps.update(self._extract_dependencies(c))
        return deps

    def is_known(self, candidate: ExprNode) -> bool:
        """Check if an expression is already in the knowledge base in canonical form."""
        canon = canonicalize(candidate).to_sexpr()
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM theorems WHERE canonical_sexpr = ? LIMIT 1", (canon,))
        return cursor.fetchone() is not None

    def is_target_solved(self, target_lhs: Union[ExprNode, str]) -> bool:
        """Check if a target problem space has already been solved or is subsumed by a generalized theorem."""
        target_str = str(target_lhs)
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM theorems WHERE target_str = ? OR clean_target = ? LIMIT 1", (target_str, target_str))
        if cursor.fetchone() is not None:
            return True

        # Check subsumption against all stored generalized meta-theorems
        try:
            from evolutionary_math.core.ast import parse_expr_str
            ast_node = target_lhs if isinstance(target_lhs, ExprNode) else parse_expr_str(target_str)
            if self.find_subsuming_theorem(ast_node) is not None:
                return True
        except Exception:
            pass

        return False

    def find_subsuming_theorem(self, target_lhs: ExprNode) -> Optional[Tuple[StoredTheorem, Dict[str, Any]]]:
        """Find an existing generalized theorem that subsumes target_lhs as a concrete instance."""
        from evolutionary_math.core.generalization import find_subsumption_match
        from evolutionary_math.core.ast import parse_expr_str

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, target_str, parameter_vars FROM theorems WHERE is_generalized = 1")
        rows = cursor.fetchall()

        for r in rows:
            param_vars = json.loads(r["parameter_vars"]) if r["parameter_vars"] else []
            if not param_vars:
                continue
            try:
                gen_target = parse_expr_str(r["target_str"])
                sub_match = find_subsumption_match(target_lhs, gen_target, param_vars)
                if sub_match is not None:
                    all_theorems = self.get_all_theorems()
                    th = next((t for t in all_theorems if t.id == r["id"]), None)
                    if th:
                        return th, sub_match
            except Exception:
                continue
        return None

    def consolidate_parametric_families(self) -> int:
        """Scan knowledge base, detect clusters of concrete theorems in the same family,
        prove and insert the generalized meta-theorem, and prune redundant concrete iterations."""
        from evolutionary_math.core.generalization import extract_parametric_family
        from evolutionary_math.core.ast import parse_expr_str
        from evolutionary_math.evolution.rational_solver import ExactPolynomialSolver
        from evolutionary_math.evaluation.tier2_symbolic import Tier2SymbolicVerifier
        from evolutionary_math.evolution.individual import Individual

        theorems = self.get_all_theorems()
        # Group concrete theorems by parametric family
        family_map: Dict[str, List[StoredTheorem]] = {}
        for th in theorems:
            try:
                tgt = parse_expr_str(th.target_str)
                family_info = extract_parametric_family(tgt)
                if family_info:
                    gen_tgt, param_name, c_val = family_info
                    gen_key = str(gen_tgt)
                    if gen_key not in family_map:
                        family_map[gen_key] = []
                    family_map[gen_key].append(th)
            except Exception:
                continue

        consolidated_count = 0
        for gen_key, member_theorems in family_map.items():
            if len(member_theorems) >= 2:
                gen_tgt = parse_expr_str(gen_key)
                solutions = ExactPolynomialSolver.solve(gen_tgt)
                if solutions:
                    gen_formula = solutions[0]
                    verifier = Tier2SymbolicVerifier(induction_variable="n")
                    res = verifier.verify(gen_tgt, gen_formula)
                    if res.is_verified:
                        ind = Individual(candidate=gen_formula, generation=0)
                        ind.evaluation_result = res
                        # Store generalized master theorem
                        self.store_discovery(
                            individual=ind,
                            target_lhs=gen_tgt,
                            experiment_id="consolidation",
                        )
                        # Purge redundant concrete iterations
                        member_ids = [t.id for t in member_theorems]
                        with self.conn:
                            for mid in member_ids:
                                self.conn.execute("DELETE FROM theorems WHERE id = ?", (mid,))
                                self.conn.execute("DELETE FROM search_history WHERE id = ? OR target_str = ?", (mid, mid))
                        consolidated_count += len(member_theorems)

        return consolidated_count

    def close(self) -> None:
        self.conn.close()


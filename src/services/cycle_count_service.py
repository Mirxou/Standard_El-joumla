from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class CycleCountPlan:
    id: int
    name: str
    frequency: str
    strategy: str
    locations: Optional[str]
    start_date: Optional[str]
    enabled: int


@dataclass
class CycleCountSession:
    id: int
    plan_id: int
    location_id: Optional[int]
    started_at: str
    closed_at: Optional[str]
    counted_by: Optional[str]
    status: str


class CycleCountService:
    """
    Cycle Count business logic over the migration 012 tables.

    Tables expected (from migration 012):
      - cycle_count_plans(id, name, frequency, strategy, locations, start_date, enabled, created_at, updated_at)
      - cycle_count_sessions(id, plan_id, location_id, started_at, closed_at, counted_by, status, accuracy, variance_qty, variance_value)
      - cycle_count_items(id, session_id, product_id, location_id, expected_qty, counted_qty, variance_qty, unit_cost, variance_value, reason_id, notes)
      - variance_reasons(id, code, name, description, is_active)
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # Plans
    def create_plan(
        self,
        name: str,
        *,
        frequency: str = "monthly",
        strategy: str = "abc",
        locations: Optional[str] = None,
        start_date: Optional[str] = None,
        enabled: bool = True,
    ) -> int:
        with self._conn() as cx:
            cur = cx.execute(
                """
                INSERT INTO cycle_count_plans(name, frequency, strategy, locations, start_date, enabled, created_at, updated_at)
                VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
                """,
                (name, frequency, strategy, locations, start_date, 1 if enabled else 0),
            )
            return int(cur.lastrowid)

    def list_plans(self, *, only_enabled: bool = False) -> List[CycleCountPlan]:
        sql = "SELECT id, name, frequency, strategy, locations, start_date, enabled FROM cycle_count_plans"
        if only_enabled:
            sql += " WHERE enabled = 1"
        sql += " ORDER BY id DESC"
        with self._conn() as cx:
            rows = cx.execute(sql).fetchall()
            return [
                CycleCountPlan(
                    id=row["id"],
                    name=row["name"],
                    frequency=row["frequency"],
                    strategy=row["strategy"],
                    locations=row["locations"],
                    start_date=row["start_date"],
                    enabled=row["enabled"],
                )
                for row in rows
            ]

    # Sessions
    def start_session(
        self,
        plan_id: int,
        *,
        location_id: Optional[int] = None,
        counted_by: Optional[str] = None,
    ) -> int:
        with self._conn() as cx:
            cur = cx.execute(
                """
                INSERT INTO cycle_count_sessions(plan_id, location_id, started_at, counted_by, status)
                VALUES(?,?,?,?, 'open')
                """,
                (plan_id, location_id, datetime.utcnow().isoformat(timespec="seconds"), counted_by),
            )
            return int(cur.lastrowid)

    def close_session(self, session_id: int) -> None:
        with self._conn() as cx:
            cx.execute(
                """
                UPDATE cycle_count_sessions
                SET closed_at = CURRENT_TIMESTAMP,
                    status = 'closed'
                WHERE id = ? AND status <> 'closed'
                """,
                (session_id,),
            )

    # Items
    def add_item_count(
        self,
        session_id: int,
        *,
        product_id: int,
        location_id: Optional[int],
        expected_qty: float,
        counted_qty: float,
        unit_cost: Optional[float] = None,
        reason_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> int:
        with self._conn() as cx:
            cur = cx.execute(
                """
                INSERT INTO cycle_count_items(
                    session_id, product_id, location_id, expected_qty, counted_qty, unit_cost, reason_id, notes
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    session_id,
                    product_id,
                    location_id,
                    float(expected_qty),
                    float(counted_qty),
                    unit_cost,
                    reason_id,
                    notes,
                ),
            )
            return int(cur.lastrowid)

    # Analytics
    def get_session_summary(self, session_id: int) -> Dict[str, Any]:
        """Return aggregated stats for a session. Compatible with views if present."""
        with self._conn() as cx:
            # Totals
            totals = cx.execute(
                """
                SELECT
                    COUNT(*) AS items,
                    SUM(COALESCE(counted_qty,0) - COALESCE(expected_qty,0)) AS variance_qty,
                    SUM(
                        COALESCE((COALESCE(counted_qty,0) - COALESCE(expected_qty,0)) * COALESCE(unit_cost,0), 0)
                    ) AS variance_value
                FROM cycle_count_items
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()

            sess = cx.execute(
                "SELECT id, plan_id, started_at, closed_at, status, counted_by FROM cycle_count_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

            return {
                "session": dict(sess) if sess else None,
                "items": int(totals["items"]) if totals and totals["items"] is not None else 0,
                "variance_qty": float(totals["variance_qty"]) if totals and totals["variance_qty"] is not None else 0.0,
                "variance_value": float(totals["variance_value"]) if totals and totals["variance_value"] is not None else 0.0,
            }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        with self._conn() as cx:
            open_sessions = cx.execute(
                "SELECT COUNT(*) AS c FROM cycle_count_sessions WHERE status = 'open'"
            ).fetchone()["c"]
            recent_closed = cx.execute(
                """
                SELECT COUNT(*) AS c
                FROM cycle_count_sessions
                WHERE status = 'closed' AND closed_at >= datetime('now', '-7 days')
                """
            ).fetchone()["c"]

            totals = cx.execute(
                """
                SELECT
                    SUM(COALESCE(variance_qty, 0)) AS variance_qty,
                    SUM(COALESCE(variance_value, 0)) AS variance_value
                FROM (
                    SELECT
                        (COALESCE(counted_qty,0) - COALESCE(expected_qty,0)) AS variance_qty,
                        (COALESCE(counted_qty,0) - COALESCE(expected_qty,0)) * COALESCE(unit_cost,0) AS variance_value
                    FROM cycle_count_items
                )
                """
            ).fetchone()

            return {
                "open_sessions": int(open_sessions),
                "recent_closed": int(recent_closed),
                "variance_qty": float(totals["variance_qty"]) if totals and totals["variance_qty"] is not None else 0.0,
                "variance_value": float(totals["variance_value"]) if totals and totals["variance_value"] is not None else 0.0,
            }

    # Listings
    def list_sessions(self, limit: int = 200) -> List[Dict[str, Any]]:
        sql = (
            """
            SELECT s.id,
                   s.plan_id,
                   p.name AS plan_name,
                   s.location_id,
                   s.started_at,
                   s.closed_at,
                   s.status,
                   s.accuracy,
                   s.variance_qty,
                   s.variance_value
            FROM cycle_count_sessions s
            LEFT JOIN cycle_count_plans p ON p.id = s.plan_id
            ORDER BY s.id DESC
            LIMIT ?
            """
        )
        with self._conn() as cx:
            rows = cx.execute(sql, (limit,)).fetchall()
            return [dict(r) for r in rows]


__all__ = [
    "CycleCountService",
    "CycleCountPlan",
    "CycleCountSession",
]

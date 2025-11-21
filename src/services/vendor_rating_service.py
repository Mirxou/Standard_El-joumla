#!/usr/bin/env python3
"""
Vendor Rating Service
Aligns with existing supplier_evaluations schema and computes scores/grades.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

from ..core.database_manager import DatabaseManager


@dataclass
class SupplierEvaluation:
    supplier_id: int
    supplier_name: Optional[str] = None
    evaluation_period_start: Optional[str] = None
    evaluation_period_end: Optional[str] = None
    quality_score: float = 0.0
    delivery_score: float = 0.0
    pricing_score: float = 0.0
    communication_score: float = 0.0
    reliability_score: float = 0.0
    total_orders: int = 0
    completed_orders: int = 0
    on_time_deliveries: int = 0
    late_deliveries: int = 0
    rejected_shipments: int = 0
    total_value: float = 0.0
    on_time_delivery_rate: float = 0.0
    quality_acceptance_rate: float = 0.0
    average_lead_time_days: float = 0.0
    overall_score: Optional[float] = None
    grade: Optional[str] = None
    is_approved: bool = True
    is_preferred: bool = False
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    evaluated_by: Optional[int] = None
    evaluation_date: Optional[str] = None


class VendorRatingService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def _compute_overall(self, e: SupplierEvaluation) -> float:
        # Average of five core criteria (1..5)
        total = (
            e.quality_score
            + e.delivery_score
            + e.pricing_score
            + e.communication_score
            + e.reliability_score
        )
        return round(total / 5.0, 2)

    def _grade(self, score: float) -> str:
        if score >= 4.8:
            return "A+"
        if score >= 4.5:
            return "A"
        if score >= 4.0:
            return "B+"
        if score >= 3.5:
            return "B"
        if score >= 3.0:
            return "C"
        if score >= 2.0:
            return "D"
        return "F"

    def create_evaluation(self, e: SupplierEvaluation) -> int:
        """Insert new row into supplier_evaluations and return id."""
        overall = e.overall_score if e.overall_score is not None else self._compute_overall(e)
        grade = e.grade or self._grade(overall)

        con = self.db.connection
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO supplier_evaluations (
                supplier_id, supplier_name,
                evaluation_period_start, evaluation_period_end,
                quality_score, delivery_score, pricing_score, communication_score, reliability_score,
                total_orders, completed_orders, on_time_deliveries, late_deliveries, rejected_shipments, total_value,
                on_time_delivery_rate, quality_acceptance_rate, average_lead_time_days,
                overall_score, grade,
                is_approved, is_preferred, notes, recommendations,
                evaluated_by, evaluation_date
            ) VALUES (
                ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?
            )
            """,
            (
                e.supplier_id, e.supplier_name,
                e.evaluation_period_start, e.evaluation_period_end,
                e.quality_score, e.delivery_score, e.pricing_score, e.communication_score, e.reliability_score,
                e.total_orders, e.completed_orders, e.on_time_deliveries, e.late_deliveries, e.rejected_shipments, e.total_value,
                e.on_time_delivery_rate, e.quality_acceptance_rate, e.average_lead_time_days,
                overall, grade,
                1 if e.is_approved else 0, 1 if e.is_preferred else 0, e.notes, e.recommendations,
                e.evaluated_by, e.evaluation_date,
            ),
        )
        con.commit()
        return cur.lastrowid

    def get_latest_evaluation(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_cursor() as cur:
            cur.execute(
                """
                SELECT * FROM supplier_evaluations
                WHERE supplier_id = ?
                ORDER BY COALESCE(evaluation_date, created_at) DESC, id DESC
                LIMIT 1
                """,
                (supplier_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_supplier_score(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        row = self.get_latest_evaluation(supplier_id)
        if not row:
            return None
        return {"supplier_id": supplier_id, "overall_score": row.get("overall_score"), "grade": row.get("grade")}

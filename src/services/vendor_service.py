#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
خدمة إدارة الموردين (Vendor Service)
تدير سجلات الموردين، أوامر الشراء، واستعراض أداء المورد
"""

import logging
import sqlite3


from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.db_helpers import escape_like_wildcards


class VendorService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def create_vendor(self, vendor_data: Dict[str, Any]) -> Optional[int]:
        try:
            now = datetime.now()
            q = (
                "INSERT INTO suppliers (name, contact_person, phone, email, address, payment_terms, credit_limit, created_at, updated_at) "  # noqa: E501
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            )
            params = (
                vendor_data.get("name"),
                vendor_data.get("contact_person"),
                vendor_data.get("phone"),
                vendor_data.get("email"),
                vendor_data.get("address"),
                vendor_data.get("payment_terms", "cash"),
                float(vendor_data.get("credit_limit") or 0),
                now,
                now,
            )
            return self.db.execute_insert(q, params)
        except (sqlite3.Error, ValueError) as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء مورد: {e}")
        return None  # On error: returns None

    def get_vendor(self, vendor_id: int) -> Optional[Dict[str, Any]]:
        try:
            row = self.db.fetch_one("SELECT * FROM suppliers WHERE id = ?", (vendor_id,))
            return row
        except (sqlite3.Error, ValueError) as e:
            if self.logger:
                self.logger.error(f"خطأ في جلب مورد {vendor_id}: {e}")
            return None  # On error: returns None

    def search_vendors(self, term: str) -> List[Dict[str, Any]]:
        try:
            like = f"%{escape_like_wildcards(term)}%"
            rows = self.db.fetch_all(
                "SELECT * FROM suppliers WHERE name LIKE ? OR contact_person LIKE ? OR phone LIKE ? OR email LIKE ?",
                (like, like, like, like),
            )
            return rows
        except (sqlite3.Error, ValueError) as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث عن موردين: {e}")
            return []  # On error: returns empty list

    def create_purchase_order(
        self, vendor_id: int, items: List[Dict[str, Any]], meta: Dict[str, Any] = None
    ) -> Optional[int]:
        try:
            # EDGE CASE: purchase order with 0 items
            if not items or len(items) == 0:
                if self.logger:
                    self.logger.warning("Cannot create purchase order with 0 items")
                return None

            now = datetime.now()
            total = sum(float(i.get("quantity", 1) or 0) * float(i.get("unit_cost", 0) or 0) for i in items)
            po_number = f"PO-{int(now.timestamp())}"

            # استخدام جدول purchase_orders الصحيح
            q = (
                "INSERT INTO purchase_orders (po_number, supplier_id, status, total_amount, order_date, created_at, updated_at, notes) "  # noqa: E501
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            )
            params = (
                po_number,
                vendor_id,
                "draft",
                total,
                now,
                now,
                now,
                str(meta or {}),
            )

            po_id = self.db.execute_insert(q, params)
            if not po_id:
                return None

            for it in items:
                # استخدام جدول purchase_order_items الصحيح
                q_item = (
                    "INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity_ordered, unit_price, subtotal, created_at) "  # noqa: E501
                    "VALUES (?, ?, ?, ?, ?, ?)"
                )
                qty = float(it.get("quantity", 1) or 0)
                cost = float(it.get("unit_cost", 0) or 0)
                self.db.execute_insert(q_item, (po_id, it.get("product_id"), qty, cost, qty * cost, now))

            if self.logger:
                self.logger.info(f"تم إنشاء أمر شراء {po_number} (ID={po_id}) للمورد {vendor_id}، المجموع={total}")
            return po_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء أمر الشراء: {e}")
            return None

    def receive_purchase(self, purchase_id: int, received_items: List[Dict[str, Any]]) -> bool:
        try:
            # EDGE CASE: purchase receipt with 0 items
            if not received_items or len(received_items) == 0:
                if self.logger:
                    self.logger.warning(f"Cannot receive purchase order {purchase_id} with 0 items")
                return False

            now = datetime.now()

            # EDGE CASE: receiving more than ordered
            for it in received_items:
                pid = it.get("product_id")
                qty = float(it.get("quantity", 1) or 0)
                try:
                    ordered_row = self.db.fetch_one(
                        "SELECT quantity_ordered, quantity_received FROM purchase_order_items "
                        "WHERE purchase_order_id = ? AND product_id = ?",
                        (purchase_id, pid),
                    )
                    if ordered_row:
                        ordered_qty = float(ordered_row.get("quantity_ordered") or 0)
                        already_received = float(ordered_row.get("quantity_received") or 0)
                        if qty + already_received > ordered_qty:
                            if self.logger:
                                self.logger.warning(
                                    f"Over-receipt for product {pid} in PO {purchase_id}: "
                                    f"ordered={ordered_qty}, already_received={already_received}, "
                                    f"this_receipt={qty}. Capping at remaining."
                                )
                            # Cap received qty at remaining ordered
                            qty = max(0, ordered_qty - already_received)
                            it["quantity"] = qty
                except Exception:
                    pass  # If check fails, proceed with original qty

            # تحديث حالة أمر الشراء في purchase_orders
            self.db.execute_non_query(
                "UPDATE purchase_orders SET status = ?, delivery_date = ?, updated_at = ? WHERE id = ?",
                ("received", now, now, purchase_id),
            )

            for it in received_items:
                # تحديث الكمية المستلمة في purchase_order_items
                pid = it.get("product_id")
                qty = float(it.get("quantity", 1) or 0)
                self.db.execute_non_query(
                    "UPDATE purchase_order_items SET quantity_received = ?, actual_delivery_date = ? WHERE purchase_order_id = ? AND product_id = ?",  # noqa: E501
                    (qty, now, purchase_id, pid),
                )

                # تسجيل حركة مخزون
                try:
                    from src.services.inventory_service import InventoryService

                    inv = InventoryService(self.db, self.logger)
                    inv._record_stock_movement(
                        product_id=pid,
                        movement_type="in",
                        quantity=int(qty or 0),
                        reference_id=purchase_id,
                        reference_type="purchase_order",
                    )
                except Exception as inv_err:
                    logging.getLogger(__name__).warning(f"Failed to record stock movement for product {pid}: {inv_err}")

                # ── MOVING AVERAGE / FIFO COSTING ──────────────────────────
                # Update product cost using the configured costing method
                # when receiving purchased items.
                try:
                    from src.services.business_rules_service import CostingService
                    from decimal import Decimal as D

                    cost_price = D(str(it.get("cost_price", 0) or 0))
                    if cost_price > 0:
                        costing = CostingService(self.db, self.logger)
                        costing.on_purchase(
                            product_id=pid,
                            quantity=D(str(qty)),
                            unit_cost=cost_price,
                            purchase_id=purchase_id,
                        )
                except Exception as costing_err:
                    logging.getLogger(__name__).warning(
                        "Costing update failed for product %d: %s", pid, costing_err
                    )

            if self.logger:
                self.logger.info(f"تم استلام أمر الشراء {purchase_id}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في استلام أمر الشراء {purchase_id}: {e}")
            return False

    def calculate_quality_score(self, vendor_id: int) -> float:
        """حساب درجة الجودة للمورد (0-100) بناءً على الوقت والكمية"""
        try:
            # 1. نسبة التسليم في الموعد (40%)
            # استخدام purchase_orders
            q_total = 'SELECT COUNT(*) as cnt FROM purchase_orders WHERE supplier_id = ? AND status = "received"'
            row = self.db.fetch_one(q_total, (vendor_id,))
            total_orders = int(row.get("cnt", 0) or 0) if row else 0

            if total_orders == 0:
                return 50.0

            # مقارنة delivery_date بـ expected_delivery_date
            q_on_time = 'SELECT COUNT(*) as cnt FROM purchase_orders WHERE supplier_id = ? AND status = "received" AND (expected_delivery_date IS NULL OR julianday(delivery_date) <= julianday(expected_delivery_date))'  # noqa: E501
            row = self.db.fetch_one(q_on_time, (vendor_id,))
            on_time_count = int(row.get("cnt", 0) or 0) if row else 0
            on_time_score = (on_time_count / total_orders) * 100

            # 2. دقة الكميات (30%)
            fulfillment_score = 100.0

            # 3. سرعة التوريد (30%)
            q_avg_days = 'SELECT AVG(julianday(delivery_date) - julianday(order_date)) as avg_lead FROM purchase_orders WHERE supplier_id = ? AND status = "received"'  # noqa: E501
            _r = self.db.fetch_one(q_avg_days, (vendor_id,))
            avg_days = float(_r.get("avg_lead", 7) or 7) if _r else 7.0
            lead_time_score = max(0, 100 - (avg_days * 5))

            final_score = (on_time_score * 0.4) + (fulfillment_score * 0.3) + (lead_time_score * 0.3)
            return round(final_score, 2)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب جودة المورد {vendor_id}: {e}")
            return 0.0

    def generate_demand_plan(self, ai_service, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """إنشاء خطة طلب بناءً على تنبؤات الذكاء الاصطناعي"""
        plan = []
        try:
            products = self.db.fetch_all(
                "SELECT id, name, current_stock, min_stock FROM products"
            )  # min_stock instead of reorder_level
            for p in products:
                pid = p["id"]
                name = p["name"]
                stock = p["current_stock"]
                min_stock = p["min_stock"]
                stock = stock or 0
                min_stock = min_stock or 0

                forecast = ai_service.demand_forecast_linear_regression(pid, days=60, forecast_days=days_ahead)
                total_predicted_demand = sum(f["predicted_quantity"] for f in forecast)

                projected_stock = stock - total_predicted_demand

                if projected_stock < min_stock:
                    suggested_qty = (min_stock + total_predicted_demand) - stock

                    # البحث عن أفضل مورد من تاريخ أوامر الشراء
                    # product_suppliers غير موجود، نستخدم purchase_order_items
                    q_vendor = """
                        SELECT po.supplier_id, poi.unit_price
                        FROM purchase_order_items poi
                        JOIN purchase_orders po ON poi.purchase_order_id = po.id
                        WHERE poi.product_id = ?
                        ORDER BY poi.created_at DESC
                        LIMIT 1
                    """
                    best_vendor = self.db.fetch_one(q_vendor, (pid,))

                    vendor_id = best_vendor["supplier_id"] if best_vendor else None
                    est_cost = best_vendor["unit_price"] if best_vendor else 0

                    plan.append(
                        {
                            "product_id": pid,
                            "product_name": name,
                            "current_stock": stock,
                            "predicted_demand": total_predicted_demand,
                            "suggested_quantity": max(1, round(suggested_qty)),
                            "suggested_vendor_id": vendor_id,
                            "estimated_unit_cost": est_cost,
                            "reason": f"توقعات الذكاء الاصطناعي تشير لطلب {total_predicted_demand} وحدة",
                        }
                    )
            return plan
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء خطة الطلب: {e}")
            return []

    def cancel_purchase_order(self, purchase_id: int) -> bool:
        """Cancel a purchase order.

        EDGE CASE: cancelling a partially received PO — only allow if no items received.
        """
        try:
            # Check current status
            po_row = self.db.fetch_one(
                "SELECT status FROM purchase_orders WHERE id = ?",
                (purchase_id,),
            )
            if not po_row:
                if self.logger:
                    self.logger.warning(f"Purchase order {purchase_id} not found for cancellation")
                return False

            po_status = po_row.get("status")
            if po_status == "cancelled":
                if self.logger:
                    self.logger.warning(f"Purchase order {purchase_id} is already cancelled")
                return False

            # EDGE CASE: partially received PO — reject cancellation
            received_row = self.db.fetch_one(
                "SELECT SUM(quantity_received) as total_received FROM purchase_order_items "
                "WHERE purchase_order_id = ?",
                (purchase_id,),
            )
            total_received = float(received_row.get("total_received", 0) or 0) if received_row else 0
            if total_received > 0:
                if self.logger:
                    self.logger.warning(
                        f"Cannot cancel PO {purchase_id}: {total_received} items already received. "
                        f"Consider returning items instead."
                    )
                return False

            self.db.execute_non_query(
                "UPDATE purchase_orders SET status = ?, updated_at = ? WHERE id = ?",
                ("cancelled", datetime.now(), purchase_id),
            )
            if self.logger:
                self.logger.info(f"Purchase order {purchase_id} cancelled")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إلغاء أمر الشراء {purchase_id}: {e}")
            return False

    def vendor_performance(self, vendor_id: int) -> Dict[str, Any]:
        try:
            # استخدام purchase_orders
            q_avg = 'SELECT AVG(julianday(delivery_date) - julianday(order_date)) as avg_lead FROM purchase_orders WHERE supplier_id = ? AND status = "received"'  # noqa: E501
            _r = self.db.fetch_one(q_avg, (vendor_id,))
            avg_days = float(_r.get("avg_lead", 0) or 0) if _r else 0.0
            q_total = "SELECT COUNT(*) as cnt FROM purchase_orders WHERE supplier_id = ?"
            _r2 = self.db.fetch_one(q_total, (vendor_id,))
            total = int(_r2.get("cnt", 0) or 0) if _r2 else 0
            q_on_time = 'SELECT COUNT(*) as cnt FROM purchase_orders WHERE supplier_id = ? AND status = "received" AND (expected_delivery_date IS NULL OR julianday(delivery_date) <= julianday(expected_delivery_date))'  # noqa: E501
            _r3 = self.db.fetch_one(q_on_time, (vendor_id,))
            on_time = int(_r3.get("cnt", 0) or 0) if _r3 else 0

            quality_score = self.calculate_quality_score(vendor_id)

            return {
                "vendor_id": vendor_id,
                "avg_lead_time_days": float(avg_days),
                "total_orders": int(total or 0),
                "on_time_rate": (int(on_time) / int(total or 0) if total > 0 else 0),
                "quality_score": quality_score,
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب أداء المورد {vendor_id}: {e}")
            return {}

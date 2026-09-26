#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الفوترة والدفع - Billing & Payments Service
توليد الفواتير، تسجيل المدفوعات، وإدارة الفواتير الدورية (Subscriptions)
"""

import logging

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


class BillingService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or logging.getLogger(__name__)

    def generate_invoice(self, sale_id: int, due_days: int = 0) -> Optional[int]:
        try:
            # استرداد بيانات الطلب
            sale = self.db.fetch_one(
                "SELECT id, customer_id, total_amount FROM sales WHERE id = ?",
                (sale_id,),
            )
            if not sale:
                self.logger.warning(f"لم يتم العثور على الطلب {sale_id} عند توليد الفاتورة")
                return None
            total = sale.get("total_amount", sale[2] if not isinstance(sale, dict) else 0)
            customer_id = sale.get("customer_id", sale[1] if not isinstance(sale, dict) else None)
            now = datetime.now()
            due = None
            if due_days and isinstance(due_days, int) and due_days > 0:
                due = now + timedelta(days=due_days)
            q = "INSERT INTO invoices (sale_id, customer_id, amount, status, issued_at, due_at) VALUES (?, ?, ?, ?, ?, ?)"  # noqa: E501
            invoice_id = self.db.execute_insert(q, (sale_id, customer_id, float(total or 0), "unpaid", now, due))

            if invoice_id:
                self.logger.info(f"تم إنشاء فاتورة ID={invoice_id} للطلب {sale_id}")
                return invoice_id
            else:
                self.logger.warning(f"فشل إنشاء الفاتورة للطلب {sale_id}")
                return None
        except Exception as e:
            self.logger.error(f"خطأ في توليد الفاتورة للطلب {sale_id}: {e}")
        return None

    def record_payment(
        self,
        invoice_id: int,
        amount: Decimal,
        method: str = "cash",
        reference: Optional[str] = None,
    ) -> bool:
        try:
            now = datetime.now()
            # Try invoice-oriented payments table first
            try:
                q = "INSERT INTO payments (invoice_id, amount, method, reference, paid_at) VALUES (?, ?, ?, ?, ?)"
                self.db.execute_insert(q, (invoice_id, float(amount or 0), method, reference, now))
            except Exception as e:
                # Fallback to core payments schema (payment_type, entity_id,
                # amount, payment_method, reference_number, payment_date, status,
                # notes, user_id, created_at, updated_at)
                msg = str(e)
                # Check for various "column missing" error messages
                if "no column" in msg or "no such column" in msg:
                    # Use core payment schema - simpler insertion
                    q2 = """INSERT INTO payments
                            (payment_type, entity_id, amount, payment_method,
                             reference_number, payment_date, status,
                             created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    params2 = (
                        "customer_payment",
                        invoice_id,
                        float(amount or 0),
                        method,
                        reference,
                        now,
                        "completed",
                        now,
                        now,
                    )
                    self.db.execute_insert(q2, params2)
                else:
                    raise
            # Update invoice status — handle partial payments properly
            try:
                invoice_row = self.db.fetch_one("SELECT amount, paid_amount FROM invoices WHERE id = ?", (invoice_id,))
                if invoice_row:
                    invoice_amount = float(
                        invoice_row.get("amount", 0) or 0
                    )
                    current_paid = float(invoice_row.get("paid_amount", 0) or 0)
                    new_paid = current_paid + float(amount or 0)

                    # Update paid_amount on the invoice
                    try:
                        self.db.execute_non_query(
                            "UPDATE invoices SET paid_amount = ? WHERE id = ?",
                            (new_paid, invoice_id),
                        )
                    except Exception as e:
                        self.logger.debug(f"paid_amount column not available: {e}")

                    if new_paid >= invoice_amount:
                        self.db.execute_non_query(
                            "UPDATE invoices SET status = ?, paid_at = ? WHERE id = ?",
                            ("paid", now, invoice_id),
                        )
                    elif new_paid > 0:
                        self.db.execute_non_query(
                            "UPDATE invoices SET status = ? WHERE id = ?",
                            ("partially_paid", invoice_id),
                        )
                    self.logger.info(f"تم تسجيل دفعة على الفاتورة {invoice_id} المبلغ: {amount}")
            except Exception as e:
                self.logger.error(f"خطأ عند تحديث حالة الفاتورة {invoice_id} بعد الدفع: {e}")
            return True
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الدفعة للفاتورة {invoice_id}: {e}")
            return False

    def create_recurring_invoice(self, subscription_id: int) -> Optional[int]:
        # تبسيط: إنشاء فاتورة بناءً على إعدادات الاشتراك
        try:
            sub = self.db.fetch_one(
                "SELECT id, customer_id, amount, frequency_days FROM subscriptions WHERE id = ?",
                (subscription_id,),
            )
            if not sub:
                return None
            # توليد فاتورة
            return self.generate_invoice_for_subscription(sub)
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء فاتورة دورية للاشتراك {subscription_id}: {e}")
            return None

    def generate_invoice_for_subscription(self, sub_row) -> Optional[int]:
        try:
            # sub_row: dict with keys (id, customer_id, amount, frequency_days)
            now = datetime.now()
            q = "INSERT INTO invoices (sale_id, customer_id, amount, status, issued_at) VALUES (?, ?, ?, ?, ?)"
            res = self.db.execute_insert(
                q, (None, sub_row.get('customer_id'),
                    float(sub_row.get('amount', 0) or 0), "unpaid", now)
            )
            if res is not None:
                return res
        except Exception as e:
            self.logger.error(f"خطأ في توليد فاتورة للاشتراك: {e}")
        return None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
خدمة المرتجعات - Return Service
تقديم خدمات إدارة مرتجعات المبيعات والمشتريات
"""

import logging


from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.models.return_invoice import (
    RefundMethod,
    ReturnInvoice,
    ReturnItem,
    ReturnReason,
    ReturnStatus,
    ReturnType,
)
from src.utils.db_helpers import get_value
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ReturnService:
    """خدمة إدارة المرتجعات"""

    def __init__(self, db_manager: DatabaseManager):
        """تهيئة خدمة المرتجعات"""
        self.db = db_manager
        logger.info("تم تهيئة خدمة المرتجعات")

    def generate_return_number(self) -> str:
        """توليد رقم مرتجع جديد"""
        try:
            cursor = self.db.connection.cursor()
            today_str = date.today().strftime("%Y%m%d")
            cursor.execute(
                """
                SELECT return_number FROM return_invoices
                WHERE return_number LIKE ?
                ORDER BY id DESC LIMIT 1
            """,
                (f"RET-{today_str}%",),
            )
            result = cursor.fetchone()

            seq = 1
            if result:
                last_number = result[0]
                # استخراج الرقم من النمط RET-YYYYMMDD-XXX
                if "-" in last_number:
                    parts = last_number.split("-")
                    if len(parts) == 3:
                        try:
                            seq = int(parts[2]) + 1
                        except (ValueError, IndexError):
                            seq = 1

            # توليد رقم جديد
            return_number = f"RET-{today_str}-{seq:03d}"

            return return_number
        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في توليد رقم المرتجع: {str(e)}")
            # رقم احتياطي
            return f"RET-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def create_return(self, return_invoice: ReturnInvoice) -> int:
        """إنشاء مرتجع جديد"""
        try:
            # توليد رقم إذا لم يكن موجوداً
            if not return_invoice.return_number:
                return_invoice.return_number = self.generate_return_number()

            # تعيين تاريخ الإرجاع
            if not return_invoice.return_date:
                return_invoice.return_date = date.today()

            # حساب المجاميع
            return_invoice.calculate_totals()

            # الطوابع الزمنية
            return_invoice.created_at = datetime.now()
            return_invoice.updated_at = datetime.now()

            cursor = self.db.connection.cursor()

            # إدراج المرتجع
            # BUGFIX (13c): Match actual DB schema: return_invoices has only
            # (id, original_invoice_id, return_date, reason, total_refund_amount, status).
            cursor.execute(
                """
                INSERT INTO return_invoices (
                    return_number, original_invoice_id, return_date, reason,
                    total_refund_amount, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    return_invoice.return_number,
                    return_invoice.original_sale_id,
                    (return_invoice.return_date.isoformat()
                     if return_invoice.return_date else None),
                    (return_invoice.return_reason.name
                     if isinstance(return_invoice.return_reason, ReturnReason)
                     else str(return_invoice.return_reason or '')),
                    float(return_invoice.total_amount or 0),
                    (return_invoice.status.name
                     if isinstance(return_invoice.status, ReturnStatus)
                     else str(return_invoice.status or 'approved')),
                ),
            )

            return_id = cursor.lastrowid
            return_invoice.id = return_id

            # إدراج البنود
            # BUGFIX (13c): Match actual DB schema: return_items has only
            # (id, return_id, product_id, quantity, refund_price).
            for item in return_invoice.items:
                item.return_id = return_id
                item.calculate_totals()
                cursor.execute(
                    """
                    INSERT INTO return_items (
                        return_id, product_id, quantity, refund_price
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        return_id,
                        item.product_id,
                        float(item.quantity_returned or 0),
                        float(item.unit_price or 0),
                    ),
                )
                item.id = cursor.lastrowid

            self.db.connection.commit()
            logger.info(f"تم إنشاء المرتجع: {return_invoice.return_number}")
            return return_id

        except Exception as e:
            self.db.connection.rollback()
            logger.log(logging.ERROR, f"خطأ في إنشاء المرتجع: {str(e)}")
            raise

    def get_return(self, return_id: int) -> Optional[ReturnInvoice]:
        """الحصول على مرتجع بالمعرف"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT * FROM return_invoices WHERE id = ?", (return_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # تحويل الصف إلى قاموس
            columns = [desc[0] for desc in cursor.description]
            return_data = dict(zip(columns, row))

            # الحصول على البنود
            cursor.execute("SELECT * FROM return_items WHERE return_id = ?", (return_id,))
            items_rows = cursor.fetchall()
            items_columns = [desc[0] for desc in cursor.description]

            items = []
            for item_row in items_rows:
                item_data = dict(zip(items_columns, item_row))
                # تحويل restockable من int إلى bool
                item_data["restockable"] = bool(item_data.get("restockable", 1))
                items.append(ReturnItem.from_dict(item_data))

            return_data["items"] = items
            return_invoice = ReturnInvoice.from_dict(return_data)

            return return_invoice

        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في الحصول على المرتجع {return_id}: {str(e)}")
            return None

    def get_return_by_number(self, return_number: str) -> Optional[ReturnInvoice]:
        """الحصول على مرتجع بالرقم"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "SELECT id FROM return_invoices WHERE return_number = ?",
                (return_number,),
            )
            row = cursor.fetchone()

            if row:
                return self.get_return(get_value(row, 'id'))
            return None

        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في الحصول على المرتجع {return_number}: {str(e)}")
            return None

    def update_return(self, return_invoice: ReturnInvoice) -> bool:
        """تحديث مرتجع"""
        try:
            return_invoice.calculate_totals()
            return_invoice.updated_at = datetime.now()

            cursor = self.db.connection.cursor()

            # تحديث المرتجع
            # BUGFIX (13c): Match actual DB schema: return_invoices has only
            # (id, original_invoice_id, return_date, reason, total_refund_amount, status).
            cursor.execute(
                """
                UPDATE return_invoices SET
                    original_invoice_id = ?,
                    return_date = ?,
                    reason = ?,
                    total_refund_amount = ?,
                    status = ?
                WHERE id = ?
            """,
                (
                    return_invoice.original_sale_id,
                    (return_invoice.return_date.isoformat()
                     if return_invoice.return_date else None),
                    (return_invoice.return_reason.name
                     if isinstance(return_invoice.return_reason, ReturnReason)
                     else str(return_invoice.return_reason or '')),
                    float(return_invoice.total_amount or 0),
                    (return_invoice.status.name
                     if isinstance(return_invoice.status, ReturnStatus)
                     else str(return_invoice.status or 'approved')),
                    return_invoice.id,
                ),
            )

            # حذف البنود القديمة
            cursor.execute("DELETE FROM return_items WHERE return_id = ?", (return_invoice.id,))

            # إدراج البنود الجديدة
            # BUGFIX (13c): Match actual DB schema: return_items has only
            # (id, return_id, product_id, quantity, refund_price).
            for item in return_invoice.items:
                item.return_id = return_invoice.id
                item.calculate_totals()
                cursor.execute(
                    """
                    INSERT INTO return_items (
                        return_id, product_id, quantity, refund_price
                    ) VALUES (?, ?, ?, ?)
                """,
                    (
                        return_invoice.id,
                        item.product_id,
                        float(item.quantity_returned or 0),
                        float(item.unit_price or 0),
                    ),
                )

            self.db.connection.commit()
            logger.info(f"تم تحديث المرتجع: {return_invoice.return_number}")
            return True

        except Exception as e:
            self.db.connection.rollback()
            logger.log(logging.ERROR, f"خطأ في تحديث المرتجع: {str(e)}")
            return False

    def delete_return(self, return_id: int) -> bool:
        """حذف مرتجع مع بنوده"""
        try:
            cursor = self.db.connection.cursor()
            # حذف البنود أولاً
            cursor.execute("DELETE FROM return_items WHERE return_id = ?", (return_id,))
            # ثم حذف المرتجع
            cursor.execute("DELETE FROM return_invoices WHERE id = ?", (return_id,))
            self.db.connection.commit()
            logger.info(f"تم حذف المرتجع {return_id} مع بنوده")
            return True
        except Exception as e:
            self.db.connection.rollback()
            logger.log(logging.ERROR, f"خطأ في حذف المرتجع: {str(e)}")
            return False

    def get_all_returns(
        self,
        return_type: Optional[ReturnType] = None,
        status: Optional[ReturnStatus] = None,
        customer_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[ReturnInvoice]:
        """الحصول على جميع المرتجعات مع فلترة اختيارية"""
        try:
            query = "SELECT * FROM return_invoices WHERE 1=1"
            params = []

            if return_type:
                query += " AND return_type = ?"
                params.append(return_type.name if isinstance(return_type, ReturnType) else return_type)

            if status:
                query += " AND status = ?"
                params.append(status.name if isinstance(status, ReturnStatus) else status)

            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)

            if supplier_id:
                query += " AND supplier_id = ?"
                params.append(supplier_id)

            if from_date:
                query += " AND return_date >= ?"
                params.append(from_date.isoformat())

            if to_date:
                query += " AND return_date <= ?"
                params.append(to_date.isoformat())

            query += " ORDER BY return_date DESC, id DESC"

            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            returns = []
            # BUGFIX (13c): Capture invoice columns BEFORE the loop so that
            # the inner SELECT on return_items does not corrupt cursor.description
            # for the next iteration of the outer loop.
            invoice_columns = [desc[0] for desc in cursor.description]

            for row in rows:
                return_data = dict(zip(invoice_columns, row))

                # الحصول على البنود — use a separate cursor to avoid
                # overwriting the outer cursor's description.
                item_cursor = self.db.connection.cursor()
                item_cursor.execute(
                    "SELECT * FROM return_items WHERE return_id = ?",
                    (return_data.get("id"),),
                )
                items_rows = item_cursor.fetchall()
                items_columns = [desc[0] for desc in item_cursor.description]

                items = []
                for item_row in items_rows:
                    item_data = dict(zip(items_columns, item_row))
                    item_data["restockable"] = bool(item_data.get("restockable", 1))
                    items.append(ReturnItem.from_dict(item_data))

                return_data["items"] = items
                returns.append(ReturnInvoice.from_dict(return_data))

            return returns

        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في الحصول على المرتجعات: {str(e)}")
            # NOTE (13c): The get_all_returns filters reference columns
            # (return_type, customer_id, supplier_id) that do not exist in
            # the current return_invoices schema.  Only status and
            # return_date are valid filters.  A future schema migration
            # should add the missing columns if the rich filtering is
            # needed.
            return []

    def approve_return(self, return_id: int, approved_by: int) -> bool:
        """الموافقة على مرتجع"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.approve(approved_by):
            return self.update_return(return_invoice)
        return False

    def reject_return(self, return_id: int) -> bool:
        """رفض مرتجع"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.reject():
            return self.update_return(return_invoice)
        return False

    def complete_return(self, return_id: int) -> bool:
        """إتمام مرتجع (بعد الاستلام والمعالجة)"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.complete():
            # تحديث المخزون للبنود القابلة لإعادة التخزين
            if return_invoice.is_sale_return:
                for item in return_invoice.restockable_items:
                    self._restock_item(item.product_id, item.quantity_returned)

            return self.update_return(return_invoice)
        return False

    def cancel_return(self, return_id: int) -> bool:
        """إلغاء مرتجع"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.cancel():
            return self.update_return(return_invoice)
        return False

    def process_refund(
        self,
        return_id: int,
        method: RefundMethod,
        amount: Decimal,
        reference: Optional[str] = None,
    ) -> bool:
        """معالجة استرداد المبلغ"""
        return_invoice = self.get_return(return_id)
        if return_invoice:
            return_invoice.process_refund(method, amount, reference)
            return self.update_return(return_invoice)
        return False

    def generate_credit_note(self, return_id: int) -> Optional[str]:
        """إنشاء إشعار دائن للمرتجع"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.status == ReturnStatus.APPROVED:
            # توليد رقم إشعار دائن
            credit_note_number = f"CN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return_invoice.generate_credit_note(credit_note_number)

            if self.update_return(return_invoice):
                logger.info(f"تم إنشاء إشعار دائن: {credit_note_number}")
                return credit_note_number
        return None

    def _restock_item(self, product_id: int, quantity: Decimal) -> bool:
        """إعادة المنتج للمخزون (without commit — caller handles transaction)"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                UPDATE products
                SET current_stock = current_stock + ?
                WHERE id = ?
            """,
                (float(quantity or 0), product_id),
            )
            logger.info(f"تم إعادة {quantity} من المنتج {product_id} للمخزون (بانتظار الالتزام)")
            return True
        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في إعادة المنتج للمخزون: {str(e)}")
            return False

    def get_returns_by_original_sale(self, sale_id: int) -> List[ReturnInvoice]:
        """الحصول على جميع المرتجعات المرتبطة بفاتورة بيع"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                SELECT id FROM return_invoices
                WHERE original_sale_id = ?
                ORDER BY return_date DESC
            """,
                (sale_id,),
            )

            return_ids = [get_value(row, 'id') for row in cursor.fetchall()]
            return [r for rid in return_ids if (r := self.get_return(rid))]

        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في الحصول على مرتجعات البيع: {str(e)}")
            return []

    def get_return_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المرتجعات"""
        try:
            cursor = self.db.connection.cursor()

            stats = {}

            # العدد والقيمة حسب النوع
            cursor.execute("""
                SELECT return_type, COUNT(*) AS cnt, SUM(total_amount) AS total
                FROM return_invoices
                GROUP BY return_type
            """)
            stats["by_type"] = {
                get_value(row, 'return_type'): {
                    "count": get_value(row, 'cnt', 0),
                    "total": get_value(row, 'total', 0) or 0,
                }
                for row in cursor.fetchall()
            }

            # العدد حسب الحالة
            cursor.execute("""
                SELECT status, COUNT(*) AS cnt, SUM(total_amount) AS total
                FROM return_invoices
                GROUP BY status
            """)
            stats["by_status"] = {
                get_value(row, 'status'): {
                    "count": get_value(row, 'cnt', 0),
                    "total": get_value(row, 'total', 0) or 0,
                }
                for row in cursor.fetchall()
            }

            # العدد حسب السبب
            cursor.execute("""
                SELECT return_reason, COUNT(*) AS cnt
                FROM return_invoices
                WHERE return_reason IS NOT NULL
                GROUP BY return_reason
            """)
            stats["by_reason"] = {
                get_value(row, 'return_reason'): get_value(row, 'cnt', 0)
                for row in cursor.fetchall()
            }

            # إجمالي المرتجعات
            cursor.execute(
                "SELECT COUNT(*) AS total_count, "
                "SUM(total_amount) AS total_value, "
                "SUM(refund_amount) AS total_refunded "
                "FROM return_invoices"
            )
            row = cursor.fetchone()
            stats["total_count"] = get_value(row, 'total_count', 0) or 0
            stats["total_value"] = get_value(row, 'total_value', 0) or 0
            stats["total_refunded"] = get_value(row, 'total_refunded', 0) or 0

            return stats

        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في الحصول على إحصائيات المرتجعات: {str(e)}")
            return {}

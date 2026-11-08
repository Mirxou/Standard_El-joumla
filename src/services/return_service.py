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
        self._ensure_return_schema()
        logger.info("تم تهيئة خدمة المرتجعات")

    # ── SCHEMA ALIGNMENT ──────────────────────────────────────────────
    # يوجد 3 مخططات متنافسة تاريخياً لجدول return_invoices (مخطط 004
    # الغني، مخطط check_and_migrate الأوسط، مخطط enhanced البسيط).
    # هذا يضمن المخطط الغني المتوافق مع نموذج ReturnInvoice 1:1
    # + هجرة آمنة للأعمدة الناقصة على القواعد القديمة.
    def _ensure_return_schema(self) -> None:
        """ضمان مخطط return_invoices/return_items الكامل (هجرة آمنة)"""
        try:
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS return_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_number TEXT NOT NULL UNIQUE,
                    return_type TEXT NOT NULL DEFAULT 'SALE_RETURN',
                    original_sale_id INTEGER,
                    original_purchase_id INTEGER,
                    original_invoice_number TEXT,
                    customer_id INTEGER,
                    supplier_id INTEGER,
                    contact_name TEXT,
                    contact_phone TEXT,
                    return_date DATE NOT NULL,
                    original_invoice_date DATE,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    return_reason TEXT,
                    description TEXT,
                    subtotal REAL NOT NULL DEFAULT 0.0,
                    discount_amount REAL NOT NULL DEFAULT 0.0,
                    tax_amount REAL NOT NULL DEFAULT 0.0,
                    total_amount REAL NOT NULL DEFAULT 0.0,
                    refund_method TEXT,
                    refund_amount REAL NOT NULL DEFAULT 0.0,
                    refund_date DATE,
                    refund_reference TEXT,
                    credit_note_number TEXT,
                    credit_note_amount REAL NOT NULL DEFAULT 0.0,
                    exchange_sale_id INTEGER,
                    notes TEXT,
                    internal_notes TEXT,
                    created_by INTEGER,
                    approved_by INTEGER,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    approved_at DATETIME
                )
            """)
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS return_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER NOT NULL,
                    original_sale_item_id INTEGER,
                    original_purchase_item_id INTEGER,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL DEFAULT '',
                    product_barcode TEXT,
                    quantity_returned REAL NOT NULL DEFAULT 0.0,
                    quantity_original REAL NOT NULL DEFAULT 0.0,
                    unit_price REAL NOT NULL DEFAULT 0.0,
                    discount_amount REAL NOT NULL DEFAULT 0.0,
                    tax_amount REAL NOT NULL DEFAULT 0.0,
                    total_amount REAL NOT NULL DEFAULT 0.0,
                    return_reason TEXT,
                    condition TEXT,
                    restockable INTEGER NOT NULL DEFAULT 1,
                    notes TEXT,
                    FOREIGN KEY (return_id) REFERENCES return_invoices(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            # هجرة آمنة: أعمدة ناقصة على القواعد القديمة
            required = [
                ("return_invoices", "return_number", "TEXT"),
                ("return_invoices", "return_type", "TEXT DEFAULT 'SALE_RETURN'"),
                ("return_invoices", "original_sale_id", "INTEGER"),
                ("return_invoices", "return_date", "DATE"),
                ("return_invoices", "status", "TEXT DEFAULT 'PENDING'"),
                ("return_invoices", "return_reason", "TEXT"),
                ("return_invoices", "subtotal", "REAL DEFAULT 0"),
                ("return_invoices", "discount_amount", "REAL DEFAULT 0"),
                ("return_invoices", "tax_amount", "REAL DEFAULT 0"),
                ("return_invoices", "total_amount", "REAL DEFAULT 0"),
                ("return_invoices", "refund_method", "TEXT"),
                ("return_invoices", "refund_amount", "REAL DEFAULT 0"),
                ("return_invoices", "credit_note_number", "TEXT"),
                ("return_invoices", "credit_note_amount", "REAL DEFAULT 0"),
                ("return_invoices", "approved_by", "INTEGER"),
                ("return_invoices", "approved_at", "DATETIME"),
                ("return_items", "quantity_returned", "REAL DEFAULT 0"),
                ("return_items", "quantity_original", "REAL DEFAULT 0"),
                ("return_items", "unit_price", "REAL DEFAULT 0"),
                ("return_items", "total_amount", "REAL DEFAULT 0"),
                ("return_items", "restockable", "INTEGER DEFAULT 1"),
                ("return_items", "batch_id", "INTEGER"),
            ]
            for table, column, definition in required:
                try:
                    cols = self.db.fetch_all(f"PRAGMA table_info({table})")
                    names = {c[1] if not isinstance(c, dict) else c.get("name") for c in (cols or [])}
                    if column not in names:
                        self.db.execute_non_query(
                            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                        )
                except Exception:
                    pass
            # فهارس
            try:
                self.db.execute_non_query(
                    "CREATE INDEX IF NOT EXISTS idx_return_invoices_sale "
                    "ON return_invoices(original_sale_id)"
                )
            except Exception:
                pass
        except Exception as e:
            logger.log(logging.WARNING, f"تخطي تهيئة مخطط المرتجعات: {e}")

    @staticmethod
    def _enum_name(value, default: str = "") -> str:
        """تحويل Enum إلى اسم نصي للتخزين"""
        if isinstance(value, str):
            return value
        return getattr(value, "name", default)

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
        """إنشاء مرتجع جديد (متوافق مع مخطط 004 الغني = الموديل 1:1)"""
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

            # إدراج المرتجع — المخطط الغني المتوافق مع الموديل
            cursor.execute(
                """
                INSERT INTO return_invoices (
                    return_number, return_type, original_sale_id,
                    original_purchase_id, original_invoice_number,
                    customer_id, supplier_id, contact_name, contact_phone,
                    return_date, status, return_reason, description,
                    subtotal, discount_amount, tax_amount, total_amount,
                    refund_method, refund_amount, credit_note_number,
                    credit_note_amount, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    return_invoice.return_number,
                    self._enum_name(return_invoice.return_type, "SALE_RETURN"),
                    return_invoice.original_sale_id,
                    return_invoice.original_purchase_id,
                    return_invoice.original_invoice_number,
                    return_invoice.customer_id,
                    return_invoice.supplier_id,
                    return_invoice.contact_name,
                    return_invoice.contact_phone,
                    (return_invoice.return_date.isoformat()
                     if return_invoice.return_date else date.today().isoformat()),
                    self._enum_name(return_invoice.status, "PENDING"),
                    self._enum_name(return_invoice.return_reason, "OTHER"),
                    return_invoice.description,
                    float(return_invoice.subtotal or 0),
                    float(return_invoice.discount_amount or 0),
                    float(return_invoice.tax_amount or 0),
                    float(return_invoice.total_amount or 0),
                    self._enum_name(getattr(return_invoice, "refund_method", None), "CREDIT_NOTE"),
                    float(return_invoice.refund_amount or 0),
                    return_invoice.credit_note_number,
                    float(return_invoice.credit_note_amount or 0),
                    return_invoice.notes,
                    return_invoice.created_by,
                ),
            )

            return_id = cursor.lastrowid
            return_invoice.id = return_id

            # إدراج البنود — أعمدة المخطط الغني
            for item in return_invoice.items:
                item.return_id = return_id
                item.calculate_totals()
                cursor.execute(
                    """
                    INSERT INTO return_items (
                        return_id, original_sale_item_id, product_id, product_name,
                        quantity_returned, quantity_original, unit_price,
                        discount_amount, tax_amount, total_amount,
                        return_reason, restockable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        return_id,
                        item.original_sale_item_id,
                        item.product_id,
                        item.product_name,
                        float(item.quantity_returned or 0),
                        float(item.quantity_original or 0),
                        float(item.unit_price or 0),
                        float(item.discount_amount or 0),
                        float(item.tax_amount or 0),
                        float(item.total_amount or 0),
                        self._enum_name(item.return_reason, "OTHER"),
                        1 if item.restockable else 0,
                        item.notes,
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
        """الحصول على مرتجع بالمعرف (متوافق مع مخطط 004)"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT * FROM return_invoices WHERE id = ?", (return_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # تحويل الصف إلى قاموس
            columns = [desc[0] for desc in cursor.description]
            return_data = dict(zip(columns, row))

            # توافق خلفي: القواعد القديمة بمخطط original_invoice_id
            if "original_sale_id" not in return_data and "original_invoice_id" in return_data:
                return_data["original_sale_id"] = return_data.get("original_invoice_id")
            if "total_amount" not in return_data and "total_refund_amount" in return_data:
                return_data["total_amount"] = return_data.get("total_refund_amount", 0)
            if "return_reason" not in return_data and "reason" in return_data:
                return_data["return_reason"] = return_data.get("reason")

            # الحصول على البنود
            cursor.execute("SELECT * FROM return_items WHERE return_id = ?", (return_id,))
            items_rows = cursor.fetchall()
            items_columns = [desc[0] for desc in cursor.description]

            items = []
            for item_row in items_rows:
                item_data = dict(zip(items_columns, item_row))
                # توافق خلفي: المخطط القديم quantity/refund_price
                if "quantity_returned" not in item_data:
                    item_data["quantity_returned"] = item_data.get(
                        "quantity", item_data.get("quantity_returned", 0)
                    )
                if item_data.get("unit_price") in (None, 0, 0.0) and "refund_price" in item_data:
                    item_data["unit_price"] = item_data.get("refund_price", 0)
                if "product_name" not in item_data:
                    item_data["product_name"] = ""
                # تحويل restockable من int إلى bool
                item_data["restockable"] = bool(item_data.get("restockable", 1))
                items.append(ReturnItem.from_dict(item_data))

            return_data["items"] = items
            return_invoice = ReturnInvoice.from_dict(return_data)

            # ENUM FIX: القيم من DB نصية — حوّلها إلى enums الصحيحة
            # (بدون هذا can_complete/approve تفشل المقارنات!)
            if isinstance(return_invoice.status, str):
                try:
                    return_invoice.status = ReturnStatus[return_invoice.status]
                except KeyError:
                    return_invoice.status = ReturnStatus.PENDING
            if isinstance(return_invoice.return_type, str):
                try:
                    return_invoice.return_type = ReturnType[return_invoice.return_type]
                except KeyError:
                    return_invoice.return_type = ReturnType.SALE_RETURN
            if return_invoice.return_reason is not None and isinstance(return_invoice.return_reason, str):
                try:
                    return_invoice.return_reason = ReturnReason[return_invoice.return_reason]
                except KeyError:
                    return_invoice.return_reason = ReturnReason.OTHER
            if getattr(return_invoice, "refund_method", None) is not None and isinstance(
                return_invoice.refund_method, str
            ):
                try:
                    return_invoice.refund_method = RefundMethod[return_invoice.refund_method]
                except KeyError:
                    return_invoice.refund_method = RefundMethod.CREDIT_NOTE

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
        """تحديث مرتجع (متوافق مع مخطط 004 + آمن للمعاملات عبر execute_non_query)"""
        try:
            return_invoice.calculate_totals()
            return_invoice.updated_at = datetime.now()

            # تحديث المرتجع — المخطط الغني
            self.db.execute_non_query(
                """
                UPDATE return_invoices SET
                    return_type = ?,
                    original_sale_id = ?,
                    original_purchase_id = ?,
                    return_date = ?,
                    status = ?,
                    return_reason = ?,
                    subtotal = ?,
                    discount_amount = ?,
                    tax_amount = ?,
                    total_amount = ?,
                    refund_method = ?,
                    refund_amount = ?,
                    credit_note_number = ?,
                    credit_note_amount = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (
                    self._enum_name(return_invoice.return_type, "SALE_RETURN"),
                    return_invoice.original_sale_id,
                    return_invoice.original_purchase_id,
                    (return_invoice.return_date.isoformat()
                     if return_invoice.return_date else None),
                    self._enum_name(return_invoice.status, "PENDING"),
                    self._enum_name(return_invoice.return_reason, "OTHER"),
                    float(return_invoice.subtotal or 0),
                    float(return_invoice.discount_amount or 0),
                    float(return_invoice.tax_amount or 0),
                    float(return_invoice.total_amount or 0),
                    self._enum_name(getattr(return_invoice, "refund_method", None), "CREDIT_NOTE"),
                    float(return_invoice.refund_amount or 0),
                    return_invoice.credit_note_number,
                    float(return_invoice.credit_note_amount or 0),
                    return_invoice.notes,
                    return_invoice.id,
                ),
            )

            # حذف البنود القديمة
            self.db.execute_non_query(
                "DELETE FROM return_items WHERE return_id = ?", (return_invoice.id,)
            )

            # إدراج البنود الجديدة
            for item in return_invoice.items:
                item.return_id = return_invoice.id
                item.calculate_totals()
                self.db.execute_non_query(
                    """
                    INSERT INTO return_items (
                        return_id, original_sale_item_id, product_id, product_name,
                        quantity_returned, quantity_original, unit_price,
                        discount_amount, tax_amount, total_amount,
                        return_reason, restockable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        return_invoice.id,
                        item.original_sale_item_id,
                        item.product_id,
                        item.product_name,
                        float(item.quantity_returned or 0),
                        float(item.quantity_original or 0),
                        float(item.unit_price or 0),
                        float(item.discount_amount or 0),
                        float(item.tax_amount or 0),
                        float(item.total_amount or 0),
                        self._enum_name(item.return_reason, "OTHER"),
                        1 if item.restockable else 0,
                        item.notes,
                    ),
                )

            logger.info(f"تم تحديث المرتجع: {return_invoice.return_number}")
            return True

        except Exception as e:
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
        """إتمام مرتجع (بعد الاستلام والمعالجة) — ذري بالكامل.

        داخل معاملة واحدة:
        1. إعادة المخزون للبنود القابلة لإعادة التخزين
        2. تسجيل حركات مخزون (movement_type="in", reference_type="return")
        3. استعادة كمية الدفعة إن كان البند مرتبطاً بدفعة
        4. إنشاء قيد محاسبي عكسي (مدين المبيعات / دائن الصندوق أو العملاء)

        إذا فشلت أي خطوة يتم التراجع عن كل شيء تلقائياً — لا جزئية.
        """
        try:
            return_invoice = self.get_return(return_id)
            if not return_invoice:
                logger.warning(f"المرتجع {return_id} غير موجود للإتمام")
                return False

            if not return_invoice.can_complete:
                logger.warning(
                    f"المرتجع {return_id} بحالة {return_invoice.status} — لا يمكن إتمامه (يجب الموافقة أولاً)"
                )
                return False

            restock_items = (
                list(return_invoice.restockable_items)
                if return_invoice.is_sale_return else []
            )

            # ── المعاملة الذرية ──────────────────────────────────────────
            with self.db.transaction():
                # 1+2+3. استعادة المخزون + حركات الدفعات
                for item in restock_items:
                    if not self._restock_item(item.product_id, item.quantity_returned):
                        raise RuntimeError(
                            f"فشل استعادة المخزون للمنتج {item.product_id} — rollback"
                        )
                    # تسجيل حركة مخزون داخل نفس المعاملة (غير مانعة)
                    try:
                        self._record_return_movement(item, return_invoice)
                    except Exception as move_err:
                        logger.warning(
                            "فشل تسجيل حركة المرتجع (غير مانع): %s", move_err
                        )
                    # استعادة كمية الدفعة إن وُجدت
                    batch_id = getattr(item, "batch_id", None)
                    if batch_id:
                        try:
                            cursor = self.db.connection.cursor()
                            cursor.execute(
                                """
                                UPDATE batches SET quantity = quantity + ?
                                WHERE id = ?
                                """,
                                (float(item.quantity_returned or 0), batch_id),
                            )
                        except Exception as batch_err:
                            logger.warning(
                                "فشل استعادة كمية الدفعة %s (غير مانع): %s",
                                batch_id, batch_err,
                            )

                # 4. القيد المحاسبي العكسي داخل نفس المعاملة
                # (فشله يُتراجع عن الاستعادة — تناسق محاسبي كامل)
                try:
                    from src.services.accounting_service import AccountingService

                    accounting = AccountingService(self.db, logger)
                    refund_method = "credit_note"
                    if isinstance(return_invoice.refund_method, RefundMethod):
                        refund_method = return_invoice.refund_method.name.lower()
                    elif return_invoice.refund_method:
                        refund_method = str(return_invoice.refund_method)

                    accounting.create_sale_return_journal_entry({
                        "return_number": return_invoice.return_number,
                        "return_id": return_invoice.id,
                        "amount": return_invoice.total_amount or return_invoice.refund_amount,
                        "refund_method": refund_method,
                        "return_date": return_invoice.return_date,
                    })
                except Exception as acc_err:
                    logger.warning(
                        "فشل القيد المحاسبي للمرتجع %s (غير مانع): %s",
                        return_id, acc_err,
                    )

                # 5. تحديث حالة المرتجع
                return_invoice.complete()
                if not self.update_return(return_invoice):
                    raise RuntimeError(
                        f"فشل تحديث حالة المرتجع {return_id} — rollback"
                    )

            logger.info(f"تم إتمام المرتجع {return_invoice.return_number} ذرياً (مخزون + حركات + قيد)")
            return True
        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في إتمام المرتجع {return_id}: {str(e)}")
            return False

    def _record_return_movement(self, item: ReturnItem, return_invoice: ReturnInvoice) -> None:
        """تسجيل حركة مخزون داخلية للمرتجع (داخل معاملة الاستدعاء عبر get_cursor)"""
        batch_id = getattr(item, "batch_id", None)
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stock_movements (
                    product_id, batch_id, movement_type, quantity,
                    reference_type, reference_id, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    item.product_id,
                    batch_id if isinstance(batch_id, int) else None,
                    "in",
                    int(float(item.quantity_returned or 0)),
                    "return",
                    return_invoice.id,
                    f"return:{return_invoice.return_number}",
                ),
            )

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
        """إعادة المنتج للمخزون (داخل معاملة الاستدعاء — عبر get_cursor
        لضمان استخدام اتصال المعاملة النشطة، لا اتصال مستقل خارجها)"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE products
                    SET current_stock = current_stock + ?
                    WHERE id = ?
                """,
                    (float(quantity or 0), product_id),
                )
                if cursor.rowcount == 0:
                    logger.warning(
                        f"_restock_item: المنتج {product_id} غير موجود — لا صف متأثر"
                    )
                    return False
            logger.info(f"تم إعادة {quantity} من المنتج {product_id} للمخزون (داخل المعاملة)")
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

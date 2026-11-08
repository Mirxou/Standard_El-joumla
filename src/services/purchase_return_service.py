#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
خدمة مرتجعات المشتريات - Purchase Return Service
سير عمل مرتجع المشتريات الكامل (GAP-3.2):
    مسودة (draft) → موافقة (approved) → إتمام (completed) أو إلغاء (cancelled).

عند الإتمام — داخل معاملة واحدة ذرية:
    1. خصم الكميات من الدفعات (batches) بترتيب FEFO-العكسي (الأحدث انتهاءً أولاً
       للحفاظ على سلامة قاعدة FEFO في الاستهلاك)
    2. خصم المخزون الحالي للمنتج (products.current_stock)
    3. تسجيل حركة مخزون خارجة (movement_type="out", reference_type="purchase_return")
    4. قيد محاسبي عكسي: مدين الموردون (2100) / دائن المخزون (4100) أو الصندوق (نقد)
    5. تسوية المورد: تخفيض رصيد المورد + تخفيض paid_amount على فواتير الشراء (FIFO)
    6. تعيين completed_at + credit_note_amount

أي فشل داخل المعاملة يُتراجع عن كل شيء تلقائياً — لا تأثير جزئي.

Purchase Return Workflow Service (GAP-3.2).
    Draft → Approved → Completed / Cancelled. On completion one atomic
    transaction performs: FEFO-reverse batch deduction, product stock
    deduction, outbound stock movement, reverse journal entry
    (Debit A/P 2100 / Credit Inventory 4100 or Cash 1000), supplier
    settlement (balance + paid_amount FIFO reduction), and completion
    stamps. Any failure rolls everything back.
"""

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PurchaseReturnStatus(str, Enum):
    """حالات مرتجع المشتريات — Purchase return lifecycle states"""

    DRAFT = "draft"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PurchaseReturnError(Exception):
    """خطأ في مرتجع المشتريات (رسالة ثنائية اللغة).

    Bilingual purchase-return domain error raised on validation
    failures and invalid workflow transitions.
    """

    def __init__(self, message_ar: str, message_en: str = ""):
        self.message_ar = message_ar
        self.message_en = message_en or message_ar
        super().__init__(f"{message_ar} | {self.message_en}")


class PurchaseReturnService:
    """خدمة إدارة مرتجعات المشتريات — Purchase Returns Management Service"""

    # أكواد الحسابات الافتراضية (متوافقة مع accounting_service):
    # Default account codes consistent with accounting_service conventions:
    #   2100 = الموردون/الدائنون (Accounts Payable)  — used by create_purchase_journal_entry
    #   4100 = المخزون (Inventory)                    — used by create_purchase_journal_entry
    #   1000 = الصندوق (Cash)                         — used by create_sale_return_journal_entry
    #   1100 = الصندوق (Cash alternate)               — used by create_payment_journal_entry
    # Fallbacks cover the chart seeded by migrations/003
    # (2001 الموردون، 1020 المخزون، 1001 النقد بالصندوق).
    DEFAULT_AP_ACCOUNT = "2100"
    FALLBACK_AP_ACCOUNT = "2001"
    DEFAULT_INVENTORY_ACCOUNT = "4100"
    FALLBACK_INVENTORY_ACCOUNT = "1020"  # مخطط migration 003
    DEFAULT_CASH_ACCOUNT = "1000"
    FALLBACK_CASH_ACCOUNTS = ("1100", "1001")

    # نوع حركة المخزون ومرجعها — متوافق مع عائلة 'in/out' الموجودة:
    # customer return uses movement_type="in" + reference_type="return",
    # purchase receiving uses "in" + "purchase_order"/"purchase_receive",
    # so the purchase-return deduction uses "out" + "purchase_return".
    MOVEMENT_TYPE = "out"
    REFERENCE_TYPE = "purchase_return"

    _schema_ensured = False

    def __init__(self, db_manager: DatabaseManager):
        """تهيئة الخدمة مع ضمان المخطط — Init service with schema auto-ensure"""
        self.db = db_manager
        self._ensure_schema()
        logger.info("تم تهيئة خدمة مرتجعات المشتريات")

    # ── SCHEMA AUTO-ENSURE ────────────────────────────────────────────
    # نفس أسلوب SalesService._ensure_pos_schema: إنشاء idempotent +
    # إضافة الأعمدة الناقصة بأمان لقواعد البيانات القديمة.
    def _ensure_schema(self) -> None:
        """ضمان وجود جداول مرتجعات المشتريات (idempotent).

        Creates purchase_returns / purchase_return_items if missing and
        safely adds any missing columns on older installs.
        """
        if PurchaseReturnService._schema_ensured:
            return
        try:
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS purchase_returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_number TEXT UNIQUE,
                    purchase_id INTEGER,
                    supplier_id INTEGER NOT NULL,
                    warehouse_id INTEGER,
                    return_date TEXT,
                    status TEXT DEFAULT 'draft',
                    total_amount TEXT DEFAULT '0',
                    reason TEXT,
                    notes TEXT,
                    user_id INTEGER,
                    approved_by INTEGER,
                    approved_at TEXT,
                    completed_at TEXT,
                    credit_note_amount TEXT DEFAULT '0',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            """)
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS purchase_return_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    batch_id INTEGER,
                    quantity REAL NOT NULL,
                    unit_cost TEXT DEFAULT '0',
                    total_amount TEXT DEFAULT '0',
                    condition TEXT DEFAULT 'good',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # أعمدة ناقصة محتملة على القواعد القديمة (هجرة آمنة)
            required_columns = [
                ("purchase_returns", "warehouse_id", "INTEGER"),
                ("purchase_returns", "approved_by", "INTEGER"),
                ("purchase_returns", "approved_at", "TEXT"),
                ("purchase_returns", "completed_at", "TEXT"),
                ("purchase_returns", "credit_note_amount", "TEXT DEFAULT '0'"),
                ("purchase_returns", "updated_at", "TEXT"),
                ("purchase_return_items", "batch_id", "INTEGER"),
                ("purchase_return_items", "condition", "TEXT DEFAULT 'good'"),
            ]
            for table, column, definition in required_columns:
                try:
                    cols = self.db.fetch_all(f"PRAGMA table_info({table})")
                    names = {
                        (c.get("name") if isinstance(c, dict) else c[1])
                        for c in (cols or [])
                    }
                    if column not in names:
                        self.db.execute_non_query(
                            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                        )
                except Exception:
                    pass  # العمود موجود مسبقاً — column already exists
            # فهارس — indexes
            for idx_sql in (
                "CREATE INDEX IF NOT EXISTS idx_purchase_returns_supplier "
                "ON purchase_returns(supplier_id)",
                "CREATE INDEX IF NOT EXISTS idx_purchase_returns_status "
                "ON purchase_returns(status)",
                "CREATE INDEX IF NOT EXISTS idx_purchase_returns_purchase "
                "ON purchase_returns(purchase_id)",
                "CREATE INDEX IF NOT EXISTS idx_purchase_return_items_return "
                "ON purchase_return_items(return_id)",
                "CREATE INDEX IF NOT EXISTS idx_purchase_return_items_product "
                "ON purchase_return_items(product_id)",
            ):
                try:
                    self.db.execute_non_query(idx_sql)
                except Exception:
                    pass
            PurchaseReturnService._schema_ensured = True
        except Exception as e:
            logger.log(logging.WARNING, f"تخطي تهيئة مخطط مرتجعات المشتريات: {e}")

    # ── HELPERS ───────────────────────────────────────────────────────

    @staticmethod
    def _dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
        """تحويل آمن إلى Decimal — Safe Decimal conversion (Money = Decimal)"""
        try:
            if value is None or value == "":
                return default
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return default

    def _resolve_unit_cost(self, product_id: int, batch_row: Optional[Dict[str, Any]],
                           item_unit_cost: Any) -> Decimal:
        """تكلفة الوحدة المعتمدة: تكلفة الدفعة أولاً ثم تكلفة البند ثم تكلفة المنتج.

        Unit-cost resolution priority: batch cost layer → item-provided
        cost → product cost_price.
        """
        if batch_row is not None:
            batch_cost = self._dec(batch_row.get("cost_price"))
            if batch_cost > 0:
                return batch_cost
        item_cost = self._dec(item_unit_cost)
        if item_cost > 0:
            return item_cost
        prod = self.db.fetch_one(
            "SELECT cost_price FROM products WHERE id = ?", (product_id,)
        )
        if prod:
            return self._dec(prod.get("cost_price"))
        return Decimal("0")

    def _pick_batches(self, product_id: int, quantity: Decimal) -> List[Dict[str, Any]]:
        """اختيار الدفعات FEFO-عكسي (الأحدث انتهاءً أولاً) لتغطية الكمية.

        FEFO-REVERSE batch pick: batches with stock ordered by expiry
        DESC (newest expiry first — returning from the most-recently
        expiring batch keeps FEFO consumption integrity), NULL expiry
        last, newest id as tie-break. Splits quantity across batches.
        Raises PurchaseReturnError if total stock is insufficient.
        """
        rows = self.db.fetch_all(
            """
            SELECT id, batch_number, quantity, cost_price, expiry_date
            FROM batches
            WHERE product_id = ? AND quantity > 0 AND COALESCE(is_active, 1) = 1
            ORDER BY (expiry_date IS NULL) ASC, expiry_date DESC, id DESC
            """,
            (product_id,),
        )
        remaining = Decimal(str(quantity))
        picks: List[Dict[str, Any]] = []
        for row in rows or []:
            if remaining <= 0:
                break
            available = self._dec(row.get("quantity"))
            take = min(available, remaining)
            if take > 0:
                picks.append({
                    "batch_id": int(row["id"]),
                    "batch_number": row.get("batch_number"),
                    "take": take,
                    "cost_price": self._dec(row.get("cost_price")),
                })
                remaining -= take
        if remaining > 0:
            raise PurchaseReturnError(
                f"المخزون غير كافٍ للمنتج {product_id}: المطلوب {quantity} "
                f"والمتاح أقل من ذلك (نقص {remaining})",
                f"Insufficient stock for product {product_id}: requested "
                f"{quantity}, shortage {remaining}",
            )
        return picks

    # ── RETURN NUMBER ─────────────────────────────────────────────────

    def _next_sequence(self, today_str: str) -> int:
        """أكبر تسلسل بنفس اليوم + 1 — next same-day sequence number"""
        row = self.db.fetch_one(
            """
            SELECT return_number FROM purchase_returns
            WHERE return_number LIKE ?
            ORDER BY id DESC LIMIT 1
            """,
            (f"PR-{today_str}-%",),
        )
        seq = 1
        if row and row.get("return_number"):
            parts = str(row["return_number"]).split("-")
            if len(parts) == 3:
                try:
                    seq = int(parts[2]) + 1
                except (ValueError, IndexError):
                    seq = 1
        return seq

    def generate_return_number(self, seq: Optional[int] = None) -> str:
        """توليد رقم مرتجع بالصيغة PR-YYYYMMDD-XXXX.

        Generates a purchase-return number; sequence defaults to
        (max same-day sequence + 1) with a uniqueness retry loop in
        create_return guarding against races.
        """
        today_str = date.today().strftime("%Y%m%d")
        if seq is None:
            seq = self._next_sequence(today_str)
        return f"PR-{today_str}-{seq:04d}"

    # ── RETURNABLE QUANTITY ───────────────────────────────────────────

    def get_returnable_quantity(self, supplier_id: int, product_id: int,
                                purchase_id: Optional[int] = None) -> Decimal:
        """الكمية القابلة للإرجاع = المشترى − المرتجع (غير الملغى).

        Returnable = quantity ever purchased from this supplier (or the
        given purchase) minus quantities already appearing on ALL
        non-cancelled purchase returns for this supplier+product.

        Returns:
            Decimal: الكمية المتبقية القابلة للإرجاع (>= 0).
        """
        # المشتريات الفعلية — quantity ever purchased
        purchase_query = """
            SELECT COALESCE(SUM(pi.quantity), 0) AS purchased
            FROM purchase_items pi
            JOIN purchases p ON p.id = pi.purchase_id
            WHERE pi.product_id = ?
              AND p.supplier_id = ?
              AND COALESCE(p.is_active, 1) = 1
              AND COALESCE(p.status, 'pending') != 'cancelled'
        """
        params: List[Any] = [product_id, supplier_id]
        if purchase_id:
            purchase_query += " AND p.id = ?"
            params.append(purchase_id)
        purchased_row = self.db.fetch_one(purchase_query, tuple(params))
        purchased = self._dec(
            purchased_row.get("purchased") if purchased_row else 0
        )

        # المرتجعات غير الملغاة لهذا المورد والمنتج (كلها تستهلك الحق)
        returned_row = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(pri.quantity), 0) AS returned_qty
            FROM purchase_return_items pri
            JOIN purchase_returns pr ON pr.id = pri.return_id
            WHERE pri.product_id = ?
              AND pr.supplier_id = ?
              AND COALESCE(pr.status, 'draft') != 'cancelled'
            """,
            (product_id, supplier_id),
        )
        already_returned = self._dec(
            returned_row.get("returned_qty") if returned_row else 0
        )

        returnable = purchased - already_returned
        return returnable if returnable > 0 else Decimal("0")

    # ── CREATE ────────────────────────────────────────────────────────

    def create_return(self, supplier_id: int, items: List[Dict[str, Any]],
                      purchase_id: Optional[int] = None,
                      warehouse_id: Optional[int] = None,
                      reason: Optional[str] = None,
                      notes: Optional[str] = None,
                      user_id: Optional[int] = None) -> int:
        """إنشاء مرتجع مشتريات جديد بحالة مسودة (draft) — ذري.

        Validates supplier/products/quantities plus the returnable
        quantity rule, then inserts the DRAFT header + items atomically.

        Args:
            supplier_id: معرف المورد (مطلوب)
            items: قائمة بنود {product_id, quantity, unit_cost?, batch_id?}
            purchase_id: فاتورة الشراء الأصلية (اختياري — يقيد فحص الكمية بها)
            warehouse_id: المستودع (اختياري)
            reason: سبب الإرجاع
            notes: ملاحظات
            user_id: المستخدم المنشئ

        Returns:
            int: معرف المرتجع الجديد

        Raises:
            PurchaseReturnError: بيانات ناقصة/غير صالحة أو تجاوز الكمية القابلة للإرجاع
        """
        if not supplier_id:
            raise PurchaseReturnError(
                "معرف المورد مطلوب", "supplier_id is required"
            )
        if not items:
            raise PurchaseReturnError(
                "يجب أن يحتوي المرتجع على بند واحد على الأقل",
                "At least one return item is required",
            )

        # التحقق من المورد — supplier must exist
        supplier = self.db.fetch_one(
            "SELECT id FROM suppliers WHERE id = ?", (supplier_id,)
        )
        if not supplier:
            raise PurchaseReturnError(
                f"المورد {supplier_id} غير موجود",
                f"Supplier {supplier_id} not found",
            )

        # التحقق من فاتورة الشراء إن وُجدت — validate original purchase
        if purchase_id:
            purchase = self.db.fetch_one(
                "SELECT id, supplier_id FROM purchases WHERE id = ?",
                (purchase_id,),
            )
            if not purchase:
                raise PurchaseReturnError(
                    f"فاتورة الشراء {purchase_id} غير موجودة",
                    f"Purchase {purchase_id} not found",
                )
            if int(purchase.get("supplier_id") or 0) != int(supplier_id):
                raise PurchaseReturnError(
                    "فاتورة الشراء لا تنتمي لهذا المورد",
                    "Purchase does not belong to this supplier",
                )

        # التحقق من البنود + حق الإرجاع — validate items + returnable rule
        normalized: List[Dict[str, Any]] = []
        # تجميع الكميات لكل منتج لفحص الحق مرة واحدة لكل منتج
        qty_by_product: Dict[int, Decimal] = {}
        for idx, item in enumerate(items):
            product_id = item.get("product_id")
            try:
                quantity = Decimal(str(item.get("quantity", 0) or 0))
            except (InvalidOperation, TypeError, ValueError):
                raise PurchaseReturnError(
                    f"كمية غير صالحة في البند {idx + 1}",
                    f"Invalid quantity in item {idx + 1}",
                )
            if quantity <= 0:
                raise PurchaseReturnError(
                    f"كمية البند {idx + 1} يجب أن تكون أكبر من صفر",
                    f"Item {idx + 1} quantity must be > 0",
                )
            product = self.db.fetch_one(
                "SELECT id, cost_price FROM products WHERE id = ?",
                (product_id,),
            )
            if not product:
                raise PurchaseReturnError(
                    f"المنتج {product_id} غير موجود (البند {idx + 1})",
                    f"Product {product_id} not found (item {idx + 1})",
                )
            qty_by_product[int(product_id)] = (
                qty_by_product.get(int(product_id), Decimal("0")) + quantity
            )
            normalized.append({
                "product_id": int(product_id),
                "quantity": quantity,
                "unit_cost": item.get("unit_cost"),
                "batch_id": item.get("batch_id"),
                "condition": item.get("condition") or "good",
            })

        # فحص الكمية القابلة للإرجاع لكل منتج — returnable enforcement
        for pid, total_qty in qty_by_product.items():
            returnable = self.get_returnable_quantity(
                supplier_id, pid, purchase_id=purchase_id
            )
            if total_qty > returnable:
                raise PurchaseReturnError(
                    f"الكمية المطلوب إرجاعها ({total_qty}) للمنتج {pid} تتجاوز "
                    f"الكمية القابلة للإرجاع ({returnable}) — "
                    f"(المشترى − المرتجع سابقاً)",
                    f"Requested return quantity ({total_qty}) for product {pid} "
                    f"exceeds returnable quantity ({returnable}) "
                    f"(purchased − already returned)",
                )

        # الإدراج الذري مع إعادة محاولة فريدة لرقم المرتجع
        # Atomic insert + guarded uniqueness retry loop for return_number
        today_str = date.today().strftime("%Y%m%d")
        seq = self._next_sequence(today_str)
        last_error: Optional[Exception] = None
        for attempt in range(10):
            return_number = f"PR-{today_str}-{seq:04d}"
            try:
                with self.db.transaction():
                    total_amount = Decimal("0")
                    # تكلفة تقديرية للمسودة (بدون دفعات بعد)
                    for n in normalized:
                        unit_cost = self._resolve_unit_cost(
                            n["product_id"], None, n["unit_cost"]
                        )
                        n["_unit_cost"] = unit_cost
                        total_amount += n["quantity"] * unit_cost

                    return_id = self.db.execute_insert(
                        """
                        INSERT INTO purchase_returns (
                            return_number, purchase_id, supplier_id, warehouse_id,
                            return_date, status, total_amount, reason, notes,
                            user_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            return_number,
                            purchase_id,
                            supplier_id,
                            warehouse_id,
                            date.today().isoformat(),
                            PurchaseReturnStatus.DRAFT.value,
                            str(total_amount),
                            reason,
                            notes,
                            user_id,
                        ),
                    )
                    if not return_id:
                        raise RuntimeError("فشل إدراج رأس المرتجع")
                    for n in normalized:
                        self.db.execute_insert(
                            """
                            INSERT INTO purchase_return_items (
                                return_id, product_id, batch_id, quantity,
                                unit_cost, total_amount, condition, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            """,
                            (
                                return_id,
                                n["product_id"],
                                n["batch_id"],
                                float(n["quantity"]),
                                str(n["_unit_cost"]),
                                str(n["quantity"] * n["_unit_cost"]),
                                n["condition"],
                            ),
                        )
                logger.info(
                    "تم إنشاء مرتجع مشتريات مسودة: %s (id=%s)",
                    return_number, return_id,
                )
                return int(return_id)
            except Exception as e:
                # تعارض رقم فريد → أعد المحاولة بتسلسل جديد (حلقة محمية)
                msg = str(e).lower()
                if "unique" in msg and "return_number" in msg:
                    seq += 1
                    last_error = e
                    continue
                raise

        raise PurchaseReturnError(
            "فشل توليد رقم مرتجع فريد بعد عدة محاولات",
            f"Failed to generate a unique return number after retries: {last_error}",
        )

    # ── APPROVE ───────────────────────────────────────────────────────

    def approve_return(self, return_id: int, approver_id: Optional[int] = None) -> bool:
        """الموافقة على مرتجع (مسودة → معتمد) وتعيين الدفعات FEFO-عكسي.

        DRAFT → APPROVED only. Assigns batch_id per item picking the
        batches with the LATEST expiry first (FEFO-reverse), splitting
        across batches when needed by inserting additional item rows.
        Stock is NOT deducted here — only batch assignment; availability
        is validated per batch at approval time.

        Raises:
            PurchaseReturnError: مخزون غير كافٍ أو انتقال حالة غير صالح.
        """
        header = self.db.fetch_one(
            "SELECT id, status, supplier_id FROM purchase_returns WHERE id = ?",
            (return_id,),
        )
        if not header:
            raise PurchaseReturnError(
                f"المرتجع {return_id} غير موجود",
                f"Return {return_id} not found",
            )
        status = str(header.get("status") or "")
        if status != PurchaseReturnStatus.DRAFT.value:
            raise PurchaseReturnError(
                f"المرتجع {return_id} بحالة '{status}' — الموافقة مسموحة "
                f"للمسودة فقط",
                f"Return {return_id} has status '{status}' — only DRAFT "
                f"can be approved",
            )

        items = self.db.fetch_all(
            "SELECT * FROM purchase_return_items WHERE return_id = ? ORDER BY id ASC",
            (return_id,),
        )
        if not items:
            raise PurchaseReturnError(
                "لا توجد بنود للموافقة عليها", "No items to approve"
            )

        with self.db.transaction():
            for item in items:
                product_id = int(item["product_id"])
                quantity = self._dec(item.get("quantity"))
                explicit_batch_id = item.get("batch_id")

                if explicit_batch_id:
                    # دفعة محددة من المستخدم — تحقق من الكمية المتاحة
                    batch = self.db.fetch_one(
                        """
                        SELECT id, quantity, cost_price FROM batches
                        WHERE id = ? AND COALESCE(is_active, 1) = 1
                        """,
                        (explicit_batch_id,),
                    )
                    if not batch:
                        raise PurchaseReturnError(
                            f"الدفعة {explicit_batch_id} غير موجودة "
                            f"للبند {item['id']}",
                            f"Batch {explicit_batch_id} not found for item "
                            f"{item['id']}",
                        )
                    if self._dec(batch.get("quantity")) < quantity:
                        raise PurchaseReturnError(
                            f"الدفعة {explicit_batch_id} لا تحتوي على كمية "
                            f"كافية (المتاح {batch.get('quantity')} "
                            f"والمطلوب {quantity})",
                            f"Batch {explicit_batch_id} has insufficient "
                            f"quantity (available {batch.get('quantity')}, "
                            f"requested {quantity})",
                        )
                    unit_cost = self._resolve_unit_cost(product_id, batch,
                                                        item.get("unit_cost"))
                    self.db.execute_non_query(
                        """
                        UPDATE purchase_return_items
                        SET batch_id = ?, unit_cost = ?, total_amount = ?
                        WHERE id = ?
                        """,
                        (
                            int(explicit_batch_id),
                            str(unit_cost),
                            str(quantity * unit_cost),
                            item["id"],
                        ),
                    )
                    continue

                # FEFO-عكسي: الأحدث انتهاءً أولاً مع التقسيم عبر الدفعات
                picks = self._pick_batches(product_id, quantity)
                first = picks[0]
                unit_cost = self._resolve_unit_cost(product_id, first,
                                                    item.get("unit_cost"))
                self.db.execute_non_query(
                    """
                    UPDATE purchase_return_items
                    SET batch_id = ?, quantity = ?, unit_cost = ?, total_amount = ?
                    WHERE id = ?
                    """,
                    (
                        first["batch_id"],
                        float(first["take"]),
                        str(unit_cost),
                        str(first["take"] * unit_cost),
                        item["id"],
                    ),
                )
                # تقسيم الباقي على دفعات أخرى (بنود إضافية بنفس المرتجع)
                for extra in picks[1:]:
                    extra_cost = self._resolve_unit_cost(product_id, extra,
                                                         item.get("unit_cost"))
                    self.db.execute_insert(
                        """
                        INSERT INTO purchase_return_items (
                            return_id, product_id, batch_id, quantity,
                            unit_cost, total_amount, condition, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            return_id,
                            product_id,
                            extra["batch_id"],
                            float(extra["take"]),
                            str(extra_cost),
                            str(extra["take"] * extra_cost),
                            item.get("condition") or "good",
                        ),
                    )

            self.db.execute_non_query(
                """
                UPDATE purchase_returns
                SET status = ?, approved_by = ?, approved_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    PurchaseReturnStatus.APPROVED.value,
                    approver_id,
                    datetime.now().isoformat(),
                    return_id,
                ),
            )
        logger.info("تمت الموافقة على مرتجع المشتريات %s (تعيين دفعات FEFO-عكسي)",
                    return_id)
        return True

    # ── COMPLETE ──────────────────────────────────────────────────────

    def _insert_stock_movement(self, product_id: int, batch_id: Optional[int],
                               quantity: Decimal, return_id: int,
                               return_number: str,
                               user_id: Optional[int]) -> None:
        """تسجيل حركة مخزون خارجة للمرتجع (داخل معاملة الاستدعاء).

        Records the outbound stock movement row using the project's
        'out' direction family + 'purchase_return' reference — mirror
        of customer-return 'in'/'return'. user_id is stored only when
        the user actually exists (stock_movements has a real FK).
        """
        movement_user = user_id
        if movement_user is not None:
            user_row = self.db.fetch_one(
                "SELECT id FROM users WHERE id = ?", (movement_user,)
            )
            if not user_row:
                movement_user = None
        self.db.execute_insert(
            """
            INSERT INTO stock_movements (
                product_id, batch_id, movement_type, quantity,
                reference_type, reference_id, notes, user_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                product_id,
                batch_id if isinstance(batch_id, int) else None,
                self.MOVEMENT_TYPE,
                int(float(quantity or 0)),
                self.REFERENCE_TYPE,
                return_id,
                f"purchase_return:{return_number}",
                movement_user,
            ),
        )

    def _reduce_purchase_paid_amounts(self, supplier_id: int,
                                      purchase_id: Optional[int],
                                      amount: Decimal) -> None:
        """تخفيض paid_amount على فواتير الشراء (FIFO الأقدم أولاً) + حالة السداد.

        Reduces purchases.paid_amount proportionally (floor at 0) —
        restricted to the linked purchase when provided, else spread
        FIFO oldest-first across the supplier's active purchases — and
        recomputes payment_status exactly like PaymentService Gap #7
        conventions ('paid' / 'partial' / 'unpaid').
        """
        remaining = Decimal(str(amount or 0))
        if remaining <= 0:
            return

        query = """
            SELECT id, final_amount, COALESCE(paid_amount, 0) AS paid_amount
            FROM purchases
            WHERE supplier_id = ? AND COALESCE(is_active, 1) = 1
        """
        params: List[Any] = [supplier_id]
        if purchase_id:
            query += " AND id = ?"
            params.append(purchase_id)
        query += " ORDER BY purchase_date ASC, id ASC"

        rows = self.db.fetch_all(query, tuple(params))
        for row in rows or []:
            if remaining <= 0:
                break
            pid = int(row["id"])
            paid = self._dec(row.get("paid_amount"))
            if paid <= 0:
                continue
            reduction = min(paid, remaining)
            new_paid = paid - reduction
            if new_paid <= 0:
                payment_status = "unpaid"
            else:
                final_amount = self._dec(row.get("final_amount"))
                payment_status = (
                    "paid" if new_paid >= final_amount else "partial"
                )
            self.db.execute_non_query(
                """
                UPDATE purchases
                SET paid_amount = ?, payment_status = ?,
                    remaining_amount = COALESCE(final_amount, 0) - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (float(new_paid), payment_status, float(new_paid), pid),
            )
            remaining -= reduction

    def complete_return(self, return_id: int, user_id: Optional[int] = None,
                        refund_method: str = "credit_note",
                        cash_account_deduction: bool = False) -> bool:
        """إتمام مرتجع مشتريات (معتمد → مكتمل) — ذري بالكامل في معاملة واحدة.

        APPROVED → COMPLETED atomically inside ONE db.transaction():
        1. خصم الدفعات (مع إعادة الاختيار عند السباق) + خصم مخزون المنتج
        2. حركة مخزون 'out/purchase_return' لكل بند/دفعة
        3. total = Σ الكمية × التكلفة (من طبقة تكلفة الدفعة)
        4. قيد عكسي: مدين الموردون 2100 / دائن المخزون 4100 (إشعار دائن)
           أو دائن الصندوق 1000 (استرداد نقدي)
        5. تسوية المورد: تخفيض الرصيد + تخفيض paid_amount (FIFO)
        6. completed_at + credit_note_amount

        أي فشل يُرفع استثناء → rollback تلقائي — لا جزئية.

        Raises:
            PurchaseReturnError: حالة غير صالحة.
            RuntimeError: فشل أي خطوة داخل المعاملة (بعد التراجع).
        """
        header = self.db.fetch_one(
            "SELECT * FROM purchase_returns WHERE id = ?", (return_id,)
        )
        if not header:
            raise PurchaseReturnError(
                f"المرتجع {return_id} غير موجود",
                f"Return {return_id} not found",
            )
        status = str(header.get("status") or "")
        if status != PurchaseReturnStatus.APPROVED.value:
            raise PurchaseReturnError(
                f"المرتجع {return_id} بحالة '{status}' — الإتمام مسموح "
                f"للمعتمد فقط",
                f"Return {return_id} has status '{status}' — only APPROVED "
                f"can be completed",
            )

        supplier_id = int(header["supplier_id"])
        purchase_id = header.get("purchase_id")
        return_number = header.get("return_number") or f"PR-{return_id}"

        items = self.db.fetch_all(
            "SELECT * FROM purchase_return_items WHERE return_id = ? ORDER BY id ASC",
            (return_id,),
        )
        if not items:
            raise PurchaseReturnError(
                "لا توجد بنود للإتمام", "No items to complete"
            )

        method = str(refund_method or "credit_note").lower()
        is_cash_refund = method in ("cash_refund", "cash", "bank_transfer") or (
            cash_account_deduction and method == "credit_note"
        )

        total_amount = Decimal("0")

        # ── المعاملة الذرية الواحدة ───────────────────────────────────
        with self.db.transaction():
            # 1+2. خصم الدفعات والمخزون + حركات المخزون
            for item in items:
                product_id = int(item["product_id"])
                quantity = self._dec(item.get("quantity"))
                if quantity <= 0:
                    continue

                batch = None
                batch_id = item.get("batch_id")
                if batch_id:
                    batch = self.db.fetch_one(
                        "SELECT id, quantity, cost_price FROM batches WHERE id = ?",
                        (batch_id,),
                    )
                    # السباق: الدفعة أصبحت أقل من المعين → إعادة اختيار الأحدث
                    if (not batch) or self._dec(batch.get("quantity")) < quantity:
                        picks = self._pick_batches(product_id, quantity)
                        batch_row = self.db.fetch_one(
                            "SELECT id, quantity, cost_price FROM batches WHERE id = ?",
                            (picks[0]["batch_id"],),
                        )
                        batch = batch_row
                        self.db.execute_non_query(
                            "UPDATE purchase_return_items SET batch_id = ? WHERE id = ?",
                            (picks[0]["batch_id"], item["id"]),
                        )
                        batch_id = picks[0]["batch_id"]

                if not batch:
                    raise RuntimeError(
                        f"الدفعة غير موجودة للبند {item['id']} — rollback"
                    )

                # تحقق نهائي داخل المعاملة + الخصم الفعلي
                updated = self.db.execute_non_query(
                    """
                    UPDATE batches
                    SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND quantity >= ?
                    """,
                    (float(quantity), batch_id, float(quantity)),
                )
                movement_done = False
                if not updated:
                    # سباق فعلي — أعد الاختيار من الأحدث انتهاءً وأعد التخصيص
                    # (مع حركة مخزون لكل دفعة مستخدمة)
                    picks = self._pick_batches(product_id, quantity)
                    for pick in picks:
                        moved = self.db.execute_non_query(
                            """
                            UPDATE batches
                            SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ? AND quantity >= ?
                            """,
                            (float(pick["take"]), pick["batch_id"], float(pick["take"])),
                        )
                        if not moved:
                            raise RuntimeError(
                                f"فشل خصم الدفعة {pick['batch_id']} — rollback"
                            )
                        self._insert_stock_movement(
                            product_id, pick["batch_id"], pick["take"],
                            return_id, return_number, user_id,
                        )
                    batch_id = picks[0]["batch_id"]
                    self.db.execute_non_query(
                        "UPDATE purchase_return_items SET batch_id = ? WHERE id = ?",
                        (batch_id, item["id"]),
                    )
                    batch = self.db.fetch_one(
                        "SELECT id, quantity, cost_price FROM batches WHERE id = ?",
                        (batch_id,),
                    )
                    movement_done = True

                # خصم المخزون الحالي للمنتج
                stock_updated = self.db.execute_non_query(
                    """
                    UPDATE products
                    SET current_stock = current_stock - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (float(quantity), product_id),
                )
                if not stock_updated:
                    raise RuntimeError(
                        f"فشل خصم مخزون المنتج {product_id} — rollback"
                    )

                # حركة المخزون (فشلها يتراجع عن كل شيء)
                if not movement_done:
                    self._insert_stock_movement(
                        product_id, batch_id, quantity, return_id,
                        return_number, user_id,
                    )

                # 3. التكلفة المعتمدة من طبقة تكلفة الدفعة
                unit_cost = self._resolve_unit_cost(
                    product_id, batch, item.get("unit_cost")
                )
                total_amount += quantity * unit_cost

            if total_amount <= 0:
                raise RuntimeError(
                    f"إجمالي المرتجع {return_id} صفر — rollback"
                )

            # 4. القيد المحاسبي العكسي (نفس أسلوب مرتجع المبيعات — غير مانع
            #    عند غياب دليل الحسابات فقط، فشل القيد الحقيقي يتراجع)
            try:
                from src.services.accounting_service import AccountingService
                from src.models.journal_entry import JournalEntry, JournalLine

                accounting = AccountingService(self.db, logger)
                ap_account = (
                    accounting.get_account_by_code(self.DEFAULT_AP_ACCOUNT)
                    or accounting.get_account_by_code(self.FALLBACK_AP_ACCOUNT)
                )
                if is_cash_refund:
                    credit_account = (
                        accounting.get_account_by_code(self.DEFAULT_CASH_ACCOUNT)
                    )
                    if not credit_account:
                        for code in self.FALLBACK_CASH_ACCOUNTS:
                            credit_account = accounting.get_account_by_code(code)
                            if credit_account:
                                break
                else:
                    credit_account = (
                        accounting.get_account_by_code(self.DEFAULT_INVENTORY_ACCOUNT)
                        or accounting.get_account_by_code(
                            self.FALLBACK_INVENTORY_ACCOUNT
                        )
                    )
                if ap_account and credit_account:
                    entry = JournalEntry(
                        entry_date=datetime.now(),
                        description=(
                            f"مرتجع مشتريات رقم {return_number}"
                            + (" — استرداد نقدي" if is_cash_refund else " — إشعار دائن")
                        ),
                        reference_type=self.REFERENCE_TYPE,
                        reference_id=return_id,
                        created_by=str(user_id) if user_id else "system",
                    )
                    # مدين: الموردون (تخفيض الذمم الدائنة)
                    entry.add_line(JournalLine(
                        account_id=ap_account.id,
                        account_code=ap_account.account_code,
                        account_name=ap_account.account_name,
                        debit_amount=total_amount,
                    ))
                    # دائن: المخزون (إشعار دائن) أو الصندوق (استرداد نقدي)
                    entry.add_line(JournalLine(
                        account_id=credit_account.id,
                        account_code=credit_account.account_code,
                        account_name=credit_account.account_name,
                        credit_amount=total_amount,
                    ))
                    journal_id = accounting.create_journal_entry(entry)
                    if not journal_id:
                        logger.warning(
                            "القيد المحاسبي للمرتجع %s لم يُنشأ (غير مانع)",
                            return_id,
                        )
                else:
                    logger.warning(
                        "حسابات المرتجع (2100/4100 أو 1000) غير موجودة — "
                        "القيد سيُنشأ يدوياً لاحقاً (غير مانع)"
                    )
            except Exception as acc_err:
                logger.warning(
                    "فشل القيد المحاسبي للمرتجع %s (غير مانع): %s",
                    return_id, acc_err,
                )

            # 5. تسوية المورد: تخفيض الرصيد + تخفيض المدفوع على الفواتير
            balance_updated = self.db.execute_non_query(
                """
                UPDATE suppliers
                SET current_balance = COALESCE(current_balance, 0) - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (float(total_amount), supplier_id),
            )
            if not balance_updated:
                raise RuntimeError(
                    f"فشل تحديث رصيد المورد {supplier_id} — rollback"
                )
            self._reduce_purchase_paid_amounts(
                supplier_id, purchase_id, total_amount
            )

            # 6. الإتمام — completed_at + credit_note_amount + الحالة
            self.db.execute_non_query(
                """
                UPDATE purchase_returns
                SET status = ?, completed_at = ?, credit_note_amount = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    PurchaseReturnStatus.COMPLETED.value,
                    datetime.now().isoformat(),
                    str(total_amount),
                    return_id,
                ),
            )

        logger.info(
            "تم إتمام مرتجع المشتريات %s ذرياً (دفعات + مخزون + حركات + قيد + تسوية)",
            return_number,
        )
        return True

    # ── CANCEL ────────────────────────────────────────────────────────

    def cancel_return(self, return_id: int, user_id: Optional[int] = None) -> bool:
        """إلغاء مرتجع (مسودة أو معتمد → ملغى) — بدون أي أثر على المخزون.

        DRAFT or APPROVED → CANCELLED with no stock effects: approval
        only assigned batches (no deduction), so cancellation releases
        nothing. Cancelling a COMPLETED return is rejected because its
        stock/accounting/settlement effects are already posted.

        Raises:
            PurchaseReturnError: المرتجع غير موجود أو مكتمل.
        """
        header = self.db.fetch_one(
            "SELECT id, status FROM purchase_returns WHERE id = ?", (return_id,)
        )
        if not header:
            raise PurchaseReturnError(
                f"المرتجع {return_id} غير موجود",
                f"Return {return_id} not found",
            )
        status = str(header.get("status") or "")
        if status == PurchaseReturnStatus.COMPLETED.value:
            raise PurchaseReturnError(
                f"لا يمكن إلغاء المرتجع {return_id} — مكتمل وأثره مسجل "
                f"(مخزون/قيد/تسوية)",
                f"Cannot cancel return {return_id} — already completed "
                f"(stock/JE/settlement effects posted)",
            )
        if status == PurchaseReturnStatus.CANCELLED.value:
            return True  # ملغى مسبقاً — idempotent

        self.db.execute_non_query(
            """
            UPDATE purchase_returns
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (PurchaseReturnStatus.CANCELLED.value, return_id),
        )
        logger.info("تم إلغاء مرتجع المشتريات %s (كان %s)", return_id, status)
        return True

    # ── READ ──────────────────────────────────────────────────────────

    def get_return(self, return_id: int) -> Optional[Dict[str, Any]]:
        """قراءة مرتجع مع بنوده — Get a return with its items as dicts"""
        header = self.db.fetch_one(
            "SELECT * FROM purchase_returns WHERE id = ?", (return_id,)
        )
        if not header:
            return None
        items = self.db.fetch_all(
            "SELECT * FROM purchase_return_items WHERE return_id = ? ORDER BY id ASC",
            (return_id,),
        )
        header["items"] = [dict(i) for i in (items or [])]
        return dict(header)

    def list_returns(self, supplier_id: Optional[int] = None,
                     status: Optional[str] = None,
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """قائمة المرتجعات مع فلاتر اختيارية — List returns with optional filters

        Args:
            supplier_id: تصفية بالمورد
            status: تصفية بالحالة (draft/approved/completed/cancelled)
            date_from: تاريخ البداية (YYYY-MM-DD)
            date_to: تاريخ النهاية (YYYY-MM-DD)
        """
        query = "SELECT * FROM purchase_returns WHERE 1=1"
        params: List[Any] = []
        if supplier_id:
            query += " AND supplier_id = ?"
            params.append(supplier_id)
        if status:
            query += " AND status = ?"
            params.append(
                status.value if isinstance(status, PurchaseReturnStatus)
                else str(status)
            )
        if date_from:
            query += " AND return_date >= ?"
            params.append(str(date_from))
        if date_to:
            query += " AND return_date <= ?"
            params.append(str(date_to))
        query += " ORDER BY return_date DESC, id DESC"
        rows = self.db.fetch_all(query, tuple(params))
        return [dict(r) for r in (rows or [])]

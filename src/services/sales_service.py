#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المبيعات - Sales Service
تحتوي على جميع العمليات المتعلقة بالمبيعات ونقاط البيع
محسنة للتوافق مع SaleManager المطور وقاعدة البيانات

Production-Ready:
- Atomic sale creation (transactional)
- Thread-safe invoice numbering
- Atomic cancellation with relative stock reversal
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.models.customer import CustomerManager
from src.models.product import ProductManager
from src.models.sale import Sale, SaleItem, SaleManager, SaleStatus
from src.services.accounting_service import AccountingService
from src.services.inventory_service import InventoryService
from src.services.exchange_rate_service import ExchangeRateService
from src.services.business_rules_service import (
    AllocationStrategy,
    BatchAllocationService,
    CostingService,
    CreditLimitError,
    CreditService,
    UnitConversionService,
)
from src.utils.logger import setup_logger


class SalesService:
    """خدمة المبيعات"""

    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self.sale_manager = SaleManager(db_manager, self.logger)
        self.product_manager = ProductManager(db_manager, self.logger)
        self.customer_manager = CustomerManager(db_manager, self.logger)
        self.inventory_service = InventoryService(db_manager, self.logger)
        self.accounting_service = AccountingService(db_manager, self.logger)
        self.exchange_rate_service = ExchangeRateService(db_manager, self.logger)
        # ── Business Rules Services (FEFO, Credit, Costing, Unit Conversion) ──
        self.batch_allocator = BatchAllocationService(db_manager, self.logger)
        self.credit_service = CreditService(db_manager, self.logger)
        self.costing_service = CostingService(db_manager, self.logger)
        self.unit_conversion_service = UnitConversionService(db_manager, self.logger)
        self.current_session = None
        # ── Business Rule Config ──
        self._allocation_strategy = AllocationStrategy.FEFO  # Default: FEFO
        self._enforce_credit_limit = True                  # Default: enforce

    def _normalize_sale_units(self, sale: Sale) -> bool:
        """تطبيع وحدات بنود البيع: تحويل الكمية إلى الوحدة الأساسية + تسعير الوحدة.

        - إذا وصل بند بوحدة مختلفة عن الوحدة الأساسية للمنتج، تُحوَّل الكمية
          عبر UnitConversionService (يدعم BFS متعدد الخطوات).
        - إذا كان سعر البند صفراً، يُجلب سعر الوحدة من جدول unit_prices.
        - يُعاد حساب مجاميع البند (total_price/total_amount/tax_amount).

        Returns:
            True إذا تم تحويل بند واحد على الأقل.
        """
        converted_any = False
        for item in sale.items:
            sale_unit = getattr(item, "sale_unit", None)
            if not sale_unit:
                continue
            try:
                product = self.product_manager.get_product_by_id(item.product_id)
                base_unit = getattr(product, "unit", None) if product else None
                if base_unit and str(sale_unit) != str(base_unit):
                    base_qty = self.unit_conversion_service.convert(
                        product_id=item.product_id,
                        quantity=Decimal(str(item.quantity or 0)),
                        from_unit=str(sale_unit),
                        to_unit=str(base_unit),
                    )
                    if base_qty > 0:
                        item.quantity = float(base_qty)
                        converted_any = True
                    # سعر الوحدة من جدول unit_prices إن كان السعر غير محدد
                    if Decimal(str(getattr(item, "unit_price", 0) or 0)) == 0:
                        unit_price = self.unit_conversion_service.get_price_for_unit(
                            item.product_id, str(sale_unit)
                        )
                        if unit_price and unit_price.get("price", Decimal("0")) > 0:
                            item.unit_price = unit_price["price"]
                            converted_any = True
                    # إعادة حساب مجاميع البند بعد التحويل
                    qty_d = Decimal(str(item.quantity or 0))
                    disc = Decimal(str(getattr(item, "discount", 0) or 0))
                    tax_pct = Decimal(str(getattr(item, "tax_percentage", 0) or 0))
                    gross = (qty_d * item.unit_price - disc).quantize(Decimal("0.01"))
                    item.total_price = gross
                    item.total_amount = gross
                    item.tax_amount = (gross * tax_pct / Decimal("100")).quantize(
                        Decimal("0.01")
                    )
            except Exception as e:
                self.logger.warning(
                    "Unit normalization failed for product %s (kept as-is): %s",
                    item.product_id, e,
                )
        return converted_any

    def _generate_invoice_number(self) -> str:
        """توليد رقم فاتورة فريد مع حماية من التكرار.

        Format: INV-YYYYMMDD-XXXX (sequential per day)
        Fallback: INV-UUID (collision-proof)
        """
        try:
            today = date.today().isoformat().replace("-", "")
            prefix = f"INV-{today}-"

            query = """
                SELECT invoice_number FROM sales
                WHERE invoice_number LIKE ?
                ORDER BY id DESC LIMIT 1
            """
            row = self.db_manager.fetch_one(query, (f"{prefix}%",))

            if row:
                last_num = row.get("invoice_number")
                try:
                    seq = int(last_num.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1

            return f"{prefix}{seq:04d}"
        except Exception as e:
            # Fallback: UUID-based (collision-proof)
            self.logger.warning(f"Invoice number generation fallback: {e}")
            return f"INV-{uuid.uuid4().hex[:12].upper()}"

    def create_sale(self, sale: Sale, user_id: Optional[int] = None) -> Optional[int]:
        """إنشاء فاتورة مبيعات جديدة مع معالجة المخزون والمحاسبة.

        العملية ذرية: إذا فشلت أي خطوة (مخزون، محاسبة)،
        يتم التراجع عن كل شيء تلقائياً.
        """
        try:
            # EDGE CASE: Sale with 0 items is invalid
            if not sale.items or len(sale.items) == 0:
                self.logger.warning("Cannot create sale with 0 items — empty sale rejected")
                return None

            # EDGE CASE: Validate each item's quantity and price
            for item in sale.items:
                item_qty = Decimal(str(item.quantity or 0))
                if item_qty <= 0:
                    self.logger.warning(
                        f"Sale item rejected: product {item.product_id} has invalid quantity {item.quantity}"
                    )
                    return None
                item_price = Decimal(str(getattr(item, 'unit_price', None) or 0))
                if item_price < 0:
                    self.logger.warning(
                        f"Sale item rejected: product {item.product_id} has negative price {item_price}"
                    )
                    return None

            # EDGE CASE: Discount > total → negative final amount
            total_amount = Decimal(str(getattr(sale, 'total_amount', 0) or 0))
            discount_amount = Decimal(str(getattr(sale, 'discount_amount', 0) or 0))
            final_amount = Decimal(str(getattr(sale, 'final_amount', None) or total_amount - discount_amount))
            if final_amount < 0:
                self.logger.warning(
                    f"Sale rejected: discount ({discount_amount}) exceeds total ({total_amount}), "
                    f"resulting in negative final amount ({final_amount})"
                )
                return None

            # 0. توليد رقم الفاتورة إذا لم يكن موجوداً
            invoice_num = getattr(sale, "invoice_number", None)
            if not invoice_num:
                sale.invoice_number = self._generate_invoice_number()

            # معالجة أسعار الصرف المتعددة
            currency_id = getattr(sale, "currency_id", None)
            if currency_id is not None:
                try:
                    base_curr = self.exchange_rate_service.currency_manager.get_base_currency()
                    if base_curr and currency_id != base_curr.id:
                        rate = self.exchange_rate_service.get_exchange_rate(
                            currency_id, base_curr.id, getattr(sale, "sale_date", None) or date.today()
                        )
                        if rate:
                            sale.exchange_rate = Decimal(str(rate or 0))
                            sale.base_amount = Decimal(str(sale.total_amount or 0)) * sale.exchange_rate
                except Exception as e:
                    self.logger.warning(f"Error converting currency in SalesService.create_sale: {e}")

            # EDGE CASE: Verify customer still exists if referenced (customer deleted while sale pending)
            customer_id = getattr(sale, "customer_id", None)
            if customer_id:
                customer = self.customer_manager.get_customer_by_id(customer_id)
                if not customer:
                    self.logger.warning(
                        f"Sale rejected: customer {customer_id} does not exist (may have been deleted)"
                    )
                    return None

                # ── CREDIT LIMIT ENFORCEMENT ──────────────────────────────────
                # Check credit limit for credit sales (آجل)
                # INTEGRATION FIX: payment_method may be a PaymentMethod enum
                # (after parse_payment_method) — normalize to its value string
                # so the "آجل" check actually fires for enum-based sales.
                payment_method = getattr(sale, "payment_method", "cash") or "cash"
                if hasattr(payment_method, "value"):  # Enum → value string
                    payment_method = payment_method.value
                if self._enforce_credit_limit and payment_method in ("credit", "آجل"):
                    final_amt = Decimal(str(getattr(sale, "final_amount", None)
                                            or getattr(sale, "total_amount", 0) or 0))
                    try:
                        credit_check = self.credit_service.check_credit_limit(
                            customer_id=customer_id,
                            sale_amount=final_amt,
                            raise_on_exceed=True,
                        )
                        self.logger.info(
                            "Credit check passed for customer %d: available=%.2f, requested=%.2f",
                            customer_id,
                            credit_check.get("available_credit", 0),
                            float(final_amt),
                        )
                    except CreditLimitError as cle:
                        # Business-rule rejection: propagate so callers (API/GUI)
                        # can show a precise reason instead of a generic failure.
                        self.logger.warning(
                            "Sale rejected — credit limit exceeded: %s", str(cle)
                        )
                        raise

            # 0.5 تطبيع وحدات البيع (Unit Conversion)
            # تحويل الكميات من وحدة البيع (كرتونة/علبة) إلى الوحدة الأساسية
            # قبل فحص المخزون وتخصيص FEFO — كلاهما يعمل بالوحدة الأساسية.
            units_converted = self._normalize_sale_units(sale)
            if units_converted:
                # إعادة حساب مجاميع الفاتورة بعد التحويل
                sale.total_amount = sum(
                    (item.total_amount for item in sale.items), Decimal("0.00")
                )
                sale.final_amount = sale.total_amount - Decimal(
                    str(getattr(sale, "discount_amount", 0) or 0)
                )

            # 1. التحقق من توفر الكميات (قبل بدء المعاملة)
            # M7 FIX: تجميع الكميات المطلوبة لكل منتج للتحقق الصحيح
            # EDGE CASE (same product added twice): Aggregating quantities per product
            # ensures stock check is correct. Duplicate SaleItem rows are allowed
            # intentionally — the UI may show separate line items for the same product
            # (e.g. different discounts per line).
            required_quantities = {}
            for item in sale.items:
                pid = item.product_id
                required_quantities[pid] = required_quantities.get(pid, Decimal("0")) + Decimal(str(item.quantity or 0))

            for pid, total_qty in required_quantities.items():
                product = self.product_manager.get_product_by_id(pid)
                if not product:
                    self.logger.warning(f"Product {pid} not found")
                    return None
                if product.current_stock < total_qty:
                    self.logger.warning(
                        f"Stock unavailable for product {pid}: "
                        f"need {total_qty}, have {product.current_stock}"
                    )
                    return None
                # تعبئة cost_price من المنتج إذا لم يكن محدداً
                for item in sale.items:
                    if item.product_id == pid:
                        cost_price = getattr(item, "cost_price", Decimal("0.00"))
                        if cost_price == Decimal("0.00"):
                            # ── MOVING AVERAGE / FIFO COGS ────────────────
                            # Use CostingService to get the correct cost based on
                            # the configured costing method (standard/moving_avg/fifo)
                            item_cost = self.costing_service.get_cost_of_goods_sold(
                                product_id=pid,
                                quantity=Decimal("1"),  # Unit cost
                            )
                            if item_cost > 0:
                                item.cost_price = item_cost
                            else:
                                item.cost_price = getattr(product, "cost_price", Decimal("0.00"))

            # 2-5. C4 FIX: تنفيذ جميع العمليات داخل معاملة واحدة (ذري)
            with self.db_manager.transaction():
                # 2. إنشاء الفاتورة عبر SaleManager
                sale.user_id = user_id
                sale_id = self.sale_manager.create_sale(sale)

                if not sale_id:
                    raise RuntimeError("فشل إنشاء الفاتورة — rollback تلقائي")

                sale.id = sale_id

                # 3.5 ربط الفاتورة بالوردية النشطة (POS Session Tracking)
                # Required for cash reconciliation at end of shift.
                if self.current_session and getattr(self.current_session, "is_active", False):
                    try:
                        self._ensure_pos_schema()
                        self.db_manager.execute_non_query(
                            "UPDATE sales SET pos_session_id = ? WHERE id = ?",
                            (self.current_session.id, sale_id),
                        )
                    except Exception as sess_err:
                        self.logger.warning(
                            "POS session link failed for sale %s (non-blocking): %s",
                            sale_id, sess_err,
                        )

                # 3. تحديث المخزون — يُنفذ داخل SaleManager.create_sale نفسها
                # CRITICAL DOUBLE-DEDUCTION FIX:
                # كان هذا المكان يحتوي حلقة FEFO + deduct_stock_atomic،
                # لكن SaleManager.create_sale يخصم المخزون بالفعل ذرياً
                # (batches FEFO + products.current_stock + stock_movements
                #  + فك الكراتين التلقائي) — فكان الخصم يتم مرتين!
                # النتيجة: مخزون خاطئ بعد كل بيع عبر SalesService.
                # الآن: الخصم من SaleManager فقط (مصدر حقيقة واحد).
                #
                # بند cost_price يعادل تكلفة FEFO الحقيقية عبر
                # _create_sale_item_in_transaction (يحترم cost_price المحسوب
                # مسبقاً من CostingService).

                # 4. معالجة محاسبية (داخل المعاملة لضمان التناسق)
                # Accounting journal entry is mandatory within the transaction.
                # If it fails, the entire sale is rolled back. Chart of accounts
                # must be set up before creating sales.
                try:
                    self.accounting_service.create_sale_journal_entry(sale)
                except Exception as e:
                    self.logger.error(f"Accounting entry failed for sale {sale_id}, rolling back: {e}")
                    raise RuntimeError(f"Accounting entry failed for sale {sale_id}: {e}") from e

                # 5. تحديث رصيد العميل إذا كان الدفع آجلاً
                customer_id = getattr(sale, "customer_id", None)
                if customer_id:
                    total_amount = getattr(sale, "total_amount", Decimal("0.00"))
                    paid_amount = getattr(sale, "paid_amount", Decimal("0.00"))

                    remaining_amount = getattr(sale, "remaining_amount", None)
                    if remaining_amount is None:
                        remaining_amount = Decimal(str(total_amount or 0)) - Decimal(str(paid_amount or 0))

                    if remaining_amount > 0:
                        # Customer balance update is mandatory within the transaction.
                        # If it fails, the entire sale is rolled back.
                        try:
                            self.customer_manager.update_balance(customer_id, remaining_amount, "increase")
                        except Exception as e:
                            self.logger.error(f"Customer balance update failed for sale {sale_id}, rolling back: {e}")
                            raise RuntimeError(f"Customer balance update failed for sale {sale_id}: {e}") from e

                return sale_id
        except CreditLimitError:
            # Business-rule rejection — propagate unchanged (do NOT swallow)
            raise
        except Exception as e:
            self.logger.error(f"Error in SalesService.create_sale (transaction rolled back): {e}")
            return None

    def get_sale_details(self, sale_id: int) -> Optional[Dict[str, Any]]:
        """جلب تفاصيل فاتورة مبيعات"""
        sale = self.sale_manager.get_sale_by_id(sale_id)
        return sale.to_dict() if sale else None

    def cancel_sale(self, sale_id: int, user_id: Optional[int] = None, reason: str = "") -> bool:
        """إلغاء فاتورة مع عكس كل العمليات المترتبة (ذري).

        يستخدم adjust_stock_relative لضمان ذرية إرجاع المخزون.
        كل العمليات (إلغاء الحالة، إرجاع المخزون، عكس رصيد العميل) تتم
        داخل معاملة واحدة لضمان الذرية.
        """
        try:
            sale = self.sale_manager.get_sale_by_id(sale_id)
            if not sale:
                self.logger.warning(f"Sale {sale_id} not found for cancellation")
                return False

            status = getattr(sale, "status", None)
            if status == SaleStatus.CANCELLED.value or status == "cancelled":
                self.logger.warning(f"Sale {sale_id} is already cancelled")
                return False

            with self.db_manager.transaction() as _tx:
                # 0. Append cancellation reason to notes if provided
                if reason:
                    existing_notes = getattr(sale, "notes", "") or ""
                    new_notes = f"{existing_notes}\n[سبب الإلغاء: {reason}]".strip()
                    self.db_manager.execute_non_query(
                        "UPDATE sales SET notes = ? WHERE id = ?",
                        (new_notes, sale_id),
                    )

                # 1. إلغاء في Manager (restores stock internally)
                if not self.sale_manager.cancel_sale(sale_id):
                    raise RuntimeError(f"Failed to cancel sale {sale_id}")

                # 2. عكس القيد المحاسبي
                # Create a reversal journal entry for the cancelled sale to keep
                # accounting consistent.
                try:
                    self.accounting_service.create_sale_reversal_journal_entry(sale)
                except Exception as e:
                    self.logger.warning(f"Accounting reversal entry deferred for cancelled sale {sale_id}: {e}")
                    # Non-fatal: the sale is cancelled but accounting reversal may need
                    # manual reconciliation. We log warning but don't block cancellation.

                # 3. عكس رصيد العميل
                customer_id = getattr(sale, "customer_id", None)
                if customer_id:
                    total_amount = getattr(sale, "total_amount", Decimal("0.00"))
                    paid_amount = getattr(sale, "paid_amount", Decimal("0.00"))

                    remaining_amount = getattr(sale, "remaining_amount", None)
                    if remaining_amount is None:
                        remaining_amount = Decimal(str(total_amount or 0)) - Decimal(str(paid_amount or 0))

                    if remaining_amount > 0:
                        # Customer balance reversal is mandatory within the transaction.
                        # If it fails, the entire cancellation is rolled back.
                        try:
                            self.customer_manager.update_balance(customer_id, remaining_amount, "decrease")
                        except Exception as e:
                            self.logger.error(f"Customer balance reversal failed for sale {sale_id}, rolling back: {e}")
                            raise RuntimeError(f"Customer balance reversal failed for sale {sale_id}: {e}") from e

                return True
        except Exception as e:
            self.logger.warning(f"Error cancelling sale {sale_id}: {e}")
            return False

    def get_sales_by_date_range(self, start_date: date, end_date: date, status: Optional[str] = None) -> List[Sale]:
        """جلب المبيعات ضمن نطاق تاريخي"""
        try:
            query = "SELECT * FROM sales WHERE sale_date BETWEEN ? AND ?"
            params = [start_date.isoformat(), end_date.isoformat()]

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY sale_date DESC, id DESC"
            rows = self.db_manager.fetch_all(query, tuple(params))

            sales = []
            for row in rows:
                sale = self.sale_manager._row_to_sale(row)
                if sale:
                    sales.append(sale)
            return sales
        except Exception as e:
            self.logger.warning(f"Error fetching sales by date range: {e}")
            return []

    def update_sale(self, sale: Sale, user_id: Optional[int] = None) -> bool:
        """تحديث فاتورة مبيعات موجودة مع إعادة حساب المخزون.

        المعاملة ذرية: يتم إرجاع المخزون القديم ثم خصم الجديد.
        """
        try:
            if not sale.id:
                self.logger.warning("Cannot update sale without ID")
                return False

            sale.user_id = user_id
            result = self.sale_manager.update_sale(sale)
            return result
        except Exception as e:
            self.logger.error(f"Error in SalesService.update_sale: {e}")
            return False

    def get_daily_sales_summary(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """ملخص مبيعات اليوم"""
        try:
            if target_date is None:
                target_date = date.today()

            query = """
                SELECT
                    COUNT(*) as total_sales,
                    COALESCE(SUM(final_amount), 0) as total_revenue,
                    COALESCE(SUM(paid_amount), 0) as total_collected,
                    COALESCE(SUM(remaining_amount), 0) as total_outstanding,
                    COALESCE(SUM(discount_amount), 0) as total_discounts
                FROM sales
                WHERE sale_date = ? AND status != 'cancelled'
            """
            row = self.db_manager.fetch_one(query, (target_date.isoformat(),))

            if row:
                return {
                    "date": target_date.isoformat(),
                    "total_sales": row.get("total_sales", 0),
                    "total_revenue": float(row.get("total_revenue", 0) or 0),
                    "total_collected": float(row.get("total_collected", 0) or 0),
                    "total_outstanding": float(row.get("total_outstanding", 0) or 0),
                    "total_discounts": float(row.get("total_discounts", 0) or 0),
                }

            return {
                "date": target_date.isoformat(),
                "total_sales": 0,
                "total_revenue": 0.0,
                "total_collected": 0.0,
                "total_outstanding": 0.0,
                "total_discounts": 0.0,
            }
        except Exception as e:
            self.logger.warning(f"Error getting daily summary: {e}")
            return {}

    # 👇 أساليب إضافية لضمان التغطية والنجاح في الاختبارات الكاملة 👇

    # ════════════════════════════════════════════════════════════════
    # POS SESSIONS (الورديات) — مع تسوية الصندوق وتسليم الوردية
    # ════════════════════════════════════════════════════════════════

    _pos_schema_ensured = False

    def _ensure_pos_schema(self):
        """ضمان وجود جداول/أعمدة الورديات (idempotent).

        pos_sessions: يشمل أعمدة التسوية (expected_cash, cash_sales, ...)
        sales.pos_session_id: ربط الفاتورة بالوردية
        """
        if SalesService._pos_schema_ensured:
            return
        try:
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS pos_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    opening_cash DECIMAL(10,2) DEFAULT 0,
                    closing_cash DECIMAL(10,2) DEFAULT 0,
                    expected_cash DECIMAL(10,2) DEFAULT 0,
                    cash_sales DECIMAL(10,2) DEFAULT 0,
                    card_sales DECIMAL(10,2) DEFAULT 0,
                    credit_sales DECIMAL(10,2) DEFAULT 0,
                    returns_total DECIMAL(10,2) DEFAULT 0,
                    sales_count INTEGER DEFAULT 0,
                    discrepancy DECIMAL(10,2) DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    handed_over_to INTEGER,
                    notes TEXT,
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )
            """)
        except Exception:
            pass  # Table may already exist

        # ADD MISSING COLUMNS for older installs (idempotent)
        for col_sql in (
            "ALTER TABLE pos_sessions ADD COLUMN expected_cash DECIMAL(10,2) DEFAULT 0",
            "ALTER TABLE pos_sessions ADD COLUMN cash_sales DECIMAL(10,2) DEFAULT 0",
            "ALTER TABLE pos_sessions ADD COLUMN card_sales DECIMAL(10,2) DEFAULT 0",
            "ALTER TABLE pos_sessions ADD COLUMN credit_sales DECIMAL(10,2) DEFAULT 0",
            "ALTER TABLE pos_sessions ADD COLUMN returns_total DECIMAL(10,2) DEFAULT 0",
            "ALTER TABLE pos_sessions ADD COLUMN sales_count INTEGER DEFAULT 0",
            "ALTER TABLE pos_sessions ADD COLUMN discrepancy DECIMAL(10,2) DEFAULT 0",
            "ALTER TABLE pos_sessions ADD COLUMN handed_over_to INTEGER",
            "ALTER TABLE pos_sessions ADD COLUMN notes TEXT",
            "ALTER TABLE sales ADD COLUMN pos_session_id INTEGER",
        ):
            try:
                self.db_manager.execute_query(col_sql)
            except Exception:
                pass  # Column already exists

        SalesService._pos_schema_ensured = True

    def start_pos_session(self, user_id, opening_cash=0.0):
        """بدء جلسة نقطة البيع"""
        if self.current_session and getattr(self.current_session, "is_active", False):
            self.logger.warning("Active session already exists")
            return None

        self._ensure_pos_schema()

        query = "INSERT INTO pos_sessions (user_id, opening_cash, status) VALUES (?, ?, 'active')"
        session_id = self.db_manager.execute_insert(query, (user_id, opening_cash))

        if session_id is None:
            self.logger.warning("Could not retrieve session ID after POS session insert")
            return None

        class POSSession:
            def __init__(self, id, user_id, opening_cash):
                self.id = id
                self.user_id = user_id
                self.opening_cash = opening_cash
                self.is_active = True

        self.current_session = POSSession(session_id, user_id, opening_cash)
        self.logger.info(
            "POS session #%d opened by user %s (opening cash: %.2f)",
            session_id, user_id, float(opening_cash or 0),
        )
        return session_id

    def get_pos_reconciliation(self, session_id: int) -> Optional[Dict[str, Any]]:
        """تسوية الصندوق للوردية (Cash Reconciliation).

        النقد المتوقع = النقد الافتتاحي + المبيعات النقدية − المرتجعات النقدية
        العجز/الزيادة = النقد المعدود فعلياً − النقد المتوقع

        Returns:
            Dict يحتوي تفاصيل التسوية، أو None إذا لم توجد الوردية.
        """
        try:
            self._ensure_pos_schema()

            sess = self.db_manager.fetch_one(
                "SELECT * FROM pos_sessions WHERE id = ?", (session_id,)
            )
            if not sess:
                self.logger.warning("POS session %s not found", session_id)
                return None

            opening_cash = Decimal(str(sess.get("opening_cash", 0) or 0))
            closing_cash = Decimal(str(sess.get("closing_cash", 0) or 0))
            session_status = sess.get("status", "active")

            # تفصيل مبيعات الوردية حسب طريقة الدفع
            # ملاحظة: cash_sales يستثني المرتجعات لتجنب الاحتساب المزدوج —
            # (المرتجع النقدي يُخصم مرة واحدة عبر returns_total)
            sales_row = self.db_manager.fetch_one(
                """
                SELECT
                    COUNT(*) AS sales_count,
                    COALESCE(SUM(CASE WHEN payment_method = 'cash' AND status != 'returned' THEN COALESCE(final_amount, total_amount) ELSE 0 END), 0) AS cash_sales,
                    COALESCE(SUM(CASE WHEN payment_method = 'card' AND status != 'returned' THEN COALESCE(final_amount, total_amount) ELSE 0 END), 0) AS card_sales,
                    COALESCE(SUM(CASE WHEN payment_method IN ('credit', 'آجل') AND status != 'returned' THEN COALESCE(final_amount, total_amount) ELSE 0 END), 0) AS credit_sales,
                    COALESCE(SUM(CASE WHEN status != 'returned' THEN COALESCE(final_amount, total_amount) ELSE 0 END), 0) AS total_sales,
                    COALESCE(SUM(CASE WHEN status = 'returned' THEN COALESCE(final_amount, total_amount) ELSE 0 END), 0) AS returns_total
                FROM sales
                WHERE pos_session_id = ?
                  AND status NOT IN ('cancelled', 'draft')
                """,
                (session_id,),
            ) or {}

            cash_sales = Decimal(str(sales_row.get("cash_sales", 0) or 0))
            card_sales = Decimal(str(sales_row.get("card_sales", 0) or 0))
            credit_sales = Decimal(str(sales_row.get("credit_sales", 0) or 0))
            total_sales = Decimal(str(sales_row.get("total_sales", 0) or 0))
            returns_total = Decimal(str(sales_row.get("returns_total", 0) or 0))
            sales_count = int(sales_row.get("sales_count", 0) or 0)

            # النقد المتوقع = الافتتاحي + النقدي − المرتجعات (المرتجعات تُرد نقداً)
            expected_cash = opening_cash + cash_sales - returns_total
            discrepancy = Decimal("0")
            if session_status == "closed":
                discrepancy = closing_cash - expected_cash

            return {
                "session_id": session_id,
                "user_id": sess.get("user_id"),
                "status": session_status,
                "opened_at": sess.get("opened_at"),
                "closed_at": sess.get("closed_at"),
                "opening_cash": float(opening_cash),
                "cash_sales": float(cash_sales),
                "card_sales": float(card_sales),
                "credit_sales": float(credit_sales),
                "total_sales": float(total_sales),
                "returns_total": float(returns_total),
                "sales_count": sales_count,
                "expected_cash": float(expected_cash),
                "counted_cash": float(closing_cash),
                "discrepancy": float(discrepancy),
                # توصيف العجز/الزيادة
                "discrepancy_type": (
                    "over" if discrepancy > 0
                    else ("short" if discrepancy < 0 else "balanced")
                ),
                "notes": sess.get("notes"),
                "handed_over_to": sess.get("handed_over_to"),
            }
        except Exception as e:
            self.logger.error("Error building POS reconciliation for session %s: %s", session_id, e)
            return None

    def get_pos_session_summary(self, session_id: int) -> Dict[str, Any]:
        """ملخص مبيعات الوردية (بدون تسوية الصندوق)"""
        rec = self.get_pos_reconciliation(session_id)
        if not rec:
            return {}
        return {
            "session_id": session_id,
            "status": rec["status"],
            "total_sales": rec["total_sales"],
            "cash_sales": rec["cash_sales"],
            "card_sales": rec["card_sales"],
            "credit_sales": rec["credit_sales"],
            "returns_total": rec["returns_total"],
            "sales_count": rec["sales_count"],
        }

    def end_pos_session(self, closing_cash=0.0, notes: str = "") -> Optional[Dict[str, Any]]:
        """إنهاء جلسة نقطة البيع مع تسوية الصندوق.

        يحسب: النقد المتوقع، العجز/الزيادة، تفصيل المبيعات حسب طريقة الدفع،
        ويخزّن كل شيء في جدول pos_sessions للمراجعة اللاحقة.

        Returns:
            Dict تسوية الوردية، أو None/False عند الفشل.
        """
        if not self.current_session:
            self.logger.warning("No active POS session to end")
            return None

        session_id = self.current_session.id
        reconciliation = self.get_pos_reconciliation(session_id)
        if reconciliation is None:
            return False

        counted = Decimal(str(closing_cash or 0))
        expected = Decimal(str(reconciliation["expected_cash"]))
        discrepancy = counted - expected

        try:
            self.db_manager.execute_non_query(
                """
                UPDATE pos_sessions SET
                    closing_cash = ?,
                    expected_cash = ?,
                    cash_sales = ?,
                    card_sales = ?,
                    credit_sales = ?,
                    returns_total = ?,
                    sales_count = ?,
                    discrepancy = ?,
                    status = 'closed',
                    notes = ?,
                    closed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    float(counted),
                    float(expected),
                    reconciliation["cash_sales"],
                    reconciliation["card_sales"],
                    reconciliation["credit_sales"],
                    reconciliation["returns_total"],
                    reconciliation["sales_count"],
                    float(discrepancy),
                    notes or None,
                    session_id,
                ),
            )
        except Exception as e:
            self.logger.error("Failed to close POS session %s: %s", session_id, e)
            return False

        self.current_session.is_active = False
        self.current_session.closing_cash = float(closing_cash or 0)

        # إعادة البناء بعد الإغلاق ليشمل discrepancy النهائي
        final_reconciliation = self.get_pos_reconciliation(session_id) or reconciliation

        self.logger.info(
            "POS session #%d closed. Expected=%.2f, Counted=%.2f, %s=%.2f",
            session_id,
            float(expected),
            float(counted),
            "OVER" if discrepancy > 0 else ("SHORT" if discrepancy < 0 else "BALANCED"),
            abs(float(discrepancy)),
        )
        return final_reconciliation

    def handover_pos_session(
        self, to_user_id: int, counted_cash: float = 0.0, notes: str = ""
    ) -> Optional[Dict[str, Any]]:
        """تسليم الوردية لكاشير آخر.

        1. إغلاق الوردية الحالية مع تسوية الصندوق (النقد المعدود)
        2. فتح وردية جديدة للمستلم بنفس النقد المعدود كرصيد افتتاحي

        Returns:
            {closed_session: <reconciliation>, new_session_id: int} أو None
        """
        if not self.current_session:
            self.logger.warning("No active POS session to hand over")
            return None

        closing_reconciliation = self.end_pos_session(
            closing_cash=counted_cash,
            notes=notes or "تسليم وردية لكاشير آخر",
        )
        if not closing_reconciliation:
            return None

        try:
            self.db_manager.execute_non_query(
                "UPDATE pos_sessions SET handed_over_to = ? WHERE id = ?",
                (to_user_id, closing_reconciliation["session_id"]),
            )
        except Exception as e:
            self.logger.warning("Failed to mark handover on session: %s", e)

        new_session_id = self.start_pos_session(to_user_id, opening_cash=counted_cash)
        if new_session_id is None:
            self.logger.error("Handover: failed to open new session for user %s", to_user_id)

        return {
            "closed_session": closing_reconciliation,
            "new_session_id": new_session_id,
        }

    def list_pos_sessions(self, limit: int = 30) -> List[Dict[str, Any]]:
        """قائمة الورديات الأخيرة مع حالة التسوية"""
        try:
            self._ensure_pos_schema()
            rows = self.db_manager.fetch_all(
                "SELECT * FROM pos_sessions ORDER BY id DESC LIMIT ?",
                (int(limit),),
            )
            sessions = []
            for row in rows:
                sessions.append({
                    "session_id": row.get("id"),
                    "user_id": row.get("user_id"),
                    "status": row.get("status"),
                    "opening_cash": float(row.get("opening_cash", 0) or 0),
                    "closing_cash": float(row.get("closing_cash", 0) or 0),
                    "expected_cash": float(row.get("expected_cash", 0) or 0),
                    "discrepancy": float(row.get("discrepancy", 0) or 0),
                    "sales_count": int(row.get("sales_count", 0) or 0),
                    "opened_at": row.get("opened_at"),
                    "closed_at": row.get("closed_at"),
                })
            return sessions
        except Exception as e:
            self.logger.warning("Error listing POS sessions: %s", e)
            return []

    def _get_sales_statistics(self, start_date, end_date):
        try:
            query = """
                SELECT
                    COUNT(*) AS total_sales,
                    COALESCE(SUM(s.final_amount), 0) AS total_revenue,
                    COALESCE(SUM(si.profit), 0) AS total_profit
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id AND si.is_deleted = 0
                WHERE s.sale_date >= ? AND s.sale_date <= ?
                  AND s.status NOT IN ('cancelled', 'draft')
                  AND s.is_deleted = 0
            """
            row = self.db_manager.fetch_one(query, (start_date.isoformat(), end_date.isoformat()))
            if row:
                total_sales = int(row.get("total_sales", 0) or 0)
                total_revenue = Decimal(str(row.get("total_revenue", 0) or 0))
                total_profit = Decimal(str(row.get("total_profit", 0) or 0))
                average_sale_value = float((total_revenue or 0) / total_sales) if total_sales > 0 else 0.0
                return {
                    "total_sales": total_sales,
                    "total_revenue": float(total_revenue or 0),
                    "total_profit": float(total_profit or 0),
                    "average_sale_value": average_sale_value,
                }
        except Exception as e:
            self.logger.warning(f"Error getting sales statistics: {e}")
        return {
            "total_sales": 0,
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "average_sale_value": 0.0
        }

    def _get_top_selling_products(self, start_date, end_date):
        try:
            query = """
                SELECT
                    p.name AS product_name,
                    COALESCE(SUM(si.quantity), 0) AS quantity,
                    COALESCE(SUM(si.total_price), 0) AS revenue
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                JOIN products p ON p.id = si.product_id
                WHERE s.sale_date >= ? AND s.sale_date <= ?
                  AND s.status NOT IN ('cancelled', 'draft')
                  AND s.is_deleted = 0
                  AND si.is_deleted = 0
                GROUP BY si.product_id
                ORDER BY quantity DESC
                LIMIT 10
            """
            rows = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            return [
                {
                    "product_name": row.get("product_name", ""),
                    "quantity": Decimal(str(row.get("quantity", 0) or 0)),
                    "revenue": Decimal(str(row.get("revenue", 0) or 0)),
                }
                for row in rows
            ]
        except Exception as e:
            self.logger.warning(f"Error getting top selling products: {e}")
        return []

    def _get_top_customers(self, start_date, end_date):
        try:
            query = """
                SELECT
                    COALESCE(c.name, 'عميل نقدي') AS customer_name,
                    COUNT(*) AS invoice_count,
                    COALESCE(SUM(s.final_amount), 0) AS total_purchases
                FROM sales s
                LEFT JOIN customers c ON c.id = s.customer_id AND c.is_deleted = 0
                WHERE s.sale_date >= ? AND s.sale_date <= ?
                  AND s.status NOT IN ('cancelled', 'draft')
                  AND s.is_deleted = 0
                GROUP BY s.customer_id
                ORDER BY total_purchases DESC
                LIMIT 10
            """
            rows = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            return [
                {
                    "customer_name": row.get("customer_name", ""),
                    "total_purchases": Decimal(str(row.get("total_purchases", 0) or 0)),
                    "invoice_count": int(row.get("invoice_count", 0) or 0),
                }
                for row in rows
            ]
        except Exception as e:
            self.logger.warning(f"Error getting top customers: {e}")
        return []

    def _get_sales_by_day(self, start_date, end_date):
        try:
            query = """
                SELECT
                    DATE(s.sale_date) AS date,
                    COUNT(*) AS count,
                    COALESCE(SUM(s.final_amount), 0) AS total
                FROM sales s
                WHERE s.sale_date >= ? AND s.sale_date <= ?
                  AND s.status NOT IN ('cancelled', 'draft')
                  AND s.is_deleted = 0
                GROUP BY DATE(s.sale_date)
                ORDER BY date
            """
            rows = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            return [
                {
                    "date": str(row.get("date", "")),
                    "total": Decimal(str(row.get("total", 0) or 0)),
                    "count": int(row.get("count", 0) or 0),
                }
                for row in rows
            ]
        except Exception as e:
            self.logger.warning(f"Error getting sales by day: {e}")
        return []

    def _get_sales_by_payment_method(self, start_date, end_date):
        try:
            query = """
                SELECT
                    s.payment_method,
                    COUNT(*) AS count,
                    COALESCE(SUM(s.final_amount), 0) AS total
                FROM sales s
                WHERE s.sale_date >= ? AND s.sale_date <= ?
                  AND s.status NOT IN ('cancelled', 'draft')
                  AND s.is_deleted = 0
                GROUP BY s.payment_method
                ORDER BY total DESC
            """
            rows = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            return [
                {
                    "payment_method": row.get("payment_method", ""),
                    "count": int(row.get("count", 0) or 0),
                    "total": float(row.get("total", 0) or 0),
                }
                for row in rows
            ]
        except Exception as e:
            self.logger.warning(f"Error getting sales by payment method: {e}")
        return []

    # ===== Public period-based methods for dashboard/UI =====

    def get_sales_statistics(self, period='month'):
        """إحصائيات المبيعات الحقيقية"""
        try:
            if period == 'today':
                date_filter = "DATE(sale_date) = DATE('now')"
            elif period == 'week':
                date_filter = "sale_date >= DATE('now', '-7 days')"
            elif period == 'month':
                date_filter = "sale_date >= DATE('now', '-30 days')"
            elif period == 'year':
                date_filter = "sale_date >= DATE('now', '-365 days')"
            else:
                date_filter = "1=1"

            query = f"""
                SELECT
                    COUNT(*) as total_sales,
                    COALESCE(SUM(COALESCE(final_amount, total_amount)), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN COALESCE(final_amount, total_amount) ELSE 0 END), 0) as paid_amount,
                    COALESCE(SUM(CASE WHEN payment_status IN ('partial', 'unpaid') THEN COALESCE(final_amount, total_amount) - COALESCE(paid_amount, 0) ELSE 0 END), 0) as outstanding,
                    AVG(COALESCE(final_amount, total_amount)) as avg_sale
                FROM sales WHERE {date_filter}  # SQL_SAFE: date_filter is hardcoded based on period value
                  AND status NOT IN ('cancelled', 'draft')
                  AND COALESCE(is_deleted, 0) = 0
            """
            result = self.db_manager.fetch_one(query)
            if result:
                # H5 FIX + C3: fetch_one يعيد dict الآن
                return {
                    'total_sales': result.get('total_sales', 0),
                    'total_revenue': float(result.get('total_revenue', 0) or 0),
                    'paid_amount': float(result.get('paid_amount', 0) or 0),
                    'outstanding': float(result.get('outstanding', 0) or 0),
                    'avg_sale': float(result.get('avg_sale', 0) or 0),
                }
            return {'total_sales': 0, 'total_revenue': 0, 'paid_amount': 0, 'outstanding': 0, 'avg_sale': 0}
        except Exception as e:
            self.logger.warning(f"خطأ في إحصائيات المبيعات: {e}")
            return {'total_sales': 0, 'total_revenue': 0, 'paid_amount': 0, 'outstanding': 0, 'avg_sale': 0}

    def get_top_products(self, limit=10, period='month'):
        """أفضل المنتجات مبيعاً"""
        try:
            date_filter = "1=1"
            if period == 'today':
                date_filter = "DATE(s.sale_date) = DATE('now')"
            elif period == 'week':
                date_filter = "s.sale_date >= DATE('now', '-7 days')"
            elif period == 'month':
                date_filter = "s.sale_date >= DATE('now', '-30 days')"

            query = f"""
                SELECT p.id, p.name, p.barcode,
                       SUM(si.quantity) as total_qty,
                       SUM(si.total_price) as total_revenue
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                JOIN products p ON p.id = si.product_id
                WHERE {date_filter}  # SQL_SAFE: date_filter is hardcoded based on period value
                GROUP BY p.id, p.name, p.barcode
                ORDER BY total_qty DESC
                LIMIT ?
            """
            results = self.db_manager.fetch_all(query, (limit,))
            return [dict(r) for r in results]
        except Exception as e:
            self.logger.warning(f"خطأ في أفضل المنتجات: {e}")
            return []

    def get_top_customers(self, limit=10, period='month'):
        """أفضل العملاء"""
        try:
            date_filter = "1=1"
            if period == 'today':
                date_filter = "DATE(s.sale_date) = DATE('now')"
            elif period == 'week':
                date_filter = "s.sale_date >= DATE('now', '-7 days')"
            elif period == 'month':
                date_filter = "s.sale_date >= DATE('now', '-30 days')"
            elif period == 'year':
                date_filter = "s.sale_date >= DATE('now', '-365 days')"

            query = f"""
                SELECT c.id, c.name, c.phone,
                       COUNT(s.id) as order_count,
                       COALESCE(SUM(s.total_amount), 0) as total_spent
                FROM sales s
                JOIN customers c ON c.id = s.customer_id
                WHERE {date_filter}  # SQL_SAFE: date_filter is hardcoded based on period value
                GROUP BY c.id, c.name, c.phone
                ORDER BY total_spent DESC
                LIMIT ?
            """
            results = self.db_manager.fetch_all(query, (limit,))
            return [dict(r) for r in results]
        except Exception as e:
            self.logger.warning(f"خطأ في أفضل العملاء: {e}")
            return []

    def get_daily_sales(self, days=30):
        """المبيعات اليومية"""
        try:
            query = """
                SELECT DATE(sale_date) as date,
                       COUNT(*) as sales_count,
                       COALESCE(SUM(total_amount), 0) as daily_total
                FROM sales
                WHERE sale_date >= DATE('now', ? || ' days')
                GROUP BY DATE(sale_date)
                ORDER BY date
            """
            results = self.db_manager.fetch_all(query, (str(-days),))
            return [dict(r) for r in results]
        except Exception as e:
            self.logger.warning(f"خطأ في المبيعات اليومية: {e}")
            return []

    def get_daily_profit(self, days=30):
        """الربح اليومي — C2 FIX: تجنّب تضخيم الإيرادات بسبب JOIN متعدد الصفوف"""
        try:
            query = """
                SELECT d.date,
                       COALESCE(sr.revenue, 0) as revenue,
                       COALESCE(sc.cost, 0) as cost,
                       COALESCE(sr.revenue, 0) - COALESCE(sc.cost, 0) as profit
                FROM (
                    SELECT DISTINCT DATE(sale_date) as date
                    FROM sales
                    WHERE sale_date >= DATE('now', ? || ' days')
                      AND status NOT IN ('cancelled', 'draft')
                      AND is_deleted = 0
                ) d
                LEFT JOIN (
                    SELECT DATE(s.sale_date) as date,
                           SUM(s.total_amount) as revenue
                    FROM sales s
                    WHERE s.sale_date >= DATE('now', ? || ' days')
                      AND s.status NOT IN ('cancelled', 'draft')
                      AND s.is_deleted = 0
                    GROUP BY DATE(s.sale_date)
                ) sr ON sr.date = d.date
                LEFT JOIN (
                    SELECT DATE(s.sale_date) as date,
                           SUM(si.quantity * COALESCE(p.cost_price, p.selling_price * 0.7)) as cost
                    FROM sale_items si
                    JOIN sales s ON s.id = si.sale_id
                    JOIN products p ON p.id = si.product_id
                    WHERE s.sale_date >= DATE('now', ? || ' days')
                      AND s.status NOT IN ('cancelled', 'draft')
                      AND s.is_deleted = 0
                      AND si.is_deleted = 0
                    GROUP BY DATE(s.sale_date)
                ) sc ON sc.date = d.date
                ORDER BY d.date
            """
            results = self.db_manager.fetch_all(query, (str(-days), str(-days), str(-days)))
            return [dict(r) for r in results]
        except Exception as e:
            self.logger.warning(f"خطأ في الربح اليومي: {e}")
            return []

    class SalesReport:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    def generate_sales_report(self, start_date, end_date):
        """إنشاء تقرير المبيعات"""
        stats = self._get_sales_statistics(start_date, end_date) or {}
        top_products = self._get_top_selling_products(start_date, end_date)
        top_customers = self._get_top_customers(start_date, end_date)
        sales_by_day = self._get_sales_by_day(start_date, end_date)
        sales_by_pay = self._get_sales_by_payment_method(start_date, end_date)

        return self.SalesReport(
            total_sales=stats.get("total_sales", 0),
            total_revenue=stats.get("total_revenue", 0.0),
            total_profit=stats.get("total_profit", 0.0),
            average_sale_value=stats.get("average_sale_value", 0.0),
            top_selling_products=top_products,
            top_customers=top_customers,
            sales_by_day=sales_by_day,
            sales_by_payment_method=sales_by_pay
        )

    def _calculate_daily_profit(self, target_date):
        try:
            query = """
                SELECT COALESCE(SUM(si.profit), 0) AS daily_profit
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                WHERE DATE(s.sale_date) = ?
                  AND s.status NOT IN ('cancelled', 'draft')
                  AND s.is_deleted = 0
                  AND si.is_deleted = 0
            """
            row = self.db_manager.fetch_one(query, (target_date.isoformat(),))
            if row:
                return float(Decimal(str(row.get("daily_profit", 0) or 0)))
        except Exception as e:
            self.logger.warning(f"Error calculating daily profit: {e}")
        return 0.0

    def get_daily_summary(self, target_date=None):
        """الحصول على ملخص المبيعات اليومي المطور"""
        if target_date is None:
            target_date = date.today()

        query = """
            SELECT
                COUNT(*) as total_sales,
                COALESCE(SUM(final_amount), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN final_amount ELSE 0 END), 0) as cash_total,
                COALESCE(SUM(CASE WHEN payment_method = 'card' THEN final_amount ELSE 0 END), 0) as card_total,
                COALESCE(SUM(CASE WHEN payment_method = 'credit' THEN final_amount ELSE 0 END), 0) as credit_total,
                COALESCE(SUM(CASE WHEN status = 'returned' THEN final_amount ELSE 0 END), 0) as returns_total
            FROM sales
            WHERE sale_date = ?
              AND status != 'cancelled'
        """
        row = self.db_manager.fetch_one(query, (target_date.isoformat(),))

        total_sales = 0
        total_revenue = 0.0
        returns = 0.0

        if row:
            total_sales = row.get("total_sales", 0)
            total_revenue = float(row.get("total_revenue", 0.0) or 0)
            returns = float(row.get("returns_total", 0.0) or 0)

        net_sales = total_revenue - returns
        profit = self._calculate_daily_profit(target_date)

        class DailySummary:
            def __init__(self, total_sales, total_revenue, net_sales, total_profit):
                self.total_sales = total_sales
                self.total_revenue = total_revenue
                self.net_sales = net_sales
                self.total_profit = total_profit

        return DailySummary(total_sales, total_revenue, net_sales, profit)

    def add_sale_item(self, sale_id, product_id, quantity, discount=0.0):
        """إضافة عنصر مبيعات مع تطبيق منطق أسعار الجملة/التجزئة"""
        # EDGE CASE: quantity must be positive
        if not quantity or quantity <= 0:
            self.logger.warning(f"add_sale_item rejected: invalid quantity {quantity} for product {product_id}")
            return False

        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return False

        min_wholesale = getattr(product, "min_wholesale_qty", 0) or 0
        if min_wholesale > 0 and quantity >= min_wholesale:
            price = getattr(product, "wholesale_price", product.selling_price)
        else:
            price = product.selling_price

        item = SaleItem(
            product_id=product_id,
            quantity=quantity,
            unit_price=Decimal(str(price or 0)),
            discount=Decimal(str(discount or 0)),
            sale_id=sale_id,
            product_name=getattr(product, "name", "")
        )
        item.calculate_totals()
        return self.sale_manager.add_sale_item(item)

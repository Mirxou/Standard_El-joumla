#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المبيعات - Sale Model
يحتوي على جميع العمليات المتعلقة بالمبيعات والفواتير
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path


# استيراد to_decimal للتحويل الآمن
try:
    from src.utils.math_utils import to_decimal
except ImportError:
    # Fallback إذا لم يكن math_utils متوفراً
    def to_decimal(value):
        if value is None or value == "":
            return Decimal("0.00")
        try:
            if isinstance(value, Decimal):
                return value
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            if isinstance(value, str):
                cleaned = (
                    value.strip()
                    .replace("د.ج", "")
                    .replace("دج", "")
                    .replace(",", "")
                    .strip()
                )
                return Decimal(cleaned) if cleaned else Decimal("0.00")
            return Decimal(str(value))
        except (ValueError, TypeError, Exception):
            return Decimal("0.00")


class SaleStatus(Enum):
    """حالات الفاتورة"""

    DRAFT = "مسودة"
    CONFIRMED = "مؤكدة"
    PAID = "مدفوعة"
    PARTIALLY_PAID = "مدفوعة جزئياً"
    CANCELLED = "ملغية"
    RETURNED = "مرتجعة"


class PaymentMethod(Enum):
    """طرق الدفع"""

    CASH = "نقدي"
    CARD = "بطاقة"
    BANK_TRANSFER = "تحويل بنكي"
    CREDIT = "آجل"
    MIXED = "مختلط"


@dataclass
class SaleItem:
    """عنصر في فاتورة المبيعات"""

    id: Optional[int] = None
    sale_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    product_barcode: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    discount_percentage: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    tax_percentage: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")

    # Limits for safety
    MAX_QUANTITY = 9999
    MAX_UNIT_PRICE = Decimal("999999.99")
    MAX_DISCOUNT_PERCENTAGE = Decimal("100.00")
    MAX_TAX_PERCENTAGE = Decimal("100.00")

    def __post_init__(self):
        """تحويل القيم بعد الإنشاء مع تحققات الأمان"""
        # تحويل الكمية إلى قيمة صحيحة موجبة
        if not isinstance(self.quantity, int):
            try:
                self.quantity = int(self.quantity)
            except (ValueError, TypeError):
                self.quantity = 1

        # التحقق من حدود الكمية
        if self.quantity < 1:
            raise ValueError(f"الكمية يجب أن تكون موجبة، تم إدخال: {self.quantity}")
        if self.quantity > self.MAX_QUANTITY:
            raise ValueError(
                f"الكمية يجب أن تكون {self.MAX_QUANTITY} أو أقل، تم إدخال: {self.quantity}"
            )

        # تحويل الأسعار والخصومات
        for field in [
            "unit_price",
            "discount_amount",
            "discount_percentage",
            "tax_amount",
            "tax_percentage",
            "total_amount",
        ]:
            value = getattr(self, field)
            if isinstance(value, (int, float, str)):
                setattr(self, field, Decimal(str(value)))

        # التحقق من حدود السعر
        if self.unit_price < 0:
            raise ValueError("سعر الوحدة لا يمكن أن يكون سالباً")
        if self.unit_price > self.MAX_UNIT_PRICE:
            raise ValueError(f"سعر الوحدة يجب أن يكون {self.MAX_UNIT_PRICE} أو أقل")

        # التحقق من حدود النسب المئوية
        if (
            self.discount_percentage < 0
            or self.discount_percentage > self.MAX_DISCOUNT_PERCENTAGE
        ):
            raise ValueError(
                f"نسبة الخصم يجب أن تكون بين 0 و{self.MAX_DISCOUNT_PERCENTAGE}%"
            )

        if self.tax_percentage < 0 or self.tax_percentage > self.MAX_TAX_PERCENTAGE:
            raise ValueError(
                f"نسبة الضريبة يجب أن تكون بين 0 و{self.MAX_TAX_PERCENTAGE}%"
            )

    @property
    def subtotal(self) -> Decimal:
        """المجموع الفرعي قبل الخصم والضريبة"""
        return self.unit_price * self.quantity

    def calculate_total(self):
        """حساب المجموع"""
        subtotal = self.subtotal

        # خصم
        if self.discount_percentage > 0:
            self.discount_amount = subtotal * (self.discount_percentage / 100)

        after_discount = subtotal - self.discount_amount

        # ضريبة
        if self.tax_percentage > 0:
            self.tax_amount = after_discount * (self.tax_percentage / 100)

        self.total_amount = after_discount + self.tax_amount

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_barcode": self.product_barcode,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "discount_amount": float(self.discount_amount),
            "discount_percentage": float(self.discount_percentage),
            "tax_amount": float(self.tax_amount),
            "tax_percentage": float(self.tax_percentage),
            "total_amount": float(self.total_amount),
        }


@dataclass
class Sale:
    """نموذج بيانات المبيعات"""

    id: Optional[int] = None
    invoice_number: str = ""
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    sale_date: Optional[date] = None
    due_date: Optional[date] = None
    status: SaleStatus = SaleStatus.DRAFT
    payment_method: PaymentMethod = PaymentMethod.CASH
    subtotal: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    discount_percentage: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    tax_percentage: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    paid_amount: Decimal = Decimal("0.00")
    remaining_amount: Decimal = Decimal("0.00")
    # Multi-Currency Support
    currency_id: Optional[int] = None  # معرف العملة المستخدمة
    exchange_rate: Decimal = Decimal("1.0")  # سعر الصرف المستخدم
    base_amount: Optional[Decimal] = None  # المبلغ بالعملة الأساسية
    converted_amount: Optional[Decimal] = None  # المبلغ بالعملة المحددة
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[SaleItem] = None

    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        if self.items is None:
            self.items = []

        for field in [
            "subtotal",
            "discount_amount",
            "discount_percentage",
            "tax_amount",
            "tax_percentage",
            "total_amount",
            "paid_amount",
            "remaining_amount",
            "exchange_rate",
            "base_amount",
            "converted_amount",
        ]:
            value = getattr(self, field)
            if value is not None and isinstance(value, (int, float, str)):
                setattr(self, field, Decimal(str(value)))

        if isinstance(self.status, str):
            self.status = SaleStatus(self.status)
        if isinstance(self.payment_method, str):
            self.payment_method = PaymentMethod(self.payment_method)

    def add_item(self, item: SaleItem):
        """إضافة عنصر للفاتورة"""
        item.calculate_total()
        self.items.append(item)
        self.calculate_totals()

    def remove_item(self, item_id: int):
        """حذف عنصر من الفاتورة"""
        self.items = [item for item in self.items if item.id != item_id]
        if self.items:
            self.calculate_totals()
        else:
            # عند حذف آخر عنصر نعيد الفاتورة إلى حالة فارغة صريحة.
            self.subtotal = Decimal("0.00")
            self.discount_amount = Decimal("0.00")
            self.tax_amount = Decimal("0.00")
            self.total_amount = Decimal("0.00")
            self.remaining_amount = Decimal("0.00")
            self.base_amount = Decimal("0.00") if self.base_amount is not None else None
            self.converted_amount = (
                Decimal("0.00") if self.converted_amount is not None else None
            )
            self.status = (
                SaleStatus.DRAFT if self.paid_amount == 0 else SaleStatus.PARTIALLY_PAID
            )

    def calculate_totals(self):
        """حساب المجاميع"""
        if self.items:
            self.subtotal = sum(item.unit_price * item.quantity for item in self.items)

            # خصم إجمالي
            if self.discount_percentage > 0:
                self.discount_amount = self.subtotal * (self.discount_percentage / 100)

            after_discount = self.subtotal - self.discount_amount

            # ضريبة إجمالية
            if self.tax_percentage > 0:
                self.tax_amount = after_discount * (self.tax_percentage / 100)

            self.total_amount = after_discount + self.tax_amount
        elif self.total_amount > 0 and self.subtotal == 0:
            # يدعم الفواتير اليدوية التي لا تحتوي على عناصر تفصيلية.
            self.subtotal = self.total_amount

        self.remaining_amount = self.total_amount - self.paid_amount

        # Multi-Currency: حساب المبالغ بالعملة المحددة والأساسية
        if self.currency_id:
            # المبلغ بالعملة المحددة
            self.converted_amount = self.total_amount
            # المبلغ بالعملة الأساسية (سيتم حسابه من ExchangeRateService)
            # سيتم تعيينه من Service Layer
        else:
            # إذا لم تكن هناك عملة محددة، استخدم المبلغ الأساسي
            self.base_amount = self.total_amount
            self.converted_amount = self.total_amount

        # تحديث حالة الدفع
        if self.paid_amount >= self.total_amount:
            self.status = SaleStatus.PAID
        elif self.paid_amount > 0:
            self.status = SaleStatus.PARTIALLY_PAID

    @property
    def is_paid(self) -> bool:
        """هل الفاتورة مدفوعة بالكامل؟"""
        return self.paid_amount >= self.total_amount

    @property
    def items_count(self) -> int:
        """عدد الأصناف"""
        return len(self.items)

    @property
    def total_quantity(self) -> int:
        """إجمالي الكمية"""
        return sum(item.quantity for item in self.items)

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "sale_date": self.sale_date.isoformat() if self.sale_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value
            if isinstance(self.status, SaleStatus)
            else self.status,
            "payment_method": self.payment_method.value
            if isinstance(self.payment_method, PaymentMethod)
            else self.payment_method,
            "subtotal": float(self.subtotal),
            "discount_amount": float(self.discount_amount),
            "discount_percentage": float(self.discount_percentage),
            "tax_amount": float(self.tax_amount),
            "tax_percentage": float(self.tax_percentage),
            "total_amount": float(self.total_amount),
            "paid_amount": float(self.paid_amount),
            "remaining_amount": float(self.remaining_amount),
            # Multi-Currency Support
            "currency_id": self.currency_id,
            "exchange_rate": float(self.exchange_rate) if self.exchange_rate else 1.0,
            "base_amount": float(self.base_amount) if self.base_amount else None,
            "converted_amount": float(self.converted_amount)
            if self.converted_amount
            else None,
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict() for item in self.items],
            "is_paid": self.is_paid,
            "items_count": self.items_count,
            "total_quantity": self.total_quantity,
        }


class SaleManager:
    """مدير المبيعات"""

    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        # Multi-Company Support
        self._tenant_manager = None

    @property
    def tenant_manager(self):
        """Lazy loading لـ TenantIsolationManager"""
        if self._tenant_manager is None:
            try:
                from src.core.tenant_isolation import TenantIsolationManager

                self._tenant_manager = TenantIsolationManager(self.db_manager)
            except ImportError:
                if self.logger:
                    self.logger.warning(
                        "TenantIsolationManager غير متاح - Multi-Company غير مفعل"
                    )
        return self._tenant_manager

    def _get_company_id(self) -> Optional[int]:
        """الحصول على معرف الشركة الحالية"""
        if self.tenant_manager:
            return self.tenant_manager.get_current_company_id()
        return None

    def _add_company_filter(
        self, query: str, params: list, company_id: Optional[int] = None
    ) -> tuple:
        """إضافة فلتر الشركة إلى الاستعلام"""
        if company_id is None:
            company_id = self._get_company_id()

        if company_id is not None:
            if "WHERE" in query.upper():
                query += " AND company_id = ?"
            else:
                query += " WHERE company_id = ?"
            params.append(company_id)

        return query, params

    def create_sale(self, sale: Sale, update_stock: bool = True) -> Optional[int]:
        """إنشاء فاتورة مبيعات جديدة مع توافق ديناميكي مع أعمدة جدول sales.

        يبني عبارة INSERT اعتماداً على الأعمدة الموجودة فعلياً في الجدول
        باستخدام PRAGMA table_info(sales) لتجنب فشل الإدراج في البيئات الاختبارية
        التي تحتوي على مخطط مبسط.
        """
        # 🔒 التحقق: إذا كان هناك مبلغ متبقي، لا يمكن حفظ الفاتورة بحالة "مدفوعة"
        if sale.status == SaleStatus.PAID and sale.remaining_amount > 0:
            if self.logger:
                self.logger.warning(
                    f"محاولة إنشاء فاتورة بحالة 'مدفوعة' مع وجود مبلغ متبقي "
                    f"({sale.remaining_amount}). سيتم رفض العملية."
                )
            raise ValueError(
                f"لا يمكن حفظ الفاتورة بحالة 'مدفوعة' إذا كان هناك مبلغ متبقي "
                f"({sale.remaining_amount}). يرجى تغيير الحالة إلى 'مدفوعة جزئياً' أو 'مؤكدة'."
            )

        # ضمان رقم فاتورة فريد إذا أعاد المستدعي استخدام رقم موجود.
        if not sale.invoice_number or self.get_sale_by_invoice_number(
            sale.invoice_number
        ):
            sale.invoice_number = self.generate_invoice_number()

        # إعادة حساب المجاميع إذا تم تعديل نسب الخصم/الضريبة بعد إضافة العناصر.
        if sale.items:
            sale.calculate_totals()

        try:
            # إنشاء الفاتورة الرئيسية - متوافق مع بنية الجدول الفعلية
            # الجدول يحتوي على: invoice_number, customer_id, total_amount, discount_amount,
            # final_amount, payment_method, sale_date, user_id, notes, status, paid_amount, remaining_amount,
            # currency_id, exchange_rate, base_amount, converted_amount (Multi-Currency),
            # is_active, created_at, updated_at
            # اكتشاف الأعمدة المتاحة في جدول sales
            conn = self.db_manager.connection
            cur_cols = conn.execute("PRAGMA table_info(sales)").fetchall()
            available_cols = {row[1] for row in cur_cols}

            # قيم محضّرة وفق نموذج Sale
            now = datetime.now()
            final_amount = sale.total_amount
            base_amount = (
                sale.base_amount if sale.base_amount is not None else sale.total_amount
            )
            converted_amount = (
                sale.converted_amount
                if sale.converted_amount is not None
                else sale.total_amount
            )
            exchange_rate = float(sale.exchange_rate) if sale.exchange_rate else 1.0

            if isinstance(sale.payment_method, PaymentMethod):
                payment_method_text = sale.payment_method.value
            elif isinstance(sale.payment_method, str):
                payment_method_text = sale.payment_method
            else:
                payment_method_text = "نقدي"

            # تحويل الحالة لقيمة متوافقة مع قيود الجدول إن وجدت
            if isinstance(sale.status, SaleStatus):
                status_to_db_mapping = {
                    SaleStatus.DRAFT: "draft",
                    SaleStatus.CONFIRMED: "confirmed",
                    SaleStatus.PAID: "paid",
                    SaleStatus.PARTIALLY_PAID: "pending",
                    SaleStatus.CANCELLED: "cancelled",
                    SaleStatus.RETURNED: "cancelled",
                }
                status_text = status_to_db_mapping.get(sale.status, "draft")
            else:
                try:
                    status_text = str(sale.status).lower()
                except Exception:
                    status_text = "draft"

            # خريطة كل القيم المحتملة
            value_map = {
                "invoice_number": sale.invoice_number,
                "customer_id": sale.customer_id,
                "total_amount": float(sale.total_amount),
                "discount_amount": float(sale.discount_amount),
                "final_amount": float(final_amount),
                "payment_method": payment_method_text,
                "sale_date": sale.sale_date or date.today(),
                "user_id": sale.created_by,
                "notes": sale.notes,
                "status": status_text,
                "paid_amount": float(sale.paid_amount),
                "remaining_amount": float(sale.remaining_amount),
                "currency_id": sale.currency_id,
                "exchange_rate": exchange_rate,
                "base_amount": float(base_amount) if base_amount else None,
                "converted_amount": float(converted_amount)
                if converted_amount
                else None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }

            # الأعمدة الفعلية التي سنُدرِجها
            insert_cols = [col for col in value_map.keys() if col in available_cols]
            insert_vals = [value_map[col] for col in insert_cols]

            # بناء عبارة الإدراج ديناميكياً
            placeholders = ", ".join(["?" for _ in insert_cols])
            query = (
                f"INSERT INTO sales ({', '.join(insert_cols)}) VALUES ({placeholders})"
            )

            # القيم النهائية للإدراج
            params = tuple(insert_vals)

            if self.logger:
                self.logger.debug(
                    f"محاولة إنشاء فاتورة: {sale.invoice_number}, customer_id={sale.customer_id}, total={sale.total_amount}"
                )

            # استخدام execute_insert إن كان يوفر معرفاً صالحاً، وإلا نعود لمسار cursor التقليدي
            sale_id = None
            try:
                sale_id = self.db_manager.execute_insert(query, params)
            except Exception:
                sale_id = None

            if not isinstance(sale_id, int) or sale_id <= 0:
                try:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    try:
                        conn.commit()
                    except Exception:
                        pass

                    sale_id = getattr(cursor, "lastrowid", None)
                    if not isinstance(sale_id, int) or sale_id <= 0:
                        try:
                            cursor.execute("SELECT last_insert_rowid()")
                            row = cursor.fetchone()
                            if row and row[0]:
                                sale_id = row[0]
                        except Exception:
                            pass

                    if (
                        not isinstance(sale_id, int) or sale_id <= 0
                    ) and sale.invoice_number:
                        try:
                            cursor.execute(
                                "SELECT id FROM sales WHERE invoice_number = ?",
                                (sale.invoice_number,),
                            )
                            row = cursor.fetchone()
                            if row and row[0]:
                                sale_id = row[0]
                        except Exception:
                            pass

                    if not isinstance(sale_id, int) or sale_id <= 0:
                        sale_id = getattr(conn, "lastrowid", None)
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    if self.logger:
                        self.logger.error(f"فشل إدراج فاتورة المبيعات: {e}")
                    return None

            if not isinstance(sale_id, int) or sale_id <= 0:
                if self.logger:
                    self.logger.error("فشل الحصول على sale_id من عملية الإدراج")
                return None

            if self.logger:
                self.logger.debug(f"✅ تم إنشاء الفاتورة الرئيسية: ID={sale_id}")

            # إضافة عناصر الفاتورة
            for item in sale.items:
                item.sale_id = sale_id
                item_result = self._create_sale_item(item)
                if self.logger:
                    if item_result:
                        self.logger.debug(
                            f"✅ تم إنشاء عنصر الفاتورة: item_id={item_result}, product_id={item.product_id}, quantity={item.quantity}"
                        )
                    else:
                        self.logger.warning(
                            f"⚠️ فشل إضافة عنصر الفاتورة: product_id={item.product_id}"
                        )

            # تحديث المخزون
            if update_stock and sale.items:
                try:
                    self._update_stock_for_sale(sale.items, operation="sale")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"خطأ في تحديث المخزون: {e}")

            # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
            try:
                from src.core.signals import signals  # pyright: ignore[reportMissingImports]

                signals.sales_updated.emit()
                signals.sale_created.emit(sale_id)
                signals.inventory_updated.emit()
                if self.logger:
                    self.logger.debug(
                        f"✅ تم إطلاق إشارات: sales_updated, sale_created, inventory_updated"
                    )
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")

            # 🔔 إطلاق Webhook: إرسال Webhook عند إنشاء فاتورة مبيعات
            try:
                from src.services.webhook_service import WebhookService

                webhook_service = WebhookService(self.db_manager, self.logger)

                # بناء Payload للـ Webhook
                webhook_payload = {
                    "event": "sale_created",
                    "sale_id": sale_id,
                    "invoice_number": sale.invoice_number,
                    "customer_id": sale.customer_id,
                    "total_amount": float(sale.total_amount)
                    if sale.total_amount
                    else 0.0,
                    "created_at": datetime.now().isoformat(),
                    "sale": sale.to_dict() if hasattr(sale, "to_dict") else {},
                }

                webhook_service.trigger_webhook(
                    event_type="sale_created",
                    payload=webhook_payload,
                    entity_id=sale_id,
                    company_id=sale.company_id if hasattr(sale, "company_id") else None,
                )

                if self.logger:
                    self.logger.debug(
                        f"✅ تم إطلاق Webhook: sale_created (Sale ID: {sale_id})"
                    )
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ فشل إطلاق Webhook: {e}")

            if self.logger:
                self.logger.info(
                    f"✅ تم إنشاء فاتورة مبيعات جديدة: {sale.invoice_number} (ID: {sale_id})"
                )
            return sale_id

        except Exception as e:
            try:
                if (
                    hasattr(self.db_manager, "connection")
                    and self.db_manager.connection
                ):
                    self.db_manager.connection.rollback()
            except Exception:
                pass
            if self.logger:
                self.logger.error(
                    f"خطأ في إنشاء فاتورة المبيعات: {str(e)}", exc_info=True
                )
            import traceback

            if self.logger:
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"DEBUG EXCEPTION: {e}")
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            return None

    def _create_sale_item(self, item: SaleItem) -> Optional[int]:
        """إنشاء عنصر فاتورة (للاستخدام المستقل)"""
        try:
            # استخدام execute_query العادي
            # Fetch product cost_price
            prod = self.db_manager.fetch_one(
                "SELECT cost_price FROM products WHERE id = ?", (item.product_id,)
            )
            cost_price = float(prod[0]) if prod and prod[0] is not None else 0.0

            # Find or create a batch for this product
            batch = self.db_manager.fetch_one(
                "SELECT id FROM batches WHERE product_id = ? LIMIT 1",
                (item.product_id,),
            )
            if batch and batch[0]:
                batch_id = batch[0]
            else:
                # create placeholder batch
                batch_number = (
                    f"auto-{item.product_id}-{int(datetime.now().timestamp())}"
                )
                bq = """
                INSERT INTO batches (product_id, batch_number, quantity, cost_price, selling_price, purchase_date)
                VALUES (?, ?, ?, ?, ?, DATE('now'))
                """
                bparams = (
                    item.product_id,
                    batch_number,
                    0,
                    cost_price,
                    float(item.unit_price),
                )
                batch_id = self.db_manager.execute_insert(bq, bparams)
                if not batch_id:
                    # إذا فشل إنشاء batch، نستخدم batch_id = 1 كقيمة افتراضية
                    # أو نرفض العملية
                    if self.logger:
                        self.logger.error(f"فشل إنشاء batch للمنتج {item.product_id}")
                    return None

            total_price = float(item.unit_price) * int(item.quantity)
            profit = total_price - (cost_price * int(item.quantity))

            query = """
            INSERT INTO sale_items (
                sale_id, product_id, batch_id, quantity, unit_price, total_price, cost_price, profit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                item.sale_id,
                item.product_id,
                batch_id,
                item.quantity,
                float(item.unit_price),
                total_price,
                cost_price,
                profit,
            )

            # استخدام execute_insert للحصول على lastrowid بشكل صحيح
            item_id = self.db_manager.execute_insert(query, params)
            return item_id

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء عنصر الفاتورة: {str(e)}")
            return None

    def _create_sale_item_in_transaction(self, cursor, item: SaleItem) -> Optional[int]:
        """إنشاء عنصر فاتورة داخل معاملة (transaction) - يستخدم نفس cursor"""
        try:
            # Fetch product cost_price باستخدام نفس cursor
            cursor.execute(
                "SELECT cost_price FROM products WHERE id = ?", (item.product_id,)
            )
            prod = cursor.fetchone()
            cost_price = float(prod[0]) if prod and prod[0] is not None else 0.0

            # Find or create a batch for this product
            cursor.execute(
                "SELECT id FROM batches WHERE product_id = ? LIMIT 1",
                (item.product_id,),
            )
            batch = cursor.fetchone()
            if batch and batch[0]:
                batch_id = batch[0]
            else:
                # create placeholder batch
                batch_number = (
                    f"auto-{item.product_id}-{int(datetime.now().timestamp())}"
                )
                bq = """
                INSERT INTO batches (product_id, batch_number, quantity, cost_price, selling_price, purchase_date)
                VALUES (?, ?, ?, ?, ?, DATE('now'))
                """
                bparams = (
                    item.product_id,
                    batch_number,
                    0,
                    cost_price,
                    float(item.unit_price),
                )
                cursor.execute(bq, bparams)
                batch_id = cursor.lastrowid

            total_price = float(item.unit_price) * int(item.quantity)
            profit = total_price - (cost_price * int(item.quantity))

            query = """
            INSERT INTO sale_items (
                sale_id, product_id, batch_id, quantity, unit_price, total_price, cost_price, profit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                item.sale_id,
                item.product_id,
                batch_id,
                item.quantity,
                float(item.unit_price),
                total_price,
                cost_price,
                profit,
            )

            cursor.execute(query, params)
            return cursor.lastrowid

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء عنصر الفاتورة داخل المعاملة: {str(e)}")
            raise

    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """الحصول على فاتورة بالمعرف"""
        try:
            # محاولة الاستعلام الكامل أولاً (مع الأعمدة الجديدة)
            try:
                query = """
                SELECT 
                    id, invoice_number, customer_id, total_amount, discount_amount,
                    final_amount, payment_method, sale_date, user_id, notes,
                    COALESCE(status, 'مسودة') as status, 
                    COALESCE(paid_amount, 0) as paid_amount, 
                    COALESCE(remaining_amount, final_amount) as remaining_amount,
                    currency_id, exchange_rate, base_amount, converted_amount,
                    is_active, created_at, updated_at
                FROM sales WHERE id = ?
                """
                result = self.db_manager.fetch_one(query, (sale_id,))
            except Exception:
                # إذا فشل، استخدم استعلام أساسي بدون الأعمدة الجديدة
                if self.logger:
                    self.logger.warning(
                        f"استخدام استعلام أساسي للفاتورة {sale_id} (الأعمدة الجديدة غير متوفرة)"
                    )
                query = """
                SELECT 
                    id, invoice_number, customer_id, total_amount, discount_amount,
                    final_amount, payment_method, sale_date, user_id, notes,
                    'مسودة' as status,
                    0 as paid_amount,
                    final_amount as remaining_amount,
                    is_active, created_at, updated_at
                FROM sales WHERE id = ?
                """
                result = self.db_manager.fetch_one(query, (sale_id,))

            if not result:
                return None

            sale = self._row_to_sale(result)

            # الحصول على عناصر الفاتورة مع معلومات المنتج
            items_query = """
            SELECT 
                si.id, si.sale_id, si.product_id, 
                COALESCE(p.name, '') as product_name,
                COALESCE(p.barcode, '') as product_barcode,
                si.quantity, si.unit_price,
                0 as discount_amount,
                0 as discount_percentage,
                0 as tax_amount,
                0 as tax_percentage,
                COALESCE(si.total_price, si.unit_price * si.quantity) as total_amount
            FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ? 
            ORDER BY si.id
            """

            items_results = self.db_manager.fetch_all(items_query, (sale_id,))
            sale.items = [self._row_to_sale_item(row) for row in items_results]

            # إعادة اشتقاق المجاميع من العناصر لضمان توافقها مع البيانات المخزنة
            if sale.items:
                calculated_subtotal = sum(
                    item.unit_price * item.quantity for item in sale.items
                )
                sale.subtotal = calculated_subtotal

                if sale.discount_amount and calculated_subtotal > 0:
                    sale.discount_percentage = (
                        sale.discount_amount / calculated_subtotal
                    ) * 100

                after_discount = calculated_subtotal - sale.discount_amount
                sale.tax_amount = (
                    sale.total_amount - after_discount
                    if sale.total_amount
                    else Decimal("0")
                )
                if after_discount > 0 and sale.tax_amount:
                    sale.tax_percentage = (sale.tax_amount / after_discount) * 100

                sale.remaining_amount = sale.total_amount - sale.paid_amount

            return sale

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"خطأ في الحصول على فاتورة المبيعات {sale_id}: {str(e)}"
                )
                import traceback

                self.logger.error(f"تفاصيل الخطأ: {traceback.format_exc()}")

        return None

    def get_sale_by_invoice_number(self, invoice_number: str) -> Optional[Sale]:
        """الحصول على فاتورة برقم الفاتورة"""
        try:
            query = "SELECT * FROM sales WHERE invoice_number = ?"
            result = self.db_manager.fetch_one(query, (invoice_number,))

            if result:
                sale = self._row_to_sale(result)
                # الحصول على العناصر
                items_query = "SELECT * FROM sale_items WHERE sale_id = ? ORDER BY id"
                items_results = self.db_manager.fetch_all(items_query, (sale.id,))
                sale.items = [self._row_to_sale_item(row) for row in items_results]
                return sale

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث بالفاتورة {invoice_number}: {str(e)}")

        return None

    def search_sales(
        self,
        search_term: str = "",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[SaleStatus] = None,
        customer_id: Optional[int] = None,
    ) -> List[Sale]:
        """البحث في المبيعات"""
        try:
            query = "SELECT * FROM sales WHERE 1=1"
            params = []

            if search_term:
                query += " AND (invoice_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            if start_date:
                query += " AND sale_date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND sale_date <= ?"
                params.append(end_date)

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)

            query += " ORDER BY sale_date DESC, id DESC"

            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_sale(row) for row in results]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في المبيعات: {str(e)}")
            return []

    def list_sales(
        self,
        search_term: str = "",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[SaleStatus] = None,
        payment_method: Optional[PaymentMethod] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """إرجاع قائمة مختصرة من الفواتير للاستخدام في الواجهة"""
        try:
            query = """
            SELECT
                id, invoice_number,
                COALESCE(customer_name, '') as customer_name,
                COALESCE(customer_phone, '') as customer_phone,
                sale_date,
                status,
                payment_method,
                total_amount,
                paid_amount,
                remaining_amount
            FROM sales
            WHERE 1=1
            """
            params: List[Any] = []

            if search_term:
                query += " AND (invoice_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            if start_date:
                query += " AND sale_date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND sale_date <= ?"
                params.append(end_date)

            if status:
                query += " AND status = ?"
                params.append(
                    status.value if isinstance(status, SaleStatus) else status
                )

            if payment_method:
                query += " AND payment_method = ?"
                params.append(
                    payment_method.value
                    if isinstance(payment_method, PaymentMethod)
                    else payment_method
                )

            query += " ORDER BY sale_date DESC, id DESC"
            if limit > 0:
                query += " LIMIT ?"
                params.append(limit)

            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_sale_dict(row) for row in results]

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في جلب قائمة المبيعات: {str(e)}")
            return []

    def get_sales_summary(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, float]:
        """ملخص رقمي للمبيعات (عدد الفواتير، الإجمالي، المدفوع، المتبقي)"""
        if not start_date and not end_date:
            # افتراض آخر 30 يوماً
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        elif start_date and not end_date:
            end_date = start_date
        elif end_date and not start_date:
            start_date = end_date

        try:
            query = """
            SELECT
                COUNT(*) as total_invoices,
                COALESCE(SUM(final_amount), 0) as total_revenue,
                COALESCE(SUM(paid_amount), 0) as total_paid,
                COALESCE(SUM(remaining_amount), 0) as total_remaining
            FROM sales
            WHERE sale_date BETWEEN ? AND ? 
            AND (status IS NULL OR status NOT IN ('cancelled', 'ملغية'))
            """
            result = self.db_manager.fetch_one(query, (start_date, end_date))

            total_invoices = int(result[0] or 0) if result else 0
            total_revenue = float(result[1] or 0) if result else 0.0
            total_paid = float(result[2] or 0) if result else 0.0
            total_remaining = float(result[3] or 0) if result else 0.0
            avg_invoice_value = (
                total_revenue / total_invoices if total_invoices > 0 else 0.0
            )

            return {
                "total_invoices": total_invoices,
                "total_revenue": total_revenue,  # استخدام final_amount
                "total_amount": total_revenue,  # للتوافق مع الكود القديم
                "total_paid": total_paid,
                "total_remaining": total_remaining,
                "avg_invoice_value": avg_invoice_value,
                "period_start": start_date.isoformat() if start_date else None,
                "period_end": end_date.isoformat() if end_date else None,
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب ملخص المبيعات: {str(e)}")
            return {
                "total_invoices": 0,
                "total_amount": 0.0,
                "total_paid": 0.0,
                "total_remaining": 0.0,
                "period_start": start_date.isoformat() if start_date else None,
                "period_end": end_date.isoformat() if end_date else None,
            }

    def get_recent_sales(self, limit: int = 5) -> List[Dict[str, Any]]:
        """الحصول على آخر الفواتير"""
        return self.list_sales(limit=limit)

    def get_daily_sales(self, target_date: Optional[date] = None) -> List[Sale]:
        """الحصول على مبيعات يوم معين"""
        if not target_date:
            target_date = date.today()

        return self.search_sales(start_date=target_date, end_date=target_date)

    def update_sale(self, sale: Sale) -> bool:
        """تحديث فاتورة موجودة"""
        if not sale.id:
            if self.logger:
                self.logger.error("لا يمكن تحديث فاتورة بدون ID")
            return False

        # 🔒 التحقق: إذا كان هناك مبلغ متبقي، لا يمكن حفظ الفاتورة بحالة "مدفوعة"
        if sale.status == SaleStatus.PAID and sale.remaining_amount > 0:
            if self.logger:
                self.logger.warning(
                    f"محاولة حفظ فاتورة {sale.id} بحالة 'مدفوعة' مع وجود مبلغ متبقي "
                    f"({sale.remaining_amount}). سيتم رفض العملية."
                )
            raise ValueError(
                f"لا يمكن حفظ الفاتورة بحالة 'مدفوعة' إذا كان هناك مبلغ متبقي "
                f"({sale.remaining_amount}). يرجى تغيير الحالة إلى 'مدفوعة جزئياً' أو 'مؤكدة'."
            )

        try:
            # تحديث بيانات الفاتورة الرئيسية
            query = """
            UPDATE sales SET
                customer_id = ?, total_amount = ?, discount_amount = ?,
                final_amount = ?, payment_method = ?, sale_date = ?,
                user_id = ?, notes = ?, status = ?, paid_amount = ?,
                remaining_amount = ?, currency_id = ?, exchange_rate = ?,
                base_amount = ?, converted_amount = ?, updated_at = ?
            WHERE id = ?
            """

            # تحويل payment_method إلى نص
            if isinstance(sale.payment_method, PaymentMethod):
                payment_method_text = sale.payment_method.value
            elif isinstance(sale.payment_method, str):
                payment_method_text = sale.payment_method
            else:
                payment_method_text = "نقدي"

            # تحويل status إلى نص إنجليزي (لتوافق مع CHECK constraint)
            # ملاحظة: constraint يتوقع: 'draft', 'pending', 'confirmed', 'invoiced', 'paid', 'cancelled'
            if isinstance(sale.status, SaleStatus):
                # تحويل القيمة العربية إلى إنجليزية - استخدام mapping مباشر
                # تحويل PARTIALLY_PAID إلى 'pending' لأن constraint لا يدعم 'partially_paid'
                status_to_db_mapping = {
                    SaleStatus.DRAFT: "draft",
                    SaleStatus.CONFIRMED: "confirmed",
                    SaleStatus.PAID: "paid",
                    SaleStatus.PARTIALLY_PAID: "pending",  # تحويل إلى 'pending' لأن constraint لا يدعم 'partially_paid'
                    SaleStatus.CANCELLED: "cancelled",
                    SaleStatus.RETURNED: "cancelled",  # تحويل 'returned' إلى 'cancelled'
                }
                # استخدام enum مباشرة كمفتاح
                status_text = status_to_db_mapping.get(sale.status, "confirmed")
            elif isinstance(sale.status, str):
                # إذا كان نصاً، تحويله إلى إنجليزية
                # ملاحظة: constraint يتوقع: 'draft', 'pending', 'confirmed', 'invoiced', 'paid', 'cancelled'
                status_mapping = {
                    "مسودة": "draft",
                    "مؤكدة": "confirmed",
                    "مدفوعة": "paid",
                    "مدفوعة جزئياً": "pending",  # تحويل إلى 'pending' لأن constraint لا يدعم 'partially_paid'
                    "ملغية": "cancelled",
                    "مرتجعة": "cancelled",  # تحويل 'returned' إلى 'cancelled'
                    "draft": "draft",
                    "pending": "pending",
                    "confirmed": "confirmed",
                    "invoiced": "invoiced",
                    "paid": "paid",
                    "partially_paid": "pending",  # تحويل إلى 'pending'
                    "cancelled": "cancelled",
                    "returned": "cancelled",  # تحويل إلى 'cancelled'
                }
                status_text = status_mapping.get(sale.status.lower(), "confirmed")
            else:
                status_text = "confirmed"  # افتراضي للفاتورة المحدثة

            # Multi-Currency: حساب المبالغ
            base_amount = (
                sale.base_amount if sale.base_amount is not None else sale.total_amount
            )
            converted_amount = (
                sale.converted_amount
                if sale.converted_amount is not None
                else sale.total_amount
            )
            exchange_rate = float(sale.exchange_rate) if sale.exchange_rate else 1.0

            params = (
                sale.customer_id,
                float(sale.total_amount),
                float(sale.discount_amount),
                float(sale.total_amount),  # final_amount
                payment_method_text,
                sale.sale_date or date.today(),
                sale.created_by,
                sale.notes,
                status_text,  # status
                float(sale.paid_amount),  # paid_amount
                float(sale.remaining_amount),  # remaining_amount
                # Multi-Currency Support
                sale.currency_id,
                exchange_rate,
                float(base_amount) if base_amount else None,
                float(converted_amount) if converted_amount else None,
                datetime.now(),
                sale.id,
            )

            # جلب العناصر القديمة لتحديث المخزون
            old_sale = self.get_sale_by_id(sale.id)
            old_items = old_sale.items if old_sale else []

            # استخدام transaction واحدة لجميع العمليات لتجنب database locked
            # استخدام get_cursor context manager إذا كان متاحاً
            if hasattr(self.db_manager, "get_cursor"):
                with self.db_manager.get_cursor() as cursor:
                    try:
                        # تحديث الفاتورة الرئيسية
                        cursor.execute(query, params)

                        # 🔥 تحديث المخزون: إرجاع الكميات القديمة أولاً
                        if old_items:
                            self._update_stock_in_transaction(
                                cursor, old_items, operation="return"
                            )

                        # حذف العناصر القديمة
                        delete_query = "DELETE FROM sale_items WHERE sale_id = ?"
                        cursor.execute(delete_query, (sale.id,))

                        # إضافة العناصر الجديدة في نفس المعاملة
                        for item in sale.items:
                            item.sale_id = sale.id
                            self._create_sale_item_in_transaction(cursor, item)

                        # 🔥 تحديث المخزون: خصم الكميات الجديدة
                        if sale.items:
                            self._update_stock_in_transaction(
                                cursor, sale.items, operation="sale"
                            )

                        # commit واحد لجميع العمليات
                        cursor.connection.commit()
                    except Exception as e:
                        cursor.connection.rollback()
                        raise
            else:
                # Fallback: استخدام الاتصال المباشر
                conn = self.db_manager.connection
                cursor = conn.cursor()

                try:
                    cursor.execute(query, params)

                    # 🔥 تحديث المخزون: إرجاع الكميات القديمة أولاً
                    if old_items:
                        self._update_stock_in_transaction(
                            cursor, old_items, operation="return"
                        )

                    # حذف العناصر القديمة
                    delete_query = "DELETE FROM sale_items WHERE sale_id = ?"
                    cursor.execute(delete_query, (sale.id,))

                    # إضافة العناصر الجديدة في نفس المعاملة
                    for item in sale.items:
                        item.sale_id = sale.id
                        self._create_sale_item_in_transaction(cursor, item)

                    # 🔥 تحديث المخزون: خصم الكميات الجديدة
                    if sale.items:
                        self._update_stock_in_transaction(
                            cursor, sale.items, operation="sale"
                        )

                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise
                finally:
                    cursor.close()

            # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
            try:
                from src.core.signals import signals  # pyright: ignore[reportMissingImports]

                signals.sales_updated.emit()
                signals.sale_updated.emit(sale.id)
                signals.inventory_updated.emit()  # المخزون قد يتغير عند تعديل الكميات
                if self.logger:
                    self.logger.debug(
                        f"✅ تم إطلاق إشارات: sales_updated, sale_updated({sale.id}), inventory_updated"
                    )
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")

            # 🔔 إطلاق Webhook: إرسال Webhook عند تحديث فاتورة مبيعات
            try:
                from src.services.webhook_service import WebhookService

                webhook_service = WebhookService(self.db_manager, self.logger)

                # بناء Payload للـ Webhook
                webhook_payload = {
                    "event": "sale_updated",
                    "sale_id": sale.id,
                    "invoice_number": sale.invoice_number,
                    "customer_id": sale.customer_id,
                    "total_amount": float(sale.total_amount)
                    if sale.total_amount
                    else 0.0,
                    "status": sale.status.value
                    if hasattr(sale.status, "value")
                    else str(sale.status),
                    "updated_at": datetime.now().isoformat(),
                    "sale": sale.to_dict() if hasattr(sale, "to_dict") else {},
                }

                webhook_service.trigger_webhook(
                    event_type="sale_updated",
                    payload=webhook_payload,
                    entity_id=sale.id,
                    company_id=sale.company_id if hasattr(sale, "company_id") else None,
                )

                if self.logger:
                    self.logger.debug(
                        f"✅ تم إطلاق Webhook: sale_updated (Sale ID: {sale.id})"
                    )
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ فشل إطلاق Webhook: {e}")

            if self.logger:
                self.logger.info(
                    f"✅ تم تحديث الفاتورة: ID={sale.id}, invoice_number={sale.invoice_number}"
                )
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"خطأ في تحديث الفاتورة {sale.id}: {str(e)}", exc_info=True
                )
            return False

    def update_sale_status(self, sale_id: int, new_status: SaleStatus) -> bool:
        """تحديث حالة الفاتورة"""
        try:
            # تحويل الحالة إلى قيمة متوافقة مع constraint
            status_to_db_mapping = {
                SaleStatus.DRAFT: "draft",
                SaleStatus.CONFIRMED: "confirmed",
                SaleStatus.PAID: "paid",
                SaleStatus.PARTIALLY_PAID: "pending",  # constraint لا يدعم 'partially_paid'
                SaleStatus.CANCELLED: "cancelled",
                SaleStatus.RETURNED: "cancelled",  # constraint لا يدعم 'returned'
            }
            db_status = status_to_db_mapping.get(new_status, "confirmed")

            query = "UPDATE sales SET status = ?, updated_at = ? WHERE id = ?"
            params = (db_status, datetime.now(), sale_id)

            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(
                        f"تم تحديث حالة الفاتورة {sale_id} إلى {new_status.value}"
                    )
                return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث حالة الفاتورة {sale_id}: {str(e)}")

        return False

    def add_payment(
        self,
        sale_id: int,
        payment_amount: Decimal,
        payment_method: Optional[PaymentMethod] = None,
    ) -> bool:
        """إضافة دفعة للفاتورة"""
        try:
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                return False

            remaining_capacity = sale.total_amount - sale.paid_amount
            applied_amount = (
                payment_amount
                if payment_amount <= remaining_capacity
                else remaining_capacity
            )
            new_paid_amount = sale.paid_amount + applied_amount
            new_remaining_amount = sale.total_amount - new_paid_amount

            # تحديد الحالة الجديدة
            if new_remaining_amount <= 0:
                new_status = SaleStatus.PAID
                new_remaining_amount = Decimal("0.00")
            elif new_paid_amount > 0:
                new_status = SaleStatus.PARTIALLY_PAID
            else:
                new_status = sale.status

            query = """
            UPDATE sales SET 
                paid_amount = ?, remaining_amount = ?, status = ?, payment_method = COALESCE(?, payment_method), updated_at = ?
            WHERE id = ?
            """

            # تحويل الحالة إلى قيمة متوافقة مع constraint
            status_to_db_mapping = {
                SaleStatus.DRAFT: "draft",
                SaleStatus.CONFIRMED: "confirmed",
                SaleStatus.PAID: "paid",
                SaleStatus.PARTIALLY_PAID: "pending",  # constraint لا يدعم 'partially_paid'
                SaleStatus.CANCELLED: "cancelled",
                SaleStatus.RETURNED: "cancelled",
            }
            db_status = status_to_db_mapping.get(new_status, "confirmed")

            if payment_method is not None:
                if isinstance(payment_method, PaymentMethod):
                    payment_method_text = payment_method.value
                else:
                    payment_method_text = str(payment_method)
            else:
                payment_method_text = None

            params = (
                float(new_paid_amount),
                float(new_remaining_amount),
                db_status,
                payment_method_text,
                datetime.now(),
                sale_id,
            )

            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(
                        f"تم إضافة دفعة {applied_amount} للفاتورة {sale_id}"
                    )
                return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة دفعة للفاتورة {sale_id}: {str(e)}")

        return False

    def cancel_sale(self, sale_id: int) -> bool:
        """إلغاء فاتورة"""
        try:
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                return False

            # إرجاع المخزون
            if sale.items:
                self._update_stock_for_sale(sale.items, operation="return")

            # تحديث حالة الفاتورة
            success = self.update_sale_status(sale_id, SaleStatus.CANCELLED)

            if success:
                # إطلاق الإشارات
                try:
                    from src.core.signals import signals  # pyright: ignore[reportMissingImports]

                    signals.sales_updated.emit()
                    signals.sale_updated.emit(sale_id)
                    signals.inventory_updated.emit()
                except Exception:
                    pass

            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إلغاء الفاتورة {sale_id}: {str(e)}")
            return False

    def delete_sale(self, sale_id: int, soft_delete: bool = True) -> bool:
        """حذف فاتورة (حذف ناعم أو صلب)"""
        try:
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                if self.logger:
                    self.logger.warning(f"الفاتورة {sale_id} غير موجودة")
                return False

            if soft_delete:
                # حذف ناعم - تحديث الحالة إلى ملغية وإرجاع المخزون
                if sale.items:
                    self._update_stock_for_sale(sale.items, operation="return")

                # تحديث الحالة إلى ملغية
                query = """
                UPDATE sales SET 
                    status = ?, 
                    is_active = 0,
                    updated_at = ?
                WHERE id = ?
                """
                status_to_db_mapping = {SaleStatus.CANCELLED: "cancelled"}
                db_status = status_to_db_mapping.get(SaleStatus.CANCELLED, "cancelled")
                params = (db_status, datetime.now(), sale_id)
            else:
                # حذف صلب - حذف نهائي
                # إرجاع المخزون أولاً
                if sale.items:
                    self._update_stock_for_sale(sale.items, operation="return")

                # حذف العناصر أولاً
                delete_items_query = "DELETE FROM sale_items WHERE sale_id = ?"
                self.db_manager.execute_query(delete_items_query, (sale_id,))

                # حذف الفاتورة
                query = "DELETE FROM sales WHERE id = ?"
                params = (sale_id,)

            result = self.db_manager.execute_query(query, params)
            if result and (
                hasattr(result, "rowcount")
                and result.rowcount > 0
                or not hasattr(result, "rowcount")
            ):
                # إطلاق الإشارات
                try:
                    from src.core.signals import signals  # pyright: ignore[reportMissingImports]

                    signals.sales_updated.emit()
                    signals.sale_deleted.emit(sale_id)
                    signals.inventory_updated.emit()
                except Exception:
                    pass

                # 🔔 إطلاق Webhook: إرسال Webhook عند حذف فاتورة مبيعات
                try:
                    from src.services.webhook_service import WebhookService

                    webhook_service = WebhookService(self.db_manager, self.logger)

                    # بناء Payload للـ Webhook
                    webhook_payload = {
                        "event": "sale_deleted",
                        "sale_id": sale_id,
                        "invoice_number": sale.invoice_number,
                        "customer_id": sale.customer_id,
                        "deleted_at": datetime.now().isoformat(),
                        "soft_delete": soft_delete,
                    }

                    webhook_service.trigger_webhook(
                        event_type="sale_deleted",
                        payload=webhook_payload,
                        entity_id=sale_id,
                        company_id=sale.company_id
                        if hasattr(sale, "company_id")
                        else None,
                    )

                    if self.logger:
                        self.logger.debug(
                            f"✅ تم إطلاق Webhook: sale_deleted (Sale ID: {sale_id})"
                        )
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق Webhook: {e}")

                if self.logger:
                    action = "تعطيل" if soft_delete else "حذف"
                    self.logger.info(
                        f"✅ تم {action} الفاتورة: ID={sale_id}, invoice_number={sale.invoice_number}"
                    )
                return True

            return False

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"خطأ في حذف الفاتورة {sale_id}: {str(e)}", exc_info=True
                )
            return False

    def _update_stock_for_sale(self, items: List[SaleItem], operation: str):
        """تحديث المخزون للمبيعات (للاستخدام المستقل)"""
        try:
            for item in items:
                if operation == "sale":
                    # خصم من المخزون
                    quantity_change = -item.quantity
                elif operation == "return":
                    # إضافة للمخزون
                    quantity_change = item.quantity
                else:
                    continue

                query = """
                UPDATE products SET 
                    current_stock = current_stock + ?, 
                    updated_at = ?
                WHERE id = ?
                """

                params = (quantity_change, datetime.now(), item.product_id)
                self.db_manager.execute_query(query, params)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المخزون للمبيعات: {str(e)}")

    def _update_stock_in_transaction(
        self, cursor, items: List[SaleItem], operation: str
    ):
        """تحديث المخزون داخل معاملة (transaction) - يستخدم نفس cursor"""
        try:
            for item in items:
                if operation == "sale":
                    # خصم من المخزون
                    quantity_change = -item.quantity
                elif operation == "return":
                    # إضافة للمخزون
                    quantity_change = item.quantity
                else:
                    continue

                query = """
                UPDATE products SET 
                    current_stock = current_stock + ?, 
                    updated_at = ?
                WHERE id = ?
                """

                params = (quantity_change, datetime.now(), item.product_id)
                cursor.execute(query, params)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المخزون داخل المعاملة: {str(e)}")
            raise

    def generate_invoice_number(self) -> str:
        """إنشاء رقم فاتورة جديد"""
        try:
            today = date.today()
            prefix = f"INV-{today.strftime('%Y%m%d')}"

            query = """
            SELECT COUNT(*) FROM sales 
            WHERE invoice_number LIKE ? AND DATE(sale_date) = ?
            """

            result = self.db_manager.fetch_one(query, (f"{prefix}%", today))
            count = (result[0] if result else 0) + 1

            return f"{prefix}-{count:04d}"

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء رقم الفاتورة: {str(e)}")
            return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def get_sales_report(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """تقرير المبيعات"""
        try:
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = start_date

            query = """
            SELECT 
                COUNT(*) as total_invoices,
                COUNT(CASE WHEN status = 'مدفوعة' THEN 1 END) as paid_invoices,
                COUNT(CASE WHEN status = 'مدفوعة جزئياً' THEN 1 END) as partially_paid_invoices,
                COUNT(CASE WHEN status = 'آجل' THEN 1 END) as credit_invoices,
                SUM(total_amount) as total_sales,
                SUM(paid_amount) as total_paid,
                SUM(remaining_amount) as total_remaining,
                AVG(total_amount) as avg_invoice_value
            FROM sales
            WHERE sale_date BETWEEN ? AND ? AND status != 'ملغية'
            """

            result = self.db_manager.fetch_one(query, (start_date, end_date))
            if result:
                return {
                    "period": f"{start_date} إلى {end_date}",
                    "total_invoices": result[0] or 0,
                    "paid_invoices": result[1] or 0,
                    "partially_paid_invoices": result[2] or 0,
                    "credit_invoices": result[3] or 0,
                    "total_sales": float(result[4] or 0),
                    "total_paid": float(result[5] or 0),
                    "total_remaining": float(result[6] or 0),
                    "avg_invoice_value": float(result[7] or 0),
                }

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير المبيعات: {str(e)}")

        return {}

    def _row_to_sale(self, row) -> Sale:
        """تحويل صف قاعدة البيانات إلى كائن مبيعات

        Schema المتوقع: id, invoice_number, customer_id, total_amount, discount_amount,
        final_amount, payment_method, sale_date, user_id, notes, status, paid_amount, remaining_amount,
        currency_id, exchange_rate, base_amount, converted_amount (Multi-Currency),
        is_active, created_at, updated_at (20 عمود)
        """

        # دالة مساعدة لتحويل التاريخ
        def to_date(value):
            if value is None or value == "":
                return None
            try:
                if isinstance(value, date):
                    return value
                if isinstance(value, str):
                    return date.fromisoformat(value)
            except (ValueError, TypeError):
                pass
            return None

        def to_datetime(value):
            if value is None or value == "":
                return None
            try:
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    return datetime.fromisoformat(
                        value.replace(" ", "T") if " " in value else value
                    )
            except (ValueError, TypeError):
                pass
            return None

        try:
            row_len = len(row)

            # معالجة status - العمود 10 (index 10)
            status_value = row[10] if row_len > 10 and row[10] is not None else "مسودة"

            # قراءة paid_amount و remaining_amount للمساعدة في تحديد الحالة
            paid_amount = (
                to_decimal(row[11])
                if row_len > 11 and row[11] is not None
                else Decimal("0")
            )
            remaining_amount = (
                to_decimal(row[12])
                if row_len > 12 and row[12] is not None
                else Decimal("0")
            )
            final_amount = (
                to_decimal(row[5])
                if row_len > 5 and row[5] is not None
                else Decimal("0")
            )

            status_mapping = {
                "draft": SaleStatus.DRAFT,
                "confirmed": SaleStatus.CONFIRMED,
                "paid": SaleStatus.PAID,
                "partially_paid": SaleStatus.PARTIALLY_PAID,
                "cancelled": SaleStatus.CANCELLED,
                "returned": SaleStatus.RETURNED,
                "مسودة": SaleStatus.DRAFT,
                "مؤكدة": SaleStatus.CONFIRMED,
                "مدفوعة": SaleStatus.PAID,
                "مدفوعة جزئياً": SaleStatus.PARTIALLY_PAID,
                "ملغية": SaleStatus.CANCELLED,
                "مرتجعة": SaleStatus.RETURNED,
            }

            # معالجة خاصة لـ 'pending' - تحديد الحالة بناءً على المبالغ المدفوعة
            status_lower = (
                status_value.lower()
                if isinstance(status_value, str)
                else str(status_value).lower()
            )
            if status_lower == "pending":
                # إذا كان هناك مبلغ مدفوع، فهي مدفوعة جزئياً أو مدفوعة بالكامل
                if paid_amount >= final_amount and final_amount > 0:
                    sale_status = SaleStatus.PAID
                elif paid_amount > 0:
                    sale_status = SaleStatus.PARTIALLY_PAID
                else:
                    # إذا لم يكن هناك مبلغ مدفوع، فهي مؤكدة (ليست مسودة)
                    sale_status = SaleStatus.CONFIRMED
            else:
                sale_status = status_mapping.get(status_lower, SaleStatus.DRAFT)

            # معالجة payment_method - العمود 6 (index 6)
            payment_value = row[6] if row_len > 6 and row[6] is not None else "نقدي"
            payment_mapping = {
                "cash": PaymentMethod.CASH,
                "نقدي": PaymentMethod.CASH,
                "card": PaymentMethod.CARD,
                "بطاقة": PaymentMethod.CARD,
                "بطاقة بنكية": PaymentMethod.CARD,
                "bank_transfer": PaymentMethod.BANK_TRANSFER,
                "تحويل": PaymentMethod.BANK_TRANSFER,
                "تحويل بنكي": PaymentMethod.BANK_TRANSFER,
                "credit": PaymentMethod.CREDIT,
                "آجل": PaymentMethod.CREDIT,
                "آجل (ذمم)": PaymentMethod.CREDIT,
                "mixed": PaymentMethod.MIXED,
                "مختلط": PaymentMethod.MIXED,
            }
            payment_method = payment_mapping.get(
                payment_value.lower()
                if isinstance(payment_value, str)
                else payment_value,
                PaymentMethod.CASH,
            )

            # قراءة paid_amount و remaining_amount - الأعمدة 11 و 12
            paid_amount = (
                to_decimal(row[11])
                if row_len > 11 and row[11] is not None
                else Decimal("0")
            )
            remaining_amount = (
                to_decimal(row[12])
                if row_len > 12 and row[12] is not None
                else Decimal("0")
            )

            # إذا كان remaining_amount صفراً ولم يكن paid_amount محدداً، احسبه من final_amount
            if remaining_amount == 0 and paid_amount == 0 and row_len > 5:
                final_amount = (
                    to_decimal(row[5]) if row[5] is not None else Decimal("0")
                )
                remaining_amount = final_amount

            # قراءة حقول Multi-Currency - الأعمدة 13-16
            currency_id = row[13] if row_len > 13 and row[13] is not None else None
            exchange_rate = (
                to_decimal(row[14])
                if row_len > 14 and row[14] is not None
                else Decimal("1.0")
            )
            base_amount = (
                to_decimal(row[15]) if row_len > 15 and row[15] is not None else None
            )
            converted_amount = (
                to_decimal(row[16]) if row_len > 16 and row[16] is not None else None
            )

            # التوافق مع schema الفعلي
            return Sale(
                id=row[0] if row_len > 0 else None,  # id
                invoice_number=row[1]
                if row_len > 1 and row[1]
                else "",  # invoice_number
                customer_id=row[2] if row_len > 2 and row[2] else None,  # customer_id
                customer_name="",  # لا يوجد في DB
                customer_phone="",  # لا يوجد في DB
                sale_date=to_date(row[7]) if row_len > 7 else None,  # sale_date
                due_date=None,  # لا يوجد في DB
                status=sale_status,
                payment_method=payment_method,
                subtotal=to_decimal(row[3])
                if row_len > 3 and row[3] is not None
                else Decimal("0"),  # total_amount as subtotal
                discount_amount=to_decimal(row[4])
                if row_len > 4 and row[4] is not None
                else Decimal("0"),  # discount_amount
                discount_percentage=Decimal("0"),  # لا يوجد في DB
                tax_amount=Decimal("0"),  # لا يوجد في DB
                tax_percentage=Decimal("0"),  # لا يوجد في DB
                total_amount=to_decimal(row[5])
                if row_len > 5 and row[5] is not None
                else Decimal("0"),  # final_amount
                paid_amount=paid_amount,  # paid_amount
                remaining_amount=remaining_amount,  # remaining_amount
                # Multi-Currency Support
                currency_id=currency_id,  # currency_id
                exchange_rate=exchange_rate,  # exchange_rate
                base_amount=base_amount,  # base_amount
                converted_amount=converted_amount,  # converted_amount
                notes=row[9] if row_len > 9 and row[9] else "",  # notes
                created_by=row[8] if row_len > 8 and row[8] else None,  # user_id
                created_at=to_datetime(row[18])
                if row_len > 18 and row[18]
                else None,  # created_at (shifted by 4 currency columns)
                updated_at=to_datetime(row[19])
                if row_len > 19 and row[19]
                else None,  # updated_at (shifted by 4 currency columns)
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحويل صف قاعدة البيانات إلى Sale: {e}")
                self.logger.error(f"عدد الأعمدة: {len(row) if row else 0}")
                try:
                    if row:
                        self.logger.error(
                            f"البيانات: {[row[i] if i < len(row) else 'N/A' for i in range(min(16, len(row) + 1))]}"
                        )
                except Exception as ex:
                    self.logger.error(f"خطأ في طباعة البيانات: {ex}")
            raise

    def _row_to_sale_dict(self, row) -> Dict[str, Any]:
        """تحويل صف مختصر إلى قاموس للاستخدام في الواجهات"""
        try:
            sale_date = row[4]
            if isinstance(sale_date, datetime):
                sale_date_str = sale_date.date().isoformat()
            elif isinstance(sale_date, date):
                sale_date_str = sale_date.isoformat()
            elif isinstance(sale_date, str):
                sale_date_str = sale_date
            else:
                sale_date_str = None

            # قراءة الحالة والمبالغ
            status_value = row[5] if len(row) > 5 else None
            total_amount = float(row[7] or 0) if len(row) > 7 else 0.0
            paid_amount = float(row[8] or 0) if len(row) > 8 else 0.0
            remaining_amount = float(row[9] or 0) if len(row) > 9 else 0.0

            # تحويل الحالة: إذا كانت 'pending'، نحدد الحالة الحقيقية من المبالغ
            if status_value and str(status_value).lower() == "pending":
                if paid_amount >= total_amount and total_amount > 0:
                    # مدفوعة بالكامل
                    status_value = "paid"
                elif paid_amount > 0:
                    # مدفوعة جزئياً
                    status_value = "partially_paid"
                else:
                    # مؤكدة (ليست معلقة)
                    status_value = "confirmed"

            return {
                "id": row[0],
                "invoice_number": row[1],
                "customer_name": row[2] or "",
                "customer_phone": row[3] or "",
                "sale_date": sale_date_str,
                "status": status_value,
                "payment_method": row[6] if len(row) > 6 else None,
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "remaining_amount": remaining_amount,
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحويل صف المبيعات إلى قاموس: {e}")
            return {
                "id": row[0],
                "invoice_number": row[1],
                "customer_name": "",
                "customer_phone": "",
                "sale_date": None,
                "status": None,
                "payment_method": None,
                "total_amount": 0.0,
                "paid_amount": 0.0,
                "remaining_amount": 0.0,
            }

    def _row_to_sale_item(self, row) -> SaleItem:
        """تحويل صف قاعدة البيانات إلى عنصر فاتورة

        Schema المتوقع: id, sale_id, product_id, product_name, product_barcode,
        quantity, unit_price, discount_amount, discount_percentage, tax_amount,
        tax_percentage, total_amount (12 عمود)
        """
        try:
            row_len = len(row)
            return SaleItem(
                id=row[0] if row_len > 0 and row[0] is not None else None,
                sale_id=row[1] if row_len > 1 and row[1] is not None else None,
                product_id=row[2] if row_len > 2 and row[2] is not None else 0,
                product_name=row[3] if row_len > 3 and row[3] is not None else "",
                product_barcode=row[4] if row_len > 4 and row[4] is not None else None,
                quantity=int(row[5]) if row_len > 5 and row[5] is not None else 1,
                unit_price=to_decimal(row[6])
                if row_len > 6 and row[6] is not None
                else Decimal("0"),
                discount_amount=to_decimal(row[7])
                if row_len > 7 and row[7] is not None
                else Decimal("0"),
                discount_percentage=to_decimal(row[8])
                if row_len > 8 and row[8] is not None
                else Decimal("0"),
                tax_amount=to_decimal(row[9])
                if row_len > 9 and row[9] is not None
                else Decimal("0"),
                tax_percentage=to_decimal(row[10])
                if row_len > 10 and row[10] is not None
                else Decimal("0"),
                total_amount=to_decimal(row[11])
                if row_len > 11 and row[11] is not None
                else Decimal("0"),
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحويل عنصر الفاتورة: {e}")
                self.logger.error(f"عدد الأعمدة: {len(row) if row else 0}")
                try:
                    if row:
                        self.logger.error(
                            f"البيانات: {[row[i] if i < len(row) else 'N/A' for i in range(min(12, len(row) + 1))]}"
                        )
                except:
                    pass
            # إرجاع عنصر فارغ بدلاً من رفع استثناء
            return SaleItem(
                id=row[0] if row and len(row) > 0 else None,
                product_id=row[2] if row and len(row) > 2 else 0,
            )

    # ============================================================
    # 🔄 ميزات المرحلة 2: المرتجعات وتحديث الحالة
    # ============================================================

    def update_order_status(self, invoice_id, new_status):
        """تحديث حالة الفاتورة (مثلاً من مكتملة إلى مرتجعة)"""
        try:
            query = "UPDATE sales SET status = ? WHERE id = ?"
            self.db_manager.execute_non_query(query, (new_status, invoice_id))
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error updating order status: {e}")
            return False

    def process_return(self, invoice_id, return_items_list, reason="Changed mind"):
        """
        معالجة عملية إرجاع منتجات من فاتورة.
        invoice_id: رقم الفاتورة الأصلية
        return_items_list: قائمة قواميس [{'product_id': 1, 'qty': 2, 'price': 100}, ...]
        """
        # استخدام get_connection من db_manager
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION")

            # 1. حساب إجمالي المبلغ المسترد
            total_refund = sum(
                item["qty"] * item["price"] for item in return_items_list
            )

            # 2. تسجيل عملية الإرجاع في الجدول الجديد
            cursor.execute(
                """
                INSERT INTO returns (original_invoice_id, reason, total_refund_amount, status)
                VALUES (?, ?, ?, 'approved')
            """,
                (invoice_id, reason, total_refund),
            )
            return_id = cursor.lastrowid

            # 3. معالجة كل منتج
            for item in return_items_list:
                # أ. تسجيل عنصر الإرجاع
                cursor.execute(
                    """
                    INSERT INTO return_items (return_id, product_id, quantity, refund_price)
                    VALUES (?, ?, ?, ?)
                """,
                    (return_id, item["product_id"], item["qty"], item["price"]),
                )

                # ب. إعادة الكمية للمخزون (زيادة المخزون) ➕📦
                cursor.execute(
                    """
                    UPDATE products SET current_stock = current_stock + ? WHERE id = ?
                """,
                    (item["qty"], item["product_id"]),
                )

            # 4. تحديث حالة الفاتورة الأصلية
            cursor.execute(
                """
                UPDATE sales SET return_status = 'returned'
                WHERE id = ?
            """,
                (invoice_id,),
            )

            conn.commit()
            if self.logger:
                self.logger.info(
                    f"✅ Return processed successfully. Refund: {total_refund}"
                )

            # 📢 لا تنس إطلاق الإشارات لتحديث الواجهة
            try:
                from src.core.signals import signals

                signals.inventory_updated.emit()
                signals.sales_updated.emit()
            except ImportError:
                pass

            return True, return_id

        except Exception as e:
            conn.rollback()
            if self.logger:
                self.logger.error(f"❌ Return processing failed: {e}")
            return False, str(e)
        finally:
            cursor.close()

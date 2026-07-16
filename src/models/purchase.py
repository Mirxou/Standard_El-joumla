import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المشتريات - Purchase Model
يحتوي على جميع العمليات المتعلقة بالمشتريات وعناصر المشتريات
متوافق مع مخطط قاعدة البيانات الفعلي ومتطلبات بيئة الاختبارات القديمة.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


class PurchaseStatus(Enum):
    PENDING = "pending"
    RECEIVED = "received"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentStatus(Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"


STATUS_TRANSLATIONS = {
    "pending": "pending",
    "received": "received",
    "partial": "partial",
    "cancelled": "cancelled",
    "returned": "returned",
    "معلقة": "pending",
    "تم الاستلام": "received",
    "مستلمة": "received",
    "جزئي": "partial",
    "ملغاة": "cancelled",
    "ملغية": "cancelled",
    "مرتجعة": "returned",
}

PAYMENT_TRANSLATIONS = {
    "unpaid": "unpaid",
    "partial": "partial",
    "paid": "paid",
    "overdue": "overdue",
    "غير مدفوعة": "unpaid",
    "مدفوعة جزئياً": "partial",
    "مدفوعة جزئيا": "partial",
    "مدفوعة": "paid",
    "متأخرة": "overdue",
}


def parse_status(val: Any) -> PurchaseStatus:
    """تحويل الحالة المدخلة إلى حالة شراء صالحة بالإنجليزية للعمليات الداخلية"""
    if isinstance(val, PurchaseStatus):
        return val
    if isinstance(val, str):
        val_clean = val.strip().lower()
        # Direct Enum match
        for s in PurchaseStatus:
            if s.value.lower() == val_clean or s.name.lower() == val_clean:
                return s
        # Translation match
        trans = STATUS_TRANSLATIONS.get(val_clean)
        if trans:
            for s in PurchaseStatus:
                if s.value.lower() == trans.lower():
                    return s
    return PurchaseStatus.PENDING


def parse_payment_status(val: Any) -> PaymentStatus:
    """تحويل حالة الدفع المدخلة إلى حالة دفع صالحة"""
    if isinstance(val, PaymentStatus):
        return val
    if isinstance(val, str):
        val_clean = val.strip().lower()
        for s in PaymentStatus:
            if s.value.lower() == val_clean or s.name.lower() == val_clean:
                return s
        trans = PAYMENT_TRANSLATIONS.get(val_clean)
        if trans:
            for s in PaymentStatus:
                if s.value.lower() == trans.lower():
                    return s
    return PaymentStatus.UNPAID


@dataclass
class PurchaseItem:
    """عنصر المشتريات"""

    id: Optional[int] = None
    purchase_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    quantity_ordered: Decimal = Decimal("0.00")
    quantity_received: Decimal = Decimal("0.00")
    unit_cost: Decimal = Decimal("0.00")
    discount_percent: Decimal = Decimal("0.00")
    tax_percent: Decimal = Decimal("15.00")  # Default tax percentage
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    barcode: Optional[str] = None

    # Calculated fields
    subtotal: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")

    def __post_init__(self):
        self.product_id = int(self.product_id or 0)
        self.product_name = str(self.product_name or "")
        
        self.quantity_ordered = Decimal(str(self.quantity_ordered or "0.00"))
        self.quantity_received = Decimal(str(self.quantity_received or "0.00"))
        self.unit_cost = Decimal(str(self.unit_cost or "0.00"))
        self.discount_percent = Decimal(str(self.discount_percent or "0.00"))
        self.tax_percent = Decimal(str(self.tax_percent or "15.00"))
        
        self.subtotal = Decimal(str(self.subtotal or "0.00"))
        self.discount_amount = Decimal(str(self.discount_amount or "0.00"))
        self.tax_amount = Decimal(str(self.tax_amount or "0.00"))
        self.total_amount = Decimal(str(self.total_amount or "0.00"))

        if isinstance(self.expiry_date, str) and self.expiry_date:
            try:
                self.expiry_date = date.fromisoformat(self.expiry_date)
            except ValueError:
                pass

        if self.id is None:
            self.calculate_totals()

    @property
    def quantity(self) -> float:
        """لضمان التوافق التنازلي مع الكود القديم"""
        return float(self.quantity_ordered)

    @quantity.setter
    def quantity(self, value):
        self.quantity_ordered = Decimal(str(value))

    @property
    def total_cost(self) -> Decimal:
        """لضمان التوافق التنازلي مع الكود القديم"""
        return self.total_amount

    @total_cost.setter
    def total_cost(self, value):
        self.total_amount = Decimal(str(value))

    @property
    def net_amount(self) -> Decimal:
        """صافي المبلغ بعد الخصم وقبل الضريبة"""
        return self.subtotal - self.discount_amount

    @property
    def pending_quantity(self) -> Decimal:
        return self.quantity_ordered - self.quantity_received

    @property
    def is_fully_received(self) -> bool:
        return self.quantity_received >= self.quantity_ordered

    def calculate_totals(self):
        self.subtotal = self.quantity_ordered * self.unit_cost
        self.discount_amount = self.subtotal * (self.discount_percent / Decimal("100.00"))
        net = self.subtotal - self.discount_amount
        self.tax_amount = net * (self.tax_percent / Decimal("100.00"))
        self.total_amount = net + self.tax_amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "purchase_id": self.purchase_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity_ordered": float(self.quantity_ordered),
            "quantity_received": float(self.quantity_received),
            "unit_cost": float(self.unit_cost),
            "discount_percent": float(self.discount_percent),
            "tax_percent": float(self.tax_percent),
            "subtotal": float(self.subtotal),
            "discount_amount": float(self.discount_amount),
            "tax_amount": float(self.tax_amount),
            "total_amount": float(self.total_amount),
            "net_amount": float(self.subtotal - self.discount_amount),
            "pending_quantity": float(self.pending_quantity),
            "is_fully_received": self.is_fully_received,
            "batch_number": self.batch_number,
            "expiry_date": self.expiry_date.isoformat() if isinstance(self.expiry_date, date) else self.expiry_date,
            "notes": self.notes,
            "barcode": self.barcode,
        }


@dataclass
class Purchase:
    """فاتورة المشتريات"""

    id: Optional[int] = None
    invoice_number: str = ""
    supplier_invoice_number: Optional[str] = None
    supplier_id: int = 0
    supplier_name: Optional[str] = None
    purchase_date: date = field(default_factory=date.today)
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    status: Any = PurchaseStatus.PENDING.value
    payment_status: Any = PaymentStatus.UNPAID.value
    payment_method: Optional[str] = None
    subtotal_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    shipping_cost: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    paid_amount: Decimal = Decimal("0.00")
    remaining_amount: Decimal = Decimal("0.00")
    currency_id: Optional[int] = None
    exchange_rate: Decimal = Decimal("1.00")
    base_amount: Decimal = Decimal("0.00")
    converted_amount: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[PurchaseItem] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.status, Enum):
            self.status = self.status.value
        elif isinstance(self.status, str):
            self.status = parse_status(self.status).value

        if isinstance(self.payment_status, Enum):
            self.payment_status = self.payment_status.value
        elif isinstance(self.payment_status, str):
            self.payment_status = parse_payment_status(self.payment_status).value

        decimal_fields = [
            "subtotal_amount", "discount_amount", "tax_amount", "shipping_cost",
            "total_amount", "paid_amount", "remaining_amount",
            "exchange_rate", "base_amount", "converted_amount"
        ]
        for f in decimal_fields:
            v = getattr(self, f, None)
            if v is not None:
                setattr(self, f, Decimal(str(v)))

        if isinstance(self.purchase_date, str) and self.purchase_date:
            try:
                self.purchase_date = date.fromisoformat(self.purchase_date)
            except ValueError:
                pass

        if isinstance(self.expected_delivery_date, str) and self.expected_delivery_date:
            try:
                self.expected_delivery_date = date.fromisoformat(self.expected_delivery_date)
            except ValueError:
                pass

        if isinstance(self.actual_delivery_date, str) and self.actual_delivery_date:
            try:
                self.actual_delivery_date = date.fromisoformat(self.actual_delivery_date)
            except ValueError:
                pass

    def __setattr__(self, name, value):
        if name == "status":
            if isinstance(value, Enum):
                value = value.value
            elif isinstance(value, str):
                value = parse_status(value).value
        elif name == "payment_status":
            if isinstance(value, Enum):
                value = value.value
            elif isinstance(value, str):
                value = parse_payment_status(value).value
        super().__setattr__(name, value)

    @property
    def is_overdue(self) -> bool:
        if not self.expected_delivery_date:
            return False
        if self.paid_amount >= self.total_amount and self.total_amount > 0:
            return False
        
        target_date = self.expected_delivery_date
        if isinstance(target_date, str):
            try:
                target_date = date.fromisoformat(target_date)
            except ValueError:
                return False
        return target_date < date.today()

    @property
    def is_fully_received(self) -> bool:
        if not self.items:
            return False
        return all(item.is_fully_received for item in self.items)

    @property
    def is_partially_received(self) -> bool:
        if self.is_fully_received:
            return False
        return any(item.quantity_received > 0 for item in self.items)

    @property
    def items_count(self) -> int:
        return len(self.items)

    @property
    def total_quantity_ordered(self) -> Decimal:
        return sum(item.quantity_ordered for item in self.items)

    @property
    def total_quantity_received(self) -> Decimal:
        return sum(item.quantity_received for item in self.items)

    def add_item(self, item: PurchaseItem):
        if item not in self.items:
            self.items.append(item)
        self.calculate_totals()

    def remove_item(self, item_id: int) -> bool:
        initial_len = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        self.calculate_totals()
        return len(self.items) < initial_len

    def calculate_totals(self):
        for item in self.items:
            item.calculate_totals()

        if self.items:
            self.subtotal_amount = sum(
                item.total_amount for item in self.items
            )
            self.discount_amount = sum(
                item.discount_amount for item in self.items
            )
            self.tax_amount = sum(
                item.tax_amount for item in self.items
            )

        self.total_amount = (
            self.subtotal_amount + self.shipping_cost
        )
        self.remaining_amount = self.total_amount - self.paid_amount

        self.base_amount = self.total_amount
        self.converted_amount = (
            self.total_amount * self.exchange_rate
        )

        self._update_payment_status()

    def _update_payment_status(self):
        """تحديث حالة الدفع بناءً على المبالغ المدفوعة"""
        if self.total_amount > 0 and self.paid_amount >= self.total_amount:
            self.payment_status = PaymentStatus.PAID.value
        elif self.paid_amount > 0:
            self.payment_status = PaymentStatus.PARTIAL.value
        else:
            if self.is_overdue:
                self.payment_status = PaymentStatus.OVERDUE.value
            else:
                self.payment_status = PaymentStatus.UNPAID.value

    def to_dict(self) -> Dict[str, Any]:
        p_date = self.purchase_date
        exp_date = self.expected_delivery_date
        act_date = self.actual_delivery_date
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "purchase_date": (
                p_date.isoformat()
                if isinstance(p_date, date) else p_date
            ),
            "expected_delivery_date": (
                exp_date.isoformat()
                if isinstance(exp_date, date) else exp_date
            ),
            "actual_delivery_date": (
                act_date.isoformat()
                if isinstance(act_date, date) else act_date
            ),
            "status": self.status,
            "payment_status": self.payment_status,
            "payment_method": self.payment_method,
            "subtotal_amount": float(self.subtotal_amount),
            "discount_amount": float(self.discount_amount),
            "tax_amount": float(self.tax_amount),
            "shipping_cost": float(self.shipping_cost),
            "total_amount": float(self.total_amount),
            "paid_amount": float(self.paid_amount),
            "remaining_amount": float(self.remaining_amount),
            "currency_id": self.currency_id,
            "exchange_rate": float(self.exchange_rate),
            "base_amount": float(self.base_amount),
            "converted_amount": float(self.converted_amount),
            "notes": self.notes,
            "items_count": self.items_count,
            "total_quantity_ordered": float(
                self.total_quantity_ordered
            ),
            "is_overdue": self.is_overdue,
            "items": [item.to_dict() for item in self.items],
        }


class PurchaseManager:
    """مدير المشتريات"""

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self._tenant_manager = None
        self._tenant_manager_loaded = False

    @property
    def tenant_manager(self):
        """خاصية كسولة لإدارة العزل متعدد المستأجرين"""
        if not self._tenant_manager_loaded:
            try:
                import importlib
                mod = importlib.import_module(
                    'src.core.tenant_isolation'
                )
                if mod is None:
                    raise ImportError(
                        'tenant_isolation is None'
                    )
                cls = getattr(
                    mod, 'TenantIsolationManager', None
                )
                if cls is not None:
                    self._tenant_manager = cls()
                else:
                    self._tenant_manager = mod
            except (ImportError, ModuleNotFoundError):
                self._tenant_manager = None
            self._tenant_manager_loaded = True
        return self._tenant_manager

    def generate_invoice_number(self) -> str:
        """توليد رقم فاتورة بصيغة PUR{N:06d}"""
        try:
            row = self.db_manager.fetch_one(
                "SELECT COUNT(*) FROM purchases"
            )
            count = int(row[0]) if row else 0
        except Exception:
            count = 0
        return f"PUR{count + 1:06d}"

    def create_purchase(self, purchase: Purchase) -> Optional[int]:
        try:
            if not purchase.invoice_number:
                purchase.invoice_number = (
                    self.generate_invoice_number()
                )
            purchase.calculate_totals()
            query = """
            INSERT INTO purchases (
                invoice_number, supplier_invoice_number,
                supplier_id,
                purchase_date, expected_delivery_date,
                received_date,
                status, payment_status, payment_terms,
                subtotal_amount, tax_amount,
                shipping_cost, total_amount,
                paid_amount, remaining_amount,
                currency_id, exchange_rate,
                base_amount, converted_amount,
                notes, user_id,
                created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
            params = (
                purchase.invoice_number,
                purchase.supplier_invoice_number,
                purchase.supplier_id,
                purchase.purchase_date,
                purchase.expected_delivery_date,
                purchase.actual_delivery_date,
                purchase.status,
                purchase.payment_status,
                purchase.payment_method,
                float(purchase.subtotal_amount),
                float(purchase.tax_amount),
                float(purchase.shipping_cost),
                float(purchase.total_amount),
                float(purchase.paid_amount),
                float(purchase.remaining_amount),
                purchase.currency_id,
                float(purchase.exchange_rate),
                float(purchase.base_amount),
                float(purchase.converted_amount),
                purchase.notes,
                purchase.user_id,
            )

            # استخدام execute_query أولاً ثم execute_insert
            purchase_id = None
            try:
                result = self.db_manager.execute_query(
                    query, params
                )
                if result and hasattr(result, 'lastrowid'):
                    purchase_id = result.lastrowid
            except (AttributeError, TypeError):
                purchase_id = (
                    self.db_manager.execute_insert(
                        query, params
                    )
                )

            if purchase_id:
                purchase.id = purchase_id
                for item in purchase.items:
                    item.purchase_id = purchase_id
                    self._create_purchase_item(item)

                # إرسال الإشارات
                self._emit_signals(
                    'purchase_created', purchase_id
                )
                # تشغيل الويب هوك
                self._trigger_webhook(
                    'purchase_created', purchase_id,
                    purchase
                )

                return purchase_id
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error creating purchase: {e}"
                )
            return None

    def _emit_signals(
        self, event: str, entity_id: int
    ):
        """إرسال إشارات النظام"""
        try:
            from src.core.signals import signals
            signals.purchases_updated.emit()
            if event == 'purchase_created':
                signals.purchase_created.emit(entity_id)
        except Exception:
            pass

    def _trigger_webhook(
        self, event_type: str, entity_id: int,
        purchase: Purchase
    ):
        """تشغيل الويب هوك"""
        try:
            from src.services.webhook_service import (
                WebhookService,
            )
            ws = WebhookService()
            ws.trigger_webhook(
                event_type=event_type,
                payload=purchase.to_dict(),
                entity_id=entity_id,
                company_id=None,
            )
        except Exception:
            pass

    def _create_purchase_item(
        self, item: PurchaseItem
    ) -> Optional[int]:
        """إنشاء عنصر مشتريات في قاعدة البيانات"""
        query = """
        INSERT INTO purchase_items (
            purchase_id, product_id, quantity,
            unit_cost, total_cost,
            quantity_ordered, quantity_received,
            discount_percent, discount_amount,
            tax_percent, tax_amount,
            total_amount, expiry_date,
            batch_number, notes, created_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, CURRENT_TIMESTAMP
        )
        """
        params = (
            item.purchase_id,
            item.product_id,
            float(item.quantity_ordered),
            float(item.unit_cost),
            float(item.total_amount),
            float(item.quantity_ordered),
            float(item.quantity_received),
            float(item.discount_percent),
            float(item.discount_amount),
            float(item.tax_percent),
            float(item.tax_amount),
            float(item.total_amount),
            item.expiry_date,
            item.batch_number,
            item.notes,
        )
        try:
            result = self.db_manager.execute_query(
                query, params
            )
            if result and hasattr(result, 'lastrowid'):
                return result.lastrowid
            return None
        except Exception:
            return None

    def get_purchase_by_id(self, purchase_id: int) -> Optional[Purchase]:
        try:
            row = self.db_manager.fetch_one("SELECT * FROM purchases WHERE id = ?", (purchase_id,))
            if not row:
                return None
            purchase = self._row_to_purchase(row)
            items_rows = self.db_manager.fetch_all("SELECT * FROM purchase_items WHERE purchase_id = ?", (purchase_id,))
            purchase.items = [self._row_to_purchase_item(irow) for irow in items_rows]
            purchase.calculate_totals()
            return purchase
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting purchase {purchase_id}: {e}")
            return None

    def _row_to_purchase(self, row) -> Optional[Purchase]:
        if not row:
            return None
        is_dict = isinstance(row, dict)

        if is_dict:
            return Purchase(
                id=row.get("id"),
                invoice_number=row.get("invoice_number", ""),
                supplier_id=row.get("supplier_id", 0),
                supplier_name=row.get("supplier_name"),
                purchase_date=self._parse_date(row.get("purchase_date")),
                expected_delivery_date=self._parse_date(row.get("expected_delivery_date")),
                actual_delivery_date=self._parse_date(row.get("actual_delivery_date") or row.get("received_date")),
                status=row.get("status", PurchaseStatus.PENDING.value),
                payment_status=row.get("payment_status", PaymentStatus.UNPAID.value),
                payment_method=row.get("payment_method"),
                subtotal_amount=Decimal(str(row.get("subtotal_amount") or row.get("subtotal") or 0)),
                discount_amount=Decimal(str(row.get("discount_amount") or 0)),
                tax_amount=Decimal(str(row.get("tax_amount") or 0)),
                shipping_cost=Decimal(str(row.get("shipping_cost") or 0)),
                total_amount=Decimal(str(row.get("total_amount") or row.get("final_amount") or 0)),
                paid_amount=Decimal(str(row.get("paid_amount") or 0)),
                remaining_amount=Decimal(str(row.get("remaining_amount") or 0)),
                currency_id=row.get("currency_id"),
                exchange_rate=Decimal(str(row.get("exchange_rate") or 1)),
                base_amount=Decimal(str(row.get("base_amount") or 0)),
                converted_amount=Decimal(str(row.get("converted_amount") or 0)),
                notes=row.get("notes"),
                user_id=row.get("user_id"),
                created_at=self._parse_datetime(row.get("created_at")),
                updated_at=self._parse_datetime(row.get("updated_at")),
            )

        if len(row) == 26:
            return Purchase(
                id=row[0],
                invoice_number=row[1],
                supplier_id=row[3] if isinstance(row[3], int) else (int(row[2]) if str(row[2]).isdigit() else 0),
                purchase_date=self._parse_date(row[4]),
                expected_delivery_date=self._parse_date(row[5]),
                actual_delivery_date=self._parse_date(row[6]),
                status=row[7],
                payment_status=row[8],
                payment_method=row[9],
                subtotal_amount=Decimal(str(row[10] or 0)),
                discount_amount=Decimal(str(row[11] or 0)),
                tax_amount=Decimal(str(row[12] or 0)),
                shipping_cost=Decimal(str(row[13] or 0)),
                total_amount=Decimal(str(row[14] or 0)),
                paid_amount=Decimal(str(row[15] or 0)),
                remaining_amount=Decimal(str(row[16] or 0)),
                currency_id=row[17],
                exchange_rate=Decimal(str(row[18] or 1)),
                base_amount=Decimal(str(row[19] or 0)),
                converted_amount=Decimal(str(row[20] or 0)),
                notes=row[21],
                user_id=row[22],
                created_at=self._parse_datetime(row[23]),
                updated_at=self._parse_datetime(row[24]),
                supplier_name=row[25],
            )
        
        if len(row) >= 29:
            return Purchase(
                id=row[0],
                invoice_number=row[1],
                supplier_id=row[2],
                total_amount=Decimal(str(row[3] or 0)),
                discount_amount=Decimal(str(row[4] or 0)),
                purchase_date=self._parse_date(row[6]),
                user_id=row[7],
                notes=row[8],
                created_at=self._parse_datetime(row[10]),
                updated_at=self._parse_datetime(row[11]),
                supplier_invoice_number=row[12],
                expected_delivery_date=self._parse_date(row[13]),
                actual_delivery_date=self._parse_date(row[14]),
                status=row[15],
                payment_status=row[16],
                payment_method=row[17],
                subtotal_amount=Decimal(str(row[18] or 0)),
                tax_amount=Decimal(str(row[19] or 0)),
                shipping_cost=Decimal(str(row[20] or 0)),
                paid_amount=Decimal(str(row[21] or 0)),
                remaining_amount=Decimal(str(row[22] or 0)),
                currency_id=row[23],
                exchange_rate=Decimal(str(row[24] or 1)),
                base_amount=Decimal(str(row[25] or 0)),
                converted_amount=Decimal(str(row[26] or 0)),
            )

        return Purchase(
            id=row[0] if len(row) > 0 else None,
            invoice_number=row[1] if len(row) > 1 else "",
            supplier_id=row[2] if len(row) > 2 else 0,
            total_amount=Decimal(str(row[3] if len(row) > 3 else 0)),
            purchase_date=self._parse_date(row[6] if len(row) > 6 else None),
            user_id=row[7] if len(row) > 7 else None,
            notes=row[8] if len(row) > 8 else None,
            status=row[15] if len(row) > 15 else PurchaseStatus.PENDING.value,
            payment_status=row[16] if len(row) > 16 else PaymentStatus.UNPAID.value,
            paid_amount=Decimal(str(row[21] if len(row) > 21 else 0)),
            remaining_amount=Decimal(str(row[22] if len(row) > 22 else 0)),
            created_at=self._parse_datetime(row[10] if len(row) > 10 else None),
            updated_at=self._parse_datetime(row[11] if len(row) > 11 else None),
        )

    def _row_to_purchase_item(self, row) -> Optional[PurchaseItem]:
        if not row:
            return None
        is_dict = isinstance(row, dict)

        if is_dict:
            return PurchaseItem(
                id=row.get("id"),
                purchase_id=row.get("purchase_id"),
                product_id=row.get("product_id", 0),
                product_name=row.get("product_name", ""),
                quantity_ordered=Decimal(str(row.get("quantity_ordered") or row.get("quantity") or 0)),
                quantity_received=Decimal(str(row.get("quantity_received") or 0)),
                unit_cost=Decimal(str(row.get("unit_cost") or 0)),
                discount_percent=Decimal(str(row.get("discount_percent") or 0)),
                discount_amount=Decimal(str(row.get("discount_amount") or 0)),
                tax_percent=Decimal(str(row.get("tax_percent") or 15.00)),
                tax_amount=Decimal(str(row.get("tax_amount") or 0)),
                total_amount=Decimal(str(row.get("total_amount") or row.get("total_cost") or 0)),
                expiry_date=self._parse_date(row.get("expiry_date")),
                batch_number=row.get("batch_number"),
                notes=row.get("notes"),
                barcode=row.get("barcode") or row.get("product_barcode"),
            )

        if len(row) == 16:
            return PurchaseItem(
                id=row[0],
                purchase_id=row[1],
                product_id=row[2],
                quantity_ordered=Decimal(str(row[3] or 0)),
                quantity_received=Decimal(str(row[4] or 0)),
                unit_cost=Decimal(str(row[5] or 0)),
                discount_percent=Decimal(str(row[6] or 0)),
                discount_amount=Decimal(str(row[7] or 0)),
                tax_percent=Decimal(str(row[8] or 15.00)),
                tax_amount=Decimal(str(row[9] or 0)),
                total_amount=Decimal(str(row[10] or 0)),
                expiry_date=self._parse_date(row[11]),
                batch_number=row[12],
                notes=row[13],
                product_name=row[14],
                barcode=row[15],
            )

        if len(row) >= 17:
            return PurchaseItem(
                id=row[0],
                purchase_id=row[1],
                product_id=row[2],
                expiry_date=self._parse_date(row[6]),
                batch_number=row[7],
                quantity_ordered=Decimal(str(row[9] or row[3] or 0)),
                quantity_received=Decimal(str(row[10] or 0)),
                discount_percent=Decimal(str(row[11] or 0)),
                discount_amount=Decimal(str(row[12] or 0)),
                tax_percent=Decimal(str(row[13] or 15.00)),
                tax_amount=Decimal(str(row[14] or 0)),
                total_amount=Decimal(str(row[15] or row[5] or 0)),
                notes=row[16],
                unit_cost=Decimal(str(row[4] or 0)),
            )

        return PurchaseItem(
            id=row[0] if len(row) > 0 else None,
            purchase_id=row[1] if len(row) > 1 else None,
            product_id=row[2] if len(row) > 2 else 0,
            quantity_ordered=Decimal(str(row[3] if len(row) > 3 else 0)),
            unit_cost=Decimal(str(row[4] if len(row) > 4 else 0)),
            total_amount=Decimal(str(row[5] if len(row) > 5 else 0)),
            expiry_date=self._parse_date(row[6] if len(row) > 6 else None),
            batch_number=row[7] if len(row) > 7 else None,
        )

    def _row_to_purchase_dict(self, row) -> Dict[str, Any]:
        if not row:
            return {}
        is_dict = isinstance(row, dict)

        def gv(k, i, d=None):
            if is_dict:
                return row.get(k, d)
            return row[i] if len(row) > i else d

        p_date = gv("purchase_date", 3)
        if p_date:
            if isinstance(p_date, (date, datetime)):
                p_date_str = p_date.strftime("%Y-%m-%d")
            else:
                p_date_str = str(p_date).split()[0]
        else:
            p_date_str = ""

        return {
            "id": gv("id", 0),
            "invoice_number": gv("invoice_number", 1, ""),
            "supplier_name": gv("supplier_name", 2, ""),
            "purchase_date": p_date_str,
            "total_amount": float(Decimal(str(gv("total_amount", 4, 0)))),
            "paid_amount": float(Decimal(str(gv("paid_amount", 5, 0)))),
            "remaining_amount": float(Decimal(str(gv("remaining_amount", 6, 0)))),
            "status": gv("status", 7, ""),
            "payment_status": gv("payment_status", 8, ""),
        }

    def _parse_datetime(self, val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except Exception:
            return None

    def _parse_date(self, val):
        if not val:
            return None
        if isinstance(val, (date, datetime)):
            return val
        try:
            return date.fromisoformat(str(val))
        except Exception:
            try:
                return datetime.fromisoformat(str(val)).date()
            except Exception:
                return None

    def get_purchase_by_invoice_number(self, invoice_number: str) -> Optional[Purchase]:
        try:
            row = self.db_manager.fetch_one("SELECT * FROM purchases WHERE invoice_number = ?", (invoice_number,))
            if not row:
                return None
            purchase = self._row_to_purchase(row)
            items_rows = self.db_manager.fetch_all("SELECT * FROM purchase_items WHERE purchase_id = ?", (purchase.id,))
            purchase.items = [self._row_to_purchase_item(irow) for irow in items_rows]
            purchase.calculate_totals()
            return purchase
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting purchase by invoice number: {e}")
            return None

    def update_purchase(self, purchase: Purchase) -> bool:
        try:
            purchase.calculate_totals()
            query = """
            UPDATE purchases SET
                invoice_number = ?,
                supplier_invoice_number = ?,
                supplier_id = ?,
                purchase_date = ?,
                expected_delivery_date = ?,
                received_date = ?,
                status = ?, payment_status = ?,
                payment_terms = ?,
                subtotal_amount = ?, tax_amount = ?,
                shipping_cost = ?, total_amount = ?,
                paid_amount = ?,
                remaining_amount = ?,
                currency_id = ?, exchange_rate = ?,
                base_amount = ?,
                converted_amount = ?,
                notes = ?, user_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            params = (
                purchase.invoice_number,
                purchase.supplier_invoice_number,
                purchase.supplier_id,
                purchase.purchase_date,
                purchase.expected_delivery_date,
                purchase.actual_delivery_date,
                purchase.status,
                purchase.payment_status,
                purchase.payment_method,
                float(purchase.subtotal_amount),
                float(purchase.tax_amount),
                float(purchase.shipping_cost),
                float(purchase.total_amount),
                float(purchase.paid_amount),
                float(purchase.remaining_amount),
                purchase.currency_id,
                float(purchase.exchange_rate),
                float(purchase.base_amount),
                float(purchase.converted_amount),
                purchase.notes,
                purchase.user_id,
                purchase.id,
            )
            # استخدام execute_query أولاً ثم execute_non_query
            try:
                self.db_manager.execute_query(
                    query, params
                )
            except (AttributeError, TypeError):
                self.db_manager.execute_non_query(
                    query, params
                )

            # تحديث عناصر المشتريات
            for item in purchase.items:
                if item.id:
                    self._update_purchase_item(item)
                else:
                    item.purchase_id = purchase.id
                    self._create_purchase_item(item)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating purchase: {e}")
            return False

    def _update_purchase_item(self, item: PurchaseItem):
        query = """
        UPDATE purchase_items SET
            quantity = ?, unit_cost = ?, total_cost = ?,
            quantity_ordered = ?, quantity_received = ?,
            discount_percent = ?, discount_amount = ?, tax_percent = ?, tax_amount = ?,
            total_amount = ?, expiry_date = ?, batch_number = ?, notes = ?
        WHERE id = ?
        """
        params = (
            float(item.quantity_ordered),
            float(item.unit_cost),
            float(item.total_amount),
            float(item.quantity_ordered),
            float(item.quantity_received),
            float(item.discount_percent),
            float(item.discount_amount),
            float(item.tax_percent),
            float(item.tax_amount),
            float(item.total_amount),
            item.expiry_date,
            item.batch_number,
            item.notes,
            item.id,
        )
        self.db_manager.execute_non_query(query, params)

    def delete_purchase(self, purchase_id: int, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                query = "UPDATE purchases SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                result = self.db_manager.execute_non_query(query, (purchase_id,))
            else:
                self.db_manager.execute_non_query("DELETE FROM purchase_items WHERE purchase_id = ?", (purchase_id,))
                result = self.db_manager.execute_non_query("DELETE FROM purchases WHERE id = ?", (purchase_id,))
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting purchase: {e}")
            return False

    def list_purchases(self, search_term: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            if search_term:
                query = """
                SELECT p.id, p.invoice_number, s.name as supplier_name, p.purchase_date,
                       p.total_amount, p.paid_amount, p.remaining_amount, p.status, p.payment_status
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.invoice_number LIKE ? ORDER BY p.id DESC LIMIT ?
                """
                rows = self.db_manager.fetch_all(query, (f"%{search_term}%", limit))
            else:
                query = """
                SELECT p.id, p.invoice_number, s.name as supplier_name, p.purchase_date,
                       p.total_amount, p.paid_amount, p.remaining_amount, p.status, p.payment_status
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.id DESC LIMIT ?
                """
                rows = self.db_manager.fetch_all(query, (limit,))

            return [self._row_to_purchase_dict(row) for row in rows if row]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing purchases: {e}")
            return []

    def search_purchases(
        self,
        search_term: str = '',
        status: Optional[str] = None,
    ) -> List[Purchase]:
        """بحث في المشتريات مع دعم فلترة الحالة"""
        try:
            query = """
                SELECT p.*
                FROM purchases p
                LEFT JOIN suppliers s
                    ON p.supplier_id = s.id
                WHERE 1=1
            """
            params: list = []

            if search_term:
                query += (
                    " AND (p.invoice_number LIKE ?)"
                )
                params.append(f"%{search_term}%")

            if status:
                query += " AND p.status = ?"
                params.append(status)

            rows = self.db_manager.fetch_all(
                query, tuple(params)
            )
            purchases = []
            for row in rows:
                if row:
                    purchase = self._row_to_purchase(row)
                    purchases.append(purchase)
            return purchases
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error searching purchases: {e}"
                )
            return []

    def update_purchase_status(self, purchase_id: int, status: Any) -> bool:
        try:
            status_str = status.value if isinstance(status, Enum) else status
            query = "UPDATE purchases SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            result = self.db_manager.execute_non_query(query, (status_str, purchase_id))
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating purchase status: {e}")
            return False

    def cancel_purchase(self, purchase_id: int, reason: Optional[str] = None) -> bool:
        try:
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False

            status_str = purchase.status.value if isinstance(purchase.status, Enum) else str(purchase.status)
            if status_str.lower() in ["received", "received", "تم الاستلام"]:
                return False

            purchase.status = PurchaseStatus.CANCELLED
            if reason:
                if purchase.notes:
                    purchase.notes = f"{purchase.notes} | Cancel Reason: {reason}"
                else:
                    purchase.notes = f"Cancel Reason: {reason}"

            return self.update_purchase(purchase)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error cancelling purchase: {e}")
            return False

    def receive_purchase_items(self, purchase_id: int, items_received: List[Dict[str, Any]]) -> bool:
        try:
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False

            item_lookup = {item.id: item for item in purchase.items if item.id is not None}

            for rec in items_received:
                item_id = rec.get("item_id")
                qty_rec = Decimal(str(rec.get("quantity_received", 0)))
                if item_id in item_lookup:
                    item = item_lookup[item_id]
                    item.quantity_received += qty_rec
                    item.calculate_totals()

                    self._update_product_stock(
                        product_id=item.product_id,
                        quantity=qty_rec,
                        unit_cost=item.unit_cost,
                        expiry_date=item.expiry_date,
                        batch_number=item.batch_number
                    )

            purchase.calculate_totals()
            if purchase.is_fully_received:
                purchase.status = PurchaseStatus.RECEIVED
            elif purchase.total_quantity_received > 0:
                purchase.status = PurchaseStatus.PARTIAL

            return self.update_purchase(purchase)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error receiving purchase items: {e}")
            return False

    # NOTE: This is the LEGACY purchase receiving path. It updates stock directly
    # without going through receiving notes or quality checks.
    # New code should use the receiving notes workflow (ReceivingDialog / receiving_note service)
    # which includes quality inspection and proper audit trails.
    def _update_product_stock(self, product_id: int, quantity: Decimal, unit_cost: Decimal, expiry_date=None, batch_number=None):
        try:
            query = "UPDATE products SET current_stock = current_stock + ? WHERE id = ?"
            self.db_manager.execute_non_query(query, (float(quantity), product_id))

            if batch_number:
                row = self.db_manager.fetch_one(
                    "SELECT id FROM batches WHERE product_id = ? AND batch_number = ?",
                    (product_id, batch_number)
                )
                if row:
                    self.db_manager.execute_non_query(
                        "UPDATE batches SET quantity = quantity + ?, cost_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (float(quantity), float(unit_cost), row[0])
                    )
                else:
                    self.db_manager.execute_insert(
                        """INSERT INTO batches (product_id, batch_number, quantity, cost_price, expiry_date, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                        (product_id, batch_number, float(quantity), float(unit_cost), expiry_date)
                    )
            else:
                default_batch = f"PUR-{date.today().strftime('%Y%m%d')}"
                self.db_manager.execute_insert(
                    """INSERT INTO batches (product_id, batch_number, quantity, cost_price, expiry_date, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                    (product_id, default_batch, float(quantity), float(unit_cost), expiry_date)
                )

            # تسجيل حركة المخزون للمراجعة والتدقيق (audit trail)
            # Legacy path: directly recording stock movement for old purchase receiving
            try:
                self.db_manager.execute_non_query(
                    """INSERT INTO stock_movements (product_id, movement_type, quantity, reference_type, notes)
                       VALUES (?, 'in', ?, 'purchase_receive', 'استلام مشتريات - مسار قديم (بدون فحص جودة)')""",
                    (product_id, float(quantity))
                )
            except Exception as mov_err:
                if self.logger:
                    self.logger.warning(f"Failed to record stock_movement for product {product_id}: {mov_err}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating product stock: {e}")

    def get_purchases_summary(self) -> Dict[str, Any]:
        try:
            row = self.db_manager.fetch_one(
                "SELECT COUNT(*), SUM(total_amount), SUM(paid_amount), SUM(remaining_amount) FROM purchases"
            )
            if not row or row[0] == 0:
                return {
                    "total_purchases": 0,
                    "total_amount": 0.0,
                    "total_paid": 0.0,
                    "total_remaining": 0.0,
                    "avg_purchase_value": 0.0,
                }
            count = row[0]
            total = float(row[1] or 0)
            paid = float(row[2] or 0)
            remaining = float(row[3] or 0)
            avg = total / count if count > 0 else 0.0
            return {
                "total_purchases": count,
                "total_amount": total,
                "total_paid": paid,
                "total_remaining": remaining,
                "avg_purchase_value": avg,
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting purchases summary: {e}")
            return {
                "total_purchases": 0,
                "total_amount": 0.0,
                "total_paid": 0.0,
                "total_remaining": 0.0,
                "avg_purchase_value": 0.0,
            }

    def get_purchases_report(self) -> Dict[str, Any]:
        """تقرير شامل عن المشتريات"""
        try:
            row = self.db_manager.fetch_one(
                """
                SELECT
                    COUNT(*),
                    SUM(CASE WHEN status='pending'
                        THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status='received'
                        THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status='partial'
                        THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status='cancelled'
                        THEN 1 ELSE 0 END),
                    SUM(total_amount),
                    SUM(paid_amount),
                    SUM(remaining_amount)
                FROM purchases
                """
            )
            if not row:
                return self._empty_report()
            return {
                "total_purchases": row[0] or 0,
                "pending_purchases": row[1] or 0,
                "received_purchases": row[2] or 0,
                "partial_purchases": row[3] or 0,
                "cancelled_purchases": row[4] or 0,
                "total_amount": float(
                    row[5] or 0
                ),
                "paid_amount": float(
                    row[6] or 0
                ),
                "remaining_amount": float(
                    row[7] or 0
                ),
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting report: {e}"
                )
            return self._empty_report()

    def _empty_report(self) -> Dict[str, Any]:
        """تقرير فارغ"""
        return {
            "total_purchases": 0,
            "pending_purchases": 0,
            "received_purchases": 0,
            "partial_purchases": 0,
            "cancelled_purchases": 0,
            "total_amount": 0.0,
            "paid_amount": 0.0,
            "remaining_amount": 0.0,
        }

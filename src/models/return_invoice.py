#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المرتجعات - Return Invoice Model
يحتوي على جميع العمليات المتعلقة بمرتجعات المبيعات والمشتريات
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path



class ReturnType(Enum):
    """نوع المرتجع"""
    SALE_RETURN = "مرتجع مبيعات"      # إرجاع من عميل
    PURCHASE_RETURN = "مرتجع مشتريات"  # إرجاع لمورد


class ReturnReason(Enum):
    """سبب الإرجاع"""
    DEFECTIVE = "معيب"
    DAMAGED = "تالف"
    WRONG_ITEM = "منتج خاطئ"
    EXPIRED = "منتهي الصلاحية"
    NOT_AS_DESCRIBED = "مخالف للوصف"
    CUSTOMER_REQUEST = "طلب العميل"
    OVERSTOCK = "فائض مخزون"
    OTHER = "أخرى"


class ReturnStatus(Enum):
    """حالة المرتجع"""
    PENDING = "معلق"           # في انتظار الموافقة
    APPROVED = "موافق عليه"    # تمت الموافقة
    REJECTED = "مرفوض"         # تم الرفض
    COMPLETED = "مكتمل"        # تم الاستلام والمعالجة
    CANCELLED = "ملغي"         # تم الإلغاء


class RefundMethod(Enum):
    """طريقة الاسترداد"""
    CASH = "نقدي"
    CREDIT_NOTE = "إشعار دائن"     # يضاف للحساب
    EXCHANGE = "استبدال"            # استبدال بمنتج آخر
    BANK_TRANSFER = "تحويل بنكي"
    STORE_CREDIT = "رصيد المتجر"    # يحفظ كرصيد للعميل


@dataclass
class ReturnItem:
    """عنصر في فاتورة المرتجعات"""
    id: Optional[int] = None
    return_id: Optional[int] = None
    original_sale_item_id: Optional[int] = None  # ربط بالبند الأصلي
    original_purchase_item_id: Optional[int] = None
    
    product_id: int = 0
    product_name: str = ""
    product_barcode: Optional[str] = None
    
    # الكميات
    quantity_returned: Decimal = Decimal('0')
    quantity_original: Decimal = Decimal('0')  # الكمية في الفاتورة الأصلية
    
    # الأسعار
    unit_price: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    
    # تفاصيل الإرجاع
    return_reason: Optional[ReturnReason] = None
    condition: Optional[str] = None  # حالة المنتج عند الإرجاع
    restockable: bool = True  # هل يمكن إعادته للمخزون؟
    
    notes: Optional[str] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        decimal_fields = ['quantity_returned', 'quantity_original', 'unit_price',
                         'discount_amount', 'tax_amount', 'total_amount']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        # تحويل السبب
        if isinstance(self.return_reason, str):
            try:
                self.return_reason = ReturnReason[self.return_reason]
            except KeyError:
                for reason in ReturnReason:
                    if reason.value == self.return_reason:
                        self.return_reason = reason
                        break
    
    @property
    def can_return_quantity(self) -> Decimal:
        """الكمية المتاحة للإرجاع"""
        return self.quantity_original - self.quantity_returned
    
    def calculate_totals(self):
        """حساب المجاميع"""
        subtotal = self.unit_price * self.quantity_returned
        self.total_amount = subtotal - self.discount_amount + self.tax_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'return_id': self.return_id,
            'original_sale_item_id': self.original_sale_item_id,
            'original_purchase_item_id': self.original_purchase_item_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_barcode': self.product_barcode,
            'quantity_returned': float(self.quantity_returned),
            'quantity_original': float(self.quantity_original),
            'unit_price': float(self.unit_price),
            'discount_amount': float(self.discount_amount),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'return_reason': self.return_reason.name if isinstance(self.return_reason, ReturnReason) else self.return_reason,
            'condition': self.condition,
            'restockable': self.restockable,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnItem':
        """إنشاء من قاموس"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ReturnInvoice:
    """نموذج بيانات فاتورة المرتجعات"""
    id: Optional[int] = None
    return_number: str = ""
    return_type: ReturnType = ReturnType.SALE_RETURN
    
    # الربط بالفاتورة الأصلية
    original_sale_id: Optional[int] = None
    original_purchase_id: Optional[int] = None
    original_invoice_number: Optional[str] = None
    
    # معلومات العميل/المورد
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # التواريخ
    return_date: Optional[date] = None
    original_invoice_date: Optional[date] = None
    
    # الحالة
    status: ReturnStatus = ReturnStatus.PENDING
    
    # السبب
    return_reason: Optional[ReturnReason] = None
    description: Optional[str] = None
    
    # المبالغ
    subtotal: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    
    # الاسترداد
    refund_method: Optional[RefundMethod] = None
    refund_amount: Decimal = Decimal('0.00')
    refund_date: Optional[date] = None
    refund_reference: Optional[str] = None
    
    # إشعار دائن
    credit_note_number: Optional[str] = None
    credit_note_amount: Decimal = Decimal('0.00')
    
    # الاستبدال
    exchange_sale_id: Optional[int] = None  # فاتورة الاستبدال
    
    # ملاحظات
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    # البنود
    items: List[ReturnItem] = None
    
    # التتبع
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        # تهيئة القوائم
        if self.items is None:
            self.items = []
        
        # تحويل القيم العددية
        decimal_fields = ['subtotal', 'discount_amount', 'tax_amount', 
                         'total_amount', 'refund_amount', 'credit_note_amount']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        # تحويل الأنواع والحالات
        if isinstance(self.return_type, str):
            try:
                self.return_type = ReturnType[self.return_type]
            except KeyError:
                for rtype in ReturnType:
                    if rtype.value == self.return_type:
                        self.return_type = rtype
                        break
        
        if isinstance(self.status, str):
            try:
                self.status = ReturnStatus[self.status]
            except KeyError:
                for status in ReturnStatus:
                    if status.value == self.status:
                        self.status = status
                        break
        
        if isinstance(self.return_reason, str):
            try:
                self.return_reason = ReturnReason[self.return_reason]
            except KeyError:
                for reason in ReturnReason:
                    if reason.value == self.return_reason:
                        self.return_reason = reason
                        break
        
        if isinstance(self.refund_method, str):
            try:
                self.refund_method = RefundMethod[self.refund_method]
            except KeyError:
                for method in RefundMethod:
                    if method.value == self.refund_method:
                        self.refund_method = method
                        break
        
        # تحويل التواريخ
        date_fields = ['return_date', 'original_invoice_date', 'refund_date']
        for field_name in date_fields:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value).date())
                except:
                    pass
        
        # تحويل الطوابع الزمنية
        for field_name in ['created_at', 'updated_at', 'approved_at']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value))
                except:
                    pass
    
    @property
    def is_sale_return(self) -> bool:
        """هل هذا مرتجع مبيعات؟"""
        return self.return_type == ReturnType.SALE_RETURN
    
    @property
    def is_purchase_return(self) -> bool:
        """هل هذا مرتجع مشتريات؟"""
        return self.return_type == ReturnType.PURCHASE_RETURN
    
    @property
    def can_approve(self) -> bool:
        """هل يمكن الموافقة على المرتجع؟"""
        return self.status == ReturnStatus.PENDING and len(self.items) > 0
    
    @property
    def can_complete(self) -> bool:
        """هل يمكن إتمام المرتجع؟"""
        return self.status == ReturnStatus.APPROVED
    
    @property
    def needs_refund(self) -> bool:
        """هل يحتاج إلى استرداد مالي؟"""
        return (self.refund_method in [RefundMethod.CASH, RefundMethod.BANK_TRANSFER] 
                and self.refund_amount > 0)
    
    @property
    def restockable_items(self) -> List[ReturnItem]:
        """البنود القابلة لإعادة التخزين"""
        return [item for item in self.items if item.restockable]
    
    def add_item(self, item: ReturnItem):
        """إضافة بند للمرتجع"""
        item.return_id = self.id
        item.calculate_totals()
        self.items.append(item)
        self.calculate_totals()
    
    def remove_item(self, item_id: int):
        """حذف بند من المرتجع"""
        self.items = [item for item in self.items if item.id != item_id]
        self.calculate_totals()
    
    def calculate_totals(self):
        """حساب المجاميع"""
        self.subtotal = sum(item.total_amount for item in self.items)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        
        # حساب مبلغ الاسترداد الافتراضي
        if self.refund_amount == 0:
            self.refund_amount = self.total_amount
    
    def approve(self, approved_by: int):
        """الموافقة على المرتجع"""
        if self.can_approve:
            self.status = ReturnStatus.APPROVED
            self.approved_by = approved_by
            self.approved_at = datetime.now()
            return True
        return False
    
    def reject(self):
        """رفض المرتجع"""
        if self.status == ReturnStatus.PENDING:
            self.status = ReturnStatus.REJECTED
            return True
        return False
    
    def complete(self):
        """إتمام المرتجع"""
        if self.can_complete:
            self.status = ReturnStatus.COMPLETED
            return True
        return False
    
    def cancel(self):
        """إلغاء المرتجع"""
        if self.status in [ReturnStatus.PENDING, ReturnStatus.APPROVED]:
            self.status = ReturnStatus.CANCELLED
            return True
        return False
    
    def process_refund(self, method: RefundMethod, amount: Decimal, reference: Optional[str] = None):
        """معالجة الاسترداد"""
        self.refund_method = method
        self.refund_amount = amount
        self.refund_date = date.today()
        self.refund_reference = reference
    
    def generate_credit_note(self, credit_note_number: str):
        """إنشاء إشعار دائن"""
        self.credit_note_number = credit_note_number
        self.credit_note_amount = self.total_amount
        self.refund_method = RefundMethod.CREDIT_NOTE
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'return_number': self.return_number,
            'return_type': self.return_type.name if isinstance(self.return_type, ReturnType) else self.return_type,
            'original_sale_id': self.original_sale_id,
            'original_purchase_id': self.original_purchase_id,
            'original_invoice_number': self.original_invoice_number,
            'customer_id': self.customer_id,
            'supplier_id': self.supplier_id,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'original_invoice_date': self.original_invoice_date.isoformat() if self.original_invoice_date else None,
            'status': self.status.name if isinstance(self.status, ReturnStatus) else self.status,
            'return_reason': self.return_reason.name if isinstance(self.return_reason, ReturnReason) else self.return_reason,
            'description': self.description,
            'subtotal': float(self.subtotal),
            'discount_amount': float(self.discount_amount),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'refund_method': self.refund_method.name if isinstance(self.refund_method, RefundMethod) else self.refund_method,
            'refund_amount': float(self.refund_amount),
            'refund_date': self.refund_date.isoformat() if self.refund_date else None,
            'refund_reference': self.refund_reference,
            'credit_note_number': self.credit_note_number,
            'credit_note_amount': float(self.credit_note_amount),
            'exchange_sale_id': self.exchange_sale_id,
            'notes': self.notes,
            'internal_notes': self.internal_notes,
            'items': [item.to_dict() for item in self.items],
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnInvoice':
        """إنشاء من قاموس"""
        items_data = data.pop('items', [])
        
        # إنشاء ReturnInvoice فقط مع الحقول الموجودة في dataclass
        return_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return_invoice = cls(**return_fields)
        
        # تحويل البنود
        return_invoice.items = [ReturnItem.from_dict(item) if isinstance(item, dict) else item 
                               for item in items_data]
        return return_invoice


class ReturnManager:
    """مدير المرتجعات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self._tenant_manager = None
    
    @property
    def tenant_manager(self):
        if self._tenant_manager is None:
            try:
                from src.core.tenant_isolation import TenantIsolationManager
                self._tenant_manager = TenantIsolationManager(self.db_manager)
            except ImportError:
                pass
        return self._tenant_manager
    
    def create_return(self, return_invoice: ReturnInvoice) -> Optional[int]:
        """إنشاء مرتجع جديد"""
        try:
             # Generate Number if empty
            if not return_invoice.return_number:
                return_invoice.return_number = f"RET-{int(datetime.now().timestamp())}"

            query = """
            INSERT INTO returns (
                return_number, return_type, original_sale_id, original_purchase_id,
                customer_id, supplier_id, return_date, status, return_reason,
                total_amount, refund_method, notes, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            params = (
                return_invoice.return_number,
                return_invoice.return_type.name if isinstance(return_invoice.return_type, ReturnType) else return_invoice.return_type,
                return_invoice.original_sale_id,
                return_invoice.original_purchase_id,
                return_invoice.customer_id,
                return_invoice.supplier_id,
                return_invoice.return_date,
                return_invoice.status.name if isinstance(return_invoice.status, ReturnStatus) else return_invoice.status,
                return_invoice.return_reason.name if isinstance(return_invoice.return_reason, ReturnReason) else return_invoice.return_reason,
                float(return_invoice.total_amount),
                return_invoice.refund_method.name if isinstance(return_invoice.refund_method, RefundMethod) and return_invoice.refund_method else None,
                return_invoice.notes,
                return_invoice.created_by,
                now.isoformat(),
                now.isoformat()
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                return_id = result.lastrowid
                return_invoice.id = return_id
                
                # Insert Items
                for item in return_invoice.items:
                    item.return_id = return_id
                    self._create_return_item(item)
                    
                return return_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating return: {e}")
            return None

    def _create_return_item(self, item: ReturnItem):
        try:
            query = """
            INSERT INTO return_items (
                return_id, product_id, quantity_returned, unit_price, total_amount, return_reason
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                item.return_id,
                item.product_id,
                float(item.quantity_returned),
                float(item.unit_price),
                float(item.total_amount),
                item.return_reason.name if isinstance(item.return_reason, ReturnReason) else item.return_reason
            )
            self.db_manager.execute_query(query, params)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating return item: {e}")

    def list_returns(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT r.*, 
                   COALESCE(c.name, 'عميل عام') as customer_name, 
                   COALESCE(s.name, 'مورد عام') as supplier_name
            FROM returns r
            LEFT JOIN customers c ON r.customer_id = c.id
            LEFT JOIN suppliers s ON r.supplier_id = s.id
            ORDER BY r.return_date DESC
            LIMIT ?
            """
            results = self.db_manager.fetch_all(query, (limit,))
            return [dict(row) for row in results]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing returns: {e}")
            return []

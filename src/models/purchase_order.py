#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج أوامر الشراء - Purchase Order Model
نظام احترافي لإدارة أوامر الشراء مع المطابقة الثلاثية والتقييم
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class POStatus(Enum):
    """حالات أمر الشراء"""
    DRAFT = "مسودة"                    # قيد الإنشاء
    PENDING_APPROVAL = "في انتظار الموافقة"  # يحتاج موافقة
    APPROVED = "موافق عليه"             # تمت الموافقة
    SENT = "مرسل للمورد"               # تم إرساله للمورد
    CONFIRMED = "مؤكد"                  # أكده المورد
    PARTIALLY_RECEIVED = "مستلم جزئياً"  # استلام جزئي
    FULLY_RECEIVED = "مستلم بالكامل"     # استلام كامل
    CLOSED = "مغلق"                     # مغلق نهائياً
    CANCELLED = "ملغي"                  # تم الإلغاء


class POPriority(Enum):
    """أولوية أمر الشراء"""
    LOW = "منخفضة"
    NORMAL = "عادية"
    HIGH = "عالية"
    URGENT = "عاجلة"


class DeliveryTerms(Enum):
    """شروط التسليم"""
    EXW = "EXW - من المصنع"
    FOB = "FOB - على ظهر السفينة"
    CIF = "CIF - التكلفة والتأمين والشحن"
    DAP = "DAP - التسليم في المكان"
    DDP = "DDP - التسليم بعد دفع الرسوم"


class PaymentTerms(Enum):
    """شروط الدفع"""
    CASH = "نقدي فوري"
    NET_7 = "خلال 7 أيام"
    NET_15 = "خلال 15 يوم"
    NET_30 = "خلال 30 يوم"
    NET_60 = "خلال 60 يوم"
    NET_90 = "خلال 90 يوم"
    ADVANCE_50 = "دفعة مقدمة 50%"
    ADVANCE_100 = "دفع كامل مقدم"


@dataclass
class PurchaseOrderItem:
    """بند في أمر الشراء"""
    id: Optional[int] = None
    po_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    product_code: Optional[str] = None
    description: Optional[str] = None
    
    # الكميات
    quantity_ordered: Decimal = Decimal('0')
    quantity_received: Decimal = Decimal('0')
    quantity_pending: Decimal = Decimal('0')  # محسوبة
    
    # الأسعار
    unit_price: Decimal = Decimal('0.00')
    discount_percentage: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    tax_percentage: Decimal = Decimal('15.00')
    tax_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    
    # تفاصيل المنتج
    unit_of_measure: Optional[str] = None  # وحدة القياس
    specifications: Optional[str] = None   # المواصفات المطلوبة
    manufacturer: Optional[str] = None     # الشركة المصنعة
    
    # التسليم
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    lead_time_days: int = 0  # وقت التسليم المتوقع بالأيام
    
    # الجودة
    quality_requirements: Optional[str] = None
    inspection_required: bool = False
    
    notes: Optional[str] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        decimal_fields = ['quantity_ordered', 'quantity_received', 'quantity_pending',
                         'unit_price', 'discount_percentage', 'discount_amount',
                         'tax_percentage', 'tax_amount', 'total_amount']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        # تحويل التواريخ
        for field_name in ['expected_delivery_date', 'actual_delivery_date']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value).date())
                except:
                    pass
    
    @property
    def subtotal(self) -> Decimal:
        """المجموع الفرعي قبل الخصم"""
        return self.unit_price * self.quantity_ordered
    
    @property
    def net_amount(self) -> Decimal:
        """المبلغ الصافي بعد الخصم قبل الضريبة"""
        return self.subtotal - self.discount_amount
    
    @property
    def is_fully_received(self) -> bool:
        """هل تم استلام الكمية كاملة؟"""
        return self.quantity_received >= self.quantity_ordered
    
    @property
    def is_partially_received(self) -> bool:
        """هل تم استلام جزئي؟"""
        return Decimal('0') < self.quantity_received < self.quantity_ordered
    
    @property
    def receipt_percentage(self) -> Decimal:
        """نسبة الاستلام"""
        if self.quantity_ordered > 0:
            return (self.quantity_received / self.quantity_ordered) * 100
        return Decimal('0')
    
    def calculate_totals(self):
        """حساب المجاميع"""
        # حساب الخصم من النسبة
        if self.discount_percentage > 0 and self.discount_amount == 0:
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        
        # حساب المبلغ الصافي
        net = self.subtotal - self.discount_amount
        
        # حساب الضريبة
        if self.tax_percentage > 0:
            self.tax_amount = (net * self.tax_percentage) / 100
        
        # المجموع النهائي
        self.total_amount = net + self.tax_amount
        
        # حساب الكمية المعلقة
        self.quantity_pending = self.quantity_ordered - self.quantity_received
    
    def receive_quantity(self, quantity: Decimal, delivery_date: Optional[date] = None):
        """استلام كمية"""
        self.quantity_received += quantity
        if self.quantity_received > self.quantity_ordered:
            self.quantity_received = self.quantity_ordered
        
        if delivery_date:
            self.actual_delivery_date = delivery_date
        elif not self.actual_delivery_date:
            self.actual_delivery_date = date.today()
        
        self.calculate_totals()
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'po_id': self.po_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_code': self.product_code,
            'description': self.description,
            'quantity_ordered': float(self.quantity_ordered),
            'quantity_received': float(self.quantity_received),
            'quantity_pending': float(self.quantity_pending),
            'unit_price': float(self.unit_price),
            'discount_percentage': float(self.discount_percentage),
            'discount_amount': float(self.discount_amount),
            'tax_percentage': float(self.tax_percentage),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'unit_of_measure': self.unit_of_measure,
            'specifications': self.specifications,
            'manufacturer': self.manufacturer,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'lead_time_days': self.lead_time_days,
            'quality_requirements': self.quality_requirements,
            'inspection_required': self.inspection_required,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PurchaseOrderItem':
        """إنشاء من قاموس"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PurchaseOrder:
    """نموذج أمر الشراء"""
    id: Optional[int] = None
    po_number: str = ""
    
    # المورد
    supplier_id: int = 0
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_email: Optional[str] = None
    supplier_phone: Optional[str] = None
    
    # التواريخ
    order_date: Optional[date] = None
    required_date: Optional[date] = None  # التاريخ المطلوب
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    approved_date: Optional[date] = None
    sent_date: Optional[date] = None
    
    # الحالة والأولوية
    status: POStatus = POStatus.DRAFT
    priority: POPriority = POPriority.NORMAL
    
    # الشروط
    payment_terms: Optional[PaymentTerms] = None
    delivery_terms: Optional[DeliveryTerms] = None
    
    # عنوان التسليم
    delivery_address: Optional[str] = None
    delivery_contact_person: Optional[str] = None
    delivery_phone: Optional[str] = None
    
    # المبالغ
    subtotal: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    discount_percentage: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    shipping_cost: Decimal = Decimal('0.00')
    other_charges: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    
    # الدفع
    advance_payment: Decimal = Decimal('0.00')  # الدفعة المقدمة
    paid_amount: Decimal = Decimal('0.00')       # المبلغ المدفوع
    balance_due: Decimal = Decimal('0.00')       # الرصيد المستحق
    
    # الملاحظات
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    
    # البنود
    items: List[PurchaseOrderItem] = field(default_factory=list)
    
    # المرجعيات
    reference_number: Optional[str] = None  # رقم مرجعي
    requisition_id: Optional[int] = None    # طلب الشراء المرجعي
    quote_id: Optional[int] = None          # عرض السعر المرجعي
    
    # الفاتورة المرتبطة (للمطابقة الثلاثية)
    related_invoice_id: Optional[int] = None
    invoice_matched: bool = False
    invoice_match_date: Optional[date] = None
    
    # التتبع
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    received_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        # تهيئة القوائم
        if self.items is None:
            self.items = []
        
        # تحويل القيم العددية
        decimal_fields = ['subtotal', 'discount_amount', 'discount_percentage',
                         'tax_amount', 'shipping_cost', 'other_charges', 
                         'total_amount', 'advance_payment', 'paid_amount', 'balance_due']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        # تحويل الأنواع
        if isinstance(self.status, str):
            try:
                self.status = POStatus[self.status]
            except KeyError:
                for status in POStatus:
                    if status.value == self.status:
                        self.status = status
                        break
        
        if isinstance(self.priority, str):
            try:
                self.priority = POPriority[self.priority]
            except KeyError:
                for priority in POPriority:
                    if priority.value == self.priority:
                        self.priority = priority
                        break
        
        if isinstance(self.payment_terms, str):
            try:
                self.payment_terms = PaymentTerms[self.payment_terms]
            except KeyError:
                for term in PaymentTerms:
                    if term.value == self.payment_terms:
                        self.payment_terms = term
                        break
        
        if isinstance(self.delivery_terms, str):
            try:
                self.delivery_terms = DeliveryTerms[self.delivery_terms]
            except KeyError:
                for term in DeliveryTerms:
                    if term.value == self.delivery_terms:
                        self.delivery_terms = term
                        break
        
        # تحويل التواريخ
        date_fields = ['order_date', 'required_date', 'expected_delivery_date',
                      'actual_delivery_date', 'approved_date', 'sent_date', 
                      'invoice_match_date']
        for field_name in date_fields:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value).date())
                except:
                    pass
        
        # تحويل الطوابع الزمنية
        for field_name in ['created_at', 'updated_at']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value))
                except:
                    pass
    
    @property
    def is_draft(self) -> bool:
        """هل هو مسودة؟"""
        return self.status == POStatus.DRAFT
    
    @property
    def is_pending_approval(self) -> bool:
        """هل ينتظر الموافقة؟"""
        return self.status == POStatus.PENDING_APPROVAL
    
    @property
    def is_approved(self) -> bool:
        """هل تمت الموافقة عليه؟"""
        return self.status in [POStatus.APPROVED, POStatus.SENT, POStatus.CONFIRMED,
                               POStatus.PARTIALLY_RECEIVED, POStatus.FULLY_RECEIVED]
    
    @property
    def is_fully_received(self) -> bool:
        """هل تم الاستلام الكامل؟"""
        return self.status == POStatus.FULLY_RECEIVED
    
    @property
    def can_be_edited(self) -> bool:
        """هل يمكن تعديله؟"""
        return self.status in [POStatus.DRAFT, POStatus.PENDING_APPROVAL]
    
    @property
    def can_be_approved(self) -> bool:
        """هل يمكن الموافقة عليه؟"""
        return self.status == POStatus.PENDING_APPROVAL and len(self.items) > 0
    
    @property
    def can_be_sent(self) -> bool:
        """هل يمكن إرساله؟"""
        return self.status == POStatus.APPROVED
    
    @property
    def can_receive(self) -> bool:
        """هل يمكن استلام شحنات؟"""
        return self.status in [POStatus.SENT, POStatus.CONFIRMED, POStatus.PARTIALLY_RECEIVED]
    
    @property
    def total_quantity_ordered(self) -> Decimal:
        """إجمالي الكميات المطلوبة"""
        return sum(item.quantity_ordered for item in self.items)
    
    @property
    def total_quantity_received(self) -> Decimal:
        """إجمالي الكميات المستلمة"""
        return sum(item.quantity_received for item in self.items)
    
    @property
    def receipt_percentage(self) -> Decimal:
        """نسبة الاستلام الكلية"""
        total_ordered = self.total_quantity_ordered
        if total_ordered > 0:
            return (self.total_quantity_received / total_ordered) * 100
        return Decimal('0')
    
    @property
    def days_until_required(self) -> Optional[int]:
        """عدد الأيام حتى التاريخ المطلوب"""
        if self.required_date:
            return (self.required_date - date.today()).days
        return None
    
    @property
    def is_overdue(self) -> bool:
        """هل متأخر عن الموعد؟"""
        if self.required_date and not self.is_fully_received:
            return date.today() > self.required_date
        return False
    
    def add_item(self, item: PurchaseOrderItem):
        """إضافة بند"""
        item.po_id = self.id
        item.calculate_totals()
        self.items.append(item)
        self.calculate_totals()
    
    def remove_item(self, item_id: int):
        """حذف بند"""
        self.items = [item for item in self.items if item.id != item_id]
        self.calculate_totals()
    
    def calculate_totals(self):
        """حساب المجاميع"""
        # حساب المجموع الفرعي من البنود
        self.subtotal = sum(item.total_amount for item in self.items)
        
        # حساب الخصم الإجمالي
        if self.discount_percentage > 0 and self.discount_amount == 0:
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        
        # المجموع النهائي
        self.total_amount = (self.subtotal - self.discount_amount + 
                            self.shipping_cost + self.other_charges)
        
        # حساب الرصيد المستحق
        self.balance_due = self.total_amount - self.paid_amount
    
    def submit_for_approval(self):
        """تقديم للموافقة"""
        if self.status == POStatus.DRAFT and len(self.items) > 0:
            self.status = POStatus.PENDING_APPROVAL
            return True
        return False
    
    def approve(self, approved_by: int):
        """الموافقة على الأمر"""
        if self.can_be_approved:
            self.status = POStatus.APPROVED
            self.approved_by = approved_by
            self.approved_date = date.today()
            return True
        return False
    
    def send_to_supplier(self):
        """إرسال للمورد"""
        if self.can_be_sent:
            self.status = POStatus.SENT
            self.sent_date = date.today()
            return True
        return False
    
    def confirm_by_supplier(self):
        """تأكيد من المورد"""
        if self.status == POStatus.SENT:
            self.status = POStatus.CONFIRMED
            return True
        return False
    
    def receive_shipment(self, items_received: Dict[int, Decimal], delivery_date: Optional[date] = None):
        """استلام شحنة"""
        if not self.can_receive:
            return False
        
        for item_id, quantity in items_received.items():
            for item in self.items:
                if item.id == item_id:
                    item.receive_quantity(quantity, delivery_date)
        
        # تحديث الحالة
        all_received = all(item.is_fully_received for item in self.items)
        any_received = any(item.quantity_received > 0 for item in self.items)
        
        if all_received:
            self.status = POStatus.FULLY_RECEIVED
            self.actual_delivery_date = delivery_date or date.today()
        elif any_received:
            self.status = POStatus.PARTIALLY_RECEIVED
        
        return True
    
    def close(self):
        """إغلاق الأمر"""
        if self.is_fully_received:
            self.status = POStatus.CLOSED
            return True
        return False
    
    def cancel(self, reason: Optional[str] = None):
        """إلغاء الأمر"""
        if self.status not in [POStatus.FULLY_RECEIVED, POStatus.CLOSED]:
            self.status = POStatus.CANCELLED
            if reason:
                self.internal_notes = f"{self.internal_notes or ''}\nسبب الإلغاء: {reason}"
            return True
        return False
    
    def match_with_invoice(self, invoice_id: int) -> bool:
        """مطابقة مع فاتورة (3-way matching)"""
        if self.is_fully_received:
            self.related_invoice_id = invoice_id
            self.invoice_matched = True
            self.invoice_match_date = date.today()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'po_number': self.po_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'supplier_contact': self.supplier_contact,
            'supplier_email': self.supplier_email,
            'supplier_phone': self.supplier_phone,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'required_date': self.required_date.isoformat() if self.required_date else None,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'approved_date': self.approved_date.isoformat() if self.approved_date else None,
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'status': self.status.name if isinstance(self.status, POStatus) else self.status,
            'priority': self.priority.name if isinstance(self.priority, POPriority) else self.priority,
            'payment_terms': self.payment_terms.name if isinstance(self.payment_terms, PaymentTerms) else self.payment_terms,
            'delivery_terms': self.delivery_terms.name if isinstance(self.delivery_terms, DeliveryTerms) else self.delivery_terms,
            'delivery_address': self.delivery_address,
            'delivery_contact_person': self.delivery_contact_person,
            'delivery_phone': self.delivery_phone,
            'subtotal': float(self.subtotal),
            'discount_amount': float(self.discount_amount),
            'discount_percentage': float(self.discount_percentage),
            'tax_amount': float(self.tax_amount),
            'shipping_cost': float(self.shipping_cost),
            'other_charges': float(self.other_charges),
            'total_amount': float(self.total_amount),
            'advance_payment': float(self.advance_payment),
            'paid_amount': float(self.paid_amount),
            'balance_due': float(self.balance_due),
            'notes': self.notes,
            'internal_notes': self.internal_notes,
            'terms_and_conditions': self.terms_and_conditions,
            'items': [item.to_dict() for item in self.items],
            'reference_number': self.reference_number,
            'requisition_id': self.requisition_id,
            'quote_id': self.quote_id,
            'related_invoice_id': self.related_invoice_id,
            'invoice_matched': self.invoice_matched,
            'invoice_match_date': self.invoice_match_date.isoformat() if self.invoice_match_date else None,
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'received_by': self.received_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PurchaseOrder':
        """إنشاء من قاموس"""
        items_data = data.pop('items', [])
        po_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        po = cls(**po_fields)
        po.items = [PurchaseOrderItem.from_dict(item) if isinstance(item, dict) else item 
                   for item in items_data]
        return po

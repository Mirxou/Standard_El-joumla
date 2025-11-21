#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج عروض الأسعار - Quote Model
يحتوي على جميع العمليات المتعلقة بعروض الأسعار
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))


class QuoteStatus(Enum):
    """حالات عرض السعر"""
    DRAFT = "مسودة"          # تحت الإنشاء
    SENT = "مرسل"            # تم إرساله للعميل
    ACCEPTED = "مقبول"       # قبله العميل
    REJECTED = "مرفوض"       # رفضه العميل
    EXPIRED = "منتهي"        # انتهت صلاحيته
    CONVERTED = "محول"       # تم تحويله لفاتورة
    CANCELLED = "ملغي"       # تم إلغاؤه


@dataclass
class QuoteItem:
    """عنصر في عرض السعر"""
    id: Optional[int] = None
    quote_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    product_barcode: Optional[str] = None
    description: Optional[str] = None
    quantity: Decimal = Decimal('1')
    unit_price: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    discount_percentage: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    tax_percentage: Decimal = Decimal('15.00')  # ضريبة القيمة المضافة
    total_amount: Decimal = Decimal('0.00')
    notes: Optional[str] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        decimal_fields = ['quantity', 'unit_price', 'discount_amount', 
                         'discount_percentage', 'tax_amount', 'tax_percentage', 
                         'total_amount']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
    
    @property
    def subtotal(self) -> Decimal:
        """المجموع الفرعي قبل الخصم"""
        return self.unit_price * self.quantity
    
    @property
    def net_amount(self) -> Decimal:
        """المبلغ الصافي بعد الخصم وقبل الضريبة"""
        return self.subtotal - self.discount_amount
    
    def calculate_totals(self):
        """حساب المجاميع"""
        # حساب الخصم من النسبة المئوية
        if self.discount_percentage > 0 and self.discount_amount == 0:
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        
        # حساب المبلغ الصافي
        net = self.subtotal - self.discount_amount
        
        # حساب الضريبة
        if self.tax_percentage > 0:
            self.tax_amount = (net * self.tax_percentage) / 100
        
        # حساب المجموع النهائي
        self.total_amount = net + self.tax_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'quote_id': self.quote_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_barcode': self.product_barcode,
            'description': self.description,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'discount_amount': float(self.discount_amount),
            'discount_percentage': float(self.discount_percentage),
            'tax_amount': float(self.tax_amount),
            'tax_percentage': float(self.tax_percentage),
            'total_amount': float(self.total_amount),
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuoteItem':
        """إنشاء من قاموس"""
        return cls(
            id=data.get('id'),
            quote_id=data.get('quote_id'),
            product_id=data.get('product_id', 0),
            product_name=data.get('product_name', ''),
            product_barcode=data.get('product_barcode'),
            description=data.get('description'),
            quantity=Decimal(str(data.get('quantity', 1))),
            unit_price=Decimal(str(data.get('unit_price', 0))),
            discount_amount=Decimal(str(data.get('discount_amount', 0))),
            discount_percentage=Decimal(str(data.get('discount_percentage', 0))),
            tax_amount=Decimal(str(data.get('tax_amount', 0))),
            tax_percentage=Decimal(str(data.get('tax_percentage', 15))),
            total_amount=Decimal(str(data.get('total_amount', 0))),
            notes=data.get('notes')
        )


@dataclass
class Quote:
    """نموذج بيانات عرض السعر"""
    id: Optional[int] = None
    quote_number: str = ""
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    
    # التواريخ
    quote_date: Optional[date] = None
    valid_until: Optional[date] = None
    sent_date: Optional[date] = None
    response_date: Optional[date] = None
    
    # الحالة
    status: QuoteStatus = QuoteStatus.DRAFT
    
    # المبالغ
    subtotal: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    discount_percentage: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    
    # شروط الدفع
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    
    # ملاحظات
    notes: Optional[str] = None
    internal_notes: Optional[str] = None  # ملاحظات داخلية لا يراها العميل
    terms_and_conditions: Optional[str] = None
    
    # البنود
    items: List[QuoteItem] = None
    
    # معلومات التحويل
    converted_to_sale_id: Optional[int] = None
    converted_date: Optional[date] = None
    
    # التتبع
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        # تهيئة القوائم
        if self.items is None:
            self.items = []
        
        # تحويل القيم العددية
        decimal_fields = ['subtotal', 'discount_amount', 'discount_percentage',
                         'tax_amount', 'total_amount']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        # تحويل الحالة
        if isinstance(self.status, str):
            try:
                self.status = QuoteStatus[self.status]
            except KeyError:
                # محاولة المطابقة بالقيمة العربية
                for status in QuoteStatus:
                    if status.value == self.status:
                        self.status = status
                        break
        
        # تحويل التواريخ
        date_fields = ['quote_date', 'valid_until', 'sent_date', 
                      'response_date', 'converted_date']
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
    def is_valid(self) -> bool:
        """هل العرض لا يزال صالحاً؟"""
        if not self.valid_until:
            return True
        return date.today() <= self.valid_until
    
    @property
    def is_expired(self) -> bool:
        """هل انتهت صلاحية العرض؟"""
        return not self.is_valid
    
    @property
    def can_be_converted(self) -> bool:
        """هل يمكن تحويل العرض لفاتورة؟"""
        return (self.status in [QuoteStatus.ACCEPTED, QuoteStatus.SENT] and 
                self.is_valid and 
                not self.converted_to_sale_id and
                len(self.items) > 0)
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """عدد الأيام المتبقية حتى انتهاء الصلاحية"""
        if not self.valid_until:
            return None
        delta = self.valid_until - date.today()
        return delta.days
    
    def add_item(self, item: QuoteItem):
        """إضافة بند للعرض"""
        item.quote_id = self.id
        item.calculate_totals()
        self.items.append(item)
        self.calculate_totals()
    
    def remove_item(self, item_id: int):
        """حذف بند من العرض"""
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
        self.total_amount = self.subtotal - self.discount_amount
    
    def mark_as_sent(self):
        """تعيين الحالة كمرسل"""
        self.status = QuoteStatus.SENT
        if not self.sent_date:
            self.sent_date = date.today()
    
    def mark_as_accepted(self):
        """تعيين الحالة كمقبول"""
        self.status = QuoteStatus.ACCEPTED
        self.response_date = date.today()
    
    def mark_as_rejected(self):
        """تعيين الحالة كمرفوض"""
        self.status = QuoteStatus.REJECTED
        self.response_date = date.today()
    
    def mark_as_converted(self, sale_id: int):
        """تعيين الحالة كمحول"""
        self.status = QuoteStatus.CONVERTED
        self.converted_to_sale_id = sale_id
        self.converted_date = date.today()
    
    def check_expiry(self):
        """فحص وتحديث حالة الصلاحية"""
        if self.is_expired and self.status not in [QuoteStatus.CONVERTED, 
                                                    QuoteStatus.ACCEPTED,
                                                    QuoteStatus.REJECTED,
                                                    QuoteStatus.CANCELLED]:
            self.status = QuoteStatus.EXPIRED
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'quote_number': self.quote_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'customer_address': self.customer_address,
            'quote_date': self.quote_date.isoformat() if self.quote_date else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'response_date': self.response_date.isoformat() if self.response_date else None,
            'status': self.status.name if isinstance(self.status, QuoteStatus) else self.status,
            'subtotal': float(self.subtotal),
            'discount_amount': float(self.discount_amount),
            'discount_percentage': float(self.discount_percentage),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'payment_terms': self.payment_terms,
            'delivery_terms': self.delivery_terms,
            'notes': self.notes,
            'internal_notes': self.internal_notes,
            'terms_and_conditions': self.terms_and_conditions,
            'items': [item.to_dict() for item in self.items],
            'converted_to_sale_id': self.converted_to_sale_id,
            'converted_date': self.converted_date.isoformat() if self.converted_date else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quote':
        """إنشاء من قاموس"""
        items_data = data.pop('items', [])
        
        # إنشاء Quote فقط مع الحقول الموجودة في dataclass
        quote_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        quote = cls(**quote_fields)
        
        # تحويل البنود
        quote.items = [QuoteItem.from_dict(item) if isinstance(item, dict) else item 
                      for item in items_data]
        return quote

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج استلام البضائع وتقييم الموردين
Receiving Notes & Supplier Evaluation Models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class ReceivingStatus(Enum):
    """حالات الاستلام"""
    PENDING = "معلق"           # في انتظار الاستلام
    IN_PROGRESS = "جاري الاستلام"  # جاري العملية
    COMPLETED = "مكتمل"        # تم الاستلام
    PARTIALLY_ACCEPTED = "مقبول جزئياً"  # قبول جزئي
    REJECTED = "مرفوض"         # مرفوض كلياً
    ON_HOLD = "معلق"           # معلق لسبب


class InspectionStatus(Enum):
    """حالات الفحص"""
    NOT_REQUIRED = "غير مطلوب"
    PENDING = "في انتظار الفحص"
    IN_PROGRESS = "جاري الفحص"
    PASSED = "نجح"
    FAILED = "فشل"
    CONDITIONAL = "مشروط"


class QualityRating(Enum):
    """تقييم الجودة"""
    EXCELLENT = "ممتاز"
    GOOD = "جيد"
    ACCEPTABLE = "مقبول"
    POOR = "ضعيف"
    REJECTED = "مرفوض"


@dataclass
class ReceivingItem:
    """بند استلام"""
    id: Optional[int] = None
    receiving_id: Optional[int] = None
    po_item_id: int = 0  # مرتبط ببند أمر الشراء
    
    product_id: int = 0
    product_name: str = ""
    product_code: Optional[str] = None
    
    # الكميات
    quantity_ordered: Decimal = Decimal('0')   # المطلوبة
    quantity_received: Decimal = Decimal('0')  # المستلمة
    quantity_accepted: Decimal = Decimal('0')  # المقبولة
    quantity_rejected: Decimal = Decimal('0')  # المرفوضة
    quantity_damaged: Decimal = Decimal('0')   # التالفة
    
    # الفحص
    inspection_status: InspectionStatus = InspectionStatus.NOT_REQUIRED
    quality_rating: Optional[QualityRating] = None
    inspection_notes: Optional[str] = None
    inspector_name: Optional[str] = None
    inspection_date: Optional[date] = None
    
    # التخزين
    warehouse_location: Optional[str] = None
    batch_number: Optional[str] = None
    serial_numbers: Optional[str] = None  # أرقام تسلسلية مفصولة بفاصلة
    expiry_date: Optional[date] = None
    
    # المطابقة
    matches_specifications: bool = True
    variance_reason: Optional[str] = None  # سبب الاختلاف
    
    notes: Optional[str] = None
    
    def __post_init__(self):
        """تحويل القيم"""
        decimal_fields = ['quantity_ordered', 'quantity_received', 
                         'quantity_accepted', 'quantity_rejected', 'quantity_damaged']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        # تحويل الأنواع
        if isinstance(self.inspection_status, str):
            try:
                self.inspection_status = InspectionStatus[self.inspection_status]
            except KeyError:
                for status in InspectionStatus:
                    if status.value == self.inspection_status:
                        self.inspection_status = status
                        break
        
        if isinstance(self.quality_rating, str):
            try:
                self.quality_rating = QualityRating[self.quality_rating]
            except KeyError:
                for rating in QualityRating:
                    if rating.value == self.quality_rating:
                        self.quality_rating = rating
                        break
        
        # تحويل التواريخ
        for field_name in ['inspection_date', 'expiry_date']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value).date())
                except:
                    pass
    
    @property
    def acceptance_rate(self) -> Decimal:
        """معدل القبول"""
        if self.quantity_received > 0:
            return (self.quantity_accepted / self.quantity_received) * 100
        return Decimal('0')
    
    @property
    def rejection_rate(self) -> Decimal:
        """معدل الرفض"""
        if self.quantity_received > 0:
            return (self.quantity_rejected / self.quantity_received) * 100
        return Decimal('0')
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'receiving_id': self.receiving_id,
            'po_item_id': self.po_item_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_code': self.product_code,
            'quantity_ordered': float(self.quantity_ordered),
            'quantity_received': float(self.quantity_received),
            'quantity_accepted': float(self.quantity_accepted),
            'quantity_rejected': float(self.quantity_rejected),
            'quantity_damaged': float(self.quantity_damaged),
            'inspection_status': self.inspection_status.name if isinstance(self.inspection_status, InspectionStatus) else self.inspection_status,
            'quality_rating': self.quality_rating.name if isinstance(self.quality_rating, QualityRating) else self.quality_rating,
            'inspection_notes': self.inspection_notes,
            'inspector_name': self.inspector_name,
            'inspection_date': self.inspection_date.isoformat() if self.inspection_date else None,
            'warehouse_location': self.warehouse_location,
            'batch_number': self.batch_number,
            'serial_numbers': self.serial_numbers,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'matches_specifications': self.matches_specifications,
            'variance_reason': self.variance_reason,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceivingItem':
        """إنشاء من قاموس"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ReceivingNote:
    """إشعار استلام"""
    id: Optional[int] = None
    receiving_number: str = ""
    
    # أمر الشراء المرتبط
    purchase_order_id: int = 0
    po_number: Optional[str] = None
    
    # المورد
    supplier_id: int = 0
    supplier_name: Optional[str] = None
    
    # معلومات الشحنة
    shipment_number: Optional[str] = None
    carrier_name: Optional[str] = None  # شركة الشحن
    tracking_number: Optional[str] = None
    
    # التواريخ
    receiving_date: Optional[date] = None
    shipment_date: Optional[date] = None
    expected_date: Optional[date] = None
    
    # الحالة
    status: ReceivingStatus = ReceivingStatus.PENDING
    
    # موظف الاستلام
    received_by: Optional[int] = None
    receiver_name: Optional[str] = None
    
    # البنود
    items: List[ReceivingItem] = field(default_factory=list)
    
    # الملاحظات
    notes: Optional[str] = None
    discrepancy_notes: Optional[str] = None  # ملاحظات الاختلافات
    
    # التوقيعات (للتوثيق)
    receiver_signature: Optional[str] = None
    supervisor_signature: Optional[str] = None
    
    # التتبع
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحويل القيم"""
        if self.items is None:
            self.items = []
        
        if isinstance(self.status, str):
            try:
                self.status = ReceivingStatus[self.status]
            except KeyError:
                for status in ReceivingStatus:
                    if status.value == self.status:
                        self.status = status
                        break
        
        # تحويل التواريخ
        date_fields = ['receiving_date', 'shipment_date', 'expected_date']
        for field_name in date_fields:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value).date())
                except:
                    pass
        
        # تحويل الطوابع الزمنية
        for field_name in ['created_at', 'updated_at', 'completed_at']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value))
                except:
                    pass
    
    @property
    def total_quantity_received(self) -> Decimal:
        """إجمالي الكميات المستلمة"""
        return sum(item.quantity_received for item in self.items)
    
    @property
    def total_quantity_accepted(self) -> Decimal:
        """إجمالي الكميات المقبولة"""
        return sum(item.quantity_accepted for item in self.items)
    
    @property
    def total_quantity_rejected(self) -> Decimal:
        """إجمالي الكميات المرفوضة"""
        return sum(item.quantity_rejected for item in self.items)
    
    @property
    def overall_acceptance_rate(self) -> Decimal:
        """معدل القبول الإجمالي"""
        total_received = self.total_quantity_received
        if total_received > 0:
            return (self.total_quantity_accepted / total_received) * 100
        return Decimal('0')
    
    @property
    def is_on_time(self) -> bool:
        """هل وصل في الموعد؟"""
        if self.expected_date and self.receiving_date:
            return self.receiving_date <= self.expected_date
        return True
    
    @property
    def delay_days(self) -> int:
        """عدد أيام التأخير"""
        if self.expected_date and self.receiving_date:
            if self.receiving_date > self.expected_date:
                return (self.receiving_date - self.expected_date).days
        return 0
    
    def add_item(self, item: ReceivingItem):
        """إضافة بند"""
        item.receiving_id = self.id
        self.items.append(item)
    
    def complete(self):
        """إتمام الاستلام"""
        if self.status in [ReceivingStatus.PENDING, ReceivingStatus.IN_PROGRESS]:
            self.status = ReceivingStatus.COMPLETED
            self.completed_at = datetime.now()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'receiving_number': self.receiving_number,
            'purchase_order_id': self.purchase_order_id,
            'po_number': self.po_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'shipment_number': self.shipment_number,
            'carrier_name': self.carrier_name,
            'tracking_number': self.tracking_number,
            'receiving_date': self.receiving_date.isoformat() if self.receiving_date else None,
            'shipment_date': self.shipment_date.isoformat() if self.shipment_date else None,
            'expected_date': self.expected_date.isoformat() if self.expected_date else None,
            'status': self.status.name if isinstance(self.status, ReceivingStatus) else self.status,
            'received_by': self.received_by,
            'receiver_name': self.receiver_name,
            'items': [item.to_dict() for item in self.items],
            'notes': self.notes,
            'discrepancy_notes': self.discrepancy_notes,
            'receiver_signature': self.receiver_signature,
            'supervisor_signature': self.supervisor_signature,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceivingNote':
        """إنشاء من قاموس"""
        items_data = data.pop('items', [])
        rn_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        rn = cls(**rn_fields)
        rn.items = [ReceivingItem.from_dict(item) if isinstance(item, dict) else item 
                   for item in items_data]
        return rn


@dataclass
class SupplierEvaluation:
    """تقييم المورد"""
    id: Optional[int] = None
    supplier_id: int = 0
    supplier_name: Optional[str] = None
    
    # الفترة التقييمية
    evaluation_period_start: Optional[date] = None
    evaluation_period_end: Optional[date] = None
    
    # معايير التقييم (من 1 إلى 5)
    quality_score: Decimal = Decimal('0')       # جودة المنتجات
    delivery_score: Decimal = Decimal('0')      # الالتزام بالمواعيد
    pricing_score: Decimal = Decimal('0')       # التنافسية السعرية
    communication_score: Decimal = Decimal('0') # التواصل والاستجابة
    reliability_score: Decimal = Decimal('0')   # الموثوقية
    
    # المقاييس الفعلية
    total_orders: int = 0
    completed_orders: int = 0
    on_time_deliveries: int = 0
    late_deliveries: int = 0
    rejected_shipments: int = 0
    total_value: Decimal = Decimal('0.00')
    
    # معدلات
    on_time_delivery_rate: Decimal = Decimal('0.00')
    quality_acceptance_rate: Decimal = Decimal('0.00')
    average_lead_time_days: Decimal = Decimal('0.00')
    
    # التقييم النهائي
    overall_score: Decimal = Decimal('0.00')  # من 5
    grade: Optional[str] = None  # A+, A, B+, B, C, D, F
    
    # التوصيات
    is_approved: bool = True
    is_preferred: bool = False
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    
    # التتبع
    evaluated_by: Optional[int] = None
    evaluation_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحويل القيم"""
        decimal_fields = ['quality_score', 'delivery_score', 'pricing_score',
                         'communication_score', 'reliability_score', 'total_value',
                         'on_time_delivery_rate', 'quality_acceptance_rate',
                         'average_lead_time_days', 'overall_score']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        # تحويل التواريخ
        date_fields = ['evaluation_period_start', 'evaluation_period_end', 'evaluation_date']
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
    
    def calculate_overall_score(self):
        """حساب التقييم الإجمالي"""
        # الأوزان
        weights = {
            'quality': Decimal('0.30'),      # 30%
            'delivery': Decimal('0.25'),     # 25%
            'pricing': Decimal('0.20'),      # 20%
            'communication': Decimal('0.15'), # 15%
            'reliability': Decimal('0.10')    # 10%
        }
        
        self.overall_score = (
            self.quality_score * weights['quality'] +
            self.delivery_score * weights['delivery'] +
            self.pricing_score * weights['pricing'] +
            self.communication_score * weights['communication'] +
            self.reliability_score * weights['reliability']
        )
        
        # تحديد الدرجة
        if self.overall_score >= Decimal('4.8'):
            self.grade = 'A+'
        elif self.overall_score >= Decimal('4.5'):
            self.grade = 'A'
        elif self.overall_score >= Decimal('4.0'):
            self.grade = 'B+'
        elif self.overall_score >= Decimal('3.5'):
            self.grade = 'B'
        elif self.overall_score >= Decimal('3.0'):
            self.grade = 'C'
        elif self.overall_score >= Decimal('2.0'):
            self.grade = 'D'
        else:
            self.grade = 'F'
        
        # تحديد الموافقة
        self.is_approved = self.overall_score >= Decimal('3.0')
        self.is_preferred = self.overall_score >= Decimal('4.5')
    
    def calculate_metrics(self):
        """حساب المقاييس"""
        if self.total_orders > 0:
            self.on_time_delivery_rate = (Decimal(self.on_time_deliveries) / Decimal(self.total_orders)) * 100
        
        # يمكن حساب معدلات أخرى من بيانات الطلبات الفعلية
        self.calculate_overall_score()
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'evaluation_period_start': self.evaluation_period_start.isoformat() if self.evaluation_period_start else None,
            'evaluation_period_end': self.evaluation_period_end.isoformat() if self.evaluation_period_end else None,
            'quality_score': float(self.quality_score),
            'delivery_score': float(self.delivery_score),
            'pricing_score': float(self.pricing_score),
            'communication_score': float(self.communication_score),
            'reliability_score': float(self.reliability_score),
            'total_orders': self.total_orders,
            'completed_orders': self.completed_orders,
            'on_time_deliveries': self.on_time_deliveries,
            'late_deliveries': self.late_deliveries,
            'rejected_shipments': self.rejected_shipments,
            'total_value': float(self.total_value),
            'on_time_delivery_rate': float(self.on_time_delivery_rate),
            'quality_acceptance_rate': float(self.quality_acceptance_rate),
            'average_lead_time_days': float(self.average_lead_time_days),
            'overall_score': float(self.overall_score),
            'grade': self.grade,
            'is_approved': self.is_approved,
            'is_preferred': self.is_preferred,
            'notes': self.notes,
            'recommendations': self.recommendations,
            'evaluated_by': self.evaluated_by,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SupplierEvaluation':
        """إنشاء من قاموس"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

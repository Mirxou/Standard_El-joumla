#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نماذج نظام الدفع الجزئي والتقسيط
Payment Installment & Schedule Models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class PaymentPlanStatus(Enum):
    """حالات خطة الدفع"""
    DRAFT = "مسودة"
    ACTIVE = "نشط"
    COMPLETED = "مكتمل"
    CANCELLED = "ملغي"
    DEFAULTED = "متعثر"
    ON_HOLD = "معلق"


class InstallmentStatus(Enum):
    """حالات القسط"""
    PENDING = "معلق"
    PAID = "مدفوع"
    PARTIALLY_PAID = "مدفوع جزئياً"
    OVERDUE = "متأخر"
    CANCELLED = "ملغي"
    WAIVED = "معفي"


class PaymentFrequency(Enum):
    """تكرار الدفع"""
    DAILY = "يومي"
    WEEKLY = "أسبوعي"
    BIWEEKLY = "كل أسبوعين"
    MONTHLY = "شهري"
    QUARTERLY = "ربع سنوي"
    SEMIANNUAL = "نصف سنوي"
    ANNUAL = "سنوي"
    CUSTOM = "مخصص"


class LateFeeType(Enum):
    """نوع غرامة التأخير"""
    NONE = "بدون"
    FIXED = "مبلغ ثابت"
    PERCENTAGE = "نسبة مئوية"
    COMPOUNDING = "نسبة تراكمية"


@dataclass
class PaymentInstallment:
    """قسط من الدفعة"""
    id: Optional[int] = None
    payment_plan_id: Optional[int] = None
    
    # معلومات القسط
    installment_number: int = 1
    due_date: Optional[date] = None
    
    # المبالغ
    principal_amount: Decimal = Decimal('0.00')  # المبلغ الأصلي
    interest_amount: Decimal = Decimal('0.00')   # الفائدة
    late_fee: Decimal = Decimal('0.00')          # غرامة التأخير
    total_amount: Decimal = Decimal('0.00')      # الإجمالي
    
    amount_paid: Decimal = Decimal('0.00')       # المدفوع
    remaining_amount: Decimal = Decimal('0.00')  # المتبقي
    
    # الحالة
    status: InstallmentStatus = InstallmentStatus.PENDING
    
    # الدفع
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    
    # الملاحظات
    notes: Optional[str] = None
    
    # التتبع
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحويل القيم"""
        decimal_fields = ['principal_amount', 'interest_amount', 'late_fee',
                         'total_amount', 'amount_paid', 'remaining_amount']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        if isinstance(self.status, str):
            try:
                self.status = InstallmentStatus[self.status]
            except KeyError:
                for status in InstallmentStatus:
                    if status.value == self.status:
                        self.status = status
                        break
        
        # تحويل التواريخ
        for field_name in ['due_date', 'payment_date']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value).date())
                except:
                    pass
        
        for field_name in ['created_at', 'updated_at']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value))
                except:
                    pass
    
    @property
    def is_paid(self) -> bool:
        """هل تم الدفع؟"""
        return self.status == InstallmentStatus.PAID
    
    @property
    def is_overdue(self) -> bool:
        """هل متأخر؟"""
        if self.status in [InstallmentStatus.PAID, InstallmentStatus.CANCELLED, InstallmentStatus.WAIVED]:
            return False
        if self.due_date and date.today() > self.due_date:
            return True
        return False
    
    @property
    def days_overdue(self) -> int:
        """عدد أيام التأخير"""
        if self.is_overdue and self.due_date:
            return (date.today() - self.due_date).days
        return 0
    
    @property
    def payment_percentage(self) -> Decimal:
        """نسبة الدفع"""
        if self.total_amount > 0:
            return (self.amount_paid / self.total_amount) * 100
        return Decimal('0')
    
    def calculate_late_fee(self, fee_type: LateFeeType, fee_value: Decimal) -> Decimal:
        """حساب غرامة التأخير"""
        if not self.is_overdue:
            return Decimal('0.00')
        
        if fee_type == LateFeeType.NONE:
            return Decimal('0.00')
        elif fee_type == LateFeeType.FIXED:
            return fee_value
        elif fee_type == LateFeeType.PERCENTAGE:
            return self.remaining_amount * (fee_value / 100)
        elif fee_type == LateFeeType.COMPOUNDING:
            # نسبة تراكمية يومية
            days = self.days_overdue
            daily_rate = fee_value / Decimal('365')
            return self.remaining_amount * (daily_rate / 100) * days
        return Decimal('0.00')
    
    def make_payment(self, amount: Decimal, payment_date: Optional[date] = None,
                    payment_method: Optional[str] = None, reference: Optional[str] = None) -> bool:
        """تسجيل دفعة"""
        if amount <= 0:
            return False
        
        # تحديث المبالغ
        self.amount_paid += amount
        self.remaining_amount = self.total_amount - self.amount_paid
        
        # تحديث الحالة
        if self.remaining_amount <= 0:
            self.status = InstallmentStatus.PAID
            self.remaining_amount = Decimal('0.00')
        elif self.amount_paid > 0:
            self.status = InstallmentStatus.PARTIALLY_PAID
        
        # تسجيل معلومات الدفع
        self.payment_date = payment_date or date.today()
        self.payment_method = payment_method
        self.payment_reference = reference
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'payment_plan_id': self.payment_plan_id,
            'installment_number': self.installment_number,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'principal_amount': float(self.principal_amount),
            'interest_amount': float(self.interest_amount),
            'late_fee': float(self.late_fee),
            'total_amount': float(self.total_amount),
            'amount_paid': float(self.amount_paid),
            'remaining_amount': float(self.remaining_amount),
            'status': self.status.name if isinstance(self.status, InstallmentStatus) else self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentInstallment':
        """إنشاء من قاموس"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PaymentPlan:
    """خطة الدفع الجزئي"""
    id: Optional[int] = None
    plan_number: str = ""
    
    # العلاقات
    invoice_id: Optional[int] = None
    invoice_number: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    
    # معلومات الخطة
    plan_name: Optional[str] = None
    description: Optional[str] = None
    
    # التواريخ
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # المبالغ
    total_amount: Decimal = Decimal('0.00')
    down_payment: Decimal = Decimal('0.00')      # الدفعة المقدمة
    financed_amount: Decimal = Decimal('0.00')   # المبلغ المقسط
    
    # شروط التقسيط
    number_of_installments: int = 1
    installment_amount: Decimal = Decimal('0.00')
    frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    
    # الفائدة
    interest_rate: Decimal = Decimal('0.00')     # نسبة الفائدة السنوية
    total_interest: Decimal = Decimal('0.00')    # إجمالي الفائدة
    
    # غرامات التأخير
    late_fee_type: LateFeeType = LateFeeType.NONE
    late_fee_value: Decimal = Decimal('0.00')
    grace_period_days: int = 0                    # فترة السماح
    
    # الحالة
    status: PaymentPlanStatus = PaymentPlanStatus.DRAFT
    
    # الملخص المالي
    total_paid: Decimal = Decimal('0.00')
    total_remaining: Decimal = Decimal('0.00')
    total_late_fees: Decimal = Decimal('0.00')
    
    # الأقساط
    installments: List[PaymentInstallment] = field(default_factory=list)
    
    # الملاحظات
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    
    # التتبع
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحويل القيم"""
        if self.installments is None:
            self.installments = []
        
        decimal_fields = ['total_amount', 'down_payment', 'financed_amount',
                         'installment_amount', 'interest_rate', 'total_interest',
                         'late_fee_value', 'total_paid', 'total_remaining', 'total_late_fees']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
        
        # تحويل الأنواع
        if isinstance(self.status, str):
            try:
                self.status = PaymentPlanStatus[self.status]
            except KeyError:
                for status in PaymentPlanStatus:
                    if status.value == self.status:
                        self.status = status
                        break
        
        if isinstance(self.frequency, str):
            try:
                self.frequency = PaymentFrequency[self.frequency]
            except KeyError:
                for freq in PaymentFrequency:
                    if freq.value == self.frequency:
                        self.frequency = freq
                        break
        
        if isinstance(self.late_fee_type, str):
            try:
                self.late_fee_type = LateFeeType[self.late_fee_type]
            except KeyError:
                for fee_type in LateFeeType:
                    if fee_type.value == self.late_fee_type:
                        self.late_fee_type = fee_type
                        break
        
        # تحويل التواريخ
        for field_name in ['start_date', 'end_date']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value).date())
                except:
                    pass
        
        for field_name in ['created_at', 'updated_at', 'completed_at']:
            value = getattr(self, field_name)
            if isinstance(value, str) and value:
                try:
                    setattr(self, field_name, datetime.fromisoformat(value))
                except:
                    pass
    
    @property
    def is_active(self) -> bool:
        """هل الخطة نشطة؟"""
        return self.status == PaymentPlanStatus.ACTIVE
    
    @property
    def is_completed(self) -> bool:
        """هل الخطة مكتملة؟"""
        return self.status == PaymentPlanStatus.COMPLETED
    
    @property
    def completion_percentage(self) -> Decimal:
        """نسبة الإنجاز"""
        if self.financed_amount > 0:
            return (self.total_paid / self.financed_amount) * 100
        return Decimal('0')
    
    @property
    def overdue_installments_count(self) -> int:
        """عدد الأقساط المتأخرة"""
        return sum(1 for inst in self.installments if inst.is_overdue)
    
    @property
    def next_installment(self) -> Optional[PaymentInstallment]:
        """القسط التالي المستحق"""
        pending = [inst for inst in self.installments 
                  if inst.status == InstallmentStatus.PENDING]
        if pending:
            return min(pending, key=lambda x: x.due_date if x.due_date else date.max)
        return None
    
    def generate_installments(self):
        """توليد الأقساط"""
        self.installments = []
        
        if self.number_of_installments <= 0:
            return
        
        # حساب مبلغ كل قسط
        base_amount = self.financed_amount / self.number_of_installments
        
        # حساب الفائدة لكل قسط (بسيطة)
        interest_per_installment = Decimal('0.00')
        if self.interest_rate > 0:
            total_interest = self.financed_amount * (self.interest_rate / 100)
            interest_per_installment = total_interest / self.number_of_installments
            self.total_interest = total_interest
        
        current_date = self.start_date or date.today()
        
        for i in range(self.number_of_installments):
            # حساب تاريخ الاستحقاق
            due_date = self._calculate_next_due_date(current_date, i)
            
            installment = PaymentInstallment(
                payment_plan_id=self.id,
                installment_number=i + 1,
                due_date=due_date,
                principal_amount=base_amount,
                interest_amount=interest_per_installment,
                total_amount=base_amount + interest_per_installment,
                remaining_amount=base_amount + interest_per_installment,
                status=InstallmentStatus.PENDING,
                created_at=datetime.now()
            )
            
            self.installments.append(installment)
        
        # حساب تاريخ الانتهاء
        if self.installments:
            self.end_date = self.installments[-1].due_date
    
    def _calculate_next_due_date(self, start: date, installment_index: int) -> date:
        """حساب تاريخ الاستحقاق التالي"""
        if self.frequency == PaymentFrequency.DAILY:
            return start + timedelta(days=installment_index + 1)
        elif self.frequency == PaymentFrequency.WEEKLY:
            return start + timedelta(weeks=installment_index + 1)
        elif self.frequency == PaymentFrequency.BIWEEKLY:
            return start + timedelta(weeks=(installment_index + 1) * 2)
        elif self.frequency == PaymentFrequency.MONTHLY:
            # إضافة شهور
            months = installment_index + 1
            year = start.year + (start.month + months - 1) // 12
            month = (start.month + months - 1) % 12 + 1
            day = min(start.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            return date(year, month, day)
        elif self.frequency == PaymentFrequency.QUARTERLY:
            return self._calculate_next_due_date(start, installment_index * 3)
        elif self.frequency == PaymentFrequency.SEMIANNUAL:
            return self._calculate_next_due_date(start, installment_index * 6)
        elif self.frequency == PaymentFrequency.ANNUAL:
            return self._calculate_next_due_date(start, installment_index * 12)
        else:
            return start + timedelta(days=30 * (installment_index + 1))
    
    def update_financial_summary(self):
        """تحديث الملخص المالي"""
        self.total_paid = sum(inst.amount_paid for inst in self.installments)
        self.total_remaining = sum(inst.remaining_amount for inst in self.installments)
        self.total_late_fees = sum(inst.late_fee for inst in self.installments)
        
        # تحديث الحالة
        if self.total_remaining <= 0 and len(self.installments) > 0:
            self.status = PaymentPlanStatus.COMPLETED
            self.completed_at = datetime.now()
    
    def apply_late_fees(self):
        """تطبيق غرامات التأخير"""
        for installment in self.installments:
            if installment.is_overdue:
                # التحقق من فترة السماح
                if installment.days_overdue > self.grace_period_days:
                    late_fee = installment.calculate_late_fee(
                        self.late_fee_type,
                        self.late_fee_value
                    )
                    installment.late_fee = late_fee
                    installment.total_amount = (installment.principal_amount + 
                                               installment.interest_amount + 
                                               installment.late_fee)
                    installment.remaining_amount = installment.total_amount - installment.amount_paid
    
    def activate(self) -> bool:
        """تفعيل الخطة"""
        if self.status == PaymentPlanStatus.DRAFT:
            self.status = PaymentPlanStatus.ACTIVE
            if not self.installments:
                self.generate_installments()
            return True
        return False
    
    def cancel(self) -> bool:
        """إلغاء الخطة"""
        if self.status in [PaymentPlanStatus.DRAFT, PaymentPlanStatus.ACTIVE]:
            self.status = PaymentPlanStatus.CANCELLED
            for inst in self.installments:
                if inst.status == InstallmentStatus.PENDING:
                    inst.status = InstallmentStatus.CANCELLED
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'plan_number': self.plan_number,
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'plan_name': self.plan_name,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'total_amount': float(self.total_amount),
            'down_payment': float(self.down_payment),
            'financed_amount': float(self.financed_amount),
            'number_of_installments': self.number_of_installments,
            'installment_amount': float(self.installment_amount),
            'frequency': self.frequency.name if isinstance(self.frequency, PaymentFrequency) else self.frequency,
            'interest_rate': float(self.interest_rate),
            'total_interest': float(self.total_interest),
            'late_fee_type': self.late_fee_type.name if isinstance(self.late_fee_type, LateFeeType) else self.late_fee_type,
            'late_fee_value': float(self.late_fee_value),
            'grace_period_days': self.grace_period_days,
            'status': self.status.name if isinstance(self.status, PaymentPlanStatus) else self.status,
            'total_paid': float(self.total_paid),
            'total_remaining': float(self.total_remaining),
            'total_late_fees': float(self.total_late_fees),
            'installments': [inst.to_dict() for inst in self.installments],
            'notes': self.notes,
            'terms_conditions': self.terms_conditions,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentPlan':
        """إنشاء من قاموس"""
        installments_data = data.pop('installments', [])
        plan_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        plan = cls(**plan_fields)
        plan.installments = [PaymentInstallment.from_dict(inst) if isinstance(inst, dict) else inst 
                            for inst in installments_data]
        return plan

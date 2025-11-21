#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج القيود اليومية
General Journal Entry Model

يحتوي على معلومات القيود المحاسبية اليومية
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


@dataclass
class JournalLine:
    """فئة تمثل سطر واحد من أسطر القيد"""
    
    id: Optional[int] = None
    journal_id: Optional[int] = None  # معرّف القيد الأب
    
    # معلومات الحساب
    account_id: int = 0
    account_code: str = ""
    account_name: str = ""
    
    # المبالغ
    debit_amount: Decimal = field(default_factory=lambda: Decimal("0.00"))
    credit_amount: Decimal = field(default_factory=lambda: Decimal("0.00"))
    
    # الوصف
    description: str = ""
    
    # الطوابع الزمنية
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحقق من صحة البيانات"""
        # يجب أن يكون هناك مبلغ واحد فقط (إما مدين أو دائن)
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValueError("لا يمكن تحديد مبلغ مدين ودائن في نفس الوقت")
        
        if self.debit_amount <= 0 and self.credit_amount <= 0:
            raise ValueError("يجب تحديد مبلغ مدين أو دائن")
    
    def is_debit(self) -> bool:
        """هل هذا السطر مدين؟"""
        return self.debit_amount > 0
    
    def is_credit(self) -> bool:
        """هل هذا السطر دائن؟"""
        return self.credit_amount > 0
    
    def get_amount(self) -> Decimal:
        """احصل على المبلغ (سواء مدين أو دائن)"""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount
    
    def get_side(self) -> str:
        """احصل على الجانب (Debit/Credit)"""
        return "DEBIT" if self.is_debit() else "CREDIT"


@dataclass
class JournalEntry:
    """فئة تمثل قيد يومي واحد"""
    
    # المعرف والمعلومات الأساسية
    id: Optional[int] = None
    entry_number: str = ""  # رقم القيد (مثل JE-001-2025-11)
    entry_date: datetime = field(default_factory=datetime.now)  # تاريخ القيد
    
    # المرجعية والتصنيف
    reference_type: str = ""  # نوع المرجع: Sales, Purchase, Payment, Manual
    reference_id: Optional[int] = None  # معرّف المرجع (بيع أو شراء)
    
    # الوصف والملاحظات
    description: str = ""
    notes: str = ""
    
    # الحالة
    is_posted: bool = False  # هل تم ترحيل القيد؟
    posted_date: Optional[datetime] = None  # تاريخ الترحيل
    posted_by: Optional[str] = None  # من قام بالترحيل
    
    # الأسطر
    lines: List[JournalLine] = field(default_factory=list)
    
    # الطوابع الزمنية
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحقق من صحة البيانات"""
        if not self.entry_date:
            self.entry_date = datetime.now()
    
    def add_line(self, line: JournalLine) -> None:
        """أضف سطرًا إلى القيد"""
        line.journal_id = self.id
        self.lines.append(line)
    
    def get_total_debits(self) -> Decimal:
        """احصل على إجمالي المبالغ المدينة"""
        return sum(line.debit_amount for line in self.lines)
    
    def get_total_credits(self) -> Decimal:
        """احصل على إجمالي المبالغ الدائنة"""
        return sum(line.credit_amount for line in self.lines)
    
    def is_balanced(self) -> bool:
        """هل القيد متوازن (مدين = دائن)؟"""
        debits = self.get_total_debits()
        credits = self.get_total_credits()
        # السماح بفرق صغير جداً بسبب التقريب
        return abs(debits - credits) < Decimal("0.01")
    
    def get_balance_difference(self) -> Decimal:
        """احصل على الفرق بين المدين والدائن"""
        return self.get_total_debits() - self.get_total_credits()
    
    def can_post(self) -> bool:
        """هل يمكن ترحيل هذا القيد؟"""
        if self.is_posted:
            return False
        if not self.lines or len(self.lines) < 2:
            return False
        if not self.is_balanced():
            return False
        return True
    
    def post(self, posted_by: str) -> bool:
        """ترحيل القيد"""
        if not self.can_post():
            return False
        
        self.is_posted = True
        self.posted_date = datetime.now()
        self.posted_by = posted_by
        return True
    
    def unpost(self) -> bool:
        """إلغاء ترحيل القيد"""
        if not self.is_posted:
            return False
        
        self.is_posted = False
        self.posted_date = None
        self.posted_by = None
        return True
    
    def get_line_count(self) -> int:
        """احصل على عدد الأسطر"""
        return len(self.lines)
    
    def get_summary(self) -> dict:
        """احصل على ملخص القيد"""
        return {
            "entry_number": self.entry_number,
            "entry_date": self.entry_date.strftime("%Y-%m-%d") if self.entry_date else "",
            "description": self.description,
            "total_debits": float(self.get_total_debits()),
            "total_credits": float(self.get_total_credits()),
            "is_balanced": self.is_balanced(),
            "is_posted": self.is_posted,
            "line_count": self.get_line_count()
        }

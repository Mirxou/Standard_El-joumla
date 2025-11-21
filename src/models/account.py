#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج دليل الحسابات
Chart of Accounts Model

يحتوي على معلومات الحسابات المحاسبية
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Account:
    """فئة تمثل حساب محاسبي واحد"""
    
    # المعرف والمعلومات الأساسية
    id: Optional[int] = None
    account_code: str = ""  # الرمز (مثل 1001 للأصول)
    account_name: str = ""  # اسم الحساب (مثل "النقد بالصندوق")
    account_type: str = ""  # نوع الحساب: Asset, Liability, Equity, Revenue, Expense
    sub_type: str = ""  # النوع الفرعي (مثل Current Asset, Fixed Asset)
    description: str = ""  # وصف الحساب
    
    # الخصائص المحاسبية
    normal_side: str = "DEBIT"  # الجانب الطبيعي: DEBIT أو CREDIT
    is_header: bool = False  # هل هو حساب رئيسي فقط (بدون حركات مباشرة)
    parent_account_id: Optional[int] = None  # الحساب الأب إن وجد
    
    # الحالة
    is_active: bool = True  # هل الحساب نشط
    is_locked: bool = False  # هل الحساب مقفل (لا يمكن تعديله)
    
    # البيانات المالية
    opening_balance: Decimal = field(default_factory=lambda: Decimal("0.00"))  # الرصيد الافتتاحي
    current_balance: Decimal = field(default_factory=lambda: Decimal("0.00"))  # الرصيد الحالي
    
    # الطوابع الزمنية
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحقق من صحة البيانات"""
        if not self.account_code:
            raise ValueError("يجب تحديد رمز الحساب")
        if not self.account_name:
            raise ValueError("يجب تحديد اسم الحساب")
        if self.account_type not in ["Asset", "Liability", "Equity", "Revenue", "Expense"]:
            raise ValueError(f"نوع حساب غير صحيح: {self.account_type}")
    
    def get_display_code(self) -> str:
        """احصل على رمز الحساب المنسق"""
        return f"{self.account_code} - {self.account_name}"
    
    def is_debit_account(self) -> bool:
        """هل هو حساب دائن؟"""
        return self.normal_side == "DEBIT"
    
    def is_credit_account(self) -> bool:
        """هل هو حساب دائن؟"""
        return self.normal_side == "CREDIT"
    
    def is_asset_account(self) -> bool:
        """هل هو حساب أصول؟"""
        return self.account_type == "Asset"
    
    def is_liability_account(self) -> bool:
        """هل هو حساب التزامات؟"""
        return self.account_type == "Liability"
    
    def is_equity_account(self) -> bool:
        """هل هو حساب حقوق الملكية؟"""
        return self.account_type == "Equity"
    
    def is_revenue_account(self) -> bool:
        """هل هو حساب إيرادات؟"""
        return self.account_type == "Revenue"
    
    def is_expense_account(self) -> bool:
        """هل هو حساب مصروفات؟"""
        return self.account_type == "Expense"
    
    def get_account_hierarchy(self) -> str:
        """احصل على تصنيف الحساب الهرمي"""
        types_map = {
            "Asset": "الأصول",
            "Liability": "الالتزامات",
            "Equity": "حقوق الملكية",
            "Revenue": "الإيرادات",
            "Expense": "المصروفات"
        }
        return types_map.get(self.account_type, "غير محدد")


@dataclass
class ChartOfAccounts:
    """فئة تمثل دليل الحسابات الكامل"""
    
    accounts: dict = field(default_factory=dict)  # معرّف -> حساب
    code_index: dict = field(default_factory=dict)  # رمز -> حساب
    
    def add_account(self, account: Account) -> None:
        """أضف حسابًا إلى الدليل"""
        if account.id:
            self.accounts[account.id] = account
        if account.account_code:
            self.code_index[account.account_code] = account
    
    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """احصل على حساب بواسطة المعرف"""
        return self.accounts.get(account_id)
    
    def get_account_by_code(self, code: str) -> Optional[Account]:
        """احصل على حساب بواسطة الرمز"""
        return self.code_index.get(code)
    
    def get_accounts_by_type(self, account_type: str) -> list:
        """احصل على جميع الحسابات من نوع معين"""
        return [acc for acc in self.accounts.values() if acc.account_type == account_type]
    
    def get_active_accounts(self) -> list:
        """احصل على جميع الحسابات النشطة"""
        return [acc for acc in self.accounts.values() if acc.is_active and not acc.is_header]
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            "accounts": {str(k): v.__dict__ for k, v in self.accounts.items()},
            "code_index": {k: v.__dict__ for k, v in self.code_index.items()}
        }

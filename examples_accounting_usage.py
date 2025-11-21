#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مثال عملي على استخدام نظام المحاسبة
Practical Example - Using the Accounting System

يوضح هذا المثال كيفية:
1. إنشاء حسابات جديدة
2. إنشاء قيود يومية
3. الاستعلام عن الأرصدة
4. طباعة التقارير المالية
"""

from src.core.database_manager import DatabaseManager
from src.services.accounting_service import AccountingService
from src.models.account import Account
from src.models.journal_entry import JournalEntry, JournalLine
from decimal import Decimal
from datetime import datetime


def example_create_accounts():
    """مثال: إنشاء حسابات إضافية"""
    print("\n" + "="*50)
    print("مثال 1: إنشاء حسابات إضافية")
    print("="*50)
    
    db = DatabaseManager()
    db.initialize()
    accounting = AccountingService(db)
    
    # إنشاء حسابات جديدة
    new_accounts = [
        Account(
            account_code="1003",
            account_name="الحسابات البنكية - البنك الأهلي",
            account_type="Asset",
            sub_type="Current Asset",
            normal_side="DEBIT",
            description="حساب جاري لدى البنك الأهلي",
            opening_balance=Decimal("50000.00")
        ),
        Account(
            account_code="5040",
            account_name="تكاليف المبيعات الإضافية",
            account_type="Expense",
            normal_side="DEBIT",
            description="تكاليف إضافية متعلقة بالمبيعات"
        ),
    ]
    
    for account in new_accounts:
        account_id = accounting.create_account(account)
        if account_id > 0:
            print(f"✓ تم إنشاء: {account.account_code} - {account.account_name} (ID: {account_id})")
    
    db.close()


def example_create_sales_entry():
    """مثال: إنشاء قيد لعملية بيع"""
    print("\n" + "="*50)
    print("مثال 2: إنشاء قيد يومي لعملية بيع")
    print("="*50)
    
    db = DatabaseManager()
    db.initialize()
    accounting = AccountingService(db)
    
    # إنشاء قيد لعملية بيع بمبلغ 10,000 دج
    # مدين: حسابات العملاء (1010)
    # دائن: إيرادات المبيعات (4001)
    
    entry = JournalEntry(
        entry_date=datetime.now(),
        description="بيع بضائع للعميل أحمد محمد",
        reference_type="Sales",
        reference_id=1  # معرّف الفاتورة
    )
    
    # سطر مدين: حسابات العملاء
    entry.add_line(JournalLine(
        account_id=3,  # حسابات العملاء (1010)
        account_code="1010",
        account_name="حسابات العملاء",
        debit_amount=Decimal("10000.00"),
        credit_amount=Decimal("0.00"),
        description="فاتورة رقم 001"
    ))
    
    # سطر دائن: إيرادات المبيعات
    entry.add_line(JournalLine(
        account_id=10,  # إيرادات المبيعات (4001)
        account_code="4001",
        account_name="إيرادات المبيعات",
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("10000.00"),
        description="إيراد من عملية بيع"
    ))
    
    # التحقق من التوازن
    if entry.is_balanced():
        print(f"✓ القيد متوازن:")
        print(f"  المدين: {entry.get_total_debits()}")
        print(f"  الدائن: {entry.get_total_credits()}")
    
    # إنشاء القيد
    entry_id = accounting.create_journal_entry(entry)
    if entry_id > 0:
        print(f"✓ تم إنشاء القيد (ID: {entry_id})")
        
        # ترحيل القيد
        if accounting.post_journal_entry(entry_id, "system"):
            print(f"✓ تم ترحيل القيد بنجاح")
    
    db.close()


def example_create_purchase_entry():
    """مثال: إنشاء قيد لعملية شراء"""
    print("\n" + "="*50)
    print("مثال 3: إنشاء قيد يومي لعملية شراء")
    print("="*50)
    
    db = DatabaseManager()
    db.initialize()
    accounting = AccountingService(db)
    
    # إنشاء قيد لعملية شراء بمبلغ 5,000 دج
    # مدين: المخزون (1020)
    # دائن: حسابات الموردين (2001)
    
    entry = JournalEntry(
        entry_date=datetime.now(),
        description="شراء بضائع من المورد محمد الأحمد",
        reference_type="Purchase",
        reference_id=1  # معرّف أمر الشراء
    )
    
    # سطر مدين: المخزون
    entry.add_line(JournalLine(
        account_id=4,  # المخزون (1020)
        account_code="1020",
        account_name="المخزون",
        debit_amount=Decimal("5000.00"),
        credit_amount=Decimal("0.00"),
        description="شراء بضائع"
    ))
    
    # سطر دائن: حسابات الموردين
    entry.add_line(JournalLine(
        account_id=6,  # حسابات الموردين (2001)
        account_code="2001",
        account_name="حسابات الموردين",
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("5000.00"),
        description="دين على المورد"
    ))
    
    # التحقق من التوازن
    if entry.is_balanced():
        print(f"✓ القيد متوازن:")
        print(f"  المدين: {entry.get_total_debits()}")
        print(f"  الدائن: {entry.get_total_credits()}")
    
    # إنشاء وترحيل القيد
    entry_id = accounting.create_journal_entry(entry)
    if entry_id > 0:
        if accounting.post_journal_entry(entry_id, "system"):
            print(f"✓ تم ترحيل قيد الشراء بنجاح")
    
    db.close()


def example_view_trial_balance():
    """مثال: عرض ميزان المراجعة"""
    print("\n" + "="*50)
    print("مثال 4: عرض ميزان المراجعة")
    print("="*50)
    
    db = DatabaseManager()
    db.initialize()
    accounting = AccountingService(db)
    
    trial_balance = accounting.get_trial_balance()
    
    if "error" not in trial_balance:
        print(f"\nميزان المراجعة - {trial_balance['date']}")
        print("-" * 60)
        print(f"{'الحساب':<40} {'مدين':>10} {'دائن':>10}")
        print("-" * 60)
        
        for account in trial_balance["accounts"]:
            debit = account["debit"]
            credit = account["credit"]
            if debit > 0 or credit > 0:
                print(f"{account['account_name']:<40} {debit:>10.2f} {credit:>10.2f}")
        
        print("-" * 60)
        print(f"{'الإجمالي':<40} {trial_balance['total_debits']:>10.2f} {trial_balance['total_credits']:>10.2f}")
        print("-" * 60)
        
        if trial_balance["is_balanced"]:
            print("✓ ميزان المراجعة متوازن")
        else:
            print("✗ ميزان المراجعة غير متوازن - هناك خطأ!")
    
    db.close()


def example_view_financial_position():
    """مثال: عرض الحالة المالية"""
    print("\n" + "="*50)
    print("مثال 5: عرض الحالة المالية (الميزانية العمومية)")
    print("="*50)
    
    db = DatabaseManager()
    db.initialize()
    accounting = AccountingService(db)
    
    position = accounting.get_financial_position()
    
    if "error" not in position:
        print(f"\nالميزانية العمومية - {position['date']}")
        print("-" * 40)
        print(f"الأصول:        {position['assets']:>20,.2f}")
        print(f"الالتزامات:    {position['liabilities']:>20,.2f}")
        print(f"حقوق الملكية:  {position['equity']:>20,.2f}")
        print("-" * 40)
        
        if position["is_balanced"]:
            print("✓ الميزانية متوازنة (أصول = التزامات + حقوق ملكية)")
        else:
            diff = position['assets'] - (position['liabilities'] + position['equity'])
            print(f"✗ الميزانية غير متوازنة - الفرق: {diff:,.2f}")
    
    db.close()


def example_view_income_statement():
    """مثال: عرض قائمة الدخل"""
    print("\n" + "="*50)
    print("مثال 6: عرض قائمة الدخل")
    print("="*50)
    
    db = DatabaseManager()
    db.initialize()
    accounting = AccountingService(db)
    
    from datetime import datetime, timedelta
    
    # احسب قائمة الدخل للشهر الحالي
    today = datetime.now()
    start_date = datetime(today.year, today.month, 1)
    end_date = datetime(today.year, today.month, 28) if today.month != 12 else datetime(today.year + 1, 1, 1)
    
    income = accounting.get_income_statement(start_date, end_date)
    
    if "error" not in income:
        print(f"\nقائمة الدخل - من {income['start_date']} إلى {income['end_date']}")
        print("-" * 40)
        print(f"إجمالي الإيرادات:  {income['total_revenues']:>15,.2f}")
        print(f"إجمالي المصروفات: {income['total_expenses']:>15,.2f}")
        print("-" * 40)
        print(f"صافي الدخل:       {income['net_income']:>15,.2f}")
        print("-" * 40)
        
        if income['net_income'] > 0:
            print("✓ الشركة حققت أرباح في هذه الفترة")
        elif income['net_income'] < 0:
            print("✗ الشركة تكبدت خسائر في هذه الفترة")
        else:
            print("⚪ الشركة لم تحقق أرباح ولا خسائر")
    
    db.close()


def main():
    """تشغيل جميع الأمثلة"""
    print("\n" + "="*60)
    print("أمثلة عملية - نظام المحاسبة")
    print("="*60)
    
    try:
        # الأمثلة قد تؤدي إلى أخطاء إذا كانت البيانات موجودة مسبقًا
        # لذا نستخدم try/except للتعامل مع الأخطاء
        
        example_create_accounts()
        example_create_sales_entry()
        example_create_purchase_entry()
        example_view_trial_balance()
        example_view_financial_position()
        example_view_income_statement()
        
        print("\n" + "="*60)
        print("✓ اكتملت جميع الأمثلة بنجاح!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nخطأ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

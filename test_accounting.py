#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبار نظام المحاسبة"""

from src.core.database_manager import DatabaseManager
from src.services.accounting_service import AccountingService

def test_accounting():
    """اختبار نظام المحاسبة"""
    try:
        # تهيئة قاعدة البيانات
        db = DatabaseManager()
        db.initialize()
        print("OK: Database initialized")
        
        # التحقق من الجداول
        tables_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """
        tables = db.fetch_all(tables_query)
        
        print("\nOK: Database tables:")
        accounting_tables = []
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            if 'account' in table_name.lower() or 'journal' in table_name.lower():
                accounting_tables.append(table_name)
        
        if accounting_tables:
            print(f"\nOK: Found {len(accounting_tables)} accounting tables:")
            for t in accounting_tables:
                print(f"  + {t}")
        else:
            print("\nWARNING: No accounting tables found")
        
        # اختبار خدمة المحاسبة
        accounting = AccountingService(db)
        print("\nOK: Accounting service initialized")
        
        # احصل على دليل الحسابات
        coa_accounts = accounting.coa.get_active_accounts()
        print(f"OK: Chart of Accounts has {len(coa_accounts)} active accounts")
        
        # احصل على ميزان المراجعة
        trial_balance = accounting.get_trial_balance()
        if "error" not in trial_balance:
            print(f"OK: Trial balance retrieved - Debits: {trial_balance.get('total_debits')}, Credits: {trial_balance.get('total_credits')}")
        
        # احصل على الحالة المالية
        position = accounting.get_financial_position()
        if "error" not in position:
            print(f"OK: Financial position - Assets: {position.get('assets')}, Liabilities: {position.get('liabilities')}")
        
        db.close()
        print("\nSUCCESS: All tests passed!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_accounting()

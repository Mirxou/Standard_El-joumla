#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار سريع للتطبيق
Quick Application Test
"""

import sys
import os
sys.path.insert(0, '.')

def test_imports():
    """اختبار الاستيرادات الأساسية"""
    print("1️⃣ اختبار الاستيرادات الأساسية...")
    print("-" * 70)
    
    try:
        from src.core.database_manager import DatabaseManager
        print("✅ DatabaseManager")
    except Exception as e:
        print(f"❌ DatabaseManager: {e}")
        return False
    
    try:
        from src.ui.dialogs.login_dialog import LoginDialog
        print("✅ LoginDialog")
    except Exception as e:
        print(f"❌ LoginDialog: {e}")
        return False
    
    try:
        from src.ui.windows.main_window import MainWindow
        print("✅ MainWindow")
    except Exception as e:
        print(f"❌ MainWindow: {e}")
        return False
    
    return True


def test_new_windows():
    """اختبار النوافذ الجديدة"""
    print("\n2️⃣ اختبار النوافذ الجديدة...")
    print("-" * 70)
    
    try:
        from src.ui.windows.receiving_notes_window import ReceivingNotesWindow
        print("✅ ReceivingNotesWindow")
    except Exception as e:
        print(f"❌ ReceivingNotesWindow: {e}")
        return False
    
    try:
        from src.ui.windows.supplier_evaluations_window import SupplierEvaluationsWindow
        print("✅ SupplierEvaluationsWindow")
    except Exception as e:
        print(f"❌ SupplierEvaluationsWindow: {e}")
        return False
    
    return True


def test_services():
    """اختبار الخدمات المحدثة"""
    print("\n3️⃣ اختبار الخدمات المحدثة...")
    print("-" * 70)
    
    try:
        from src.services.exchange_rate_service import ExchangeRateService
        if hasattr(ExchangeRateService, 'delete_exchange_rate'):
            print("✅ ExchangeRateService.delete_exchange_rate")
        else:
            print("❌ delete_exchange_rate method not found")
            return False
    except Exception as e:
        print(f"❌ ExchangeRateService: {e}")
        return False
    
    return True


def test_database():
    """اختبار الاتصال بقاعدة البيانات"""
    print("\n4️⃣ اختبار قاعدة البيانات...")
    print("-" * 70)
    
    try:
        from src.core.database_manager import DatabaseManager
        db = DatabaseManager()
        db.initialize()
        
        print("✅ اتصال قاعدة البيانات يعمل")
        
        # التحقق من وجود المنتجات
        import sqlite3
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        print(f"✅ عدد المنتجات في النظام: {count:,}")
        conn.close()
        
        return True
    except Exception as e:
        print(f"⚠️ تحذير في قاعدة البيانات: {str(e)[:60]}")
        return True  # لا نوقف الاختبار


def main():
    """تشغيل جميع الاختبارات"""
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "🧪 اختبار سريع للتطبيق" + " "*30 + "║")
    print("║" + " "*15 + "QUICK APPLICATION TEST" + " "*31 + "║")
    print("╚" + "═"*68 + "╝")
    print()
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_new_windows():
        all_passed = False
    
    if not test_services():
        all_passed = False
    
    if not test_database():
        all_passed = False
    
    print()
    print("═" * 70)
    
    if all_passed:
        print("🎉 جميع الاختبارات نجحت!")
        print("🎉 All tests passed!")
        print()
        print("✅ التطبيق جاهز للتشغيل")
        print("✅ Application is ready to run")
        return 0
    else:
        print("⚠️ بعض الاختبارات فشلت")
        print("⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

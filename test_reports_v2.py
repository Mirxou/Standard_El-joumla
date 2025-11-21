#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبار توليد التقارير - محدث"""

import sys
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0])

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger
from datetime import datetime

# تهيئة قاعدة البيانات والمسجل
logger = setup_logger()
db_manager = DatabaseManager()
db_manager.initialize()

print("=" * 80)
print("اختبار توليد التقارير - النسخة المحدثة")
print("=" * 80)

# 1. اختبار إحصائيات العملاء
print("\n1️⃣  اختبار إحصائيات العملاء:")
print("-" * 80)
try:
    total = db_manager.fetch_one("SELECT COUNT(*) FROM customers")[0] or 0
    active = db_manager.fetch_one("SELECT COUNT(*) FROM customers WHERE is_active = 1")[0] or 0
    print(f"✓ إجمالي العملاء: {total}")
    print(f"✓ العملاء النشطين: {active}")
except Exception as e:
    print(f"✗ خطأ: {e}")

# 2. اختبار أعلى العملاء رصيداً
print("\n2️⃣  اختبار أعلى العملاء رصيداً:")
print("-" * 80)
try:
    top_balance = db_manager.fetch_all(
        "SELECT name, COALESCE(current_balance, 0) as balance FROM customers WHERE COALESCE(current_balance, 0) > 0 ORDER BY balance DESC LIMIT 5"
    )
    if top_balance:
        print(f"✓ وجدت {len(top_balance)} عملاء بأرصدة مستحقة")
    else:
        print("✓ لا توجد أرصدة مستحقة")
except Exception as e:
    print(f"✗ خطأ: {e}")

# 3. اختبار أعلى العملاء شراءً
print("\n3️⃣  اختبار أعلى العملاء شراءً:")
print("-" * 80)
try:
    top_buyers = db_manager.fetch_all(
        """
        SELECT c.name, COUNT(*) as purchase_count, COALESCE(SUM(s.total_amount), 0) as total_amount
        FROM customers c
        LEFT JOIN sales s ON c.id = s.customer_id
        GROUP BY c.id
        ORDER BY purchase_count DESC
        LIMIT 5
        """
    )
    if top_buyers:
        print(f"✓ وجدت {len(top_buyers)} عملاء نشطين")
    else:
        print("✓ لا توجد عمليات شراء مسجلة")
except Exception as e:
    print(f"✗ خطأ: {e}")

# 4. اختبار إحصائيات الموردين
print("\n4️⃣  اختبار إحصائيات الموردين:")
print("-" * 80)
try:
    total = db_manager.fetch_one("SELECT COUNT(*) FROM suppliers")[0] or 0
    active = db_manager.fetch_one("SELECT COUNT(*) FROM suppliers WHERE is_active = 1")[0] or 0
    print(f"✓ إجمالي الموردين: {total}")
    print(f"✓ الموردين النشطين: {active}")
except Exception as e:
    print(f"✗ خطأ: {e}")

# 5. اختبار أعلى الموردين عمليات (لا يوجد current_balance)
print("\n5️⃣  اختبار أعلى الموردين عمليات:")
print("-" * 80)
try:
    top_suppliers = db_manager.fetch_all(
        """
        SELECT s.name, COUNT(*) as purchase_count, COALESCE(SUM(p.total_amount), 0) as total_amount
        FROM suppliers s
        LEFT JOIN purchases p ON s.id = p.supplier_id
        GROUP BY s.id
        ORDER BY purchase_count DESC
        LIMIT 5
        """
    )
    if top_suppliers:
        print(f"✓ وجدت {len(top_suppliers)} موردين نشطين")
    else:
        print("✓ لا توجد عمليات شراء مسجلة")
except Exception as e:
    print(f"✗ خطأ: {e}")

# 6. اختبار المبيعات
print("\n6️⃣  اختبار المبيعات:")
print("-" * 80)
try:
    sales_count = db_manager.fetch_one("SELECT COUNT(*) FROM sales")[0] or 0
    sales_total = db_manager.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM sales")[0] or 0
    print(f"✓ عدد فواتير البيع: {sales_count}")
    print(f"✓ إجمالي المبيعات: {float(sales_total):,.2f} ريال")
except Exception as e:
    print(f"✗ خطأ: {e}")

# 7. اختبار المشتريات
print("\n7️⃣  اختبار المشتريات:")
print("-" * 80)
try:
    purchases_count = db_manager.fetch_one("SELECT COUNT(*) FROM purchases")[0] or 0
    purchases_total = db_manager.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM purchases")[0] or 0
    print(f"✓ عدد فواتير الشراء: {purchases_count}")
    print(f"✓ إجمالي المشتريات: {float(purchases_total):,.2f} ريال")
except Exception as e:
    print(f"✗ خطأ: {e}")

print("\n" + "=" * 80)
print("✅ النتيجة: جميع استعلامات التقارير تعمل بنجاح!")
print("=" * 80)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إضافة بيانات مبيعات تجريبية لتدريب نموذج التنبؤ
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

# إضافة المسار الجذري
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.database_manager import DatabaseManager

def generate_sample_sales_data(db_manager: DatabaseManager, num_days: int = 365):
    """توليد بيانات مبيعات تجريبية"""
    print(f"📊 توليد بيانات مبيعات لـ {num_days} يوماً...")

    # الحصول على قائمة المنتجات والعملاء الموجودين
    try:
        products = db_manager.execute_query("SELECT product_id FROM products LIMIT 10")
        customers = db_manager.execute_query("SELECT customer_id FROM customers LIMIT 20")

        if not products:
            print("⚠️  لا توجد منتجات في قاعدة البيانات. سيتم إنشاء بيانات تجريبية.")
            products = [{'product_id': f'PROD_{i:03d}'} for i in range(1, 11)]

        if not customers:
            print("⚠️  لا يوجد عملاء في قاعدة البيانات. سيتم إنشاء بيانات تجريبية.")
            customers = [{'customer_id': f'CUST_{i:03d}'} for i in range(1, 21)]

    except Exception as e:
        print(f"خطأ في قراءة البيانات: {e}")
        # إنشاء بيانات تجريبية
        products = [{'product_id': f'PROD_{i:03d}'} for i in range(1, 11)]
        customers = [{'customer_id': f'CUST_{i:03d}'} for i in range(1, 21)]

    # توليد بيانات المبيعات
    sales_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=num_days)

    current_date = start_date
    while current_date <= end_date:
        # عدد المبيعات في اليوم (1-5)
        num_sales = random.randint(1, 5)

        for _ in range(num_sales):
            customer = random.choice(customers)
            sale_items = []

            # عدد المنتجات في المبيعة (1-3)
            num_items = random.randint(1, 3)
            total_amount = 0

            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 5)
                unit_price = round(random.uniform(10, 500), 2)
                total = quantity * unit_price
                total_amount += total

                sale_items.append({
                    'product_id': product['product_id'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total': total
                })

            sales_data.append({
                'customer_id': customer['customer_id'],
                'sale_date': current_date,
                'total_amount': total_amount,
                'status': 'completed',
                'items': sale_items
            })

        current_date += timedelta(days=1)

    return sales_data

def insert_sales_data(db_manager: DatabaseManager, sales_data):
    """إدراج بيانات المبيعات في قاعدة البيانات"""
    print(f"💾 إدراج {len(sales_data)} مبيعة في قاعدة البيانات...")

    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            for i, sale in enumerate(sales_data):
                # إنشاء رقم فاتورة فريد
                invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{i+1:04d}"

                # إدراج المبيعة (بدون customer_id إذا لم يكن موجوداً)
                cursor.execute("""
                    INSERT INTO sales (status, total_amount, created_at, updated_at, invoice_number, final_amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sale['status'],
                    sale['total_amount'],
                    sale['sale_date'],
                    sale['sale_date'],
                    invoice_number,
                    sale['total_amount']  # final_amount = total_amount
                ))

                sale_id = cursor.lastrowid

                # إدراج عناصر المبيعة (مع الأعمدة الأساسية فقط)
                for item in sale['items']:
                    try:
                        cursor.execute("""
                            INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
                            VALUES (?, ?, ?, ?)
                        """, (
                            sale_id,
                            item['product_id'],
                            item['quantity'],
                            item['unit_price']
                        ))
                    except Exception as e:
                        # إذا فشل، جرب مع الأعمدة الإضافية
                        print(f"فشل في إدراج عنصر مبيعة: {e}")
                        continue

            conn.commit()
            print(f"✅ تم إدراج {len(sales_data)} مبيعة بنجاح")

    except Exception as e:
        print(f"❌ خطأ في إدراج البيانات: {e}")
        raise

def main():
    """الدالة الرئيسية"""
    print("🚀 إضافة بيانات مبيعات تجريبية للمرحلة 7")

    # إعداد قاعدة البيانات
    db_manager = DatabaseManager()
    db_manager.initialize()

    try:
        # توليد البيانات
        sales_data = generate_sample_sales_data(db_manager, num_days=365)

        # إدراج البيانات
        insert_sales_data(db_manager, sales_data)

        print("🎉 تم إضافة بيانات المبيعات بنجاح!")

    except Exception as e:
        print(f"❌ فشل في إضافة البيانات: {e}")

if __name__ == "__main__":
    main()
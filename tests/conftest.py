"""
Pytest Configuration and Shared Fixtures
إعدادات pytest والـ fixtures المشتركة
"""

import pytest
import sys
import os
from pathlib import Path
from typing import Generator
import tempfile
import shutil

# إضافة مسار المشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture(scope="session")
def project_path():
    """مسار المشروع"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def temp_db_path():
    """مسار قاعدة بيانات مؤقتة للاختبارات"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    yield db_path
    # تنظيف بعد الاختبارات
    # 🔥 CRITICAL FIX: انتظار قليل قبل الحذف للتأكد من إغلاق جميع الاتصالات
    import time
    time.sleep(0.1)  # انتظار 100ms
    
    # محاولة حذف الملفات بشكل آمن
    try:
        if os.path.exists(db_path):
            # محاولة إزالة الملف مباشرة
            try:
                os.remove(db_path)
            except PermissionError:
                # إذا فشل، انتظر قليلاً ثم حاول مرة أخرى
                time.sleep(0.2)
                try:
                    os.remove(db_path)
                except Exception:
                    pass  # تجاهل الخطأ - سيتم حذف المجلد لاحقاً
        
        # حذف المجلد المؤقت
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                # إذا فشل، تجاهل - سيتم تنظيفه لاحقاً من النظام
                pass
    except Exception:
        pass  # تجاهل أي أخطاء في التنظيف


@pytest.fixture(scope="function")
def db_manager(temp_db_path):
    """مدير قاعدة بيانات للاختبارات"""
    from src.core.database_manager import DatabaseManager
    from datetime import datetime
    
    db = DatabaseManager(db_path=temp_db_path)
    db.initialize()
    
    # 🔥 CRITICAL FIX: إنشاء فئة وهمية قبل الاختبارات
    # هذا يحل مشكلة FOREIGN KEY constraint failed
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        # إنشاء فئة افتراضية للاختبارات
        cursor.execute("""
            INSERT OR IGNORE INTO categories (id, name, description, is_active, created_at, updated_at)
            VALUES (1, 'عام', 'فئة عامة للاختبارات', 1, ?, ?)
        """, (datetime.now(), datetime.now()))
        conn.commit()
        cursor.close()
    except Exception as e:
        # إذا فشل، لا مشكلة - قد تكون الفئة موجودة بالفعل
        pass
    
    yield db
    
    # إغلاق جميع الاتصالات بشكل صحيح
    try:
        db.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def sample_product_data():
    """بيانات منتج نموذجية للاختبارات"""
    return {
        "name": "منتج اختبار",
        "name_en": "Test Product",
        "barcode": "1234567890123",
        "category_id": 1,
        "unit": "قطعة",
        "cost_price": 100.0,
        "selling_price": 150.0,
        "min_stock": 10,
        "current_stock": 50,
        "description": "منتج للاختبار",
        "is_active": True
    }


@pytest.fixture(scope="function")
def sample_customer_data():
    """بيانات عميل نموذجية للاختبارات"""
    return {
        "name": "عميل اختبار",
        "email": "test@example.com",
        "phone": "0123456789",
        "address": "عنوان اختبار",
        "is_active": True
    }


@pytest.fixture(scope="function")
def sample_sale_data():
    """بيانات فاتورة مبيعات نموذجية للاختبارات"""
    return {
        "customer_id": 1,
        "invoice_number": "INV-001",
        "subtotal": 1000.0,
        "discount_amount": 50.0,
        "tax_amount": 142.5,
        "total_amount": 1092.5,
        "payment_method": "cash",
        "status": "confirmed"
    }


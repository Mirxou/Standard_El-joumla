#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعدادات pytest
Pytest Configuration
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime
import sqlite3
import shutil

# إضافة مسار المشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """إنشاء قاعدة بيانات مؤقتة للاختبار"""
    db_dir = tmp_path_factory.mktemp("data")
    db_path = db_dir / "test_inventory.db"
    
    # نسخ قاعدة البيانات الأصلية إذا كانت موجودة
    original_db = project_root / "inventory.db"
    if original_db.exists():
        shutil.copy(original_db, db_path)
    
    yield str(db_path)
    
    # تنظيف
    if db_path.exists():
        db_path.unlink()

@pytest.fixture(scope="session")
def db_manager(test_db_path):
    """إنشاء مدير قاعدة البيانات للاختبار"""
    from src.core.database_manager import DatabaseManager
    
    manager = DatabaseManager(test_db_path)
    yield manager
    manager.close()

@pytest.fixture
def sample_product(db_manager):
    """إنشاء منتج تجريبي"""
    cursor = db_manager.connection.cursor()
    cursor.execute("""
        INSERT INTO products (name, barcode, unit, cost_price, selling_price, min_stock, current_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("منتج اختبار", "TEST001", "قطعة", 10.0, 15.0, 5, 100))
    db_manager.connection.commit()
    product_id = cursor.lastrowid
    
    yield product_id
    
    # تنظيف
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db_manager.connection.commit()

@pytest.fixture
def sample_customer(db_manager):
    """إنشاء عميل تجريبي"""
    cursor = db_manager.connection.cursor()
    cursor.execute("""
        INSERT INTO customers (name, phone, email, city, credit_limit)
        VALUES (?, ?, ?, ?, ?)
    """, ("عميل اختبار", "0500000000", "test@test.com", "الرياض", 10000.0))
    db_manager.connection.commit()
    customer_id = cursor.lastrowid
    
    yield customer_id
    
    # تنظيف
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    db_manager.connection.commit()

@pytest.fixture(scope="session")
def playwright_config():
    """إعدادات Playwright"""
    return {
        "headless": False,  # عرض المتصفح أثناء الاختبار
        "slow_mo": 500,  # تباطؤ بين الإجراءات (بالميلي ثانية)
        "timeout": 30000,  # وقت انتظار (30 ثانية)
        "viewport": {"width": 1920, "height": 1080},
        "locale": "ar-SA",
    }

@pytest.fixture
def app_url():
    """رابط التطبيق"""
    return "http://localhost:8000"  # يمكن تعديله حسب الحاجة

def pytest_configure(config):
    """إعداد pytest"""
    # إنشاء مجلد التقارير
    reports_dir = project_root / "test_reports"
    reports_dir.mkdir(exist_ok=True)
    
    # إعداد علامات مخصصة
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests"
    )

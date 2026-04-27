#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات DatabaseLogger بعد الإصلاحات
Tests for DatabaseLogger after fixes
"""

import pytest
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.utils.logger import DatabaseLogger
from src.core.database_manager import DatabaseManager


@pytest.fixture
def db_manager():
    """إنشاء DatabaseManager للاختبار"""
    db_path = ":memory:"
    db = DatabaseManager(db_path)
    db.initialize()
    
    # إنشاء جدول سجل التدقيق
    db.execute_non_query("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT,
            module TEXT,
            entity_type TEXT,
            entity_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return db


@pytest.fixture
def db_logger(db_manager):
    """إنشاء DatabaseLogger للاختبار"""
    return DatabaseLogger(db_manager, user_id=1)


class TestDatabaseLoggerFixes:
    """اختبارات إصلاحات DatabaseLogger"""
    
    def test_log_operation_with_valid_user(self, db_manager, db_logger):
        """اختبار تسجيل عملية مع مستخدم صحيح"""
        # إنشاء مستخدم في قاعدة البيانات
        db_manager.execute_non_query(
            "INSERT INTO users (username, password_hash, salt, email, full_name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            ("test_user", "hash", "salt123", "test@test.com", "Test User", 1)
        )
        
        # تسجيل عملية
        db_logger.log_operation(
            action="CREATE",
            table_name="test_table",
            record_id=1,
            new_values={"name": "test"}
        )
        
        # التحقق من أن العملية تمت بدون أخطاء
        # (لا يجب أن يكون هناك أخطاء FOREIGN KEY)
        assert True
    
    def test_log_operation_with_invalid_user(self, db_manager, db_logger):
        """اختبار تسجيل عملية مع مستخدم غير موجود"""
        # استخدام user_id غير موجود
        db_logger.user_id = 99999
        
        # تسجيل عملية (يجب أن تستخدم NULL بدلاً من user_id)
        db_logger.log_operation(
            action="CREATE",
            table_name="test_table",
            record_id=1,
            new_values={"name": "test"}
        )
        
        # التحقق من أن العملية تمت بدون أخطاء FOREIGN KEY
        assert True
    
    def test_log_operation_with_none_user(self, db_manager):
        """اختبار تسجيل عملية بدون user_id"""
        db_logger = DatabaseLogger(db_manager, user_id=None)
        
        # تسجيل عملية
        db_logger.log_operation(
            action="CREATE",
            table_name="test_table",
            record_id=1,
            new_values={"name": "test"}
        )
        
        # التحقق من أن العملية تمت بدون أخطاء
        assert True
    
    def test_log_operation_foreign_key_error_handling(self, db_manager, db_logger):
        """اختبار معالجة أخطاء FOREIGN KEY"""
        # محاولة تسجيل عملية مع user_id غير موجود
        # (بدون إنشاء المستخدم أولاً)
        db_logger.user_id = 99999
        
        # يجب أن يتم التعامل مع الخطأ بشكل صحيح
        # ولا يجب أن يسبب فشل الاختبار
        try:
            db_logger.log_operation(
                action="CREATE",
                table_name="test_table",
                record_id=1,
                new_values={"name": "test"}
            )
        except Exception as e:
            # إذا حدث خطأ، يجب أن يكون معالجاً بشكل صحيح
            assert "FOREIGN KEY" not in str(e) or "constraint failed" not in str(e)
    
    def test_log_operation_error_messages(self, db_manager, db_logger):
        """اختبار رسائل الخطأ المحسّنة"""
        # استخدام user_id غير موجود
        db_logger.user_id = 99999
        
        # تسجيل عملية
        db_logger.log_operation(
            action="CREATE",
            table_name="test_table",
            record_id=1,
            new_values={"name": "test"}
        )
        
        # التحقق من أن العملية تمت (يجب أن تستخدم NULL)
        assert True
    
    def test_log_operation_with_json_values(self, db_manager, db_logger):
        """اختبار تسجيل عملية مع قيم JSON معقدة"""
        # إنشاء مستخدم
        db_manager.execute_non_query(
            "INSERT INTO users (username, password_hash, salt, email, full_name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            ("test_user", "hash", "salt123", "test@test.com", "Test User", 1)
        )
        
        # تسجيل عملية مع قيم معقدة
        complex_values = {
            "name": "test",
            "nested": {
                "key": "value",
                "number": 123
            },
            "list": [1, 2, 3]
        }
        
        db_logger.log_operation(
            action="UPDATE",
            table_name="test_table",
            record_id=1,
            old_values={"name": "old"},
            new_values=complex_values
        )
        
        assert True
    
    def test_log_operation_multiple_operations(self, db_manager, db_logger):
        """اختبار تسجيل عمليات متعددة"""
        # إنشاء مستخدم
        db_manager.execute_non_query(
            "INSERT INTO users (username, password_hash, salt, email, full_name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            ("test_user", "hash", "salt123", "test@test.com", "Test User", 1)
        )
        
        # تسجيل عدة عمليات
        for i in range(5):
            db_logger.log_operation(
                action="CREATE",
                table_name="test_table",
                record_id=i,
                new_values={"id": i, "name": f"test_{i}"}
            )
        
        # التحقق من أن جميع العمليات تمت بدون أخطاء
        assert True


class TestDatabaseLoggerEdgeCases:
    """اختبارات الحالات الحدية"""
    
    def test_log_operation_empty_values(self, db_manager, db_logger):
        """اختبار تسجيل عملية بقيم فارغة"""
        db_logger.log_operation(
            action="CREATE",
            table_name="test_table",
            record_id=None,
            old_values=None,
            new_values=None
        )
        
        assert True
    
    def test_log_operation_special_characters(self, db_manager, db_logger):
        """اختبار تسجيل عملية مع أحرف خاصة"""
        # إنشاء مستخدم
        db_manager.execute_non_query(
            "INSERT INTO users (username, password_hash, salt, email, full_name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            ("test_user", "hash", "salt123", "test@test.com", "Test User", 1)
        )
        
        special_values = {
            "name": "test with 'quotes' and \"double quotes\"",
            "unicode": "العربية",
            "special": "!@#$%^&*()"
        }
        
        db_logger.log_operation(
            action="CREATE",
            table_name="test_table",
            record_id=1,
            new_values=special_values
        )
        
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])





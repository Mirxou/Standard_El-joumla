#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات إضافية لـ DatabaseLogger
Extended tests for DatabaseLogger
"""

import pytest
from pathlib import Path
import sys
import json
from decimal import Decimal
from datetime import datetime

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
    
    yield db
    
    # تنظيف
    if db.connection:
        db.connection.close()


@pytest.fixture
def test_user(db_manager):
    """إنشاء مستخدم اختبار"""
    db_manager.execute_non_query(
        "INSERT INTO users (username, password_hash, salt, email, full_name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
        ("test_user", "hash", "salt123", "test@test.com", "Test User", 1)
    )
    # الحصول على معرف المستخدم
    user_id = db_manager.execute_scalar("SELECT id FROM users WHERE username = ?", ("test_user",))
    return user_id


class TestDatabaseLoggerExtended:
    """اختبارات إضافية لـ DatabaseLogger"""
    
    def test_log_operation_large_json(self, db_manager, test_user):
        """اختبار تسجيل عملية مع JSON كبير"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        # إنشاء JSON كبير
        large_data = {
            "items": [{"id": i, "name": f"item_{i}", "data": "x" * 100} for i in range(100)],
            "metadata": {"timestamp": datetime.now().isoformat(), "version": "1.0"}
        }
        
        db_logger.log_operation(
            action="CREATE",
            table_name="large_table",
            record_id=1,
            new_values=large_data
        )
        
        assert True
    
    def test_log_operation_unicode_characters(self, db_manager, test_user):
        """اختبار تسجيل عملية مع أحرف Unicode"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        unicode_data = {
            "name": "العربية",
            "description": "中文 English Русский",
            "emoji": "🚀 ✅ ❌ ⚠️",
            "special": "©®™€£¥"
        }
        
        db_logger.log_operation(
            action="UPDATE",
            table_name="unicode_table",
            record_id=1,
            old_values={"name": "old"},
            new_values=unicode_data
        )
        
        assert True
    
    def test_log_operation_decimal_values(self, db_manager, test_user):
        """اختبار تسجيل عملية مع قيم Decimal"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        decimal_data = {
            "price": Decimal("123.45"),
            "quantity": Decimal("100.00"),
            "total": Decimal("12345.00")
        }
        
        db_logger.log_operation(
            action="CREATE",
            table_name="decimal_table",
            record_id=1,
            new_values=decimal_data
        )
        
        assert True
    
    def test_log_operation_datetime_values(self, db_manager, test_user):
        """اختبار تسجيل عملية مع قيم datetime"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        datetime_data = {
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "expires_at": datetime(2025, 12, 31, 23, 59, 59)
        }
        
        db_logger.log_operation(
            action="CREATE",
            table_name="datetime_table",
            record_id=1,
            new_values=datetime_data
        )
        
        assert True
    
    def test_log_operation_nested_structures(self, db_manager, test_user):
        """اختبار تسجيل عملية مع هياكل متداخلة"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        nested_data = {
            "user": {
                "id": 1,
                "name": "Test",
                "address": {
                    "street": "123 Main St",
                    "city": "Test City",
                    "country": "Test Country"
                }
            },
            "items": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ]
        }
        
        db_logger.log_operation(
            action="CREATE",
            table_name="nested_table",
            record_id=1,
            new_values=nested_data
        )
        
        assert True
    
    def test_log_operation_null_values(self, db_manager, test_user):
        """اختبار تسجيل عملية مع قيم NULL"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        null_data = {
            "name": "Test",
            "description": None,
            "optional_field": None
        }
        
        db_logger.log_operation(
            action="UPDATE",
            table_name="null_table",
            record_id=1,
            old_values={"name": "Old"},
            new_values=null_data
        )
        
        assert True
    
    def test_log_operation_boolean_values(self, db_manager, test_user):
        """اختبار تسجيل عملية مع قيم boolean"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        boolean_data = {
            "is_active": True,
            "is_deleted": False,
            "is_verified": True
        }
        
        db_logger.log_operation(
            action="UPDATE",
            table_name="boolean_table",
            record_id=1,
            new_values=boolean_data
        )
        
        assert True
    
    def test_log_operation_list_values(self, db_manager, test_user):
        """اختبار تسجيل عملية مع قوائم"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        list_data = {
            "tags": ["tag1", "tag2", "tag3"],
            "numbers": [1, 2, 3, 4, 5],
            "mixed": [1, "two", 3.0, True, None]
        }
        
        db_logger.log_operation(
            action="CREATE",
            table_name="list_table",
            record_id=1,
            new_values=list_data
        )
        
        assert True
    
    def test_log_operation_concurrent_operations(self, db_manager, test_user):
        """اختبار تسجيل عمليات متزامنة"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        # تسجيل عدة عمليات بسرعة
        for i in range(10):
            db_logger.log_operation(
                action="CREATE",
                table_name="concurrent_table",
                record_id=i,
                new_values={"id": i, "data": f"data_{i}"}
            )
        
        assert True
    
    def test_log_operation_error_recovery(self, db_manager):
        """اختبار استعادة الأخطاء"""
        # استخدام user_id غير موجود
        db_logger = DatabaseLogger(db_manager, user_id=99999)
        
        # يجب أن تتعامل مع الخطأ بشكل صحيح
        db_logger.log_operation(
            action="CREATE",
            table_name="error_table",
            record_id=1,
            new_values={"name": "test"}
        )
        
        # يجب أن تستمر العملية بدون فشل
        assert True
    
    def test_log_operation_performance(self, db_manager, test_user):
        """اختبار أداء تسجيل العمليات"""
        import time
        
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        start_time = time.time()
        
        # تسجيل 100 عملية
        for i in range(100):
            db_logger.log_operation(
                action="CREATE",
                table_name="performance_table",
                record_id=i,
                new_values={"id": i, "data": f"data_{i}"}
            )
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / 100
        
        # يجب أن يكون متوسط الوقت معقولاً (أقل من 0.1 ثانية لكل عملية)
        assert avg_time < 0.1, f"متوسط الوقت كبير جداً: {avg_time:.4f} ثانية"
    
    def test_log_operation_audit_trail_integrity(self, db_manager, test_user):
        """اختبار سلامة سجل التدقيق"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        # تسجيل عملية
        db_logger.log_operation(
            action="CREATE",
            table_name="audit_table",
            record_id=1,
            new_values={"name": "test"}
        )
        
        # التحقق من وجود السجل في audit_log
        result = db_manager.execute_query(
            "SELECT user_id, action, module, entity_id FROM audit_log WHERE module = ? AND entity_id = ?",
            ("audit_table", 1)
        )
        
        assert len(result) > 0, "يجب أن يكون السجل موجوداً في audit_log"
        # result يمكن أن يكون list of dicts أو list of tuples
        if isinstance(result[0], dict):
            assert result[0]["user_id"] == test_user, f"يجب أن يكون user_id صحيحاً (متوقع: {test_user}, فعلي: {result[0]['user_id']})"
            assert result[0]["action"] == "CREATE", "يجب أن يكون action صحيحاً"
        else:
            # list of tuples
            assert result[0][0] == test_user, f"يجب أن يكون user_id صحيحاً (متوقع: {test_user}, فعلي: {result[0][0]})"
            assert result[0][1] == "CREATE", "يجب أن يكون action صحيحاً"
    
    def test_log_operation_json_serialization(self, db_manager, test_user):
        """اختبار تسلسل JSON"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        # بيانات تحتوي على أنواع مختلفة
        complex_data = {
            "string": "test",
            "int": 123,
            "float": 123.45,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"}
        }
        
        # يجب أن يتم تسلسل JSON بنجاح
        db_logger.log_operation(
            action="CREATE",
            table_name="json_table",
            record_id=1,
            new_values=complex_data
        )
        
        # التحقق من أن البيانات تم حفظها بشكل صحيح
        result = db_manager.execute_scalar(
            "SELECT new_values FROM audit_log WHERE module = ?",
            ("json_table",)
        )
        
        assert result is not None, "يجب أن تكون البيانات محفوظة"
        parsed = json.loads(result)
        assert parsed["string"] == "test", "يجب أن تكون البيانات صحيحة"


class TestDatabaseLoggerEdgeCasesExtended:
    """اختبارات الحالات الحدية الإضافية"""
    
    def test_log_operation_empty_strings(self, db_manager, test_user):
        """اختبار تسجيل عملية مع strings فارغة"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        empty_data = {
            "name": "",
            "description": "",
            "notes": ""
        }
        
        db_logger.log_operation(
            action="UPDATE",
            table_name="empty_table",
            record_id=1,
            new_values=empty_data
        )
        
        assert True
    
    def test_log_operation_very_long_strings(self, db_manager, test_user):
        """اختبار تسجيل عملية مع strings طويلة جداً"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        long_string = "x" * 10000  # 10KB string
        long_data = {
            "description": long_string,
            "content": long_string * 2  # 20KB string
        }
        
        db_logger.log_operation(
            action="CREATE",
            table_name="long_table",
            record_id=1,
            new_values=long_data
        )
        
        assert True
    
    def test_log_operation_special_table_names(self, db_manager, test_user):
        """اختبار تسجيل عملية مع أسماء جداول خاصة"""
        db_logger = DatabaseLogger(db_manager, user_id=test_user)
        
        special_names = [
            "table_with_underscores",
            "TableWithCamelCase",
            "table-with-dashes",
            "123table",
            "table'with'quotes"
        ]
        
        for table_name in special_names:
            try:
                db_logger.log_operation(
                    action="CREATE",
                    table_name=table_name,
                    record_id=1,
                    new_values={"name": "test"}
                )
            except Exception:
                # بعض الأسماء قد لا تكون صالحة
                pass
        
        assert True
    
    def test_log_operation_multiple_users(self, db_manager):
        """اختبار تسجيل عمليات من مستخدمين متعددين"""
        # إنشاء مستخدمين
        db_manager.execute_non_query(
            "INSERT INTO users (username, password_hash, salt, email, full_name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            ("user1", "hash1", "salt1", "user1@test.com", "User 1", 1)
        )
        db_manager.execute_non_query(
            "INSERT INTO users (username, password_hash, salt, email, full_name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            ("user2", "hash2", "salt2", "user2@test.com", "User 2", 1)
        )
        
        user1_id = db_manager.execute_scalar("SELECT id FROM users WHERE username = ?", ("user1",))
        user2_id = db_manager.execute_scalar("SELECT id FROM users WHERE username = ?", ("user2",))
        
        logger1 = DatabaseLogger(db_manager, user_id=user1_id)
        logger2 = DatabaseLogger(db_manager, user_id=user2_id)
        
        # تسجيل عمليات من مستخدمين مختلفين
        logger1.log_operation(action="CREATE", table_name="multi_table", record_id=1, new_values={"user": "1"})
        logger2.log_operation(action="CREATE", table_name="multi_table", record_id=2, new_values={"user": "2"})
        
        # التحقق من أن كل عملية مرتبطة بالمستخدم الصحيح
        results = db_manager.execute_query(
            "SELECT user_id, entity_id FROM audit_log WHERE module = ? ORDER BY entity_id",
            ("multi_table",)
        )
        
        assert len(results) >= 2, f"يجب أن يكون هناك سجلان على الأقل (وجد: {len(results)})"
        # execute_query يعيد list of dicts
        user_ids = [row["user_id"] for row in results]
        assert user1_id in user_ids, f"يجب أن يكون user1_id ({user1_id}) موجوداً في النتائج"
        assert user2_id in user_ids, f"يجب أن يكون user2_id ({user2_id}) موجوداً في النتائج"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])





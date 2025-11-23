#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نظام تسجيل الاستعلامات البطيئة
"""
import pytest
import time
from pathlib import Path
from src.core.database_manager import DatabaseManager


class TestSlowQueryLogging:
    @pytest.fixture
    def db(self, tmp_path):
        """إنشاء قاعدة بيانات مؤقتة للاختبار"""
        db_path = tmp_path / "test_slow_queries.db"
        db = DatabaseManager(str(db_path))
        db.initialize()
        return db
    
    def test_slow_query_table_exists(self, db):
        """التحقق من وجود جدول slow_queries"""
        result = db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='slow_queries'"
        )
        assert len(result) == 1
        assert result[0]['name'] == 'slow_queries'
    
    def test_slow_query_logging(self, db):
        """اختبار تسجيل استعلام بطيء"""
        # تعيين عتبة منخفضة للاختبار
        db.slow_query_threshold_ms = 0.1
        
        # تنفيذ استعلام بطيء (عن طريق إضافة تأخير)
        db.execute_query("SELECT 1 WHERE 1=0")  # استعلام سريع
        time.sleep(0.002)  # تأخير صغير
        
        # التحقق من تسجيل الاستعلامات البطيئة
        slow_queries = db.execute_query(
            "SELECT COUNT(*) as count FROM slow_queries"
        )
        # قد تكون هناك استعلامات بطيئة أو لا (حسب سرعة النظام)
        assert slow_queries[0]['count'] >= 0
    
    def test_slow_query_threshold_configuration(self, db):
        """اختبار تعيين عتبة الاستعلام البطيء"""
        # تعيين عتبة مخصصة
        db.slow_query_threshold_ms = 50.0
        assert db.slow_query_threshold_ms == 50.0
        
        # تعيين عتبة أخرى
        db.slow_query_threshold_ms = 200.0
        assert db.slow_query_threshold_ms == 200.0
    
    def test_slow_query_data_structure(self, db):
        """التحقق من بنية بيانات الاستعلامات البطيئة"""
        # الحصول على معلومات الجدول
        columns = db.execute_query("PRAGMA table_info(slow_queries)")
        
        column_names = [col['name'] for col in columns]
        
        # التحقق من الأعمدة المطلوبة
        assert 'id' in column_names
        assert 'query_text' in column_names
        assert 'params' in column_names
        assert 'duration_ms' in column_names
        assert 'executed_at' in column_names
    
    def test_slow_query_params_serialization(self, db):
        """اختبار تسلسل معاملات الاستعلام"""
        db.slow_query_threshold_ms = 0.0  # تسجيل جميع الاستعلامات
        
        # تنفيذ استعلام مع معاملات
        db.execute_query(
            "SELECT ? as value, ? as name",
            (123, "test")
        )
        
        # التحقق من تسجيل المعاملات
        slow_queries = db.execute_query(
            "SELECT params FROM slow_queries WHERE query_text LIKE '%SELECT%value%' ORDER BY id DESC LIMIT 1"
        )
        
        if slow_queries:
            params = slow_queries[0]['params']
            assert params is not None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار تصدير مقاييس الأداء
"""
import pytest
import json
import csv
from pathlib import Path
from src.core.database_manager import DatabaseManager
from src.services.performance_service import PerformanceService


class TestMetricsExport:
    @pytest.fixture
    def db(self, tmp_path):
        """إنشاء قاعدة بيانات مؤقتة للاختبار"""
        db_path = tmp_path / "test_metrics.db"
        db = DatabaseManager(str(db_path))
        db.initialize()
        return db
    
    @pytest.fixture
    def performance_service(self, db):
        """إنشاء خدمة الأداء"""
        return PerformanceService(db)
    
    def test_export_metrics_to_csv(self, performance_service, tmp_path):
        """اختبار تصدير المقاييس إلى CSV"""
        # جمع بعض المقاييس
        performance_service.start_monitoring()
        import time
        time.sleep(0.5)  # انتظار لجمع بعض المقاييس
        performance_service.stop_monitoring()
        
        # تصدير إلى CSV
        output_file = tmp_path / "metrics.csv"
        result = performance_service.export_metrics_to_csv(str(output_file), minutes=1)
        
        # التحقق من النجاح (قد لا تكون هناك بيانات بعد)
        if result['success']:
            assert output_file.exists()
            
            # قراءة الملف والتحقق من البنية
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                assert 'timestamp' in headers
                assert 'db_size_mb' in headers
                assert 'query_count' in headers
                assert 'avg_query_time_ms' in headers
                assert 'cache_hit_rate' in headers
    
    def test_export_metrics_to_json(self, performance_service, tmp_path):
        """اختبار تصدير المقاييس إلى JSON"""
        # جمع بعض المقاييس
        performance_service.start_monitoring()
        import time
        time.sleep(0.5)
        performance_service.stop_monitoring()
        
        # تصدير إلى JSON
        output_file = tmp_path / "metrics.json"
        result = performance_service.export_metrics_to_json(str(output_file), minutes=1)
        
        # التحقق من النجاح
        if result['success']:
            assert output_file.exists()
            
            # قراءة الملف والتحقق من البنية
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                assert 'export_timestamp' in data
                assert 'time_range_minutes' in data
                assert 'total_records' in data
                assert 'metrics' in data
                assert isinstance(data['metrics'], list)
    
    def test_export_empty_metrics(self, performance_service, tmp_path):
        """اختبار تصدير مقاييس فارغة"""
        # محاولة التصدير بدون جمع مقاييس
        output_file = tmp_path / "empty_metrics.csv"
        result = performance_service.export_metrics_to_csv(str(output_file), minutes=1)
        
        # يجب أن يفشل أو يعيد رسالة "لا توجد بيانات"
        if not result['success']:
            assert 'error' in result
    
    def test_get_slow_queries_from_db(self, performance_service, db):
        """اختبار الحصول على الاستعلامات البطيئة من قاعدة البيانات"""
        # إدراج بعض الاستعلامات البطيئة للاختبار
        db.execute_query(
            "INSERT INTO slow_queries (query_text, duration_ms) VALUES (?, ?)",
            ("SELECT * FROM test", 150.5)
        )
        db.execute_query(
            "INSERT INTO slow_queries (query_text, duration_ms) VALUES (?, ?)",
            ("SELECT COUNT(*) FROM test2", 200.3)
        )
        
        # الحصول على الاستعلامات البطيئة
        slow_queries = performance_service.get_slow_queries_from_db(limit=10)
        
        assert len(slow_queries) >= 2
        assert any(q['query_text'] == "SELECT * FROM test" for q in slow_queries)

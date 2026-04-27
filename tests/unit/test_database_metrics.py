#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Database Metrics
اختبارات Database Metrics
"""

import pytest
import time
import statistics
import threading
from datetime import datetime, timedelta
from src.core.database_metrics import DatabaseMetrics, get_database_metrics


@pytest.fixture(scope="function")
def metrics():
    """DatabaseMetrics instance للاختبارات"""
    return DatabaseMetrics(max_history=100)


@pytest.fixture(scope="function")
def metrics_small():
    """DatabaseMetrics instance مع max_history صغير للاختبار"""
    return DatabaseMetrics(max_history=5)


class TestDatabaseMetrics:
    """اختبارات DatabaseMetrics"""
    
    def test_metrics_initialization(self, metrics):
        """اختبار تهيئة Metrics"""
        assert metrics.max_history == 100
        assert len(metrics.query_times) == 0
        assert len(metrics.slow_queries) == 0
        assert len(metrics.query_errors) == 0
        assert metrics.connection_count == 0
        assert metrics.max_connections == 0
        assert metrics.total_queries == 0
        assert metrics.total_selects == 0
        assert metrics.total_inserts == 0
        assert metrics.total_updates == 0
        assert metrics.total_deletes == 0
        assert isinstance(metrics.start_time, datetime)
    
    def test_metrics_record_query(self, metrics):
        """اختبار تسجيل استعلام"""
        metrics.record_query("SELECT * FROM test", 50.0, "SELECT", success=True)
        
        assert metrics.total_queries == 1
        assert len(metrics.query_times) == 1
        assert metrics.query_times[0]["query"] == "SELECT * FROM test"
        assert metrics.query_times[0]["duration_ms"] == 50.0
        assert metrics.query_times[0]["query_type"] == "SELECT"
        assert metrics.query_times[0]["success"] is True
        assert isinstance(metrics.query_times[0]["timestamp"], datetime)
    
    def test_metrics_record_query_long_query(self, metrics):
        """اختبار تسجيل استعلام طويل (يُقطع إلى 100 حرف)"""
        long_query = "SELECT * FROM " + "test_table " * 20  # query طويل
        metrics.record_query(long_query, 50.0, "SELECT")
        
        assert len(metrics.query_times[0]["query"]) == 100
    
    def test_metrics_record_query_types_select(self, metrics):
        """اختبار تسجيل استعلام SELECT"""
        metrics.record_query("SELECT * FROM test", 50.0, "SELECT")
        
        assert metrics.total_selects == 1
        assert metrics.total_inserts == 0
        assert metrics.total_updates == 0
        assert metrics.total_deletes == 0
    
    def test_metrics_record_query_types_insert(self, metrics):
        """اختبار تسجيل استعلام INSERT"""
        metrics.record_query("INSERT INTO test VALUES (?)", 30.0, "INSERT")
        
        assert metrics.total_inserts == 1
        assert metrics.total_selects == 0
    
    def test_metrics_record_query_types_update(self, metrics):
        """اختبار تسجيل استعلام UPDATE"""
        metrics.record_query("UPDATE test SET name = ?", 40.0, "UPDATE")
        
        assert metrics.total_updates == 1
    
    def test_metrics_record_query_types_delete(self, metrics):
        """اختبار تسجيل استعلام DELETE"""
        metrics.record_query("DELETE FROM test WHERE id = ?", 35.0, "DELETE")
        
        assert metrics.total_deletes == 1
    
    def test_metrics_record_query_types_case_insensitive(self, metrics):
        """اختبار أن أنواع الاستعلامات case-insensitive"""
        metrics.record_query("SELECT 1", 10.0, "select")
        metrics.record_query("INSERT INTO test", 20.0, "Insert")
        metrics.record_query("UPDATE test", 30.0, "UPDATE")
        
        assert metrics.total_selects == 1
        assert metrics.total_inserts == 1
        assert metrics.total_updates == 1
    
    def test_metrics_record_query_error(self, metrics):
        """اختبار تسجيل استعلام مع خطأ"""
        metrics.record_query(
            "SELECT * FROM nonexistent",
            50.0,
            "SELECT",
            success=False,
            error="Table not found"
        )
        
        assert len(metrics.query_errors) == 1
        assert metrics.query_errors[0]["query"] == "SELECT * FROM nonexistent"
        assert metrics.query_errors[0]["error"] == "Table not found"
        assert isinstance(metrics.query_errors[0]["timestamp"], datetime)
    
    def test_metrics_record_query_success_no_error(self, metrics):
        """اختبار أن الأخطاء لا تُسجل للاستعلامات الناجحة"""
        metrics.record_query("SELECT 1", 10.0, "SELECT", success=True, error=None)
        
        assert len(metrics.query_errors) == 0
    
    def test_metrics_record_slow_query(self, metrics):
        """اختبار تسجيل استعلام بطيء"""
        metrics.record_slow_query("SELECT * FROM large_table", 150.0, threshold_ms=100.0)
        
        assert len(metrics.slow_queries) == 1
        assert metrics.slow_queries[0]["query"] == "SELECT * FROM large_table"
        assert metrics.slow_queries[0]["duration_ms"] == 150.0
        assert isinstance(metrics.slow_queries[0]["timestamp"], datetime)
    
    def test_metrics_record_slow_query_below_threshold(self, metrics):
        """اختبار أن الاستعلامات السريعة لا تُسجل"""
        metrics.record_slow_query("SELECT 1", 50.0, threshold_ms=100.0)
        
        assert len(metrics.slow_queries) == 0
    
    def test_metrics_record_slow_query_long_query(self, metrics):
        """اختبار أن الاستعلامات البطيئة الطويلة تُقطع إلى 200 حرف"""
        long_query = "SELECT * FROM " + "table " * 50
        metrics.record_slow_query(long_query, 150.0, threshold_ms=100.0)
        
        assert len(metrics.slow_queries[0]["query"]) == 200
    
    def test_metrics_record_lock_wait(self, metrics):
        """اختبار تسجيل lock wait time"""
        metrics.record_lock_wait(250.5)
        
        assert len(metrics.lock_wait_times) == 1
        assert metrics.lock_wait_times[0]["wait_time_ms"] == 250.5
        assert isinstance(metrics.lock_wait_times[0]["timestamp"], datetime)
    
    def test_metrics_update_connection_count(self, metrics):
        """اختبار تحديث عدد الاتصالات"""
        metrics.update_connection_count(5)
        assert metrics.connection_count == 5
        
        metrics.update_connection_count(10)
        assert metrics.connection_count == 10
        assert metrics.max_connections == 10
        
        metrics.update_connection_count(8)
        assert metrics.connection_count == 8
        assert metrics.max_connections == 10  # يجب أن يبقى الأقصى
    
    def test_metrics_get_statistics_empty(self, metrics):
        """اختبار الحصول على إحصائيات بدون بيانات"""
        stats = metrics.get_statistics()
        
        assert stats["total_queries"] == 0
        assert stats["avg_response_time_ms"] == 0
        assert stats["min_response_time_ms"] == 0
        assert stats["max_response_time_ms"] == 0
        assert stats["p95_response_time_ms"] == 0
        assert stats["slow_queries_count"] == 0
        assert stats["error_rate"] == 0
        assert stats["connection_count"] == 0
        assert stats["query_types"] == {}
    
    def test_metrics_get_statistics_with_data(self, metrics):
        """اختبار الحصول على إحصائيات مع بيانات"""
        # تسجيل عدة استعلامات
        metrics.record_query("SELECT 1", 10.0, "SELECT")
        metrics.record_query("SELECT 2", 20.0, "SELECT")
        metrics.record_query("INSERT INTO test", 30.0, "INSERT")
        metrics.record_query("UPDATE test", 40.0, "UPDATE")
        metrics.record_query("SELECT 3", 50.0, "SELECT", success=False, error="Error")
        
        stats = metrics.get_statistics()
        
        assert stats["total_queries"] == 5
        assert stats["avg_response_time_ms"] == 30.0  # (10+20+30+40+50)/5
        assert stats["min_response_time_ms"] == 10.0
        assert stats["max_response_time_ms"] == 50.0
        assert stats["error_rate"] == 0.2  # 1 error / 5 queries
        assert stats["query_types"]["SELECT"] == 3
        assert stats["query_types"]["INSERT"] == 1
        assert stats["query_types"]["UPDATE"] == 1
        assert stats["total_selects"] == 3
        assert stats["total_inserts"] == 1
        assert stats["total_updates"] == 1
    
    def test_metrics_get_statistics_time_window(self, metrics):
        """اختبار إحصائيات بنافذة زمنية"""
        # تسجيل استعلام قديم (محاكاة)
        old_time = datetime.now() - timedelta(minutes=120)  # قبل ساعتين
        metrics.query_times.append({
            "query": "SELECT old",
            "duration_ms": 100.0,
            "query_type": "SELECT",
            "timestamp": old_time,
            "success": True
        })
        
        # تسجيل استعلام جديد
        metrics.record_query("SELECT new", 50.0, "SELECT")
        
        # إحصائيات لآخر 60 دقيقة (يجب أن تستبعد القديم)
        stats = metrics.get_statistics(time_window_minutes=60)
        assert stats["total_queries"] == 1  # فقط الاستعلام الجديد
        
        # إحصائيات لآخر 180 دقيقة (يجب أن تشمل القديم)
        stats = metrics.get_statistics(time_window_minutes=180)
        assert stats["total_queries"] == 2
    
    def test_metrics_get_statistics_p95(self, metrics):
        """اختبار حساب P95"""
        # تسجيل 100 استعلام بقيم مختلفة
        for i in range(100):
            metrics.record_query(f"SELECT {i}", float(i), "SELECT")
        
        stats = metrics.get_statistics()
        
        # P95 يجب أن يكون حوالي القيمة 95
        assert stats["p95_response_time_ms"] >= 90
        assert stats["p95_response_time_ms"] <= 99
    
    def test_metrics_get_recent_slow_queries(self, metrics):
        """اختبار الحصول على آخر الاستعلامات البطيئة"""
        # تسجيل عدة استعلامات بطيئة
        for i in range(15):
            metrics.record_slow_query(f"SELECT slow_{i}", 150.0 + i, threshold_ms=100.0)
        
        recent = metrics.get_recent_slow_queries(limit=10)
        
        assert len(recent) == 10
        # يجب أن تكون آخر 10 (الأحدث)
        assert recent[-1]["query"] == "SELECT slow_14"
    
    def test_metrics_get_recent_errors(self, metrics):
        """اختبار الحصول على آخر الأخطاء"""
        # تسجيل عدة أخطاء
        for i in range(12):
            metrics.record_query(
                f"SELECT error_{i}",
                50.0,
                "SELECT",
                success=False,
                error=f"Error {i}"
            )
        
        recent_errors = metrics.get_recent_errors(limit=8)
        
        assert len(recent_errors) == 8
        # يجب أن تكون آخر 8 (الأحدث)
        assert recent_errors[-1]["error"] == "Error 11"
    
    def test_metrics_reset(self, metrics):
        """اختبار إعادة تعيين الإحصائيات"""
        # إضافة بيانات
        metrics.record_query("SELECT 1", 50.0, "SELECT")
        metrics.record_slow_query("SELECT slow", 150.0, threshold_ms=100.0)
        metrics.record_query("SELECT error", 50.0, "SELECT", success=False, error="Error")
        metrics.update_connection_count(10)
        metrics.record_lock_wait(100.0)
        
        # إعادة التعيين
        original_start_time = metrics.start_time
        time.sleep(0.01)  # تأخير صغير للتأكد من تغيير الوقت
        metrics.reset()
        
        assert len(metrics.query_times) == 0
        assert len(metrics.slow_queries) == 0
        assert len(metrics.query_errors) == 0
        assert len(metrics.lock_wait_times) == 0
        assert metrics.connection_count == 0
        assert metrics.max_connections == 0
        assert metrics.total_queries == 0
        assert metrics.total_selects == 0
        assert metrics.total_inserts == 0
        assert metrics.total_updates == 0
        assert metrics.total_deletes == 0
        assert metrics.start_time > original_start_time
    
    def test_metrics_max_history_limit(self, metrics_small):
        """اختبار حد max_history"""
        # تسجيل أكثر من max_history
        for i in range(10):
            metrics_small.record_query(f"SELECT {i}", 50.0, "SELECT")
        
        # يجب أن يكون فقط آخر max_history (5)
        assert len(metrics_small.query_times) == 5
        # يجب أن تكون آخر 5 استعلامات
        assert "SELECT 5" in metrics_small.query_times[0]["query"]
        assert "SELECT 9" in metrics_small.query_times[-1]["query"]
    
    def test_metrics_thread_safety(self, metrics):
        """اختبار thread safety"""
        results = []
        errors = []
        
        def record_queries(start, count):
            """تسجيل استعلامات من thread"""
            try:
                for i in range(count):
                    metrics.record_query(
                        f"SELECT {start + i}",
                        50.0,
                        "SELECT"
                    )
                    results.append(start + i)
            except Exception as e:
                errors.append(e)
        
        # إنشاء عدة threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_queries, args=(i * 10, 10))
            threads.append(thread)
            thread.start()
        
        # انتظار انتهاء جميع threads
        for thread in threads:
            thread.join()
        
        # التحقق من عدم وجود أخطاء
        assert len(errors) == 0
        
        # التحقق من أن جميع الاستعلامات تم تسجيلها
        assert metrics.total_queries == 50
        assert len(metrics.query_times) == 50
    
    def test_metrics_slow_queries_limit(self, metrics):
        """اختبار حد slow_queries (100)"""
        # تسجيل أكثر من 100 استعلام بطيء
        for i in range(150):
            metrics.record_slow_query(f"SELECT slow_{i}", 150.0, threshold_ms=100.0)
        
        # يجب أن يكون فقط آخر 100
        assert len(metrics.slow_queries) == 100
    
    def test_metrics_query_errors_limit(self, metrics):
        """اختبار حد query_errors (100)"""
        # تسجيل أكثر من 100 خطأ
        for i in range(150):
            metrics.record_query(
                f"SELECT error_{i}",
                50.0,
                "SELECT",
                success=False,
                error=f"Error {i}"
            )
        
        # يجب أن يكون فقط آخر 100
        assert len(metrics.query_errors) == 100
    
    def test_metrics_lock_wait_times_limit(self, metrics):
        """اختبار حد lock_wait_times (100)"""
        # تسجيل أكثر من 100 lock wait
        for i in range(150):
            metrics.record_lock_wait(100.0 + i)
        
        # يجب أن يكون فقط آخر 100
        assert len(metrics.lock_wait_times) == 100
    
    def test_metrics_get_statistics_uptime(self, metrics):
        """اختبار حساب uptime"""
        stats = metrics.get_statistics()
        
        assert "uptime_seconds" in stats
        assert stats["uptime_seconds"] >= 0
        assert isinstance(stats["uptime_seconds"], float)
        
        # انتظار قليل
        time.sleep(0.1)
        stats2 = metrics.get_statistics()
        
        assert stats2["uptime_seconds"] > stats["uptime_seconds"]
    
    def test_metrics_get_statistics_query_types(self, metrics):
        """اختبار إحصائيات أنواع الاستعلامات"""
        metrics.record_query("SELECT 1", 10.0, "SELECT")
        metrics.record_query("SELECT 2", 20.0, "SELECT")
        metrics.record_query("INSERT INTO test", 30.0, "INSERT")
        metrics.record_query("UPDATE test", 40.0, "UPDATE")
        metrics.record_query("DELETE FROM test", 50.0, "DELETE")
        
        stats = metrics.get_statistics()
        query_types = stats["query_types"]
        
        assert query_types["SELECT"] == 2
        assert query_types["INSERT"] == 1
        assert query_types["UPDATE"] == 1
        assert query_types["DELETE"] == 1
    
    def test_get_database_metrics_singleton(self):
        """اختبار أن get_database_metrics يُرجع singleton"""
        metrics1 = get_database_metrics()
        metrics2 = get_database_metrics()
        
        assert metrics1 is metrics2
    
    def test_metrics_statistics_error_rate_calculation(self, metrics):
        """اختبار حساب error rate"""
        # 10 استعلامات ناجحة
        for i in range(10):
            metrics.record_query(f"SELECT {i}", 50.0, "SELECT", success=True)
        
        # 5 استعلامات فاشلة
        for i in range(5):
            metrics.record_query(
                f"SELECT error_{i}",
                50.0,
                "SELECT",
                success=False,
                error="Error"
            )
        
        stats = metrics.get_statistics()
        
        # error_rate = 5 / 15 = 0.333...
        assert abs(stats["error_rate"] - (5.0 / 15.0)) < 0.001





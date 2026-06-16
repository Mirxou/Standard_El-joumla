#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Performance Metrics
تتبع أداء قاعدة البيانات
"""

import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional

from src.utils.logger import setup_logger


class DatabaseMetrics:
    """تتبع metrics أداء قاعدة البيانات"""

    def __init__(self, max_history: int = 1000):
        """
        تهيئة Database Metrics

        Args:
            max_history: أقصى عدد من السجلات المحفوظة
        """
        self.max_history = max_history
        self.logger = setup_logger(__name__)
        self.lock = Lock()

        # Query execution times
        self.query_times: deque = deque(maxlen=max_history)

        # Slow queries (> threshold)
        self.slow_queries: deque = deque(maxlen=100)

        # Error tracking
        self.query_errors: deque = deque(maxlen=100)

        # Connection tracking
        self.connection_count = 0
        self.max_connections = 0

        # Statistics
        self.total_queries = 0
        self.total_selects = 0
        self.total_inserts = 0
        self.total_updates = 0
        self.total_deletes = 0

        # Lock wait times (SQLite specific)
        self.lock_wait_times: deque = deque(maxlen=100)

        # Timestamp tracking
        self.start_time = datetime.now()

    def record_query(
        self,
        query: str,
        duration_ms: float,
        query_type: str = "unknown",
        success: bool = True,
        error: Optional[str] = None,
    ):
        """
        تسجيل استعلام

        Args:
            query: SQL query
            duration_ms: مدة التنفيذ بالمللي ثانية
            query_type: نوع الاستعلام (SELECT, INSERT, UPDATE, DELETE)
            success: نجاح الاستعلام
            error: رسالة الخطأ إن وجدت
        """
        with self.lock:
            self.total_queries += 1

            # تسجيل وقت التنفيذ
            self.query_times.append(
                {
                    "query": query[:100],  # أول 100 حرف فقط
                    "duration_ms": duration_ms,
                    "query_type": query_type,
                    "timestamp": datetime.now(),
                    "success": success,
                }
            )

            # تحديث الإحصائيات
            query_type_upper = query_type.upper()
            if query_type_upper == "SELECT":
                self.total_selects += 1
            elif query_type_upper == "INSERT":
                self.total_inserts += 1
            elif query_type_upper == "UPDATE":
                self.total_updates += 1
            elif query_type_upper == "DELETE":
                self.total_deletes += 1

            # تسجيل الأخطاء
            if not success and error:
                self.query_errors.append({"query": query[:100], "error": error, "timestamp": datetime.now()})

    def record_slow_query(self, query: str, duration_ms: float, threshold_ms: float = 100.0):
        """تسجيل استعلام بطيء"""
        if duration_ms >= threshold_ms:
            with self.lock:
                self.slow_queries.append(
                    {
                        "query": query[:200],
                        "duration_ms": duration_ms,
                        "timestamp": datetime.now(),
                    }
                )

    def record_lock_wait(self, wait_time_ms: float):
        """تسجيل وقت انتظار Lock (SQLite)"""
        with self.lock:
            self.lock_wait_times.append({"wait_time_ms": wait_time_ms, "timestamp": datetime.now()})

    def update_connection_count(self, count: int):
        """تحديث عدد الاتصالات"""
        with self.lock:
            self.connection_count = count
            if count > self.max_connections:
                self.max_connections = count

    def get_statistics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        الحصول على إحصائيات الأداء

        Args:
            time_window_minutes: نافذة الوقت بالدقائق

        Returns:
            Dict containing statistics
        """
        with self.lock:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

            # تصفية الاستعلامات في النافذة الزمنية
            recent_queries = [q for q in self.query_times if q["timestamp"] >= cutoff_time]

            if not recent_queries:
                return {
                    "total_queries": 0,
                    "avg_response_time_ms": 0,
                    "min_response_time_ms": 0,
                    "max_response_time_ms": 0,
                    "p95_response_time_ms": 0,
                    "slow_queries_count": 0,
                    "error_rate": 0,
                    "connection_count": self.connection_count,
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "query_types": {},
                }

            durations = [q["duration_ms"] for q in recent_queries]
            [q for q in recent_queries if q["success"]]
            errors = [q for q in recent_queries if not q["success"]]

            # حساب percentiles
            sorted_durations = sorted(durations)
            p95_index = int(len(sorted_durations) * 0.95)
            p95_response_time = sorted_durations[p95_index] if p95_index < len(sorted_durations) else 0

            # إحصائيات حسب نوع الاستعلام
            query_types = defaultdict(int)
            for q in recent_queries:
                query_types[q["query_type"]] += 1

            return {
                "total_queries": len(recent_queries),
                "avg_response_time_ms": statistics.mean(durations) if durations else 0,
                "min_response_time_ms": min(durations) if durations else 0,
                "max_response_time_ms": max(durations) if durations else 0,
                "p95_response_time_ms": p95_response_time,
                "slow_queries_count": len(self.slow_queries),
                "error_rate": (len(errors) / len(recent_queries) if recent_queries else 0),
                "connection_count": self.connection_count,
                "max_connections": self.max_connections,
                "query_types": dict(query_types),
                "total_selects": self.total_selects,
                "total_inserts": self.total_inserts,
                "total_updates": self.total_updates,
                "total_deletes": self.total_deletes,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            }

    def get_recent_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على آخر الاستعلامات البطيئة"""
        with self.lock:
            return list(self.slow_queries)[-limit:]

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على آخر الأخطاء"""
        with self.lock:
            return list(self.query_errors)[-limit:]

    def reset(self):
        """إعادة تعيين جميع الإحصائيات"""
        with self.lock:
            self.query_times.clear()
            self.slow_queries.clear()
            self.query_errors.clear()
            self.connection_count = 0
            self.max_connections = 0
            self.total_queries = 0
            self.total_selects = 0
            self.total_inserts = 0
            self.total_updates = 0
            self.total_deletes = 0
            self.lock_wait_times.clear()
            self.start_time = datetime.now()


# Global instance
_metrics_instance: Optional[DatabaseMetrics] = None


def get_database_metrics() -> DatabaseMetrics:
    """الحصول على Database Metrics instance (Singleton)"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = DatabaseMetrics()
    return _metrics_instance

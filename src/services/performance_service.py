"""
خدمة تحسين الأداء والصيانة
Performance Optimization & Maintenance Service
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

from ..core.database_manager import DatabaseManager


class PerformanceMetrics:
    """مقاييس الأداء"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.query_count = 0
        self.avg_query_time_ms = 0.0
        self.cache_hit_rate = 0.0
        self.db_size_mb = 0.0
        self.active_connections = 0


class PerformanceService:
    """خدمة تحسين الأداء والصيانة"""
    
    def __init__(self, db: DatabaseManager, cache_service=None):
        self.db = db
        self.cache = cache_service
        
        # Query performance tracking
        self.query_times = deque(maxlen=1000)
        self.slow_queries = deque(maxlen=100)
        self.slow_query_threshold_ms = 100
        
        # Metrics history (last hour)
        self.metrics_history = deque(maxlen=360)  # 1 per 10 seconds
        
        # Monitoring state
        self._monitoring = False
        self._monitoring_thread = None
    
    # ==================== Database Optimization ====================
    
    def optimize_database(self) -> Dict[str, Any]:
        """تحسين قاعدة البيانات"""
        start_time = time.time()
        results = {}
        
        try:
            # 1. تحليل الجداول
            analyze_result = self._analyze_tables()
            results['analyze'] = analyze_result
            
            # 2. إعادة فهرسة
            reindex_result = self._reindex_database()
            results['reindex'] = reindex_result
            
            # 3. تنظيف (VACUUM)
            vacuum_result = self._vacuum_database()
            results['vacuum'] = vacuum_result
            
            # 4. تحديث الإحصائيات
            stats_result = self._update_statistics()
            results['statistics'] = stats_result
            
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'execution_time': round(execution_time, 2),
                'operations': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def _analyze_tables(self) -> Dict[str, Any]:
        """تحليل جميع الجداول"""
        try:
            tables = self._get_all_tables()
            analyzed = 0
            
            for table in tables:
                self.db.execute_update(f"ANALYZE {table}")
                analyzed += 1
            
            return {
                'success': True,
                'tables_analyzed': analyzed
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _reindex_database(self) -> Dict[str, Any]:
        """إعادة بناء جميع الفهارس"""
        try:
            self.db.execute_update("REINDEX")
            
            return {
                'success': True,
                'message': 'تمت إعادة بناء جميع الفهارس'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _vacuum_database(self) -> Dict[str, Any]:
        """تنظيف وضغط قاعدة البيانات"""
        try:
            # الحصول على الحجم قبل التنظيف
            size_before = Path(self.db.db_path).stat().st_size
            
            # تنفيذ VACUUM
            self.db.execute_update("VACUUM")
            
            # الحصول على الحجم بعد التنظيف
            size_after = Path(self.db.db_path).stat().st_size
            
            return {
                'success': True,
                'size_before_mb': round(size_before / (1024 * 1024), 2),
                'size_after_mb': round(size_after / (1024 * 1024), 2),
                'space_freed_mb': round((size_before - size_after) / (1024 * 1024), 2)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_statistics(self) -> Dict[str, Any]:
        """تحديث إحصائيات قاعدة البيانات"""
        try:
            # تحديث إحصائيات SQLite
            self.db.execute_update("PRAGMA optimize")
            
            return {
                'success': True,
                'message': 'تم تحديث الإحصائيات'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== Database Maintenance ====================
    
    def check_integrity(self) -> Dict[str, Any]:
        """فحص سلامة قاعدة البيانات"""
        try:
            result = self.db.execute_query("PRAGMA integrity_check")
            
            is_ok = len(result) == 1 and result[0].get('integrity_check') == 'ok'
            
            return {
                'success': True,
                'is_healthy': is_ok,
                'checks': result,
                'message': 'قاعدة البيانات سليمة' if is_ok else 'توجد مشاكل في قاعدة البيانات'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def repair_database(self) -> Dict[str, Any]:
        """إصلاح قاعدة البيانات"""
        try:
            # فحص السلامة أولاً
            integrity = self.check_integrity()
            
            if integrity.get('is_healthy'):
                return {
                    'success': True,
                    'message': 'قاعدة البيانات لا تحتاج إلى إصلاح'
                }
            
            # محاولة إصلاح عن طريق VACUUM
            vacuum_result = self._vacuum_database()
            
            # فحص السلامة مرة أخرى
            integrity_after = self.check_integrity()
            
            return {
                'success': integrity_after.get('is_healthy', False),
                'vacuum_result': vacuum_result,
                'integrity_after': integrity_after
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_data(self, days: int = 90) -> Dict[str, Any]:
        """تنظيف البيانات القديمة"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            deleted_count = 0
            
            # حذف سجلات التدقيق القديمة
            audit_deleted = self.db.execute_update(
                "DELETE FROM audit_logs WHERE created_at < ?",
                [cutoff_date]
            )
            deleted_count += audit_deleted
            
            # حذف سجلات تسجيل الدخول القديمة
            login_deleted = self.db.execute_update(
                "DELETE FROM login_history WHERE created_at < ?",
                [cutoff_date]
            )
            deleted_count += login_deleted
            
            # حذف سجلات البحث القديمة
            search_deleted = self.db.execute_update(
                "DELETE FROM search_history WHERE created_at < ?",
                [cutoff_date]
            )
            deleted_count += search_deleted
            
            return {
                'success': True,
                'deleted_records': deleted_count,
                'audit_logs': audit_deleted,
                'login_history': login_deleted,
                'search_history': search_deleted
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== Performance Analysis ====================
    
    def analyze_performance(self) -> Dict[str, Any]:
        """تحليل أداء قاعدة البيانات"""
        try:
            analysis = {}
            
            # حجم قاعدة البيانات
            db_size = Path(self.db.db_path).stat().st_size
            analysis['database_size_mb'] = round(db_size / (1024 * 1024), 2)
            
            # عدد الجداول
            tables = self._get_all_tables()
            analysis['total_tables'] = len(tables)
            
            # حجم كل جدول
            table_sizes = {}
            for table in tables:
                size_result = self.db.execute_query(
                    f"SELECT COUNT(*) as count FROM {table}"
                )
                table_sizes[table] = size_result[0]['count'] if size_result else 0
            
            analysis['table_sizes'] = table_sizes
            analysis['total_records'] = sum(table_sizes.values())
            
            # الجداول الأكبر
            largest_tables = sorted(
                table_sizes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            analysis['largest_tables'] = [
                {'table': table, 'records': count}
                for table, count in largest_tables
            ]
            
            # عدد الفهارس
            indexes = self._get_all_indexes()
            analysis['total_indexes'] = len(indexes)
            
            # إعدادات SQLite
            pragma_settings = self._get_pragma_settings()
            analysis['sqlite_settings'] = pragma_settings
            
            # مساحة غير مستخدمة
            freelist = self.db.execute_query("PRAGMA freelist_count")
            analysis['freelist_pages'] = freelist[0]['freelist_count'] if freelist else 0
            
            page_size = self.db.execute_query("PRAGMA page_size")
            analysis['page_size'] = page_size[0]['page_size'] if page_size else 0
            
            # حساب المساحة القابلة للاستعادة
            if analysis['freelist_pages'] > 0 and analysis['page_size'] > 0:
                reclaimable = (analysis['freelist_pages'] * analysis['page_size']) / (1024 * 1024)
                analysis['reclaimable_space_mb'] = round(reclaimable, 2)
            else:
                analysis['reclaimable_space_mb'] = 0
            
            return {
                'success': True,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على الاستعلامات البطيئة"""
        # ملاحظة: يتطلب تفعيل query logging
        # هذا مثال بسيط - يمكن تحسينه بإضافة نظام logging
        return []
    
    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """إحصائيات جدول معين"""
        try:
            stats = {}
            
            # عدد السجلات
            count_result = self.db.execute_query(
                f"SELECT COUNT(*) as count FROM {table_name}"
            )
            stats['record_count'] = count_result[0]['count'] if count_result else 0
            
            # معلومات الجدول
            table_info = self.db.execute_query(
                f"PRAGMA table_info({table_name})"
            )
            stats['columns'] = [
                {
                    'name': col['name'],
                    'type': col['type'],
                    'not_null': bool(col['notnull']),
                    'default': col['dflt_value'],
                    'primary_key': bool(col['pk'])
                }
                for col in table_info
            ]
            stats['column_count'] = len(table_info)
            
            # الفهارس
            index_list = self.db.execute_query(
                f"PRAGMA index_list({table_name})"
            )
            stats['indexes'] = [
                {
                    'name': idx['name'],
                    'unique': bool(idx['unique']),
                    'origin': idx['origin']
                }
                for idx in index_list
            ]
            stats['index_count'] = len(index_list)
            
            return {
                'success': True,
                'table': table_name,
                'statistics': stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== Helper Methods ====================
    
    def _get_all_tables(self) -> List[str]:
        """الحصول على قائمة جميع الجداول"""
        result = self.db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row['name'] for row in result]
    
    def _get_all_indexes(self) -> List[str]:
        """الحصول على قائمة جميع الفهارس"""
        result = self.db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
        return [row['name'] for row in result]
    
    def _get_pragma_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات PRAGMA"""
        settings = {}
        
        pragma_commands = [
            'journal_mode', 'synchronous', 'cache_size',
            'page_size', 'auto_vacuum', 'temp_store'
        ]
        
        for pragma in pragma_commands:
            try:
                result = self.db.execute_query(f"PRAGMA {pragma}")
                if result:
                    settings[pragma] = result[0].get(pragma, result[0].get(list(result[0].keys())[0]))
            except:
                settings[pragma] = None
        
        return settings
    
    def apply_performance_settings(self) -> Dict[str, Any]:
        """تطبيق إعدادات الأداء الموصى بها"""
        try:
            settings_applied = []
            
            # إعدادات الأداء
            performance_settings = [
                ("PRAGMA journal_mode = WAL", "تفعيل Write-Ahead Logging"),
                ("PRAGMA synchronous = NORMAL", "ضبط التزامن"),
                ("PRAGMA cache_size = -64000", "زيادة حجم الذاكرة المؤقتة"),
                ("PRAGMA temp_store = MEMORY", "تخزين مؤقت في الذاكرة"),
                ("PRAGMA mmap_size = 268435456", "تفعيل memory-mapped I/O")
            ]
            
            for pragma, description in performance_settings:
                try:
                    self.db.execute_update(pragma)
                    settings_applied.append({
                        'setting': pragma,
                        'description': description,
                        'status': 'success'
                    })
                except Exception as e:
                    settings_applied.append({
                        'setting': pragma,
                        'description': description,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'settings_applied': settings_applied
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """معلومات النظام"""
        try:
            import platform
            import psutil
            
            return {
                'success': True,
                'system': {
                    'platform': platform.system(),
                    'platform_release': platform.release(),
                    'platform_version': platform.version(),
                    'architecture': platform.machine(),
                    'processor': platform.processor(),
                    'ram_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                    'ram_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                    'ram_percent': psutil.virtual_memory().percent,
                    'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                    'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                    'disk_percent': psutil.disk_usage('/').percent
                }
            }
        except ImportError:
            return {
                'success': False,
                'error': 'مكتبة psutil غير متوفرة'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== Real-time Monitoring ====================
    
    def start_monitoring(self):
        """بدء المراقبة المستمرة"""
        if self._monitoring:
            return
        
        def monitor_loop():
            self._monitoring = True
            while self._monitoring:
                try:
                    metrics = self.collect_current_metrics()
                    self.metrics_history.append(metrics)
                    time.sleep(10)  # Collect every 10 seconds
                except Exception:
                    pass
        
        self._monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """إيقاف المراقبة"""
        self._monitoring = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
    
    def collect_current_metrics(self) -> PerformanceMetrics:
        """جمع المقاييس الحالية"""
        metrics = PerformanceMetrics()
        
        try:
            # Database size
            db_size = Path(self.db.db_path).stat().st_size
            metrics.db_size_mb = round(db_size / (1024 * 1024), 2)
            
            # Query metrics
            metrics.query_count = len(self.query_times)
            if self.query_times:
                metrics.avg_query_time_ms = sum(self.query_times) / len(self.query_times)
            
            # Cache metrics
            if self.cache:
                cache_stats = self.cache.get_all_stats()
                if '_totals' in cache_stats:
                    metrics.cache_hit_rate = cache_stats['_totals']['overall_hit_rate']
        
        except Exception:
            pass
        
        return metrics
    
    def log_query_time(self, query_time_ms: float, query: str = None):
        """تسجيل وقت استعلام"""
        self.query_times.append(query_time_ms)
        
        # Log slow queries
        if query_time_ms > self.slow_query_threshold_ms and query:
            self.slow_queries.append({
                'timestamp': datetime.now(),
                'duration_ms': query_time_ms,
                'query': query[:200]  # Truncate long queries
            })
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """الحصول على المقاييس الحالية"""
        try:
            import psutil
            
            metrics = self.collect_current_metrics()
            
            return {
                'timestamp': metrics.timestamp.isoformat(),
                'cpu': {
                    'percent': round(psutil.cpu_percent(interval=0.1), 2)
                },
                'memory': {
                    'percent': round(psutil.virtual_memory().percent, 2),
                    'used_mb': round(psutil.virtual_memory().used / (1024 * 1024), 2),
                    'available_mb': round(psutil.virtual_memory().available / (1024 * 1024), 2)
                },
                'database': {
                    'size_mb': metrics.db_size_mb,
                    'query_count': metrics.query_count,
                    'avg_query_time_ms': round(metrics.avg_query_time_ms, 2),
                    'cache_hit_rate': round(metrics.cache_hit_rate, 2)
                }
            }
        except ImportError:
            # Fallback without psutil
            metrics = self.collect_current_metrics()
            return {
                'timestamp': metrics.timestamp.isoformat(),
                'database': {
                    'size_mb': metrics.db_size_mb,
                    'query_count': metrics.query_count,
                    'avg_query_time_ms': round(metrics.avg_query_time_ms, 2),
                    'cache_hit_rate': round(metrics.cache_hit_rate, 2)
                }
            }
    
    def get_metrics_history(self, minutes: int = 60) -> List[Dict]:
        """الحصول على تاريخ المقاييس"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        history = []
        for metrics in self.metrics_history:
            if metrics.timestamp >= cutoff_time:
                history.append({
                    'timestamp': metrics.timestamp.isoformat(),
                    'db_size_mb': metrics.db_size_mb,
                    'query_count': metrics.query_count,
                    'avg_query_time_ms': round(metrics.avg_query_time_ms, 2),
                    'cache_hit_rate': round(metrics.cache_hit_rate, 2)
                })
        
        return history
    
    def get_slow_queries_report(self, limit: int = 20) -> List[Dict]:
        """الحصول على تقرير الاستعلامات البطيئة"""
        slow_queries = list(self.slow_queries)[-limit:]
        
        return [
            {
                'timestamp': q['timestamp'].isoformat(),
                'duration_ms': round(q['duration_ms'], 2),
                'query': q['query']
            }
            for q in slow_queries
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """الحصول على حالة صحة النظام"""
        try:
            import psutil
            
            metrics = self.collect_current_metrics()
            
            health = 'healthy'
            issues = []
            
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > 80:
                health = 'warning'
                issues.append(f'CPU usage high ({cpu_percent:.1f}%)')
            
            # Check Memory
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 85:
                health = 'warning'
                issues.append(f'Memory usage high ({memory_percent:.1f}%)')
            
            # Check Disk
            disk_percent = psutil.disk_usage('.').percent
            if disk_percent > 90:
                health = 'critical'
                issues.append(f'Disk usage critical ({disk_percent:.1f}%)')
            
            # Check query performance
            if metrics.avg_query_time_ms > 200:
                health = 'warning'
                issues.append(f'Slow queries detected (avg {metrics.avg_query_time_ms:.1f}ms)')
            
            # Check cache hit rate
            if metrics.cache_hit_rate > 0 and metrics.cache_hit_rate < 50:
                issues.append(f'Low cache hit rate ({metrics.cache_hit_rate:.1f}%)')
            
            return {
                'status': health,
                'issues': issues,
                'checked_at': datetime.now().isoformat()
            }
        
        except ImportError:
            return {
                'status': 'unknown',
                'issues': ['psutil not available for system monitoring'],
                'checked_at': datetime.now().isoformat()
            }

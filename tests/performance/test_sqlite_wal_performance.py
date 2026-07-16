#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت اختبار SQLite WAL Mode Performance
Test SQLite WAL mode performance with concurrent reads/writes
"""

import sqlite3
import statistics
import sys
import threading
import time
from pathlib import Path  # noqa: F811
from typing import List

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.config_manager import ConfigManager


class PerformanceTest:
    """اختبار أداء SQLite WAL"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.results = {
            "reads": [],
            "writes": [],
            "concurrent_reads": [],
            "concurrent_writes": [],
            "errors": [],
        }

    def test_single_read(self, iterations: int = 100) -> List[float]:
        """اختبار قراءة واحدة"""
        times = []
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row

        try:
            for _ in range(iterations):
                start = time.perf_counter()
                cursor = conn.execute("SELECT COUNT(*) FROM products")
                cursor.fetchone()
                elapsed = (time.perf_counter() - start) * 1000  # ms
                times.append(elapsed)
        finally:
            conn.close()

        return times

    def test_single_write(self, iterations: int = 50) -> List[float]:
        """اختبار كتابة واحدة"""
        times = []
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

        try:
            # إنشاء جدول تجريبي إذا لم يكن موجوداً
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            for i in range(iterations):
                start = time.perf_counter()
                conn.execute("INSERT INTO test_performance (data) VALUES (?)", (f"test_{i}",))
                conn.commit()
                elapsed = (time.perf_counter() - start) * 1000  # ms
                times.append(elapsed)

            # تنظيف
            conn.execute("DELETE FROM test_performance")
            conn.commit()
        finally:
            conn.close()

        return times

    def test_concurrent_reads(self, num_threads: int = 10, iterations_per_thread: int = 20) -> List[float]:
        """اختبار قراءات متزامنة"""
        times = []
        errors = []
        lock = threading.Lock()

        def read_worker(thread_id: int):
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=true")
            conn.row_factory = sqlite3.Row

            try:
                for i in range(iterations_per_thread):
                    try:
                        start = time.perf_counter()
                        cursor = conn.execute("SELECT * FROM products LIMIT 10")
                        cursor.fetchall()
                        elapsed = (time.perf_counter() - start) * 1000

                        with lock:
                            times.append(elapsed)
                    except Exception as e:
                        with lock:
                            errors.append(f"Thread {thread_id}, Iteration {i}: {str(e)}")
            finally:
                conn.close()

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=read_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return times, errors

    def test_concurrent_writes(self, num_threads: int = 3, iterations_per_thread: int = 10) -> List[float]:
        """اختبار كتابات متزامنة"""
        times = []
        errors = []
        lock = threading.Lock()

        # إنشاء جدول تجريبي
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_concurrent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

        def write_worker(thread_id: int):
            conn = sqlite3.connect(self.db_path, timeout=60.0)
            conn.execute("PRAGMA journal_mode=WAL")

            try:
                for i in range(iterations_per_thread):
                    try:
                        start = time.perf_counter()
                        conn.execute(
                            "INSERT INTO test_concurrent (thread_id, data) VALUES (?, ?)",
                            (thread_id, f"data_{i}"),
                        )
                        conn.commit()
                        elapsed = (time.perf_counter() - start) * 1000

                        with lock:
                            times.append(elapsed)
                    except Exception as e:
                        with lock:
                            errors.append(f"Thread {thread_id}, Iteration {i}: {str(e)}")
            finally:
                conn.close()

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=write_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # تنظيف
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("DELETE FROM test_concurrent")
        conn.commit()
        conn.close()

        return times, errors

    def run_all_tests(self):
        """تشغيل جميع الاختبارات"""
        # print("=" * 60)
        # print("🧪 اختبار أداء SQLite WAL Mode")
        # print("=" * 60)
        # print(f"قاعدة البيانات: {self.db_path}")
        # print(f"الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # print()

        # 1. اختبار قراءة واحدة
        # print("1️⃣ اختبار قراءة واحدة (100 iteration)...")
        read_times = self.test_single_read(100)
        self.results["reads"] = read_times
        # print(f"   متوسط: {statistics.mean(read_times):.2f} ms")
        # print(f"   أدنى: {min(read_times):.2f} ms")
        # print(f"   أعلى: {max(read_times):.2f} ms")
        # print(f"   متوسط الوسيط: {statistics.median(read_times):.2f} ms")
        # print()

        # 2. اختبار كتابة واحدة
        # print("2️⃣ اختبار كتابة واحدة (50 iteration)...")
        write_times = self.test_single_write(50)
        self.results["writes"] = write_times
        # print(f"   متوسط: {statistics.mean(write_times):.2f} ms")
        # print(f"   أدنى: {min(write_times):.2f} ms")
        # print(f"   أعلى: {max(write_times):.2f} ms")
        # print(f"   متوسط الوسيط: {statistics.median(write_times):.2f} ms")
        # print()

        # 3. اختبار قراءات متزامنة
        # print("3️⃣ اختبار قراءات متزامنة (10 threads, 20 iterations each)...")
        concurrent_read_times, read_errors = self.test_concurrent_reads(10, 20)
        self.results["concurrent_reads"] = concurrent_read_times
        self.results["errors"].extend(read_errors)
        if concurrent_read_times:
            # print(f"   متوسط: {statistics.mean(concurrent_read_times):.2f} ms")
            pass
            # print(f"   أدنى: {min(concurrent_read_times):.2f} ms")
            # print(f"   أعلى: {max(concurrent_read_times):.2f} ms")
            # print(f"   متوسط الوسيط: {statistics.median(concurrent_read_times):.2f} ms")
        if read_errors:
            # print(f"   ⚠️  {len(read_errors)} أخطاء")
            pass
        # print()

        # 4. اختبار كتابات متزامنة
        # print("4️⃣ اختبار كتابات متزامنة (3 threads, 10 iterations each)...")
        concurrent_write_times, write_errors = self.test_concurrent_writes(3, 10)
        self.results["concurrent_writes"] = concurrent_write_times
        self.results["errors"].extend(write_errors)
        if concurrent_write_times:
            # print(f"   متوسط: {statistics.mean(concurrent_write_times):.2f} ms")
            pass
            # print(f"   أدنى: {min(concurrent_write_times):.2f} ms")
            # print(f"   أعلى: {max(concurrent_write_times):.2f} ms")
            # print(f"   متوسط الوسيط: {statistics.median(concurrent_write_times):.2f} ms")
        if write_errors:
            # print(f"   ⚠️  {len(write_errors)} أخطاء")
            pass
        # print()

        # ملخص النتائج
        # print("=" * 60)
        # print("📊 ملخص النتائج")
        # print("=" * 60)

        # معايير النجاح
        success = True

        # قراءة < 500ms
        avg_read = statistics.mean(self.results["reads"]) if self.results["reads"] else 0
        if avg_read > 500:
            # print(f"❌ متوسط القراءة ({avg_read:.2f} ms) > 500ms")
            success = False
        else:
            # print(f"✅ متوسط القراءة: {avg_read:.2f} ms (< 500ms)")
            pass

        # كتابة < 2000ms
        avg_write = statistics.mean(self.results["writes"]) if self.results["writes"] else 0
        if avg_write > 2000:
            # print(f"❌ متوسط الكتابة ({avg_write:.2f} ms) > 2000ms")
            success = False
        else:
            # print(f"✅ متوسط الكتابة: {avg_write:.2f} ms (< 2000ms)")
            pass

        # لا أخطاء في concurrent
        if self.results["errors"]:
            # print(f"⚠️  {len(self.results['errors'])} أخطاء في الاختبارات المتزامنة")
            for error in self.results["errors"][:5]:  # أول 5 أخطاء فقط
                # print(f"   - {error}")
                pass
            if len(self.results["errors"]) > 5:
                # print(f"   ... و {len(self.results['errors']) - 5} أخطاء أخرى")
                pass
        else:
            # print("✅ لا توجد أخطاء في الاختبارات المتزامنة")
            pass

        # concurrent reads performance
        if self.results["concurrent_reads"]:
            avg_concurrent_read = statistics.mean(self.results["concurrent_reads"])
            if avg_concurrent_read > 1000:
                # print(f"⚠️  متوسط القراءات المتزامنة ({avg_concurrent_read:.2f} ms) مرتفع")
                pass
            else:
                # print(f"✅ متوسط القراءات المتزامنة: {avg_concurrent_read:.2f} ms")
                pass

        # print()
        if success and not self.results["errors"]:
            # print("✅ جميع الاختبارات نجحت!")
            pass
            # print("✅ SQLite WAL mode جاهز للاستخدام مع Desktop + Web")
        else:
            # print("⚠️  بعض الاختبارات فشلت أو أداء بطيء")
            pass
            # print("⚠️  قد تحتاج لمراجعة الإعدادات أو النظر في PostgreSQL")

        # print("=" * 60)


if __name__ == "__main__":
    # الحصول على مسار قاعدة البيانات
    config_manager = ConfigManager()
    config_manager.load_config()
    db_path = config_manager.get_database_path()

    if not Path(db_path).exists():
        # print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        pass
        # print("يرجى تشغيل التطبيق أولاً لإنشاء قاعدة البيانات")
        sys.exit(1)

    # تشغيل الاختبارات
    tester = PerformanceTest(db_path)
    tester.run_all_tests()

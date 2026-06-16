#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت مراقبة اختبار الفوضى (Chaos Test Monitor)
يراقب: ملف WAL، استهلاك CPU، والسجلات
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil


class ChaosTestMonitor:
    """مراقب اختبار الفوضى"""

    def __init__(self, db_path: str = "database.db", log_file: Optional[str] = None):
        self.db_path = Path(db_path)
        self.wal_path = self.db_path.parent / f"{self.db_path.name}-wal"
        self.log_file = log_file
        self.start_time = time.time()
        self.check_interval = 2.0  # فحص كل ثانيتين

    def check_wal_file(self) -> bool:
        """التحقق من وجود ملف WAL"""
        return self.wal_path.exists()

    def get_cpu_usage(self) -> float:
        """الحصول على استهلاك CPU"""
        try:
            return psutil.cpu_percent(interval=0.5)
        except Exception:
            return 0.0

    def get_memory_usage(self) -> dict:
        """الحصول على استهلاك الذاكرة"""
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            return {
                "rss_mb": mem_info.rss / (1024 * 1024),  # Resident Set Size
                "vms_mb": mem_info.vms / (1024 * 1024),  # Virtual Memory Size
                "percent": process.memory_percent(),
            }
        except Exception:
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

    def format_timestamp(self) -> str:
        """تنسيق الطابع الزمني"""
        return datetime.now().strftime("%H:%M:%S")

    def print_status(self, iteration: int):
        """طباعة حالة المراقبة"""
        wal_exists = self.check_wal_file()
        cpu = self.get_cpu_usage()
        mem = self.get_memory_usage()
        elapsed = time.time() - self.start_time  # noqa: F841

        # رموز الحالة
        wal_icon = "✅" if wal_exists else "❌"  # noqa: F841
        cpu_icon = "⚠️" if cpu > 50 else "✅"  # noqa: F841

        # print(f"\n{'='*70}")
        # print(f"📊 حالة المراقبة - التكرار #{iteration} ({self.format_timestamp()})")
        # print(f"{'='*70}")
        # print(f"⏱️  الوقت المنقضي: {elapsed:.1f} ثانية")
        # print("\n📁 ملف WAL:")
        # print(f"   {wal_icon} {'موجود' if wal_exists else 'غير موجود'}")
        # print(f"   المسار: {self.wal_path}")

        # print("\n💻 الموارد:")
        # print(f"   {cpu_icon} CPU: {cpu:.1f}%")
        # print(f"   ✅ RAM: {mem['rss_mb']:.1f} MB (RSS)")
        # print(f"   📊 RAM %: {mem['percent']:.1f}%")

        # تحذيرات
        warnings = []
        if not wal_exists:
            warnings.append("⚠️  ملف WAL غير موجود - WAL mode قد لا يكون مفعلاً")
        if cpu > 50:
            warnings.append(f"⚠️  CPU مرتفع ({cpu:.1f}%) - قد يكون هناك حلقة مفرغة")
        if mem["rss_mb"] > 1000:
            warnings.append(f"⚠️  استهلاك RAM مرتفع ({mem['rss_mb']:.1f} MB)")

        if warnings:
            # print("\n⚠️  تحذيرات:")
            for warning in warnings:
                # print(f"   {warning}")
                pass
        else:
            # print("\n✅ كل شيء طبيعي!")
            pass

        # print(f"{'='*70}\n")

    def monitor_loop(self, duration: int = 120):
        """حلقة المراقبة الرئيسية"""
        # print("🚀 بدء مراقبة اختبار الفوضى...")
        # print(f"⏱️  المدة: {duration} ثانية")
        # print(f"📁 قاعدة البيانات: {self.db_path}")
        # print(f"📁 ملف WAL المتوقع: {self.wal_path}")
        # print("\n💡 اضغط Ctrl+C لإيقاف المراقبة\n")

        iteration = 0
        try:
            while time.time() - self.start_time < duration:
                iteration += 1
                self.print_status(iteration)
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            # print("\n\n⏹️  تم إيقاف المراقبة بواسطة المستخدم")
            pass

        # التقرير النهائي
        self.print_final_report()

    def print_final_report(self):
        """طباعة التقرير النهائي"""
        elapsed = time.time() - self.start_time  # noqa: F841
        wal_exists = self.check_wal_file()
        cpu = self.get_cpu_usage()
        mem = self.get_memory_usage()

        # print(f"\n{'='*70}")
        # print("📊 التقرير النهائي")
        # print(f"{'='*70}")
        # print(f"⏱️  المدة الإجمالية: {elapsed:.1f} ثانية")
        # print(f"📁 ملف WAL: {'✅ موجود' if wal_exists else '❌ غير موجود'}")
        # print(f"💻 CPU النهائي: {cpu:.1f}%")
        # print(f"💾 RAM النهائي: {mem['rss_mb']:.1f} MB")

        # التقييم
        # print("\n🎯 التقييم:")
        if wal_exists and cpu < 30 and mem["rss_mb"] < 500:
            # print("   ✅ ممتاز! النظام يعمل بشكل مثالي")
            pass
        elif wal_exists and cpu < 50:
            # print("   ✅ جيد! النظام مستقر")
            pass
        elif not wal_exists:
            # print("   ⚠️  ملف WAL غير موجود - تحقق من إعدادات SQLite")
            pass
        else:
            # print("   ⚠️  قد تكون هناك مشاكل في الأداء")
            pass

        # print(f"{'='*70}\n")


def main():
    """الدالة الرئيسية"""
    import argparse

    parser = argparse.ArgumentParser(description="مراقب اختبار الفوضى")
    parser.add_argument("--db", default="database.db", help="مسار قاعدة البيانات")
    parser.add_argument("--duration", type=int, default=120, help="مدة المراقبة بالثواني")
    parser.add_argument("--interval", type=float, default=2.0, help="فترة الفحص بالثواني")

    args = parser.parse_args()

    # التحقق من وجود psutil
    try:
        pass
    except ImportError:
        # print("❌ خطأ: psutil غير مثبت")
        pass
        # print("📦 قم بتثبيته: pip install psutil")
        return 1

    # إنشاء المراقب
    monitor = ChaosTestMonitor(db_path=args.db)
    monitor.check_interval = args.interval

    # بدء المراقبة
    monitor.monitor_loop(duration=args.duration)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

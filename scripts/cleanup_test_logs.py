#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تنظيف السجلات القديمة من الاختبارات
Script to clean up old test logs and crash reports
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

def clean_test_crash_reports(logs_dir: Path = None, days_old: int = 7, force_delete_tests: bool = True):
    """
    حذف تقارير الأعطال من الاختبارات
    
    Args:
        logs_dir: مسار مجلد السجلات (افتراضي: logs)
        days_old: عدد الأيام القديمة للحذف (افتراضي: 7 أيام)
        force_delete_tests: حذف ملفات الاختبارات بغض النظر عن التاريخ (افتراضي: True)
    """
    if logs_dir is None:
        logs_dir = Path(__file__).parent.parent / "logs"
    
    crash_reports_dir = logs_dir / "crash_reports"
    
    if not crash_reports_dir.exists():
        print(f"⚠️ مجلد تقارير الأعطال غير موجود: {crash_reports_dir}")
        return 0
    
    deleted_count = 0
    kept_count = 0
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    print(f"🔍 البحث عن تقارير الأعطال من الاختبارات...")
    if force_delete_tests:
        print(f"🗑️  وضع الحذف القسري: سيتم حذف جميع ملفات الاختبارات")
    else:
        print(f"📅 حذف التقارير الأقدم من: {cutoff_date.strftime('%Y-%m-%d')}")
    print("-" * 60)
    
    for crash_file in crash_reports_dir.glob("*.txt"):
        try:
            # قراءة محتوى الملف
            content = crash_file.read_text(encoding='utf-8', errors='ignore')
            
            # التحقق من تاريخ الملف
            file_mtime = datetime.fromtimestamp(crash_file.stat().st_mtime)
            
            # التحقق من أن الملف من الاختبارات
            is_test_file = (
                "test_exception_handler" in content or
                "LogicalVersionError" in content or
                "Test error" in content or
                "tests/unit" in content
            )
            
            # حذف الملف إذا كان من الاختبارات
            if is_test_file:
                if force_delete_tests or file_mtime < cutoff_date:
                    crash_file.unlink()
                    deleted_count += 1
                    print(f"🗑️  حذف: {crash_file.name}")
                else:
                    kept_count += 1
            else:
                kept_count += 1
                
        except Exception as e:
            print(f"⚠️ خطأ في معالجة {crash_file.name}: {e}")
    
    print("-" * 60)
    print(f"✅ تم حذف {deleted_count} ملف")
    print(f"📁 تم الاحتفاظ بـ {kept_count} ملف")
    
    return deleted_count

def clean_old_log_files(logs_dir: Path = None, days_old: int = 30):
    """
    تنظيف ملفات السجلات القديمة
    
    Args:
        logs_dir: مسار مجلد السجلات
        days_old: عدد الأيام القديمة للحذف
    """
    if logs_dir is None:
        logs_dir = Path(__file__).parent.parent / "logs"
    
    if not logs_dir.exists():
        print(f"⚠️ مجلد السجلات غير موجود: {logs_dir}")
        return 0
    
    deleted_count = 0
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    print(f"\n🔍 تنظيف ملفات السجلات القديمة...")
    print(f"📅 حذف الملفات الأقدم من: {cutoff_date.strftime('%Y-%m-%d')}")
    print("-" * 60)
    
    # الملفات التي يجب الاحتفاظ بها دائماً
    keep_files = {
        "__main__.log",
        "database_operations.log",
        "exception_handler.log"
    }
    
    for log_file in logs_dir.glob("*.log"):
        try:
            # تخطي الملفات المهمة
            if log_file.name in keep_files:
                continue
            
            # التحقق من تاريخ الملف
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            # حذف الملف إذا كان قديماً وفارغاً أو صغيراً جداً
            file_size = log_file.stat().st_size
            
            if file_mtime < cutoff_date and (file_size == 0 or file_size < 1024):  # أقل من 1KB
                log_file.unlink()
                deleted_count += 1
                print(f"🗑️  حذف: {log_file.name} ({file_size} bytes)")
                
        except Exception as e:
            print(f"⚠️ خطأ في معالجة {log_file.name}: {e}")
    
    print("-" * 60)
    print(f"✅ تم حذف {deleted_count} ملف سجل")
    
    return deleted_count

if __name__ == "__main__":
    print("=" * 60)
    print("🧹 تنظيف السجلات القديمة")
    print("=" * 60)
    
    # تنظيف تقارير الأعطال من الاختبارات (حذف قسري لملفات الاختبارات)
    test_crashes_deleted = clean_test_crash_reports(days_old=7, force_delete_tests=True)
    
    # تنظيف ملفات السجلات القديمة
    old_logs_deleted = clean_old_log_files(days_old=30)
    
    print("\n" + "=" * 60)
    print(f"✅ اكتمل التنظيف!")
    print(f"📊 الإحصائيات:")
    print(f"   - تقارير أعطال محذوفة: {test_crashes_deleted}")
    print(f"   - ملفات سجلات محذوفة: {old_logs_deleted}")
    print("=" * 60)


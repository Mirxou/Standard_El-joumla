#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت تنظيف ملفات السجلات
يحذف ملفات السجلات القديمة (أكبر من 30 يوم) أو يضغطها
"""

from pathlib import Path
from datetime import datetime, timedelta

def cleanup_logs(logs_dir: str = "logs", days_to_keep: int = 30):
    """تنظيف ملفات السجلات"""
    logs_path = Path(logs_dir)
    
    if not logs_path.exists():
        print(f"⚠️  مجلد السجلات غير موجود: {logs_dir}")
        return
    
    print(f"🔍 فحص ملفات السجلات في: {logs_dir}")
    print(f"📅 سيتم الاحتفاظ بالملفات الأحدث من {days_to_keep} يوم\n")
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    deleted_size = 0
    
    # البحث عن ملفات السجلات
    for log_file in logs_path.rglob("*.log"):
        try:
            # الحصول على تاريخ آخر تعديل
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if mtime < cutoff_date:
                size = log_file.stat().st_size / (1024 * 1024)  # بالميجابايت
                deleted_size += size
                deleted_count += 1
                
                print(f"🗑️  حذف: {log_file.name} ({size:.2f} MB, {mtime.strftime('%Y-%m-%d')})")
                log_file.unlink()
        
        except Exception as e:
            print(f"⚠️  خطأ في معالجة {log_file.name}: {e}")
    
    print(f"\n✅ تم حذف {deleted_count} ملف ({deleted_size:.2f} MB)")
    
    # تنظيف مجلد crash_reports أيضاً
    crash_dir = logs_path / "crash_reports"
    if crash_dir.exists():
        print(f"\n🔍 فحص تقارير الأعطال...")
        crash_count = 0
        crash_size = 0
        
        for crash_file in crash_dir.glob("*.txt"):
            try:
                mtime = datetime.fromtimestamp(crash_file.stat().st_mtime)
                if mtime < cutoff_date:
                    size = crash_file.stat().st_size / 1024  # بالكيلوبايت
                    crash_size += size
                    crash_count += 1
                    crash_file.unlink()
            except Exception:
                pass
        
        if crash_count > 0:
            print(f"🗑️  تم حذف {crash_count} تقرير أعطال ({crash_size:.2f} KB)")

if __name__ == "__main__":
    cleanup_logs()


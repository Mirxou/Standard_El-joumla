#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت مراقبة السجلات الجديدة
Script to monitor logs for new issues
"""

import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import re

class LogMonitor:
    """مراقب السجلات للكشف عن المشاكل الجديدة"""
    
    def __init__(self, logs_dir: Path = None):
        if logs_dir is None:
            logs_dir = Path(__file__).parent.parent / "logs"
        self.logs_dir = logs_dir
        self.last_check_time = datetime.now()
        self.known_errors: Set[str] = set()
        
        # أنماط الأخطاء المهمة
        self.error_patterns = {
            "FOREIGN KEY": r"FOREIGN KEY constraint failed",
            "AttributeError": r"AttributeError:.*has no attribute",
            "ValueError": r"ValueError:.*invalid literal",
            "ImportError": r"ImportError|ModuleNotFoundError",
            "DatabaseError": r"DatabaseError|sqlite3\.",
            "PermissionError": r"PermissionError",
            "FileNotFoundError": r"FileNotFoundError",
        }
    
    def scan_logs(self) -> Dict[str, List[Dict]]:
        """فحص السجلات للعثور على أخطاء جديدة"""
        errors_found = {}
        
        # فحص ملفات السجلات الرئيسية
        log_files = [
            "exception_handler.log",
            "database_operations.log",
            "__main__.log",
            "test_app_errors.log"
        ]
        
        for log_file in log_files:
            file_path = self.logs_dir / log_file
            if file_path.exists():
                errors = self._scan_file(file_path)
                if errors:
                    errors_found[log_file] = errors
        
        # فحص تقارير الأعطال الجديدة
        crash_reports_dir = self.logs_dir / "crash_reports"
        if crash_reports_dir.exists():
            crashes = self._scan_crash_reports(crash_reports_dir)
            if crashes:
                errors_found["crash_reports"] = crashes
        
        return errors_found
    
    def _scan_file(self, file_path: Path) -> List[Dict]:
        """فحص ملف سجل واحد"""
        errors = []
        
        try:
            # قراءة الملف من آخر نقطة فحص
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if file_mtime <= self.last_check_time:
                return errors  # لا توجد تحديثات جديدة
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                for error_type, pattern in self.error_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        error_key = f"{file_path.name}:{i}:{error_type}"
                        
                        # التحقق من أن الخطأ جديد
                        if error_key not in self.known_errors:
                            self.known_errors.add(error_key)
                            errors.append({
                                "type": error_type,
                                "line": i,
                                "message": line.strip(),
                                "file": file_path.name,
                                "timestamp": file_mtime.isoformat()
                            })
        
        except Exception as e:
            print(f"⚠️ خطأ في فحص {file_path}: {e}")
        
        return errors
    
    def _scan_crash_reports(self, crash_dir: Path) -> List[Dict]:
        """فحص تقارير الأعطال الجديدة"""
        crashes = []
        
        try:
            for crash_file in crash_dir.glob("*.txt"):
                file_mtime = datetime.fromtimestamp(crash_file.stat().st_mtime)
                
                if file_mtime > self.last_check_time:
                    content = crash_file.read_text(encoding='utf-8', errors='ignore')
                    
                    # تخطي تقارير الاختبارات
                    if "test_exception_handler" in content or "LogicalVersionError" in content:
                        continue
                    
                    crashes.append({
                        "file": crash_file.name,
                        "timestamp": file_mtime.isoformat(),
                        "size": crash_file.stat().st_size
                    })
        
        except Exception as e:
            print(f"⚠️ خطأ في فحص تقارير الأعطال: {e}")
        
        return crashes
    
    def generate_report(self, errors: Dict[str, List[Dict]]) -> str:
        """إنشاء تقرير عن الأخطاء المكتشفة"""
        if not errors:
            return "✅ لا توجد أخطاء جديدة"
        
        report = []
        report.append("=" * 60)
        report.append("📊 تقرير مراقبة السجلات")
        report.append(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        total_errors = sum(len(errs) for errs in errors.values())
        report.append(f"\n🔴 إجمالي الأخطاء المكتشفة: {total_errors}\n")
        
        for file_name, file_errors in errors.items():
            report.append(f"\n📁 {file_name}: {len(file_errors)} خطأ")
            report.append("-" * 60)
            
            for error in file_errors[:10]:  # عرض أول 10 أخطاء فقط
                if "type" in error:
                    report.append(f"  [{error['type']}] السطر {error['line']}:")
                    report.append(f"    {error['message'][:100]}...")
                else:
                    report.append(f"  تقرير عطل جديد: {error['file']}")
                    report.append(f"    الوقت: {error['timestamp']}")
        
        if total_errors > 10:
            report.append(f"\n... و {total_errors - 10} خطأ آخر")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def update_check_time(self):
        """تحديث وقت آخر فحص"""
        self.last_check_time = datetime.now()

def monitor_continuously(interval: int = 300):
    """مراقبة مستمرة للسجلات"""
    monitor = LogMonitor()
    
    print("🔍 بدء مراقبة السجلات...")
    print(f"⏱️  فترة الفحص: {interval} ثانية")
    print("اضغط Ctrl+C للإيقاف\n")
    
    try:
        while True:
            errors = monitor.scan_logs()
            
            if errors:
                report = monitor.generate_report(errors)
                print(report)
                print("\n" + "⏳ انتظار الفحص التالي...\n")
            else:
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - لا توجد أخطاء جديدة")
            
            monitor.update_check_time()
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n🛑 تم إيقاف المراقبة")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # مراقبة مستمرة
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        monitor_continuously(interval)
    else:
        # فحص واحد
        monitor = LogMonitor()
        errors = monitor.scan_logs()
        report = monitor.generate_report(errors)
        print(report)


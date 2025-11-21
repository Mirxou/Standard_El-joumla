"""
اختبار خدمات النسخ الاحتياطي والأداء
Test Backup and Performance Services
"""

import sys
import os
from pathlib import Path

# إضافة المسار الأساسي للمشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager
from src.services.backup_service import BackupService
from src.services.performance_service import PerformanceService
import time
import tempfile


class Colors:
    """ألوان للطباعة"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.END}\n")


def test_backup_service():
    """اختبار خدمة النسخ الاحتياطي"""
    print_section("اختبار خدمة النسخ الاحتياطي")
    
    try:
        # إنشاء قاعدة بيانات مؤقتة للاختبار
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test.db")
            
            print_info(f"مسار قاعدة البيانات التجريبية: {test_db_path}")
            
            # إنشاء DatabaseManager
            db_manager = DatabaseManager(test_db_path)
            db_manager.initialize()
            
            # إنشاء BackupService
            backup_service = BackupService(db_manager, backup_dir=os.path.join(temp_dir, "backups"))
            
            # Test 1: إنشاء نسخة احتياطية
            print_info("Test 1: إنشاء نسخة احتياطية...")
            backup_name = backup_service.create_backup(
                description="نسخة اختبار 1",
                include_attachments=False,
                compress=True
            )
            print_success(f"تم إنشاء النسخة: {backup_name}")
            
            # Test 2: قائمة النسخ الاحتياطية
            print_info("Test 2: قائمة النسخ الاحتياطية...")
            backups = backup_service.list_backups()
            assert len(backups) == 1, "يجب أن يكون هناك نسخة واحدة"
            expected_name = backup_name['backup_name'] if isinstance(backup_name, dict) else backup_name
            assert backups[0]['name'] == expected_name, f"اسم النسخة غير صحيح: {backups[0]['name']} != {expected_name}"
            print_success(f"تم العثور على {len(backups)} نسخة احتياطية")
            
            # Test 3: إحصائيات النسخ
            print_info("Test 3: إحصائيات النسخ الاحتياطية...")
            stats = backup_service.get_backup_statistics()
            assert stats['total_backups'] == 1, "إحصائيات خاطئة"
            assert stats['total_size'] > 0, "حجم النسخة يجب أن يكون أكبر من 0"
            print_success(f"إجمالي النسخ: {stats['total_backups']}, الحجم: {stats['total_size']} بايت")
            
            # Test 4: إنشاء نسخة ثانية
            print_info("Test 4: إنشاء نسخة احتياطية ثانية...")
            time.sleep(1)  # للتأكد من اختلاف الوقت
            backup_name2 = backup_service.create_backup(
                description="نسخة اختبار 2",
                include_attachments=False,
                compress=True
            )
            print_success(f"تم إنشاء النسخة: {backup_name2}")
            
            # Test 5: حذف نسخة
            print_info("Test 5: حذف نسخة احتياطية...")
            delete_name = backup_name['backup_name'] if isinstance(backup_name, dict) else backup_name
            backup_service.delete_backup(delete_name)
            backups = backup_service.list_backups()
            assert len(backups) == 1, "يجب أن تبقى نسخة واحدة فقط"
            print_success("تم حذف النسخة بنجاح")
            
            # Test 6: استعادة نسخة
            print_info("Test 6: استعادة نسخة احتياطية...")
            # إجراء تعديل على قاعدة البيانات
            cursor = db_manager.connection.cursor()
            cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO test_table (name) VALUES ('test')")
            db_manager.connection.commit()
            
            # استعادة النسخة
            restore_name = backup_name2['backup_name'] if isinstance(backup_name2, dict) else backup_name2
            backup_service.restore_backup(restore_name, restore_attachments=False)
            
            # التحقق من أن الجدول تم حذفه
            cursor = db_manager.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
            result = cursor.fetchone()
            assert result is None, "الجدول يجب أن يكون محذوفاً بعد الاستعادة"
            print_success("تم استعادة النسخة بنجاح")
            
            # Test 7: تنظيف النسخ القديمة
            print_info("Test 7: تنظيف النسخ القديمة...")
            # إنشاء عدة نسخ
            for i in range(5):
                backup_service.create_backup(
                    description=f"نسخة {i}",
                    include_attachments=False,
                    compress=True
                )
                time.sleep(0.1)
            
            backups_before = len(backup_service.list_backups())
            print_info(f"عدد النسخ قبل التنظيف: {backups_before}")
            
            backup_service.cleanup_old_backups(keep_count=3)
            backups_after = len(backup_service.list_backups())
            print_info(f"عدد النسخ بعد التنظيف: {backups_after}")
            
            assert backups_after <= 3, "يجب أن يبقى 3 نسخ فقط"
            print_success(f"تم التنظيف: {backups_before} → {backups_after} نسخة")
            
            # Test 8: تصدير البيانات
            print_info("Test 8: تصدير البيانات...")
            export_path = os.path.join(temp_dir, "export.json")
            
            # إنشاء جدول للتصدير
            cursor = db_manager.connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS export_test (id INTEGER PRIMARY KEY, data TEXT)")
            cursor.execute("INSERT INTO export_test (data) VALUES ('test1'), ('test2')")
            db_manager.connection.commit()
            
            backup_service.export_data(
                tables=['export_test'],
                output_path=export_path,
                format='json'
            )
            
            assert os.path.exists(export_path), "ملف التصدير يجب أن يكون موجوداً"
            print_success("تم تصدير البيانات بنجاح")
            
            print_section("✓ اختبار خدمة النسخ الاحتياطي مكتمل")
            
            # إغلاق الاتصال بقاعدة البيانات قبل الخروج
            db_manager.connection.close()
            return True
            
    except Exception as e:
        print_error(f"فشل اختبار النسخ الاحتياطي: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_service():
    """اختبار خدمة الأداء"""
    print_section("اختبار خدمة الأداء")
    
    try:
        # إنشاء قاعدة بيانات مؤقتة للاختبار
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_perf.db")
            
            print_info(f"مسار قاعدة البيانات التجريبية: {test_db_path}")
            
            # إنشاء DatabaseManager
            db_manager = DatabaseManager(test_db_path)
            db_manager.initialize()
            
            # إنشاء PerformanceService
            perf_service = PerformanceService(db_manager)
            
            # إنشاء بيانات تجريبية
            cursor = db_manager.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_data (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value INTEGER
                )
            """)
            cursor.execute("CREATE INDEX idx_test_name ON test_data(name)")
            
            # إدخال بيانات
            for i in range(100):
                cursor.execute(
                    "INSERT INTO test_data (name, value) VALUES (?, ?)",
                    (f"Item {i}", i)
                )
            db_manager.connection.commit()
            
            # Test 1: تطبيق إعدادات الأداء
            print_info("Test 1: تطبيق إعدادات الأداء...")
            perf_service.apply_performance_settings()
            
            # التحقق من إعدادات WAL
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            assert journal_mode.upper() == 'WAL', f"يجب أن يكون WAL، وجد: {journal_mode}"
            print_success("تم تطبيق إعدادات الأداء بنجاح")
            
            # Test 2: فحص السلامة
            print_info("Test 2: فحص سلامة قاعدة البيانات...")
            integrity_ok = perf_service.check_integrity()
            assert integrity_ok, "قاعدة البيانات يجب أن تكون سليمة"
            print_success("قاعدة البيانات سليمة")
            
            # Test 3: تحليل الأداء
            print_info("Test 3: تحليل الأداء...")
            analysis = perf_service.analyze_performance()
            
            assert 'database_size_mb' in analysis, "يجب أن يحتوي على حجم قاعدة البيانات"
            assert 'table_count' in analysis, "يجب أن يحتوي على عدد الجداول"
            assert 'index_count' in analysis, "يجب أن يحتوي على عدد الفهارس"
            assert 'largest_tables' in analysis, "يجب أن يحتوي على أكبر الجداول"
            
            print_success(f"حجم قاعدة البيانات: {analysis['database_size_mb']:.2f} MB")
            print_success(f"عدد الجداول: {analysis['table_count']}")
            print_success(f"عدد الفهارس: {analysis['index_count']}")
            
            # Test 4: إحصائيات الجداول
            print_info("Test 4: الحصول على إحصائيات جدول...")
            table_stats = perf_service.get_table_statistics('test_data')
            
            assert table_stats is not None, "يجب أن تكون الإحصائيات موجودة"
            assert 'row_count' in table_stats, "يجب أن يحتوي على عدد الصفوف"
            assert table_stats['row_count'] == 100, f"عدد الصفوف يجب أن يكون 100، وجد: {table_stats['row_count']}"
            
            print_success(f"عدد الصفوف في test_data: {table_stats['row_count']}")
            print_success(f"عدد الأعمدة: {len(table_stats['columns'])}")
            print_success(f"عدد الفهارس: {len(table_stats['indexes'])}")
            
            # Test 5: تحسين قاعدة البيانات
            print_info("Test 5: تحسين قاعدة البيانات...")
            start_time = time.time()
            perf_service.optimize_database()
            elapsed = time.time() - start_time
            print_success(f"تم التحسين في {elapsed:.2f} ثانية")
            
            # Test 6: معلومات النظام
            print_info("Test 6: الحصول على معلومات النظام...")
            system_info = perf_service.get_system_info()
            
            assert 'memory_total_gb' in system_info, "يجب أن يحتوي على إجمالي الذاكرة"
            assert 'memory_available_gb' in system_info, "يجب أن يحتوي على الذاكرة المتاحة"
            assert 'disk_total_gb' in system_info, "يجب أن يحتوي على إجمالي القرص"
            
            print_success(f"إجمالي الذاكرة: {system_info['memory_total_gb']:.2f} GB")
            print_success(f"الذاكرة المتاحة: {system_info['memory_available_gb']:.2f} GB")
            print_success(f"مساحة القرص الحرة: {system_info['disk_free_gb']:.2f} GB")
            
            # Test 7: حذف البيانات القديمة
            print_info("Test 7: حذف البيانات القديمة...")
            
            # إنشاء جداول تدقيق بسيطة للاختبار
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action TEXT
                )
            """)
            cursor.execute("""
                INSERT INTO audit_logs (created_at, action)
                VALUES (date('now', '-100 days'), 'test1'),
                       (date('now', '-50 days'), 'test2'),
                       (date('now', '-10 days'), 'test3')
            """)
            db_manager.connection.commit()
            
            deleted = perf_service.cleanup_data(days=60)
            print_success(f"تم حذف {deleted} سجل قديم")
            
            # التحقق من الحذف
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            remaining = cursor.fetchone()[0]
            print_info(f"السجلات المتبقية: {remaining}")
            
            # Test 8: إصلاح قاعدة البيانات
            print_info("Test 8: إصلاح قاعدة البيانات...")
            perf_service.repair_database()
            print_success("تم إصلاح قاعدة البيانات بنجاح")
            
            # التحقق من السلامة بعد الإصلاح
            integrity_ok = perf_service.check_integrity()
            assert integrity_ok, "قاعدة البيانات يجب أن تكون سليمة بعد الإصلاح"
            print_success("قاعدة البيانات سليمة بعد الإصلاح")
            
            print_section("✓ اختبار خدمة الأداء مكتمل")
            
            # إغلاق الاتصال بقاعدة البيانات قبل الخروج
            db_manager.connection.close()
            return True
            
    except Exception as e:
        print_error(f"فشل اختبار الأداء: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """اختبار التكامل بين الخدمات"""
    print_section("اختبار التكامل")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_integration.db")
            
            print_info(f"مسار قاعدة البيانات التجريبية: {test_db_path}")
            
            # إنشاء الخدمات
            db_manager = DatabaseManager(test_db_path)
            db_manager.initialize()
            
            backup_service = BackupService(db_manager, backup_dir=os.path.join(temp_dir, "backups"))
            perf_service = PerformanceService(db_manager)
            
            # Test 1: تحسين ثم نسخ احتياطي
            print_info("Test 1: تحسين قاعدة البيانات ثم إنشاء نسخة احتياطية...")
            
            perf_service.optimize_database()
            print_success("تم التحسين")
            
            backup_name = backup_service.create_backup(
                description="نسخة بعد التحسين",
                compress=True
            )
            print_success(f"تم إنشاء النسخة: {backup_name}")
            
            # Test 2: إجراء تعديلات ثم استعادة
            print_info("Test 2: إجراء تعديلات ثم استعادة النسخة...")
            
            cursor = db_manager.connection.cursor()
            cursor.execute("CREATE TABLE temp_table (id INTEGER)")
            cursor.execute("INSERT INTO temp_table VALUES (1), (2), (3)")
            db_manager.connection.commit()
            
            # استعادة النسخة
            restore_name = backup_name['backup_name'] if isinstance(backup_name, dict) else backup_name
            backup_service.restore_backup(restore_name)
            
            # التحقق من حذف الجدول
            cursor = db_manager.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temp_table'")
            result = cursor.fetchone()
            assert result is None, "الجدول يجب أن يكون محذوفاً"
            print_success("تم الاستعادة بنجاح")
            
            # Test 3: فحص السلامة بعد الاستعادة
            print_info("Test 3: فحص السلامة بعد الاستعادة...")
            integrity_ok = perf_service.check_integrity()
            assert integrity_ok, "قاعدة البيانات يجب أن تكون سليمة"
            print_success("قاعدة البيانات سليمة")
            
            # Test 4: تحليل الأداء
            print_info("Test 4: تحليل الأداء النهائي...")
            analysis = perf_service.analyze_performance()
            print_success(f"حجم قاعدة البيانات: {analysis['database_size_mb']:.2f} MB")
            print_success(f"عدد الجداول: {analysis['table_count']}")
            
            print_section("✓ اختبار التكامل مكتمل")
            
            # إغلاق الاتصال بقاعدة البيانات قبل الخروج
            db_manager.connection.close()
            return True
            
    except Exception as e:
        print_error(f"فشل اختبار التكامل: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """تشغيل جميع الاختبارات"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("  اختبار خدمات النسخ الاحتياطي والأداء")
    print("  Backup and Performance Services Test Suite")
    print("="*60)
    print(f"{Colors.END}\n")
    
    results = []
    
    # تشغيل الاختبارات
    results.append(("خدمة النسخ الاحتياطي", test_backup_service()))
    results.append(("خدمة الأداء", test_performance_service()))
    results.append(("اختبار التكامل", test_integration()))
    
    # عرض الملخص
    print_section("ملخص الاختبارات")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    for name, success in results:
        status = "✓ نجح" if success else "✗ فشل"
        color = Colors.GREEN if success else Colors.RED
        print(f"{color}{status}{Colors.END} - {name}")
    
    print(f"\n{Colors.BOLD}الإجمالي: {total} اختبار{Colors.END}")
    print(f"{Colors.GREEN}✓ نجح: {passed}{Colors.END}")
    
    if failed > 0:
        print(f"{Colors.RED}✗ فشل: {failed}{Colors.END}")
        sys.exit(1)
    else:
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
        print("  جميع الاختبارات نجحت!")
        print("  All Tests Passed!")
        print(f"{'='*60}{Colors.END}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

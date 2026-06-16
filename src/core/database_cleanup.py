import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Cleanup Service
خدمة تنظيف قاعدة البيانات والأرشفة الدورية
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from src.core.local_database_manager import LocalDatabaseManager
from src.utils.logger import setup_logger


class DatabaseCleanup:
    """خدمة تنظيف قاعدة البيانات"""

    def __init__(self, local_db: LocalDatabaseManager):
        self.local_db = local_db
        self.logger = setup_logger(__name__)

    def archive_old_sales(self, years: int = 3) -> int:
        """
        أرشفة المبيعات القديمة

        Args:
            years: عدد السنوات (افتراضي: 3)

        Returns:
            عدد السجلات المؤرشفة
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=years * 365)

            # إنشاء جدول الأرشيف إذا لم يكن موجوداً
            self.local_db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS archived_sales (
                    id INTEGER PRIMARY KEY,
                    invoice_number TEXT,
                    customer_id INTEGER,
                    total_amount DECIMAL(10,2),
                    discount_amount DECIMAL(10,2),
                    final_amount DECIMAL(10,2),
                    payment_method TEXT,
                    sale_date DATE,
                    user_id INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # نقل البيانات القديمة
            with self.local_db.transaction():
                # نسخ البيانات
                self.local_db.execute_non_query(
                    """
                    INSERT INTO archived_sales
                    (id, invoice_number, customer_id, total_amount, discount_amount,
                     final_amount, payment_method, sale_date, user_id, notes,
                     created_at, updated_at)
                    SELECT id, invoice_number, customer_id, total_amount, discount_amount,
                           final_amount, payment_method, sale_date, user_id, notes,
                           created_at, updated_at
                    FROM sales
                    WHERE sale_date < ? AND is_deleted = 0
                """,
                    (cutoff_date.date().isoformat(),),
                )

                # حذف البيانات القديمة (Soft Delete)
                count = self.local_db.execute_non_query(
                    """
                    UPDATE sales
                    SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP
                    WHERE sale_date < ? AND is_deleted = 0
                """,
                    (cutoff_date.date().isoformat(),),
                )

            self.logger.info(f"✅ تم أرشفة {count} مبيعة قديمة")
            return count

        except Exception as e:
            self.logger.error(f"❌ فشل أرشفة المبيعات: {str(e)}")
            return 0

    def vacuum(self) -> bool:
        """
        تشغيل VACUUM لتحسين الأداء

        Returns:
            True إذا نجح VACUUM
        """
        try:
            self.local_db.execute_non_query("VACUUM")
            self.logger.info("✅ تم تشغيل VACUUM بنجاح")
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل VACUUM: {str(e)}")
            return False

    def cleanup_old_audit_logs(self, days: int = 365) -> int:
        """
        تنظيف سجلات Audit Trail القديمة (اختياري - عادة لا يتم حذفها)

        Args:
            days: عدد الأيام (افتراضي: 365)

        Returns:
            عدد السجلات المحذوفة
        """
        # ملاحظة: Audit Trail عادة لا يتم حذفه
        # هذه الدالة للاستخدام في حالات خاصة فقط
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # حذف السجلات القديمة جداً (فقط إذا كان هناك سياسة واضحة)
            count = self.local_db.execute_non_query(
                """
                DELETE FROM audit_logs
                WHERE timestamp < ?
            """,
                (cutoff_date.isoformat(),),
            )

            self.logger.info(f"✅ تم تنظيف {count} سجل Audit Trail قديم")
            return count

        except Exception as e:
            self.logger.error(f"❌ فشل تنظيف Audit Logs: {str(e)}")
            return 0

    def run_cleanup(self, archive_years: int = 3, vacuum: bool = True) -> Dict[str, Any]:
        """
        تشغيل تنظيف شامل

        Args:
            archive_years: عدد السنوات للأرشفة
            vacuum: تشغيل VACUUM

        Returns:
            نتيجة التنظيف
        """
        result = {"archived_sales": 0, "vacuum_success": False, "errors": []}

        try:
            # أرشفة المبيعات القديمة
            result["archived_sales"] = self.archive_old_sales(archive_years)

            # VACUUM
            if vacuum:
                result["vacuum_success"] = self.vacuum()

            self.logger.info("✅ تم التنظيف بنجاح")

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"❌ فشل التنظيف: {str(e)}")

        return result

import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Repository - Repository Pattern
الكلاس الأساسي لجميع Repositories
"""

from abc import ABC
from typing import Any, Dict, List, Optional

from src.core.local_database_manager import LocalDatabaseManager
from src.utils.logger import setup_logger


class BaseRepository(ABC):
    """الكلاس الأساسي لجميع Repositories"""

    def __init__(self, db_manager: LocalDatabaseManager, table_name: str):
        """
        تهيئة Repository

        Args:
            db_manager: مدير قاعدة البيانات المحلية
            table_name: اسم الجدول
        """
        self.db = db_manager
        self.table_name = table_name
        self.logger = setup_logger(__name__)

    def find_by_id(self, record_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """
        البحث عن سجل بالمعرف

        Args:
            record_id: معرف السجل
            include_deleted: تضمين السجلات المحذوفة منطقياً

        Returns:
            السجل أو None إذا لم يوجد
        """
        deleted_filter = "" if include_deleted else "AND is_deleted = 0"
        results = self.db.execute_query(
            f"SELECT * FROM {self.table_name} WHERE id = ? {deleted_filter}",
            (record_id,),
            exclude_deleted=not include_deleted,
        )
        return results[0] if results else None

    def find_all(
        self,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        الحصول على جميع السجلات

        Args:
            include_deleted: تضمين السجلات المحذوفة منطقياً
            limit: حد أقصى لعدد السجلات
            offset: إزاحة

        Returns:
            قائمة بالسجلات
        """
        deleted_filter = "" if include_deleted else "AND is_deleted = 0"
        limit_clause = f"LIMIT {limit}" if limit else ""
        offset_clause = f"OFFSET {offset}" if offset > 0 else ""

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE 1=1 {deleted_filter}
            ORDER BY id DESC
            {limit_clause} {offset_clause}
        """
        return self.db.execute_query(query, exclude_deleted=not include_deleted)

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """فحص البيانات وتطهيرها من حقول غير صالحة لمنع SQL Injection"""
        try:
            cursor = self.db.connection.execute(f'PRAGMA table_info("{self.table_name}")')
            allowed_columns = {row[1] for row in cursor.fetchall()}
            return {k: v for k, v in data.items() if k in allowed_columns}
        except Exception as e:
            self.logger.warning(f"⚠️ فشل التحقق من الأعمدة: {e}")
            return {}

    def create(self, data: Dict[str, Any]) -> int:
        """
        إنشاء سجل جديد

        Args:
            data: بيانات السجل

        Returns:
            معرف السجل الجديد
        """
        # إزالة id من البيانات إذا كان موجوداً (سيتم توليده تلقائياً)
        data = {k: v for k, v in data.items() if k != "id"}

        # إضافة is_synced = 0 و is_deleted = 0
        data.setdefault("is_synced", 0)
        data.setdefault("is_deleted", 0)

        # تطهير البيانات لمنع ثغرات حقن الاستعلامات
        data = self._sanitize_data(data)
        if not data:
            raise ValueError("No valid columns provided for creation")

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())

        query = f"""
            INSERT INTO {self.table_name} ({columns})
            VALUES ({placeholders})
        """

        cursor = self.db.connection.execute(query, values)
        self.db.connection.commit()
        return cursor.lastrowid

    def update(self, record_id: int, data: Dict[str, Any], use_lock: bool = True) -> bool:
        """
        تحديث سجل مع Row-level Locking

        Args:
            record_id: معرف السجل
            data: البيانات المحدثة
            use_lock: استخدام Row-level Locking (افتراضي: True)

        Returns:
            True إذا نجح التحديث
        """
        # إزالة id و is_synced من البيانات
        data = {k: v for k, v in data.items() if k not in ["id", "is_synced"]}

        # تعيين is_synced = 0 عند التحديث
        data["is_synced"] = 0

        # تطهير البيانات لمنع ثغرات حقن الاستعلامات
        data = self._sanitize_data(data)

        if not data:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = tuple(data.values()) + (record_id,)

        try:
            with self.db.transaction():
                # Row-level Locking
                if use_lock:
                    if not self.db.lock_row(self.table_name, record_id):
                        self.logger.warning(f"⚠️ فشل قفل الصف: {self.table_name}.{record_id}")
                        return False

                query = f"""
                    UPDATE {self.table_name}
                    SET {set_clause}
                    WHERE id = ? AND is_deleted = 0
                """
                self.db.execute_non_query(query, values)

            self.logger.info(f"✅ تم تحديث السجل: {self.table_name}.{record_id}")
            return True
        except Exception as e:
            self.logger.warning(f"❌ فشل تحديث السجل: {str(e)}")
            return False

    def delete(self, record_id: int, hard_delete: bool = False) -> bool:
        """
        حذف سجل (Soft Delete افتراضياً)

        Args:
            record_id: معرف السجل
            hard_delete: حذف فعلي (غير مستحسن - يجب استخدام Soft Delete)

        Returns:
            True إذا نجح الحذف
        """
        if hard_delete:
            self.logger.warning(f"⚠️ Hard Delete مستخدم - غير مستحسن: {self.table_name}.{record_id}")
            query = f"DELETE FROM {self.table_name} WHERE id = ?"
            self.db.execute_non_query(query, (record_id,))
            return True
        else:
            # Soft Delete
            return self.db.soft_delete(self.table_name, record_id)

    def restore(self, record_id: int) -> bool:
        """
        استعادة سجل محذوف منطقياً

        Args:
            record_id: معرف السجل

        Returns:
            True إذا نجحت الاستعادة
        """
        return self.db.restore_deleted(self.table_name, record_id)

    def count(self, include_deleted: bool = False) -> int:
        """
        عدد السجلات

        Args:
            include_deleted: تضمين السجلات المحذوفة منطقياً

        Returns:
            عدد السجلات
        """
        deleted_filter = "" if include_deleted else "AND is_deleted = 0"
        results = self.db.execute_query(
            f"SELECT COUNT(*) as count FROM {self.table_name} WHERE 1=1 {deleted_filter}",
            exclude_deleted=not include_deleted,
        )
        return results[0]["count"] if results else 0

    def find_pending_sync(self) -> List[Dict[str, Any]]:
        """
        الحصول على السجلات المعلقة (غير المتزامنة)

        Returns:
            قائمة بالسجلات المعلقة
        """
        return self.db.get_pending_items(self.table_name, include_deleted=True)

    def mark_as_synced(self, record_id: int, sync_version: int = 1):
        """
        تعليم سجل كمتزامن

        Args:
            record_id: معرف السجل
            sync_version: إصدار المزامنة
        """
        self.db.mark_as_synced(self.table_name, record_id, sync_version)

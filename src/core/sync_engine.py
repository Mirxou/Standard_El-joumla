import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Engine - محرك المزامنة
يدير عملية المزامنة بين النظام المحلي والسحابة
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """اتجاه المزامنة"""

    UP = "UP"  # رفع إلى السحابة
    DOWN = "DOWN"  # تنزيل من السحابة
    BOTH = "BOTH"  # مزامنة ثنائية


class SyncStatus(Enum):
    """حالة المزامنة"""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CONFLICT = "CONFLICT"


@dataclass
class SyncResult:
    """نتيجة المزامنة"""

    success: bool
    status: SyncStatus
    direction: SyncDirection
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    local_hash: Optional[str] = None
    remote_hash: Optional[str] = None
    conflict_detected: bool = False
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    data_size_bytes: Optional[int] = None


class SyncEngine:
    """محرك المزامنة"""

    def __init__(self, db_manager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة محرك المزامنة

        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger

    def calculate_hash(self, data: Dict[str, Any]) -> str:
        """
        حساب Hash للبيانات

        Args:
            data: البيانات المراد حساب Hash لها

        Returns:
            str: Hash (SHA256)
        """
        try:
            # تحويل البيانات إلى JSON مرتب
            json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
            # حساب Hash
            hash_obj = hashlib.sha256(json_str.encode("utf-8"))
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.warning(f"❌ خطأ في حساب Hash: {e}", exc_info=True)
            return ""

    def compare_versions(self, local_version: int, remote_version: int) -> str:
        """
        مقارنة الإصدارات

        Returns:
            str: "LOCAL_NEWER", "REMOTE_NEWER", "SAME", "CONFLICT"
        """
        if local_version > remote_version:
            return "LOCAL_NEWER"
        elif remote_version > local_version:
            return "REMOTE_NEWER"
        elif local_version == remote_version:
            return "SAME"
        else:
            return "CONFLICT"

    def detect_conflict(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any],
        local_version: int,
        remote_version: int,
    ) -> bool:
        """
        اكتشاف التعارض

        Args:
            local_data: البيانات المحلية
            remote_data: البيانات السحابية
            local_version: الإصدار المحلي
            remote_version: الإصدار السحابي

        Returns:
            bool: True إذا كان هناك تعارض
        """
        try:
            # إذا كانت إحدى البيانات مفقودة، فلا يوجد تعارض (ربما إضافة جديدة)
            if local_data is None or remote_data is None:
                return False

            # حساب Hash
            local_hash = self.calculate_hash(local_data)
            remote_hash = self.calculate_hash(remote_data)

            # إذا كانت Hashes مختلفة، نتحقق من الإصدارات
            if local_hash != remote_hash:
                version_comparison = self.compare_versions(local_version, remote_version)
                if version_comparison == "SAME" or version_comparison == "CONFLICT":
                    return True

            return False

        except Exception as e:
            self.logger.warning(f"❌ خطأ في اكتشاف التعارض: {e}", exc_info=True)
            return False

    def sync_entity(
        self,
        entity_type: str,
        entity_id: int,
        local_data: Dict[str, Any],
        remote_data: Optional[Dict[str, Any]],
        local_version: int,
        remote_version: int,
        direction: SyncDirection = SyncDirection.BOTH,
    ) -> SyncResult:
        """
        مزامنة كيان

        Args:
            entity_type: نوع الكيان
            entity_id: معرف الكيان
            local_data: البيانات المحلية
            remote_data: البيانات السحابية (None إذا لم تكن موجودة)
            local_version: الإصدار المحلي
            remote_version: الإصدار السحابي
            direction: اتجاه المزامنة

        Returns:
            SyncResult: نتيجة المزامنة
        """
        start_time = datetime.now()

        try:
            # حساب Hashes
            local_hash = self.calculate_hash(local_data)
            remote_hash = self.calculate_hash(remote_data) if remote_data else None

            # اكتشاف التعارض
            conflict_detected = False
            if remote_data and local_data:
                conflict_detected = self.detect_conflict(local_data, remote_data, local_version, remote_version)

            if conflict_detected:
                return SyncResult(
                    success=False,
                    status=SyncStatus.CONFLICT,
                    direction=direction,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    local_hash=local_hash,
                    remote_hash=remote_hash,
                    conflict_detected=True,
                    execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                )

            # تحديد الاتجاه
            if direction == SyncDirection.UP or (direction == SyncDirection.BOTH and local_version > remote_version):
                # رفع إلى السحابة
                status = SyncStatus.SUCCESS
                success = True
            elif direction == SyncDirection.DOWN or (
                direction == SyncDirection.BOTH and remote_version > local_version
            ):
                # تنزيل من السحابة
                status = SyncStatus.SUCCESS
                success = True
            else:
                # لا حاجة للمزامنة
                status = SyncStatus.SUCCESS
                success = True

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            data_size = len(json.dumps(local_data, ensure_ascii=False).encode("utf-8"))

            return SyncResult(
                success=success,
                status=status,
                direction=direction,
                entity_type=entity_type,
                entity_id=entity_id,
                local_hash=local_hash,
                remote_hash=remote_hash,
                conflict_detected=False,
                execution_time_ms=execution_time,
                data_size_bytes=data_size,
            )

        except Exception as e:
            self.logger.warning(f"❌ خطأ في مزامنة الكيان: {e}", exc_info=True)
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                direction=direction,
                entity_type=entity_type,
                entity_id=entity_id,
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )

    def get_sync_state(self, sync_settings_id: int, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على حالة المزامنة"""
        try:
            query = """
                SELECT * FROM sync_state
                WHERE sync_settings_id = ? AND entity_type = ? AND entity_id = ?
            """

            row = self.db_manager.fetch_one(query, (sync_settings_id, entity_type, entity_id))
            return dict(row) if row else None

        except Exception as e:
            self.logger.warning(f"❌ خطأ في الحصول على حالة المزامنة: {e}", exc_info=True)
            return None

    def update_sync_state(
        self,
        sync_settings_id: int,
        entity_type: str,
        entity_id: int,
        local_version: int,
        remote_version: int,
        local_hash: str,
        remote_hash: str,
    ):
        """تحديث حالة المزامنة"""
        try:
            # التحقق من وجود السجل
            existing = self.get_sync_state(sync_settings_id, entity_type, entity_id)

            if existing:
                # تحديث
                query = """
                    UPDATE sync_state SET
                        local_version = ?, remote_version = ?,
                        local_hash = ?, remote_hash = ?,
                        last_synced_at = CURRENT_TIMESTAMP
                    WHERE sync_settings_id = ? AND entity_type = ? AND entity_id = ?
                """
                self.db_manager.execute_query(
                    query,
                    (
                        local_version,
                        remote_version,
                        local_hash,
                        remote_hash,
                        sync_settings_id,
                        entity_type,
                        entity_id,
                    ),
                )
            else:
                # إدراج جديد
                query = """
                    INSERT INTO sync_state (
                        sync_settings_id, entity_type, entity_id,
                        local_version, remote_version,
                        local_hash, remote_hash, last_synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """
                self.db_manager.execute_query(
                    query,
                    (
                        sync_settings_id,
                        entity_type,
                        entity_id,
                        local_version,
                        remote_version,
                        local_hash,
                        remote_hash,
                    ),
                )

        except Exception as e:
            self.logger.warning(f"❌ خطأ في تحديث حالة المزامنة: {e}", exc_info=True)

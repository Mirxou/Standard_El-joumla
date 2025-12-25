#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conflict Resolver - محلل التعارضات
يحل التعارضات في المزامنة
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ResolutionStrategy(Enum):
    """استراتيجية حل التعارض"""
    LOCAL_WINS = "LOCAL_WINS"  # الفوز للمحلي
    REMOTE_WINS = "REMOTE_WINS"  # الفوز للسحابي
    MANUAL_MERGE = "MANUAL_MERGE"  # دمج يدوي
    NEWEST_WINS = "NEWEST_WINS"  # الأحدث يفوز
    ASK_USER = "ASK_USER"  # سؤال المستخدم


@dataclass
class ConflictResolution:
    """حل التعارض"""
    success: bool
    strategy: ResolutionStrategy
    resolved_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ConflictResolver:
    """محلل التعارضات"""
    
    def __init__(self, db_manager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة محلل التعارضات
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
    
    def resolve_conflict(self, conflict_id: int, strategy: ResolutionStrategy,
                       local_data: Dict[str, Any], remote_data: Dict[str, Any],
                       local_version: int, remote_version: int,
                       custom_merge: Optional[Dict[str, Any]] = None) -> ConflictResolution:
        """
        حل تعارض
        
        Args:
            conflict_id: معرف التعارض
            strategy: استراتيجية الحل
            local_data: البيانات المحلية
            remote_data: البيانات السحابية
            local_version: الإصدار المحلي
            remote_version: الإصدار السحابي
            custom_merge: دمج مخصص (لـ MANUAL_MERGE)
            
        Returns:
            ConflictResolution: نتيجة الحل
        """
        try:
            resolved_data = None
            
            if strategy == ResolutionStrategy.LOCAL_WINS:
                resolved_data = local_data.copy()
                resolved_data["_version"] = local_version + 1
                resolved_data["_resolved_by"] = "LOCAL_WINS"
                
            elif strategy == ResolutionStrategy.REMOTE_WINS:
                resolved_data = remote_data.copy()
                resolved_data["_version"] = remote_version + 1
                resolved_data["_resolved_by"] = "REMOTE_WINS"
                
            elif strategy == ResolutionStrategy.NEWEST_WINS:
                # مقارنة التواريخ
                local_date = local_data.get("updated_at") or local_data.get("created_at")
                remote_date = remote_data.get("updated_at") or remote_data.get("created_at")
                
                if local_date and remote_date:
                    local_dt = datetime.fromisoformat(local_date.replace('Z', '+00:00'))
                    remote_dt = datetime.fromisoformat(remote_date.replace('Z', '+00:00'))
                    
                    if local_dt > remote_dt:
                        resolved_data = local_data.copy()
                        resolved_data["_version"] = local_version + 1
                        resolved_data["_resolved_by"] = "NEWEST_WINS_LOCAL"
                    else:
                        resolved_data = remote_data.copy()
                        resolved_data["_version"] = remote_version + 1
                        resolved_data["_resolved_by"] = "NEWEST_WINS_REMOTE"
                else:
                    # Fallback إلى LOCAL_WINS
                    resolved_data = local_data.copy()
                    resolved_data["_version"] = local_version + 1
                    resolved_data["_resolved_by"] = "NEWEST_WINS_FALLBACK"
                    
            elif strategy == ResolutionStrategy.MANUAL_MERGE:
                if custom_merge:
                    resolved_data = custom_merge.copy()
                    resolved_data["_version"] = max(local_version, remote_version) + 1
                    resolved_data["_resolved_by"] = "MANUAL_MERGE"
                else:
                    # دمج تلقائي بسيط
                    resolved_data = self._auto_merge(local_data, remote_data)
                    resolved_data["_version"] = max(local_version, remote_version) + 1
                    resolved_data["_resolved_by"] = "AUTO_MERGE"
            
            else:
                return ConflictResolution(
                    success=False,
                    strategy=strategy,
                    error_message=f"استراتيجية غير مدعومة: {strategy}"
                )
            
            # حفظ الحل
            self._save_resolution(conflict_id, strategy, resolved_data)
            
            return ConflictResolution(
                success=True,
                strategy=strategy,
                resolved_data=resolved_data
            )
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حل التعارض: {e}", exc_info=True)
            return ConflictResolution(
                success=False,
                strategy=strategy,
                error_message=str(e)
            )
    
    def _auto_merge(self, local_data: Dict[str, Any], remote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        دمج تلقائي بسيط
        
        يجمع الحقول من كلا البيانات، مع إعطاء الأولوية للبيانات المحلية
        """
        merged = local_data.copy()
        
        # إضافة الحقول من السحابة التي لا توجد محلياً
        for key, value in remote_data.items():
            if key not in merged or merged[key] is None:
                merged[key] = value
        
        return merged
    
    def _save_resolution(self, conflict_id: int, strategy: ResolutionStrategy,
                        resolved_data: Dict[str, Any]):
        """حفظ حل التعارض"""
        try:
            query = """
                UPDATE sync_conflicts SET
                    status = 'RESOLVED',
                    resolution_strategy = ?,
                    resolved_data = ?,
                    resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            
            self.db_manager.execute_query(
                query,
                (strategy.value, json.dumps(resolved_data, ensure_ascii=False), conflict_id)
            )
            
            self.logger.info(f"✅ تم حفظ حل التعارض: ID={conflict_id}")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حفظ حل التعارض: {e}", exc_info=True)
    
    def get_conflicts(self, sync_settings_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """الحصول على التعارضات"""
        try:
            if status:
                query = """
                    SELECT * FROM sync_conflicts
                    WHERE sync_settings_id = ? AND status = ?
                    ORDER BY created_at DESC
                """
                rows = self.db_manager.fetch_all(query, (sync_settings_id, status))
            else:
                query = """
                    SELECT * FROM sync_conflicts
                    WHERE sync_settings_id = ?
                    ORDER BY created_at DESC
                """
                rows = self.db_manager.fetch_all(query, (sync_settings_id,))
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على التعارضات: {e}", exc_info=True)
            return []
    
    def create_conflict(self, sync_settings_id: int, entity_type: str, entity_id: int,
                       local_data: Dict[str, Any], remote_data: Dict[str, Any],
                       local_version: int, remote_version: int) -> Optional[int]:
        """إنشاء تعارض جديد"""
        try:
            query = """
                INSERT INTO sync_conflicts (
                    sync_settings_id, entity_type, entity_id,
                    local_data, remote_data,
                    local_version, remote_version,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')
            """
            
            result = self.db_manager.execute_query(
                query,
                (sync_settings_id, entity_type, entity_id,
                 json.dumps(local_data, ensure_ascii=False),
                 json.dumps(remote_data, ensure_ascii=False),
                 local_version, remote_version)
            )
            
            if result:
                conflict_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء تعارض: ID={conflict_id}")
                return conflict_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء التعارض: {e}", exc_info=True)
            return None


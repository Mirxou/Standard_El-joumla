#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Sync Service - خدمة المزامنة السحابية
مزامنة البيانات مع Cloud Storage (AWS S3, Google Cloud, Azure)
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from pathlib import Path
import sys

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager
from src.core.sync_engine import SyncEngine, SyncDirection, SyncStatus, SyncResult
from src.core.conflict_resolver import ConflictResolver, ResolutionStrategy, ConflictResolution

logger = logging.getLogger(__name__)


@dataclass
class CloudSyncSettings:
    """إعدادات المزامنة السحابية"""
    id: Optional[int] = None
    name: str = ""
    provider: str = ""  # AWS_S3, GOOGLE_CLOUD, AZURE_BLOB, LOCAL
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    sync_enabled: bool = False
    auto_sync: bool = False
    sync_interval_minutes: int = 60
    last_sync_at: Optional[datetime] = None
    backup_enabled: bool = False
    auto_backup: bool = False
    backup_interval_hours: int = 24
    backup_time: Optional[str] = None
    last_backup_at: Optional[datetime] = None
    encryption_enabled: bool = True
    encryption_key: Optional[str] = None
    config: Optional[str] = None
    company_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CloudSyncService:
    """خدمة المزامنة السحابية"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة المزامنة السحابية
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
        
        # تهيئة المحركات
        self.sync_engine = SyncEngine(db_manager, logger_instance)
        self.conflict_resolver = ConflictResolver(db_manager, logger_instance)
        
        # Cloud Storage Clients (سيتم تهيئتها عند الحاجة)
        self._s3_client = None
        self._gcs_client = None
        self._azure_client = None
    
    # ============================================================================
    # إدارة الإعدادات (CRUD)
    # ============================================================================
    
    def create_settings(self, settings: CloudSyncSettings) -> Optional[int]:
        """إنشاء إعدادات مزامنة جديدة"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                INSERT INTO cloud_sync_settings (
                    name, provider, access_key, secret_key, bucket_name, region, endpoint_url,
                    sync_enabled, auto_sync, sync_interval_minutes,
                    backup_enabled, auto_backup, backup_interval_hours, backup_time,
                    encryption_enabled, encryption_key, config,
                    company_id, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                settings.name, settings.provider, settings.access_key, settings.secret_key,
                settings.bucket_name, settings.region, settings.endpoint_url,
                1 if settings.sync_enabled else 0, 1 if settings.auto_sync else 0,
                settings.sync_interval_minutes,
                1 if settings.backup_enabled else 0, 1 if settings.auto_backup else 0,
                settings.backup_interval_hours, settings.backup_time,
                1 if settings.encryption_enabled else 0, settings.encryption_key,
                settings.config, company_id, settings.created_by
            )
            
            result = self.db_manager.execute_query(query, values)
            if result:
                settings_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء إعدادات مزامنة: {settings.name} (ID: {settings_id})")
                return settings_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء إعدادات المزامنة: {e}", exc_info=True)
            return None
    
    def get_settings(self, settings_id: int) -> Optional[CloudSyncSettings]:
        """الحصول على إعدادات مزامنة"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                SELECT * FROM cloud_sync_settings
                WHERE id = ?
            """
            params = [settings_id]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            row = self.db_manager.fetch_one(query, tuple(params))
            if row:
                return self._row_to_settings(row)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على إعدادات المزامنة: {e}", exc_info=True)
            return None
    
    def get_all_settings(self) -> List[CloudSyncSettings]:
        """الحصول على جميع الإعدادات"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "SELECT * FROM cloud_sync_settings WHERE 1=1"
            params = []
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            query += " ORDER BY name"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_settings(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على الإعدادات: {e}", exc_info=True)
            return []
    
    def update_settings(self, settings: CloudSyncSettings) -> bool:
        """تحديث إعدادات مزامنة"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                UPDATE cloud_sync_settings SET
                    name = ?, provider = ?, access_key = ?, secret_key = ?,
                    bucket_name = ?, region = ?, endpoint_url = ?,
                    sync_enabled = ?, auto_sync = ?, sync_interval_minutes = ?,
                    backup_enabled = ?, auto_backup = ?, backup_interval_hours = ?, backup_time = ?,
                    encryption_enabled = ?, encryption_key = ?, config = ?
                WHERE id = ?
            """
            
            params = [
                settings.name, settings.provider, settings.access_key, settings.secret_key,
                settings.bucket_name, settings.region, settings.endpoint_url,
                1 if settings.sync_enabled else 0, 1 if settings.auto_sync else 0,
                settings.sync_interval_minutes,
                1 if settings.backup_enabled else 0, 1 if settings.auto_backup else 0,
                settings.backup_interval_hours, settings.backup_time,
                1 if settings.encryption_enabled else 0, settings.encryption_key,
                settings.config, settings.id
            ]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            result = self.db_manager.execute_query(query, tuple(params))
            if result and (hasattr(result, 'rowcount') and result.rowcount > 0 or not hasattr(result, 'rowcount')):
                self.logger.info(f"✅ تم تحديث إعدادات المزامنة: {settings.name} (ID: {settings.id})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث إعدادات المزامنة: {e}", exc_info=True)
            return False
    
    def delete_settings(self, settings_id: int) -> bool:
        """حذف إعدادات مزامنة"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "DELETE FROM cloud_sync_settings WHERE id = ?"
            params = [settings_id]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            result = self.db_manager.execute_query(query, tuple(params))
            
            if result and (hasattr(result, 'rowcount') and result.rowcount > 0 or not hasattr(result, 'rowcount')):
                self.logger.info(f"✅ تم حذف إعدادات المزامنة: ID={settings_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حذف إعدادات المزامنة: {e}", exc_info=True)
            return False
    
    # ============================================================================
    # المزامنة (Sync)
    # ============================================================================
    
    def sync_entity(self, settings_id: int, entity_type: str, entity_id: int,
                   direction: SyncDirection = SyncDirection.BOTH) -> SyncResult:
        """
        مزامنة كيان
        
        Args:
            settings_id: معرف الإعدادات
            entity_type: نوع الكيان
            entity_id: معرف الكيان
            direction: اتجاه المزامنة
            
        Returns:
            SyncResult: نتيجة المزامنة
        """
        try:
            settings = self.get_settings(settings_id)
            if not settings:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    direction=direction,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    error_message="الإعدادات غير موجودة"
                )
            
            if not settings.sync_enabled:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    direction=direction,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    error_message="المزامنة غير مفعلة"
                )
            
            # الحصول على البيانات المحلية
            local_data = self._get_local_entity(entity_type, entity_id)
            if not local_data:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    direction=direction,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    error_message="الكيان المحلي غير موجود"
                )
            
            # الحصول على حالة المزامنة
            sync_state = self.sync_engine.get_sync_state(settings_id, entity_type, entity_id)
            local_version = sync_state.get("local_version", 1) if sync_state else 1
            remote_version = sync_state.get("remote_version", 1) if sync_state else 1
            
            # الحصول على البيانات السحابية
            remote_data = self._get_remote_entity(settings, entity_type, entity_id)
            
            # تنفيذ المزامنة
            result = self.sync_engine.sync_entity(
                entity_type=entity_type,
                entity_id=entity_id,
                local_data=local_data,
                remote_data=remote_data,
                local_version=local_version,
                remote_version=remote_version,
                direction=direction
            )
            
            # إذا كان هناك تعارض، إنشاء سجل تعارض
            if result.conflict_detected:
                self.conflict_resolver.create_conflict(
                    sync_settings_id=settings_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    local_data=local_data,
                    remote_data=remote_data or {},
                    local_version=local_version,
                    remote_version=remote_version
                )
            
            # حفظ سجل المزامنة
            self._log_sync(settings_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في مزامنة الكيان: {e}", exc_info=True)
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                direction=direction,
                entity_type=entity_type,
                entity_id=entity_id,
                error_message=str(e)
            )
    
    def full_sync(self, settings_id: int) -> Dict[str, Any]:
        """
        مزامنة كاملة
        
        Args:
            settings_id: معرف الإعدادات
            
        Returns:
            Dict[str, Any]: نتائج المزامنة
        """
        try:
            settings = self.get_settings(settings_id)
            if not settings or not settings.sync_enabled:
                return {"success": False, "error": "المزامنة غير مفعلة"}
            
            results = {
                "success": True,
                "synced": 0,
                "failed": 0,
                "conflicts": 0,
                "details": []
            }
            
            # مزامنة الكيانات الرئيسية
            entity_types = ["sales", "purchases", "products", "customers", "suppliers"]
            
            for entity_type in entity_types:
                entities = self._get_all_local_entities(entity_type)
                for entity in entities:
                    entity_id = entity.get("id")
                    if entity_id:
                        result = self.sync_entity(settings_id, entity_type, entity_id)
                        if result.success:
                            results["synced"] += 1
                        elif result.conflict_detected:
                            results["conflicts"] += 1
                        else:
                            results["failed"] += 1
                        
                        results["details"].append({
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                            "success": result.success,
                            "conflict": result.conflict_detected
                        })
            
            # تحديث آخر مزامنة
            self._update_last_sync(settings_id)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في المزامنة الكاملة: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    # ============================================================================
    # Cloud Storage Operations
    # ============================================================================
    
    def _get_remote_entity(self, settings: CloudSyncSettings, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على كيان من السحابة"""
        try:
            provider = settings.provider.upper()
            
            if provider == "AWS_S3":
                return self._get_from_s3(settings, entity_type, entity_id)
            elif provider == "GOOGLE_CLOUD":
                return self._get_from_gcs(settings, entity_type, entity_id)
            elif provider == "AZURE_BLOB":
                return self._get_from_azure(settings, entity_type, entity_id)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على الكيان من السحابة: {e}", exc_info=True)
            return None
    
    def _get_from_s3(self, settings: CloudSyncSettings, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        """الحصول من AWS S3"""
        try:
            import boto3
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.access_key,
                aws_secret_access_key=settings.secret_key,
                region_name=settings.region,
                endpoint_url=settings.endpoint_url
            )
            
            key = f"{entity_type}/{entity_id}.json"
            
            response = s3_client.get_object(Bucket=settings.bucket_name, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            
            # فك التشفير إذا كان مفعلاً
            if settings.encryption_enabled and settings.encryption_key:
                data = self._decrypt_data(data, settings.encryption_key)
            
            return data
            
        except Exception as e:
            # الملف غير موجود = لا توجد بيانات سحابية
            if "NoSuchKey" in str(e) or "404" in str(e):
                return None
            self.logger.error(f"❌ خطأ في الحصول من S3: {e}", exc_info=True)
            return None
    
    def _get_from_gcs(self, settings: CloudSyncSettings, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        """الحصول من Google Cloud Storage"""
        try:
            from google.cloud import storage
            
            client = storage.Client.from_service_account_json(
                settings.config if settings.config else None
            )
            
            bucket = client.bucket(settings.bucket_name)
            blob = bucket.blob(f"{entity_type}/{entity_id}.json")
            
            if not blob.exists():
                return None
            
            data = json.loads(blob.download_as_text())
            
            # فك التشفير
            if settings.encryption_enabled and settings.encryption_key:
                data = self._decrypt_data(data, settings.encryption_key)
            
            return data
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول من GCS: {e}", exc_info=True)
            return None
    
    def _get_from_azure(self, settings: CloudSyncSettings, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        """الحصول من Azure Blob Storage"""
        try:
            from azure.storage.blob import BlobServiceClient
            
            blob_service_client = BlobServiceClient(
                account_url=f"https://{settings.bucket_name}.blob.core.windows.net",
                credential=settings.secret_key
            )
            
            container_client = blob_service_client.get_container_client(settings.bucket_name)
            blob_client = container_client.get_blob_client(f"{entity_type}/{entity_id}.json")
            
            if not blob_client.exists():
                return None
            
            data = json.loads(blob_client.download_blob().readall().decode('utf-8'))
            
            # فك التشفير
            if settings.encryption_enabled and settings.encryption_key:
                data = self._decrypt_data(data, settings.encryption_key)
            
            return data
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول من Azure: {e}", exc_info=True)
            return None
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def _get_local_entity(self, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على كيان محلي"""
        try:
            query = f"SELECT * FROM {entity_type} WHERE id = ?"
            row = self.db_manager.fetch_one(query, (entity_id,))
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على الكيان المحلي: {e}", exc_info=True)
            return None
    
    def _get_all_local_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """الحصول على جميع الكيانات المحلية"""
        try:
            query = f"SELECT * FROM {entity_type} LIMIT 1000"  # حد أقصى
            rows = self.db_manager.fetch_all(query)
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على الكيانات المحلية: {e}", exc_info=True)
            return []
    
    def _encrypt_data(self, data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """تشفير البيانات"""
        try:
            from cryptography.fernet import Fernet
            import base64
            
            # إنشاء مفتاح من Key
            key_bytes = key.encode('utf-8')
            key_b64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            fernet = Fernet(key_b64)
            
            # تشفير JSON
            json_str = json.dumps(data, ensure_ascii=False)
            encrypted = fernet.encrypt(json_str.encode('utf-8'))
            
            return {"encrypted": base64.b64encode(encrypted).decode('utf-8')}
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في التشفير: {e}", exc_info=True)
            return data
    
    def _decrypt_data(self, data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """فك تشفير البيانات"""
        try:
            from cryptography.fernet import Fernet
            import base64
            
            if "encrypted" not in data:
                return data
            
            # إنشاء مفتاح من Key
            key_bytes = key.encode('utf-8')
            key_b64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            fernet = Fernet(key_b64)
            
            # فك التشفير
            encrypted_bytes = base64.b64decode(data["encrypted"])
            decrypted = fernet.decrypt(encrypted_bytes)
            
            return json.loads(decrypted.decode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في فك التشفير: {e}", exc_info=True)
            return data
    
    def _log_sync(self, settings_id: int, result: SyncResult):
        """تسجيل المزامنة"""
        try:
            query = """
                INSERT INTO sync_logs (
                    sync_settings_id, sync_type, entity_type, entity_id,
                    status, direction, local_hash, remote_hash,
                    conflict_resolved, error_message, sync_data,
                    execution_time_ms, data_size_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                settings_id, "FULL_SYNC" if result.entity_type else "ENTITY_SYNC",
                result.entity_type, result.entity_id,
                result.status.value, result.direction.value if isinstance(result.direction, SyncDirection) else str(result.direction),
                result.local_hash, result.remote_hash,
                0, result.error_message,
                json.dumps({"success": result.success}, ensure_ascii=False),
                result.execution_time_ms, result.data_size_bytes
            )
            
            self.db_manager.execute_query(query, values)
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تسجيل المزامنة: {e}", exc_info=True)
    
    def _update_last_sync(self, settings_id: int):
        """تحديث آخر مزامنة"""
        try:
            query = """
                UPDATE cloud_sync_settings
                SET last_sync_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            self.db_manager.execute_query(query, (settings_id,))
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث آخر مزامنة: {e}", exc_info=True)
    
    def _row_to_settings(self, row: Dict[str, Any]) -> CloudSyncSettings:
        """تحويل صف قاعدة البيانات إلى CloudSyncSettings"""
        return CloudSyncSettings(
            id=row.get("id"),
            name=row.get("name", ""),
            provider=row.get("provider", ""),
            access_key=row.get("access_key"),
            secret_key=row.get("secret_key"),
            bucket_name=row.get("bucket_name"),
            region=row.get("region"),
            endpoint_url=row.get("endpoint_url"),
            sync_enabled=bool(row.get("sync_enabled", 0)),
            auto_sync=bool(row.get("auto_sync", 0)),
            sync_interval_minutes=row.get("sync_interval_minutes", 60),
            last_sync_at=self._parse_datetime(row.get("last_sync_at")),
            backup_enabled=bool(row.get("backup_enabled", 0)),
            auto_backup=bool(row.get("auto_backup", 0)),
            backup_interval_hours=row.get("backup_interval_hours", 24),
            backup_time=row.get("backup_time"),
            last_backup_at=self._parse_datetime(row.get("last_backup_at")),
            encryption_enabled=bool(row.get("encryption_enabled", 1)),
            encryption_key=row.get("encryption_key"),
            config=row.get("config"),
            company_id=row.get("company_id"),
            created_by=row.get("created_by"),
            created_at=self._parse_datetime(row.get("created_at")),
            updated_at=self._parse_datetime(row.get("updated_at"))
        )
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """تحليل datetime من قاعدة البيانات"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except:
                    return None
        return None


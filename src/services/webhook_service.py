#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook Service - خدمة إدارة Webhooks
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import json
import sys
from pathlib import Path


from src.core.database_manager import DatabaseManager
from src.core.webhook_dispatcher import get_webhook_dispatcher, WebhookDeliveryResult
from src.core.tenant_isolation import TenantIsolationManager
from src.utils.logger import setup_logger


@dataclass
class Webhook:
    """Webhook Data Class"""
    id: Optional[int]
    name: str
    url: str
    event_type: str
    http_method: str = "POST"
    headers: Optional[str] = None  # JSON String
    payload_template: Optional[str] = None  # JSON Template
    is_active: bool = True
    retry_count: int = 3
    timeout_seconds: int = 30
    secret_key: Optional[str] = None
    priority: int = 5  # الأولوية (1=عاجل, 5=عادي, 10=منخفض)
    rate_limit_per_minute: int = 60  # حد الإرسال (عدد الطلبات في الدقيقة)
    company_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى Dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "event_type": self.event_type,
            "http_method": self.http_method,
            "headers": self.headers,
            "payload_template": self.payload_template,
            "is_active": self.is_active,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "secret_key": self.secret_key,
            "priority": self.priority,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Webhook":
        """إنشاء من Dictionary"""
        # Parse datetime strings
        created_at = None
        updated_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            else:
                created_at = data["created_at"]
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(data["updated_at"])
            else:
                updated_at = data["updated_at"]
        
        return cls(
            id=data.get("id"),
            name=data["name"],
            url=data["url"],
            event_type=data["event_type"],
            http_method=data.get("http_method", "POST"),
            headers=data.get("headers"),
            payload_template=data.get("payload_template"),
            is_active=bool(data.get("is_active", True)),
            retry_count=int(data.get("retry_count", 3)),
            timeout_seconds=int(data.get("timeout_seconds", 30)),
            secret_key=data.get("secret_key"),
            priority=int(data.get("priority", 5)),
            rate_limit_per_minute=int(data.get("rate_limit_per_minute", 60)),
            company_id=data.get("company_id"),
            created_by=data.get("created_by"),
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class WebhookLog:
    """Webhook Log Data Class"""
    id: Optional[int]
    webhook_id: int
    event_type: str
    entity_id: Optional[int] = None
    payload: str = ""  # JSON String
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempt_number: int = 1
    is_success: bool = False
    execution_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى Dictionary"""
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "payload": self.payload,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "attempt_number": self.attempt_number,
            "is_success": self.is_success,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class WebhookService:
    """خدمة إدارة Webhooks"""
    
    def __init__(self, db_manager: DatabaseManager, logger=None):
        """
        تهيئة Webhook Service
        
        Args:
            db_manager: DatabaseManager instance
            logger: Logger instance (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self.dispatcher = get_webhook_dispatcher()
        self._tenant_manager = None
    
    @property
    def tenant_manager(self) -> TenantIsolationManager:
        """Lazy loading لـ TenantIsolationManager"""
        if self._tenant_manager is None:
            self._tenant_manager = TenantIsolationManager(self.db_manager)
        return self._tenant_manager
    
    def _get_company_id(self) -> Optional[int]:
        """الحصول على company_id الحالي"""
        return self.tenant_manager.get_current_company_id()
    
    # ==================== CRUD Operations ====================
    
    def create_webhook(
        self,
        name: str,
        url: str,
        event_type: str,
        http_method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        payload_template: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        retry_count: int = 3,
        timeout_seconds: int = 30,
        secret_key: Optional[str] = None,
        priority: int = 5,
        rate_limit_per_minute: int = 60,
        company_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Optional[int]:
        """
        إنشاء Webhook جديد
        
        Args:
            name: اسم Webhook
            url: عنوان URL
            event_type: نوع الحدث (sale_created, payment_received, etc.)
            http_method: طريقة HTTP (POST, PUT, PATCH)
            headers: Headers مخصصة (Dict)
            payload_template: قالب Payload (Dict)
            is_active: نشط/غير نشط
            retry_count: عدد محاولات إعادة الإرسال
            timeout_seconds: مهلة الانتظار (بالثواني)
            secret_key: Secret Key للتوقيع
            company_id: معرف الشركة (اختياري - يستخدم الحالي إذا لم يُحدد)
            created_by: معرف المستخدم الذي أنشأ Webhook
            
        Returns:
            webhook_id أو None في حالة الفشل
        """
        try:
            # استخدام company_id الحالي إذا لم يُحدد
            if company_id is None:
                company_id = self._get_company_id()
            
            # تحويل headers و payload_template إلى JSON
            headers_json = json.dumps(headers) if headers else None
            payload_template_json = json.dumps(payload_template) if payload_template else None
            
            query = """
                INSERT INTO webhooks (
                    name, url, event_type, http_method, headers, payload_template,
                    is_active, retry_count, timeout_seconds, secret_key,
                    priority, rate_limit_per_minute,
                    company_id, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            params = (
                name, url, event_type, http_method, headers_json, payload_template_json,
                int(is_active), retry_count, timeout_seconds, secret_key,
                priority, rate_limit_per_minute,
                company_id, created_by, now, now
            )
            
            self.db_manager.execute_query(query, params)
            webhook_id = self.db_manager.get_last_insert_id()
            
            if self.logger:
                self.logger.info(f"✅ تم إنشاء Webhook جديد: {name} (ID: {webhook_id})")
            
            return webhook_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في إنشاء Webhook: {e}", exc_info=True)
            return None
    
    def get_webhook(self, webhook_id: int, company_id: Optional[int] = None) -> Optional[Webhook]:
        """
        الحصول على Webhook
        
        Args:
            webhook_id: معرف Webhook
            company_id: معرف الشركة (اختياري - للتحقق من الصلاحيات)
            
        Returns:
            Webhook أو None
        """
        try:
            if company_id is None:
                company_id = self._get_company_id()
            
            query = """
                SELECT * FROM webhooks
                WHERE id = ? AND company_id = ?
            """
            
            rows = self.db_manager.execute_query(query, (webhook_id, company_id))
            
            if rows:
                return self._row_to_webhook(rows[0])
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في جلب Webhook: {e}", exc_info=True)
            return None
    
    def get_all_webhooks(
        self,
        event_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        company_id: Optional[int] = None
    ) -> List[Webhook]:
        """
        الحصول على جميع Webhooks
        
        Args:
            event_type: فلتر حسب نوع الحدث (اختياري)
            is_active: فلتر حسب الحالة (اختياري)
            company_id: معرف الشركة (اختياري - يستخدم الحالي إذا لم يُحدد)
            
        Returns:
            قائمة Webhooks
        """
        try:
            if company_id is None:
                company_id = self._get_company_id()
            
            query = "SELECT * FROM webhooks WHERE company_id = ?"
            params = [company_id]
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if is_active is not None:
                query += " AND is_active = ?"
                params.append(int(is_active))
            
            query += " ORDER BY created_at DESC"
            
            rows = self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_webhook(row) for row in rows]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في جلب Webhooks: {e}", exc_info=True)
            return []
    
    def update_webhook(
        self,
        webhook_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None,
        event_type: Optional[str] = None,
        http_method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        payload_template: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        retry_count: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        secret_key: Optional[str] = None,
        priority: Optional[int] = None,
        rate_limit_per_minute: Optional[int] = None,
        company_id: Optional[int] = None
    ) -> bool:
        """
        تحديث Webhook
        
        Returns:
            True في حالة النجاح
        """
        try:
            if company_id is None:
                company_id = self._get_company_id()
            
            # بناء Query ديناميكي
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if url is not None:
                updates.append("url = ?")
                params.append(url)
            
            if event_type is not None:
                updates.append("event_type = ?")
                params.append(event_type)
            
            if http_method is not None:
                updates.append("http_method = ?")
                params.append(http_method)
            
            if headers is not None:
                updates.append("headers = ?")
                params.append(json.dumps(headers))
            
            if payload_template is not None:
                updates.append("payload_template = ?")
                params.append(json.dumps(payload_template))
            
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(int(is_active))
            
            if retry_count is not None:
                updates.append("retry_count = ?")
                params.append(retry_count)
            
            if timeout_seconds is not None:
                updates.append("timeout_seconds = ?")
                params.append(timeout_seconds)
            
            if secret_key is not None:
                updates.append("secret_key = ?")
                params.append(secret_key)
            
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            
            if rate_limit_per_minute is not None:
                updates.append("rate_limit_per_minute = ?")
                params.append(rate_limit_per_minute)
            
            if not updates:
                return True  # لا توجد تحديثات
            
            updates.append("updated_at = ?")
            params.append(datetime.now())
            
            params.append(webhook_id)
            params.append(company_id)
            
            query = f"""
                UPDATE webhooks
                SET {', '.join(updates)}
                WHERE id = ? AND company_id = ?
            """
            
            self.db_manager.execute_query(query, tuple(params))
            
            if self.logger:
                self.logger.info(f"✅ تم تحديث Webhook: {webhook_id}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في تحديث Webhook: {e}", exc_info=True)
            return False
    
    def delete_webhook(self, webhook_id: int, company_id: Optional[int] = None) -> bool:
        """
        حذف Webhook
        
        Returns:
            True في حالة النجاح
        """
        try:
            if company_id is None:
                company_id = self._get_company_id()
            
            query = "DELETE FROM webhooks WHERE id = ? AND company_id = ?"
            self.db_manager.execute_query(query, (webhook_id, company_id))
            
            if self.logger:
                self.logger.info(f"✅ تم حذف Webhook: {webhook_id}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في حذف Webhook: {e}", exc_info=True)
            return False
    
    # ==================== Webhook Delivery ====================
    
    def trigger_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        entity_id: Optional[int] = None,
        company_id: Optional[int] = None
    ) -> None:
        """
        إطلاق Webhook للأحداث
        
        Args:
            event_type: نوع الحدث (sale_created, payment_received, etc.)
            payload: البيانات المرسلة (Dict)
            entity_id: معرف الكيان (sale_id, payment_id, etc.)
            company_id: معرف الشركة (اختياري - يستخدم الحالي إذا لم يُحدد)
        """
        try:
            if company_id is None:
                company_id = self._get_company_id()
            
            # الحصول على جميع Webhooks النشطة لهذا الحدث
            webhooks = self.get_all_webhooks(
                event_type=event_type,
                is_active=True,
                company_id=company_id
            )
            
            if not webhooks:
                if self.logger:
                    self.logger.debug(f"لا توجد Webhooks نشطة للحدث: {event_type}")
                return
            
            # إرسال كل Webhook
            for webhook in webhooks:
                try:
                    # استخدام Payload Template إذا كان موجوداً
                    final_payload = self._build_payload(webhook, payload)
                    
                    # Parse Headers
                    headers = {}
                    if webhook.headers:
                        try:
                            headers = json.loads(webhook.headers)
                        except:
                            pass
                    
                    # إرسال Webhook (Async)
                    success = self.dispatcher.deliver_webhook(
                        url=webhook.url,
                        payload=final_payload,
                        http_method=webhook.http_method,
                        headers=headers,
                        secret_key=webhook.secret_key,
                        timeout_seconds=webhook.timeout_seconds,
                        retry_count=webhook.retry_count,
                        webhook_id=webhook.id,
                        event_type=event_type,
                        entity_id=entity_id,
                        callback=self._on_webhook_delivered,
                        priority=webhook.priority,
                        rate_limit_per_minute=webhook.rate_limit_per_minute
                    )
                    
                    if not success:
                        if self.logger:
                            self.logger.warning(
                                f"⚠️ تم تجاوز Rate Limit لـ Webhook {webhook.name} "
                                f"(ID: {webhook.id})"
                            )
                    
                    if self.logger:
                        self.logger.debug(
                            f"✅ تم إطلاق Webhook: {webhook.name} "
                            f"(Event: {event_type}, Entity: {entity_id})"
                        )
                        
                except Exception as e:
                    if self.logger:
                        self.logger.error(
                            f"❌ خطأ في إطلاق Webhook {webhook.name}: {e}",
                            exc_info=True
                        )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في trigger_webhook: {e}", exc_info=True)
    
    def _build_payload(self, webhook: Webhook, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        بناء Payload النهائي باستخدام Template
        
        Args:
            webhook: Webhook instance
            event_payload: Payload الحدث الأصلي
            
        Returns:
            Payload النهائي
        """
        # إذا لم يكن هناك Template، استخدم Payload الأصلي
        if not webhook.payload_template:
            return event_payload
        
        try:
            # استبدال Template Variables في النص أولاً
            template_str = webhook.payload_template
            
            # استبدال المتغيرات الأساسية
            if webhook.event_type:
                template_str = template_str.replace("{event_type}", webhook.event_type)
            
            if webhook.id:
                # نستخدم استبدال ذكي للأرقام إذا كانت القيم غير محاطة بعلامات اقتباس
                # لكن الاستبدال النصي البسيط يكفي عادة إذا كان القالب مكتوباً بشكل صحيح
                template_str = template_str.replace("{webhook_id}", str(webhook.id))
            
            # Parse Template بعد الاستبدال
            final_payload = json.loads(template_str)
            
            # دمج Event Payload (يغطي القيم الأصلية)
            if isinstance(final_payload, dict):
                final_payload.update(event_payload)
            
            return final_payload
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ فشل بناء Payload من Template: {e}")
            return event_payload
    
    def _on_webhook_delivered(
        self,
        result: WebhookDeliveryResult,
        webhook_id: Optional[int],
        event_type: Optional[str],
        entity_id: Optional[int],
        payload_json: str
    ) -> None:
        """
        Callback عند اكتمال إرسال Webhook (للتسجيل)
        
        Args:
            result: نتيجة الإرسال
            webhook_id: معرف Webhook
            event_type: نوع الحدث
            entity_id: معرف الكيان
            payload_json: Payload كـ JSON String
        """
        try:
            query = """
                INSERT INTO webhook_logs (
                    webhook_id, event_type, entity_id, payload,
                    response_status, response_body, error_message,
                    attempt_number, is_success, execution_time_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                webhook_id,
                event_type,
                entity_id,
                payload_json[:10000],  # حد أقصى 10KB
                result.status_code,
                result.response_body[:1000] if result.response_body else None,  # حد أقصى 1KB
                result.error_message[:500] if result.error_message else None,  # حد أقصى 500 حرف
                result.attempt_number,
                int(result.success),
                result.execution_time_ms,
                datetime.now()
            )
            
            self.db_manager.execute_query(query, params)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في تسجيل Webhook Log: {e}", exc_info=True)
    
    # ==================== Webhook Logs ====================
    
    def get_webhook_logs(
        self,
        webhook_id: Optional[int] = None,
        event_type: Optional[str] = None,
        is_success: Optional[bool] = None,
        limit: int = 100,
        company_id: Optional[int] = None
    ) -> List[WebhookLog]:
        """
        الحصول على سجلات Webhooks
        
        Args:
            webhook_id: فلتر حسب Webhook ID (اختياري)
            event_type: فلتر حسب نوع الحدث (اختياري)
            is_success: فلتر حسب النجاح/الفشل (اختياري)
            limit: حد أقصى للنتائج
            company_id: معرف الشركة (اختياري)
            
        Returns:
            قائمة WebhookLogs
        """
        try:
            if company_id is None:
                company_id = self._get_company_id()
            
            # بناء Query مع JOIN للحصول على Webhooks من نفس الشركة فقط
            query = """
                SELECT wl.* FROM webhook_logs wl
                INNER JOIN webhooks w ON wl.webhook_id = w.id
                WHERE w.company_id = ?
            """
            params = [company_id]
            
            if webhook_id:
                query += " AND wl.webhook_id = ?"
                params.append(webhook_id)
            
            if event_type:
                query += " AND wl.event_type = ?"
                params.append(event_type)
            
            if is_success is not None:
                query += " AND wl.is_success = ?"
                params.append(int(is_success))
            
            query += " ORDER BY wl.created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = self.db_manager.execute_query(query, tuple(params))
            
            return [self._row_to_webhook_log(row) for row in rows]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في جلب Webhook Logs: {e}", exc_info=True)
            return []
    
    # ==================== Helper Methods ====================
    
    def _row_to_webhook(self, row: Dict[str, Any]) -> Webhook:
        """تحويل Row إلى Webhook"""
        return Webhook(
            id=row.get("id"),
            name=row["name"],
            url=row["url"],
            event_type=row["event_type"],
            http_method=row.get("http_method", "POST"),
            headers=row.get("headers"),
            payload_template=row.get("payload_template"),
            is_active=bool(row.get("is_active", True)),
            retry_count=int(row.get("retry_count", 3)),
            timeout_seconds=int(row.get("timeout_seconds", 30)),
            secret_key=row.get("secret_key"),
            priority=int(row.get("priority", 5)),
            rate_limit_per_minute=int(row.get("rate_limit_per_minute", 60)),
            company_id=row.get("company_id"),
            created_by=row.get("created_by"),
            created_at=self._parse_datetime(row.get("created_at")),
            updated_at=self._parse_datetime(row.get("updated_at"))
        )
    
    def _row_to_webhook_log(self, row: Dict[str, Any]) -> WebhookLog:
        """تحويل Row إلى WebhookLog"""
        return WebhookLog(
            id=row.get("id"),
            webhook_id=row["webhook_id"],
            event_type=row["event_type"],
            entity_id=row.get("entity_id"),
            payload=row.get("payload", ""),
            response_status=row.get("response_status"),
            response_body=row.get("response_body"),
            error_message=row.get("error_message"),
            attempt_number=int(row.get("attempt_number", 1)),
            is_success=bool(row.get("is_success", False)),
            execution_time_ms=row.get("execution_time_ms"),
            created_at=self._parse_datetime(row.get("created_at"))
        )
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime من قيمة"""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except:
                    return None
        
        return None


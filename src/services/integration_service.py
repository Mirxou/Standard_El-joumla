import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Service - خدمة التكامل الرئيسية
إدارة جميع التكاملات مع الأنظمة الخارجية
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager
from src.services.accounting_integration_service import AccountingIntegrationService
from src.services.payment_gateway_service import PaymentGatewayService
from src.services.shipping_service import ShippingService

logger = logging.getLogger(__name__)


@dataclass
class Integration:
    """تكامل"""

    id: Optional[int] = None
    name: str = ""
    integration_type: str = ""  # PAYMENT_GATEWAY, SHIPPING, ACCOUNTING
    provider: str = ""  # Stripe, PayPal, FedEx, DHL, QuickBooks, Xero
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    api_url: Optional[str] = None
    webhook_url: Optional[str] = None
    config: Optional[str] = None  # JSON
    is_active: bool = True
    is_test_mode: bool = True
    company_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "integration_type": self.integration_type,
            "provider": self.provider,
            "api_key": "***" if self.api_key else None,  # إخفاء API Key
            "api_secret": "***" if self.api_secret else None,  # إخفاء API Secret
            "api_url": self.api_url,
            "webhook_url": self.webhook_url,
            "config": self.config,
            "is_active": self.is_active,
            "is_test_mode": self.is_test_mode,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Integration":
        """إنشاء من قاموس"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class IntegrationService:
    """خدمة التكامل الرئيسية"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        logger_instance: Optional[logging.Logger] = None,
    ):
        """
        تهيئة خدمة التكامل

        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None

        # تهيئة الخدمات الفرعية
        self.payment_gateway_service = PaymentGatewayService(db_manager, logger_instance)
        self.shipping_service = ShippingService(db_manager, logger_instance)
        self.accounting_service = AccountingIntegrationService(db_manager, logger_instance)

    # ============================================================================
    # إدارة التكاملات (CRUD)
    # ============================================================================

    def create_integration(self, integration: Integration) -> Optional[int]:
        """إنشاء تكامل جديد"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = """
                INSERT INTO integrations (
                    name, integration_type, provider,
                    api_key, api_secret, api_url, webhook_url,
                    config, is_active, is_test_mode,
                    company_id, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                integration.name,
                integration.integration_type,
                integration.provider,
                integration.api_key,
                integration.api_secret,
                integration.api_url,
                integration.webhook_url,
                integration.config,
                1 if integration.is_active else 0,
                1 if integration.is_test_mode else 0,
                company_id,
                integration.created_by,
            )

            result = self.db_manager.execute_query(query, values)
            if result:
                integration_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء تكامل: {integration.name} (ID: {integration_id})")
                return integration_id

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء التكامل: {e}", exc_info=True)
            return None

    def get_integration(self, integration_id: int) -> Optional[Integration]:
        """الحصول على تكامل"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = """
                SELECT * FROM integrations
                WHERE id = ?
            """
            params = [integration_id]

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            row = self.db_manager.fetch_one(query, tuple(params))
            if row:
                return self._row_to_integration(row)

            return None

        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على التكامل: {e}", exc_info=True)
            return None

    def get_all_integrations(self, integration_type: Optional[str] = None) -> List[Integration]:
        """الحصول على جميع التكاملات"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            if integration_type:
                query = """
                    SELECT * FROM integrations
                    WHERE integration_type = ?
                """
                params = [integration_type]
            else:
                query = "SELECT * FROM integrations WHERE 1=1"
                params = []

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            query += " ORDER BY name"

            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_integration(row) for row in rows]

        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على التكاملات: {e}", exc_info=True)
            return []

    def update_integration(self, integration: Integration) -> bool:
        """تحديث تكامل"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = """
                UPDATE integrations SET
                    name = ?, integration_type = ?, provider = ?,
                    api_key = ?, api_secret = ?, api_url = ?, webhook_url = ?,
                    config = ?, is_active = ?, is_test_mode = ?
                WHERE id = ?
            """

            params = [
                integration.name,
                integration.integration_type,
                integration.provider,
                integration.api_key,
                integration.api_secret,
                integration.api_url,
                integration.webhook_url,
                integration.config,
                1 if integration.is_active else 0,
                1 if integration.is_test_mode else 0,
                integration.id,
            ]

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            result = self.db_manager.execute_query(query, tuple(params))
            if result and (hasattr(result, "rowcount") and result.rowcount > 0 or not hasattr(result, "rowcount")):
                self.logger.info(f"✅ تم تحديث التكامل: {integration.name} (ID: {integration.id})")
                return True

            return False

        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث التكامل: {e}", exc_info=True)
            return False

    def delete_integration(self, integration_id: int) -> bool:
        """حذف تكامل"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None

            query = "DELETE FROM integrations WHERE id = ?"
            params = [integration_id]

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            result = self.db_manager.execute_query(query, tuple(params))

            if result and (hasattr(result, "rowcount") and result.rowcount > 0 or not hasattr(result, "rowcount")):
                self.logger.info(f"✅ تم حذف التكامل: ID={integration_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"❌ خطأ في حذف التكامل: {e}", exc_info=True)
            return False

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _row_to_integration(self, row: Dict[str, Any]) -> Integration:
        """تحويل صف قاعدة البيانات إلى Integration"""
        return Integration(
            id=row.get("id"),
            name=row.get("name", ""),
            integration_type=row.get("integration_type", ""),
            provider=row.get("provider", ""),
            api_key=row.get("api_key"),
            api_secret=row.get("api_secret"),
            api_url=row.get("api_url"),
            webhook_url=row.get("webhook_url"),
            config=row.get("config"),
            is_active=bool(row.get("is_active", 1)),
            is_test_mode=bool(row.get("is_test_mode", 1)),
            company_id=row.get("company_id"),
            created_by=row.get("created_by"),
            created_at=self._parse_datetime(row.get("created_at")),
            updated_at=self._parse_datetime(row.get("updated_at")),
        )

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """تحليل datetime من قاعدة البيانات"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return None
        return None

    # ============================================================================
    # Logging
    # ============================================================================

    def log_integration_request(
        self,
        integration_id: int,
        log_type: str,
        operation: str,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
    ):
        """تسجيل طلب تكامل"""
        try:
            query = """
                INSERT INTO integration_logs (
                    integration_id, log_type, operation,
                    request_data, response_data, error_message, execution_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                integration_id,
                log_type,
                operation,
                json.dumps(request_data, ensure_ascii=False) if request_data else None,
                (json.dumps(response_data, ensure_ascii=False) if response_data else None),
                error_message,
                execution_time_ms,
            )

            self.db_manager.execute_query(query, values)

        except Exception as e:
            self.logger.error(f"❌ خطأ في تسجيل الطلب: {e}", exc_info=True)

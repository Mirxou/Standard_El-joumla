#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSO Service - خدمة Single Sign-On
دعم SAML و OAuth2 للمصادقة الموحدة
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager

logger = logging.getLogger(__name__)


class SSOProviderType:
    """أنواع مزودي SSO"""
    SAML = "SAML"
    OAUTH2 = "OAUTH2"
    OPENID_CONNECT = "OPENID_CONNECT"


@dataclass
class SSOProvider:
    """مزود SSO"""
    id: Optional[int] = None
    name: str = ""
    provider_type: str = SSOProviderType.OAUTH2
    enabled: bool = False
    config: str = ""  # JSON
    company_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SSOService:
    """خدمة Single Sign-On"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة SSO
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
        
        self._create_tables()
    
    def _create_tables(self):
        """إنشاء جداول SSO"""
        try:
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS sso_providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    provider_type TEXT NOT NULL,
                    enabled INTEGER DEFAULT 0,
                    config TEXT,
                    company_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            """)
            
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS sso_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    provider_id INTEGER NOT NULL,
                    sso_token TEXT NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    company_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (provider_id) REFERENCES sso_providers(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            """)
            
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_sso_sessions_token 
                ON sso_sessions(sso_token)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_sso_sessions_user 
                ON sso_sessions(user_id)
            """)
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء جداول SSO: {e}", exc_info=True)
    
    # ============================================================================
    # OAuth2 Support
    # ============================================================================
    
    def initiate_oauth2_login(self, provider_id: int, redirect_uri: str) -> Dict[str, Any]:
        """
        بدء عملية تسجيل الدخول عبر OAuth2
        
        Args:
            provider_id: معرف المزود
            redirect_uri: URI لإعادة التوجيه بعد المصادقة
            
        Returns:
            Dict مع authorization URL
        """
        try:
            provider = self.get_provider(provider_id)
            if not provider or not provider.enabled:
                return {"error": "المزود غير مفعّل"}
            
            config = json.loads(provider.config) if provider.config else {}
            
            # إنشاء state parameter للتحقق من الأمان
            import secrets
            state = secrets.token_urlsafe(32)
            
            # بناء authorization URL
            auth_url = config.get("authorization_endpoint", "")
            client_id = config.get("client_id", "")
            scope = config.get("scope", "openid profile email")
            
            authorization_url = f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&state={state}"
            
            return {
                "success": True,
                "authorization_url": authorization_url,
                "state": state
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في بدء عملية OAuth2: {e}", exc_info=True)
            return {"error": str(e)}
    
    def handle_oauth2_callback(self, provider_id: int, code: str, state: str) -> Dict[str, Any]:
        """
        معالجة callback من OAuth2
        
        Args:
            provider_id: معرف المزود
            code: authorization code
            state: state parameter للتحقق
            
        Returns:
            Dict مع معلومات المستخدم
        """
        try:
            provider = self.get_provider(provider_id)
            if not provider:
                return {"error": "المزود غير موجود"}
            
            config = json.loads(provider.config) if provider.config else {}
            
            # TODO: استبدال authorization code بـ access token
            # هذا يتطلب HTTP request إلى token endpoint
            # access_token = self._exchange_code_for_token(code, config)
            
            # TODO: الحصول على معلومات المستخدم من userinfo endpoint
            # user_info = self._get_user_info(access_token, config)
            
            return {
                "success": True,
                "message": "OAuth2 callback handled (implementation pending)"
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في معالجة OAuth2 callback: {e}", exc_info=True)
            return {"error": str(e)}
    
    # ============================================================================
    # SAML Support
    # ============================================================================
    
    def initiate_saml_login(self, provider_id: int) -> Dict[str, Any]:
        """
        بدء عملية تسجيل الدخول عبر SAML
        
        Args:
            provider_id: معرف المزود
            
        Returns:
            Dict مع SAML request
        """
        try:
            provider = self.get_provider(provider_id)
            if not provider or not provider.enabled:
                return {"error": "المزود غير مفعّل"}
            
            config = json.loads(provider.config) if provider.config else {}
            
            # TODO: إنشاء SAML AuthnRequest
            # يتطلب مكتبة python-saml أو python3-saml
            
            return {
                "success": True,
                "message": "SAML login initiated (implementation pending)"
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في بدء عملية SAML: {e}", exc_info=True)
            return {"error": str(e)}
    
    def handle_saml_response(self, provider_id: int, saml_response: str) -> Dict[str, Any]:
        """
        معالجة SAML response
        
        Args:
            provider_id: معرف المزود
            saml_response: SAML response XML
            
        Returns:
            Dict مع معلومات المستخدم
        """
        try:
            provider = self.get_provider(provider_id)
            if not provider:
                return {"error": "المزود غير موجود"}
            
            # TODO: التحقق من SAML response وتفكيكها
            # يتطلب مكتبة python-saml أو python3-saml
            
            return {
                "success": True,
                "message": "SAML response handled (implementation pending)"
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في معالجة SAML response: {e}", exc_info=True)
            return {"error": str(e)}
    
    # ============================================================================
    # Provider Management
    # ============================================================================
    
    def create_provider(self, provider: SSOProvider) -> Optional[int]:
        """إنشاء مزود SSO"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                INSERT INTO sso_providers (
                    name, provider_type, enabled, config, company_id
                ) VALUES (?, ?, ?, ?, ?)
            """
            
            values = (
                provider.name,
                provider.provider_type,
                1 if provider.enabled else 0,
                provider.config,
                company_id
            )
            
            result = self.db_manager.execute_query(query, values)
            if result:
                provider_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء مزود SSO: {provider.name} (ID: {provider_id})")
                return provider_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء مزود SSO: {e}", exc_info=True)
            return None
    
    def get_provider(self, provider_id: int) -> Optional[SSOProvider]:
        """الحصول على مزود SSO"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "SELECT * FROM sso_providers WHERE id = ?"
            params = [provider_id]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            row = self.db_manager.fetch_one(query, tuple(params))
            if row:
                return self._row_to_provider(row)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على مزود SSO: {e}", exc_info=True)
            return None
    
    def get_all_providers(self) -> List[SSOProvider]:
        """الحصول على جميع مزودي SSO"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "SELECT * FROM sso_providers WHERE 1=1"
            params = []
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            query += " ORDER BY name"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_provider(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على مزودي SSO: {e}", exc_info=True)
            return []
    
    def update_provider(self, provider: SSOProvider) -> bool:
        """تحديث مزود SSO"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                UPDATE sso_providers SET
                    name = ?, provider_type = ?, enabled = ?,
                    config = ?, updated_at = ?
                WHERE id = ?
            """
            
            params = [
                provider.name,
                provider.provider_type,
                1 if provider.enabled else 0,
                provider.config,
                datetime.now().isoformat(),
                provider.id
            ]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            result = self.db_manager.execute_query(query, tuple(params))
            if result and (hasattr(result, 'rowcount') and result.rowcount > 0 or not hasattr(result, 'rowcount')):
                self.logger.info(f"✅ تم تحديث مزود SSO: {provider.name} (ID: {provider.id})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث مزود SSO: {e}", exc_info=True)
            return False
    
    def delete_provider(self, provider_id: int) -> bool:
        """حذف مزود SSO"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "DELETE FROM sso_providers WHERE id = ?"
            params = [provider_id]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            result = self.db_manager.execute_query(query, tuple(params))
            if result and (hasattr(result, 'rowcount') and result.rowcount > 0 or not hasattr(result, 'rowcount')):
                self.logger.info(f"✅ تم حذف مزود SSO: ID={provider_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حذف مزود SSO: {e}", exc_info=True)
            return False
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def _row_to_provider(self, row: Dict[str, Any]) -> SSOProvider:
        """تحويل صف قاعدة البيانات إلى SSOProvider"""
        return SSOProvider(
            id=row.get("id"),
            name=row.get("name", ""),
            provider_type=row.get("provider_type", SSOProviderType.OAUTH2),
            enabled=bool(row.get("enabled", 0)),
            config=row.get("config", ""),
            company_id=row.get("company_id"),
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


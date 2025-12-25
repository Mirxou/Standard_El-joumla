#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT Authentication للـ REST API
JWT Authentication for REST API
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import secrets

try:
    from PyJWT import PyJWT
except ImportError:
    try:
        import jwt as PyJWT
    except ImportError:
        PyJWT = None

from src.core.database_manager import DatabaseManager
from src.core.security_service import AdvancedSecurityService
from src.core.permission_manager import PermissionManager
from src.utils.logger import setup_logger


class JWTAuthManager:
    """مدير JWT Authentication"""
    
    def __init__(self, db_manager: DatabaseManager, secret_key: Optional[str] = None):
        """
        تهيئة مدير JWT Authentication
        
        Args:
            db_manager: مدير قاعدة البيانات
            secret_key: مفتاح التوقيع (إذا لم يتم تحديده، سيتم إنشاء واحد عشوائي)
        """
        self.db_manager = db_manager
        self.security_service = AdvancedSecurityService(db_manager)
        self.permission_manager = PermissionManager(db_manager)
        self.logger = setup_logger(__name__)
        
        # مفتاح التوقيع (يجب أن يكون آمناً في الإنتاج)
        self.secret_key = secret_key or self._get_or_create_secret_key()
        
        # خوارزمية التوقيع
        self.algorithm = "HS256"
        
        # مدة صلاحية Token (بالساعات)
        self.access_token_expire_hours = 24
        self.refresh_token_expire_days = 30
    
    def _get_or_create_secret_key(self) -> str:
        """الحصول على أو إنشاء مفتاح التوقيع"""
        try:
            # محاولة الحصول من قاعدة البيانات
            result = self.db_manager.fetch_one(
                "SELECT value FROM settings WHERE key = ?",
                ("jwt_secret_key",)
            )
            
            if result:
                return result[0]
            
            # إنشاء مفتاح جديد
            secret_key = secrets.token_urlsafe(32)
            
            # حفظ في قاعدة البيانات
            try:
                self.db_manager.execute_query(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    ("jwt_secret_key", secret_key)
                )
            except Exception:
                # إذا فشل، قد يكون الجدول غير موجود - لا مشكلة
                pass
            
            return secret_key
            
        except Exception:
            # في حالة الخطأ، استخدم مفتاح افتراضي (غير آمن للإنتاج!)
            self.logger.warning("فشل الحصول على مفتاح JWT - استخدام مفتاح افتراضي")
            return "default-secret-key-change-in-production"
    
    def create_access_token(
        self,
        user_id: int,
        username: str,
        company_id: Optional[int] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        إنشاء JWT Access Token
        
        Args:
            user_id: معرف المستخدم
            username: اسم المستخدم
            company_id: معرف الشركة (اختياري)
            expires_delta: مدة الصلاحية (اختياري)
            
        Returns:
            JWT Token كسلسلة نصية
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.access_token_expire_hours)
        
        # بيانات Token
        payload = {
            "sub": str(user_id),  # Subject (User ID)
            "username": username,
            "exp": expire,  # Expiration
            "iat": datetime.utcnow(),  # Issued At
            "type": "access"
        }
        
        if company_id:
            payload["company_id"] = company_id
        
        # إنشاء Token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return token
    
    def create_refresh_token(
        self,
        user_id: int,
        username: str,
        company_id: Optional[int] = None
    ) -> str:
        """
        إنشاء JWT Refresh Token
        
        Args:
            user_id: معرف المستخدم
            username: اسم المستخدم
            company_id: معرف الشركة (اختياري)
            
        Returns:
            JWT Refresh Token كسلسلة نصية
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        if company_id:
            payload["company_id"] = company_id
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return token
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        التحقق من صحة Token
        
        Args:
            token: JWT Token
            token_type: نوع Token ("access" أو "refresh")
            
        Returns:
            بيانات Token إذا كان صالحاً، None خلاف ذلك
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # التحقق من نوع Token
            if payload.get("type") != token_type:
                self.logger.warning(f"نوع Token غير صحيح: {payload.get('type')} != {token_type}")
                return None
            
            # التحقق من انتهاء الصلاحية (يتم تلقائياً في jwt.decode)
            
            return payload
            
        except ExpiredSignatureError:
            self.logger.warning("Token منتهي الصلاحية")
            return None
        except InvalidTokenError as e:
            self.logger.warning(f"Token غير صالح: {e}")
            return None
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من Token: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        مصادقة المستخدم وإنشاء Tokens
        
        Args:
            username: اسم المستخدم
            password: كلمة المرور
            
        Returns:
            بيانات المستخدم مع Tokens إذا نجحت المصادقة، None خلاف ذلك
        """
        try:
            # التحقق من المستخدم في قاعدة البيانات
            # محاولة قراءة company_id مع التعامل مع عدم وجوده
            try:
                user = self.db_manager.fetch_one(
                    """
                    SELECT id, username, full_name, role_id, is_active, 
                           COALESCE(company_id, NULL) as company_id
                    FROM users
                    WHERE (username = ? OR email = ?) AND is_active = 1
                    """,
                    (username, username)
                )
            except Exception as e:
                # إذا فشل الاستعلام بسبب عدم وجود company_id، نجرب بدونها
                self.logger.debug(f"Retrying query without company_id: {e}")
                user = self.db_manager.fetch_one(
                    """
                    SELECT id, username, full_name, role_id, is_active
                    FROM users
                    WHERE (username = ? OR email = ?) AND is_active = 1
                    """,
                    (username, username)
                )
                company_id = None
            
            if not user:
                self.logger.warning(f"مستخدم غير موجود: {username}")
                return None
            
            # التعامل مع النتيجة (قد تكون tuple أو dict)
            if isinstance(user, dict):
                user_id = user.get('id')
                db_username = user.get('username')
                full_name = user.get('full_name')
                role_id = user.get('role_id')
                is_active = user.get('is_active')
                company_id = user.get('company_id', None)
            else:
                # إذا كانت tuple، نتعامل معها حسب عدد الأعمدة
                if len(user) >= 6:
                    user_id, db_username, full_name, role_id, is_active, company_id = user[:6]
                elif len(user) >= 5:
                    user_id, db_username, full_name, role_id, is_active = user[:5]
                    company_id = None
                else:
                    self.logger.error(f"نتيجة غير متوقعة من قاعدة البيانات: {user}")
                    return None
            
            # التحقق من كلمة المرور
            # نحتاج إلى الحصول على كلمة المرور من قاعدة البيانات
            password_result = self.db_manager.fetch_one(
                "SELECT password_hash FROM users WHERE id = ?",
                (user_id,)
            )
            
            if not password_result:
                return None
            
            password_hash = password_result[0]
            
            # التحقق من كلمة المرور (الترتيب: stored_hash, provided_password)
            if not self.security_service.verify_password(password_hash, password):
                self.logger.warning(f"كلمة مرور خاطئة للمستخدم: {username}")
                # تسجيل محاولة فاشلة
                self.security_service.record_failed_login(username)
                return None
            
            # مسح محاولات تسجيل الدخول الفاشلة
            self.security_service.clear_failed_attempts(username)
            
            # التحقق من الحظر
            is_locked, remaining = self.security_service.is_account_locked(username)
            if is_locked:
                self.logger.warning(f"الحساب محظور: {username} - متبقي: {remaining} ثانية")
                return None
            
            # إنشاء Tokens
            access_token = self.create_access_token(user_id, username, company_id)
            refresh_token = self.create_refresh_token(user_id, username, company_id)
            
            # تسجيل جلسة (company_id سيتم تخزينه في Token، ليس في Session)
            session_token = self.security_service.create_session(
                user_id=user_id,
                username=username,
                ip_address=None,  # يمكن إضافة IP من Request لاحقاً
                user_agent=None   # يمكن إضافة User Agent من Request لاحقاً
            )
            
            # تسجيل حدث أمني (company_id سيتم تخزينه في Token، ليس في Event)
            self.security_service.log_security_event(
                event_type="LOGIN",
                user_id=user_id,
                username=username,
                description=f"تسجيل دخول ناجح عبر API",
                severity="INFO"
            )
            
            return {
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "role_id": role_id,
                "company_id": company_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_hours * 3600  # بالثواني
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في مصادقة المستخدم: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        تحديث Access Token باستخدام Refresh Token
        
        Args:
            refresh_token: Refresh Token
            
        Returns:
            Access Token جديد إذا كان Refresh Token صالحاً
        """
        payload = self.verify_token(refresh_token, token_type="refresh")
        
        if not payload:
            return None
        
        user_id = int(payload.get("sub"))
        username = payload.get("username")
        company_id = payload.get("company_id")
        
        # إنشاء Access Token جديد
        access_token = self.create_access_token(user_id, username, company_id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_hours * 3600
        }
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        الحصول على بيانات المستخدم الحالي من Token
        
        Args:
            token: JWT Token
            
        Returns:
            بيانات المستخدم إذا كان Token صالحاً
        """
        payload = self.verify_token(token, token_type="access")
        
        if not payload:
            return None
        
        user_id = int(payload.get("sub"))
        
        try:
            user = self.db_manager.fetch_one(
                """
                SELECT id, username, full_name, role_id, is_active, company_id
                FROM users
                WHERE id = ? AND is_active = 1
                """,
                (user_id,)
            )
            
            if not user:
                return None
            
            user_id, username, full_name, role_id, is_active, company_id = user
            
            return {
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "role_id": role_id,
                "company_id": company_id,
                "is_active": bool(is_active)
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على بيانات المستخدم: {e}")
            return None
    
    def check_permission(self, user_id: int, permission: str, company_id: Optional[int] = None) -> bool:
        """
        التحقق من صلاحية المستخدم
        
        Args:
            user_id: معرف المستخدم
            permission: الصلاحية المطلوبة
            company_id: معرف الشركة (اختياري)
            
        Returns:
            True إذا كان لديه الصلاحية
        """
        return self.permission_manager.check_permission(user_id, permission, company_id)


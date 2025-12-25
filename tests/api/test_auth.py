#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for JWT Authentication
اختبارات وحدة لمصادقة JWT
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import jwt
import sys
from pathlib import Path

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.auth import JWTAuthManager
from src.core.database_manager import DatabaseManager
from src.core.security_service import AdvancedSecurityService


class TestJWTAuthManager:
    """اختبارات مدير JWT Authentication"""
    
    @pytest.fixture
    def db_manager(self):
        """إنشاء DatabaseManager للاختبارات"""
        db = DatabaseManager(db_path=":memory:")
        db.initialize()
        return db
    
    @pytest.fixture
    def auth_manager(self, db_manager):
        """إنشاء JWTAuthManager للاختبارات"""
        return JWTAuthManager(db_manager, secret_key="test-secret-key-for-testing")
    
    def test_auth_manager_init(self, auth_manager):
        """اختبار تهيئة Auth Manager"""
        assert auth_manager is not None
        assert auth_manager.secret_key == "test-secret-key-for-testing"
        assert auth_manager.algorithm == "HS256"
    
    def test_create_access_token(self, auth_manager):
        """اختبار إنشاء Access Token"""
        user_id = 1
        username = "test_user"
        company_id = 1
        
        token = auth_manager.create_access_token(user_id, username, company_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # التحقق من محتوى Token
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["username"] == username
        assert payload["company_id"] == company_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token(self, auth_manager):
        """اختبار إنشاء Refresh Token"""
        user_id = 1
        username = "test_user"
        company_id = 1
        
        token = auth_manager.create_refresh_token(user_id, username, company_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # التحقق من محتوى Token
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["username"] == username
        assert payload["company_id"] == company_id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_token_valid(self, auth_manager):
        """اختبار التحقق من Token صالح"""
        user_id = 1
        username = "test_user"
        
        token = auth_manager.create_access_token(user_id, username)
        payload = auth_manager.verify_token(token, token_type="access")
        
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["username"] == username
        assert payload["type"] == "access"
    
    def test_verify_token_expired(self, auth_manager):
        """اختبار التحقق من Token منتهي الصلاحية"""
        # إنشاء Token منتهي الصلاحية
        payload = {
            "sub": "1",
            "username": "test_user",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "access"
        }
        expired_token = jwt.encode(payload, auth_manager.secret_key, algorithm=auth_manager.algorithm)
        
        result = auth_manager.verify_token(expired_token, token_type="access")
        assert result is None
    
    def test_verify_token_invalid(self, auth_manager):
        """اختبار التحقق من Token غير صالح"""
        invalid_token = "invalid.token.here"
        
        result = auth_manager.verify_token(invalid_token, token_type="access")
        assert result is None
    
    def test_verify_token_wrong_type(self, auth_manager):
        """اختبار التحقق من Token بنوع خاطئ"""
        user_id = 1
        username = "test_user"
        
        # إنشاء refresh token
        refresh_token = auth_manager.create_refresh_token(user_id, username)
        
        # محاولة التحقق منه كـ access token
        result = auth_manager.verify_token(refresh_token, token_type="access")
        assert result is None
    
    @patch('src.api.auth.AdvancedSecurityService')
    def test_authenticate_user_success(self, mock_security_service, auth_manager, db_manager):
        """اختبار مصادقة مستخدم بنجاح"""
        # إعداد Mock
        mock_security_service_instance = Mock()
        mock_security_service_instance.is_account_locked.return_value = (False, 0)
        mock_security_service_instance.verify_password.return_value = True
        mock_security_service_instance.clear_failed_attempts.return_value = None
        
        auth_manager.security_service = mock_security_service_instance
        
        # إعداد قاعدة البيانات
        db_manager.execute_query("""
            INSERT INTO users (id, username, password_hash, full_name, role_id, is_active, company_id)
            VALUES (1, 'test_user', 'hashed_password', 'Test User', 1, 1, 1)
        """)
        
        result = auth_manager.authenticate_user("test_user", "password123")
        
        assert result is not None
        assert result["user_id"] == 1
        assert result["username"] == "test_user"
        assert result["is_active"] == 1
    
    @patch('src.api.auth.AdvancedSecurityService')
    def test_authenticate_user_wrong_password(self, mock_security_service, auth_manager, db_manager):
        """اختبار مصادقة مستخدم بكلمة مرور خاطئة"""
        # إعداد Mock
        mock_security_service_instance = Mock()
        mock_security_service_instance.is_account_locked.return_value = (False, 0)
        mock_security_service_instance.verify_password.return_value = False
        mock_security_service_instance.record_failed_login.return_value = None
        
        auth_manager.security_service = mock_security_service_instance
        
        # إعداد قاعدة البيانات
        db_manager.execute_query("""
            INSERT INTO users (id, username, password_hash, full_name, role_id, is_active, company_id)
            VALUES (1, 'test_user', 'hashed_password', 'Test User', 1, 1, 1)
        """)
        
        result = auth_manager.authenticate_user("test_user", "wrong_password")
        
        assert result is None
    
    @patch('src.api.auth.AdvancedSecurityService')
    def test_authenticate_user_locked_account(self, mock_security_service, auth_manager):
        """اختبار مصادقة مستخدم بحساب محظور"""
        # إعداد Mock
        mock_security_service_instance = Mock()
        mock_security_service_instance.is_account_locked.return_value = (True, 300)  # محظور لمدة 5 دقائق
        
        auth_manager.security_service = mock_security_service_instance
        
        result = auth_manager.authenticate_user("test_user", "password123")
        
        assert result is None
    
    def test_authenticate_user_not_found(self, auth_manager, db_manager):
        """اختبار مصادقة مستخدم غير موجود"""
        result = auth_manager.authenticate_user("nonexistent_user", "password123")
        
        assert result is None
    
    def test_get_current_user(self, auth_manager):
        """اختبار الحصول على المستخدم الحالي من Token"""
        user_id = 1
        username = "test_user"
        company_id = 1
        
        token = auth_manager.create_access_token(user_id, username, company_id)
        user = auth_manager.get_current_user(token)
        
        assert user is not None
        assert user["user_id"] == user_id
        assert user["username"] == username
        assert user["company_id"] == company_id
    
    def test_get_current_user_invalid_token(self, auth_manager):
        """اختبار الحصول على المستخدم الحالي من Token غير صالح"""
        invalid_token = "invalid.token.here"
        user = auth_manager.get_current_user(invalid_token)
        
        assert user is None
    
    def test_refresh_access_token(self, auth_manager):
        """اختبار تحديث Access Token"""
        user_id = 1
        username = "test_user"
        company_id = 1
        
        # إنشاء refresh token
        refresh_token = auth_manager.create_refresh_token(user_id, username, company_id)
        
        # تحديث access token
        new_access_token = auth_manager.refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        assert isinstance(new_access_token, str)
        
        # التحقق من محتوى Token الجديد
        payload = jwt.decode(new_access_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["username"] == username
        assert payload["company_id"] == company_id
        assert payload["type"] == "access"
    
    def test_refresh_access_token_invalid(self, auth_manager):
        """اختبار تحديث Access Token بـ Refresh Token غير صالح"""
        invalid_refresh_token = "invalid.token.here"
        result = auth_manager.refresh_access_token(invalid_refresh_token)
        
        assert result is None
    
    def test_refresh_access_token_wrong_type(self, auth_manager):
        """اختبار تحديث Access Token بـ Access Token بدلاً من Refresh Token"""
        user_id = 1
        username = "test_user"
        
        # إنشاء access token
        access_token = auth_manager.create_access_token(user_id, username)
        
        # محاولة استخدامه كـ refresh token
        result = auth_manager.refresh_access_token(access_token)
        
        assert result is None



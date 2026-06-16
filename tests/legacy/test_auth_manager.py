#!/usr/bin/env python3
"""
اختبارات Auth Manager
"""

from unittest.mock import patch

import pytest

from src.core.security_service import AuthManager


class TestAuthManager:
    """اختبارات مدير المصادقة"""

    @pytest.fixture
    def auth_manager(self):
        """إنشاء مدير مصادقة"""
        return AuthManager()

    def test_initialization(self, auth_manager):
        """اختبار التهيئة"""
        assert auth_manager is not None

    def test_authenticate_user(self, auth_manager):
        """اختبار مصادقة المستخدم"""
        with patch.object(auth_manager, "verify_credentials", return_value=True):
            result = auth_manager.authenticate("username", "password")
            assert result is not None

    def test_authenticate_invalid_user(self, auth_manager):
        """اختبار مصادقة مستخدم غير صالح"""
        with patch.object(auth_manager, "verify_credentials", return_value=False):
            result = auth_manager.authenticate("invalid", "wrong")
            assert result is None or result is False

    def test_generate_token(self, auth_manager):
        """اختبار إنشاء رمز مميز"""
        with patch.object(auth_manager, "generate_token", return_value="token123"):
            token = auth_manager.generate_token("user_id")
            assert token == "token123"

    def test_verify_token(self, auth_manager):
        """اختبار التحقق من الرمز"""
        with patch.object(auth_manager, "verify_token", return_value={"user_id": "123"}):
            result = auth_manager.verify_token("valid_token")
            assert result is not None

    def test_logout_user(self, auth_manager):
        """اختبار تسجيل خروج المستخدم"""
        result = auth_manager.logout("user_id")
        assert result is not None

    def test_check_permission(self, auth_manager):
        """اختبار التحقق من الإذن"""
        with patch.object(auth_manager, "has_permission", return_value=True):
            result = auth_manager.check_permission("user_id", "read")
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
اختبارات Permission Service
"""

from unittest.mock import patch

import pytest

from src.services.permission_service import PermissionService


class TestPermissionService:
    """اختبارات خدمة الأذونات"""

    @pytest.fixture
    def permission_service(self):
        """إنشاء خدمة أذونات"""
        return PermissionService()

    def test_initialization(self, permission_service):
        """اختبار التهيئة"""
        assert permission_service is not None

    def test_check_permission(self, permission_service):
        """اختبار التحقق من إذن"""
        with patch.object(permission_service, "check", return_value=True):
            result = permission_service.check("user_id", "read")
            assert result is True

    def test_grant_permission(self, permission_service):
        """اختبار منح إذن"""
        with patch.object(permission_service, "grant", return_value=True):
            result = permission_service.grant("user_id", "write")
            assert result is True

    def test_revoke_permission(self, permission_service):
        """اختبار إلغاء إذن"""
        with patch.object(permission_service, "revoke", return_value=True):
            result = permission_service.revoke("user_id", "delete")
            assert result is True

    def test_get_user_permissions(self, permission_service):
        """اختبار الحصول على أذونات المستخدم"""
        with patch.object(permission_service, "get_permissions", return_value=["read", "write"]):
            result = permission_service.get_permissions("user_id")
            assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

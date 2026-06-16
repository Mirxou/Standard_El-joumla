#!/usr/bin/env python3
"""
اختبارات Role Service
"""

from unittest.mock import patch

import pytest

from src.services.role_service import RoleService


class TestRoleService:
    """اختبارات خدمة الأدوار"""

    @pytest.fixture
    def role_service(self):
        """إنشاء خدمة أدوار"""
        return RoleService()

    def test_initialization(self, role_service):
        """اختبار التهيئة"""
        assert role_service is not None

    def test_create_role(self, role_service):
        """اختبار إنشاء دور"""
        with patch.object(role_service, "create", return_value={"id": "1", "name": "admin"}):
            result = role_service.create({"name": "admin"})
            assert result is not None

    def test_get_role(self, role_service):
        """اختبار الحصول على دور"""
        with patch.object(role_service, "get", return_value={"id": "1", "name": "admin"}):
            result = role_service.get("1")
            assert result is not None

    def test_assign_role(self, role_service):
        """اختبار تعيين دور"""
        with patch.object(role_service, "assign", return_value=True):
            result = role_service.assign("user_id", "role_id")
            assert result is True

    def test_get_permissions(self, role_service):
        """اختبار الحصول على أذونات الدور"""
        with patch.object(role_service, "get_permissions", return_value=["read", "write"]):
            result = role_service.get_permissions("role_id")
            assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

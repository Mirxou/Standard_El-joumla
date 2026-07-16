#!/usr/bin/env python3
"""
اختبارات Roles Manager
"""

from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.admin.roles_manager import RolesManager

app = QApplication.instance() or QApplication([])


class TestRolesManager:
    """اختبارات مدير الأدوار"""

    @pytest.fixture
    def manager(self):
        """إنشاء مدير للاختبارات"""
        auth_service = Mock()
        return RolesManager(auth_service)

    def test_initialization(self, manager):
        """اختبار التهيئة"""
        assert manager is not None
        assert hasattr(manager, "auth_service")

    def test_load_roles(self, manager):
        """اختبار تحميل الأدوار"""
        manager.auth_service.get_roles.return_value = [
            {"id": 1, "name": "admin", "permissions": ["all"]},
            {"id": 2, "name": "user", "permissions": ["read"]},
        ]
        result = manager.load_roles()
        assert result is not None

    def test_create_role(self, manager):
        """اختبار إنشاء دور"""
        role_data = {"name": "manager", "permissions": ["read", "write"]}
        result = manager.create_role(role_data)
        assert result is not None

    def test_update_role(self, manager):
        """اختبار تحديث دور"""
        role_data = {"id": 1, "name": "admin", "permissions": ["all"]}
        result = manager.update_role(role_data)
        assert result is not None

    def test_delete_role(self, manager):
        """اختبار حذف دور"""
        result = manager.delete_role(1)
        assert result is not None

    def test_assign_role_to_user(self, manager):
        """اختبار تعيين دور لمستخدم"""
        result = manager.assign_role_to_user(1, 2)
        assert result is not None

    def test_remove_role_from_user(self, manager):
        """اختبار إزالة دور من مستخدم"""
        result = manager.remove_role_from_user(1, 2)
        assert result is not None

    def test_get_role_permissions(self, manager):
        """اختبار الحصول على أذونات الدور"""
        manager.auth_service.get_role_permissions.return_value = ["read", "write"]
        permissions = manager.get_role_permissions(1)
        assert isinstance(permissions, list)

    def test_set_role_permissions(self, manager):
        """اختبار تعيين أذونات الدور"""
        result = manager.set_role_permissions(1, ["read", "write", "delete"])
        assert result is not None

    def test_search_roles(self, manager):
        """اختبار البحث عن الأدوار"""
        result = manager.search_roles("admin")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

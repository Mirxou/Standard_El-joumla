#!/usr/bin/env python3
"""
اختبارات Role Based Morpher
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.components.role_based_morpher import RoleBasedMorpher

app = QApplication.instance() or QApplication([])


class TestRoleBasedMorpher:
    """اختبارات المحول القائم على الأدوار"""

    @pytest.fixture
    def morpher(self):
        """إنشاء محول للاختبارات"""
        return RoleBasedMorpher()

    def test_initialization(self, morpher):
        """اختبار التهيئة"""
        assert morpher is not None
        assert hasattr(morpher, "current_role")

    def test_set_role_admin(self, morpher):
        """اختبار تعيين دور المسؤول"""
        morpher.set_role("admin")
        assert morpher.current_role == "admin"

    def test_set_role_cashier(self, morpher):
        """اختبار تعيين دور الكاشير"""
        morpher.set_role("cashier")
        assert morpher.current_role == "cashier"

    def test_set_role_manager(self, morpher):
        """اختبار تعيين دور المدير"""
        morpher.set_role("manager")
        assert morpher.current_role == "manager"

    def test_add_role_config(self, morpher):
        """اختبار إضافة إعدادات دور"""
        config = {
            "visible_widgets": ["sales", "reports"],
            "permissions": ["create", "read"],
        }
        result = morpher.add_role_config("custom", config)
        assert result is not None

    def test_apply_role_config(self, morpher):
        """اختبار تطبيق إعدادات الدور"""
        morpher.set_role("admin")
        result = morpher.apply_role_config()
        assert result is not None

    def test_get_current_permissions(self, morpher):
        """اختبار الحصول على أذونات الدور الحالي"""
        morpher.set_role("admin")
        permissions = morpher.get_current_permissions()
        assert isinstance(permissions, list)

    def test_is_widget_visible_for_role(self, morpher):
        """اختبار التحقق من ظهور عنصر واجهة للدور"""
        morpher.set_role("admin")
        result = morpher.is_widget_visible_for_role("reports")
        assert isinstance(result, bool)

    def test_has_permission(self, morpher):
        """اختبار التحقق من وجود إذن"""
        morpher.set_role("admin")
        result = morpher.has_permission("create")
        assert isinstance(result, bool)

    def test_reset_to_default(self, morpher):
        """اختبار إعادة التعيين للافتراضي"""
        morpher.set_role("custom")
        morpher.reset_to_default()
        assert morpher.current_role == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج الصلاحيات والأدوار - Permission & Role Model Tests
"""

import unittest
from datetime import datetime
from src.models.permission import (
    PermissionAction, ResourceType, UserStatus, Permission, Role
)


class TestPermissionActionEnum(unittest.TestCase):
    """اختبارات تعداد أنواع العمليات"""
    
    def test_permission_action_values(self):
        """اختبار قيم أنواع العمليات"""
        self.assertEqual(PermissionAction.VIEW.value, "عرض")
        self.assertEqual(PermissionAction.CREATE.value, "إنشاء")
        self.assertEqual(PermissionAction.EDIT.value, "تعديل")
        self.assertEqual(PermissionAction.DELETE.value, "حذف")
        self.assertEqual(PermissionAction.APPROVE.value, "موافقة")
        self.assertEqual(PermissionAction.EXPORT.value, "تصدير")
        self.assertEqual(PermissionAction.PRINT.value, "طباعة")
        self.assertEqual(PermissionAction.MANAGE.value, "إدارة كاملة")
    
    def test_all_permission_actions(self):
        """اختبار عدد جميع العمليات"""
        actions = list(PermissionAction)
        self.assertEqual(len(actions), 8)


class TestResourceTypeEnum(unittest.TestCase):
    """اختبارات تعداد أنواع الموارد"""
    
    def test_resource_type_values(self):
        """اختبار قيم أنواع الموارد"""
        self.assertEqual(ResourceType.PRODUCTS.value, "المنتجات")
        self.assertEqual(ResourceType.CUSTOMERS.value, "العملاء")
        self.assertEqual(ResourceType.SUPPLIERS.value, "الموردين")
        self.assertEqual(ResourceType.SALES.value, "المبيعات")
        self.assertEqual(ResourceType.PURCHASES.value, "المشتريات")
        self.assertEqual(ResourceType.INVENTORY.value, "المخزون")
        self.assertEqual(ResourceType.ACCOUNTING.value, "المحاسبة")
        self.assertEqual(ResourceType.REPORTS.value, "التقارير")
    
    def test_all_resource_types(self):
        """اختبار عدد جميع أنواع الموارد"""
        types = list(ResourceType)
        self.assertGreaterEqual(len(types), 15)


class TestUserStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات المستخدم"""
    
    def test_user_status_values(self):
        """اختبار قيم حالات المستخدم"""
        self.assertEqual(UserStatus.ACTIVE.value, "نشط")
        self.assertEqual(UserStatus.INACTIVE.value, "غير نشط")
        self.assertEqual(UserStatus.SUSPENDED.value, "معلق")
        self.assertEqual(UserStatus.LOCKED.value, "مقفل")
    
    def test_all_user_statuses(self):
        """اختبار عدد جميع الحالات"""
        statuses = list(UserStatus)
        self.assertEqual(len(statuses), 4)


class TestPermissionCreation(unittest.TestCase):
    """اختبارات إنشاء الصلاحية"""
    
    def test_permission_default_values(self):
        """اختبار القيم الافتراضية"""
        permission = Permission()
        
        self.assertIsNone(permission.id)
        self.assertEqual(permission.name, "")
        self.assertEqual(permission.code, "")
        self.assertEqual(permission.action, PermissionAction.VIEW)
        self.assertEqual(permission.resource_type, ResourceType.PRODUCTS)
        self.assertFalse(permission.is_system)
    
    def test_permission_with_values(self):
        """اختبار إنشاء صلاحية مع قيم"""
        permission = Permission(
            id=1,
            name="عرض المنتجات",
            code="PRODUCT_VIEW",
            action=PermissionAction.VIEW,
            resource_type=ResourceType.PRODUCTS
        )
        
        self.assertEqual(permission.id, 1)
        self.assertEqual(permission.name, "عرض المنتجات")
        self.assertEqual(permission.code, "PRODUCT_VIEW")


class TestPermissionActions(unittest.TestCase):
    """اختبارات أنواع العمليات"""
    
    def test_permission_view(self):
        """اختبار صلاحية العرض"""
        permission = Permission(
            name="عرض المنتجات",
            action=PermissionAction.VIEW
        )
        
        self.assertEqual(permission.action, PermissionAction.VIEW)
    
    def test_permission_create(self):
        """اختبار صلاحية الإنشاء"""
        permission = Permission(
            name="إنشاء منتج",
            action=PermissionAction.CREATE
        )
        
        self.assertEqual(permission.action, PermissionAction.CREATE)
    
    def test_permission_edit(self):
        """اختبار صلاحية التعديل"""
        permission = Permission(
            name="تعديل منتج",
            action=PermissionAction.EDIT
        )
        
        self.assertEqual(permission.action, PermissionAction.EDIT)
    
    def test_permission_delete(self):
        """اختبار صلاحية الحذف"""
        permission = Permission(
            name="حذف منتج",
            action=PermissionAction.DELETE
        )
        
        self.assertEqual(permission.action, PermissionAction.DELETE)
    
    def test_permission_manage(self):
        """اختبار الإدارة الكاملة"""
        permission = Permission(
            name="إدارة المنتجات",
            action=PermissionAction.MANAGE
        )
        
        self.assertEqual(permission.action, PermissionAction.MANAGE)


class TestPermissionResources(unittest.TestCase):
    """اختبارات أنواع الموارد"""
    
    def test_permission_products(self):
        """اختبار صلاحية المنتجات"""
        permission = Permission(
            name="إدارة المنتجات",
            resource_type=ResourceType.PRODUCTS
        )
        
        self.assertEqual(permission.resource_type, ResourceType.PRODUCTS)
    
    def test_permission_customers(self):
        """اختبار صلاحية العملاء"""
        permission = Permission(
            name="إدارة العملاء",
            resource_type=ResourceType.CUSTOMERS
        )
        
        self.assertEqual(permission.resource_type, ResourceType.CUSTOMERS)
    
    def test_permission_sales(self):
        """اختبار صلاحية المبيعات"""
        permission = Permission(
            name="إدارة المبيعات",
            resource_type=ResourceType.SALES
        )
        
        self.assertEqual(permission.resource_type, ResourceType.SALES)
    
    def test_permission_accounting(self):
        """اختبار صلاحية المحاسبة"""
        permission = Permission(
            name="إدارة المحاسبة",
            resource_type=ResourceType.ACCOUNTING
        )
        
        self.assertEqual(permission.resource_type, ResourceType.ACCOUNTING)


class TestPermissionToDict(unittest.TestCase):
    """اختبارات تحويل الصلاحية إلى قاموس"""
    
    def test_permission_to_dict_basic(self):
        """اختبار التحويل الأساسي"""
        permission = Permission(
            id=1,
            name="عرض المنتجات",
            code="PRODUCT_VIEW"
        )
        
        perm_dict = permission.to_dict()
        
        self.assertEqual(perm_dict['id'], 1)
        self.assertEqual(perm_dict['name'], "عرض المنتجات")
        self.assertEqual(perm_dict['code'], "PRODUCT_VIEW")
    
    def test_permission_to_dict_with_date(self):
        """اختبار التحويل مع التاريخ"""
        created = datetime(2024, 1, 1, 10, 0, 0)
        permission = Permission(
            id=1,
            name="عرض المنتجات",
            created_at=created
        )
        
        perm_dict = permission.to_dict()
        
        self.assertIn("2024-01-01T10:00:00", perm_dict['created_at'])


class TestPermissionFromDict(unittest.TestCase):
    """اختبارات إنشاء صلاحية من قاموس"""
    
    def test_permission_from_dict_basic(self):
        """اختبار الإنشاء الأساسي"""
        data = {
            'id': 1,
            'name': 'عرض المنتجات',
            'code': 'PRODUCT_VIEW',
            'resource_type': 'PRODUCTS',
            'action': 'VIEW'
        }
        
        permission = Permission.from_dict(data)
        
        self.assertEqual(permission.id, 1)
        self.assertEqual(permission.name, 'عرض المنتجات')
        self.assertEqual(permission.action, PermissionAction.VIEW)


class TestPermissionSystem(unittest.TestCase):
    """اختبارات الصلاحيات النظامية"""
    
    def test_permission_system_true(self):
        """اختبار صلاحية نظامية"""
        permission = Permission(
            name="صلاحية نظامية",
            is_system=True
        )
        
        self.assertTrue(permission.is_system)
    
    def test_permission_system_false(self):
        """اختبار صلاحية مخصصة"""
        permission = Permission(
            name="صلاحية مخصصة",
            is_system=False
        )
        
        self.assertFalse(permission.is_system)


class TestRoleCreation(unittest.TestCase):
    """اختبارات إنشاء الدور"""
    
    def test_role_default_values(self):
        """اختبار القيم الافتراضية للدور"""
        role = Role()
        
        self.assertIsNone(role.id)
        self.assertEqual(role.name, "")
        self.assertTrue(role.is_active)
        self.assertEqual(role.permissions, [])
    
    def test_role_with_values(self):
        """اختبار إنشاء دور مع قيم"""
        role = Role(
            id=1,
            name="مدير",
            code="ADMIN",
            description="مدير النظام"
        )
        
        self.assertEqual(role.id, 1)
        self.assertEqual(role.name, "مدير")
        self.assertEqual(role.code, "ADMIN")


class TestRolePermissions(unittest.TestCase):
    """اختبارات الصلاحيات في الدور"""
    
    def test_role_empty_permissions(self):
        """اختبار دور بدون صلاحيات"""
        role = Role(name="دور بدون صلاحيات")
        
        self.assertEqual(len(role.permissions), 0)
    
    def test_role_with_permissions(self):
        """اختبار دور مع صلاحيات"""
        perm1 = Permission(id=1, name="عرض", code="VIEW")
        perm2 = Permission(id=2, name="إنشاء", code="CREATE")
        
        role = Role(
            name="محرر",
            permissions=[perm1, perm2]
        )
        
        self.assertEqual(len(role.permissions), 2)


class TestRoleStatus(unittest.TestCase):
    """اختبارات حالة الدور"""
    
    def test_role_active(self):
        """اختبار دور نشط"""
        role = Role(
            name="مدير",
            is_active=True
        )
        
        self.assertTrue(role.is_active)
    
    def test_role_inactive(self):
        """اختبار دور غير نشط"""
        role = Role(
            name="دور قديم",
            is_active=False
        )
        
        self.assertFalse(role.is_active)


class TestRoleSystem(unittest.TestCase):
    """اختبارات الأدوار النظامية"""
    
    def test_role_system_role(self):
        """اختبار دور نظامي"""
        role = Role(
            name="مدير نظام",
            is_system=True
        )
        
        self.assertTrue(role.is_system)
    
    def test_role_custom_role(self):
        """اختبار دور مخصص"""
        role = Role(
            name="دور مخصص",
            is_system=False
        )
        
        self.assertFalse(role.is_system)


class TestRoleEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""
    
    def test_role_long_name(self):
        """اختبار اسم طويل للدور"""
        long_name = "ا" * 500
        role = Role(name=long_name)
        
        self.assertEqual(len(role.name), 500)
    
    def test_role_special_characters(self):
        """اختبار أحرف خاصة"""
        role = Role(
            name="دور (مخصص) - نسخة 2",
            description="وصف مع علامات @ # $"
        )
        
        self.assertIn("(", role.name)
        self.assertIn("@", role.description)
    
    def test_role_many_permissions(self):
        """اختبار دور بعدد كبير من الصلاحيات"""
        permissions = [
            Permission(id=i, name=f"صلاحية {i}", code=f"PERM_{i}")
            for i in range(50)
        ]
        
        role = Role(
            name="دور شامل",
            permissions=permissions
        )
        
        self.assertEqual(len(role.permissions), 50)


class TestPermissionIntegration(unittest.TestCase):
    """اختبارات التكامل الشاملة"""
    
    def test_permission_complete(self):
        """اختبار صلاحية كاملة"""
        created = datetime(2024, 1, 1, 10, 0, 0)
        permission = Permission(
            id=1,
            name="إدارة المنتجات",
            code="PRODUCT_MANAGE",
            action=PermissionAction.MANAGE,
            resource_type=ResourceType.PRODUCTS,
            description="صلاحية الإدارة الكاملة للمنتجات",
            is_system=True,
            created_at=created
        )
        
        self.assertEqual(permission.id, 1)
        self.assertEqual(permission.action, PermissionAction.MANAGE)
        self.assertTrue(permission.is_system)
    
    def test_role_complete(self):
        """اختبار دور كامل"""
        perms = [
            Permission(id=1, name="عرض", code="VIEW", action=PermissionAction.VIEW),
            Permission(id=2, name="إنشاء", code="CREATE", action=PermissionAction.CREATE),
            Permission(id=3, name="تعديل", code="EDIT", action=PermissionAction.EDIT)
        ]
        
        role = Role(
            id=1,
            name="محرر محتوى",
            code="EDITOR",
            description="دور محرر المحتوى",
            is_system=False,
            is_active=True,
            permissions=perms
        )
        
        self.assertEqual(role.id, 1)
        self.assertEqual(len(role.permissions), 3)
        self.assertTrue(role.is_active)


if __name__ == '__main__':
    unittest.main()

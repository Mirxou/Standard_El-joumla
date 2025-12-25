"""
اختبارات شاملة لنموذج User
Comprehensive tests for User model
"""

import unittest
from datetime import datetime, timedelta
from src.models.user import User, UserRole, Permission, UserManager


class TestUserRoleEnum(unittest.TestCase):
    """اختبارات تعداد أدوار المستخدمين"""

    def test_user_role_admin(self):
        """دور المدير"""
        self.assertEqual(UserRole.ADMIN.value, "مدير")

    def test_user_role_manager(self):
        """دور مدير الفرع"""
        self.assertEqual(UserRole.MANAGER.value, "مدير فرع")

    def test_user_role_cashier(self):
        """دور الكاشير"""
        self.assertEqual(UserRole.CASHIER.value, "كاشير")

    def test_user_role_inventory(self):
        """دور مسؤول المخزون"""
        self.assertEqual(UserRole.INVENTORY.value, "مسؤول مخزون")

    def test_user_role_accountant(self):
        """دور المحاسب"""
        self.assertEqual(UserRole.ACCOUNTANT.value, "محاسب")

    def test_user_role_viewer(self):
        """دور المشاهد"""
        self.assertEqual(UserRole.VIEWER.value, "مشاهد")


class TestPermissionEnum(unittest.TestCase):
    """اختبارات تعداد الصلاحيات"""

    def test_permission_products_view(self):
        """صلاحية عرض المنتجات"""
        self.assertEqual(Permission.PRODUCTS_VIEW.value, "عرض_المنتجات")

    def test_permission_sales_create(self):
        """صلاحية إنشاء المبيعات"""
        self.assertEqual(Permission.SALES_CREATE.value, "إنشاء_المبيعات")

    def test_permission_purchases_view(self):
        """صلاحية عرض المشتريات"""
        self.assertEqual(Permission.PURCHASES_VIEW.value, "عرض_المشتريات")


class TestUserCreation(unittest.TestCase):
    """اختبارات إنشاء مستخدم"""

    def test_user_basic_creation(self):
        """إنشاء مستخدم أساسي"""
        user = User(
            username="ahmed",
            email="ahmed@example.com",
            full_name="أحمد محمد"
        )
        self.assertEqual(user.username, "ahmed")
        self.assertEqual(user.email, "ahmed@example.com")
        self.assertEqual(user.full_name, "أحمد محمد")

    def test_user_default_role(self):
        """الدور الافتراضي للمستخدم"""
        user = User(username="test")
        self.assertEqual(user.role, UserRole.VIEWER.value)

    def test_user_default_active(self):
        """المستخدم نشط افتراضياً"""
        user = User(username="test")
        self.assertTrue(user.is_active)

    def test_user_default_not_locked(self):
        """المستخدم غير مقفول افتراضياً"""
        user = User(username="test")
        self.assertFalse(user.is_locked)

    def test_user_default_permissions_empty(self):
        """الصلاحيات فارغة افتراضياً"""
        user = User(username="test")
        self.assertEqual(len(user.permissions), 0)
        self.assertIsInstance(user.permissions, set)

    def test_user_with_phone(self):
        """مستخدم مع رقم هاتف"""
        user = User(
            username="test",
            phone="+966123456789"
        )
        self.assertEqual(user.phone, "+966123456789")

    def test_user_with_role(self):
        """مستخدم مع دور محدد"""
        user = User(
            username="test",
            role=UserRole.ADMIN.value
        )
        self.assertEqual(user.role, UserRole.ADMIN.value)


class TestUserProperties(unittest.TestCase):
    """اختبارات خصائص المستخدم"""

    def test_user_is_admin_true(self):
        """التحقق من أن المستخدم مدير"""
        user = User(
            username="test",
            role=UserRole.ADMIN.value
        )
        self.assertTrue(user.is_admin)

    def test_user_is_admin_false(self):
        """التحقق من أن المستخدم ليس مدير"""
        user = User(
            username="test",
            role=UserRole.VIEWER.value
        )
        self.assertFalse(user.is_admin)

    def test_password_not_expired_when_none(self):
        """كلمة المرور لم تنته عندما تكون None"""
        user = User(
            username="test",
            password_expires_at=None
        )
        self.assertFalse(user.is_password_expired)

    def test_password_not_expired(self):
        """كلمة المرور لم تنته"""
        future = datetime.now() + timedelta(days=10)
        user = User(
            username="test",
            password_expires_at=future
        )
        self.assertFalse(user.is_password_expired)

    def test_password_expired(self):
        """كلمة المرور انتهت"""
        past = datetime.now() - timedelta(days=1)
        user = User(
            username="test",
            password_expires_at=past
        )
        self.assertTrue(user.is_password_expired)

    def test_days_until_password_expires_none(self):
        """عدد الأيام عندما تكون قيمة الانتهاء None"""
        user = User(
            username="test",
            password_expires_at=None
        )
        self.assertIsNone(user.days_until_password_expires)

    def test_days_until_password_expires(self):
        """عدد الأيام المتبقية لانتهاء كلمة المرور"""
        future = datetime.now() + timedelta(days=5)
        user = User(
            username="test",
            password_expires_at=future
        )
        days = user.days_until_password_expires
        self.assertGreaterEqual(days, 4)
        self.assertLessEqual(days, 5)


class TestUserPermissions(unittest.TestCase):
    """اختبارات صلاحيات المستخدم"""

    def test_admin_has_all_permissions(self):
        """المدير لديه جميع الصلاحيات"""
        user = User(
            username="test",
            role=UserRole.ADMIN.value
        )
        self.assertTrue(user.has_permission(Permission.PRODUCTS_VIEW.value))
        self.assertTrue(user.has_permission(Permission.USERS_MANAGE.value))
        self.assertTrue(user.has_permission(Permission.BACKUP_RESTORE.value))

    def test_non_admin_without_permission(self):
        """المستخدم غير المسؤول بدون صلاحية"""
        user = User(
            username="test",
            role=UserRole.VIEWER.value
        )
        self.assertFalse(user.has_permission(Permission.PRODUCTS_VIEW.value))

    def test_add_permission(self):
        """إضافة صلاحية"""
        user = User(
            username="test",
            role=UserRole.VIEWER.value
        )
        user.add_permission(Permission.PRODUCTS_VIEW.value)
        self.assertTrue(user.has_permission(Permission.PRODUCTS_VIEW.value))

    def test_remove_permission(self):
        """حذف صلاحية"""
        user = User(
            username="test",
            role=UserRole.VIEWER.value
        )
        user.add_permission(Permission.PRODUCTS_VIEW.value)
        user.remove_permission(Permission.PRODUCTS_VIEW.value)
        self.assertFalse(user.has_permission(Permission.PRODUCTS_VIEW.value))

    def test_set_permissions(self):
        """تعيين الصلاحيات"""
        user = User(username="test")
        permissions = [
            Permission.PRODUCTS_VIEW.value,
            Permission.SALES_VIEW.value,
            Permission.REPORTS_VIEW.value
        ]
        user.set_permissions(permissions)
        self.assertEqual(len(user.permissions), 3)
        self.assertTrue(user.has_permission(Permission.PRODUCTS_VIEW.value))
        self.assertTrue(user.has_permission(Permission.SALES_VIEW.value))
        self.assertTrue(user.has_permission(Permission.REPORTS_VIEW.value))

    def test_remove_nonexistent_permission(self):
        """حذف صلاحية غير موجودة"""
        user = User(username="test")
        # يجب ألا يرفع خطأ
        user.remove_permission(Permission.PRODUCTS_VIEW.value)
        self.assertFalse(user.has_permission(Permission.PRODUCTS_VIEW.value))


class TestUserSerialization(unittest.TestCase):
    """اختبارات تسلسل بيانات المستخدم"""

    def test_user_to_dict(self):
        """تحويل المستخدم إلى قاموس"""
        user = User(
            id=1,
            username="ahmed",
            email="ahmed@example.com",
            full_name="أحمد محمد",
            phone="+966123456789",
            role=UserRole.ADMIN.value,
            is_active=True
        )
        user_dict = user.to_dict()
        self.assertEqual(user_dict['id'], 1)
        self.assertEqual(user_dict['username'], "ahmed")
        self.assertEqual(user_dict['email'], "ahmed@example.com")
        self.assertEqual(user_dict['full_name'], "أحمد محمد")
        self.assertEqual(user_dict['role'], UserRole.ADMIN.value)
        self.assertTrue(user_dict['is_active'])


class TestUserAccountManagement(unittest.TestCase):
    """اختبارات إدارة حسابات المستخدمين"""

    def test_user_with_password_hash(self):
        """مستخدم مع كلمة مرور مشفرة"""
        user = User(
            username="test",
            password_hash="hashed_password_123",
            salt="salt_value"
        )
        self.assertEqual(user.password_hash, "hashed_password_123")
        self.assertEqual(user.salt, "salt_value")

    def test_user_locked_account(self):
        """حساب مستخدم مقفول"""
        user = User(
            username="test",
            is_locked=True
        )
        self.assertTrue(user.is_locked)

    def test_user_failed_login_attempts(self):
        """عدد محاولات تسجيل الدخول الفاشلة"""
        user = User(
            username="test",
            failed_login_attempts=3
        )
        self.assertEqual(user.failed_login_attempts, 3)

    def test_user_last_login(self):
        """آخر تسجيل دخول"""
        now = datetime.now()
        user = User(
            username="test",
            last_login=now
        )
        self.assertEqual(user.last_login, now)

    def test_user_last_password_change(self):
        """آخر تغيير كلمة مرور"""
        now = datetime.now()
        user = User(
            username="test",
            last_password_change=now
        )
        self.assertEqual(user.last_password_change, now)


class TestUserEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_user_inactive(self):
        """مستخدم غير نشط"""
        user = User(
            username="test",
            is_active=False
        )
        self.assertFalse(user.is_active)

    def test_user_with_notes(self):
        """مستخدم مع ملاحظات"""
        user = User(
            username="test",
            notes="مستخدم تجريبي"
        )
        self.assertEqual(user.notes, "مستخدم تجريبي")

    def test_user_multiple_roles(self):
        """اختبار جميع الأدوار"""
        roles = [
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.CASHIER,
            UserRole.INVENTORY,
            UserRole.ACCOUNTANT,
            UserRole.VIEWER
        ]
        for role in roles:
            user = User(username="test", role=role.value)
            self.assertEqual(user.role, role.value)

    def test_user_with_id(self):
        """مستخدم مع معرف"""
        user = User(id=100, username="test")
        self.assertEqual(user.id, 100)

    def test_user_created_at_timestamp(self):
        """مستخدم مع وقت الإنشاء"""
        now = datetime.now()
        user = User(
            username="test",
            created_at=now
        )
        self.assertEqual(user.created_at, now)

    def test_user_updated_at_timestamp(self):
        """مستخدم مع وقت التحديث"""
        now = datetime.now()
        user = User(
            username="test",
            updated_at=now
        )
        self.assertEqual(user.updated_at, now)

    def test_user_created_by(self):
        """المستخدم الذي أنشأ هذا المستخدم"""
        user = User(
            username="test",
            created_by=1
        )
        self.assertEqual(user.created_by, 1)


class DummyResult:
    def __init__(self, rowcount=1, lastrowid=1):
        self.rowcount = rowcount
        self.lastrowid = lastrowid


class DummyUserDB:
    def __init__(self):
        self.fetch_one_results = []
        self.fetch_all_results = []
        self.execute_query_calls = []
        self.non_query_calls = []
        self.last_insert_id = 1

    def fetch_one(self, query, params=()):
        self.execute_query_calls.append(("fetch_one", query, params))
        if self.fetch_one_results:
            return self.fetch_one_results.pop(0)
        return None

    def fetch_all(self, query, params=()):
        self.execute_query_calls.append(("fetch_all", query, params))
        if self.fetch_all_results:
            return self.fetch_all_results.pop(0)
        return []

    def execute_non_query(self, query, params=()):
        self.non_query_calls.append((query, params))
        return 1

    def execute_query(self, query, params=()):
        self.execute_query_calls.append(("execute_query", query, params))
        return DummyResult(rowcount=1, lastrowid=self.last_insert_id)

    def get_last_insert_id(self):
        return self.last_insert_id


class TestUserManager(unittest.TestCase):
    def test_create_user_assigns_default_permissions_and_hash(self):
        db = DummyUserDB()
        db.last_insert_id = 42
        manager = UserManager(db)
        user = User(username="viewer", role=UserRole.VIEWER.value)

        user_id = manager.create_user(user, "pass123")

        self.assertEqual(user_id, 42)
        self.assertEqual(user.id, 42)
        self.assertTrue(user.password_hash)
        self.assertTrue(user.salt)

        permission_calls = [c for c in db.execute_query_calls if c[0] == "execute_query" and "user_permissions" in c[1]]
        expected_min = len(UserManager.DEFAULT_PERMISSIONS[UserRole.VIEWER.value])
        self.assertGreaterEqual(len(permission_calls), expected_min)

    def test_create_user_blocks_duplicate_username(self):
        db = DummyUserDB()
        manager = UserManager(db)
        manager.get_user_by_username = lambda username: User(username=username)
        user = User(username="duplicate")

        result = manager.create_user(user, "irrelevant")

        self.assertIsNone(result)
        self.assertIsNone(user.id)

    def test_authenticate_user_locks_after_failures(self):
        db = DummyUserDB()
        manager = UserManager(db)
        manager.max_failed_attempts = 2

        salt = "pepper"
        hashed = manager._hash_password("secret", salt)
        row = (
            1,
            "user",
            "email",
            "full",
            None,
            UserRole.VIEWER.value,
            hashed,
            salt,
            1,
            0,
            1,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        db.fetch_one_results.append(row)

        result = manager.authenticate_user("user", "wrong")

        self.assertIsNone(result)
        last_call = db.execute_query_calls[-1]
        self.assertEqual(last_call[2][0], 2)
        self.assertTrue(last_call[2][1])


if __name__ == '__main__':
    unittest.main()

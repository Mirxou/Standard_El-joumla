"""
اختبارات شاملة لنماذج Dashboard و Permission
Comprehensive tests for Dashboard and Permission models
"""

import unittest
from datetime import datetime, date, timedelta
from src.models.dashboard import KPI, TimeSeriesPoint, ChartSeries, DashboardData
from src.models.permission import (
    PermissionAction,
    ResourceType,
    UserStatus,
    Permission,
    Role,
    User,
    AuditLog,
    LoginHistory,
)


class TestKPI(unittest.TestCase):
    """اختبارات KPI"""

    def test_kpi_creation(self):
        """إنشاء KPI أساسي"""
        kpi = KPI(key="sales", title="المبيعات", value=1000)
        self.assertEqual(kpi.key, "sales")
        self.assertEqual(kpi.title, "المبيعات")
        self.assertEqual(kpi.value, 1000)
        self.assertEqual(kpi.change, 0.0)
        self.assertEqual(kpi.color, "#2196F3")

    def test_kpi_with_all_fields(self):
        """إنشاء KPI بجميع الحقول"""
        kpi = KPI(
            key="profit",
            title="الربح",
            value=5000.50,
            change=15.5,
            change_label="↑ 15.5%",
            unit="دج",
            color="#4CAF50"
        )
        self.assertEqual(kpi.value, 5000.50)
        self.assertEqual(kpi.change, 15.5)
        self.assertEqual(kpi.change_label, "↑ 15.5%")
        self.assertEqual(kpi.unit, "دج")
        self.assertEqual(kpi.color, "#4CAF50")


class TestTimeSeriesPoint(unittest.TestCase):
    """اختبارات نقاط المتسلسلة الزمنية"""

    def test_time_series_point_basic(self):
        """إنشاء نقطة بيانات أساسية"""
        point = TimeSeriesPoint(label="يناير", value=100)
        self.assertEqual(point.label, "يناير")
        self.assertEqual(point.value, 100)
        self.assertIsNone(point.ts)

    def test_time_series_point_with_timestamp(self):
        """إنشاء نقطة بيانات مع timestamp"""
        now = datetime.now()
        point = TimeSeriesPoint(label="اليوم", value=250, ts=now)
        self.assertEqual(point.value, 250)
        self.assertEqual(point.ts, now)


class TestChartSeries(unittest.TestCase):
    """اختبارات سلسلة المخطط"""

    def test_chart_series_basic(self):
        """إنشاء سلسلة مخطط"""
        series = ChartSeries(name="المبيعات")
        self.assertEqual(series.name, "المبيعات")
        self.assertEqual(len(series.points), 0)
        self.assertIsNone(series.color)

    def test_chart_series_with_points(self):
        """سلسلة مخطط مع نقاط"""
        points = [
            TimeSeriesPoint("يناير", 100),
            TimeSeriesPoint("فبراير", 150),
        ]
        series = ChartSeries(name="الإيرادات", points=points, color="#FF9800")
        self.assertEqual(len(series.points), 2)
        self.assertEqual(series.points[0].value, 100)
        self.assertEqual(series.color, "#FF9800")


class TestDashboardData(unittest.TestCase):
    """اختبارات بيانات لوحة المعلومات"""

    def test_dashboard_creation(self):
        """إنشاء لوحة معلومات"""
        today = date.today()
        dashboard = DashboardData(
            period_start=today,
            period_end=today
        )
        self.assertEqual(dashboard.period_start, today)
        self.assertEqual(dashboard.period_end, today)
        self.assertEqual(len(dashboard.kpis), 0)
        self.assertEqual(dashboard.inventory_value, 0.0)

    def test_dashboard_with_data(self):
        """لوحة معلومات مع بيانات"""
        today = date.today()
        kpis = [KPI("sales", "المبيعات", 5000)]
        top_products = [{"name": "Product 1", "sales": 100}]
        
        dashboard = DashboardData(
            period_start=today,
            period_end=today,
            kpis=kpis,
            top_products=top_products,
            inventory_value=50000,
            low_stock_count=5,
            receivables_balance=10000,
            payables_balance=8000,
            active_customers=50,
            active_suppliers=20,
            notes="تقرير شهري"
        )
        
        self.assertEqual(len(dashboard.kpis), 1)
        self.assertEqual(dashboard.kpis[0].value, 5000)
        self.assertEqual(len(dashboard.top_products), 1)
        self.assertEqual(dashboard.inventory_value, 50000)
        self.assertEqual(dashboard.low_stock_count, 5)
        self.assertEqual(dashboard.active_customers, 50)


class TestPermissionEnums(unittest.TestCase):
    """اختبارات Enum الصلاحيات"""

    def test_permission_action_values(self):
        """فحص قيم PermissionAction"""
        self.assertEqual(PermissionAction.VIEW.value, "عرض")
        self.assertEqual(PermissionAction.CREATE.value, "إنشاء")
        self.assertEqual(PermissionAction.EDIT.value, "تعديل")
        self.assertEqual(PermissionAction.DELETE.value, "حذف")
        self.assertEqual(PermissionAction.APPROVE.value, "موافقة")

    def test_resource_type_values(self):
        """فحص قيم ResourceType"""
        self.assertEqual(ResourceType.PRODUCTS.value, "المنتجات")
        self.assertEqual(ResourceType.CUSTOMERS.value, "العملاء")
        self.assertEqual(ResourceType.SALES.value, "المبيعات")

    def test_user_status_values(self):
        """فحص قيم UserStatus"""
        self.assertEqual(UserStatus.ACTIVE.value, "نشط")
        self.assertEqual(UserStatus.INACTIVE.value, "غير نشط")
        self.assertEqual(UserStatus.SUSPENDED.value, "معلق")


class TestPermission(unittest.TestCase):
    """اختبارات Permission"""

    def test_permission_creation(self):
        """إنشاء صلاحية"""
        perm = Permission(
            id=1,
            name="عرض المنتجات",
            code="VIEW_PRODUCTS",
            resource_type=ResourceType.PRODUCTS,
            action=PermissionAction.VIEW
        )
        self.assertEqual(perm.id, 1)
        self.assertEqual(perm.code, "VIEW_PRODUCTS")
        self.assertEqual(perm.resource_type, ResourceType.PRODUCTS)

    def test_permission_to_dict(self):
        """تحويل صلاحية إلى dict"""
        perm = Permission(
            id=1,
            name="إنشاء فاتورة",
            code="CREATE_INVOICE",
            resource_type=ResourceType.SALES,
            action=PermissionAction.CREATE,
            is_system=True
        )
        result = perm.to_dict()
        self.assertEqual(result["name"], "إنشاء فاتورة")
        self.assertEqual(result["code"], "CREATE_INVOICE")
        self.assertEqual(result["resource_type"], "SALES")
        self.assertTrue(result["is_system"])

    def test_permission_from_dict(self):
        """إنشاء صلاحية من dict"""
        data = {
            "id": 2,
            "name": "حذف مستخدم",
            "code": "DELETE_USER",
            "resource_type": "USERS",
            "action": "DELETE",
            "description": "حذف حساب مستخدم",
            "is_system": False,
            "created_at": None
        }
        perm = Permission.from_dict(data)
        self.assertEqual(perm.id, 2)
        self.assertEqual(perm.code, "DELETE_USER")
        self.assertEqual(perm.resource_type, ResourceType.USERS)


class TestRole(unittest.TestCase):
    """اختبارات Role"""

    def test_role_creation(self):
        """إنشاء دور"""
        role = Role(
            id=1,
            name="مدير",
            code="ADMIN",
            description="مدير النظام"
        )
        self.assertEqual(role.id, 1)
        self.assertEqual(role.code, "ADMIN")
        self.assertTrue(role.is_active)
        self.assertEqual(len(role.permissions), 0)

    def test_role_has_permission(self):
        """التحقق من وجود صلاحية في الدور"""
        perm1 = Permission(code="VIEW_PRODUCTS")
        perm2 = Permission(code="CREATE_SALE")
        role = Role(name="مبيعات", permissions=[perm1, perm2])
        
        self.assertTrue(role.has_permission("VIEW_PRODUCTS"))
        self.assertTrue(role.has_permission("CREATE_SALE"))
        self.assertFalse(role.has_permission("DELETE_USER"))

    def test_role_can_perform(self):
        """التحقق من إمكانية تنفيذ عملية"""
        perm = Permission(
            resource_type=ResourceType.PRODUCTS,
            action=PermissionAction.VIEW
        )
        role = Role(name="مشاهد", permissions=[perm])
        
        self.assertTrue(role.can_perform(ResourceType.PRODUCTS, PermissionAction.VIEW))
        self.assertFalse(role.can_perform(ResourceType.PRODUCTS, PermissionAction.DELETE))

    def test_role_to_dict(self):
        """تحويل دور إلى dict"""
        perm = Permission(id=1, name="عرض", code="VIEW")
        role = Role(id=1, name="مشاهد", code="VIEWER", permissions=[perm])
        
        result = role.to_dict()
        self.assertEqual(result["name"], "مشاهد")
        self.assertEqual(len(result["permissions"]), 1)


class TestUser(unittest.TestCase):
    """اختبارات User"""

    def test_user_creation(self):
        """إنشاء مستخدم"""
        user = User(
            id=1,
            username="ahmed",
            full_name="أحمد محمد",
            email="ahmed@example.com"
        )
        self.assertEqual(user.username, "ahmed")
        self.assertEqual(user.status, UserStatus.ACTIVE)
        self.assertFalse(user.is_locked)

    def test_user_is_active(self):
        """فحص تفعيل المستخدم"""
        user = User(status=UserStatus.ACTIVE, is_locked=False)
        self.assertTrue(user.is_active())
        
        user.status = UserStatus.INACTIVE
        self.assertFalse(user.is_active())
        
        user.status = UserStatus.ACTIVE
        user.is_locked = True
        self.assertFalse(user.is_active())

    def test_user_is_active_with_lock_expiry(self):
        """فحص انتهاء قفل المستخدم"""
        user = User(status=UserStatus.ACTIVE, is_locked=True)
        
        # قفل منتهي الصلاحية
        past_time = datetime.now() - timedelta(hours=1)
        user.locked_until = past_time
        
        result = user.is_active()
        self.assertTrue(result)
        self.assertFalse(user.is_locked)
        self.assertEqual(user.failed_login_attempts, 0)

    def test_user_has_permission(self):
        """فحص صلاحية المستخدم"""
        perm = Permission(code="VIEW_PRODUCTS")
        role = Role(name="مشاهد", permissions=[perm])
        user = User(role=role)
        
        self.assertTrue(user.has_permission("VIEW_PRODUCTS"))
        self.assertFalse(user.has_permission("DELETE_USER"))

    def test_user_has_permission_no_role(self):
        """فحص صلاحية مستخدم بدون دور"""
        user = User(role=None)
        self.assertFalse(user.has_permission("ANY"))

    def test_user_can_perform(self):
        """فحص إمكانية تنفيذ عملية"""
        perm = Permission(
            resource_type=ResourceType.PRODUCTS,
            action=PermissionAction.CREATE
        )
        role = Role(name="محرر", permissions=[perm])
        user = User(role=role)
        
        self.assertTrue(user.can_perform(ResourceType.PRODUCTS, PermissionAction.CREATE))
        self.assertFalse(user.can_perform(ResourceType.PRODUCTS, PermissionAction.DELETE))

    def test_user_to_dict(self):
        """تحويل مستخدم إلى dict"""
        user = User(
            id=1,
            username="sara",
            full_name="سارة علي",
            email="sara@example.com",
            password_hash="hashed_pwd"
        )
        result = user.to_dict()
        self.assertEqual(result["username"], "sara")
        self.assertNotIn("password_hash", result)
        
        result_with_pwd = user.to_dict(include_password=True)
        self.assertIn("password_hash", result_with_pwd)

    def test_user_to_dict_with_role(self):
        """تحويل مستخدم مع دور إلى dict"""
        role = Role(id=1, name="مدير")
        user = User(id=1, username="admin", role=role)
        
        result = user.to_dict()
        self.assertIsNotNone(result["role"])
        self.assertEqual(result["role"]["name"], "مدير")


class TestAuditLog(unittest.TestCase):
    """اختبارات AuditLog"""

    def test_audit_log_creation(self):
        """إنشاء سجل تدقيق"""
        log = AuditLog(
            id=1,
            user_id=5,
            username="ahmed",
            action="CREATE",
            resource_type="PRODUCT",
            resource_id=100
        )
        self.assertEqual(log.user_id, 5)
        self.assertEqual(log.action, "CREATE")
        self.assertEqual(log.status, "success")

    def test_audit_log_to_dict(self):
        """تحويل سجل تدقيق إلى dict"""
        log = AuditLog(
            id=1,
            username="admin",
            action="DELETE",
            resource_type="USER",
            resource_id=10,
            status="success"
        )
        result = log.to_dict()
        self.assertEqual(result["action"], "DELETE")
        self.assertEqual(result["resource_type"], "USER")


class TestLoginHistory(unittest.TestCase):
    """اختبارات LoginHistory"""

    def test_login_history_success(self):
        """تسجيل دخول ناجح"""
        history = LoginHistory(
            id=1,
            user_id=1,
            username="user1",
            status="success",
            ip_address="192.168.1.1"
        )
        self.assertEqual(history.status, "success")
        self.assertEqual(history.ip_address, "192.168.1.1")

    def test_login_history_failed(self):
        """تسجيل دخول فاشل"""
        history = LoginHistory(
            user_id=2,
            username="user2",
            status="failed",
            failure_reason="Invalid password"
        )
        self.assertEqual(history.status, "failed")
        self.assertEqual(history.failure_reason, "Invalid password")

    def test_login_history_to_dict(self):
        """تحويل سجل الدخول إلى dict"""
        history = LoginHistory(
            id=1,
            username="test",
            status="success",
            ip_address="127.0.0.1"
        )
        result = history.to_dict()
        self.assertEqual(result["username"], "test")
        self.assertEqual(result["ip_address"], "127.0.0.1")


if __name__ == '__main__':
    unittest.main()




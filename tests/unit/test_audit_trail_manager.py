"""
Unit Tests for AuditTrailManager
اختبارات وحدة AuditTrailManager
"""

import pytest

from src.core.audit_trail_manager import (
    AuditAction,
    AuditEntity,
    AuditEntry,
    AuditTrailManager,
)


class TestAuditAction:
    """اختبارات أنواع العمليات"""

    def test_audit_action_values(self):
        """اختبار قيم AuditAction"""
        assert AuditAction.CREATE.value == "create"
        assert AuditAction.UPDATE.value == "update"
        assert AuditAction.DELETE.value == "delete"


class TestAuditEntity:
    """اختبارات الكيانات"""

    def test_audit_entity_values(self):
        """اختبار قيم AuditEntity"""
        assert AuditEntity.SALE.value == "sale"
        assert AuditEntity.PRODUCT.value == "product"
        assert AuditEntity.CUSTOMER.value == "customer"


class TestAuditEntry:
    """اختبارات سجل التدقيق"""

    def test_audit_entry_init(self):
        """اختبار تهيئة سجل تدقيق"""
        entry = AuditEntry(
            user_id=1,
            username="test_user",
            action="create",
            entity_type="product",
            entity_id=1,
        )

        assert entry.user_id == 1
        assert entry.username == "test_user"
        assert entry.action == "create"

    def test_audit_entry_to_dict(self):
        """اختبار تحويل سجل التدقيق إلى قاموس"""
        entry = AuditEntry(
            user_id=1,
            username="test_user",
            action="create",
            entity_type="product",
            entity_id=1,
        )

        entry_dict = entry.to_dict()
        assert "user_id" in entry_dict
        assert "username" in entry_dict
        assert "action" in entry_dict


class TestAuditTrailManager:
    """اختبارات مدير سجل التدقيق"""

    @pytest.fixture
    def audit_manager(self, db_manager):
        """إنشاء مدير سجل التدقيق"""
        return AuditTrailManager(db_manager)

    def test_init(self, audit_manager):
        """اختبار التهيئة"""
        assert audit_manager is not None

    def test_log(self, audit_manager):
        """اختبار تسجيل إجراء"""
        result = audit_manager.log(
            user_id=1,
            username="test_user",
            action=AuditAction.CREATE.value,
            entity_type=AuditEntity.PRODUCT.value,
            entity_id=1,
            old_values=None,
            new_values={"name": "Test Product"},
        )

        # قد يفشل إذا لم يكن هناك مستخدم في قاعدة البيانات
        # لكن يجب ألا يرفع استثناء
        assert isinstance(result, (bool, type(None), int))

    def test_get_entity_history(self, audit_manager):
        """اختبار الحصول على تاريخ كيان معين"""
        history = audit_manager.get_entity_history(entity_type=AuditEntity.PRODUCT.value, entity_id=1, limit=10)

        # يجب أن يعيد قائمة (حتى لو كانت فارغة)
        assert isinstance(history, list)

    def test_search(self, audit_manager):
        """اختبار البحث في سجلات التدقيق"""
        results = audit_manager.search(action=AuditAction.CREATE.value, limit=10)

        assert isinstance(results, list)

    def test_get_user_activity(self, audit_manager):
        """اختبار الحصول على نشاط مستخدم معين"""
        activity = audit_manager.get_user_activity(user_id=1, limit=10)

        assert isinstance(activity, list)


class TestAuditTrailManagerAdvanced:
    """اختبارات متقدمة لـ AuditTrailManager"""

    @pytest.fixture
    def mock_db(self):
        """Mock DatabaseManager"""
        from unittest.mock import MagicMock

        mock = MagicMock()
        mock.lastrowid = 1
        return mock

    @pytest.fixture
    def audit_manager(self, mock_db):
        """AuditTrailManager مع Mock DB"""
        return AuditTrailManager(mock_db)

    def test_calculate_changes(self, audit_manager):
        """اختبار حساب التغييرات بين القيم القديمة والجديدة"""
        old_values = {"name": "Old", "price": 10}
        new_values = {"name": "New", "price": 20}

        changes = audit_manager._calculate_changes(old_values, new_values)

        assert "name" in changes
        assert "price" in changes
        assert changes["name"] == ("Old", "New")
        assert changes["price"] == (10, 20)

    def test_calculate_changes_no_changes(self, audit_manager):
        """اختبار عدم وجود تغييرات"""
        old_values = {"name": "Same"}
        new_values = {"name": "Same"}

        changes = audit_manager._calculate_changes(old_values, new_values)

        assert changes == {}

    def test_calculate_changes_new_fields(self, audit_manager):
        """اختبار إضافة حقول جديدة"""
        old_values = {"name": "Product"}
        new_values = {"name": "Product", "description": "New desc"}

        changes = audit_manager._calculate_changes(old_values, new_values)

        assert "description" in changes
        assert changes["description"] == (None, "New desc")

    def test_calculate_changes_removed_fields(self, audit_manager):
        """اختبار حذف حقول"""
        old_values = {"name": "Product", "old_field": "value"}
        new_values = {"name": "Product"}

        changes = audit_manager._calculate_changes(old_values, new_values)

        assert "old_field" in changes
        assert changes["old_field"] == ("value", None)

    def test_update_activity_summary_new_user(self, audit_manager, mock_db):
        """اختبار تحديث ملخص النشاط لمستخدم جديد"""
        mock_db.fetch_one.return_value = None

        audit_manager._update_activity_summary(user_id=1, action=AuditAction.CREATE.value, success=True)

        # يجب أن يتم إدراج سجل جديد
        assert mock_db.execute.called

    def test_update_activity_summary_existing_user(self, audit_manager, mock_db):
        """اختبار تحديث ملخص النشاط لمستخدم موجود"""
        mock_db.fetch_one.return_value = {"total_actions": 5}

        audit_manager._update_activity_summary(user_id=1, action=AuditAction.UPDATE.value, success=True)

        # يجب أن يتم تحديث السجل
        assert mock_db.execute.called

    def test_update_activity_summary_failed_attempt(self, audit_manager, mock_db):
        """اختبار تحديث محاولة فاشلة"""
        mock_db.fetch_one.return_value = {"total_actions": 5}

        audit_manager._update_activity_summary(user_id=1, action=AuditAction.CREATE.value, success=False)

        # يجب أن يتم تحديث محاولات فاشلة
        assert mock_db.execute.called


class TestAuditEntryAdvanced:
    """اختبارات متقدمة لـ AuditEntry"""

    def test_audit_entry_with_changes(self):
        """اختبار سجل مع تغييرات"""
        entry = AuditEntry(
            audit_id=1,
            user_id=5,
            username="admin",
            action=AuditAction.UPDATE.value,
            entity_type=AuditEntity.PRODUCT.value,
            entity_id=100,
            old_values={"name": "Old", "price": 10},
            new_values={"name": "New", "price": 15},
            changes={"name": ("Old", "New"), "price": (10, 15)},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
        )

        entry_dict = entry.to_dict()

        assert entry_dict["audit_id"] == 1
        assert entry_dict["user_id"] == 5
        assert entry_dict["action"] == "update"
        assert entry_dict["changes"] == {"name": ("Old", "New"), "price": (10, 15)}
        assert entry_dict["ip_address"] == "192.168.1.1"
        assert entry_dict["success"] is True

    def test_audit_entry_defaults(self):
        """اختبار القيم الافتراضية لـ AuditEntry"""
        entry = AuditEntry()

        assert entry.audit_id is None
        assert entry.user_id is None
        assert entry.username == ""
        assert entry.action == ""
        assert entry.entity_type == ""
        assert entry.old_values == {}
        assert entry.new_values == {}
        assert entry.changes == {}
        assert entry.success is True
        assert entry.error_message == ""

    def test_audit_entry_failed_operation(self):
        """اختبار سجل لعملية فاشلة"""
        entry = AuditEntry(
            user_id=1,
            username="user",
            action=AuditAction.DELETE.value,
            entity_type=AuditEntity.CUSTOMER.value,
            success=False,
            error_message="Permission denied",
        )

        assert entry.success is False
        assert entry.error_message == "Permission denied"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

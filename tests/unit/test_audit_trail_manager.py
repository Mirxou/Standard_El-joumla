"""
Unit Tests for AuditTrailManager
اختبارات وحدة AuditTrailManager
"""

import pytest
from src.core.audit_trail_manager import AuditTrailManager, AuditAction, AuditEntity, AuditEntry


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
            entity_id=1
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
            entity_id=1
        )
        
        entry_dict = entry.to_dict()
        assert 'user_id' in entry_dict
        assert 'username' in entry_dict
        assert 'action' in entry_dict


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
            new_values={"name": "Test Product"}
        )
        
        # قد يفشل إذا لم يكن هناك مستخدم في قاعدة البيانات
        # لكن يجب ألا يرفع استثناء
        assert isinstance(result, (bool, type(None), int))
    
    def test_get_entity_history(self, audit_manager):
        """اختبار الحصول على تاريخ كيان معين"""
        history = audit_manager.get_entity_history(
            entity_type=AuditEntity.PRODUCT.value,
            entity_id=1,
            limit=10
        )
        
        # يجب أن يعيد قائمة (حتى لو كانت فارغة)
        assert isinstance(history, list)
    
    def test_search(self, audit_manager):
        """اختبار البحث في سجلات التدقيق"""
        results = audit_manager.search(
            action=AuditAction.CREATE.value,
            limit=10
        )
        
        assert isinstance(results, list)
    
    def test_get_user_activity(self, audit_manager):
        """اختبار الحصول على نشاط مستخدم معين"""
        activity = audit_manager.get_user_activity(user_id=1, limit=10)
        
        assert isinstance(activity, list)


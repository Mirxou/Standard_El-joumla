"""
Unit Tests for Sync Engine
اختبارات وحدة محرك المزامنة
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.sync_engine import SyncDirection, SyncEngine, SyncResult, SyncStatus


class TestSyncDirection:
    """اختبارات اتجاهات المزامنة"""

    def test_sync_direction_values(self):
        """اختبار قيم SyncDirection"""
        assert SyncDirection.UP.value == "UP"
        assert SyncDirection.DOWN.value == "DOWN"
        assert SyncDirection.BOTH.value == "BOTH"


class TestSyncStatus:
    """اختبارات حالات المزامنة"""

    def test_sync_status_values(self):
        """اختبار قيم SyncStatus"""
        assert SyncStatus.PENDING.value == "PENDING"
        assert SyncStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert SyncStatus.SUCCESS.value == "SUCCESS"
        assert SyncStatus.FAILED.value == "FAILED"
        assert SyncStatus.CONFLICT.value == "CONFLICT"


class TestSyncResult:
    """اختبارات نتيجة المزامنة"""

    def test_sync_result_creation(self):
        """اختبار إنشاء SyncResult"""
        result = SyncResult(
            success=True,
            status=SyncStatus.SUCCESS,
            direction=SyncDirection.UP,
            entity_type="product",
            entity_id=1,
            local_hash="abc123",
            remote_hash="abc123",
            conflict_detected=False,
            execution_time_ms=100,
            data_size_bytes=1024,
        )

        assert result.success is True
        assert result.status == SyncStatus.SUCCESS
        assert result.direction == SyncDirection.UP
        assert result.entity_type == "product"
        assert result.entity_id == 1
        assert result.local_hash == "abc123"
        assert result.remote_hash == "abc123"
        assert result.conflict_detected is False
        assert result.execution_time_ms == 100
        assert result.data_size_bytes == 1024

    def test_sync_result_failure(self):
        """اختبار SyncResult فاشل"""
        result = SyncResult(
            success=False,
            status=SyncStatus.FAILED,
            direction=SyncDirection.UP,
            entity_type="product",
            entity_id=1,
            error_message="Connection timeout",
            execution_time_ms=5000,
        )

        assert result.success is False
        assert result.status == SyncStatus.FAILED
        assert result.error_message == "Connection timeout"

    def test_sync_result_conflict(self):
        """اختبار SyncResult مع تعارض"""
        result = SyncResult(
            success=False,
            status=SyncStatus.CONFLICT,
            direction=SyncDirection.BOTH,
            entity_type="sale",
            entity_id=100,
            local_hash="hash1",
            remote_hash="hash2",
            conflict_detected=True,
            error_message="Version conflict detected",
        )

        assert result.conflict_detected is True
        assert result.status == SyncStatus.CONFLICT
        assert result.local_hash != result.remote_hash


class TestSyncEngine:
    """اختبارات SyncEngine"""

    @pytest.fixture
    def mock_db(self):
        """Mock DatabaseManager"""
        return MagicMock()

    @pytest.fixture
    def sync_engine(self, mock_db):
        """SyncEngine مع Mock DB"""
        return SyncEngine(mock_db)

    def test_sync_engine_initialization(self, sync_engine, mock_db):
        """اختبار تهيئة SyncEngine"""
        assert sync_engine.db_manager == mock_db
        assert sync_engine.logger is not None


class TestSyncEngineHash:
    """اختبارات حساب Hash"""

    @pytest.fixture
    def sync_engine(self):
        return SyncEngine(MagicMock())

    def test_calculate_hash_with_dict(self, sync_engine):
        """اختبار حساب Hash لقاموس"""
        data = {"name": "Product", "price": 100}
        hash_result = sync_engine.calculate_hash(data)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 hex length

    def test_calculate_hash_consistent(self, sync_engine):
        """اختبار أن Hash ثابت للبيانات المتطابقة"""
        data = {"name": "Product", "price": 100}
        hash1 = sync_engine.calculate_hash(data)
        hash2 = sync_engine.calculate_hash(data)

        assert hash1 == hash2

    def test_calculate_hash_different_order(self, sync_engine):
        """اختبار أن Hash ثابت بغض النظر عن ترتيب المفاتيح"""
        data1 = {"name": "Product", "price": 100}
        data2 = {"price": 100, "name": "Product"}
        hash1 = sync_engine.calculate_hash(data1)
        hash2 = sync_engine.calculate_hash(data2)

        assert hash1 == hash2

    def test_calculate_hash_different_data(self, sync_engine):
        """اختبار أن Hash مختلف للبيانات المختلفة"""
        data1 = {"name": "Product1", "price": 100}
        data2 = {"name": "Product2", "price": 100}
        hash1 = sync_engine.calculate_hash(data1)
        hash2 = sync_engine.calculate_hash(data2)

        assert hash1 != hash2

    def test_calculate_hash_empty_dict(self, sync_engine):
        """اختبار حساب Hash لقاموس فارغ"""
        data = {}
        hash_result = sync_engine.calculate_hash(data)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64


class TestSyncEngineVersionComparison:
    """اختبارات مقارنة الإصدارات"""

    @pytest.fixture
    def sync_engine(self):
        return SyncEngine(MagicMock())

    def test_compare_versions_local_newer(self, sync_engine):
        """اختبار الإصدار المحلي أحدث"""
        result = sync_engine.compare_versions(5, 3)
        assert result == "LOCAL_NEWER"

    def test_compare_versions_remote_newer(self, sync_engine):
        """اختبار الإصدار السحابي أحدث"""
        result = sync_engine.compare_versions(2, 5)
        assert result == "REMOTE_NEWER"

    def test_compare_versions_same(self, sync_engine):
        """اختبار الإصداران متطابقان"""
        result = sync_engine.compare_versions(3, 3)
        assert result == "SAME"


class TestSyncEngineConflictDetection:
    """اختبارات اكتشاف التعارض"""

    @pytest.fixture
    def sync_engine(self):
        return SyncEngine(MagicMock())

    def test_detect_conflict_no_conflict(self, sync_engine):
        """اختبار عدم وجود تعارض عند البيانات متطابقة"""
        local_data = {"name": "Product", "price": 100}
        remote_data = {"name": "Product", "price": 100}

        result = sync_engine.detect_conflict(local_data, remote_data, 1, 1)

        assert result is False

    def test_detect_conflict_different_versions(self, sync_engine):
        """اختبار عدم وجود تعارض عند الإصدارات مختلفة"""
        local_data = {"name": "Old", "price": 100}
        remote_data = {"name": "New", "price": 150}

        # إصدار محلي أحدث - لا يوجد تعارض حقيقي
        result = sync_engine.detect_conflict(local_data, remote_data, 2, 1)

        # لا يوجد تعارض لأن أحد الإصدارات أحدث
        assert result is False

    def test_detect_conflict_with_none_data(self, sync_engine):
        """اختبار اكتشاف التعارض مع بيانات فارغة"""
        local_data = {"name": "Product"}

        result = sync_engine.detect_conflict(local_data, None, 1, 1)

        assert result is False

    def test_detect_conflict_same_version_different_data(self, sync_engine):
        """اختبار التعارض عند نفس الإصدار وبيانات مختلفة"""
        local_data = {"name": "Version A", "price": 100}
        remote_data = {"name": "Version B", "price": 150}

        # نفس الإصدار مع بيانات مختلفة
        result = sync_engine.detect_conflict(local_data, remote_data, 1, 1)

        # يجب أن يكتشف التعارض
        assert result is True


class TestSyncEngineSyncEntity:
    """اختبارات مزامنة كيان"""

    @pytest.fixture
    def mock_db(self):
        mock = MagicMock()
        mock.fetch_one.return_value = None
        return mock

    @pytest.fixture
    def sync_engine(self, mock_db):
        return SyncEngine(mock_db)

    def test_sync_entity_local_newer(self, sync_engine, mock_db):
        """اختبار مزامنة عندما يكون المحلي أحدث"""
        local_data = {"name": "Product", "version": 2}
        remote_data = {"name": "Product", "version": 1}

        result = sync_engine.sync_entity(
            entity_type="product",
            entity_id=1,
            local_data=local_data,
            remote_data=remote_data,
            local_version=2,
            remote_version=1,
            direction=SyncDirection.BOTH,
        )

        assert result.success is True
        assert result.status == SyncStatus.SUCCESS
        assert result.conflict_detected is False

    def test_sync_entity_remote_newer(self, sync_engine):
        """اختبار مزامنة عندما يكون السحابي أحدث"""
        local_data = {"name": "Product", "version": 1}
        remote_data = {"name": "Product", "version": 2}

        result = sync_engine.sync_entity(
            entity_type="product",
            entity_id=1,
            local_data=local_data,
            remote_data=remote_data,
            local_version=1,
            remote_version=2,
            direction=SyncDirection.BOTH,
        )

        assert result.success is True
        assert result.status == SyncStatus.SUCCESS

    def test_sync_entity_conflict(self, sync_engine):
        """اختبار مزامنة مع تعارض"""
        local_data = {"name": "Local Version", "version": 2}
        remote_data = {"name": "Remote Version", "version": 2}

        result = sync_engine.sync_entity(
            entity_type="product",
            entity_id=1,
            local_data=local_data,
            remote_data=remote_data,
            local_version=2,
            remote_version=2,
            direction=SyncDirection.BOTH,
        )

        assert result.success is False
        assert result.status == SyncStatus.CONFLICT
        assert result.conflict_detected is True

    def test_sync_entity_force_up(self, sync_engine):
        """اختبار مزامنة UP قسري"""
        local_data = {"name": "Product"}

        result = sync_engine.sync_entity(
            entity_type="product",
            entity_id=1,
            local_data=local_data,
            remote_data=None,
            local_version=1,
            remote_version=0,
            direction=SyncDirection.UP,
        )

        assert result.success is True
        assert result.direction == SyncDirection.UP

    def test_sync_entity_force_down(self, sync_engine):
        """اختبار مزامنة DOWN قسري"""
        local_data = {"name": "Old"}
        remote_data = {"name": "New"}

        result = sync_engine.sync_entity(
            entity_type="product",
            entity_id=1,
            local_data=local_data,
            remote_data=remote_data,
            local_version=1,
            remote_version=2,
            direction=SyncDirection.DOWN,
        )

        assert result.success is True
        assert result.direction == SyncDirection.DOWN


class TestSyncEngineSyncState:
    """اختبارات حالة المزامنة"""

    @pytest.fixture
    def mock_db(self):
        mock = MagicMock()
        return mock

    @pytest.fixture
    def sync_engine(self, mock_db):
        return SyncEngine(mock_db)

    def test_get_sync_state_existing(self, sync_engine, mock_db):
        """اختبار الحصول على حالة موجودة"""
        mock_db.fetch_one.return_value = {
            "sync_settings_id": 1,
            "entity_type": "product",
            "entity_id": 100,
            "local_version": 5,
            "remote_version": 5,
            "local_hash": "abc123",
            "remote_hash": "abc123",
        }

        result = sync_engine.get_sync_state(1, "product", 100)

        assert result is not None
        assert result["entity_type"] == "product"
        assert result["local_version"] == 5

    def test_get_sync_state_nonexistent(self, sync_engine, mock_db):
        """اختبار الحصول على حالة غير موجودة"""
        mock_db.fetch_one.return_value = None

        result = sync_engine.get_sync_state(1, "product", 999)

        assert result is None

    def test_update_sync_state_new(self, sync_engine, mock_db):
        """اختبار تحديث حالة جديدة"""
        mock_db.fetch_one.return_value = None

        sync_engine.update_sync_state(
            sync_settings_id=1,
            entity_type="product",
            entity_id=100,
            local_version=1,
            remote_version=1,
            local_hash="hash1",
            remote_hash="hash1",
        )

        # يجب أن يتم إدراج سجل جديد (INSERT)
        assert mock_db.execute_query.called

    def test_update_sync_state_existing(self, sync_engine, mock_db):
        """اختبار تحديث حالة موجودة"""
        mock_db.fetch_one.return_value = {"id": 1}

        sync_engine.update_sync_state(
            sync_settings_id=1,
            entity_type="product",
            entity_id=100,
            local_version=2,
            remote_version=2,
            local_hash="hash2",
            remote_hash="hash2",
        )

        # يجب أن يتم تحديث السجل (UPDATE)
        assert mock_db.execute_query.called


class TestSyncEngineErrorHandling:
    """اختبارات معالجة الأخطاء"""

    @pytest.fixture
    def mock_db(self):
        mock = MagicMock()
        mock.fetch_one.side_effect = Exception("Database error")
        return mock

    @pytest.fixture
    def sync_engine(self, mock_db):
        return SyncEngine(mock_db)

    def test_sync_entity_exception(self, sync_engine):
        """اختبار معالجة استثناء في مزامنة الكيان"""
        local_data = {"name": "Product"}

        with patch.object(sync_engine, "calculate_hash", side_effect=Exception("Calculation error")):
            result = sync_engine.sync_entity(
                entity_type="product",
                entity_id=1,
                local_data=local_data,
                remote_data=None,
                local_version=1,
                remote_version=0,
                direction=SyncDirection.UP,
            )

        assert result.success is False
        assert result.status == SyncStatus.FAILED
        assert "Calculation error" in result.error_message

    def test_get_sync_state_exception(self, sync_engine):
        """اختبار معالجة استثناء في الحصول على الحالة"""
        result = sync_engine.get_sync_state(1, "product", 100)

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Delta Sync
اختبارات Delta Sync
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.api.delta_sync import DeltaSyncManager


class TestDeltaSyncInitialization:
    """اختبارات تهيئة Delta Sync Manager"""

    def test_initialization_with_mock_db(self):
        """اختبار التهيئة باستخدام Mock database"""
        mock_db = Mock()
        mock_db.get_last_synced_at.return_value = datetime.now()

        manager = DeltaSyncManager(mock_db)

        assert manager.local_db == mock_db

    def test_initialization_with_none_db(self):
        """اختبار التهيئة بدون database"""
        manager = DeltaSyncManager(None)

        assert manager.local_db is None


class TestGetPendingCount:
    """اختبارات الحصول على عدد العناصر المعلقة"""

    @pytest.fixture
    def mock_db(self):
        """إنشاء Mock database"""
        db = Mock()
        db.get_last_synced_at.return_value = datetime.now()
        return db

    @pytest.fixture
    def delta_sync(self, mock_db):
        """إنشاء Delta Sync Manager"""
        return DeltaSyncManager(mock_db)

    def test_get_pending_count_for_table(self, delta_sync, mock_db):
        """اختبار الحصول على عدد العناصر المعلقة لجدول محدد"""
        mock_db.execute_query.return_value = [{"count": 5}]

        result = delta_sync.get_pending_count("products")

        assert result == 5
        mock_db.execute_query.assert_called_once()
        # التحقق من أن الاستعلام يحتوي على اسم الجدول
        query = mock_db.execute_query.call_args[0][0]
        assert "products" in query

    def test_get_pending_count_empty_result(self, delta_sync, mock_db):
        """اختبار الحصول على عدد العناصر مع نتيجة فارغة"""
        mock_db.execute_query.return_value = []

        result = delta_sync.get_pending_count("customers")

        assert result == 0

    def test_get_pending_count_total(self, delta_sync, mock_db):
        """اختبار الحصول على الإجمالي من جميع الجداول"""
        # محاكاة القيم لجميع الجداول
        mock_db.execute_query.side_effect = [
            [{"count": 1}],  # products
            [{"count": 2}],  # customers
            [{"count": 0}],  # sales
            [{"count": 0}],  # sale_items
            [{"count": 1}],  # batches
            [{"count": 0}],  # categories
            [{"count": 1}],  # suppliers
        ]

        result = delta_sync.get_pending_count()

        assert result == 5  # 1 + 2 + 0 + 0 + 1 + 0 + 1
        assert mock_db.execute_query.call_count == 7

    def test_get_pending_count_no_db(self):
        """اختبار الحصول على العدد بدون database"""
        delta_sync = DeltaSyncManager(None)

        result = delta_sync.get_pending_count("products")

        assert result == 0


class TestGetSyncSummary:
    """اختبارات الحصول على ملخص حالة المزامنة"""

    @pytest.fixture
    def mock_db(self):
        """إنشاء Mock database"""
        db = Mock()
        db.get_last_synced_at.return_value = datetime(2024, 1, 15, 10, 30, 0)
        return db

    @pytest.fixture
    def delta_sync(self, mock_db):
        """إنشاء Delta Sync Manager"""
        return DeltaSyncManager(mock_db)

    def test_get_sync_summary(self, delta_sync, mock_db):
        """اختبار الحصول على ملخص المزامنة"""
        # محاكاة القيم لجميع الجداول
        mock_db.execute_query.side_effect = [
            [{"count": 1}],  # products
            [{"count": 2}],  # customers
            [{"count": 0}],  # sales
            [{"count": 0}],  # sale_items
            [{"count": 1}],  # batches
            [{"count": 0}],  # categories
            [{"count": 1}],  # suppliers
        ]

        result = delta_sync.get_sync_summary()

        assert result["last_synced_at"] == "2024-01-15T10:30:00"
        assert result["pending_count"] == 5
        assert result["table_counts"]["products"] == 1
        assert result["table_counts"]["customers"] == 2
        assert result["table_counts"]["sales"] == 0
        assert result["is_synced"] is False

    def test_get_sync_summary_fully_synced(self, delta_sync, mock_db):
        """اختبار المزامنة الكاملة"""
        # محاكاة القيم الصفرية لجميع الجداول (مزامنة كاملة)
        mock_db.execute_query.return_value = [{"count": 0}]

        result = delta_sync.get_sync_summary()

        assert result["pending_count"] == 0
        assert result["is_synced"] is True

    def test_get_sync_summary_no_last_sync(self, delta_sync, mock_db):
        """اختبار بدون تاريخ آخر مزامنة"""
        mock_db.get_last_synced_at.return_value = None
        mock_db.execute_query.return_value = [{"count": 0}]

        result = delta_sync.get_sync_summary()

        assert result["last_synced_at"] is None
        assert result["is_synced"] is True

    def test_get_sync_summary_no_db(self):
        """اختبار بدون database"""
        delta_sync = DeltaSyncManager(None)

        result = delta_sync.get_sync_summary()

        assert result["last_synced_at"] is None
        assert result["pending_count"] == 0
        assert result["is_synced"] is True


class TestDeltaSyncAdvanced:
    """اختبارات متقدمة لـ Delta Sync"""

    @pytest.fixture
    def mock_db(self):
        """إنشاء Mock database"""
        db = Mock()
        db.get_last_synced_at.return_value = datetime.now()
        return db

    @pytest.fixture
    def delta_sync(self, mock_db):
        """إنشاء Delta Sync Manager"""
        return DeltaSyncManager(mock_db)

    def test_get_pending_count_with_deleted_items(self, delta_sync, mock_db):
        """اختبار العدد مع العناصر المحذوفة"""
        mock_db.execute_query.return_value = [{"count": 3}]

        result = delta_sync.get_pending_count("products")

        assert result == 3
        # التحقق من أن الاستعلام يستبعد العناصر المحذوفة
        query = mock_db.execute_query.call_args[0][0]
        assert "is_deleted = 0" in query

    def test_get_pending_count_with_synced_items(self, delta_sync, mock_db):
        """اختبار العدد مع العناصر المزامنة"""
        mock_db.execute_query.return_value = [{"count": 2}]

        result = delta_sync.get_pending_count("customers")

        assert result == 2
        # التحقق من أن الاستعلام يستبعد العناصر المزامنة
        query = mock_db.execute_query.call_args[0][0]
        assert "is_synced = 0" in query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

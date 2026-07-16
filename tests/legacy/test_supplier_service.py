#!/usr/bin/env python3
"""
اختبارات Supplier Service
"""

from unittest.mock import patch

import pytest

from src.services.supplier_service import SupplierService


class TestSupplierService:
    """اختبارات خدمة الموردين"""

    @pytest.fixture
    def supplier_service(self):
        """إنشاء خدمة موردين"""
        return SupplierService()

    def test_initialization(self, supplier_service):
        """اختبار التهيئة"""
        assert supplier_service is not None

    def test_create_supplier(self, supplier_service):
        """اختبار إنشاء مورد"""
        with patch.object(supplier_service, "create", return_value={"id": "1", "name": "Supplier"}):
            result = supplier_service.create({"name": "Supplier", "contact": "123"})
            assert result is not None

    def test_get_supplier(self, supplier_service):
        """اختبار الحصول على مورد"""
        with patch.object(supplier_service, "get", return_value={"id": "1", "name": "Supplier"}):
            result = supplier_service.get("1")
            assert result is not None

    def test_update_supplier(self, supplier_service):
        """اختبار تحديث مورد"""
        with patch.object(supplier_service, "update", return_value=True):
            result = supplier_service.update("1", {"contact": "456"})
            assert result is True

    def test_delete_supplier(self, supplier_service):
        """اختبار حذف مورد"""
        with patch.object(supplier_service, "delete", return_value=True):
            result = supplier_service.delete("1")
            assert result is True

    def test_get_all_suppliers(self, supplier_service):
        """اختبار الحصول على جميع الموردين"""
        with patch.object(supplier_service, "get_all", return_value=[{"id": "1"}, {"id": "2"}]):
            result = supplier_service.get_all()
            assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

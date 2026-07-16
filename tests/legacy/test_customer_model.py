#!/usr/bin/env python3
"""
اختبارات Customer Model
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui.models.customer_model import CustomerModel

app = QApplication.instance() or QApplication([])


class TestCustomerModel:
    """اختبارات نموذج العملاء"""

    @pytest.fixture
    def model(self):
        """إنشاء نموذج للاختبارات"""
        customers = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]
        return CustomerModel(customers)

    def test_initialization(self, model):
        """اختبار التهيئة"""
        assert model is not None

    def test_row_count(self, model):
        """اختبار عدد الصفوف"""
        count = model.rowCount()
        assert count == 2

    def test_data(self, model):
        """اختبار البيانات"""
        index = model.index(0, 0)
        data = model.data(index, Qt.DisplayRole)
        assert data is not None

    def test_set_data(self, model):
        """اختبار تعيين البيانات"""
        index = model.index(0, 1)
        result = model.setData(index, "New Name", Qt.EditRole)
        assert isinstance(result, bool)

    def test_add_customer(self, model):
        """اختبار إضافة عميل"""
        customer = {"id": 3, "name": "Bob", "email": "bob@example.com"}
        result = model.add_customer(customer)
        assert result is not None

    def test_remove_customer(self, model):
        """اختبار إزالة عميل"""
        result = model.remove_customer(0)
        assert result is not None

    def test_search_customers(self, model):
        """اختبار البحث عن عملاء"""
        result = model.search_customers("John")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

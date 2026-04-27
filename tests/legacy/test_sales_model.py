#!/usr/bin/env python3
"""
اختبارات Sales Model
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QModelIndex
from decimal import Decimal
from src.ui.models.sales_model import SalesModel

app = QApplication.instance() or QApplication([])


class TestSalesModel:
    """اختبارات نموذج المبيعات"""
    
    @pytest.fixture
    def model(self):
        """إنشاء نموذج للاختبارات"""
        sales = [
            {"id": 1, "date": "2024-01-01", "total": Decimal("150.00"), "items": 3},
            {"id": 2, "date": "2024-01-02", "total": Decimal("250.00"), "items": 5}
        ]
        return SalesModel(sales)
    
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
    
    def test_add_sale(self, model):
        """اختبار إضافة عملية بيع"""
        sale = {"id": 3, "date": "2024-01-03", "total": Decimal("100.00"), "items": 2}
        result = model.add_sale(sale)
        assert result is not None
    
    def test_get_total_sales(self, model):
        """اختبار الحصول على إجمالي المبيعات"""
        total = model.get_total_sales()
        assert isinstance(total, Decimal)
    
    def test_filter_by_date(self, model):
        """اختبار التصفية حسب التاريخ"""
        result = model.filter_by_date("2024-01-01", "2024-01-02")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




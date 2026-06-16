#!/usr/bin/env python3
"""
اختبارات Wholesale Dashboard Dialog
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QTableWidget

from src.ui.dialogs.wholesale_dashboard_dialog import WholesaleDashboardDialog

app = QApplication.instance() or QApplication([])


class TestWholesaleDashboardDialog:
    """اختبارات نافذة لوحة تحكم الجملة"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        sales_service = Mock()
        return WholesaleDashboardDialog(sales_service)

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "total_sales_label")
        assert hasattr(dialog, "orders_table")
        assert hasattr(dialog, "top_customers_table")

    def test_orders_table(self, dialog):
        """اختبار جدول الطلبات"""
        assert dialog.orders_table is not None
        assert isinstance(dialog.orders_table, QTableWidget)

    def test_top_customers_table(self, dialog):
        """اختبار جدول أفضل العملاء"""
        assert dialog.top_customers_table is not None
        assert isinstance(dialog.top_customers_table, QTableWidget)

    def test_load_wholesale_data(self, dialog):
        """اختبار تحميل بيانات الجملة"""
        result = dialog.load_wholesale_data()

        assert result is not None

    def test_load_orders(self, dialog):
        """اختبار تحميل الطلبات"""
        orders = [
            {
                "id": 1,
                "order_number": "WO-001",
                "customer": "عميل جملة 1",
                "total": Decimal("5000.00"),
            },
            {
                "id": 2,
                "order_number": "WO-002",
                "customer": "عميل جملة 2",
                "total": Decimal("7500.00"),
            },
        ]
        dialog.sales_service.get_wholesale_orders.return_value = orders

        result = dialog.load_orders()

        assert result is not None

    def test_load_top_customers(self, dialog):
        """اختبار تحميل أفضل العملاء"""
        customers = [
            {"id": 1, "name": "عميل 1", "total_purchases": Decimal("15000.00")},
            {"id": 2, "name": "عميل 2", "total_purchases": Decimal("12000.00")},
        ]
        dialog.sales_service.get_top_wholesale_customers.return_value = customers

        result = dialog.load_top_customers()

        assert result is not None

    def test_filter_by_date_range(self, dialog):
        """اختبار التصفية حسب نطاق التاريخ"""
        dialog.date_from.setDate(QDate(2024, 1, 1))
        dialog.date_to.setDate(QDate(2024, 12, 31))

        result = dialog.filter_by_date_range()

        assert result is not None

    def test_refresh_dashboard(self, dialog):
        """اختبار تحديث لوحة التحكم"""
        result = dialog.refresh_dashboard()

        assert result is not None

    def test_export_report(self, dialog):
        """اختبار تصدير التقرير"""
        result = dialog.export_report("wholesale_report.xlsx")

        assert result is not None

    def test_on_order_selected(self, dialog):
        """اختبار اختيار طلب"""
        result = dialog.on_order_selected(0)

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

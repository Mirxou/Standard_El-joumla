#!/usr/bin/env python3
"""
اختبارات Quote History Dialog
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QTableWidget

from src.ui.dialogs.quote_history_dialog import QuoteHistoryDialog

app = QApplication.instance() or QApplication([])


class TestQuoteHistoryDialog:
    """اختبارات نافذة سجل عروض الأسعار"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        sales_service = Mock()
        return QuoteHistoryDialog(sales_service)

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "quotes_table")
        assert hasattr(dialog, "search_input")
        assert hasattr(dialog, "date_from")

    def test_quotes_table(self, dialog):
        """اختبار جدول العروض"""
        assert dialog.quotes_table is not None
        assert isinstance(dialog.quotes_table, QTableWidget)

    def test_load_quotes(self, dialog):
        """اختبار تحميل العروض"""
        quotes = [
            {
                "id": 1,
                "quote_number": "Q001",
                "customer_name": "عميل 1",
                "total": Decimal("500.00"),
                "date": date(2024, 1, 15),
            },
            {
                "id": 2,
                "quote_number": "Q002",
                "customer_name": "عميل 2",
                "total": Decimal("750.00"),
                "date": date(2024, 1, 20),
            },
        ]
        dialog.sales_service.get_all_quotes.return_value = quotes

        result = dialog.load_quotes()

        assert result is not None

    def test_search_quotes(self, dialog):
        """اختبار البحث في العروض"""
        dialog.search_input.setText("Q001")

        result = dialog.search_quotes()

        assert result is not None

    def test_filter_by_date_range(self, dialog):
        """اختبار التصفية حسب نطاق التاريخ"""
        dialog.date_from.setDate(QDate(2024, 1, 1))
        dialog.date_to.setDate(QDate(2024, 1, 31))

        result = dialog.filter_by_date_range()

        assert result is not None

    def test_on_quote_selected(self, dialog):
        """اختبار اختيار عرض"""
        result = dialog.on_quote_selected(0)

        assert result is not None

    def test_view_quote_details(self, dialog):
        """اختبار عرض تفاصيل العرض"""
        dialog.selected_quote_id = 1

        result = dialog.view_quote_details()

        assert result is not None

    def test_convert_to_invoice(self, dialog):
        """اختبار تحويل عرض إلى فاتورة"""
        dialog.selected_quote_id = 1

        result = dialog.convert_to_invoice()

        assert result is not None

    def test_export_quotes(self, dialog):
        """اختبار تصدير العروض"""
        result = dialog.export_quotes("quotes.csv")

        assert result is not None

    def test_print_quote(self, dialog):
        """اختبار طباعة العرض"""
        dialog.selected_quote_id = 1

        result = dialog.print_quote()

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

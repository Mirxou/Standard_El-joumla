#!/usr/bin/env python3
"""
اختبارات Contacts Report Dialog
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.dialogs.contacts_report_dialog import ContactsReportDialog

app = QApplication.instance() or QApplication([])


class TestContactsReportDialog:
    """اختبارات نافذة تقرير جهات الاتصال"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        mock_logger = MagicMock()
        return ContactsReportDialog(db_manager=mock_db, logger=mock_logger)

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "tab_widget")
        assert hasattr(dialog, "customers_report_text")
        assert hasattr(dialog, "suppliers_report_text")
        assert hasattr(dialog, "comparison_report_text")

    def test_generate_customers_report(self, dialog):
        """اختبار توليد تقرير العملاء"""
        dialog.db_manager.fetch_one.return_value = (10,)
        dialog.db_manager.fetch_all.return_value = [("Client A", 100)]

        dialog.generate_customers_report()

        text = dialog.customers_report_text.toPlainText()
        assert "تقرير العملاء" in text

    def test_generate_suppliers_report(self, dialog):
        """اختبار توليد تقرير الموردين"""
        dialog.db_manager.fetch_one.return_value = (5,)
        dialog.db_manager.fetch_all.return_value = [("Supplier A", 2, 500)]

        dialog.generate_suppliers_report()

        text = dialog.suppliers_report_text.toPlainText()
        assert "تقرير الموردين" in text

    def test_generate_comparison_report(self, dialog):
        """اختبار توليد تقرير المقارنة"""
        dialog.db_manager.fetch_one.side_effect = [
            (10,),
            (8,),
            (1000,),  # Customers: total, active, balance
            (5,),
            (4,),  # Suppliers: total, active
            (5000,),
            (20,),  # Sales: total, count
            (2000,),
            (10,),  # Purchases: total, count
        ]

        dialog.generate_comparison_report()

        text = dialog.comparison_report_text.toPlainText()
        assert "تقرير المقارنة" in text

    def test_export_report(self, dialog):
        """اختبار التصدير"""
        with patch("builtins.open", MagicMock()) as mock_open:
            dialog.export_report()
            mock_open.assert_called_once()

    def test_print_report(self, dialog):
        """اختبار طباعة التقرير"""
        with patch.object(dialog.notify, "show_info") as mock_notify:
            dialog.print_report()
            mock_notify.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

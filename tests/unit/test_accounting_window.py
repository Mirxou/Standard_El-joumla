#!/usr/bin/env python3
"""
اختبارات Accounting Window
"""

from unittest.mock import MagicMock

import pytest

try:
    from PySide6.QtWidgets import QApplication

    from src.ui.windows.accounting_window import AccountingWindow

    HAS_QT = True
except ImportError:
    HAS_QT = False


@pytest.fixture
def qapp():
    """إنشاء تطبيق Qt للاختبارات"""
    if not HAS_QT:
        pytest.skip("PySide6 not available")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestAccountingWindow:
    """اختبارات نافذة المحاسبة"""

    @pytest.fixture
    def window(self, qapp):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        return AccountingWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_transactions(self, window):
        """اختبار تحميل المعاملات"""
        result = window.load_transactions()
        assert result is not None

    def test_add_transaction(self, window):
        """اختبار إضافة معاملة"""
        result = window.add_transaction()
        assert result is not None

    def test_edit_transaction(self, window):
        """اختبار تعديل معاملة"""
        result = window.edit_transaction(1)
        assert result is not None

    def test_delete_transaction(self, window):
        """اختبار حذف معاملة"""
        result = window.delete_transaction(1)
        assert result is not None

    def test_get_balance(self, window):
        """اختبار الحصول على الرصيد"""
        balance = window.get_balance()
        assert isinstance(balance, (int, float))

    def test_generate_report(self, window):
        """اختبار إنشاء تقرير"""
        result = window.generate_report("income_statement")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

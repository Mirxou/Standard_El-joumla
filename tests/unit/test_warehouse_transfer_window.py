#!/usr/bin/env python3
"""
اختبارات Warehouse Transfer Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.warehouse_transfer_window import WarehouseTransferWindow

app = QApplication.instance() or QApplication([])


class TestWarehouseTransferWindow:
    """اختبارات نافذة نقل المستودعات"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return WarehouseTransferWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_transfers(self, window):
        """اختبار تحميل النقلات"""
        window.load_transfers()

    def test_create_transfer(self, window):
        """اختبار إنشاء نقل"""
        window.create_transfer("from_warehouse", "to_warehouse", [{"product_id": "1", "qty": 10}])

    def test_approve_transfer(self, window):
        """اختبار الموافقة على نقل"""
        window.approve_transfer("transfer_id")

    def test_complete_transfer(self, window):
        """اختبار إكمال نقل"""
        window.complete_transfer("transfer_id")

    def test_get_transfer_status(self, window):
        """اختبار الحصول على حالة النقل"""
        status = window.get_transfer_status("transfer_id")
        assert isinstance(status, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

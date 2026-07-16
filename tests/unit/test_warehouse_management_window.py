#!/usr/bin/env python3
"""
اختبارات Warehouse Management Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.warehouse_management_window import WarehouseManagementWindow

app = QApplication.instance() or QApplication([])


class TestWarehouseManagementWindow:
    """اختبارات نافذة إدارة المستودعات"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return WarehouseManagementWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_warehouses(self, window):
        """اختبار تحميل المستودعات"""
        window.load_warehouses()

    def test_add_warehouse(self, window):
        """اختبار إضافة مستودع"""
        window.add_warehouse()

    def test_edit_warehouse(self, window):
        """اختبار تعديل مستودع"""
        window.edit_warehouse("warehouse_id")

    def test_delete_warehouse(self, window):
        """اختبار حذف مستودع"""
        window.delete_warehouse("warehouse_id")

    def test_manage_warehouse_locations(self, window):
        """اختبار إدارة مواقع المستودع"""
        window.manage_warehouse_locations("warehouse_id")

    def test_get_warehouse_inventory(self, window):
        """اختبار الحصول على مخزون المستودع"""
        inventory = window.get_warehouse_inventory("warehouse_id")
        assert isinstance(inventory, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

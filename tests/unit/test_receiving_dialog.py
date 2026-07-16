#!/usr/bin/env python3
"""
اختبارات Receiving Dialog
"""

from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication, QTableWidget

from src.ui.dialogs.receiving_dialog import ReceivingDialog

app = QApplication.instance() or QApplication([])


class TestReceivingDialog:
    """اختبارات نافذة الاستلام"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        inventory_service = Mock()
        purchase_order = {"id": 1, "po_number": "PO-001", "supplier_id": 1}
        return ReceivingDialog(inventory_service, purchase_order)

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "po_number_label")
        assert hasattr(dialog, "items_table")
        assert hasattr(dialog, "receive_button")

    def test_items_table(self, dialog):
        """اختبار جدول العناصر"""
        assert dialog.items_table is not None
        assert isinstance(dialog.items_table, QTableWidget)

    def test_load_po_items(self, dialog):
        """اختبار تحميل عناصر أمر الشراء"""
        items = [
            {
                "product_id": 1,
                "product_name": "منتج 1",
                "ordered_qty": 100,
                "received_qty": 0,
            },
            {
                "product_id": 2,
                "product_name": "منتج 2",
                "ordered_qty": 50,
                "received_qty": 0,
            },
        ]
        dialog.inventory_service.get_po_items.return_value = items

        result = dialog.load_po_items()

        assert result is not None

    def test_set_received_quantity(self, dialog):
        """اختبار تعيين الكمية المستلمة"""
        result = dialog.set_received_quantity(0, 80)

        assert result is not None

    def test_get_received_items(self, dialog):
        """اختبار الحصول على العناصر المستلمة"""
        result = dialog.get_received_items()

        assert isinstance(result, list)

    def test_validate_receiving(self, dialog):
        """اختبار التحقق من الاستلام"""
        result = dialog.validate_receiving()

        assert isinstance(result, bool)

    def test_on_receive(self, dialog):
        """اختبار تنفيذ الاستلام"""
        result = dialog.on_receive()

        assert result is not None

    def test_on_partial_receive(self, dialog):
        """اختبار الاستلام الجزئي"""
        result = dialog.on_partial_receive()

        assert result is not None

    def test_update_inventory(self, dialog):
        """اختبار تحديث المخزون"""
        items = [{"product_id": 1, "received_qty": 80}]
        result = dialog.update_inventory(items)

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

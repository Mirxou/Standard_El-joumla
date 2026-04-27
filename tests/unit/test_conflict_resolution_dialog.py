#!/usr/bin/env python3
"""
اختبارات Conflict Resolution Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QDialog, QTableWidget, QPushButton, QComboBox, QLabel
from PySide6.QtCore import Qt
from src.ui.dialogs.conflict_resolution_dialog import ConflictResolutionDialog

app = QApplication.instance() or QApplication([])


class TestConflictResolutionDialog:
    """اختبارات نافذة حل التعارضات"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        conflict_data = {
            "table_name": "products",
            "record_id": 1,
            "reason": "Update Conflict",
            "local_data": {"name": "Product A", "price": 100},
            "remote_data": {"name": "Product B", "price": 110}
        }
        return ConflictResolutionDialog(conflict_data)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert dialog.conflict_data["table_name"] == "products"
    
    def test_ui_components(self, dialog):
        """التحقق من وجود مكونات الواجهة"""
        assert hasattr(dialog, 'main_frame')
        assert hasattr(dialog, 'keep_local_radio')
        assert hasattr(dialog, 'keep_remote_radio')
        assert hasattr(dialog, 'merge_radio')
    
    def test_resolve_local(self, dialog):
        """اختبار اختيار الحل المحلي"""
        dialog.keep_local_radio.setChecked(True)
        dialog.resolve()
        assert dialog.get_resolution() == ConflictResolutionDialog.RESOLUTION_KEEP_LOCAL
    
    def test_resolve_remote(self, dialog):
        """اختبار اختيار الحل البعيد"""
        dialog.keep_remote_radio.setChecked(True)
        dialog.resolve()
        assert dialog.get_resolution() == ConflictResolutionDialog.RESOLUTION_KEEP_REMOTE
    
    def test_get_resolution_none_initially(self, dialog):
        """التحقق من أن القرار فارغ في البداية"""
        assert dialog.get_resolution() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




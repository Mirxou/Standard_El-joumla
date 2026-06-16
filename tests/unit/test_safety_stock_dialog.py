#!/usr/bin/env python3
"""
اختبارات Safety Stock Dialog
"""

from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.dialogs.safety_stock_dialog import SafetyStockDialog

app = QApplication.instance() or QApplication([])


class TestSafetyStockDialog:
    """اختبارات نافذة المخزون الاحتياطي"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        inventory_service = Mock()
        product = {"id": 1, "name": "منتج تجريبي", "current_stock": 100}
        return SafetyStockDialog(inventory_service, product)

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "product_name_label")
        assert hasattr(dialog, "current_stock_label")
        assert hasattr(dialog, "safety_level_spin")

    def test_safety_level_spin(self, dialog):
        """اختبار حقل مستوى المخزون الاحتياطي"""
        dialog.safety_level_spin.setValue(50)
        assert dialog.safety_level_spin.value() == 50

    def test_reorder_point_spin(self, dialog):
        """اختبار حقل نقطة إعادة الطلب"""
        dialog.reorder_point_spin.setValue(30)
        assert dialog.reorder_point_spin.value() == 30

    def test_calculate_safety_stock(self, dialog):
        """اختبار حساب المخزون الاحتياطي"""
        result = dialog.calculate_safety_stock(avg_daily_usage=10, lead_time_days=7, safety_days=3)

        assert isinstance(result, int)
        assert result == 100  # 10 * (7 + 3)

    def test_get_safety_stock_settings(self, dialog):
        """اختبار الحصول على إعدادات المخزون الاحتياطي"""
        dialog.safety_level_spin.setValue(50)
        dialog.reorder_point_spin.setValue(30)

        settings = dialog.get_safety_stock_settings()

        assert isinstance(settings, dict)
        assert settings.get("safety_level") == 50
        assert settings.get("reorder_point") == 30

    def test_validate_settings(self, dialog):
        """اختبار التحقق من الإعدادات"""
        dialog.safety_level_spin.setValue(50)
        dialog.reorder_point_spin.setValue(30)

        assert dialog.validate_settings() is True

    def test_on_save(self, dialog):
        """اختبار حفظ الإعدادات"""
        dialog.safety_level_spin.setValue(50)
        dialog.reorder_point_spin.setValue(30)

        result = dialog.on_save()

        assert result is not None

    def test_load_historical_data(self, dialog):
        """اختبار تحميل البيانات التاريخية"""
        result = dialog.load_historical_data()

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

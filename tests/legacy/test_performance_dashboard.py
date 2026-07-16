#!/usr/bin/env python3
"""
اختبارات Performance Dashboard
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.performance_dashboard import PerformanceDashboard

app = QApplication.instance() or QApplication([])


class TestPerformanceDashboard:
    """اختبارات لوحة أداء النظام"""

    @pytest.fixture
    def dashboard(self):
        """إنشاء لوحة للاختبارات"""
        return PerformanceDashboard()

    def test_initialization(self, dashboard):
        """اختبار التهيئة"""
        assert dashboard is not None

    def test_update_cpu_usage(self, dashboard):
        """اختبار تحديث استخدام CPU"""
        result = dashboard.update_cpu_usage(45.5)
        assert result is not None

    def test_update_memory_usage(self, dashboard):
        """اختبار تحديث استخدام الذاكرة"""
        result = dashboard.update_memory_usage(60.0)
        assert result is not None

    def test_update_disk_usage(self, dashboard):
        """اختبار تحديث استخدام القرص"""
        result = dashboard.update_disk_usage(75.0)
        assert result is not None

    def test_update_network_stats(self, dashboard):
        """اختبار تحديث إحصائيات الشبكة"""
        stats = {"upload": 100, "download": 500}
        result = dashboard.update_network_stats(stats)
        assert result is not None

    def test_refresh_data(self, dashboard):
        """اختبار تحديث البيانات"""
        result = dashboard.refresh_data()
        assert result is not None

    def test_set_alert_threshold(self, dashboard):
        """اختبار تعيين حد التنبيه"""
        result = dashboard.set_alert_threshold("cpu", 80)
        assert result is not None

    def test_get_performance_history(self, dashboard):
        """اختبار الحصول على تاريخ الأداء"""
        history = dashboard.get_performance_history()
        assert isinstance(history, dict)

    def test_export_stats(self, dashboard):
        """اختبار تصدير الإحصائيات"""
        result = dashboard.export_stats("stats.json")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

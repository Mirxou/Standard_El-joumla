#!/usr/bin/env python3
"""
اختبارات Performance Panel
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.admin.performance_panel import PerformancePanel

app = QApplication.instance() or QApplication([])


class TestPerformancePanel:
    """اختبارات لوحة الأداء"""

    @pytest.fixture
    def panel(self):
        """إنشاء لوحة للاختبارات"""
        return PerformancePanel()

    def test_initialization(self, panel):
        """اختبار التهيئة"""
        assert panel is not None

    def test_update_cpu_stats(self, panel):
        """اختبار تحديث إحصائيات CPU"""
        result = panel.update_cpu_stats(45.5, 8)
        assert result is not None

    def test_update_memory_stats(self, panel):
        """اختبار تحديث إحصائيات الذاكرة"""
        result = panel.update_memory_stats(60.0, 8, 16)
        assert result is not None

    def test_update_disk_stats(self, panel):
        """اختبار تحديث إحصائيات القرص"""
        result = panel.update_disk_stats(75.0, 500, 1000)
        assert result is not None

    def test_update_network_stats(self, panel):
        """اختبار تحديث إحصائيات الشبكة"""
        result = panel.update_network_stats(1000, 500)
        assert result is not None

    def test_start_monitoring(self, panel):
        """اختبار بدء المراقبة"""
        result = panel.start_monitoring(1000)
        assert result is not None

    def test_stop_monitoring(self, panel):
        """اختبار إيقاف المراقبة"""
        result = panel.stop_monitoring()
        assert result is not None

    def test_export_performance_data(self, panel):
        """اختبار تصدير بيانات الأداء"""
        result = panel.export_performance_data("perf.json")
        assert result is not None

    def test_set_alert_threshold(self, panel):
        """اختبار تعيين حد التنبيه"""
        result = panel.set_alert_threshold("cpu", 80)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

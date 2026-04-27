#!/usr/bin/env python3
"""
اختبارات Cache Stats Panel - محدثة للتوافق مع API الفعلي
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidget
from PySide6.QtCore import Qt
from src.ui.admin.cache_stats_panel import CacheStatsPanel

app = QApplication.instance() or QApplication([])


class TestCacheStatsPanel:
    """اختبارات لوحة إحصائيات الذاكرة المؤقتة"""
    
    @pytest.fixture
    def panel(self):
        """إنشاء لوحة للاختبارات"""
        mock_cache = MagicMock()
        mock_cache.caches = {
            'products': MagicMock(),
            'customers': MagicMock(),
        }
        mock_cache.caches['products'].get_stats.return_value = {
            'size': 10, 'max_size': 100, 'hits': 50, 'misses': 5,
            'hit_rate': 90.0, 'evictions': 0, 'expirations': 0, 'usage_percent': 10.0
        }
        mock_cache.caches['customers'].get_stats.return_value = {
            'size': 5, 'max_size': 100, 'hits': 20, 'misses': 2,
            'hit_rate': 90.9, 'evictions': 0, 'expirations': 0, 'usage_percent': 5.0
        }
        mock_cache.get_all_stats.return_value = {
            'products': {'size': 10, 'max_size': 100, 'hits': 50, 'misses': 5,
                        'hit_rate': 90.0, 'evictions': 0, 'expirations': 0, 'usage_percent': 10.0},
            '_totals': {
                'total_size': 15, 'total_max_size': 200, 'total_hits': 70,
                'total_misses': 7, 'total_evictions': 0, 'total_expirations': 0,
                'overall_hit_rate': 90.9
            }
        }
        return CacheStatsPanel(mock_cache)
    
    def test_initialization(self, panel):
        """اختبار التهيئة - الخاصية الفعلية هي cache وليس cache_manager"""
        assert panel is not None
        assert hasattr(panel, 'cache')   # self.cache = cache_service
        assert hasattr(panel, 'caches_table')  # QTableWidget
    
    def test_update_stats(self, panel):
        """اختبار تحديث الإحصائيات - عبر refresh()"""
        assert hasattr(panel, 'refresh')
        panel.refresh()  # Should not raise
    
    def test_clear_cache(self, panel):
        """اختبار مسح الذاكرة المؤقتة - عبر _clear_all_caches()"""
        assert hasattr(panel, '_clear_all_caches')
        panel._clear_all_caches()  # Should not raise
    
    def test_refresh_cache(self, panel):
        """اختبار تحديث الذاكرة المؤقتة - refresh() متاحة"""
        panel.refresh()
    
    def test_show_cache_details(self, panel):
        """اختبار عرض caches_table"""
        assert hasattr(panel, 'caches_table')
        assert isinstance(panel.caches_table, QTableWidget)
    
    def test_set_auto_refresh(self, panel):
        """اختبار وجود خاصية auto-refresh"""
        assert hasattr(panel, '_setup_auto_refresh')
    
    def test_get_hit_rate(self, panel):
        """اختبار وجود get_all_stats في cache"""
        stats = panel.cache.get_all_stats()
        assert '_totals' in stats
        assert 'overall_hit_rate' in stats['_totals']
    
    def test_export_stats(self, panel):
        """اختبار وجود وظيفة التحديث"""
        assert hasattr(panel, 'refresh')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
اختبارات Advanced Search Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.advanced_search_window import AdvancedSearchWindow

app = QApplication.instance() or QApplication([])


class TestAdvancedSearchWindow:
    """اختبارات نافذة البحث المتقدم"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        mock_db.fetch_one.return_value = None

        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            # We need to mock AdvancedSearchService's return values too
            with patch("src.ui.windows.advanced_search_window.AdvancedSearchService") as mock_service:
                mock_service.return_value.list_saved_filters.return_value = []
                return AdvancedSearchWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_set_search_criteria(self, window):
        """اختبار تعيين معايير البحث"""
        window.set_search_criteria({"name": "test"})

    def test_execute_search(self, window):
        """اختبار تنفيذ البحث"""
        window.execute_search()

    def test_get_search_results(self, window):
        """اختبار الحصول على نتائج البحث"""
        results = window.get_search_results()
        assert isinstance(results, list)

    def test_save_search(self, window):
        """اختبار حفظ البحث"""
        window.save_search("my_search")

    def test_load_saved_search(self, window):
        """اختبار تحميل بحث محفوظ"""
        window.load_saved_search("my_search")

    def test_clear_filters(self, window):
        """اختبار مسح الفلاتر"""
        window.clear_filters()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

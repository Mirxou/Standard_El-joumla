#!/usr/bin/env python3
"""
اختبارات Conversational Search
"""

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.components.conversational_search import ConversationalSearch

app = QApplication.instance() or QApplication([])


class TestConversationalSearch:
    """اختبارات البحث التفاعلي"""

    @pytest.fixture
    def conversational_service(self):
        service = MagicMock()
        return service

    @pytest.fixture
    def search(self, conversational_service):
        """إنشاء عنصر بحث للاختبارات"""
        return ConversationalSearch(conversational_service=conversational_service)

    def test_initialization(self, search):
        """اختبار تهيئة العنصر"""
        assert search is not None
        assert hasattr(search, "results_list")
        assert search.conversational_service is not None

    def test_search_no_service(self):
        """اختبار البحث بدون خدمة"""
        search_no_srv = ConversationalSearch()
        search_no_srv.search("test")

        assert search_no_srv.results_list.count() == 1
        assert "غير متاحة" in search_no_srv.results_list.item(0).text()

    def test_search_with_results(self, search):
        """اختبار البحث بنجاح"""
        mock_result = MagicMock()
        mock_result.explanation = "Here are the results"
        mock_result.suggested_actions = ["action 1", "action 2"]
        search.conversational_service.process_natural_language_query.return_value = mock_result

        search.search("أريد مبيعات اليوم")

        search.conversational_service.process_natural_language_query.assert_called_with("أريد مبيعات اليوم")
        assert search.results_list.count() == 3  # 1 explanation + 2 actions
        assert "Here are the results" in search.results_list.item(0).text()
        assert "action 1" in search.results_list.item(1).text()

    def test_search_with_error(self, search):
        """اختبار البحث عند وجود خطأ"""
        search.conversational_service.process_natural_language_query.side_effect = Exception("Service error")

        search.search("test")

        assert search.results_list.count() == 1
        assert "Service error" in search.results_list.item(0).text()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""Tests for Reports Analytics UI"""
import pytest
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication
from src.ui.reports_analytics_ui import ReportsAnalyticsUI

app = QApplication.instance() or QApplication([])

class TestReportsAnalyticsUI:
    @pytest.fixture
    def ui(self):
        analytics_service = Mock()
        return ReportsAnalyticsUI(analytics_service)
    
    def test_initialization(self, ui):
        assert ui is not None
    
    def test_generate_sales_report(self, ui):
        result = ui.generate_sales_report("2024-01-01", "2024-12-31")
        assert result is not None
    
    def test_export_report(self, ui):
        result = ui.export_report("sales", "pdf")
        assert result is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])




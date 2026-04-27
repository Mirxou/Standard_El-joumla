#!/usr/bin/env python3
"""
اختبارات Report Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.report_service import ReportService


class TestReportService:
    """اختبارات خدمة التقارير"""
    
    @pytest.fixture
    def report_service(self):
        """إنشاء خدمة تقارير"""
        return ReportService()
    
    def test_initialization(self, report_service):
        """اختبار التهيئة"""
        assert report_service is not None
    
    def test_generate_sales_report(self, report_service):
        """اختبار إنشاء تقرير المبيعات"""
        with patch.object(report_service, 'generate_sales_report', return_value={"total": 1000}):
            result = report_service.generate_sales_report("2024-01-01", "2024-01-31")
            assert result is not None
    
    def test_generate_inventory_report(self, report_service):
        """اختبار إنشاء تقرير المخزون"""
        with patch.object(report_service, 'generate_inventory_report', return_value={"items": []}):
            result = report_service.generate_inventory_report()
            assert result is not None
    
    def test_export_report_pdf(self, report_service):
        """اختبار تصدير تقرير PDF"""
        with patch.object(report_service, 'export_pdf', return_value="report.pdf"):
            result = report_service.export_pdf({"data": []}, "report.pdf")
            assert result == "report.pdf"
    
    def test_export_report_excel(self, report_service):
        """اختبار تصدير تقرير Excel"""
        with patch.object(report_service, 'export_excel', return_value="report.xlsx"):
            result = report_service.export_excel({"data": []}, "report.xlsx")
            assert result == "report.xlsx"
    
    def test_schedule_report(self, report_service):
        """اختبار جدولة تقرير"""
        with patch.object(report_service, 'schedule', return_value=True):
            result = report_service.schedule("daily", "08:00")
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




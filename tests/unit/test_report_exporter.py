#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for ReportExporter
اختبارات وحدة لخدمة تصدير التقارير
"""

import pytest
import os
import json
import csv
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, Mock
from src.services.report_exporter import ReportExporter, ReportType, ReportFilter, ExportFormat, ReportData

class TestReportExporter:
    @pytest.fixture
    def db_manager(self):
        mock_db = MagicMock()
        # Mock execute_query to return empty list by default
        mock_db.execute_query.return_value = []
        mock_db.fetch_one.return_value = (None, None)
        mock_db.execute_scalar.return_value = 0
        return mock_db

    @pytest.fixture
    def service(self, db_manager):
        with patch('src.services.report_exporter.setup_logger', return_value=MagicMock()):
            with patch('src.services.report_exporter.DatabaseLogger', return_value=MagicMock()):
                with patch('src.services.report_exporter.ProductManager', return_value=MagicMock()):
                    with patch('src.services.report_exporter.SaleManager', return_value=MagicMock()):
                        with patch('src.services.report_exporter.PurchaseManager', return_value=MagicMock()):
                            with patch('src.services.report_exporter.CustomerManager', return_value=MagicMock()):
                                with patch('src.services.report_exporter.SupplierManager', return_value=MagicMock()):
                                    return ReportExporter(db_manager)

    def test_initialization(self, service):
        """Test if the service initializes correctly"""
        assert service.db is not None
        assert os.path.exists(service.reports_dir)

    def test_generate_sales_summary_report(self, service, db_manager):
        """Test generating a sales summary report"""
        filters = ReportFilter(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now()
        )
        
        # Mock DB response
        mock_rows = [
            {
                "id": 1, "invoice_number": "INV-001", "sale_date": "2026-04-16",
                "total_amount": 1000.0, "final_amount": 1100.0, "payment_method": "cash",
                "status": "paid", "customer_name": "Test Customer"
            }
        ]
        db_manager.execute_query.return_value = mock_rows
        
        # Mock daily sales chart data
        service._get_daily_sales_chart_data = MagicMock(return_value={})
        service._get_top_customers_chart_data = MagicMock(return_value={})
        
        report = service.generate_sales_summary_report(filters)
        
        assert isinstance(report, ReportData)
        assert report.title == "تقرير ملخص المبيعات"
        assert len(report.data) == 1
        assert report.data[0]["invoice_number"] == "INV-001"
        assert report.summary["total_sales"] == 1

    def test_export_to_json(self, service, tmp_path):
        """Test exporting report data to JSON format"""
        report_data = ReportData(
            title="Test Report",
            subtitle="Subtitle",
            generated_at=datetime.now(),
            filters=ReportFilter(),
            data=[{"id": 1, "name": "Item 1"}],
            summary={"total": 1}
        )
        
        filename = "test_export.json"
        filepath = str(tmp_path / filename)
        
        # We need to patch os.path.join to use our tmp_path
        with patch('os.path.join', return_value=filepath):
            result_path = service.export_report(report_data, ExportFormat.JSON, filename)
            
            assert os.path.exists(result_path)
            with open(result_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                assert saved_data["title"] == "Test Report"
                assert len(saved_data["data"]) == 1

    def test_export_to_csv(self, service, tmp_path):
        """Test exporting report data to CSV format"""
        report_data = ReportData(
            title="Test Report",
            subtitle="Subtitle",
            generated_at=datetime.now(),
            filters=ReportFilter(),
            data=[{"id": 1, "name": "Item 1", "value": 100.5}],
            summary={"total": 1}
        )
        
        filename = "test_export.csv"
        filepath = str(tmp_path / filename)
        
        with patch('os.path.join', return_value=filepath):
            result_path = service.export_report(report_data, ExportFormat.CSV, filename)
            
            assert os.path.exists(result_path)
            with open(result_path, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["id"] == "1"
                assert rows[0]["name"] == "Item 1"

    def test_generate_report_router(self, service):
        """Test the generate_report router method"""
        filters = ReportFilter()
        service.generate_sales_summary_report = MagicMock()
        
        service.generate_report(ReportType.SALES_SUMMARY, filters)
        service.generate_sales_summary_report.assert_called_once_with(filters)

if __name__ == "__main__":
    pytest.main([__file__])




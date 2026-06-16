#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Report Generator Service
اختبارات خدمة مولد التقارير
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.services.report_generator import ReportFilter, ReportGenerator, ReportType


class TestReportGeneratorInitialization:
    """اختبارات تهيئة مولد التقارير"""

    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = Mock()
        mock_config = Mock()

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)

        assert generator.db_manager == mock_db
        assert generator.config_manager == mock_config

    def test_initialization_without_db_manager(self):
        """اختبار التهيئة بدون مدير قاعدة بيانات"""
        with patch("src.services.report_generator.DatabaseManager") as mock_db_class, patch(
            "src.services.report_generator.ConfigManager"
        ) as mock_config_class:

            mock_db = Mock()
            mock_config = Mock()
            mock_db_class.return_value = mock_db
            mock_config_class.return_value = mock_config

            generator = ReportGenerator()

            assert generator.db_manager == mock_db
            assert generator.config_manager == mock_config


class TestGenerateSalesSummaryReport:
    """اختبارات توليد تقرير ملخص المبيعات"""

    @pytest.fixture
    def generator_with_mocks(self):
        """إنشاء مولد تقارير مع mocks"""
        mock_db = Mock()
        mock_config = Mock()

        mock_db.fetch_all.return_value = [
            {
                "date": "2024-01-01",
                "total": 1000.0,
                "profit": 200.0,
                "quantity": 10,
                "invoice_count": 5,
            },
            {
                "date": "2024-01-02",
                "total": 1500.0,
                "profit": 300.0,
                "quantity": 15,
                "invoice_count": 8,
            },
        ]

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)
        generator._get_returns_data = Mock(return_value=[])
        generator._get_top_products = Mock(return_value=[])
        generator._get_top_customers = Mock(return_value=[])
        generator._get_top_categories = Mock(return_value=[])
        generator._generate_sales_charts = Mock(return_value={})

        return generator

    def test_generate_sales_summary_report_success(self, generator_with_mocks):
        """اختبار توليد تقرير ملخص المبيعات بنجاح"""
        filters = ReportFilter(start_date=datetime.now() - timedelta(days=30), end_date=datetime.now())

        result = generator_with_mocks.generate_sales_summary_report(filters)

        assert result is not None
        assert result.report_type == ReportType.SALES_SUMMARY
        assert result.sales_summary is not None
        assert result.sales_summary.total_sales == 2500.0
        assert result.sales_summary.total_profit == 500.0

    def test_generate_sales_summary_report_with_returns(self, generator_with_mocks):
        """اختبار توليد تقرير مع إرجاعات"""
        generator_with_mocks._get_returns_data.return_value = [
            {"total": 100.0},
            {"total": 50.0},
        ]

        filters = ReportFilter(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            include_returns=True,
        )

        result = generator_with_mocks.generate_sales_summary_report(filters)

        assert result is not None
        assert result.sales_summary.returns_value == 150.0
        assert result.sales_summary.net_sales == 2350.0


class TestGenerateSalesDetailedReport:
    """اختبارات توليد تقرير المبيعات التفصيلي"""

    @pytest.fixture
    def generator_with_mocks(self):
        """إنشاء مولد تقارير مع mocks"""
        mock_db = Mock()
        mock_config = Mock()

        mock_db.fetch_all.return_value = [
            {
                "date": "2024-01-01",
                "invoice_number": "INV-001",
                "customer_name": "Customer 1",
                "product_name": "Product 1",
                "quantity": 2,
                "unit_price": 100.0,
                "discount": 0,
                "tax": 10.0,
                "total": 210.0,
                "profit": 50.0,
                "profit_margin": 23.8,
                "payment_method": "cash",
            }
        ]

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)
        return generator

    def test_generate_sales_detailed_report_success(self, generator_with_mocks):
        """اختبار توليد تقرير تفصيلي بنجاح"""
        filters = ReportFilter(start_date=datetime.now() - timedelta(days=30), end_date=datetime.now())

        result = generator_with_mocks.generate_sales_detailed_report(filters)

        assert result is not None
        assert result.report_type == ReportType.SALES_DETAILED
        assert len(result.sales_lines) == 1
        assert result.sales_lines[0].invoice_number == "INV-001"
        assert result.sales_lines[0].total == 210.0


class TestGenerateInventoryReport:
    """اختبارات توليد تقرير المخزون"""

    @pytest.fixture
    def generator_with_mocks(self):
        """إنشاء مولد تقارير مع mocks"""
        mock_db = Mock()
        mock_config = Mock()

        mock_db.fetch_all.return_value = [
            {
                "product_id": 1,
                "product_name": "Product 1",
                "category_name": "Category 1",
                "current_stock": 50,
                "min_stock": 10,
                "max_stock": 100,
                "unit_cost": 50.0,
                "total_value": 2500.0,
            }
        ]

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)
        return generator

    def test_generate_inventory_report_success(self, generator_with_mocks):
        """اختبار توليد تقرير المخزون بنجاح"""
        filters = ReportFilter(start_date=datetime.now() - timedelta(days=30), end_date=datetime.now())

        result = generator_with_mocks.generate_inventory_report(filters)

        assert result is not None
        assert result.report_type == ReportType.INVENTORY
        assert len(result.inventory_lines) == 1

    def test_generate_inventory_report_low_stock(self, generator_with_mocks):
        """اختبار تحديد منتجات المخزون المنخفض"""
        mock_db = Mock()
        mock_config = Mock()

        mock_db.fetch_all.return_value = [
            {
                "product_id": 1,
                "product_name": "Low Stock Product",
                "current_stock": 5,
                "min_stock": 10,
                "max_stock": 100,
                "unit_cost": 50.0,
                "total_value": 250.0,
            }
        ]

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)

        filters = ReportFilter(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            low_stock_only=True,
        )

        result = generator.generate_inventory_report(filters)

        assert result is not None
        assert len(result.inventory_lines) == 1
        assert result.inventory_lines[0].is_low_stock is True


class TestGenerateFinancialReport:
    """اختبارات توليد التقرير المالي"""

    def test_generate_financial_report_success(self):
        """اختبار توليد التقرير المالي بنجاح"""
        mock_db = Mock()
        mock_config = Mock()

        mock_db.fetch_all.side_effect = [
            # Revenue data
            [{"account": "Sales", "amount": 10000.0}],
            # Expense data
            [{"account": "Rent", "amount": 2000.0}],
            # Asset data
            [{"account": "Cash", "amount": 5000.0}],
            # Liability data
            [{"account": "Loans", "amount": 3000.0}],
        ]

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)

        filters = ReportFilter(start_date=datetime.now() - timedelta(days=30), end_date=datetime.now())

        result = generator.generate_financial_report(filters)

        assert result is not None
        assert result.report_type == ReportType.FINANCIAL
        assert result.financial_summary is not None


class TestExportReport:
    """اختبارات تصدير التقارير"""

    @pytest.fixture
    def generator(self):
        """إنشاء مولد تقارير"""
        mock_db = Mock()
        mock_config = Mock()
        return ReportGenerator(db_manager=mock_db, config_manager=mock_config)

    def test_export_report_to_pdf(self, generator):
        """اختبار تصدير التقرير إلى PDF"""
        mock_report = Mock()
        mock_report.to_html.return_value = "<html>Report</html>"

        with patch("src.services.report_generator.PDFExportService") as mock_pdf_class:
            mock_pdf = Mock()
            mock_pdf.html_to_pdf.return_value = True
            mock_pdf_class.return_value = mock_pdf

            result = generator.export_report(mock_report, "pdf", "/output/report.pdf")

            assert result["success"] is True
            assert result["format"] == "pdf"

    def test_export_report_to_excel(self, generator):
        """اختبار تصدير التقرير إلى Excel"""
        mock_report = Mock()
        mock_report.to_dataframe.return_value = Mock()

        with patch("pandas.DataFrame.to_excel") as mock_to_excel:  # noqa: F841
            result = generator.export_report(mock_report, "excel", "/output/report.xlsx")

            assert result["success"] is True
            assert result["format"] == "excel"

    def test_export_report_invalid_format(self, generator):
        """اختبار تصدير بنسق غير صالح"""
        mock_report = Mock()

        result = generator.export_report(mock_report, "invalid", "/output/report.invalid")

        assert result["success"] is False
        assert "Invalid format" in result["error"]


class TestScheduleReport:
    """اختبارات جدولة التقارير"""

    def test_schedule_report_success(self):
        """اختبار جدولة تقرير بنجاح"""
        mock_db = Mock()
        mock_config = Mock()

        mock_db.execute.return_value = 1

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)

        result = generator.schedule_report(
            report_type=ReportType.SALES_SUMMARY,
            frequency="daily",
            recipients=["admin@example.com"],
        )

        assert result["success"] is True
        assert result["schedule_id"] == 1

    def test_schedule_report_invalid_frequency(self):
        """اختبار جدولة بنوع تكرار غير صالح"""
        mock_db = Mock()
        mock_config = Mock()

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)

        result = generator.schedule_report(report_type=ReportType.SALES_SUMMARY, frequency="invalid")

        assert result["success"] is False
        assert "Invalid frequency" in result["error"]


class TestGetReportHistory:
    """اختبارات الحصول على سجل التقارير"""

    def test_get_report_history_success(self):
        """اختبار الحصول على سجل التقارير بنجاح"""
        mock_db = Mock()
        mock_config = Mock()

        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "report_type": "SALES_SUMMARY",
                "generated_at": "2024-01-01 10:00:00",
                "file_path": "/reports/report1.pdf",
            },
            {
                "id": 2,
                "report_type": "INVENTORY",
                "generated_at": "2024-01-02 10:00:00",
                "file_path": "/reports/report2.pdf",
            },
        ]

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)

        result = generator.get_report_history(limit=10)

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["reports"]) == 2


class TestFilterReport:
    """اختبارات تصفية التقارير"""

    def test_filter_report_by_date_range(self):
        """اختبار تصفية التقرير حسب نطاق التاريخ"""
        mock_db = Mock()
        mock_config = Mock()

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)  # noqa: F841

        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        filters = ReportFilter(start_date=start_date, end_date=end_date)

        assert filters.start_date == start_date
        assert filters.end_date == end_date

    def test_filter_report_by_product_ids(self):
        """اختبار تصفية التقرير حسب معرفات المنتجات"""
        mock_db = Mock()
        mock_config = Mock()

        generator = ReportGenerator(db_manager=mock_db, config_manager=mock_config)  # noqa: F841

        filters = ReportFilter(product_ids=[1, 2, 3])

        assert filters.product_ids == [1, 2, 3]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

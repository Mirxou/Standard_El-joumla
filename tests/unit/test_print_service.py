#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Print Service
اختبارات خدمة الطباعة
"""

from unittest.mock import Mock, patch

import pytest

from src.services.print_service import PrintService


class TestPrintServiceInitialization:
    """اختبارات تهيئة خدمة الطباعة"""

    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = Mock()
        mock_db_config = Mock()

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        assert service.db_manager == mock_db
        assert service.db_config_manager == mock_db_config
        assert service.print_manager is not None
        assert service.pdf_export is not None

    def test_initialization_without_db_manager(self):
        """اختبار التهيئة بدون مدير قاعدة بيانات"""
        with patch("src.services.print_service.DatabaseManager") as mock_db_class, patch(
            "src.services.print_service.DatabaseConfigManager"
        ) as mock_db_config_class:

            mock_db = Mock()
            mock_db_config = Mock()
            mock_db_class.return_value = mock_db
            mock_db_config_class.return_value = mock_db_config

            service = PrintService()

            assert service.db_manager == mock_db
            assert service.db_config_manager == mock_db_config


class TestPrintInvoice:
    """اختبارات طباعة الفاتورة"""

    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_db_config = Mock()

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        # Mock print_manager methods
        service.print_manager.get_default_template = Mock()
        service.print_manager.render_template = Mock(return_value="<html>Invoice</html>")
        service.print_manager.log_print_job = Mock()

        # Mock pdf_export
        service.pdf_export.html_to_pdf = Mock(return_value=True)

        # Mock _get_invoice_data
        service._get_invoice_data = Mock(return_value={"invoice_number": "INV-001", "customer_name": "Test Customer"})

        return service

    def test_print_invoice_success_with_pdf(self, service_with_mocks):
        """اختبار طباعة الفاتورة بنجاح مع PDF"""
        mock_template = Mock()
        mock_template.id = 1
        service_with_mocks.print_manager.get_default_template.return_value = mock_template

        result = service_with_mocks.print_invoice(sale_id=1, save_pdf=True)

        assert result["success"] is True
        assert result["html"] == "<html>Invoice</html>"
        assert "pdf_path" in result
        service_with_mocks.print_manager.log_print_job.assert_called_once()

    def test_print_invoice_without_pdf(self, service_with_mocks):
        """اختبار طباعة الفاتورة بدون PDF"""
        mock_template = Mock()
        mock_template.id = 1
        service_with_mocks.print_manager.get_default_template.return_value = mock_template

        result = service_with_mocks.print_invoice(sale_id=1, save_pdf=False)

        assert result["success"] is True
        assert result["pdf_path"] is None
        service_with_mocks.pdf_export.html_to_pdf.assert_not_called()

    def test_print_invoice_not_found(self, service_with_mocks):
        """اختبار طباعة فاتورة غير موجودة"""
        service_with_mocks._get_invoice_data.return_value = None

        result = service_with_mocks.print_invoice(sale_id=999)

        assert result["success"] is False
        assert "Invoice not found" in result["error"]

    def test_print_invoice_template_not_found(self, service_with_mocks):
        """اختبار طباعة فاتورة بدون قالب"""
        service_with_mocks.print_manager.get_default_template.return_value = None

        result = service_with_mocks.print_invoice(sale_id=1)

        assert result["success"] is False
        assert "Template not found" in result["error"]

    def test_print_invoice_with_custom_template(self, service_with_mocks):
        """اختبار طباعة الفاتورة بقالب مخصص"""
        mock_template = Mock()
        mock_template.id = 2
        service_with_mocks.print_manager.get_template_by_name.return_value = mock_template

        result = service_with_mocks.print_invoice(sale_id=1, template_name="custom_template")

        assert result["success"] is True
        service_with_mocks.print_manager.get_template_by_name.assert_called_once_with("custom_template")


class TestPrintQuote:
    """اختبارات طباعة عرض السعر"""

    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_db_config = Mock()

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        service.print_manager.get_default_template = Mock()
        service.print_manager.render_template = Mock(return_value="<html>Quote</html>")
        service.print_manager.log_print_job = Mock()
        service.pdf_export.html_to_pdf = Mock(return_value=True)

        service._get_quote_data = Mock(return_value={"quote_number": "QT-001", "customer_name": "Test Customer"})

        return service

    def test_print_quote_success(self, service_with_mocks):
        """اختبار طباعة عرض السعر بنجاح"""
        mock_template = Mock()
        mock_template.id = 1
        service_with_mocks.print_manager.get_default_template.return_value = mock_template

        result = service_with_mocks.print_quote(quote_id=1, save_pdf=True)

        assert result["success"] is True
        assert result["html"] == "<html>Quote</html>"

    def test_print_quote_not_found(self, service_with_mocks):
        """اختبار طباعة عرض سعر غير موجود"""
        service_with_mocks._get_quote_data.return_value = None

        result = service_with_mocks.print_quote(quote_id=999)

        assert result["success"] is False
        assert "Quote not found" in result["error"]


class TestPrintThermalReceipt:
    """اختبارات طباعة الإيصال الحراري"""

    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_db_config = Mock()

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        mock_template = Mock()
        mock_template.id = 1

        service.print_manager.get_default_template = Mock(return_value=mock_template)
        service.print_manager.render_template = Mock(return_value="<html>Thermal Receipt</html>")
        service.print_manager.log_print_job = Mock()

        service._get_invoice_data = Mock(return_value={"invoice_number": "INV-001", "total": 1000.0})

        return service

    def test_print_thermal_receipt_success(self, service_with_mocks):
        """اختبار طباعة الإيصال الحراري بنجاح"""
        result = service_with_mocks.print_thermal_receipt(sale_id=1, printer_width=80)

        assert result["success"] is True
        assert result["html"] == "<html>Thermal Receipt</html>"
        assert result["printer_width"] == 80

    def test_print_thermal_receipt_invoice_not_found(self, service_with_mocks):
        """اختبار طباعة إيصال مع فاتورة غير موجودة"""
        service_with_mocks._get_invoice_data.return_value = None

        result = service_with_mocks.print_thermal_receipt(sale_id=999)

        assert result["success"] is False
        assert "Invoice not found" in result["error"]

    def test_print_thermal_receipt_template_not_found(self, service_with_mocks):
        """اختبار طباعة إيصال بدون قالب"""
        service_with_mocks.print_manager.get_default_template.return_value = None

        result = service_with_mocks.print_thermal_receipt(sale_id=1)

        assert result["success"] is False
        assert "Thermal template not found" in result["error"]


class TestBatchPrintInvoices:
    """اختبارات طباعة دفعة من الفواتير"""

    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_db_config = Mock()

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        mock_template = Mock()
        mock_template.id = 1

        service.print_manager.get_default_template = Mock(return_value=mock_template)
        service.print_manager.get_template_by_name = Mock(return_value=mock_template)
        service.print_manager.render_template = Mock(return_value="<html>Invoice</html>")
        service.print_manager.log_print_job = Mock()
        service.pdf_export.html_to_pdf = Mock(return_value=True)

        service._get_invoice_data = Mock(
            side_effect=lambda sale_id: {
                "invoice_number": f"INV-{sale_id}",
                "total": 1000.0 * sale_id,
            }
        )

        return service

    def test_batch_print_success(self, service_with_mocks):
        """اختبار طباعة دفعة بنجاح"""
        result = service_with_mocks.batch_print_invoices(sale_ids=[1, 2, 3], template_name=None, save_pdf=True)

        assert result["success"] == 3
        assert result["failed"] == 0
        assert len(result["files"]) == 3

    def test_batch_print_with_failures(self, service_with_mocks):
        """اختبار طباعة دفعة مع بعض الفشل"""

        # فشل فاتورة واحدة
        def mock_get_data(sale_id):
            if sale_id == 2:
                return None
            return {"invoice_number": f"INV-{sale_id}", "total": 1000.0}

        service_with_mocks._get_invoice_data.side_effect = mock_get_data

        result = service_with_mocks.batch_print_invoices(sale_ids=[1, 2, 3])

        assert result["success"] == 2
        assert result["failed"] == 1
        assert len(result["errors"]) == 1

    def test_batch_print_empty_list(self, service_with_mocks):
        """اختبار طباعة دفعة فارغة"""
        result = service_with_mocks.batch_print_invoices(sale_ids=[])

        assert result["success"] == 0
        assert result["failed"] == 0

    def test_batch_print_with_custom_template(self, service_with_mocks):
        """اختبار طباعة دفعة بقالب مخصص"""
        result = service_with_mocks.batch_print_invoices(sale_ids=[1, 2], template_name="custom_template")

        assert result["success"] == 2
        service_with_mocks.print_manager.get_template_by_name.assert_called_with("custom_template")


class TestGetInvoiceData:
    """اختبارات الحصول على بيانات الفاتورة"""

    def test_get_invoice_data_success(self):
        """اختبار الحصول على بيانات الفاتورة بنجاح"""
        mock_db = Mock()
        mock_db_config = Mock()

        # Mock database response
        mock_db.fetch_one.return_value = {
            "id": 1,
            "sale_number": "INV-001",
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "total_amount": 1000.0,
            "paid_amount": 500.0,
            "remaining_amount": 500.0,
        }
        mock_db.fetch_all.return_value = [
            {
                "product_name": "Product 1",
                "quantity": 2,
                "unit_price": 500.0,
                "total_price": 1000.0,
            }
        ]

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        # Mock get_company_info
        service._get_company_info = Mock(
            return_value={
                "name": "Test Company",
                "phone": "1234567890",
                "address": "Test Address",
            }
        )

        result = service._get_invoice_data(sale_id=1)

        assert result is not None
        assert result["invoice_number"] == "INV-001"
        assert result["customer_name"] == "Test Customer"
        assert len(result["items"]) == 1

    def test_get_invoice_data_not_found(self):
        """اختبار الحصول على فاتورة غير موجودة"""
        mock_db = Mock()
        mock_db_config = Mock()

        mock_db.fetch_one.return_value = None

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        result = service._get_invoice_data(sale_id=999)

        assert result is None


class TestGetCompanyInfo:
    """اختبارات الحصول على معلومات الشركة"""

    def test_get_company_info_with_db_values(self):
        """اختبار الحصول على معلومات الشركة من قاعدة البيانات"""
        mock_db = Mock()
        mock_db_config = Mock()

        mock_db_config.get_setting.side_effect = lambda key, default=None: {
            "company.name": "Test Company",
            "company.phone": "1234567890",
            "company.address": "Test Address",
            "company.email": "company@test.com",
            "company.tax_number": "TAX123",
        }.get(key, default)

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        result = service._get_company_info()

        assert result["name"] == "Test Company"
        assert result["phone"] == "1234567890"
        assert result["address"] == "Test Address"
        assert result["email"] == "company@test.com"
        assert result["tax_number"] == "TAX123"

    def test_get_company_info_with_defaults(self):
        """اختبار الحصول على معلومات الشركة مع قيم افتراضية"""
        mock_db = Mock()
        mock_db_config = Mock()

        mock_db_config.get_setting.return_value = None

        service = PrintService(db_manager=mock_db, db_config_manager=mock_db_config)

        result = service._get_company_info()

        assert result["name"] == "شركتي"
        assert result["phone"] == ""
        assert result["address"] == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

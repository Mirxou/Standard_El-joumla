import pytest
from unittest.mock import patch, Mock
from src.services.pdf_service import PDFService, GTKNotFoundError


class TestPDFService:
    @patch("src.services.pdf_service.Environment")
    def test_pdf_service_initialization(self, mock_env):
        """اختبار تهيئة خدمة الـ PDF ومسار القوالب"""
        service = PDFService()
        assert "assets/templates" in service.template_path

    @patch("src.services.pdf_service.Environment")
    def test_generate_invoice_pdf_success(self, mock_env):
        """اختبار توليد PDF الفاتورة بنجاح"""
        # محاكاة قالب Jinja2
        mock_template = Mock()
        mock_template.render.return_value = "<html><body>Invoice</body></html>"
        
        mock_env_instance = Mock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        service = PDFService()
        mock_invoice_data = {
            "invoice": {"id": "123", "reference": "INV-123"},
            "customer": {"name": "Test Customer"}
        }

        # محاكاة فئة HTML من WeasyPrint
        with patch("src.services.pdf_service.HTML") as mock_html_class:
            mock_html_instance = Mock()
            mock_html_instance.write_pdf.return_value = b"%PDF-1.4 mock bytes"
            mock_html_class.return_value = mock_html_instance

            pdf_bytes = service.generate_invoice_pdf(mock_invoice_data)
            
            assert pdf_bytes == b"%PDF-1.4 mock bytes"
            mock_html_class.assert_called_once_with(
                string="<html><body>Invoice</body></html>",
                base_url=service.template_path
            )
            mock_html_instance.write_pdf.assert_called_once()

    @patch("src.services.pdf_service.Environment")
    def test_generate_invoice_pdf_gtk_not_found(self, mock_env):
        """اختبار رفع استثناء GTKNotFoundError عند غياب مكتبة libgobject"""
        mock_template = Mock()
        mock_template.render.return_value = "<html><body>Invoice</body></html>"
        
        mock_env_instance = Mock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        service = PDFService()
        mock_invoice_data = {}

        # محاكاة غياب فئة HTML (gobject/GTK غير متوفر)
        with patch("src.services.pdf_service.HTML", None):
            with pytest.raises(GTKNotFoundError) as excinfo:
                service.generate_invoice_pdf(mock_invoice_data)
            
            assert "تحميل وتثبيت GTK3 Runtime" in str(excinfo.value)


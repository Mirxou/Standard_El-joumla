#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for PDF Export Service
اختبارات خدمة تصدير PDF
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from src.services.pdf_export_service import (
    PDFExportService,
    get_pdf_service,
    initialize_pdf_service,
)


class TestPDFExportServiceInitialization:
    """اختبارات تهيئة خدمة تصدير PDF"""

    def test_initialization_default(self):
        """اختبار التهيئة الافتراضية"""
        service = PDFExportService()

        assert service.default_styles is not None
        assert "page_size" in service.default_styles
        assert service.default_styles["page_size"] == "A4"

    def test_initialization_with_custom_styles(self):
        """اختبار التهيئة مع أنماط مخصصة"""
        custom_styles = {"page_size": "Letter", "margin": "1cm", "font_family": "Arial"}

        service = PDFExportService(styles=custom_styles)

        assert service.default_styles["page_size"] == "Letter"
        assert service.default_styles["margin"] == "1cm"
        assert service.default_styles["font_family"] == "Arial"


class TestHtmlToPDF:
    """اختبارات تحويل HTML إلى PDF"""

    @pytest.fixture
    def service(self):
        """إنشاء خدمة PDF"""
        return PDFExportService()

    @patch("src.services.pdf_export_service.HTML")
    @patch("src.services.pdf_export_service.Path.exists")
    @patch("src.services.pdf_export_service.Path.mkdir")
    def test_html_to_pdf_success(self, mock_mkdir, mock_exists, mock_html_class, service):
        """اختبار تحويل HTML إلى PDF بنجاح"""
        mock_exists.return_value = True
        mock_html = Mock()
        mock_html_class.return_value = mock_html

        html_content = "<html><body><h1>Test</h1></body></html>"

        result = service.html_to_pdf(html_content, "/output/test.pdf")

        assert result is True
        mock_html.write_pdf.assert_called_once_with("/output/test.pdf")

    @patch("src.services.pdf_export_service.Path.exists")
    @patch("src.services.pdf_export_service.Path.mkdir")
    def test_html_to_pdf_creates_directory(self, mock_mkdir, mock_exists, service):
        """اختبار إنشاء المجلد إذا لم يكن موجوداً"""
        mock_exists.return_value = False

        with patch("src.services.pdf_export_service.HTML") as mock_html_class:
            mock_html = Mock()
            mock_html_class.return_value = mock_html

            html_content = "<html><body>Test</body></html>"
            result = service.html_to_pdf(html_content, "/output/test.pdf")  # noqa: F841

            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("src.services.pdf_export_service.HTML")
    @patch("src.services.pdf_export_service.Path.exists")
    def test_html_to_pdf_exception(self, mock_exists, mock_html_class, service):
        """اختبار التعامل مع الاستثناء"""
        mock_exists.return_value = True
        mock_html_class.side_effect = Exception("HTML processing error")

        html_content = "<html><body>Test</body></html>"

        result = service.html_to_pdf(html_content, "/output/test.pdf")

        assert result is False

    def test_html_to_pdf_import_error(self, service):
        """اختبار عندما لا يكون weasyprint متاحاً"""
        with patch.dict("sys.modules", {"weasyprint": None}):
            html_content = "<html><body>Test</body></html>"
            result = service.html_to_pdf(html_content, "/output/test.pdf")

            # يجب أن يعيد False أو يتعامل مع الخطأ
            assert result is False or result is None


class TestUrlToPDF:
    """اختبارات تحويل URL إلى PDF"""

    @pytest.fixture
    def service(self):
        """إنشاء خدمة PDF"""
        return PDFExportService()

    @patch("src.services.pdf_export_service.HTML")
    @patch("src.services.pdf_export_service.Path.exists")
    def test_url_to_pdf_success(self, mock_exists, mock_html_class, service):
        """اختبار تحويل URL إلى PDF بنجاح"""
        mock_exists.return_value = True
        mock_html = Mock()
        mock_html_class.return_value = mock_html

        result = service.url_to_pdf("http://example.com", "/output/test.pdf")

        assert result is True
        mock_html_class.assert_called_once_with(url="http://example.com")
        mock_html.write_pdf.assert_called_once_with("/output/test.pdf")

    @patch("src.services.pdf_export_service.HTML")
    @patch("src.services.pdf_export_service.Path.exists")
    def test_url_to_pdf_with_options(self, mock_exists, mock_html_class, service):
        """اختبار تحويل URL مع خيارات إضافية"""
        mock_exists.return_value = True
        mock_html = Mock()
        mock_html_class.return_value = mock_html

        result = service.url_to_pdf(
            "http://example.com",
            "/output/test.pdf",
            media_type="print",
            base_url="http://base.com",
        )

        assert result is True


class TestFileToPDF:
    """اختبارات تحويل ملف HTML إلى PDF"""

    @pytest.fixture
    def service(self):
        """إنشاء خدمة PDF"""
        return PDFExportService()

    @patch("src.services.pdf_export_service.HTML")
    @patch("src.services.pdf_export_service.Path.exists")
    def test_file_to_pdf_success(self, mock_exists, mock_html_class, service):
        """اختبار تحويل ملف إلى PDF بنجاح"""
        mock_exists.return_value = True
        mock_html = Mock()
        mock_html_class.return_value = mock_html

        with patch("builtins.open", mock_open(read_data="<html><body>Test</body></html>")):
            result = service.file_to_pdf("/input/test.html", "/output/test.pdf")

            assert result is True
            mock_html_class.assert_called_once()

    @patch("src.services.pdf_export_service.Path.exists")
    def test_file_to_pdf_file_not_found(self, mock_exists, service):
        """اختبار تحويل ملف غير موجود"""
        mock_exists.return_value = False

        result = service.file_to_pdf("/input/nonexistent.html", "/output/test.pdf")

        assert result is False

    @patch("src.services.pdf_export_service.HTML")
    @patch("src.services.pdf_export_service.Path.exists")
    def test_file_to_pdf_exception(self, mock_exists, mock_html_class, service):
        """اختبار التعامل مع استثناء أثناء قراءة الملف"""
        mock_exists.return_value = True
        mock_html_class.side_effect = Exception("Processing error")

        with patch("builtins.open", mock_open(read_data="<html>Test</html>")):
            result = service.file_to_pdf("/input/test.html", "/output/test.pdf")

            assert result is False


class TestApplyStyles:
    """اختبارات تطبيق الأنماط"""

    def test_apply_styles_default(self):
        """اختبار تطبيق الأنماط الافتراضية"""
        service = PDFExportService()
        html_content = "<h1>Test</h1>"

        result = service.apply_styles(html_content)

        assert "<style>" in result
        assert "@page" in result
        assert "body" in result

    def test_apply_styles_custom(self):
        """اختبار تطبيق أنماط مخصصة"""
        custom_styles = {
            "page_size": "Letter",
            "margin": "2cm",
            "font_family": "Times New Roman",
        }
        service = PDFExportService(styles=custom_styles)
        html_content = "<h1>Test</h1>"

        result = service.apply_styles(html_content)

        assert "Letter" in result or "margin" in result
        assert "font-family" in result

    def test_apply_styles_existing_html_structure(self):
        """اختبار تطبيق الأنماط على HTML كامل"""
        service = PDFExportService()
        html_content = """
        <html>
        <head><title>Test</title></head>
        <body><h1>Hello</h1></body>
        </html>
        """

        result = service.apply_styles(html_content)

        assert "<html>" in result
        assert "<style>" in result


class TestAddHeaderFooter:
    """اختبارات إضافة رأس وتذييل الصفحة"""

    @pytest.fixture
    def service(self):
        """إنشاء خدمة PDF"""
        return PDFExportService()

    def test_add_header_footer(self, service):
        """اختبار إضافة رأس وتذييل"""
        html_content = "<html><body><h1>Content</h1></body></html>"

        result = service.add_header_footer(
            html_content,
            header_text="Header Text",
            footer_text="Footer Text",
            page_numbers=True,
        )

        assert "Header Text" in result
        assert "Footer Text" in result
        assert "page" in result.lower() or "counter" in result.lower()

    def test_add_header_footer_no_page_numbers(self, service):
        """اختبار إضافة رأس وتذييل بدون أرقام صفحات"""
        html_content = "<html><body>Content</body></html>"

        result = service.add_header_footer(html_content, header_text="Header", footer_text="Footer", page_numbers=False)

        assert "Header" in result
        assert "Footer" in result

    def test_add_header_footer_only_header(self, service):
        """اختبار إضافة رأس فقط"""
        html_content = "<html><body>Content</body></html>"

        result = service.add_header_footer(html_content, header_text="Header Only")

        assert "Header Only" in result


class TestMergePDFs:
    """اختبارات دمج ملفات PDF"""

    @pytest.fixture
    def service(self):
        """إنشاء خدمة PDF"""
        return PDFExportService()

    @patch("src.services.pdf_export_service.PdfMerger")
    @patch("src.services.pdf_export_service.Path.exists")
    def test_merge_pdfs_success(self, mock_exists, mock_merger_class, service):
        """اختبار دمج PDFs بنجاح"""
        mock_exists.return_value = True
        mock_merger = Mock()
        mock_merger_class.return_value = mock_merger

        result = service.merge_pdfs(["/file1.pdf", "/file2.pdf"], "/output/merged.pdf")

        assert result is True
        assert mock_merger.append.call_count == 2
        mock_merger.write.assert_called_once_with("/output/merged.pdf")

    @patch("src.services.pdf_export_service.Path.exists")
    def test_merge_pdfs_file_not_found(self, mock_exists, service):
        """اختبار دمج مع ملف غير موجود"""
        mock_exists.return_value = False

        result = service.merge_pdfs(["/file1.pdf", "/nonexistent.pdf"], "/output/merged.pdf")

        assert result is False

    @patch("src.services.pdf_export_service.Path.exists")
    def test_merge_pdfs_empty_list(self, mock_exists, service):
        """اختبار دمج قائمة فارغة"""
        result = service.merge_pdfs([], "/output/merged.pdf")

        assert result is False


class TestAddWatermark:
    """اختبارات إضافة علامة مائية"""

    @pytest.fixture
    def service(self):
        """إنشاء خدمة PDF"""
        return PDFExportService()

    @patch("src.services.pdf_export_service.PdfReader")
    @patch("src.services.pdf_export_service.PdfWriter")
    @patch("src.services.pdf_export_service.Path.exists")
    def test_add_watermark_success(self, mock_exists, mock_writer_class, mock_reader_class, service):
        """اختبار إضافة علامة مائية بنجاح"""
        mock_exists.return_value = True

        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock()]  # صفحتان
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        with patch("builtins.open", mock_open()):
            result = service.add_watermark("/input/test.pdf", "/output/watermarked.pdf", "WATERMARK", opacity=0.5)

            assert result is True
            mock_writer.write.assert_called_once()

    @patch("src.services.pdf_export_service.Path.exists")
    def test_add_watermark_file_not_found(self, mock_exists, service):
        """اختبار إضافة علامة مائية لملف غير موجود"""
        mock_exists.return_value = False

        result = service.add_watermark("/input/nonexistent.pdf", "/output/watermarked.pdf", "WATERMARK")

        assert result is False


class TestGlobalFunctions:
    """اختبارات الدوال العامة"""

    def test_initialize_pdf_service(self):
        """اختبار تهيئة خدمة PDF العامة"""
        with patch("src.services.pdf_export_service.PDFExportService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            result = initialize_pdf_service()

            assert result == mock_service

    def test_get_pdf_service(self):
        """اختبار الحصول على خدمة PDF العامة"""
        # يجب أن يعيد None قبل التهيئة
        result = get_pdf_service()
        assert result is None or isinstance(result, PDFExportService)


class TestEncryptPDF:
    """اختبارات تشفير PDF"""

    @pytest.fixture
    def service(self):
        """إنشاء خدمة PDF"""
        return PDFExportService()

    @patch("src.services.pdf_export_service.PdfReader")
    @patch("src.services.pdf_export_service.PdfWriter")
    @patch("src.services.pdf_export_service.Path.exists")
    def test_encrypt_pdf_success(self, mock_exists, mock_writer_class, mock_reader_class, service):
        """اختبار تشفير PDF بنجاح"""
        mock_exists.return_value = True

        mock_reader = Mock()
        mock_reader.pages = [Mock()]
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        with patch("builtins.open", mock_open()):
            result = service.encrypt_pdf("/input/test.pdf", "/output/encrypted.pdf", password="secret123")

            assert result is True
            mock_writer.encrypt.assert_called_once_with("secret123")

    @patch("src.services.pdf_export_service.Path.exists")
    def test_encrypt_pdf_file_not_found(self, mock_exists, service):
        """اختبار تشفير ملف غير موجود"""
        mock_exists.return_value = False

        result = service.encrypt_pdf("/input/nonexistent.pdf", "/output/encrypted.pdf", password="secret")

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

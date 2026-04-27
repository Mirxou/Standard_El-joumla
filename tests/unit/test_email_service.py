#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Email Service
اختبارات خدمة البريد الإلكتروني
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from email.mime.multipart import MIMEMultipart
from src.services.email_service import EmailService, DEFAULT_INVOICE_EMAIL_HTML, DEFAULT_INVOICE_EMAIL_TEXT


class TestEmailServiceInitialization:
    """اختبارات تهيئة خدمة البريد"""
    
    def test_initialization_with_config(self):
        """اختبار التهيئة مع إعدادات"""
        mock_print_service = Mock()
        config = {
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_user': 'user@example.com',
            'smtp_password': 'password',
            'smtp_from': 'from@example.com',
            'smtp_tls': True
        }
        
        service = EmailService(config=config, print_service=mock_print_service)
        
        assert service.smtp_host == 'smtp.example.com'
        assert service.smtp_port == 587
        assert service.smtp_user == 'user@example.com'
        assert service.smtp_password == 'password'
        assert service.smtp_from == 'from@example.com'
        assert service.smtp_tls is True
        assert service._print_service == mock_print_service
    
    def test_initialization_with_default_config(self):
        """اختبار التهيئة مع إعدادات افتراضية"""
        mock_print_service = Mock()
        
        service = EmailService(print_service=mock_print_service)
        
        assert service.smtp_host == 'localhost'
        assert service.smtp_port == 587
        assert service.smtp_tls is True


class TestRenderTemplate:
    """اختبارات تصيير القالب"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة البريد"""
        mock_print_service = Mock()
        config = {'smtp_from': 'from@example.com'}
        return EmailService(config=config, print_service=mock_print_service)
    
    def test_render_template_with_variables(self, service):
        """اختبار تصيير القالب مع متغيرات"""
        template = "Hello {{ name }}, your invoice is {{ invoice_number }}"
        data = {'name': 'John', 'invoice_number': '12345'}
        
        result = service.render_template(template, data)
        
        assert result == "Hello John, your invoice is 12345"
    
    def test_render_template_with_missing_variable(self, service):
        """اختبار تصيير القالب مع متغير مفقود"""
        template = "Hello {{ name }}, your invoice is {{ invoice_number }}"
        data = {'name': 'John'}
        
        result = service.render_template(template, data)
        
        assert result == "Hello John, your invoice is "
    
    def test_render_template_empty_data(self, service):
        """اختبار تصيير القالب مع بيانات فارغة"""
        template = "Hello {{ name }}"
        data = {}
        
        result = service.render_template(template, data)
        
        assert result == "Hello "


class TestSendEmail:
    """اختبارات إرسال البريد"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة البريد"""
        mock_print_service = Mock()
        config = {
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_from': 'from@example.com',
            'smtp_tls': True
        }
        return EmailService(config=config, print_service=mock_print_service)
    
    @patch('smtplib.SMTP')
    @patch('ssl.create_default_context')
    def test_send_email_success(self, mock_ssl, mock_smtp_class, service):
        """اختبار إرسال البريد بنجاح"""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        result = service.send_email(
            to='to@example.com',
            subject='Test Subject',
            body_html='<p>Test</p>',
            body_text='Test'
        )
        
        assert result['success'] is True
        assert 'to@example.com' in result['recipients']
        mock_smtp.ehlo.assert_called()
        mock_smtp.starttls.assert_called()
        mock_smtp.send_message.assert_called_once()
    
    @patch('smtplib.SMTP_SSL')
    @patch('ssl.create_default_context')
    def test_send_email_with_port_465(self, mock_ssl, mock_smtp_ssl, service):
        """اختبار إرسال البريد مع المنفذ 465"""
        service.smtp_port = 465
        mock_smtp = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_smtp
        
        result = service.send_email(
            to='to@example.com',
            subject='Test Subject',
            body_html='<p>Test</p>'
        )
        
        assert result['success'] is True
        mock_smtp_ssl.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_exception(self, mock_smtp_class, service):
        """اختبار إرسال البريد مع استثناء"""
        mock_smtp_class.side_effect = Exception("SMTP Error")
        
        result = service.send_email(
            to='to@example.com',
            subject='Test Subject',
            body_html='<p>Test</p>'
        )
        
        assert 'error' in result
    
    def test_send_email_with_multiple_recipients(self, service):
        """اختبار إرسال البريد لعدة مستلمين"""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            result = service.send_email(
                to=['to1@example.com', 'to2@example.com'],
                cc='cc@example.com',
                bcc='bcc@example.com',
                subject='Test Subject',
                body_html='<p>Test</p>'
            )
            
            assert result['success'] is True
            assert 'to1@example.com' in result['recipients']
            assert 'to2@example.com' in result['recipients']
            assert 'cc@example.com' in result['recipients']
            assert 'bcc@example.com' in result['recipients']


class TestSendInvoiceEmail:
    """اختبارات إرسال البريد بالفاتورة"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة البريد"""
        mock_print_service = Mock()
        mock_print_service._get_invoice_data.return_value = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'invoice_number': 'INV-001',
            'date': '2024-01-01',
            'total': '1000.00',
            'paid': '500.00',
            'remaining': '500.00',
            'company_name': 'Test Company',
            'company_phone': '1234567890',
            'company_address': 'Test Address'
        }
        mock_print_service.print_invoice.return_value = {'success': True}
        
        config = {
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_from': 'from@example.com'
        }
        return EmailService(config=config, print_service=mock_print_service)
    
    @patch('smtplib.SMTP')
    def test_send_invoice_email_success(self, mock_smtp_class, service):
        """اختبار إرسال الفاتورة بنجاح"""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        result = service.send_invoice_email(
            sale_id=1,
            to_email='john@example.com',
            include_pdf=True
        )
        
        assert result['success'] is True
        service._print_service._get_invoice_data.assert_called_once_with(1)
        service._print_service.print_invoice.assert_called_once()
    
    def test_send_invoice_email_invoice_not_found(self, service):
        """اختبار إرسال الفاتورة مع عدم وجود الفاتورة"""
        service._print_service._get_invoice_data.return_value = None
        
        result = service.send_invoice_email(sale_id=999)
        
        assert result['success'] is False
        assert 'Invoice not found' in result['error']
    
    def test_send_invoice_email_no_email_provided_or_found(self, service):
        """اختبار إرسال الفاتورة بدون بريد إلكتروني"""
        service._print_service._get_invoice_data.return_value = {
            'customer_name': 'John Doe',
            'customer_email': None
        }
        
        result = service.send_invoice_email(sale_id=1)
        
        assert result['success'] is False
        assert 'Recipient email not provided' in result['error']
    
    def test_send_invoice_email_pdf_generation_failed(self, service):
        """اختبار إرسال الفاتورة مع فشل إنشاء PDF"""
        service._print_service.print_invoice.return_value = {'success': False}
        
        result = service.send_invoice_email(
            sale_id=1,
            to_email='john@example.com',
            include_pdf=True
        )
        
        assert result['success'] is False
        assert 'Failed to generate invoice PDF' in result['error']
    
    @patch('smtplib.SMTP')
    def test_send_invoice_email_derive_email_from_invoice(self, mock_smtp_class, service):
        """اختبار استخلاص البريد من الفاتورة"""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        result = service.send_invoice_email(sale_id=1)  # بدون to_email
        
        assert result['success'] is True


class TestSendAlert:
    """اختبارات إرسال التنبيهات"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة البريد"""
        mock_print_service = Mock()
        config = {'smtp_from': 'from@example.com'}
        return EmailService(config=config, print_service=mock_print_service)
    
    @patch('smtplib.SMTP')
    def test_send_alert_success(self, mock_smtp_class, service):
        """اختبار إرسال التنبيه بنجاح"""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        result = service.send_alert(
            to='alert@example.com',
            title='Test Alert',
            message='This is a test alert'
        )
        
        assert result['success'] is True
        mock_smtp.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_alert_creates_html(self, mock_smtp_class, service):
        """اختبار أن send_alert ينشئ HTML"""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        result = service.send_alert(
            to='alert@example.com',
            title='Alert Title',
            message='Alert Message'
        )
        
        # التحقق من أن الرسالة تحتوي على HTML
        call_args = mock_smtp.send_message.call_args
        msg = call_args[0][0]
        assert 'Alert Title' in str(msg)
        assert 'Alert Message' in str(msg)


class TestSendReport:
    """اختبارات إرسال التقارير"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة البريد"""
        mock_print_service = Mock()
        config = {'smtp_from': 'from@example.com'}
        return EmailService(config=config, print_service=mock_print_service)
    
    @patch('smtplib.SMTP')
    def test_send_report_without_pdf(self, mock_smtp_class, service):
        """اختبار إرسال التقرير بدون PDF"""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        result = service.send_report(
            to='report@example.com',
            title='Monthly Report',
            html_content='<h1>Report</h1><p>Content</p>'
        )
        
        assert result['success'] is True
        # يجب أن لا يكون هناك مرفقات
        call_args = mock_smtp.send_message.call_args
        msg = call_args[0][0]
        assert msg.get_content_type() == 'text/html'
    
    @patch('smtplib.SMTP')
    @patch('src.services.email_service.PDFExportService')
    def test_send_report_with_pdf(self, mock_pdf_class, mock_smtp_class, service):
        """اختبار إرسال التقرير مع PDF"""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        
        mock_pdf = Mock()
        mock_pdf.html_to_pdf.return_value = True
        mock_pdf_class.return_value = mock_pdf
        
        with patch('builtins.open', mock_open(read_data=b'PDF content')):
            with patch('pathlib.Path.exists', return_value=True):
                result = service.send_report(
                    to='report@example.com',
                    title='Monthly Report',
                    html_content='<h1>Report</h1>',
                    pdf_filename='report.pdf'
                )
                
                assert result['success'] is True


class TestSmtpLogin:
    """اختبارات تسجيل الدخول SMTP"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة البريد مع بيانات اعتماد"""
        mock_print_service = Mock()
        config = {
            'smtp_user': 'user@example.com',
            'smtp_password': 'password123'
        }
        return EmailService(config=config, print_service=mock_print_service)
    
    def test_smtp_login_with_credentials(self, service):
        """اختبار تسجيل الدخول مع بيانات اعتماد"""
        mock_server = Mock()
        
        service._smtp_login(mock_server)
        
        mock_server.login.assert_called_once_with('user@example.com', 'password123')
    
    def test_smtp_login_without_credentials(self):
        """اختبار تسجيل الدخول بدون بيانات اعتماد"""
        mock_print_service = Mock()
        service = EmailService(config={}, print_service=mock_print_service)
        mock_server = Mock()
        
        service._smtp_login(mock_server)
        
        mock_server.login.assert_not_called()


class TestDefaultTemplates:
    """اختبارات القوالب الافتراضية"""
    
    def test_default_invoice_html_structure(self):
        """اختبار بناء قالب HTML الافتراضي"""
        assert '<html lang="ar" dir="rtl">' in DEFAULT_INVOICE_EMAIL_HTML
        assert '{{ company_name }}' in DEFAULT_INVOICE_EMAIL_HTML
        assert '{{ customer_name }}' in DEFAULT_INVOICE_EMAIL_HTML
        assert '{{ invoice_number }}' in DEFAULT_INVOICE_EMAIL_HTML
        assert '{{ total }}' in DEFAULT_INVOICE_EMAIL_HTML
        assert '{{ paid }}' in DEFAULT_INVOICE_EMAIL_HTML
        assert '{{ remaining }}' in DEFAULT_INVOICE_EMAIL_HTML
    
    def test_default_invoice_text_structure(self):
        """اختبار بناء قالب النص الافتراضي"""
        assert '{{ company_name }}' in DEFAULT_INVOICE_EMAIL_TEXT
        assert '{{ customer_name }}' in DEFAULT_INVOICE_EMAIL_TEXT
        assert '{{ invoice_number }}' in DEFAULT_INVOICE_EMAIL_TEXT
        assert '{{ total }}' in DEFAULT_INVOICE_EMAIL_TEXT
        assert 'دج' in DEFAULT_INVOICE_EMAIL_TEXT


class TestEmailValidation:
    """اختبارات التحقق من صحة البريد"""
    
    def test_validate_email_format(self):
        """اختبار التحقق من تنسيق البريد"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org'
        ]
        for email in valid_emails:
            assert '@' in email
            assert '.' in email.split('@')[1]


class TestEmailServiceConfiguration:
    """اختبارات إعدادات خدمة البريد"""
    
    @pytest.fixture
    def service_with_full_config(self):
        """إنشاء خدمة مع إعدادات كاملة"""
        mock_print_service = Mock()
        config = {
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_user': 'user@example.com',
            'smtp_password': 'password123',
            'smtp_from': 'from@example.com',
            'use_tls': True
        }
        return EmailService(config=config, print_service=mock_print_service)
    
    def test_service_configuration(self, service_with_full_config):
        """اختبار إعدادات الخدمة"""
        assert service_with_full_config.config is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])




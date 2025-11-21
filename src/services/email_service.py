"""
خدمة البريد الإلكتروني
Email Service

إرسال رسائل بريد إلكتروني مع دعم القوالب والمرفقات (PDF)
Send emails with templates and PDF attachments
"""

from __future__ import annotations

import os
import ssl
import smtplib
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
import logging

from jinja2 import Environment, BaseLoader, select_autoescape

from src.services.print_service import PrintService

logger = logging.getLogger(__name__)


class EmailService:
    """
    خدمة البريد الإلكتروني باستخدام SMTP

    الإعداد عبر متغيرات البيئة:
    - SMTP_HOST (إلزامي)
    - SMTP_PORT (افتراضي 587)
    - SMTP_USER (اختياري)
    - SMTP_PASSWORD (اختياري)
    - SMTP_TLS (افتراضي true)
    - SMTP_FROM (العنوان الافتراضي للإرسال)
    """

    def __init__(self) -> None:
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_tls = os.getenv("SMTP_TLS", "true").lower() in ("1", "true", "yes", "on")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user or "no-reply@example.com")

        self._jinja = Environment(loader=BaseLoader(), autoescape=select_autoescape(['html', 'xml']))
        self._print_service = PrintService()

    def _ensure_smtp_config(self) -> None:
        if not self.smtp_host:
            raise RuntimeError("SMTP_HOST is not configured")

    def render_template(self, template_str: str, data: Dict[str, Any]) -> str:
        """تصيير قالب بريد إلكتروني باستخدام Jinja2"""
        template = self._jinja.from_string(template_str)
        return template.render(**data)

    def send_email(
        self,
        to: List[str] | str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        إرسال بريد إلكتروني عام.
        attachments: قائمة عناصر من الشكل { 'filename': str, 'content': bytes, 'mime': 'application/pdf' }
        """
        self._ensure_smtp_config()

        if isinstance(to, str):
            recipients = [to]
        else:
            recipients = to
        all_rcpts = list(recipients) + (cc or []) + (bcc or [])

        msg = EmailMessage()
        msg['From'] = self.smtp_from
        msg['To'] = ', '.join(recipients)
        if cc:
            msg['Cc'] = ', '.join(cc)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        if headers:
            for k, v in headers.items():
                msg[k] = v

        # بديل نصي تلقائي إذا لم يُمرر body_text
        if not body_text and body_html:
            body_text = """هذا البريد يحتوي على محتوى HTML. يرجى استخدام عميل بريد يدعم HTML."""

        if body_html:
            msg.add_alternative(body_html, subtype='html')
        if body_text:
            # اجعل النص العادي جزءاً منفصلاً
            if msg.get_content_maintype() == 'multipart':
                # أضف بديل نصي
                msg.get_payload()[0].set_content(body_text)
            else:
                msg.set_content(body_text)

        # مرفقات
        if attachments:
            for att in attachments:
                content = att.get('content', b'')
                filename = att.get('filename', 'attachment.bin')
                mime = att.get('mime', 'application/octet-stream')
                maintype, _, subtype = mime.partition('/')
                msg.add_attachment(content, maintype=maintype, subtype=subtype or 'octet-stream', filename=filename)

        # إرسال عبر SMTP
        context = ssl.create_default_context()
        logger.info(f"Sending email to {all_rcpts} via {self.smtp_host}:{self.smtp_port}")
        if self.smtp_tls and self.smtp_port == 465:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                self._smtp_login(server)
                server.send_message(msg, from_addr=self.smtp_from, to_addrs=all_rcpts)
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                if self.smtp_tls:
                    server.starttls(context=context)
                    server.ehlo()
                self._smtp_login(server)
                server.send_message(msg, from_addr=self.smtp_from, to_addrs=all_rcpts)

        return {"success": True, "recipients": all_rcpts}

    def _smtp_login(self, server: smtplib.SMTP) -> None:
        if self.smtp_user and self.smtp_password:
            server.login(self.smtp_user, self.smtp_password)

    def send_invoice_email(
        self,
        sale_id: int,
        to_email: Optional[str] = None,
        subject: Optional[str] = None,
        include_pdf: bool = True,
        template_html: Optional[str] = None,
        template_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        إرسال فاتورة بالبريد مع خيار إرفاق PDF مولد من خدمة الطباعة.
        إذا لم يُمرر to_email سيتم محاولة جلب بريد العميل من قاعدة البيانات عبر PrintService.
        """
        # الحصول على بيانات الفاتورة لاشتقاق البريد وملء القالب
        invoice_data = self._print_service._get_invoice_data(sale_id)
        if not invoice_data:
            return {"success": False, "error": "Invoice not found"}

        # اشتقاق البريد إن لم يُمرر
        if not to_email:
            # محاولة قراءة بريد العميل إن وُجد
            to_email = invoice_data.get('customer_email') or ''
            if not to_email:
                return {"success": False, "error": "Recipient email not provided and not found on customer"}

        # تصيير جسم الرسالة
        if not subject:
            subject = f"فاتورة رقم {invoice_data.get('invoice_number', sale_id)}"
        if not template_html:
            template_html = DEFAULT_INVOICE_EMAIL_HTML
        if not template_text:
            template_text = DEFAULT_INVOICE_EMAIL_TEXT

        body_html = self.render_template(template_html, invoice_data)
        body_text = self.render_template(template_text, invoice_data)

        attachments: List[Dict[str, Any]] = []
        if include_pdf:
            # أنشئ PDF مؤقت وارفقه
            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = Path(tmpdir) / f"invoice_{sale_id}.pdf"
                pdf_result = self._print_service.print_invoice(
                    sale_id=sale_id,
                    save_pdf=True,
                    pdf_path=str(pdf_path)
                )
                if not pdf_result.get('success'):
                    return {"success": False, "error": "Failed to generate invoice PDF"}
                content = Path(pdf_path).read_bytes()
                attachments.append({
                    'filename': f"invoice_{invoice_data.get('invoice_number', sale_id)}.pdf",
                    'content': content,
                    'mime': 'application/pdf'
                })

        return self.send_email(
            to=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            attachments=attachments
        )

    def send_alert(self, to: str | List[str], title: str, message: str) -> Dict[str, Any]:
        """إرسال تنبيه نصي بسيط عبر البريد"""
        html = f"""
        <html dir="rtl"><body>
            <h3>{title}</h3>
            <p>{message}</p>
        </body></html>
        """
        return self.send_email(to=to, subject=title, body_html=html, body_text=message)

    def send_report(
        self,
        to: str | List[str],
        title: str,
        html_content: str,
        pdf_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """إرسال تقرير HTML مع خيار إرفاقه كـ PDF"""
        attachments: List[Dict[str, Any]] = []
        if pdf_filename:
            # تحويل HTML إلى PDF عبر خدمة PDF مباشرة
            from src.services.pdf_export_service import PDFExportService
            pdf = PDFExportService()
            with tempfile.TemporaryDirectory() as tmpdir:
                out = Path(tmpdir) / pdf_filename
                ok = pdf.html_to_pdf(html_content, str(out))
                if ok:
                    attachments.append({'filename': pdf_filename, 'content': out.read_bytes(), 'mime': 'application/pdf'})
        return self.send_email(to=to, subject=title, body_html=html_content, attachments=attachments)


DEFAULT_INVOICE_EMAIL_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.7; }
    .box { border: 1px solid #ddd; padding: 16px; border-radius: 8px; }
    .muted { color: #666; font-size: 12px; }
  </style>
</head>
<body>
  <div class="box">
    <h2>فاتورتك من {{ company_name }}</h2>
    <p>عميلنا العزيز {{ customer_name }},</p>
    <p>مرفق فاتورتك رقم <strong>{{ invoice_number }}</strong> بتاريخ {{ date }}.</p>
    <ul>
      <li>الإجمالي: <strong>{{ total }}</strong> دج</li>
      <li>المدفوع: <strong>{{ paid }}</strong> دج</li>
      <li>المتبقي: <strong>{{ remaining }}</strong> دج</li>
    </ul>
    <p class="muted">للاستفسار، تواصل معنا: {{ company_phone }} — {{ company_address }}</p>
  </div>
</body>
</html>
"""

DEFAULT_INVOICE_EMAIL_TEXT = (
    "عميلنا العزيز {{ customer_name }}\n"
    "مرفق فاتورتك رقم {{ invoice_number }} بتاريخ {{ date }}.\n"
    "الإجمالي: {{ total }} دج - المدفوع: {{ paid }} دج - المتبقي: {{ remaining }} دج\n"
    "{{ company_name }} — {{ company_phone }}"
)

import os
import logging
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any

logger = logging.getLogger(__name__)

# محاولة استيراد weasyprint على مستوى الموديل لتمكين الـ Mocking والـ Patching
try:
    from weasyprint import HTML
except (ImportError, OSError):
    HTML = None


class GTKNotFoundError(OSError):
    """استثناء مخصص يشرح للمستخدم كيفية تحميل وتثبيت حزمة GTK+ لتمكين الطباعة"""
    def __init__(self, original_error=None):
        message = (
            "تعذر توليد ملف PDF بسبب غياب مكتبات النظام الثنائية GTK+ / gobject المطلوبة من WeasyPrint على نظام Windows.\n"
            "لحل هذه المشكلة وتفعيل ميزة فواتير PDF، يرجى:\n"
            "1. تحميل وتثبيت GTK3 Runtime من الرابط التالي:\n"
            "   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases\n"
            "2. تأكد من تحديد خيار 'إضافة إلى مسار النظام (PATH)' أثناء التثبيت.\n"
            "3. أعد تشغيل التطبيق أو خادم الـ API لتطبيق التغييرات."
        )
        super().__init__(message)
        self.original_error = original_error


class PDFService:
    def __init__(self, templates_dir: str = "assets/templates"):
        """
        تهيئة محرك Jinja2 لربط القوالب بمسار المشروع.
        """
        # تحديد المسار المطلق لمجلد القوالب لضمان عدم حدوث أخطاء أثناء النشر
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.template_path = os.path.join(base_dir, templates_dir)
        
        self.env = Environment(
            loader=FileSystemLoader(self.template_path),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate_invoice_pdf(self, invoice_data: Dict[str, Any], output_path: str = None) -> bytes:
        """
        تولد ملف PDF للفاتورة باستخدام WeasyPrint مع التحقق الآمن من مكتبات النظام.
        """
        # 1. جلب القالب ورندرة الـ HTML
        template = self.env.get_template("invoice_template.html")
        html_out = template.render(
            invoice=invoice_data.get('invoice', {}),
            customer=invoice_data.get('customer', {})
        )

        # 2. محاولة توليد PDF
        if HTML is None:
            logger.warning("WeasyPrint HTML class is not available (missing GTK+ dependencies).")
            raise GTKNotFoundError()

        try:
            # توليد PDF
            pdf_bytes = HTML(string=html_out, base_url=self.template_path).write_pdf()
            
            # حفظ الملف محلياً إذا تم طلب ذلك
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                    
            return pdf_bytes

        except Exception as e:
            logger.error("Failed to generate PDF using WeasyPrint: %s", str(e))
            raise e


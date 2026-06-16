import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Invoice Print Service - HTML Template Engine
خدمة طباعة الفواتير باستخدام Jinja2 و HTML Templates
"""

import base64
import io
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Try to import QR Code and Barcode libraries
try:
    import qrcode

    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    qrcode = None

try:
    import barcode
    from barcode.writer import ImageWriter

    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False
    barcode = None

logger = logging.getLogger(__name__)


class InvoicePrintService:
    """
    خدمة طباعة الفواتير الاحترافية
    تستخدم Jinja2 لملء قوالب HTML بالبيانات
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        تهيئة خدمة الطباعة

        Args:
            template_dir: مسار مجلد القوالب (افتراضي: assets/templates)
        """
        # تحديد مسار القوالب
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # البحث عن مجلد القوالب
            base_path = Path(__file__).parent.parent.parent
            self.template_dir = base_path / "assets" / "templates"

        # إنشاء مجلد القوالب إذا لم يكن موجوداً
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # تهيئة Jinja2 Environment
        try:
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
            )
            logger.info(f"✅ تم تحميل قوالب الطباعة من: {self.template_dir}")
        except Exception as e:
            logger.log(logging.ERROR, f"❌ فشل تحميل قوالب الطباعة: {e}")
            self.env = None

    def generate_invoice_html(
        self, invoice_data: Dict[str, Any], template_name: str = "invoice.html"
    ) -> tuple[bool, str, Optional[str]]:
        """
        توليد فاتورة HTML من القالب

        Args:
            invoice_data: Dictionary يحتوي على بيانات الفاتورة
            template_name: اسم ملف القالب (افتراضي: invoice.html)

        Returns:
            tuple: (success, message, html_content)
        """
        if not self.env:
            return False, "قوالب الطباعة غير متاحة", None

        try:
            # 1. تحميل القالب
            try:
                template = self.env.get_template(template_name)
            except TemplateNotFound:
                return (
                    False,
                    f"القالب '{template_name}' غير موجود في {self.template_dir}",
                    None,
                )

            # 2. إعداد البيانات مع القيم الافتراضية
            formatted_data = self._format_invoice_data(invoice_data)

            # 3. ملء القالب بالبيانات
            html_content = template.render(**formatted_data)

            return True, "تم توليد الفاتورة بنجاح", html_content

        except Exception as e:
            error_msg = f"خطأ في توليد الفاتورة: {str(e)}"
            logger.log(logging.ERROR, error_msg)
            return False, error_msg, None

    def print_invoice(
        self,
        invoice_data: Dict[str, Any],
        template_name: str = "invoice.html",
        auto_print: bool = False,
    ) -> tuple[bool, str]:
        """
        طباعة فاتورة (فتح في المتصفح)

        Args:
            invoice_data: Dictionary يحتوي على بيانات الفاتورة
            template_name: اسم ملف القالب
            auto_print: فتح نافذة الطباعة تلقائياً

        Returns:
            tuple: (success, message)
        """
        # توليد HTML
        success, message, html_content = self.generate_invoice_html(invoice_data, template_name)

        if not success or not html_content:
            return False, message

        try:
            # حفظ الملف مؤقتاً
            temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8")
            temp_file.write(html_content)
            temp_file.close()

            temp_path = Path(temp_file.name)

            # فتح الملف في المتصفح الافتراضي
            file_url = f"file:///{temp_path.absolute().as_posix()}"
            webbrowser.open(file_url)

            if auto_print:
                # إضافة script للطباعة التلقائية (سيتم تنفيذه في المتصفح)
                logger.info("تم فتح نافذة الطباعة")

            return True, f"تم فتح الفاتورة في المتصفح: {temp_path.name}"

        except Exception as e:
            error_msg = f"خطأ في فتح الفاتورة: {str(e)}"
            logger.log(logging.ERROR, error_msg)
            return False, error_msg

    def save_invoice_html(
        self,
        invoice_data: Dict[str, Any],
        output_path: str,
        template_name: str = "invoice.html",
    ) -> tuple[bool, str]:
        """
        حفظ الفاتورة كملف HTML

        Args:
            invoice_data: Dictionary يحتوي على بيانات الفاتورة
            output_path: مسار الملف الناتج
            template_name: اسم ملف القالب

        Returns:
            tuple: (success, message)
        """
        # توليد HTML
        success, message, html_content = self.generate_invoice_html(invoice_data, template_name)

        if not success or not html_content:
            return False, message

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            return True, f"تم حفظ الفاتورة في: {output_path}"

        except Exception as e:
            error_msg = f"خطأ في حفظ الفاتورة: {str(e)}"
            logger.log(logging.ERROR, error_msg)
            return False, error_msg

    def _format_invoice_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تنسيق بيانات الفاتورة وإضافة القيم الافتراضية

        Args:
            data: بيانات الفاتورة الخام

        Returns:
            Dictionary منسق مع القيم الافتراضية
        """
        # التاريخ والوقت
        now = datetime.now()
        print_date = now.strftime("%Y-%m-%d %H:%M:%S")

        # تنسيق تاريخ الفاتورة
        invoice_date = data.get("date", now.strftime("%Y-%m-%d"))
        if isinstance(invoice_date, str):
            try:
                # محاولة تحويل التاريخ إلى تنسيق أفضل
                date_obj = datetime.strptime(invoice_date, "%Y-%m-%d")
                invoice_date = date_obj.strftime("%Y-%m-%d")
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in invoice_print_service.py")

        # تنسيق الأصناف
        items = data.get("items", [])
        formatted_items = []
        for item in items:
            formatted_items.append(
                {
                    "name": item.get("name", "منتج غير محدد"),
                    "barcode": item.get("barcode", ""),
                    "qty": item.get("quantity", item.get("qty", 0)),
                    "price": float(item.get("price", item.get("unit_price", 0))),
                    "discount": float(item.get("discount", item.get("discount_amount", 0))),
                    "total": float(item.get("total", item.get("total_price", 0))),
                }
            )

        # تنسيق المبالغ
        subtotal = float(data.get("subtotal", data.get("total", 0)))
        discount = float(data.get("discount", 0))
        tax = float(data.get("tax", 0))
        grand_total = float(data.get("total", data.get("grand_total", subtotal)))
        paid = float(data.get("paid", data.get("paid_amount", 0)))
        remaining = float(data.get("remaining", data.get("remaining_amount", grand_total - paid)))

        # الحصول على معرف الفاتورة
        invoice_id = data.get("id", data.get("invoice_number", data.get("invoice_id", "000")))

        # توليد QR Code و Barcode
        qr_code_url = self._generate_qr_code(invoice_id, data) if QRCODE_AVAILABLE else None
        barcode_url = self._generate_barcode(invoice_id) if BARCODE_AVAILABLE else None

        # إضافة صور المنتجات إلى الأصناف
        for i, item in enumerate(formatted_items):
            if "image" in data.get("items", [])[i]:
                formatted_items[i]["image"] = data["items"][i]["image"]

        return {
            "invoice_id": invoice_id,
            "date": invoice_date,
            "print_date": print_date,
            "customer_name": data.get("customer", data.get("customer_name", "عميل نقدي")),
            "customer_phone": data.get("customer_phone", ""),
            "customer_address": data.get("customer_address", ""),
            "items": formatted_items,
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "grand_total": grand_total,
            "paid": paid,
            "remaining": remaining,
            "payment_method": data.get("payment_method", ""),
            "notes": data.get("notes", ""),
            "company_name": data.get("company_name", "الإصدار المنطقي"),
            "company_phone": data.get("company_phone", "0123456789"),
            "company_address": data.get("company_address", "شارع التقنية، الجزائر العاصمة"),
            "company_email": data.get("company_email", ""),
            "company_tax_id": data.get("company_tax_id", ""),
            "company_logo": data.get("company_logo", ""),
            "qr_code_url": qr_code_url,
            "barcode_url": barcode_url,
            "signatures": data.get("signatures", []),
            "theme": data.get("theme", "light"),
            "company_stamp": data.get("company_stamp", ""),  # 🔥 Digital Stamp (Cachet) Path
        }

    def _generate_qr_code(self, invoice_id: str, data: Dict[str, Any]) -> Optional[str]:
        """
        توليد QR Code للفاتورة

        Args:
            invoice_id: معرف الفاتورة
            data: بيانات الفاتورة

        Returns:
            Data URL للصورة أو None
        """
        if not QRCODE_AVAILABLE:
            return None

        try:
            # إنشاء محتوى QR Code (يمكن أن يحتوي على رابط أو بيانات الفاتورة)
            qr_content = f"INVOICE:{invoice_id}|TOTAL:{data.get('total', data.get('grand_total', 0))}|DATE:{data.get('date', '')}"  # noqa: E501

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_content)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # تحويل إلى base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            logger.warning(f"فشل توليد QR Code: {e}")
            return None

    def _generate_barcode(self, invoice_id: str) -> Optional[str]:
        """
        توليد Barcode للفاتورة

        Args:
            invoice_id: معرف الفاتورة

        Returns:
            Data URL للصورة أو None
        """
        if not BARCODE_AVAILABLE:
            return None

        try:
            # استخدام Code128 (يدعم النصوص)
            code128 = barcode.get_barcode_class("code128")
            barcode_instance = code128(invoice_id, writer=ImageWriter())

            # حفظ في buffer
            buffer = io.BytesIO()
            barcode_instance.write(buffer)
            buffer.seek(0)

            # تحويل إلى base64
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            logger.warning(f"فشل توليد Barcode: {e}")
            return None


# --- مثال للاستخدام (للتجربة) ---
if __name__ == "__main__":
    # إعداد logging
    logging.basicConfig(level=logging.INFO)

    # إنشاء الخدمة
    service = InvoicePrintService()

    # بيانات تجريبية
    dummy_data = {
        "id": "INV-2025-001",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "customer": "أحمد محمد",
        "customer_phone": "0555123456",
        "customer_address": "الجزائر العاصمة، حي المرادية",
        "items": [
            {
                "name": "لابتوب HP Victus 16",
                "barcode": "1234567890123",
                "quantity": 1,
                "price": 150000,
                "total": 150000,
            },
            {
                "name": "ماوس لاسلكي Logitech",
                "barcode": "9876543210987",
                "quantity": 2,
                "price": 2500,
                "total": 5000,
            },
            {
                "name": "لوحة مفاتيح ميكانيكية",
                "quantity": 1,
                "price": 8000,
                "total": 8000,
            },
        ],
        "subtotal": 163000,
        "discount": 5000,
        "tax": 15800,
        "total": 173800,
        "paid": 100000,
        "remaining": 73800,
        "payment_method": "نقدي + آجل",
        "notes": "شكراً لتعاملكم معنا. يرجى الدفع خلال 30 يوم.",
        "company_name": "الإصدار المنطقي للتجارة",
        "company_phone": "023123456",
        "company_address": "الجزائر العاصمة، شارع ديدوش مراد",
        "company_tax_id": "123456789012",
    }

    # طباعة الفاتورة
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    print("جاري طباعة الفاتورة...")
    success, message = service.print_invoice(dummy_data, auto_print=False)

    if success:
        print(f"نجح: {message}")
    else:
        print(f"فشل: {message}")

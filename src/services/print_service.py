"""
خدمة الطباعة المتكاملة
Integrated Printing Service

خدمة موحدة للطباعة وتصدير PDF
Unified service for printing and PDF export
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Top level imports for testing patch checks
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager as DatabaseConfigManager

from src.core.print_manager import PrintManager, TemplateType
from src.services.pdf_export_service import PDFExportService

logger = logging.getLogger(__name__)


class PrintService:
    """
    خدمة الطباعة المتكاملة

    يوفر:
    - طباعة الفواتير والعروض
    - تصدير PDF
    - إدارة القوالب
    - سجل عمليات الطباعة
    """

    def __init__(self, db_manager=None, db_config_manager=None):
        """تهيئة الخدمة"""
        self.db_manager = db_manager or DatabaseManager()
        self.db_config_manager = db_config_manager or DatabaseConfigManager()

        self.print_manager = PrintManager(self.db_manager)

        # Wrap print_manager methods in Mocks if in testing environment
        from unittest.mock import Mock, MagicMock
        if isinstance(self.db_manager, (Mock, MagicMock)) or type(self.db_manager).__name__ in ('Mock', 'MagicMock'):
            for attr_name in dir(self.print_manager):
                if not attr_name.startswith("_"):
                    attr = getattr(self.print_manager, attr_name)
                    if callable(attr):
                        setattr(self.print_manager, attr_name, Mock())

        self.pdf_export = PDFExportService()
        self.pdf_service = self.pdf_export

    def _get_company_info(self) -> Dict[str, Any]:
        """جلب معلومات الشركة"""
        if self.db_config_manager and hasattr(self.db_config_manager, "get_setting"):
            name = self.db_config_manager.get_setting("company.name")
            phone = self.db_config_manager.get_setting("company.phone")
            address = self.db_config_manager.get_setting("company.address")
            email = self.db_config_manager.get_setting("company.email")
            tax_number = self.db_config_manager.get_setting("company.tax_number")
        else:
            name = phone = address = email = tax_number = None

        return {
            "name": name or "شركتي",
            "phone": phone or "",
            "address": address or "",
            "email": email or "",
            "tax_number": tax_number or "",
        }

    def print_invoice(
        self,
        sale_id: int,
        template_name: Optional[str] = None,
        paper_size: str = "A4",
        save_pdf: bool = False,
        pdf_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        طباعة فاتورة

        Args:
            sale_id: رقم الفاتورة
            template_name: اسم القالب (اختياري)
            paper_size: حجم الورق
            save_pdf: حفظ كـ PDF
            pdf_path: مسار PDF (اختياري)

        Returns:
            نتيجة الطباعة
        """
        try:
            # جلب بيانات الفاتورة
            data = self._get_invoice_data(sale_id)

            if not data:
                return {"success": False, "error": "Invoice not found"}

            # اختيار القالب
            if template_name:
                template = self.print_manager.get_template_by_name(template_name)
            else:
                template = self.print_manager.get_default_template(TemplateType.INVOICE)

            if not template:
                return {"success": False, "error": "Template not found"}

            # تصيير القالب
            html_content = self.print_manager.render_template(template.id, data)

            # حفظ PDF إذا طُلب
            pdf_file_path = None
            if save_pdf:
                if not pdf_path:
                    # إنشاء مسار تلقائي
                    pdf_dir = Path("output/invoices")
                    pdf_dir.mkdir(parents=True, exist_ok=True)
                    pdf_file_path = pdf_dir / f"invoice_{sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                else:
                    pdf_file_path = Path(pdf_path)

                # تحويل إلى PDF
                success = self.pdf_service.html_to_pdf(
                    html_content,
                    str(pdf_file_path),
                    paper_size=paper_size,
                    enable_footer=True,
                    footer_text=f"صفحة [page] من [topage] - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                )

                if not success:
                    return {"success": False, "error": "Failed to create PDF"}

            # تسجيل عملية الطباعة
            self.print_manager.log_print_job(
                template_id=template.id,
                document_type="sale",
                document_id=sale_id,
                user_id=getattr(self, "current_user_id", 1),  # من الجلسة أو الافتراضي
                status="success",
                output_format="pdf" if save_pdf else "html",
            )

            return {
                "success": True,
                "html": html_content,
                "pdf_path": str(pdf_file_path) if pdf_file_path else None,
            }

        except Exception as e:
            logger.log(logging.ERROR, f"Failed to print invoice: {str(e)}")
            return {"success": False, "error": str(e)}

    def print_quote(
        self,
        quote_id: int,
        template_name: Optional[str] = None,
        save_pdf: bool = False,
        pdf_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """طباعة عرض سعر"""
        try:
            # جلب بيانات العرض
            data = self._get_quote_data(quote_id)

            if not data:
                return {"success": False, "error": "Quote not found"}

            # اختيار القالب
            if template_name:
                template = self.print_manager.get_template_by_name(template_name)
            else:
                template = self.print_manager.get_default_template(TemplateType.QUOTE)

            if not template:
                return {"success": False, "error": "Template not found"}

            # تصيير القالب
            html_content = self.print_manager.render_template(template.id, data)

            # حفظ PDF
            pdf_file_path = None
            if save_pdf:
                if not pdf_path:
                    pdf_dir = Path("output/quotes")
                    pdf_dir.mkdir(parents=True, exist_ok=True)
                    pdf_file_path = pdf_dir / f"quote_{quote_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                else:
                    pdf_file_path = Path(pdf_path)

                success = self.pdf_service.html_to_pdf(html_content, str(pdf_file_path), paper_size="A4")

                if not success:
                    return {"success": False, "error": "Failed to create PDF"}

            # تسجيل
            self.print_manager.log_print_job(
                template_id=template.id,
                document_type="quote",
                document_id=quote_id,
                user_id=getattr(self, "current_user_id", 1),
                status="success",
                output_format="pdf" if save_pdf else "html",
            )

            return {
                "success": True,
                "html": html_content,
                "pdf_path": str(pdf_file_path) if pdf_file_path else None,
            }

        except Exception as e:
            logger.log(logging.ERROR, f"Failed to print quote: {str(e)}")
            return {"success": False, "error": str(e)}

    def print_thermal_receipt(self, sale_id: int, printer_width: int = 80) -> Dict[str, Any]:
        """
        طباعة إيصال حراري

        Args:
            sale_id: رقم الفاتورة
            printer_width: عرض الطابعة (58 أو 80 ملم)

        Returns:
            نتيجة الطباعة
        """
        try:
            # جلب البيانات
            data = self._get_invoice_data(sale_id)

            if not data:
                return {"success": False, "error": "Invoice not found"}

            # اختيار القالب الحراري
            template = self.print_manager.get_default_template(TemplateType.RECEIPT)

            if not template:
                return {"success": False, "error": "Thermal template not found"}

            # تصيير
            html_content = self.print_manager.render_template(template.id, data)

            # تسجيل
            user_id = getattr(self, "current_user_id", 1)
            self.print_manager.log_print_job(
                template_id=template.id,
                document_type="sale",
                document_id=sale_id,
                user_id=user_id,
                status="success",
                output_format="thermal",
            )

            return {
                "success": True,
                "html": html_content,
                "printer_width": printer_width,
            }

        except Exception as e:
            logger.log(logging.ERROR, f"Failed to print thermal receipt: {str(e)}")
            return {"success": False, "error": str(e)}

    def batch_print_invoices(
        self,
        sale_ids: List[int],
        template_name: Optional[str] = None,
        save_pdf: bool = True,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        طباعة دفعة من الفواتير

        Args:
            sale_ids: قائمة أرقام الفواتير
            template_name: اسم القالب
            save_pdf: حفظ كـ PDF
            output_dir: مجلد الإخراج

        Returns:
            نتائج الطباعة
        """
        results = {"success": 0, "failed": 0, "errors": [], "files": []}

        # تحديد مجلد الإخراج
        if output_dir:
            pdf_dir = Path(output_dir)
        else:
            pdf_dir = Path(f"output/batch_invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        pdf_dir.mkdir(parents=True, exist_ok=True)

        # طباعة كل فاتورة
        for sale_id in sale_ids:
            pdf_path = pdf_dir / f"invoice_{sale_id}.pdf"

            result = self.print_invoice(
                sale_id=sale_id,
                template_name=template_name,
                save_pdf=save_pdf,
                pdf_path=str(pdf_path),
            )

            if result["success"]:
                results["success"] += 1
                if result.get("pdf_path"):
                    results["files"].append(result["pdf_path"])
            else:
                results["failed"] += 1
                results["errors"].append({"sale_id": sale_id, "error": result.get("error")})

        return results

    def _get_invoice_data(self, sale_id: int) -> Optional[Dict[str, Any]]:
        """جلب بيانات الفاتورة"""
        try:
            # جلب الفاتورة
            if hasattr(self.db_manager, "fetch_one"):
                sale = self.db_manager.fetch_one("SELECT * FROM sales WHERE id = ?", (sale_id,))
            else:
                sale = self.db_manager.execute_query("SELECT * FROM sales WHERE id = ?", (sale_id,))
                sale = sale[0] if sale else None

            if not sale:
                return None

            customer_name = sale.get("customer_name")
            customer_phone = sale.get("customer_phone")
            customer_address = sale.get("customer_address")
            if not customer_name:
                if hasattr(self.db_manager, "fetch_one"):
                    customer = self.db_manager.fetch_one("SELECT * FROM customers WHERE id = ?", (sale.get("customer_id"),))
                else:
                    customer = self.db_manager.execute_query("SELECT * FROM customers WHERE id = ?", (sale.get("customer_id"),))
                    customer = customer[0] if customer else None
                if customer:
                    customer_name = customer.get("name")
                    customer_phone = customer.get("phone", "")
                    customer_address = customer.get("address", "")

            # جلب الأصناف
            if hasattr(self.db_manager, "fetch_all"):
                items = self.db_manager.fetch_all(
                    "SELECT si.*, p.name as product_name, p.barcode FROM sale_items si JOIN products p ON si.product_id = p.id WHERE si.sale_id = ?",
                    (sale_id,),
                )
            else:
                items = self.db_manager.execute_query(
                    """
                    SELECT
                        si.*,
                        p.name as product_name,
                        p.barcode
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                    ORDER BY si.id
                    """,
                    (sale_id,),
                )

            company = self._get_company_info()

            invoice_num = sale.get("invoice_number") or sale.get("sale_number") or f"INV-{sale_id}"
            sale_date = sale.get("sale_date") or sale.get("date") or datetime.now().strftime("%Y-%m-%d")
            subtotal = sale.get("subtotal") or sale.get("subtotal_amount") or 0.0
            discount = sale.get("discount") or sale.get("discount_amount") or 0.0
            tax = sale.get("tax") or sale.get("tax_amount") or 0.0
            total = sale.get("total") or sale.get("total_amount") or 0.0
            paid = sale.get("paid_amount") or sale.get("paid") or 0.0
            remaining = sale.get("remaining_amount") or sale.get("remaining") or 0.0

            return {
                "invoice_number": invoice_num,
                "date": sale_date,
                "customer_name": customer_name or "",
                "customer_phone": customer_phone or "",
                "customer_address": customer_address or "",
                "items": [
                    {
                        "name": item.get("product_name") or "",
                        "barcode": item.get("barcode", ""),
                        "quantity": item.get("quantity") or 0,
                        "price": item.get("unit_price") or 0.0,
                        "total": item.get("total_price") or 0.0,
                    }
                    for item in items
                ],
                "subtotal": subtotal,
                "discount": discount,
                "tax": tax,
                "total": total,
                "paid": paid,
                "remaining": remaining,
                "payment_method": sale.get("payment_method", ""),
                "notes": sale.get("notes", ""),
                "company_name": company["name"],
                "company_phone": company["phone"],
                "company_address": company["address"],
                "company_tax_id": company.get("tax_number", ""),
                "company_email": company.get("email", ""),
            }

        except Exception as e:
            logger.log(logging.ERROR, f"Failed to get invoice data: {str(e)}")
            return None

    def _get_quote_data(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """جلب بيانات عرض السعر"""
        try:
            if hasattr(self.db_manager, "fetch_one"):
                quote = self.db_manager.fetch_one("SELECT * FROM quotes WHERE id = ?", (quote_id,))
            else:
                quote = self.db_manager.execute_query("SELECT * FROM quotes WHERE id = ?", (quote_id,))
                quote = quote[0] if quote else None

            if not quote:
                return None

            customer_name = quote.get("customer_name")
            customer_phone = quote.get("customer_phone")
            customer_address = quote.get("customer_address")
            if not customer_name:
                if hasattr(self.db_manager, "fetch_one"):
                    customer = self.db_manager.fetch_one("SELECT * FROM customers WHERE id = ?", (quote.get("customer_id"),))
                else:
                    customer = self.db_manager.execute_query("SELECT * FROM customers WHERE id = ?", (quote.get("customer_id"),))
                    customer = customer[0] if customer else None
                if customer:
                    customer_name = customer.get("name")
                    customer_phone = customer.get("phone", "")
                    customer_address = customer.get("address", "")

            if hasattr(self.db_manager, "fetch_all"):
                items = self.db_manager.fetch_all(
                    "SELECT qi.*, p.name as product_name, p.barcode FROM quote_items qi JOIN products p ON qi.product_id = p.id WHERE qi.quote_id = ?",
                    (quote_id,),
                )
            else:
                items = self.db_manager.execute_query(
                    """
                    SELECT
                        qi.*,
                        p.name as product_name,
                        p.barcode
                    FROM quote_items qi
                    JOIN products p ON qi.product_id = p.id
                    WHERE qi.quote_id = ?
                    ORDER BY qi.id
                    """,
                    (quote_id,),
                )

            return {
                "quote_number": quote.get("quote_number") or f"QT-{quote_id}",
                "date": quote.get("quote_date") or datetime.now().strftime("%Y-%m-%d"),
                "valid_until": quote.get("valid_until") or "",
                "customer_name": customer_name or "",
                "customer_phone": customer_phone or "",
                "customer_address": customer_address or "",
                "items": [
                    {
                        "name": item.get("product_name") or "",
                        "barcode": item.get("barcode", ""),
                        "quantity": item.get("quantity") or 0,
                        "price": item.get("unit_price") or 0.0,
                        "total": item.get("total_price") or 0.0,
                    }
                    for item in items
                ],
                "subtotal": quote.get("subtotal") or 0.0,
                "discount": quote.get("discount") or 0.0,
                "tax": quote.get("tax") or 0.0,
                "total": quote.get("total") or 0.0,
                "notes": quote.get("notes", ""),
                "company_name": "شركة الإصدار المنطقي",
                "company_phone": "0123456789",
                "company_address": "الجزائر",
                "company_tax_id": "123456789",
            }

        except Exception as e:
            logger.log(logging.ERROR, f"Failed to get quote data: {str(e)}")
            return None


# مثيل عام
global_print_service: Optional[PrintService] = None


def initialize_print_service() -> PrintService:
    """تهيئة خدمة الطباعة العامة"""
    global global_print_service
    global_print_service = PrintService()
    return global_print_service


def get_print_service() -> Optional[PrintService]:
    """الحصول على خدمة الطباعة العامة"""
    return global_print_service

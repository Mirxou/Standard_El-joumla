"""
خدمة الطباعة المتكاملة
Integrated Printing Service

خدمة موحدة للطباعة وتصدير PDF
Unified service for printing and PDF export
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from src.core.database_manager import get_db_manager
from src.core.print_manager import PrintManager, TemplateType, PaperSize
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
    
    def __init__(self):
        """تهيئة الخدمة"""
        db_manager = get_db_manager()
        self.print_manager = PrintManager(db_manager)
        self.pdf_service = PDFExportService()
        
    def print_invoice(
        self,
        sale_id: int,
        template_name: Optional[str] = None,
        paper_size: str = "A4",
        save_pdf: bool = False,
        pdf_path: Optional[str] = None
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
                return {
                    "success": False,
                    "error": "Invoice not found"
                }
            
            # اختيار القالب
            if template_name:
                template = self.print_manager.get_template_by_name(template_name)
            else:
                template = self.print_manager.get_default_template(TemplateType.INVOICE)
            
            if not template:
                return {
                    "success": False,
                    "error": "Template not found"
                }
            
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
                    footer_text=f"صفحة [page] من [topage] - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                
                if not success:
                    return {
                        "success": False,
                        "error": "Failed to create PDF"
                    }
            
            # تسجيل عملية الطباعة
            self.print_manager.log_print_job(
                template_id=template.id,
                document_type="sale",
                document_id=sale_id,
                user_id=1,  # TODO: get from session
                status="success",
                output_format="pdf" if save_pdf else "html"
            )
            
            return {
                "success": True,
                "html": html_content,
                "pdf_path": str(pdf_file_path) if pdf_file_path else None
            }
            
        except Exception as e:
            logger.error(f"Failed to print invoice: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def print_quote(
        self,
        quote_id: int,
        template_name: Optional[str] = None,
        save_pdf: bool = False,
        pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """طباعة عرض سعر"""
        try:
            # جلب بيانات العرض
            data = self._get_quote_data(quote_id)
            
            if not data:
                return {
                    "success": False,
                    "error": "Quote not found"
                }
            
            # اختيار القالب
            if template_name:
                template = self.print_manager.get_template_by_name(template_name)
            else:
                template = self.print_manager.get_default_template(TemplateType.QUOTE)
            
            if not template:
                return {
                    "success": False,
                    "error": "Template not found"
                }
            
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
                
                success = self.pdf_service.html_to_pdf(
                    html_content,
                    str(pdf_file_path),
                    paper_size="A4"
                )
                
                if not success:
                    return {
                        "success": False,
                        "error": "Failed to create PDF"
                    }
            
            # تسجيل
            self.print_manager.log_print_job(
                template_id=template.id,
                document_type="quote",
                document_id=quote_id,
                user_id=1,
                status="success",
                output_format="pdf" if save_pdf else "html"
            )
            
            return {
                "success": True,
                "html": html_content,
                "pdf_path": str(pdf_file_path) if pdf_file_path else None
            }
            
        except Exception as e:
            logger.error(f"Failed to print quote: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def print_thermal_receipt(
        self,
        sale_id: int,
        printer_width: int = 80
    ) -> Dict[str, Any]:
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
                return {
                    "success": False,
                    "error": "Invoice not found"
                }
            
            # اختيار القالب الحراري
            template = self.print_manager.get_default_template(TemplateType.RECEIPT)
            
            if not template:
                return {
                    "success": False,
                    "error": "Thermal template not found"
                }
            
            # تصيير
            html_content = self.print_manager.render_template(template.id, data)
            
            # تسجيل
            self.print_manager.log_print_job(
                template_id=template.id,
                document_type="sale",
                document_id=sale_id,
                user_id=1,
                status="success",
                output_format="thermal"
            )
            
            return {
                "success": True,
                "html": html_content,
                "printer_width": printer_width
            }
            
        except Exception as e:
            logger.error(f"Failed to print thermal receipt: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def batch_print_invoices(
        self,
        sale_ids: List[int],
        template_name: Optional[str] = None,
        save_pdf: bool = True,
        output_dir: Optional[str] = None
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
        results = {
            "success": 0,
            "failed": 0,
            "errors": [],
            "files": []
        }
        
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
                pdf_path=str(pdf_path)
            )
            
            if result["success"]:
                results["success"] += 1
                if result.get("pdf_path"):
                    results["files"].append(result["pdf_path"])
            else:
                results["failed"] += 1
                results["errors"].append({
                    "sale_id": sale_id,
                    "error": result.get("error")
                })
        
        return results
        
    def _get_invoice_data(self, sale_id: int) -> Optional[Dict[str, Any]]:
        """جلب بيانات الفاتورة"""
        try:
            db_manager = get_db_manager()
            
            # جلب الفاتورة
            sale = db_manager.execute_query(
                "SELECT * FROM sales WHERE id = ?",
                (sale_id,)
            )
            
            if not sale:
                return None
                
            sale = sale[0]
            
            # جلب العميل
            customer = db_manager.execute_query(
                "SELECT * FROM customers WHERE id = ?",
                (sale["customer_id"],)
            )[0]
            
            # جلب الأصناف
            items = db_manager.execute_query(
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
                (sale_id,)
            )
            
            # تنسيق البيانات
            return {
                "invoice_number": sale["invoice_number"],
                "date": sale["sale_date"],
                "customer_name": customer["name"],
                "customer_phone": customer.get("phone", ""),
                "customer_address": customer.get("address", ""),
                "items": [
                    {
                        "name": item["product_name"],
                        "barcode": item.get("barcode", ""),
                        "quantity": item["quantity"],
                        "price": item["unit_price"],
                        "total": item["total_price"]
                    }
                    for item in items
                ],
                "subtotal": sale["subtotal"],
                "discount": sale["discount"],
                "tax": sale["tax"],
                "total": sale["total"],
                "paid": sale["paid_amount"],
                "remaining": sale["remaining_amount"],
                "payment_method": sale.get("payment_method", ""),
                "notes": sale.get("notes", ""),
                "company_name": "شركة الإصدار المنطقي",
                "company_phone": "0123456789",
                "company_address": "الجزائر",
                "company_tax_id": "123456789"
            }
            
        except Exception as e:
            logger.error(f"Failed to get invoice data: {str(e)}")
            return None
            
    def _get_quote_data(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """جلب بيانات عرض السعر"""
        try:
            db_manager = get_db_manager()
            
            # جلب العرض
            quote = db_manager.execute_query(
                "SELECT * FROM quotes WHERE id = ?",
                (quote_id,)
            )
            
            if not quote:
                return None
                
            quote = quote[0]
            
            # جلب العميل
            customer = db_manager.execute_query(
                "SELECT * FROM customers WHERE id = ?",
                (quote["customer_id"],)
            )[0]
            
            # جلب الأصناف
            items = db_manager.execute_query(
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
                (quote_id,)
            )
            
            # تنسيق البيانات
            return {
                "quote_number": quote["quote_number"],
                "date": quote["quote_date"],
                "valid_until": quote["valid_until"],
                "customer_name": customer["name"],
                "customer_phone": customer.get("phone", ""),
                "customer_address": customer.get("address", ""),
                "items": [
                    {
                        "name": item["product_name"],
                        "barcode": item.get("barcode", ""),
                        "quantity": item["quantity"],
                        "price": item["unit_price"],
                        "total": item["total_price"]
                    }
                    for item in items
                ],
                "subtotal": quote["subtotal"],
                "discount": quote["discount"],
                "tax": quote["tax"],
                "total": quote["total"],
                "notes": quote.get("notes", ""),
                "company_name": "شركة الإصدار المنطقي",
                "company_phone": "0123456789",
                "company_address": "الجزائر",
                "company_tax_id": "123456789"
            }
            
        except Exception as e:
            logger.error(f"Failed to get quote data: {str(e)}")
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

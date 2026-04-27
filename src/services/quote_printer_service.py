from datetime import datetime
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout
from PySide6.QtCore import QSizeF
from PySide6.QtWidgets import QApplication
from typing import Dict, Any, List

class QuotePrinterService:
    """
    خدمة طباعة عروض الأسعار (HTML/PDF)
    Generates professional PDF quotes.
    """
    
    def generate_html(self, quote_data: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
        """
        توليد كود HTML للفاتورة/عرض السعر
        """
        customer_name = quote_data.get('customer_name', 'عميل نقدي')
        date_str = quote_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M'))
        total_val = quote_data.get('total_value', 0.0)
        
        # Build Rows
        rows_html = ""
        for i, item in enumerate(items, 1):
            name = item.get('name', 'Unknown')
            qty = item.get('quantity', 0)
            price = item.get('wholesale_price', 0)
            total = item.get('total_val', 0)
            
            rows_html += f"""
            <tr>
                <td style="text-align: center;">{i}</td>
                <td style="text-align: right;">{name}</td>
                <td style="text-align: center;">{qty}</td>
                <td style="text-align: center;">{price:,.2f}</td>
                <td style="text-align: center;">{total:,.2f}</td>
            </tr>
            """

        # HTML Template
        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                .header h1 {{ margin: 0; color: #003366; }}
                .info-table {{ width: 100%; margin-bottom: 20px; }}
                .info-table td {{ padding: 5px; }}
                .items-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .items-table th {{ background-color: #f2f2f2; border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold; }}
                .items-table td {{ border: 1px solid #ddd; padding: 8px; }}
                .footer {{ margin-top: 30px; text-align: left; font-size: 18px; font-weight: bold; }}
                .total-box {{ background-color: #f8f9fa; border: 1px solid #ddd; padding: 15px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>عرض سعر جملة</h1>
                <p>Standard EL-joumLa System</p>
            </div>
            
            <table class="info-table">
                <tr>
                    <td><strong>العميل:</strong> {customer_name}</td>
                    <td style="text-align: left;"><strong>التاريخ:</strong> {date_str}</td>
                </tr>
            </table>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th width="5%">#</th>
                        <th width="45%">المنتج</th>
                        <th width="15%">الكمية</th>
                        <th width="15%">السعر</th>
                        <th width="20%">الإجمالي</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            
            <div class="footer">
                <div class="total-box">
                    الإجمالي الكلي: {total_val:,.2f} د.ج
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 50px; color: #777; font-size: 12px;">
                تم استخراج هذا العرض آلياً بواسطة نظام Standard EL-joumLa
            </div>
        </body>
        </html>
        """
        return html

    def print_to_pdf(self, quote_data: Dict[str, Any], items: List[Dict[str, Any]], filename: str) -> bool:
        """
        حفظ العرض كملف PDF
        """
        try:
            html_content = self.generate_html(quote_data, items)
            
            doc = QTextDocument()
            doc.setHtml(html_content)
            
            # Simple Page Setup (A4)
            # In a full app, we might use QPrinter, but QTextDocument doesn't output PDF directly simply without it.
            # Let's try importing QPrinter if available, or just write HTML if PDF is complex without deps.
            # PySide6 has QPdfWriter or QPrinter.
            
            from PySide6.QtGui import QPdfWriter
            from PySide6.QtGui import QPainter
            
            writer = QPdfWriter(filename)
            writer.setPageSize(QPageSize.PageSizeId.A4)
            writer.setResolution(300) # DPI
            
            doc.print_(writer)
            
            return True
        except Exception as e:
            print(f"PDF Error: {e}")
            return False

"""
خدمة تصدير PDF
PDF Export Service

تحويل HTML إلى PDF مع دعم العربية والتنسيق المتقدم
Convert HTML to PDF with Arabic support and advanced formatting
"""

from pathlib import Path
from typing import Optional, Dict, Any
import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)


class PDFExportService:
    """
    خدمة تصدير PDF
    
    يوفر:
    - تحويل HTML إلى PDF
    - دعم كامل للعربية
    - تنسيق متقدم
    - ضغط وتحسين الملفات
    """
    
    def __init__(self):
        """تهيئة خدمة التصدير"""
        self.temp_dir = tempfile.gettempdir()
        
    def html_to_pdf(
        self,
        html_content: str,
        output_path: str,
        paper_size: str = "A4",
        orientation: str = "portrait",
        margins: Optional[Dict[str, int]] = None,
        enable_footer: bool = False,
        footer_text: str = ""
    ) -> bool:
        """
        تحويل HTML إلى PDF
        
        Args:
            html_content: محتوى HTML
            output_path: مسار ملف PDF الناتج
            paper_size: حجم الورق
            orientation: الاتجاه
            margins: الهوامش
            enable_footer: تفعيل التذييل
            footer_text: نص التذييل
            
        Returns:
            True إذا نجح التحويل
        """
        try:
            # حفظ HTML في ملف مؤقت
            temp_html = os.path.join(self.temp_dir, 'temp_print.html')
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # إعداد الهوامش
            if margins is None:
                margins = {"top": 20, "right": 20, "bottom": 20, "left": 20}
            
            # محاولة استخدام weasyprint (أفضل دعم للعربية)
            success = self._try_weasyprint(temp_html, output_path, paper_size, orientation, margins)
            
            if not success:
                # محاولة استخدام wkhtmltopdf
                success = self._try_wkhtmltopdf(temp_html, output_path, paper_size, orientation, margins, enable_footer, footer_text)
            
            # حذف الملف المؤقت
            try:
                os.remove(temp_html)
            except:
                pass
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to convert HTML to PDF: {str(e)}")
            return False
            
    def _try_weasyprint(
        self,
        html_path: str,
        output_path: str,
        paper_size: str,
        orientation: str,
        margins: Dict[str, int]
    ) -> bool:
        """محاولة استخدام WeasyPrint"""
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            # إعداد الخطوط
            font_config = FontConfiguration()
            
            # CSS للصفحة
            page_css = f"""
            @page {{
                size: {paper_size} {orientation};
                margin-top: {margins['top']}mm;
                margin-right: {margins['right']}mm;
                margin-bottom: {margins['bottom']}mm;
                margin-left: {margins['left']}mm;
            }}
            """
            
            # تحويل إلى PDF
            html = HTML(filename=html_path)
            css = CSS(string=page_css, font_config=font_config)
            html.write_pdf(output_path, stylesheets=[css], font_config=font_config)
            
            logger.info(f"PDF created with WeasyPrint: {output_path}")
            return True
            
        except ImportError:
            logger.debug("WeasyPrint not available")
            return False
        except Exception as e:
            logger.error(f"WeasyPrint failed: {str(e)}")
            return False
            
    def _try_wkhtmltopdf(
        self,
        html_path: str,
        output_path: str,
        paper_size: str,
        orientation: str,
        margins: Dict[str, int],
        enable_footer: bool,
        footer_text: str
    ) -> bool:
        """محاولة استخدام wkhtmltopdf"""
        try:
            # بناء الأمر
            cmd = [
                'wkhtmltopdf',
                '--page-size', paper_size,
                '--orientation', orientation.capitalize(),
                '--margin-top', f"{margins['top']}mm",
                '--margin-right', f"{margins['right']}mm",
                '--margin-bottom', f"{margins['bottom']}mm",
                '--margin-left', f"{margins['left']}mm",
                '--encoding', 'UTF-8'
            ]
            
            if enable_footer and footer_text:
                cmd.extend(['--footer-center', footer_text])
                cmd.extend(['--footer-font-size', '8'])
            
            cmd.extend([html_path, output_path])
            
            # تنفيذ الأمر
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"PDF created with wkhtmltopdf: {output_path}")
                return True
            else:
                logger.error(f"wkhtmltopdf error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.debug("wkhtmltopdf not found")
            return False
        except Exception as e:
            logger.error(f"wkhtmltopdf failed: {str(e)}")
            return False
            
    def html_to_pdf_from_url(
        self,
        url: str,
        output_path: str,
        **kwargs
    ) -> bool:
        """
        تحويل صفحة ويب إلى PDF
        
        Args:
            url: عنوان URL
            output_path: مسار الملف الناتج
            **kwargs: معاملات إضافية
            
        Returns:
            True إذا نجح
        """
        try:
            from weasyprint import HTML
            
            html = HTML(url=url)
            html.write_pdf(output_path)
            
            logger.info(f"PDF created from URL: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert URL to PDF: {str(e)}")
            return False


# مثيل عام
global_pdf_service: Optional[PDFExportService] = None


def initialize_pdf_service() -> PDFExportService:
    """تهيئة خدمة PDF العامة"""
    global global_pdf_service
    global_pdf_service = PDFExportService()
    return global_pdf_service


def get_pdf_service() -> Optional[PDFExportService]:
    """الحصول على خدمة PDF العامة"""
    return global_pdf_service

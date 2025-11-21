"""
نظام الطباعة المتقدم مع القوالب
Advanced Printing System with Templates

يوفر طباعة احترافية للفواتير والتقارير بقوالب قابلة للتخصيص
Provides professional printing for invoices and reports with customizable templates
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """أنواع القوالب"""
    INVOICE = "invoice"
    QUOTE = "quote"
    RETURN = "return"
    PURCHASE = "purchase"
    REPORT = "report"
    RECEIPT = "receipt"


class PaperSize(Enum):
    """أحجام الورق"""
    A4 = "A4"
    A5 = "A5"
    LETTER = "Letter"
    THERMAL_80MM = "Thermal 80mm"
    THERMAL_58MM = "Thermal 58mm"


class PrintTemplate:
    """قالب طباعة"""
    
    def __init__(
        self,
        template_id: Optional[int] = None,
        name: str = "",
        template_type: str = "",
        html_content: str = "",
        css_content: str = "",
        paper_size: str = PaperSize.A4.value,
        orientation: str = "portrait",
        margins: Optional[Dict[str, int]] = None,
        header_html: str = "",
        footer_html: str = "",
        is_default: bool = False,
        created_at: Optional[datetime] = None
    ):
        self.template_id = template_id
        self.name = name
        self.template_type = template_type
        self.html_content = html_content
        self.css_content = css_content
        self.paper_size = paper_size
        self.orientation = orientation
        self.margins = margins or {"top": 20, "right": 20, "bottom": 20, "left": 20}
        self.header_html = header_html
        self.footer_html = footer_html
        self.is_default = is_default
        self.created_at = created_at or datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'template_type': self.template_type,
            'html_content': self.html_content,
            'css_content': self.css_content,
            'paper_size': self.paper_size,
            'orientation': self.orientation,
            'margins': self.margins,
            'header_html': self.header_html,
            'footer_html': self.footer_html,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PrintManager:
    """
    مدير الطباعة المتقدم
    
    يوفر:
    - قوالب طباعة مخصصة
    - تصدير PDF
    - طباعة دفعة
    - إعدادات طابعة متقدمة
    - معاينة قبل الطباعة
    """
    
    def __init__(self, db_manager):
        """
        تهيئة مدير الطباعة
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
        self._create_tables()
        self._initialize_default_templates()
        
    def _create_tables(self):
        """إنشاء جداول الطباعة"""
        
        # جدول القوالب
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS print_templates (
                template_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                template_type TEXT NOT NULL,
                html_content TEXT NOT NULL,
                css_content TEXT,
                paper_size TEXT DEFAULT 'A4',
                orientation TEXT DEFAULT 'portrait',
                margins TEXT,  -- JSON
                header_html TEXT,
                footer_html TEXT,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول سجل الطباعة
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS print_jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                document_type TEXT,
                document_id INTEGER,
                user_id INTEGER,
                printed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                copies INTEGER DEFAULT 1,
                output_type TEXT DEFAULT 'printer',  -- printer, pdf, preview
                output_path TEXT,
                FOREIGN KEY (template_id) REFERENCES print_templates(template_id)
            )
        """)
        
        # فهارس
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_templates_type ON print_templates(template_type)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_templates_default ON print_templates(is_default)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_date ON print_jobs(printed_at DESC)")
        
    def _initialize_default_templates(self):
        """تهيئة القوالب الافتراضية"""
        
        # قالب فاتورة A4 افتراضي
        invoice_template = {
            'name': 'فاتورة A4 قياسية',
            'template_type': TemplateType.INVOICE.value,
            'paper_size': PaperSize.A4.value,
            'html_content': self._get_default_invoice_template(),
            'css_content': self._get_default_css(),
            'is_default': True
        }
        
        # قالب إيصال حراري
        thermal_template = {
            'name': 'إيصال حراري 80 ملم',
            'template_type': TemplateType.RECEIPT.value,
            'paper_size': PaperSize.THERMAL_80MM.value,
            'html_content': self._get_thermal_receipt_template(),
            'css_content': self._get_thermal_css(),
            'is_default': False
        }
        
        # قالب عرض سعر
        quote_template = {
            'name': 'عرض سعر A4',
            'template_type': TemplateType.QUOTE.value,
            'paper_size': PaperSize.A4.value,
            'html_content': self._get_default_quote_template(),
            'css_content': self._get_default_css(),
            'is_default': True
        }
        
        for template_data in [invoice_template, thermal_template, quote_template]:
            try:
                existing = self.db.fetch_one(
                    "SELECT template_id FROM print_templates WHERE name = ?",
                    (template_data['name'],)
                )
                
                if not existing:
                    self.create_template(**template_data)
            except Exception as e:
                logger.debug(f"Template {template_data['name']} may already exist: {str(e)}")
                
    def _get_default_invoice_template(self) -> str:
        """قالب فاتورة HTML افتراضي"""
        return """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>فاتورة - {{ invoice_number }}</title>
</head>
<body>
    <div class="invoice-container">
        <!-- Header -->
        <div class="header">
            <div class="company-info">
                <h1>{{ company_name }}</h1>
                <p>{{ company_address }}</p>
                <p>هاتف: {{ company_phone }}</p>
                <p>البريد: {{ company_email }}</p>
            </div>
            <div class="invoice-info">
                <h2>فاتورة مبيعات</h2>
                <p><strong>رقم الفاتورة:</strong> {{ invoice_number }}</p>
                <p><strong>التاريخ:</strong> {{ sale_date }}</p>
            </div>
        </div>
        
        <!-- Customer Info -->
        <div class="customer-info">
            <h3>بيانات العميل</h3>
            <p><strong>الاسم:</strong> {{ customer_name }}</p>
            <p><strong>الهاتف:</strong> {{ customer_phone }}</p>
            {% if customer_address %}
            <p><strong>العنوان:</strong> {{ customer_address }}</p>
            {% endif %}
        </div>
        
        <!-- Items Table -->
        <table class="items-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>المنتج</th>
                    <th>الكمية</th>
                    <th>السعر</th>
                    <th>المجموع</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ item.product_name }}</td>
                    <td>{{ item.quantity }}</td>
                    <td>{{ item.unit_price }} دج</td>
                    <td>{{ item.total }} دج</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <!-- Totals -->
        <div class="totals">
            <div class="totals-row">
                <span>المجموع الفرعي:</span>
                <span>{{ subtotal }} دج</span>
            </div>
            {% if discount > 0 %}
            <div class="totals-row">
                <span>الخصم:</span>
                <span>-{{ discount }} دج</span>
            </div>
            {% endif %}
            {% if tax > 0 %}
            <div class="totals-row">
                <span>الضريبة:</span>
                <span>{{ tax }} دج</span>
            </div>
            {% endif %}
            <div class="totals-row total">
                <span><strong>الإجمالي:</strong></span>
                <span><strong>{{ total }} دج</strong></span>
            </div>
        </div>
        
        <!-- Payment Info -->
        <div class="payment-info">
            <p><strong>طريقة الدفع:</strong> {{ payment_method }}</p>
            {% if paid_amount > 0 %}
            <p><strong>المدفوع:</strong> {{ paid_amount }} دج</p>
            {% endif %}
            {% if remaining_amount > 0 %}
            <p><strong>المتبقي:</strong> {{ remaining_amount }} دج</p>
            {% endif %}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>شكراً لتعاملكم معنا</p>
            {% if notes %}
            <p class="notes">{{ notes }}</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""
    
    def _get_thermal_receipt_template(self) -> str:
        """قالب إيصال حراري"""
        return """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>إيصال - {{ invoice_number }}</title>
</head>
<body>
    <div class="receipt">
        <div class="center">
            <h2>{{ company_name }}</h2>
            <p>{{ company_phone }}</p>
        </div>
        
        <div class="divider"></div>
        
        <p><strong>فاتورة #:</strong> {{ invoice_number }}</p>
        <p><strong>التاريخ:</strong> {{ sale_date }}</p>
        <p><strong>العميل:</strong> {{ customer_name }}</p>
        
        <div class="divider"></div>
        
        <table>
            {% for item in items %}
            <tr>
                <td colspan="2">{{ item.product_name }}</td>
            </tr>
            <tr>
                <td>{{ item.quantity }} × {{ item.unit_price }}</td>
                <td class="align-left">{{ item.total }} دج</td>
            </tr>
            {% endfor %}
        </table>
        
        <div class="divider"></div>
        
        <div class="total-line">
            <span>المجموع:</span>
            <span>{{ total }} دج</span>
        </div>
        
        {% if paid_amount > 0 %}
        <div class="total-line">
            <span>المدفوع:</span>
            <span>{{ paid_amount }} دج</span>
        </div>
        {% endif %}
        
        {% if remaining_amount > 0 %}
        <div class="total-line">
            <span>المتبقي:</span>
            <span>{{ remaining_amount }} دج</span>
        </div>
        {% endif %}
        
        <div class="divider"></div>
        
        <div class="center">
            <p>شكراً لزيارتكم</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _get_default_quote_template(self) -> str:
        """قالب عرض سعر"""
        return """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>عرض سعر - {{ quote_number }}</title>
</head>
<body>
    <div class="invoice-container">
        <div class="header">
            <div class="company-info">
                <h1>{{ company_name }}</h1>
                <p>{{ company_address }}</p>
                <p>هاتف: {{ company_phone }}</p>
            </div>
            <div class="invoice-info">
                <h2>عرض سعر</h2>
                <p><strong>رقم العرض:</strong> {{ quote_number }}</p>
                <p><strong>التاريخ:</strong> {{ quote_date }}</p>
                <p><strong>صالح حتى:</strong> {{ valid_until }}</p>
            </div>
        </div>
        
        <div class="customer-info">
            <h3>إلى السيد/ة</h3>
            <p><strong>{{ customer_name }}</strong></p>
            <p>{{ customer_phone }}</p>
        </div>
        
        <table class="items-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>الصنف</th>
                    <th>الكمية</th>
                    <th>السعر</th>
                    <th>المجموع</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ item.product_name }}</td>
                    <td>{{ item.quantity }}</td>
                    <td>{{ item.unit_price }} دج</td>
                    <td>{{ item.total }} دج</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div class="totals">
            <div class="totals-row total">
                <span><strong>الإجمالي:</strong></span>
                <span><strong>{{ total }} دج</strong></span>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>ملاحظات:</strong></p>
            <p>{{ notes }}</p>
            <p class="signature">التوقيع: __________________</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _get_default_css(self) -> str:
        """CSS افتراضي للقوالب"""
        return """
body {
    font-family: 'Arial', sans-serif;
    margin: 0;
    padding: 20px;
    direction: rtl;
    font-size: 12pt;
}

.invoice-container {
    max-width: 800px;
    margin: 0 auto;
}

.header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;
    border-bottom: 2px solid #333;
    padding-bottom: 20px;
}

.company-info h1 {
    margin: 0;
    color: #2c3e50;
    font-size: 24pt;
}

.company-info p {
    margin: 5px 0;
    color: #666;
}

.invoice-info {
    text-align: left;
}

.invoice-info h2 {
    margin: 0;
    color: #2c3e50;
    font-size: 20pt;
}

.customer-info {
    background: #f8f9fa;
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 5px;
}

.customer-info h3 {
    margin-top: 0;
    color: #2c3e50;
}

.items-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
}

.items-table th {
    background: #2c3e50;
    color: white;
    padding: 10px;
    text-align: right;
}

.items-table td {
    padding: 8px;
    border-bottom: 1px solid #ddd;
    text-align: right;
}

.items-table tbody tr:hover {
    background: #f8f9fa;
}

.totals {
    float: left;
    width: 300px;
    margin-bottom: 20px;
}

.totals-row {
    display: flex;
    justify-content: space-between;
    padding: 8px;
    border-bottom: 1px solid #ddd;
}

.totals-row.total {
    background: #2c3e50;
    color: white;
    font-size: 14pt;
    border: none;
}

.payment-info {
    clear: both;
    margin: 20px 0;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 5px;
}

.footer {
    text-align: center;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #ddd;
}

.notes {
    font-style: italic;
    color: #666;
}

.signature {
    margin-top: 40px;
    text-align: left;
}

@media print {
    body {
        padding: 0;
    }
    
    .invoice-container {
        max-width: none;
    }
}
"""
    
    def _get_thermal_css(self) -> str:
        """CSS للطباعة الحرارية"""
        return """
body {
    font-family: monospace;
    margin: 0;
    padding: 5px;
    direction: rtl;
    font-size: 10pt;
    width: 72mm;
}

.receipt {
    width: 100%;
}

.center {
    text-align: center;
}

h2 {
    margin: 5px 0;
    font-size: 14pt;
}

p {
    margin: 3px 0;
}

.divider {
    border-top: 1px dashed #000;
    margin: 10px 0;
}

table {
    width: 100%;
    border-collapse: collapse;
}

table td {
    padding: 2px 0;
}

.align-left {
    text-align: left;
}

.total-line {
    display: flex;
    justify-content: space-between;
    font-weight: bold;
    margin: 5px 0;
}

@media print {
    body {
        padding: 0;
    }
}
"""
    
    def create_template(
        self,
        name: str,
        template_type: str,
        html_content: str,
        css_content: str = "",
        paper_size: str = PaperSize.A4.value,
        orientation: str = "portrait",
        margins: Optional[Dict[str, int]] = None,
        header_html: str = "",
        footer_html: str = "",
        is_default: bool = False
    ) -> Optional[int]:
        """
        إنشاء قالب طباعة جديد
        
        Args:
            name: اسم القالب
            template_type: نوع القالب
            html_content: محتوى HTML
            css_content: محتوى CSS
            paper_size: حجم الورق
            orientation: الاتجاه (portrait/landscape)
            margins: الهوامش
            header_html: رأس الصفحة
            footer_html: تذييل الصفحة
            is_default: افتراضي
            
        Returns:
            معرف القالب أو None
        """
        try:
            margins_json = json.dumps(margins) if margins else json.dumps({"top": 20, "right": 20, "bottom": 20, "left": 20})
            
            # إذا كان افتراضي، إزالة الافتراضية من القوالب الأخرى
            if is_default:
                self.db.execute(
                    "UPDATE print_templates SET is_default = 0 WHERE template_type = ?",
                    (template_type,)
                )
            
            cursor = self.db.execute(
                """INSERT INTO print_templates (
                    name, template_type, html_content, css_content,
                    paper_size, orientation, margins, header_html, footer_html, is_default
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, template_type, html_content, css_content, paper_size,
                 orientation, margins_json, header_html, footer_html, is_default)
            )
            
            logger.info(f"Template created: {name}")
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Failed to create template: {str(e)}")
            return None
            
    def get_template(self, template_id: int) -> Optional[PrintTemplate]:
        """الحصول على قالب بالمعرف"""
        row = self.db.fetch_one(
            "SELECT * FROM print_templates WHERE template_id = ?",
            (template_id,)
        )
        
        if row:
            margins = json.loads(row[7]) if row[7] else {}
            return PrintTemplate(
                template_id=row[0],
                name=row[1],
                template_type=row[2],
                html_content=row[3],
                css_content=row[4],
                paper_size=row[5],
                orientation=row[6],
                margins=margins,
                header_html=row[8],
                footer_html=row[9],
                is_default=bool(row[10]),
                created_at=datetime.fromisoformat(row[11]) if row[11] else None
            )
        return None
        
    def get_default_template(self, template_type: str) -> Optional[PrintTemplate]:
        """الحصول على القالب الافتراضي لنوع معين"""
        row = self.db.fetch_one(
            "SELECT * FROM print_templates WHERE template_type = ? AND is_default = 1",
            (template_type,)
        )
        
        if row:
            margins = json.loads(row[7]) if row[7] else {}
            return PrintTemplate(
                template_id=row[0],
                name=row[1],
                template_type=row[2],
                html_content=row[3],
                css_content=row[4],
                paper_size=row[5],
                orientation=row[6],
                margins=margins,
                header_html=row[8],
                footer_html=row[9],
                is_default=bool(row[10]),
                created_at=datetime.fromisoformat(row[11]) if row[11] else None
            )
        return None
        
    def list_templates(self, template_type: Optional[str] = None) -> List[PrintTemplate]:
        """قائمة القوالب"""
        if template_type:
            query = "SELECT * FROM print_templates WHERE template_type = ? ORDER BY name"
            rows = self.db.fetch_all(query, (template_type,))
        else:
            query = "SELECT * FROM print_templates ORDER BY template_type, name"
            rows = self.db.fetch_all(query)
            
        templates = []
        for row in rows:
            margins = json.loads(row[7]) if row[7] else {}
            templates.append(PrintTemplate(
                template_id=row[0],
                name=row[1],
                template_type=row[2],
                html_content=row[3],
                css_content=row[4],
                paper_size=row[5],
                orientation=row[6],
                margins=margins,
                header_html=row[8],
                footer_html=row[9],
                is_default=bool(row[10]),
                created_at=datetime.fromisoformat(row[11]) if row[11] else None
            ))
            
        return templates
        
    def render_template(
        self,
        template: PrintTemplate,
        data: Dict[str, Any]
    ) -> str:
        """
        تصيير قالب مع البيانات
        
        Args:
            template: القالب
            data: البيانات
            
        Returns:
            HTML جاهز للطباعة
        """
        try:
            from jinja2 import Template
            
            # تجميع HTML و CSS
            full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
    {template.css_content}
    </style>
</head>
<body>
    {template.html_content}
</body>
</html>
"""
            
            # تصيير القالب
            jinja_template = Template(full_html)
            rendered = jinja_template.render(**data)
            
            return rendered
            
        except Exception as e:
            logger.error(f"Failed to render template: {str(e)}")
            return ""
            
    def log_print_job(
        self,
        template_id: int,
        document_type: str,
        document_id: int,
        user_id: Optional[int] = None,
        copies: int = 1,
        output_type: str = "printer",
        output_path: str = ""
    ) -> Optional[int]:
        """تسجيل عملية طباعة"""
        try:
            cursor = self.db.execute(
                """INSERT INTO print_jobs (
                    template_id, document_type, document_id, user_id,
                    copies, output_type, output_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (template_id, document_type, document_id, user_id,
                 copies, output_type, output_path)
            )
            
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Failed to log print job: {str(e)}")
            return None


# مثيل عام
global_print_manager: Optional[PrintManager] = None


def initialize_print_manager(db_manager) -> PrintManager:
    """تهيئة مدير الطباعة العام"""
    global global_print_manager
    global_print_manager = PrintManager(db_manager)
    return global_print_manager


def get_print_manager() -> Optional[PrintManager]:
    """الحصول على مدير الطباعة العام"""
    return global_print_manager

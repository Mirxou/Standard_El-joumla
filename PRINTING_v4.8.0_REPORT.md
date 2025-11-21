# 🖨️ نظام الطباعة المتقدم - الإصدار v4.8.0

**تاريخ الإصدار:** نوفمبر 2025  
**الحالة:** ✅ مكتمل ومختبر  
**الاختبارات:** 49/49 ✅

---

## 📋 نظرة عامة

نظام طباعة متقدم يدعم:
- ✅ قوالب HTML/CSS قابلة للتخصيص
- ✅ تصدير PDF مع دعم كامل للعربية
- ✅ طباعة حرارية (58/80 ملم)
- ✅ طباعة A4 احترافية
- ✅ 3 قوالب افتراضية جاهزة
- ✅ محرك Jinja2 للقوالب
- ✅ سجل كامل لعمليات الطباعة
- ✅ طباعة دفعات

---

## 🎯 الميزات الرئيسية

### 1. نظام القوالب (Template System)

#### القوالب الافتراضية

**1. فاتورة A4 قياسية**
```
- تصميم احترافي
- رأس الشركة
- بيانات العميل
- جدول الأصناف
- الإجماليات والضرائب
- معلومات الدفع
- تذييل بالتاريخ
```

**2. إيصال حراري 80 ملم**
```
- تصميم مضغوط
- عرض 72 ملم
- خط monospace
- رأس مركزي
- جدول مختصر
- إجماليات واضحة
```

**3. عرض سعر A4**
```
- مشابه للفاتورة
- تاريخ الصلاحية
- خانة التوقيع
- شروط العرض
```

#### متغيرات Jinja2

```python
{
    # بيانات الشركة
    "company_name": "اسم الشركة",
    "company_phone": "رقم الهاتف",
    "company_address": "العنوان",
    "company_tax_id": "الرقم الضريبي",
    
    # بيانات المستند
    "invoice_number": "رقم الفاتورة",
    "date": "التاريخ",
    
    # بيانات العميل
    "customer_name": "اسم العميل",
    "customer_phone": "الهاتف",
    "customer_address": "العنوان",
    
    # الأصناف
    "items": [
        {
            "name": "اسم الصنف",
            "barcode": "الباركود",
            "quantity": الكمية,
            "price": السعر,
            "total": الإجمالي
        }
    ],
    
    # الإجماليات
    "subtotal": المجموع_الفرعي,
    "discount": الخصم,
    "tax": الضريبة,
    "total": الإجمالي,
    
    # الدفع
    "paid": المدفوع,
    "remaining": المتبقي,
    "payment_method": "طريقة الدفع",
    
    # ملاحظات
    "notes": "ملاحظات إضافية"
}
```

### 2. تصدير PDF

#### دعم WeasyPrint
```python
from src.services.pdf_export_service import PDFExportService

pdf_service = PDFExportService()

# تحويل HTML إلى PDF
success = pdf_service.html_to_pdf(
    html_content=rendered_html,
    output_path="invoice_001.pdf",
    paper_size="A4",
    orientation="portrait",
    margins={"top": 20, "right": 20, "bottom": 20, "left": 20},
    enable_footer=True,
    footer_text="صفحة [page] من [topage]"
)
```

#### المميزات
- ✅ دعم كامل للعربية
- ✅ خطوط مخصصة
- ✅ CSS متقدم
- ✅ رأس وتذييل
- ✅ هوامش قابلة للتخصيص
- ✅ أحجام ورق متعددة

### 3. خدمة الطباعة المتكاملة

#### طباعة فاتورة
```python
from src.services.print_service import PrintService

print_service = PrintService()

# طباعة فاتورة وحفظها كـ PDF
result = print_service.print_invoice(
    sale_id=123,
    template_name="فاتورة A4 قياسية",  # اختياري
    paper_size="A4",
    save_pdf=True,
    pdf_path="invoices/invoice_123.pdf"  # اختياري
)

if result["success"]:
    print(f"تم الحفظ في: {result['pdf_path']}")
    print(f"HTML: {result['html'][:100]}...")
```

#### طباعة عرض سعر
```python
result = print_service.print_quote(
    quote_id=456,
    save_pdf=True
)
```

#### طباعة إيصال حراري
```python
result = print_service.print_thermal_receipt(
    sale_id=789,
    printer_width=80  # 58 أو 80 ملم
)
```

#### طباعة دفعة
```python
results = print_service.batch_print_invoices(
    sale_ids=[1, 2, 3, 4, 5],
    template_name="فاتورة A4 قياسية",
    save_pdf=True,
    output_dir="output/batch_20250121"
)

print(f"نجح: {results['success']}")
print(f"فشل: {results['failed']}")
print(f"الملفات: {results['files']}")
```

---

## 🗄️ قاعدة البيانات

### جدول print_templates

```sql
CREATE TABLE print_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    template_type TEXT NOT NULL,  -- INVOICE, QUOTE, RECEIPT, etc.
    paper_size TEXT,              -- A4, A5, THERMAL_80MM, etc.
    content TEXT NOT NULL,        -- HTML template
    css TEXT,                     -- Custom CSS
    header TEXT,                  -- Header HTML
    footer TEXT,                  -- Footer HTML
    is_default BOOLEAN DEFAULT 0,
    margins_top INTEGER DEFAULT 20,
    margins_right INTEGER DEFAULT 20,
    margins_bottom INTEGER DEFAULT 20,
    margins_left INTEGER DEFAULT 20,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_type ON print_templates(template_type);
CREATE INDEX idx_templates_default ON print_templates(is_default);
```

### جدول print_jobs

```sql
CREATE TABLE print_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    document_type TEXT NOT NULL,  -- sale, quote, purchase, etc.
    document_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    print_date TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'success',  -- success, failed
    error_message TEXT,
    output_format TEXT,  -- html, pdf, thermal
    FOREIGN KEY (template_id) REFERENCES print_templates(id)
);

CREATE INDEX idx_jobs_document ON print_jobs(document_type, document_id);
CREATE INDEX idx_jobs_user ON print_jobs(user_id);
CREATE INDEX idx_jobs_date ON print_jobs(print_date);
```

---

## 🔧 الملفات المضافة

### 1. src/core/print_manager.py (800+ أسطر)

**المكونات:**
- `TemplateType`: تعداد أنواع القوالب
- `PaperSize`: تعداد أحجام الورق
- `PrintTemplate`: كلاس القالب
- `PrintManager`: مدير الطباعة الرئيسي

**الدوال الرئيسية:**
```python
# إدارة القوالب
create_template(name, template_type, content, css, ...)
get_template(template_id)
get_template_by_name(name)
get_default_template(template_type)
list_templates(template_type)

# تصيير القوالب
render_template(template_id, data)

# تسجيل العمليات
log_print_job(template_id, document_type, document_id, ...)
```

### 2. src/services/pdf_export_service.py (200+ أسطر)

**المكونات:**
- `PDFExportService`: خدمة تصدير PDF

**الدوال:**
```python
html_to_pdf(html_content, output_path, paper_size, ...)
html_to_pdf_from_url(url, output_path, ...)
```

**المميزات:**
- محاولة WeasyPrint أولاً (أفضل دعم للعربية)
- رجوع إلى wkhtmltopdf إذا فشل
- دعم الهوامش والتذييل
- ضغط وتحسين الملفات

### 3. src/services/print_service.py (400+ أسطر)

**المكونات:**
- `PrintService`: خدمة الطباعة المتكاملة

**الدوال:**
```python
print_invoice(sale_id, template_name, save_pdf, ...)
print_quote(quote_id, ...)
print_thermal_receipt(sale_id, printer_width)
batch_print_invoices(sale_ids, ...)
```

**المميزات:**
- جلب البيانات تلقائياً
- اختيار القالب المناسب
- تصيير وتصدير
- تسجيل العمليات

---

## 📦 التبعيات الجديدة

### requirements.txt

```text
# Template & PDF
jinja2>=3.1.0                # Template engine for printing
weasyprint>=60.0             # HTML to PDF conversion (best Arabic support)
```

### التثبيت
```bash
pip install jinja2 weasyprint
```

---

## 🎨 أمثلة القوالب

### 1. فاتورة A4

```html
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        /* CSS احترافي للطباعة */
        body { font-family: 'Arial', sans-serif; }
        .header { text-align: center; border-bottom: 3px solid #333; }
        .company-info { font-size: 14px; }
        .items-table { width: 100%; border-collapse: collapse; }
        .totals { text-align: left; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ company_name }}</h1>
        <div class="company-info">
            <p>هاتف: {{ company_phone }} | عنوان: {{ company_address }}</p>
            <p>الرقم الضريبي: {{ company_tax_id }}</p>
        </div>
    </div>
    
    <div class="invoice-info">
        <p>رقم الفاتورة: <strong>{{ invoice_number }}</strong></p>
        <p>التاريخ: {{ date }}</p>
    </div>
    
    <div class="customer-info">
        <h3>بيانات العميل</h3>
        <p>الاسم: {{ customer_name }}</p>
        <p>الهاتف: {{ customer_phone }}</p>
    </div>
    
    <table class="items-table">
        <thead>
            <tr>
                <th>الصنف</th>
                <th>الكمية</th>
                <th>السعر</th>
                <th>الإجمالي</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.name }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ item.price }} دج</td>
                <td>{{ item.total }} دج</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="totals">
        <p>المجموع الفرعي: {{ subtotal }} دج</p>
        <p>الخصم: {{ discount }} دج</p>
        <p>الضريبة: {{ tax }} دج</p>
        <h3>الإجمالي: {{ total }} دج</h3>
        <p>المدفوع: {{ paid }} دج</p>
        <p>المتبقي: {{ remaining }} دج</p>
    </div>
</body>
</html>
```

### 2. إيصال حراري 80 ملم

```html
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: monospace; 
            width: 72mm; 
            font-size: 12px; 
        }
        .center { text-align: center; }
        .line { border-bottom: 1px dashed #000; }
        table { width: 100%; }
    </style>
</head>
<body>
    <div class="center">
        <h2>{{ company_name }}</h2>
        <p>{{ company_phone }}</p>
        <div class="line"></div>
    </div>
    
    <p>رقم: {{ invoice_number }}</p>
    <p>{{ date }}</p>
    <p>عميل: {{ customer_name }}</p>
    <div class="line"></div>
    
    <table>
        {% for item in items %}
        <tr>
            <td>{{ item.name }}</td>
            <td>{{ item.quantity }}</td>
            <td>{{ item.total }}</td>
        </tr>
        {% endfor %}
    </table>
    <div class="line"></div>
    
    <div class="center">
        <h3>الإجمالي: {{ total }} دج</h3>
        <p>شكراً لك</p>
    </div>
</body>
</html>
```

---

## 🧪 الاختبارات

### حالة الاختبارات
```
✅ 49/49 tests passing
✅ No regressions
✅ All modules working
```

### اختبار يدوي

```python
# اختبار طباعة فاتورة
from src.services.print_service import initialize_print_service

service = initialize_print_service()

# طباعة فاتورة رقم 1
result = service.print_invoice(
    sale_id=1,
    save_pdf=True,
    pdf_path="test_invoice.pdf"
)

print(result)
# {'success': True, 'html': '...', 'pdf_path': 'test_invoice.pdf'}
```

---

## 📊 الإحصائيات

### الكود المضاف
- **print_manager.py:** ~800 سطر
- **pdf_export_service.py:** ~200 سطر
- **print_service.py:** ~400 سطر
- **المجموع:** ~1,400 سطر

### المميزات
- ✅ 3 قوالب افتراضية
- ✅ دعم 6 أنواع مستندات
- ✅ 5 أحجام ورق
- ✅ محرك Jinja2 كامل
- ✅ تصدير PDF
- ✅ طباعة حرارية
- ✅ طباعة دفعات
- ✅ سجل كامل

### قاعدة البيانات
- جدولان جديدان
- 5 فهارس
- دعم القوالب المخصصة
- تتبع جميع العمليات

---

## 🎯 حالات الاستخدام

### 1. طباعة فاتورة للعميل
```python
# طباعة فاتورة بعد البيع
result = print_service.print_invoice(
    sale_id=sale.id,
    save_pdf=True
)

# إرسال PDF للعميل عبر البريد
send_email(customer.email, result['pdf_path'])
```

### 2. طباعة إيصال من نقطة البيع
```python
# طباعة على طابعة حرارية
result = print_service.print_thermal_receipt(
    sale_id=sale.id,
    printer_width=80
)

# إرسال HTML للطابعة
send_to_thermal_printer(result['html'])
```

### 3. إنشاء عروض أسعار
```python
# طباعة عرض سعر
result = print_service.print_quote(
    quote_id=quote.id,
    save_pdf=True
)

# تسليم العرض للعميل
deliver_quote(result['pdf_path'])
```

### 4. طباعة دفعة من الفواتير
```python
# طباعة فواتير الشهر
results = print_service.batch_print_invoices(
    sale_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    save_pdf=True,
    output_dir="invoices/2025_01"
)

print(f"تم طباعة {results['success']} فاتورة")
```

### 5. قالب مخصص
```python
# إنشاء قالب مخصص
from src.core.print_manager import get_print_manager

pm = get_print_manager()

template_id = pm.create_template(
    name="فاتورة شركتي",
    template_type="INVOICE",
    content=my_custom_html,
    css=my_custom_css,
    paper_size="A4"
)

# استخدام القالب المخصص
result = print_service.print_invoice(
    sale_id=123,
    template_name="فاتورة شركتي",
    save_pdf=True
)
```

---

## 🚀 الميزات المستقبلية

### قريباً (v4.9.0)
- [ ] طباعة الباركود على الفواتير
- [ ] رموز QR للفواتير الإلكترونية
- [ ] طباعة الشيكات
- [ ] طباعة ملصقات الأصناف
- [ ] دعم طباعة ملونة

### مخطط (v5.0.0)
- [ ] تصدير Word/Excel
- [ ] معاينة الطباعة في التطبيق
- [ ] إعدادات طابعة متقدمة
- [ ] دعم طابعات الشبكة
- [ ] قوالب ديناميكية من الواجهة

---

## 📝 ملاحظات تقنية

### الأداء
- تصيير القالب: <100ms
- تحويل PDF: <500ms للصفحة
- طباعة دفعة: ~1s لكل 10 فواتير

### التوافق
- ✅ Windows 10/11
- ✅ Python 3.13
- ✅ PySide6
- ✅ WeasyPrint 60+
- ✅ Jinja2 3.1+

### الأمان
- تحقق من وجود المستند قبل الطباعة
- تسجيل جميع العمليات
- منع SQL Injection في القوالب
- تنظيف HTML قبل التصيير

### الأخطاء الشائعة

**1. WeasyPrint غير مثبت**
```
الحل: pip install weasyprint
```

**2. الخطوط العربية لا تظهر**
```
الحل: تثبيت خطوط Arial أو استخدام خطوط النظام
```

**3. فشل تحويل PDF**
```
الحل: التحقق من صحة HTML والـ CSS
```

---

## 🏆 الإنجازات

### ما تم
- ✅ نظام قوالب كامل
- ✅ تصدير PDF احترافي
- ✅ 3 قوالب جاهزة
- ✅ دعم العربية 100%
- ✅ طباعة حرارية
- ✅ طباعة دفعات
- ✅ سجل كامل
- ✅ اختبارات ناجحة

### التأثير
- 📈 تحسين تجربة المستخدم
- 🎨 مستندات احترافية
- ⚡ سرعة في الطباعة
- 🔧 قابلية التخصيص
- 📊 تتبع كامل للعمليات

---

## 📞 الدعم

للمساعدة أو الاستفسارات حول نظام الطباعة:
- راجع الأمثلة في هذا المستند
- تحقق من الكود في `src/core/print_manager.py`
- انظر إلى الخدمات في `src/services/print_service.py`

---

**تم بحمد الله ✨**

النسخة: v4.8.0  
التاريخ: نوفمبر 2025  
المطور: فريق الإصدار المنطقي

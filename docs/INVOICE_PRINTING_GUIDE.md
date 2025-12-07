# 🖨️ دليل نظام طباعة الفواتير الاحترافي

## نظرة عامة

تم بناء نظام طباعة فواتير احترافي باستخدام **HTML/CSS Templates + Jinja2** بدلاً من الرسم المباشر بالكود. هذا يجعل:
- ✅ الصيانة أسهل (تعديل HTML بدلاً من Python)
- ✅ التصميم أجمل (CSS كامل)
- ✅ الطباعة أضمن (المتصفح يدعم الطباعة بشكل مثالي)

## الملفات المُنشأة

### 1. قوالب الفواتير

#### قالب الفاتورة الرئيسي
**الموقع:** `assets/templates/invoice.html`

قالب HTML احترافي يدعم:
- العربية (RTL)
- تصميم عصري مع Royal Blue accents
- جداول منسقة
- ملاحظات وبيانات الشركة
- QR Code و Barcode
- شعار الشركة وصور المنتجات
- التوقيعات الإلكترونية
- دعم السمات (Light/Dark)
- طباعة محسّنة (Print Media Queries)

#### قوالب متخصصة

**`receipt.html`** - إيصال بسيط للطابعات الحرارية:
- تصميم مضغوط
- مناسب للطابعات 80mm
- خط Courier New

**`quote.html`** - عرض أسعار:
- تصميم مشابه للفاتورة
- حقول خاصة بالعروض
- تاريخ انتهاء الصلاحية

**`purchase_order.html`** - أمر شراء:
- معلومات المورد
- تفاصيل التسليم
- شروط الدفع

**`invoice-thermal.html`** - فاتورة للطابعات الحرارية:
- عرض 80mm
- تصميم مضغوط
- مناسب للطابعات الحرارية

**`invoice-a4.html`** - فاتورة A4:
- محسّنة لطباعة A4
- تصميم احترافي
- مساحات أكبر

**`invoice-compact.html`** - فاتورة مضغوطة:
- خطوط أصغر
- مسافات أقل
- مناسب للطباعة الاقتصادية

### 2. ملفات CSS

- **`invoice.css`** - أنماط الفاتورة الرئيسية
- **`invoice-dark.css`** - أنماط السمات الداكنة
- **`receipt.css`** - أنماط الإيصال

### 3. خدمة الطباعة
**الموقع:** `src/services/invoice_print_service.py`

الخدمة توفر:
- `generate_invoice_html()` - توليد HTML من القالب
- `print_invoice()` - فتح الفاتورة في المتصفح للطباعة
- `save_invoice_html()` - حفظ الفاتورة كملف HTML
- دعم جميع القوالب المتاحة
- توليد QR Code و Barcode تلقائياً

## كيفية الاستخدام

### من واجهة المبيعات

1. افتح صفحة **المبيعات**
2. حدد فاتورة من الجدول
3. اضغط زر **"📄 طباعة فاتورة"**
4. ستفتح الفاتورة في المتصفح
5. اضغط `Ctrl+P` للطباعة

### من الكود (Python)

```python
from src.services.invoice_print_service import InvoicePrintService

# إنشاء الخدمة
service = InvoicePrintService()

# إعداد بيانات الفاتورة
invoice_data = {
    'id': 'INV-2025-001',
    'date': '2025-01-15',
    'customer': 'أحمد محمد',
    'customer_phone': '0555123456',
    'customer_address': 'الجزائر العاصمة',
    'items': [
        {
            'name': 'لابتوب HP Victus',
            'barcode': '1234567890123',
            'quantity': 1,
            'price': 150000,
            'total': 150000
        },
        {
            'name': 'ماوس لاسلكي',
            'quantity': 2,
            'price': 2500,
            'total': 5000
        }
    ],
    'subtotal': 155000,
    'discount': 5000,
    'tax': 15800,
    'total': 165800,
    'paid': 100000,
    'remaining': 65800,
    'payment_method': 'نقدي + آجل',
    'notes': 'شكراً لتعاملكم معنا',
    'company_name': 'الإصدار المنطقي',
    'company_phone': '0123456789',
    'company_address': 'الجزائر العاصمة',
    'company_tax_id': '123456789012',
    'company_email': 'info@logicalversion.com',
    'company_logo': 'assets/images/logo.png',  # مسار الشعار
    'qr_code_url': None,  # سيتم توليده تلقائياً
    'barcode_url': None,  # سيتم توليده تلقائياً
    'theme': 'light'  # 'light' أو 'dark'
}

# طباعة الفاتورة (استخدام القالب الافتراضي)
success, message = service.print_invoice(invoice_data)

# طباعة باستخدام قالب محدد
success, message = service.print_invoice(
    invoice_data,
    template_name="receipt.html"  # أو "quote.html", "purchase_order.html", إلخ
)

# طباعة فاتورة حرارية
success, message = service.print_invoice(
    invoice_data,
    template_name="invoice-thermal.html"
)

# طباعة فاتورة A4
success, message = service.print_invoice(
    invoice_data,
    template_name="invoice-a4.html"
)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

## تخصيص القالب

### تعديل بيانات الشركة

افتح `assets/templates/invoice.html` وعدّل:

```html
<div class="company-info">
    <h1>{{ company_name or "الإصدار المنطقي" }}</h1>
    <p>
        {{ company_address or "شارع التقنية، الجزائر العاصمة" }}<br>
        هاتف: {{ company_phone or "0123456789" }}<br>
        {% if company_tax_id %}
        الرقم الضريبي: {{ company_tax_id }}
        {% endif %}
    </p>
</div>
```

### تغيير الألوان

عدّل CSS في القالب:

```css
.invoice-box {
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.header {
    border-bottom: 2px solid #3b82f6; /* Royal Blue */
}

.company-info h1 {
    color: #3b82f6; /* Royal Blue */
}
```

### إضافة حقول جديدة

1. أضف الحقل في `invoice_data`:
```python
invoice_data['new_field'] = 'قيمة جديدة'
```

2. استخدمه في القالب:
```html
<p>{{ new_field }}</p>
```

### استخدام القوالب المختلفة

```python
# إيصال بسيط
service.print_invoice(invoice_data, template_name="receipt.html")

# عرض أسعار
service.print_invoice(invoice_data, template_name="quote.html")

# أمر شراء
service.print_invoice(invoice_data, template_name="purchase_order.html")

# فاتورة حرارية
service.print_invoice(invoice_data, template_name="invoice-thermal.html")

# فاتورة A4
service.print_invoice(invoice_data, template_name="invoice-a4.html")

# فاتورة مضغوطة
service.print_invoice(invoice_data, template_name="invoice-compact.html")
```

### QR Code و Barcode

يتم توليد QR Code و Barcode تلقائياً إذا لم يتم توفيرهما:

```python
# QR Code تلقائي (يحتوي على رابط الفاتورة)
invoice_data['qr_code_url'] = None  # سيتم توليده تلقائياً

# Barcode تلقائي (يحتوي على رقم الفاتورة)
invoice_data['barcode_url'] = None  # سيتم توليده تلقائياً

# أو توفير QR Code/Barcode مخصص
invoice_data['qr_code_url'] = 'data:image/png;base64,...'
invoice_data['barcode_url'] = 'data:image/png;base64,...'
```

### دعم السمات

```python
# سمة فاتحة
invoice_data['theme'] = 'light'

# سمة داكنة
invoice_data['theme'] = 'dark'
```

## هيكل البيانات المطلوبة

```python
invoice_data = {
    # معلومات الفاتورة
    'id': str,              # رقم الفاتورة
    'date': str,            # تاريخ الفاتورة (YYYY-MM-DD)
    
    # معلومات العميل
    'customer': str,        # اسم العميل
    'customer_phone': str,  # هاتف العميل (اختياري)
    'customer_address': str, # عنوان العميل (اختياري)
    
    # الأصناف
    'items': [
        {
            'name': str,        # اسم المنتج
            'barcode': str,     # الباركود (اختياري)
            'quantity': int,    # الكمية
            'price': float,     # السعر
            'total': float      # الإجمالي
        }
    ],
    
    # المبالغ
    'subtotal': float,      # المجموع الفرعي
    'discount': float,      # الخصم (اختياري)
    'tax': float,           # الضريبة (اختياري)
    'total': float,         # الإجمالي النهائي
    'paid': float,          # المدفوع (اختياري)
    'remaining': float,     # المتبقي (اختياري)
    
    # معلومات إضافية
    'payment_method': str,  # طريقة الدفع (اختياري)
    'notes': str,           # ملاحظات (اختياري)
    
    # بيانات الشركة
    'company_name': str,
    'company_phone': str,
    'company_address': str,
    'company_tax_id': str   # (اختياري)
}
```

## الميزات

### ✅ ما يعمل الآن

- ✅ طباعة فواتير HTML احترافية
- ✅ دعم كامل للعربية (RTL)
- ✅ تصميم عصري وجميل
- ✅ فتح تلقائي في المتصفح
- ✅ طباعة محسّنة (Print Media Queries)
- ✅ دعم جميع بيانات الفاتورة (أصناف، خصومات، ضرائب، مدفوعات)
- ✅ **قوالب متعددة:** فاتورة، إيصال، عرض أسعار، أمر شراء
- ✅ **قوالب متخصصة:** حرارية، A4، مضغوطة
- ✅ **QR Code و Barcode:** توليد تلقائي
- ✅ **شعار الشركة:** دعم الصور
- ✅ **صور المنتجات:** عرض صور المنتجات في الفاتورة
- ✅ **التوقيعات الإلكترونية:** دعم التوقيعات
- ✅ **دعم السمات:** Light/Dark themes
- ✅ **CSS منفصل:** ملفات CSS منفصلة للصيانة السهلة

### 🔄 قيد التطوير (لاحقاً)

- [ ] حفظ تلقائي كـ PDF (باستخدام WeasyPrint)
- [ ] إرسال الفاتورة بالبريد الإلكتروني
- [ ] طباعة دفعة من الفواتير
- [ ] قوالب مخصصة من واجهة المستخدم

## استكشاف الأخطاء

### المشكلة: "القالب غير موجود"

**الحل:** تأكد من وجود ملف `assets/templates/invoice.html`

```bash
# إنشاء المجلد إذا لم يكن موجوداً
mkdir -p assets/templates
```

### المشكلة: "خطأ في توليد الفاتورة"

**الحل:** تحقق من:
1. تثبيت Jinja2: `pip install jinja2`
2. صحة بيانات `invoice_data`
3. وجود جميع الحقول المطلوبة

### المشكلة: "لا يفتح المتصفح"

**الحل:** 
- تأكد من وجود متصفح افتراضي
- جرب فتح الملف يدوياً من `temp_invoice.html`

## أمثلة متقدمة

### حفظ الفاتورة كملف HTML

```python
success, message = service.save_invoice_html(
    invoice_data,
    output_path="output/invoices/invoice_001.html"
)
```

### توليد HTML فقط (بدون طباعة)

```python
success, message, html_content = service.generate_invoice_html(invoice_data)

if success:
    # استخدم html_content كما تشاء
    print(html_content)
```

---

**تم إنشاء هذا النظام بواسطة:** Logical Version Team  
**التاريخ:** 2025-01-15  
**الإصدار:** 1.0.0


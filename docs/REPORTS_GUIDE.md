# 📊 دليل نظام التقارير - Reports Guide

## نظرة عامة

يوفر نظام ستاندرد الجملة نظام تقارير شامل يدعم:
- تقارير المبيعات
- تقارير المخزون
- التقارير المالية
- تقارير التحليلات
- تصدير بصيغ متعددة (PDF, Excel, CSV, JSON)

## ReportExporter

### التهيئة

```python
from src.services.report_exporter import ReportExporter
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize()

report_exporter = ReportExporter(db_manager)
```

### توليد تقرير

```python
from src.models.report import ReportType, ReportFilter
from datetime import datetime, timedelta

# إنشاء فلاتر
filters = ReportFilter(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    customer_id=None,
    product_id=None
)

# توليد التقرير
report_data = report_exporter.generate_report(
    report_type=ReportType.SALES_SUMMARY,
    filters=filters
)

print(f"العنوان: {report_data.title}")
print(f"عدد السجلات: {len(report_data.data)}")
print(f"الملخص: {report_data.summary}")
```

## Report Types

### تقارير المبيعات

```python
# ملخص المبيعات
report = report_exporter.generate_report(
    ReportType.SALES_SUMMARY,
    filters
)

# المبيعات التفصيلية
report = report_exporter.generate_report(
    ReportType.SALES_DETAILED,
    filters
)

# المبيعات حسب المنتج
report = report_exporter.generate_report(
    ReportType.SALES_BY_PRODUCT,
    filters
)

# المبيعات حسب العميل
report = report_exporter.generate_report(
    ReportType.SALES_BY_CUSTOMER,
    filters
)

# المبيعات حسب الفئة
report = report_exporter.generate_report(
    ReportType.SALES_BY_CATEGORY,
    filters
)
```

### تقارير المخزون

```python
# حالة المخزون
report = report_exporter.generate_report(
    ReportType.INVENTORY_STATUS,
    filters
)

# حركة المخزون
report = report_exporter.generate_report(
    ReportType.INVENTORY_MOVEMENT,
    filters
)

# تقييم المخزون
report = report_exporter.generate_report(
    ReportType.INVENTORY_VALUATION,
    filters
)

# أعمار المخزون
report = report_exporter.generate_report(
    ReportType.INVENTORY_AGING,
    filters
)

# دوران المخزون
report = report_exporter.generate_report(
    ReportType.INVENTORY_TURNOVER,
    filters
)
```

### التقارير المالية

```python
# الملخص المالي
report = report_exporter.generate_report(
    ReportType.FINANCIAL_SUMMARY,
    filters
)

# قائمة الدخل
report = report_exporter.generate_report(
    ReportType.FINANCIAL_INCOME,
    filters
)

# الميزانية العمومية
report = report_exporter.generate_report(
    ReportType.FINANCIAL_BALANCE,
    filters
)

# التدفقات النقدية
report = report_exporter.generate_report(
    ReportType.CASH_FLOW,
    filters
)

# الأرباح والخسائر
report = report_exporter.generate_report(
    ReportType.PROFIT_LOSS,
    filters
)
```

### تقارير التحليلات

```python
# تحليل العملاء
report = report_exporter.generate_report(
    ReportType.CUSTOMER_ANALYSIS,
    filters
)

# تحليل الموردين
report = report_exporter.generate_report(
    ReportType.SUPPLIER_ANALYSIS,
    filters
)

# أداء المنتجات
report = report_exporter.generate_report(
    ReportType.PRODUCT_PERFORMANCE,
    filters
)

# تحليل المدفوعات
report = report_exporter.generate_report(
    ReportType.PAYMENT_ANALYSIS,
    filters
)

# أعمار الذمم المدينة
report = report_exporter.generate_report(
    ReportType.RECEIVABLES_AGING,
    filters
)

# أعمار الذمم الدائنة
report = report_exporter.generate_report(
    ReportType.PAYABLES_AGING,
    filters
)
```

## Report Filters

### إنشاء فلاتر مخصصة

```python
from src.models.report import ReportFilter, ReportPeriod
from datetime import datetime, timedelta

# فلتر بسيط
filters = ReportFilter(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)

# فلتر متقدم
filters = ReportFilter(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    customer_id=1,
    product_id=5,
    category_id=2,
    min_amount=100.0,
    max_amount=10000.0,
    payment_method="نقدي",
    group_by="date",
    sort_by="total",
    sort_order="DESC",
    limit=100
)

# فلتر مع قوائم IDs
filters = ReportFilter(
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    customer_ids=[1, 2, 3],
    product_ids=[10, 20, 30],
    category_ids=[1, 2]
)
```

## Export Formats

### تصدير إلى PDF

```python
from src.models.report import ExportFormat

# توليد التقرير
report_data = report_exporter.generate_report(
    ReportType.SALES_SUMMARY,
    filters
)

# تصدير إلى PDF
export_path = report_exporter.export_report(
    report_data=report_data,
    format=ExportFormat.PDF,
    output_path="reports/sales_summary.pdf"
)
```

### تصدير إلى Excel

```python
export_path = report_exporter.export_report(
    report_data=report_data,
    format=ExportFormat.EXCEL,
    output_path="reports/sales_summary.xlsx"
)
```

### تصدير إلى CSV

```python
export_path = report_exporter.export_report(
    report_data=report_data,
    format=ExportFormat.CSV,
    output_path="reports/sales_summary.csv"
)
```

### تصدير إلى JSON

```python
export_path = report_exporter.export_report(
    report_data=report_data,
    format=ExportFormat.JSON,
    output_path="reports/sales_summary.json"
)
```

## أمثلة عملية

### مثال 1: تقرير مبيعات شهري

```python
from datetime import datetime, timedelta
from src.models.report import ReportType, ReportFilter, ExportFormat

# إنشاء فلاتر للشهر الحالي
today = datetime.now()
first_day = datetime(today.year, today.month, 1)
last_day = datetime(today.year, today.month + 1, 1) - timedelta(days=1)

filters = ReportFilter(
    start_date=first_day,
    end_date=last_day
)

# توليد التقرير
report_data = report_exporter.generate_report(
    ReportType.SALES_SUMMARY,
    filters
)

# تصدير إلى PDF
export_path = report_exporter.export_report(
    report_data=report_data,
    format=ExportFormat.PDF,
    output_path=f"reports/sales_{today.year}_{today.month:02d}.pdf"
)

print(f"تم تصدير التقرير إلى: {export_path}")
```

### مثال 2: تقرير مخزون للمنتجات منخفضة المخزون

```python
# إنشاء فلتر للمنتجات منخفضة المخزون
filters = ReportFilter(
    include_zero_balances=True
)

# توليد التقرير
report_data = report_exporter.generate_report(
    ReportType.INVENTORY_STATUS,
    filters
)

# تصفية المنتجات منخفضة المخزون
low_stock_items = [
    item for item in report_data.data
    if item.get('current_stock', 0) < item.get('min_stock', 0)
]

print(f"عدد المنتجات منخفضة المخزون: {len(low_stock_items)}")
for item in low_stock_items:
    print(f"  - {item['name']}: {item['current_stock']} / {item['min_stock']}")
```

### مثال 3: تقرير مالي سنوي

```python
from datetime import datetime

# إنشاء فلاتر للسنة الحالية
year = datetime.now().year
filters = ReportFilter(
    start_date=datetime(year, 1, 1),
    end_date=datetime(year, 12, 31)
)

# توليد التقارير المالية
income_report = report_exporter.generate_report(
    ReportType.FINANCIAL_INCOME,
    filters
)

balance_report = report_exporter.generate_report(
    ReportType.FINANCIAL_BALANCE,
    filters
)

cashflow_report = report_exporter.generate_report(
    ReportType.CASH_FLOW,
    filters
)

# تصدير جميع التقارير
reports = [
    (income_report, "income"),
    (balance_report, "balance"),
    (cashflow_report, "cashflow")
]

for report_data, name in reports:
    export_path = report_exporter.export_report(
        report_data=report_data,
        format=ExportFormat.PDF,
        output_path=f"reports/{name}_{year}.pdf"
    )
    print(f"تم تصدير {name} إلى: {export_path}")
```

### مثال 4: تقرير مخصص مع تجميع

```python
# تقرير مبيعات مجمعة حسب المنتج
filters = ReportFilter(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    group_by="product",
    sort_by="total",
    sort_order="DESC",
    limit=10  # أفضل 10 منتجات
)

report_data = report_exporter.generate_report(
    ReportType.SALES_BY_PRODUCT,
    filters
)

# عرض أفضل المنتجات
print("أفضل 10 منتجات:")
for i, item in enumerate(report_data.data[:10], 1):
    print(f"{i}. {item['product_name']}: {item['total']} ريال")
```

## Report Data Structure

### ReportData

```python
@dataclass
class ReportData:
    title: str                    # عنوان التقرير
    subtitle: str                 # العنوان الفرعي
    generated_at: datetime        # وقت التوليد
    filters: ReportFilter         # الفلاتر المستخدمة
    data: List[Dict[str, Any]]    # بيانات التقرير
    summary: Dict[str, Any]       # الملخص
    charts_data: Optional[Dict[str, Any]] = None  # بيانات الرسوم البيانية
```

### الوصول إلى البيانات

```python
# الوصول إلى البيانات
for row in report_data.data:
    print(f"التاريخ: {row['date']}")
    print(f"المبلغ: {row['total']}")
    print("---")

# الوصول إلى الملخص
summary = report_data.summary
print(f"إجمالي المبيعات: {summary.get('total_sales', 0)}")
print(f"عدد الفواتير: {summary.get('total_invoices', 0)}")
print(f"متوسط قيمة الفاتورة: {summary.get('average_invoice_value', 0)}")
```

## Charts Data

### بيانات الرسوم البيانية

```python
# الوصول إلى بيانات الرسوم البيانية
if report_data.charts_data:
    charts = report_data.charts_data
    
    # رسم بياني للمبيعات اليومية
    if 'daily_sales' in charts:
        daily_sales = charts['daily_sales']
        # استخدام البيانات في رسم بياني
        plot_chart(daily_sales['labels'], daily_sales['values'])
```

## أفضل الممارسات

1. **استخدم الفلاتر المناسبة:**
   - حدد الفترة الزمنية بدقة
   - استخدم IDs محددة عند الحاجة

2. **احفظ التقارير بانتظام:**
   - استخدم أسماء ملفات واضحة
   - أضف التاريخ في اسم الملف

3. **استخدم التجميع:**
   - `group_by` لتجميع البيانات
   - `sort_by` لترتيب النتائج

4. **راقب الأداء:**
   - استخدم `limit` للتقارير الكبيرة
   - تجنب الفترات الزمنية الطويلة جداً

5. **استخدم الصيغة المناسبة:**
   - PDF للطباعة
   - Excel للتحليل
   - JSON للبرمجة

## استكشاف الأخطاء

### المشكلة: "لا توجد بيانات"

**الحل:** تحقق من:
1. صحة الفلاتر
2. وجود بيانات في الفترة المحددة
3. صحة IDs المستخدمة

### المشكلة: "التقرير بطيء"

**الحل:**
1. استخدم `limit` لتقليل البيانات
2. قلل الفترة الزمنية
3. استخدم فلاتر أكثر تحديداً

### المشكلة: "فشل التصدير"

**الحل:** تأكد من:
1. تثبيت المكتبات المطلوبة (WeasyPrint للـ PDF)
2. وجود مساحة كافية على القرص
3. صلاحيات الكتابة في مجلد التصدير

---

**تم إنشاء هذا الدليل بواسطة:** Standard El-Joumla Team  
**التاريخ:** 2025-01-15  
**الإصدار:** 5.3.0


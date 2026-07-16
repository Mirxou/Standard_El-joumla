# خطة دمج SalesDialog - "زراعة المخ" 🧠

## الهدف
دمج الواجهة الجديدة (3-Zone Layout) مع المنطق القديم (SalesDialog) في ملف واحد.

## الهيكل المطلوب

### 1. الواجهة (من wholesale_invoice_ui.py)
- Zone 1: Header مع Customer Selection و Insight Cards
- Zone 2: Power Grid (جدول المنتجات)
- Zone 3: Footer مع Logistics و Financials

### 2. المنطق (من sales_dialog.py)
- `save_sale()` - حفظ الفاتورة
- `calculate_totals()` - حساب المجاميع (باستخدام math_utils)
- `add_product_to_sale()` - إضافة منتج
- `load_data()` - تحميل العملاء
- `on_customer_changed()` - معالجة تغيير العميل
- `print_invoice()` - طباعة الفاتورة
- إطلاق AppSignals بعد الحفظ

### 3. الربط
- ربط الأزرار (Save, Save & Print) بدوال الحفظ
- ربط Customer Combo بتحميل العملاء الحقيقيين
- ربط Product Table بـ InvoiceTableModel
- ربط البحث الذكي بإضافة المنتجات

## الخطوات
1. ✅ نسخ احتياطي من الملف القديم
2. ⏳ إنشاء الملف المدمج
3. ⏳ اختبار الوظائف الأساسية
4. ⏳ اختبار الحفظ والطباعة


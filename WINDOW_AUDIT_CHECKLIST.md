# Window Audit Checklist - قائمة فحص النوافذ

## 🎯 الهدف
فحص كل نافذة على حدة للتأكد من عملها بشكل صحيح مع Window Manager الجديد.

---

## 📋 قائمة النوافذ للفحص (19 نافذة)

### ✅ النوافذ الأساسية
- [ ] `reports` - ReportsWindow
- [ ] `dashboard` - DashboardWindow
- [ ] `accounts` - AccountsWindow

### ✅ النوافذ المتقدمة
- [ ] `advanced_reports` - AdvancedReportsWindow
- [ ] `advanced_search` - AdvancedSearchWindow

### ✅ نوافذ المبيعات
- [ ] `quotes` - QuotesWindow
- [ ] `returns` - ReturnsWindow

### ✅ نوافذ المشتريات
- [ ] `purchase_orders` - PurchaseOrdersWindow

### ✅ نوافذ المحاسبة
- [ ] `accounting` - AccountingWindow
- [ ] `payment_plans` - PaymentPlansWindow
- [ ] `payment_dashboard` - PaymentDashboard

### ✅ نوافذ المخزون
- [ ] `physical_counts` - PhysicalCountsWindow
- [ ] `cycle_count` - CycleCountWindow
- [ ] `stock_adjustments` - StockAdjustmentsWindow

### ✅ نوافذ التحليل
- [ ] `abc_analysis` - ABCAnalysisWindow
- [ ] `safety_stock` - SafetyStockWindow
- [ ] `batch_tracking` - BatchTrackingWindow
- [ ] `reorder_recommendations` - ReorderRecommendationsWindow

### ✅ نوافذ النظام
- [ ] `permissions` - PermissionManagementWindow

---

## 🔍 نقاط الفحص لكل نافذة

### 1. التحقق من Attributes
- [ ] `window_key` موجود
- [ ] `window_singleton` موجود
- [ ] `window_title` موجود (اختياري)

### 2. التحقق من __init__
- [ ] `__init__` يستقبل `db_manager` بشكل صحيح
- [ ] `__init__` يستقبل `parent` بشكل صحيح
- [ ] لا توجد أخطاء في `__init__`

### 3. التحقق من التسجيل
- [ ] النافذة مسجلة في `WindowManager`
- [ ] `init_kwargs` صحيحة
- [ ] `singleton` صحيح

### 4. التحقق من الوظائف
- [ ] النافذة تفتح بدون أخطاء
- [ ] النافذة تغلق بدون أخطاء
- [ ] حفظ/استعادة الحالة يعمل

---

## 🚨 المشاكل الشائعة

### المشكلة 1: window_key مفقود
**الحل:** إضافة `window_key = "window_name"` في تعريف الكلاس

### المشكلة 2: init_kwargs خاطئة
**الحل:** التحقق من `create_init_kwargs_provider` في `window_registry.py`

### المشكلة 3: النافذة لا تفتح
**الحل:** التحقق من `__init__` و `init_kwargs`

### المشكلة 4: حفظ الحالة لا يعمل
**الحل:** التحقق من أن النافذة تُغلق بشكل صحيح

---

## 📊 النتائج

سيتم تسجيل نتائج الفحص لكل نافذة هنا.


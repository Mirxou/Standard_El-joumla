# 🎯 خطة عمل تحسين التغطية - Coverage Action Plan

## 📊 الوضع الحالي

- **التغطية**: 28.87%
- **الهدف**: 60%
- **الفجوة**: 31.13%
- **الأسطر المطلوبة**: ~5,200 سطر إضافي

---

## 🚀 المرحلة 1: Core Modules (أسبوع 1-2)

### 1.1 DatabaseManager Tests
**الملف**: `tests/unit/test_database_manager.py` (جديد)
**الهدف**: 60%+ تغطية

**الاختبارات المطلوبة**:
- [ ] `test_initialize()` - تهيئة قاعدة البيانات
- [ ] `test_execute_query()` - استعلامات SELECT
- [ ] `test_execute_non_query()` - INSERT/UPDATE/DELETE
- [ ] `test_execute_scalar()` - قيمة واحدة
- [ ] `test_get_cursor()` - الحصول على cursor
- [ ] `test_transactions()` - المعاملات (commit/rollback)
- [ ] `test_connection_pool()` - Connection Pooling
- [ ] `test_migrations()` - Migrations تلقائية
- [ ] `test_backup()` - النسخ الاحتياطي
- [ ] `test_error_handling()` - معالجة الأخطاء

**التغطية المتوقعة**: +3-5%

---

### 1.2 ErrorDialog Tests
**الملف**: `tests/unit/test_error_dialog.py` (جديد)
**الهدف**: 50%+ تغطية

**الاختبارات المطلوبة**:
- [ ] `test_error_dialog_creation()` - إنشاء الحوار
- [ ] `test_error_display()` - عرض الأخطاء
- [ ] `test_error_categories()` - تصنيف الأخطاء
- [ ] `test_error_notification()` - الإشعارات
- [ ] `test_auto_close()` - الإغلاق التلقائي

**التغطية المتوقعة**: +1-2%

---

## 🚀 المرحلة 2: Models (أسبوع 3-4)

### 2.1 Purchase Model Tests
**الملف**: `tests/unit/test_purchase_model.py` (جديد)
**الهدف**: 60%+ تغطية

**الاختبارات المطلوبة**:
- [ ] `test_purchase_create()` - إنشاء مشتريات
- [ ] `test_purchase_update()` - تحديث المشتريات
- [ ] `test_purchase_delete()` - حذف المشتريات
- [ ] `test_purchase_manager_crud()` - CRUD operations
- [ ] `test_purchase_status()` - حالات المشتريات
- [ ] `test_purchase_items()` - عناصر المشتريات
- [ ] `test_purchase_calculations()` - الحسابات

**التغطية المتوقعة**: +2-3%

---

### 2.2 Payment Model Tests
**الملف**: `tests/unit/test_payment_model.py` (جديد)
**الهدف**: 60%+ تغطية

**الاختبارات المطلوبة**:
- [ ] `test_payment_create()` - إنشاء مدفوعات
- [ ] `test_payment_update()` - تحديث المدفوعات
- [ ] `test_payment_delete()` - حذف المدفوعات
- [ ] `test_payment_manager_crud()` - CRUD operations
- [ ] `test_payment_types()` - أنواع المدفوعات
- [ ] `test_payment_calculations()` - الحسابات

**التغطية المتوقعة**: +2-3%

---

## 🚀 المرحلة 3: Services (أسبوع 5-6)

### 3.1 Inventory Service Tests
**الملف**: `tests/unit/test_inventory_service.py` (جديد)
**الهدف**: 60%+ تغطية

**الاختبارات المطلوبة**:
- [ ] `test_stock_adjustment()` - تعديل المخزون
- [ ] `test_stock_transfer()` - نقل المخزون
- [ ] `test_stock_count()` - جرد المخزون
- [ ] `test_low_stock_alerts()` - تنبيهات المخزون المنخفض
- [ ] `test_reorder_point()` - نقطة إعادة الطلب
- [ ] `test_abc_analysis()` - تحليل ABC

**التغطية المتوقعة**: +3-4%

---

### 3.2 Sales Service Tests
**الملف**: `tests/unit/test_sales_service.py` (جديد)
**الهدف**: 60%+ تغطية

**الاختبارات المطلوبة**:
- [ ] `test_create_sale()` - إنشاء مبيعات
- [ ] `test_update_sale()` - تحديث المبيعات
- [ ] `test_cancel_sale()` - إلغاء المبيعات
- [ ] `test_sale_calculations()` - حسابات المبيعات
- [ ] `test_sale_discounts()` - الخصومات
- [ ] `test_sale_taxes()` - الضرائب

**التغطية المتوقعة**: +3-4%

---

### 3.3 Payment Service Tests
**الملف**: `tests/unit/test_payment_service.py` (جديد)
**الهدف**: 60%+ تغطية

**الاختبارات المطلوبة**:
- [ ] `test_process_payment()` - معالجة المدفوعات
- [ ] `test_refund_payment()` - استرداد المدفوعات
- [ ] `test_payment_plans()` - خطط الدفع
- [ ] `test_payment_calculations()` - حسابات المدفوعات
- [ ] `test_payment_validation()` - التحقق من المدفوعات

**التغطية المتوقعة**: +2-3%

---

## 📊 التغطية المتوقعة بعد كل مرحلة

### بعد المرحلة 1 (أسبوع 2):
- **التغطية**: 32-35%
- **الزيادة**: +3-6%

### بعد المرحلة 2 (أسبوع 4):
- **التغطية**: 36-40%
- **الزيادة**: +4-5%

### بعد المرحلة 3 (أسبوع 6):
- **التغطية**: 42-48%
- **الزيادة**: +8-10%

---

## 🎯 الأهداف النهائية

### الهدف القصير المدى (شهر واحد):
- **التغطية**: 40%+
- **الاختبارات المضافة**: ~40-50 اختبار

### الهدف المتوسط المدى (3 أشهر):
- **التغطية**: 60%+
- **الاختبارات المضافة**: ~100-150 اختبار

---

## ✅ الخطوات التالية الفورية

1. **إنشاء `test_database_manager.py`** (اليوم)
2. **إنشاء `test_error_dialog.py`** (اليوم)
3. **إنشاء `test_purchase_model.py`** (غداً)
4. **إنشاء `test_payment_model.py`** (غداً)
5. **إنشاء `test_inventory_service.py`** (الأسبوع القادم)
6. **إنشاء `test_sales_service.py`** (الأسبوع القادم)
7. **إنشاء `test_payment_service.py`** (الأسبوع القادم)

---

## 📝 ملاحظات

- جميع الاختبارات يجب أن تكون **unit tests** (سريعة ومعزولة)
- استخدام **fixtures** للبيانات المشتركة
- استخدام **mocks** للتبعيات الخارجية
- الهدف: **60%+ تغطية** لكل وحدة

---

**آخر تحديث**: 5 ديسمبر 2025
**التغطية الحالية**: 28.87%
**الهدف**: 60%


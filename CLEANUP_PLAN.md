# Post-Migration Cleanup Plan - خطة تنظيف ما بعد الترحيل

## 🎯 الهدف
تنظيف المشروع من الكود القديم والملفات غير المستخدمة بعد الترحيل إلى Window Manager الجديد.

---

## 📋 الملفات المراد تنظيفها

### 1. ملفات الكود القديمة
- ❌ `src/ui/window_manager.py` - النسخة القديمة (883 سطر)
  - **الحالة:** غير مستخدم (تم استبداله بـ `src/core/window_manager.py`)
  - **الإجراء:** حذف الملف

### 2. ملفات الاختبار القديمة
- ❌ `test_window_manager.py` - اختبارات النسخة القديمة
  - **الحالة:** غير مستخدم (تم استبداله بـ `test_window_manager_integration.py`)
  - **الإجراء:** حذف الملف

### 3. ملفات التوثيق القديمة (يمكن دمجها)
- ⚠️ `src/ui/WINDOW_MANAGER_GUIDE.md` - دليل النسخة القديمة
  - **الحالة:** يحتوي على معلومات قديمة
  - **الإجراء:** تحديث أو حذف
- ⚠️ `WINDOW_MANAGER_ENTERPRISE_EDITION.md` - توثيق النسخة القديمة
- ⚠️ `WINDOW_MANAGER_FINAL_IMPROVEMENTS.md` - توثيق النسخة القديمة
- ⚠️ `WINDOW_MANAGER_INTEGRATION_SUMMARY.md` - ملخص قديم
- ⚠️ `WINDOW_MANAGER_PHANTOM_WINDOW_FIX.md` - إصلاح قديم
- ⚠️ `WINDOW_REFACTORING_GUIDE.md` - دليل قديم
- ⚠️ `WINDOW_REFACTORING_SUMMARY.md` - ملخص قديم

### 4. ملفات التوثيق الحالية (الاحتفاظ بها)
- ✅ `WINDOW_MANAGER_MIGRATION.md` - دليل الترحيل
- ✅ `WINDOW_MANAGER_UPDATE_SUMMARY.md` - ملخص التحديثات
- ✅ `WINDOW_MANAGER_COMPLETE_GUIDE.md` - دليل شامل
- ✅ `WINDOW_MANAGER_TEST_PLAN.md` - خطة الاختبار
- ✅ `WINDOW_MANAGER_TEST_RESULTS.md` - نتائج الاختبار
- ✅ `WINDOW_MANAGER_FINAL_STATUS.md` - الحالة النهائية
- ✅ `AUTO_REGISTRATION_GUIDE.md` - دليل التسجيل التلقائي

---

## 🔍 خطوات التنظيف

### المرحلة 1: التحقق من الاستخدام
1. ✅ التحقق من أن `src/ui/window_manager.py` غير مستخدم
2. ✅ التحقق من أن `test_window_manager.py` غير مستخدم
3. ✅ التحقق من الملفات التوثيقية القديمة

### المرحلة 2: الحذف الآمن
1. حذف `src/ui/window_manager.py`
2. حذف `test_window_manager.py`
3. دمج أو حذف الملفات التوثيقية القديمة

### المرحلة 3: التنظيف النهائي
1. تحديث أي مراجع متبقية
2. التأكد من عدم وجود أخطاء
3. إنشاء ملخص نهائي

---

## ✅ النتيجة المتوقعة

بعد التنظيف:
- ✅ كود أنظف وأسهل للصيانة
- ✅ ملفات أقل
- ✅ توثيق محدث
- ✅ لا توجد ملفات قديمة غير مستخدمة


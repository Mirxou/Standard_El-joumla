# Tests Module Index - فهرس الاختبارات

## 📋 قائمة سريعة

### Unit Tests (25 ملف)
1. `test_math_utils.py` - الأدوات الرياضية
2. `test_logger.py` - نظام السجلات
3. `test_logging_service.py` - خدمة السجلات
4. `test_config_manager.py` - مدير الإعدادات
5. `test_exception_handler.py` - معالج الاستثناءات
6. `test_database_logger_fixes.py` - إصلاحات DatabaseLogger
7. `test_database_logger_extended.py` - DatabaseLogger موسع
8. `test_backup_manager.py` - مدير النسخ الاحتياطي
9. `test_incremental_backup.py` - النسخ الاحتياطي التدريجي
10. `test_encryption_manager.py` - مدير التشفير
11. `test_security_service.py` - خدمة الأمان
12. `test_mfa_service.py` - خدمة MFA
13. `test_rate_limiter.py` - محدود المعدل
14. `test_permission_manager.py` - مدير الصلاحيات
15. `test_cache_manager.py` - مدير التخزين المؤقت
16. `test_caching_service.py` - خدمة التخزين المؤقت
17. `test_product_model.py` - نموذج المنتج
18. `test_sale_model.py` - نموذج المبيعات
19. `test_api_client.py` - عميل API
20. `test_api_modules.py` - وحدات API
21. `test_ai_modules.py` - وحدات AI
22. `test_audit_trail_manager.py` - مدير سجل المراجعة
23. `test_print_manager.py` - مدير الطباعة
24. `test_i18n.py` - نظام الترجمة

### API Tests (3 ملفات)
25. `test_api_integration.py` - تكامل API
26. `test_api_advanced.py` - API المتقدمة
27. `test_api_server.py` - خادم API

### UI Tests (5 ملفات)
28. `test_main_window.py` - النافذة الرئيسية
29. `test_windows.py` - النوافذ
30. `test_dialogs.py` - الحوارات
31. `test_error_dialog.py` - حوار الأخطاء
32. `test_interactions.py` - التفاعلات

### Integration Tests (6 ملفات)
33. `test_database_manager_advanced.py` - مدير قاعدة البيانات المتقدم
34. `test_product_manager_advanced.py` - مدير المنتجات المتقدم
35. `test_customer_manager.py` - مدير العملاء
36. `test_sale_manager.py` - مدير المبيعات
37. `test_api_sync.py` - مزامنة API
38. `test_full_workflows.py` - سير العمل الكاملة

### Configuration Files
39. `conftest.py` - إعدادات pytest والـ fixtures
40. `__init__.py` - تهيئة الحزمة
41. `README.md` - دليل شامل

---

## 📊 الإحصائيات

- **إجمالي الملفات**: 42 ملف Python
- **إجمالي الأسطر**: 5,338 سطر
- **متوسط الأسطر لكل ملف**: 127 سطر
- **Unit Tests**: 25 ملف
- **API Tests**: 3 ملفات
- **UI Tests**: 5 ملفات
- **Integration Tests**: 6 ملفات

---

## 🔍 البحث السريع

### حسب النوع:
- **Unit**: `tests/unit/` (25 ملف)
- **API**: `tests/api/` (3 ملفات)
- **UI**: `tests/ui/` (5 ملفات)
- **Integration**: `tests/integration/` (6 ملفات)

### حسب الوظيفة:
- **Core**: `test_math_utils.py`, `test_logger.py`, `test_config_manager.py`
- **Database**: `test_database_logger_*.py`, `test_backup_manager.py`
- **Security**: `test_encryption_manager.py`, `test_security_service.py`, `test_mfa_service.py`
- **Models**: `test_product_model.py`, `test_sale_model.py`
- **API**: `test_api_*.py`
- **UI**: `test_main_window.py`, `test_windows.py`, `test_dialogs.py`

---

## 💻 أمثلة الاستخدام السريع

### تشغيل جميع الاختبارات
```bash
pytest
```

### تشغيل اختبارات وحدة فقط
```bash
pytest tests/unit -m unit
```

### تشغيل اختبارات تكامل فقط
```bash
pytest tests/integration -m integration
```

### تشغيل مع التغطية
```bash
pytest --cov=src --cov-report=term-missing
```

---

## 🔗 روابط سريعة

- [README.md](README.md) - دليل شامل
- [conftest.py](conftest.py) - الـ fixtures المشتركة
- [../src/README.md](../src/README.md) - دليل الكود المصدري

---

## ✅ الحالة

- ✅ جميع الاختبارات موثقة بشكل جيد
- ✅ استخدام pytest بشكل صحيح
- ✅ تنظيم جيد للاختبارات
- ✅ fixtures مشتركة ومنظمة
- ✅ تغطية شاملة للميزات


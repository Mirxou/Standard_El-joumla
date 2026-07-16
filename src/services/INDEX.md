# Services Module Index - فهرس الخدمات

## 📋 قائمة سريعة بالخدمات (57 خدمة)

### المبيعات والمشتريات (5 خدمات)
1. `sales_service.py` - خدمة المبيعات
2. `purchase_service.py` - خدمة المشتريات
3. `purchase_order_service.py` - خدمة أوامر الشراء
4. `quote_service.py` - خدمة عروض الأسعار
5. `return_service.py` - خدمة المرتجعات

### المخزون (5 خدمات)
6. `inventory_service.py` - خدمة المخزون الأساسية
7. `inventory_service_enhanced.py` - خدمة مخزون محسّنة
8. `inventory_count_service.py` - خدمة الجرد الفعلي
9. `inventory_optimization_service.py` - خدمة تحسين المخزون
10. `cycle_count_service.py` - خدمة الجرد الدوري

### المالية (5 خدمات)
11. `payment_service.py` ⭐ - خدمة المدفوعات (1,215 سطر)
12. `payment_plan_service.py` - خدمة خطط الدفع
13. `billing_service.py` - خدمة الفوترة
14. `accounting_service.py` - خدمة المحاسبة
15. `recurring_invoice_service.py` - خدمة الفواتير الدورية

### التقارير (3 خدمات)
16. `report_exporter.py` ⭐⭐ - خدمة تصدير التقارير (1,410 سطر - أكبر ملف)
17. `report_generator.py` - مولد التقارير (899 سطر)
18. `pdf_export_service.py` - خدمة تصدير PDF

### الطباعة (3 خدمات)
19. `invoice_print_service.py` - خدمة طباعة الفواتير
20. `print_service.py` - خدمة الطباعة العامة
21. `printing_service.py` - خدمة طباعة بسيطة

### المستخدمين والصلاحيات (5 خدمات)
22. `user_service.py` - خدمة المستخدمين (640 سطر)
23. `rbac_service.py` - خدمة التحكم في الوصول (530 سطر)
24. `permission_service.py` - خدمة الصلاحيات (440 سطر)
25. `security_service.py` - خدمة الأمان
26. `mfa_service.py` - خدمة المصادقة متعددة العوامل

### البحث والفلترة (3 خدمات)
27. `search_service.py` - خدمة البحث
28. `advanced_search_service.py` - خدمة بحث متقدمة
29. `filter_manager.py` - مدير الفلاتر

### لوحات المعلومات (2 خدمات)
30. `dashboard_service.py` - خدمة لوحات المعلومات (486 سطر)
31. `performance_service.py` - خدمة الأداء (753 سطر)

### الإشعارات والتذكيرات (3 خدمات)
32. `notification_service.py` - خدمة الإشعارات (594 سطر)
33. `reminder_service.py` - خدمة التذكيرات
34. `email_service.py` - خدمة البريد الإلكتروني

### الموردين (3 خدمات)
35. `vendor_service.py` - خدمة الموردين
36. `vendor_portal.py` - بوابة الموردين (430 سطر)
37. `vendor_rating_service.py` - خدمة تقييم الموردين

### التسويق والعلاقات (5 خدمات)
38. `marketing_service.py` - خدمة التسويق (548 سطر)
39. `marketing_automation_service.py` - خدمة أتمتة التسويق
40. `crm_service.py` - خدمة إدارة علاقات العملاء (445 سطر)
41. `loyalty_service.py` - خدمة برامج الولاء (343 سطر)
42. `churn_service.py` - خدمة تحليل التسرب

### المنتجات (1 خدمة)
43. `product_service_enhanced.py` - خدمة منتجات محسّنة (~33KB)

### النسخ الاحتياطي (1 خدمة)
44. `backup_service.py` - خدمة النسخ الاحتياطي (693 سطر)

### المراجعة والسجلات (2 خدمات)
45. `audit_service.py` - خدمة المراجعة (350 سطر)
46. `audit_log_service.py` - خدمة سجلات المراجعة (655 سطر)

### الاستيراد والتصدير (1 خدمة)
47. `import_export_service.py` - خدمة الاستيراد والتصدير (541 سطر)

### خدمات أخرى (8 خدمات)
48. `cache_service.py` - خدمة التخزين المؤقت (314 سطر)
49. `cache_backends.py` - واجهات التخزين المؤقت
50. `image_manager_service.py` - خدمة إدارة الصور (349 سطر)
51. `encryption_service.py` - خدمة التشفير
52. `task_scheduler_service.py` - خدمة جدولة المهام
53. `scheduler_service.py` - خدمة جدولة بسيطة
54. `notes_service.py` - خدمة الملاحظات
55. `support_service.py` - خدمة الدعم
56. `ai_service.py` - خدمة الذكاء الاصطناعي (345 سطر)
57. `smart_assistant.py` - مساعد ذكي

---

## 📊 الإحصائيات

- **إجمالي الخدمات**: 57 خدمة
- **أكبر ملف**: `report_exporter.py` (1,410 سطر)
- **أصغر ملف**: `mfa_service.py` (59 سطر)
- **متوسط الأسطر**: ~500-600 سطر لكل خدمة

---

## 🔍 البحث السريع

### حسب الوظيفة:
- **CRUD Operations**: جميع الخدمات
- **Reports**: `report_exporter.py`, `report_generator.py`, `pdf_export_service.py`
- **Printing**: `invoice_print_service.py`, `print_service.py`, `printing_service.py`
- **Security**: `user_service.py`, `rbac_service.py`, `permission_service.py`, `security_service.py`, `mfa_service.py`
- **Search**: `search_service.py`, `advanced_search_service.py`, `filter_manager.py`
- **Analytics**: `dashboard_service.py`, `performance_service.py`, `churn_service.py`

### حسب الحجم:
- **كبيرة (> 1000 سطر)**: `report_exporter.py`, `payment_service.py`
- **متوسطة (500-1000 سطر)**: `report_generator.py`, `user_service.py`, `rbac_service.py`, `performance_service.py`, `notification_service.py`, `backup_service.py`, `audit_log_service.py`
- **صغيرة (< 500 سطر)**: باقي الخدمات

---

## 💻 أمثلة الاستخدام السريع

### خدمة المبيعات
```python
from src.services.sales_service import SalesService

sales_service = SalesService(db_manager, logger)
invoice_id = sales_service.create_invoice(customer_id=1, items=[...])
```

### خدمة المخزون
```python
from src.services.inventory_service import InventoryService

inventory_service = InventoryService(db_manager, logger)
low_stock = inventory_service.get_low_stock_products()
```

### خدمة التقارير
```python
from src.services.report_exporter import ReportExporter

report_exporter = ReportExporter(db_manager)
report = report_exporter.generate_sales_report(filters)
```

### خدمة المدفوعات
```python
from src.services.payment_service import PaymentService

payment_service = PaymentService(db_manager, logger)
payment = payment_service.create_payment(customer_id=1, amount=1000)
```

---

## 🔗 روابط سريعة

- [README.md](README.md) - دليل شامل
- [../models/README.md](../models/README.md) - دليل النماذج
- [../core/README.md](../core/README.md) - دليل الوحدات الأساسية
- [../ui/README.md](../ui/README.md) - دليل واجهات المستخدم

---

## ✅ الحالة

- ✅ جميع الخدمات موثقة بشكل جيد
- ✅ استخدام نمط Service Pattern بشكل متسق
- ✅ تكامل جيد مع النماذج وقاعدة البيانات
- ✅ دعم كامل للعمليات الأساسية
- ✅ تقارير وتحليلات شاملة


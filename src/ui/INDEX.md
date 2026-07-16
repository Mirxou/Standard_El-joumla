# UI Module Index - فهرس واجهات المستخدم

## 📋 قائمة سريعة

### النوافذ (23 نافذة)
1. `windows/main_window.py` ⭐ - النافذة الرئيسية
2. `windows/dashboard_window.py` - لوحة المعلومات
3. `windows/smart_dashboard_window.py` - لوحة معلومات ذكية
4. `windows/reports_window.py` - التقارير
5. `windows/advanced_reports_window.py` - التقارير المتقدمة
6. `windows/advanced_search_window.py` - البحث المتقدم
7. `windows/accounting_window.py` - المحاسبة
8. `windows/accounts_window.py` - الحسابات
9. `windows/payment_dashboard.py` - لوحة المدفوعات
10. `windows/payment_plans_window.py` - خطط الدفع
11. `windows/purchase_orders_window.py` - أوامر الشراء
12. `windows/quotes_window.py` - عروض الأسعار
13. `windows/returns_window.py` - المرتجعات
14. `windows/physical_counts_window.py` - الجرد الفعلي
15. `windows/cycle_count_window.py` - الجرد الدوري
16. `windows/stock_adjustments_window.py` - تعديلات المخزون
17. `windows/safety_stock_window.py` - المخزون الآمن
18. `windows/reorder_recommendations_window.py` - توصيات إعادة الطلب
19. `windows/abc_analysis_window.py` - تحليل ABC
20. `windows/batch_tracking_window.py` - تتبع الدفعات
21. `windows/permission_management_window.py` - إدارة الصلاحيات
22. `windows/template_editor_window.py` - محرر القوالب

### الحوارات (24 حوار)
23. `dialogs/login_dialog.py` - تسجيل الدخول
24. `dialogs/forgot_password_dialog.py` - استعادة كلمة المرور
25. `dialogs/product_dialog.py` - المنتج
26. `dialogs/sales_dialog.py` ⭐ - المبيعات (3-Zone Layout)
27. `dialogs/customer_form_dialog.py` - العميل
28. `dialogs/customer_management_dialog.py` - إدارة العملاء
29. `dialogs/supplier_form_dialog.py` - المورد
30. `dialogs/supplier_management_dialog.py` - إدارة الموردين
31. `dialogs/purchase_order_dialog.py` - أمر الشراء
32. `dialogs/payment_dialog.py` - الدفع
33. `dialogs/payment_plan_dialog.py` - خطة الدفع
34. `dialogs/installment_payment_dialog.py` - دفع الأقساط
35. `dialogs/adjust_stock_dialog.py` - تعديل المخزون
36. `dialogs/transfer_stock_dialog.py` - نقل المخزون
37. `dialogs/receiving_dialog.py` - الاستلام
38. `dialogs/category_dialog.py` - الفئة
39. `dialogs/category_form_dialog.py` - نموذج الفئة
40. `dialogs/batch_dialog.py` - الدفعة
41. `dialogs/safety_stock_dialog.py` - المخزون الآمن
42. `dialogs/count_details_dialog.py` - تفاصيل الجرد
43. `dialogs/contacts_report_dialog.py` - تقرير جهات الاتصال
44. `dialogs/theme_selector_dialog.py` - اختيار السمة
45. `dialogs/encryption_dialog.py` - التشفير

### الويدجتات (1 ويدجت)
46. `widgets/sales_chart.py` - رسم بياني للمبيعات

### النماذج (2 نموذج)
47. `models/inventory_table_model.py` - نموذج جدول المخزون
48. `models/invoice_table_model.py` - نموذج جدول الفواتير

### المندوبون (2 مندوب)
49. `delegates/action_delegate.py` - مندوب الإجراءات
50. `delegates/modern_action_delegate.py` - مندوب إجراءات حديث

### العناصر (3 عنصر)
51. `items/draggable_image_item.py` - صورة قابلة للسحب
52. `items/draggable_table_item.py` - جدول قابل للسحب
53. `items/draggable_text_item.py` - نص قابل للسحب

### الإدارة (5 لوحات)
54. `admin/audit_viewer.py` - عارض المراجعة
55. `admin/cache_stats_panel.py` - إحصائيات التخزين المؤقت
56. `admin/performance_panel.py` - لوحة الأداء
57. `admin/roles_manager.py` - مدير الأدوار
58. `admin/sessions_panel.py` - لوحة الجلسات

### الملفات الرئيسية (7 ملفات)
59. `theme_manager.py` ⭐ - مدير السمات (680 سطر)
60. `notifications_manager.py` ⭐⭐ - مدير الإشعارات (763 سطر)
61. `performance_dashboard.py` - لوحة الأداء (536 سطر)
62. `quick_actions_toolbar.py` - شريط الإجراءات السريعة (425 سطر)
63. `shortcuts_manager.py` - مدير الاختصارات (340 سطر)
64. `setup_wizard.py` - معالج الإعداد (541 سطر)
65. `system_management_window.py` ⭐⭐ - إدارة النظام (843 سطر)

### الأنماط (13 ملف QSS)
66. `styles/main.qss` - الأنماط الرئيسية
67. `styles/variables.qss` - المتغيرات
68. `styles/buttons.qss` - أنماط الأزرار
69. `styles/dialogs.qss` - أنماط الحوارات
70. `styles/tables.qss` - أنماط الجداول
71. `styles/inputs.qss` - أنماط حقول الإدخال
72. `styles/tabs.qss` - أنماط التبويبات
73. `styles/scrollbars.qss` - أنماط أشرطة التمرير
74. `styles/progress.qss` - أنماط أشرطة التقدم
75. `styles/general.qss` - الأنماط العامة
76. `styles/main.py` - تحميل الأنماط
77. `styles/icon_loader.py` - تحميل الأيقونات

---

## 📊 الإحصائيات

- **إجمالي الملفات**: 74 ملف Python + 13 ملف QSS
- **النوافذ**: 23 نافذة
- **الحوارات**: 24 حوار
- **الويدجتات**: 1 ويدجت
- **النماذج**: 2 نموذج
- **المندوبون**: 2 مندوب
- **العناصر**: 3 عنصر
- **لوحات الإدارة**: 5 لوحات
- **الملفات الرئيسية**: 7 ملفات
- **الأنماط**: 13 ملف QSS

---

## 🔍 البحث السريع

### حسب الوظيفة:
- **Windows**: `windows/` (23 نافذة)
- **Dialogs**: `dialogs/` (24 حوار)
- **Widgets**: `widgets/` (1 ويدجت)
- **Models**: `models/` (2 نموذج)
- **Delegates**: `delegates/` (2 مندوب)
- **Items**: `items/` (3 عنصر)
- **Admin**: `admin/` (5 لوحات)
- **Styles**: `styles/` (13 ملف QSS)

### حسب الحجم:
- **كبيرة (> 800 سطر)**: `system_management_window.py`, `notifications_manager.py`, `main_window.py`
- **متوسطة (400-800 سطر)**: `theme_manager.py`, `setup_wizard.py`, `performance_dashboard.py`, `quick_actions_toolbar.py`
- **صغيرة (< 400 سطر)**: باقي الملفات

---

## 💻 أمثلة الاستخدام السريع

### Theme Manager
```python
from src.ui.theme_manager import get_theme_manager

theme_manager = get_theme_manager()
theme_manager.set_theme("dark")
```

### Notifications Manager
```python
from src.ui.notifications_manager import get_notifications_manager
from src.ui.notifications_manager import NotificationType

notifications = get_notifications_manager()
notifications.show_notification(
    "عنوان",
    "رسالة",
    NotificationType.INFO
)
```

### Shortcuts Manager
```python
from src.ui.shortcuts_manager import ShortcutsManager

shortcuts = ShortcutsManager()
shortcuts.register_shortcut("Ctrl+N", self.new_action)
```

---

## 🔗 روابط سريعة

- [README.md](README.md) - دليل شامل
- [../services/README.md](../services/README.md) - دليل الخدمات
- [../models/README.md](../models/README.md) - دليل النماذج
- [../core/README.md](../core/README.md) - دليل الوحدات الأساسية

---

## ✅ الحالة

- ✅ جميع الواجهات موثقة بشكل جيد
- ✅ استخدام PySide6 بشكل صحيح
- ✅ دعم كامل للغة العربية (RTL)
- ✅ تصميم حديث ومتجاوب
- ✅ تكامل جيد مع الخدمات والنماذج


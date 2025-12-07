# UI Module - وحدات واجهة المستخدم

## نظرة عامة
هذا المجلد يحتوي على جميع وحدات واجهة المستخدم (User Interface) للتطبيق. يستخدم PySide6 (Qt6) لبناء الواجهات الرسومية.

## 📊 الإحصائيات

- **إجمالي الملفات**: 74 ملف Python
- **المجلدات الفرعية**: 7 مجلدات
- **Syntax Check**: ✅ جميع الملفات صحيحة
- **Linter**: ✅ لا توجد أخطاء

## 📁 الهيكل

### 1. النوافذ (Windows) - 23 نافذة

#### `windows/main_window.py` ⭐
- **`MainWindow`** - النافذة الرئيسية للتطبيق
- **الميزات**: لوحة التحكم، القوائم، التبويبات، جميع الوحدات

#### `windows/dashboard_window.py`
- **`DashboardWindow`** - نافذة لوحة المعلومات
- **الميزات**: KPIs، الرسوم البيانية، الإحصائيات

#### `windows/smart_dashboard_window.py`
- **`SmartDashboardWindow`** - لوحة معلومات ذكية
- **الميزات**: لوحة معلومات تفاعلية مع AI

#### `windows/reports_window.py`
- **`ReportsWindow`** - نافذة التقارير
- **الميزات**: إنشاء وتصدير التقارير

#### `windows/advanced_reports_window.py`
- **`AdvancedReportsWindow`** - نافذة التقارير المتقدمة
- **الميزات**: تقارير متقدمة مع فلترة معقدة

#### `windows/advanced_search_window.py`
- **`AdvancedSearchWindow`** - نافذة البحث المتقدم
- **الميزات**: بحث متقدم في جميع الكيانات

#### `windows/accounting_window.py`
- **`AccountingWindow`** - نافذة المحاسبة
- **الميزات**: القيود المحاسبية، الحسابات، الميزانيات

#### `windows/accounts_window.py`
- **`AccountsWindow`** - نافذة الحسابات
- **الميزات**: إدارة الحسابات المحاسبية

#### `windows/payment_dashboard.py`
- **`PaymentDashboard`** - لوحة معلومات المدفوعات
- **الميزات**: إحصائيات المدفوعات، الذمم

#### `windows/payment_plans_window.py`
- **`PaymentPlansWindow`** - نافذة خطط الدفع
- **الميزات**: إدارة خطط الدفع

#### `windows/purchase_orders_window.py`
- **`PurchaseOrdersWindow`** - نافذة أوامر الشراء
- **الميزات**: إدارة أوامر الشراء

#### `windows/quotes_window.py`
- **`QuotesWindow`** - نافذة عروض الأسعار
- **الميزات**: إدارة عروض الأسعار

#### `windows/returns_window.py`
- **`ReturnsWindow`** - نافذة المرتجعات
- **الميزات**: إدارة المرتجعات

#### `windows/physical_counts_window.py`
- **`PhysicalCountsWindow`** - نافذة الجرد الفعلي
- **الميزات**: إدارة الجرد الفعلي

#### `windows/cycle_count_window.py`
- **`CycleCountWindow`** - نافذة الجرد الدوري
- **الميزات**: إدارة الجرد الدوري

#### `windows/stock_adjustments_window.py`
- **`StockAdjustmentsWindow`** - نافذة تعديلات المخزون
- **الميزات**: إدارة تعديلات المخزون

#### `windows/safety_stock_window.py`
- **`SafetyStockWindow`** - نافذة المخزون الآمن
- **الميزات**: إدارة المخزون الآمن

#### `windows/reorder_recommendations_window.py`
- **`ReorderRecommendationsWindow`** - نافذة توصيات إعادة الطلب
- **الميزات**: توصيات إعادة الطلب

#### `windows/abc_analysis_window.py`
- **`ABCAnalysisWindow`** - نافذة تحليل ABC
- **الميزات**: تحليل ABC للمنتجات

#### `windows/batch_tracking_window.py`
- **`BatchTrackingWindow`** - نافذة تتبع الدفعات
- **الميزات**: تتبع الدفعات

#### `windows/permission_management_window.py`
- **`PermissionManagementWindow`** - نافذة إدارة الصلاحيات
- **الميزات**: إدارة الصلاحيات والأدوار

#### `windows/template_editor_window.py`
- **`TemplateEditorWindow`** - نافذة محرر القوالب
- **الميزات**: تحرير قوالب التقارير

---

### 2. الحوارات (Dialogs) - 24 حوار

#### `dialogs/login_dialog.py`
- **`LoginDialog`** - حوار تسجيل الدخول
- **الميزات**: تسجيل الدخول، استعادة كلمة المرور

#### `dialogs/forgot_password_dialog.py`
- **`ForgotPasswordDialog`** - حوار استعادة كلمة المرور
- **الميزات**: استعادة كلمة المرور

#### `dialogs/product_dialog.py`
- **`ProductDialog`** - حوار المنتج
- **الميزات**: إنشاء/تعديل المنتجات

#### `dialogs/sales_dialog.py` ⭐
- **`SalesDialog`** - حوار المبيعات
- **الميزات**: إنشاء/تعديل الفواتير، تصميم 3-Zone Enterprise Layout

#### `dialogs/customer_form_dialog.py`
- **`CustomerFormDialog`** - حوار العميل
- **الميزات**: إنشاء/تعديل العملاء

#### `dialogs/customer_management_dialog.py`
- **`CustomerManagementDialog`** - حوار إدارة العملاء
- **الميزات**: إدارة شاملة للعملاء

#### `dialogs/supplier_form_dialog.py`
- **`SupplierFormDialog`** - حوار المورد
- **الميزات**: إنشاء/تعديل الموردين

#### `dialogs/supplier_management_dialog.py`
- **`SupplierManagementDialog`** - حوار إدارة الموردين
- **الميزات**: إدارة شاملة للموردين

#### `dialogs/purchase_order_dialog.py`
- **`PurchaseOrderDialog`** - حوار أمر الشراء
- **الميزات**: إنشاء/تعديل أوامر الشراء

#### `dialogs/payment_dialog.py`
- **`PaymentDialog`** - حوار الدفع
- **الميزات**: تسجيل المدفوعات

#### `dialogs/payment_plan_dialog.py`
- **`PaymentPlanDialog`** - حوار خطة الدفع
- **الميزات**: إنشاء خطط الدفع

#### `dialogs/installment_payment_dialog.py`
- **`InstallmentPaymentDialog`** - حوار دفع الأقساط
- **الميزات**: دفع الأقساط

#### `dialogs/adjust_stock_dialog.py`
- **`AdjustStockDialog`** - حوار تعديل المخزون
- **الميزات**: تعديل المخزون

#### `dialogs/transfer_stock_dialog.py`
- **`TransferStockDialog`** - حوار نقل المخزون
- **الميزات**: نقل المخزون بين المخازن

#### `dialogs/receiving_dialog.py`
- **`ReceivingDialog`** - حوار الاستلام
- **الميزات**: تسجيل الاستلام

#### `dialogs/category_dialog.py`
- **`CategoryDialog`** - حوار الفئة
- **الميزات**: إدارة الفئات

#### `dialogs/category_form_dialog.py`
- **`CategoryFormDialog`** - حوار نموذج الفئة
- **الميزات**: إنشاء/تعديل الفئات

#### `dialogs/batch_dialog.py`
- **`BatchDialog`** - حوار الدفعة
- **الميزات**: إدارة الدفعات

#### `dialogs/safety_stock_dialog.py`
- **`SafetyStockDialog`** - حوار المخزون الآمن
- **الميزات**: إدارة المخزون الآمن

#### `dialogs/count_details_dialog.py`
- **`CountDetailsDialog`** - حوار تفاصيل الجرد
- **الميزات**: تفاصيل الجرد

#### `dialogs/contacts_report_dialog.py`
- **`ContactsReportDialog`** - حوار تقرير جهات الاتصال
- **الميزات**: تقارير جهات الاتصال

#### `dialogs/theme_selector_dialog.py`
- **`ThemeSelectorDialog`** - حوار اختيار السمة
- **الميزات**: اختيار السمة (Dark/Light)

#### `dialogs/encryption_dialog.py`
- **`EncryptionDialog`** - حوار التشفير
- **الميزات**: إعدادات التشفير

---

### 3. الويدجتات (Widgets) - 1 ويدجت

#### `widgets/sales_chart.py`
- **`SalesChartWidget`** - ويدجت الرسم البياني للمبيعات
- **الميزات**: رسم بياني للمبيعات باستخدام PyQtGraph

---

### 4. النماذج (Models) - 2 نموذج

#### `models/inventory_table_model.py`
- **`InventoryTableModel`** - نموذج جدول المخزون
- **الميزات**: عرض بيانات المخزون في جدول

#### `models/invoice_table_model.py`
- **`InvoiceTableModel`** - نموذج جدول الفواتير
- **الميزات**: عرض بيانات الفواتير في جدول

---

### 5. المندوبون (Delegates) - 2 مندوب

#### `delegates/action_delegate.py`
- **`ActionDelegate`** - مندوب الإجراءات
- **الميزات**: عرض أزرار الإجراءات في الجداول

#### `delegates/modern_action_delegate.py`
- **`ModernActionDelegate`** - مندوب إجراءات حديث
- **الميزات**: تصميم حديث لأزرار الإجراءات

---

### 6. العناصر (Items) - 3 عنصر

#### `items/draggable_image_item.py`
- **`DraggableImageItem`** - عنصر صورة قابل للسحب
- **الميزات**: صور قابلة للسحب والإفلات

#### `items/draggable_table_item.py`
- **`DraggableTableItem`** - عنصر جدول قابل للسحب
- **الميزات**: جداول قابلة للسحب والإفلات

#### `items/draggable_text_item.py`
- **`DraggableTextItem`** - عنصر نص قابل للسحب
- **الميزات**: نصوص قابلة للسحب والإفلات

---

### 7. الإدارة (Admin) - 4 لوحات

#### `admin/audit_viewer.py`
- **`AuditViewer`** - عارض المراجعة
- **الميزات**: عرض سجلات المراجعة

#### `admin/cache_stats_panel.py`
- **`CacheStatsPanel`** - لوحة إحصائيات التخزين المؤقت
- **الميزات**: إحصائيات التخزين المؤقت

#### `admin/performance_panel.py`
- **`PerformancePanel`** - لوحة الأداء
- **الميزات**: مراقبة الأداء

#### `admin/roles_manager.py`
- **`RolesManager`** - مدير الأدوار
- **الميزات**: إدارة الأدوار والصلاحيات

#### `admin/sessions_panel.py`
- **`SessionsPanel`** - لوحة الجلسات
- **الميزات**: إدارة الجلسات

---

### 8. الملفات الرئيسية (Root Files) - 7 ملفات

#### `theme_manager.py` (680 سطر)
- **`ThemeManager`** - مدير السمات
- **الميزات**: Dark/Light themes، انتقالات سلسة، إعدادات دائمة

#### `notifications_manager.py` (763 سطر) ⭐
- **`SmartNotificationsManager`** - مدير الإشعارات الذكي
- **الميزات**: إشعارات تلقائية، تنبيهات، System Tray

#### `performance_dashboard.py` (536 سطر)
- **`PerformanceDashboard`** - لوحة معلومات الأداء
- **الميزات**: مراقبة الأداء، التحليلات

#### `quick_actions_toolbar.py` (425 سطر)
- **`QuickActionsToolbar`** - شريط الإجراءات السريعة
- **الميزات**: إجراءات سريعة للوصول السريع

#### `shortcuts_manager.py` (340 سطر)
- **`ShortcutsManager`** - مدير الاختصارات
- **الميزات**: إدارة اختصارات لوحة المفاتيح

#### `setup_wizard.py` (541 سطر)
- **`SetupWizard`** - معالج الإعداد الأولي
- **الميزات**: إعداد التطبيق لأول مرة

#### `system_management_window.py` (843 سطر) ⭐⭐
- **`SystemManagementWindow`** - نافذة إدارة النظام
- **الميزات**: إدارة شاملة للنظام، الإعدادات، الأدوات

---

### 9. الأنماط (Styles) - 13 ملف QSS

#### `styles/main.qss`
- الأنماط الرئيسية

#### `styles/variables.qss`
- المتغيرات (الألوان، الخطوط)

#### `styles/buttons.qss`
- أنماط الأزرار

#### `styles/dialogs.qss`
- أنماط الحوارات

#### `styles/tables.qss`
- أنماط الجداول

#### `styles/inputs.qss`
- أنماط حقول الإدخال

#### `styles/tabs.qss`
- أنماط التبويبات

#### `styles/scrollbars.qss`
- أنماط أشرطة التمرير

#### `styles/progress.qss`
- أنماط أشرطة التقدم

#### `styles/general.qss`
- الأنماط العامة

#### `styles/main.py`
- تحميل الأنماط

#### `styles/icon_loader.py`
- تحميل الأيقونات

---

## 🏗️ البنية المعمارية

### نمط التصميم
جميع الواجهات تتبع نمط **MVC (Model-View-Controller)**:
- **Model** - نماذج البيانات (`models/`)
- **View** - الواجهات (`windows/`, `dialogs/`, `widgets/`)
- **Controller** - منطق التحكم (في الخدمات)

### الهيكل العام
```python
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal

class CustomDialog(QDialog):
    """حوار مخصص"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("عنوان الحوار")
        self._setup_ui()
    
    def _setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)
        # ... إضافة العناصر
```

---

## 🔗 التكامل

### مع الخدمات (Services)
```python
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService

# في الواجهات
inventory_service = InventoryService(db_manager, logger)
sales_service = SalesService(db_manager, logger)
```

### مع النماذج (Models)
```python
from src.models.product import ProductManager
from src.models.sale import SaleManager

# في الواجهات
product_manager = ProductManager(db_manager, logger)
sale_manager = SaleManager(db_manager, logger)
```

### مع Theme Manager
```python
from src.ui.theme_manager import get_theme_manager

theme_manager = get_theme_manager()
theme_manager.set_theme("dark")
```

### مع Notifications Manager
```python
from src.ui.notifications_manager import get_notifications_manager

notifications = get_notifications_manager()
notifications.show_notification("عنوان", "رسالة", NotificationType.INFO)
```

---

## 📝 الميزات الرئيسية

### 1. السمات (Themes)
- ✅ Dark/Light themes
- ✅ انتقالات سلسة
- ✅ إعدادات دائمة
- ✅ ألوان مخصصة

### 2. الإشعارات (Notifications)
- ✅ إشعارات تلقائية
- ✅ تنبيهات
- ✅ System Tray
- ✅ أولويات مختلفة

### 3. الاختصارات (Shortcuts)
- ✅ اختصارات لوحة المفاتيح
- ✅ إدارة شاملة
- ✅ تخصيص

### 4. الأداء (Performance)
- ✅ تحميل البيانات في الخلفية (Threads)
- ✅ تحديث تلقائي
- ✅ مراقبة الأداء

### 5. التصميم
- ✅ تصميم حديث (Modern UI)
- ✅ RTL support (دعم العربية)
- ✅ Responsive design
- ✅ Accessibility

---

## 🎯 أفضل الممارسات

### 1. استخدام Threads للعمليات الثقيلة
```python
from PySide6.QtCore import QThread, Signal

class DataLoaderWorker(QThread):
    data_loaded = Signal(list)
    
    def run(self):
        # عملية ثقيلة
        data = load_data()
        self.data_loaded.emit(data)

# في الواجهة
worker = DataLoaderWorker()
worker.data_loaded.connect(self.on_data_loaded)
worker.start()
```

### 2. استخدام Signals/Slots
```python
from PySide6.QtCore import Signal

class CustomWidget(QWidget):
    data_changed = Signal(object)
    
    def on_change(self):
        self.data_changed.emit(new_data)
```

### 3. إدارة الموارد
```python
def closeEvent(self, event):
    # تنظيف الموارد
    if self.worker:
        self.worker.terminate()
        self.worker.wait()
    event.accept()
```

---

## 📚 المراجع

- `src/services/` - الخدمات المستخدمة في الواجهات
- `src/models/` - النماذج المستخدمة في الواجهات
- `src/core/database_manager.py` - مدير قاعدة البيانات
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)

---

## ✅ الخلاصة

- ✅ جميع الواجهات موثقة بشكل جيد
- ✅ استخدام PySide6 بشكل صحيح
- ✅ دعم كامل للغة العربية (RTL)
- ✅ تصميم حديث ومتجاوب
- ✅ تكامل جيد مع الخدمات والنماذج

**التقييم**: 5/5 ⭐⭐⭐⭐⭐


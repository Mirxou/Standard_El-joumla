# Services Module - وحدات الخدمات

## نظرة عامة
هذا المجلد يحتوي على جميع الخدمات (Services) للتطبيق. الخدمات تحتوي على منطق العمل (Business Logic) وتتكامل مع النماذج (Models) وقاعدة البيانات.

## 📊 الإحصائيات

- **إجمالي الملفات**: 55 ملف Python
- **إجمالي الأسطر**: ~50,000+ سطر (تقديري)
- **أكبر ملف**: `report_exporter.py` (1,410 سطر)
- **Syntax Check**: ✅ جميع الملفات صحيحة
- **Linter**: ✅ لا توجد أخطاء

## 📁 التصنيف

### 1. خدمات المبيعات والمشتريات (Sales & Purchases)

#### `sales_service.py` (322 سطر)
- **`SalesService`** - خدمة المبيعات
- **الميزات**: إنشاء الفواتير، إدارة الطلبات، التقارير

#### `purchase_service.py` (168 سطر)
- **`PurchaseService`** - خدمة المشتريات
- **الميزات**: إدارة المشتريات، تتبع الاستلام

#### `purchase_order_service.py` (567 سطر)
- **`PurchaseOrderService`** - خدمة أوامر الشراء
- **الميزات**: إنشاء أوامر الشراء، الموافقات، التتبع

#### `quote_service.py` (~19KB)
- **`QuoteService`** - خدمة عروض الأسعار
- **الميزات**: إنشاء عروض الأسعار، التحويل إلى فاتورة

#### `return_service.py` (~24KB)
- **`ReturnService`** - خدمة المرتجعات
- **الميزات**: إدارة المرتجعات، استرداد المخزون

---

### 2. خدمات المخزون (Inventory Services)

#### `inventory_service.py` (571 سطر)
- **`InventoryService`** - خدمة المخزون الأساسية
- **الميزات**: إدارة المخزون، حركات المخزون، التنبيهات

#### `inventory_service_enhanced.py` (~25KB)
- **`InventoryServiceEnhanced`** - خدمة مخزون محسّنة
- **الميزات**: ميزات إضافية للمخزون

#### `inventory_count_service.py` (751 سطر)
- **`InventoryCountService`** - خدمة الجرد الفعلي
- **الميزات**: إدارة الجرد الفعلي، حساب الفروقات

#### `inventory_optimization_service.py` (592 سطر)
- **`InventoryOptimizationService`** - خدمة تحسين المخزون
- **الميزات**: حساب نقاط إعادة الطلب، تحليل ABC

#### `cycle_count_service.py` (249 سطر)
- **`CycleCountService`** - خدمة الجرد الدوري
- **الميزات**: إدارة الجرد الدوري، الجدولة

---

### 3. الخدمات المالية (Financial Services)

#### `payment_service.py` (1,215 سطر) ⭐
- **`PaymentService`** - خدمة المدفوعات
- **الميزات**: إدارة المدفوعات، الذمم المدينة والدائنة، التقارير المالية

#### `payment_plan_service.py` (~20KB)
- **`PaymentPlanService`** - خدمة خطط الدفع
- **الميزات**: إدارة خطط الدفع، الجدولة

#### `billing_service.py` (6.6KB)
- **`BillingService`** - خدمة الفوترة
- **الميزات**: توليد الفواتير، إدارة الفواتير الدورية

#### `accounting_service.py` (~21KB)
- **`AccountingService`** - خدمة المحاسبة
- **الميزات**: القيود المحاسبية، الحسابات، الميزانيات

#### `recurring_invoice_service.py` (77 سطر)
- **`RecurringInvoiceService`** - خدمة الفواتير الدورية
- **الميزات**: إنشاء فواتير متكررة تلقائياً

---

### 4. خدمات التقارير (Reporting Services)

#### `report_exporter.py` (1,410 سطر) ⭐ أكبر ملف
- **`ReportExporter`** - خدمة تصدير التقارير
- **الميزات**: تصدير التقارير إلى Excel, PDF, HTML, CSV

#### `report_generator.py` (899 سطر)
- **`ReportGenerator`** - مولد التقارير
- **الميزات**: إنشاء تقارير المبيعات، المخزون، المالية

#### `pdf_export_service.py` (227 سطر)
- **`PDFExportService`** - خدمة تصدير PDF
- **الميزات**: تصدير التقارير إلى PDF

---

### 5. خدمات الطباعة (Printing Services)

#### `invoice_print_service.py` (420 سطر)
- **`InvoicePrintService`** - خدمة طباعة الفواتير
- **الميزات**: طباعة الفواتير باستخدام HTML/Jinja2

#### `print_service.py` (490 سطر)
- **`PrintService`** - خدمة الطباعة العامة
- **الميزات**: طباعة الإيصالات، الفواتير، التقارير

#### `printing_service.py` (156 سطر)
- **`PrintingService`** - خدمة طباعة بسيطة
- **الميزات**: طباعة أساسية

---

### 6. خدمات المستخدمين والصلاحيات (User & Permissions Services)

#### `user_service.py` (640 سطر)
- **`UserService`** - خدمة المستخدمين
- **الميزات**: إدارة المستخدمين، المصادقة، الجلسات

#### `rbac_service.py` (530 سطر)
- **`RBACService`** - خدمة التحكم في الوصول (Role-Based Access Control)
- **الميزات**: إدارة الأدوار، الصلاحيات، الوصول

#### `permission_service.py` (440 سطر)
- **`PermissionService`** - خدمة الصلاحيات
- **الميزات**: إدارة الصلاحيات، التحقق من الوصول

#### `security_service.py` (204 سطر)
- **`SecurityService`** - خدمة الأمان
- **الميزات**: الأمان، التشفير، التحقق

#### `mfa_service.py` (59 سطر)
- **`MFAService`** - خدمة المصادقة متعددة العوامل
- **ملاحظة**: يوجد أيضاً في `src/security/mfa_service.py` (أكثر تفصيلاً)

---

### 7. خدمات البحث والفلترة (Search & Filter Services)

#### `search_service.py` (340 سطر)
- **`SearchService`** - خدمة البحث
- **الميزات**: بحث متقدم في جميع الكيانات

#### `advanced_search_service.py` (366 سطر)
- **`AdvancedSearchService`** - خدمة بحث متقدمة
- **الميزات**: بحث متقدم مع فلترة معقدة

#### `filter_manager.py` (329 سطر)
- **`FilterManager`** - مدير الفلاتر
- **الميزات**: إدارة الفلاتر، الحفظ، التحميل

---

### 8. خدمات لوحات المعلومات (Dashboard Services)

#### `dashboard_service.py` (486 سطر)
- **`DashboardService`** - خدمة لوحات المعلومات
- **الميزات**: بيانات لوحة المعلومات، KPIs، الرسوم البيانية

#### `performance_service.py` (753 سطر)
- **`PerformanceService`** - خدمة الأداء
- **الميزات**: مراقبة الأداء، التحليلات، التحسين

---

### 9. خدمات الإشعارات والتذكيرات (Notifications & Reminders)

#### `notification_service.py` (594 سطر)
- **`NotificationService`** - خدمة الإشعارات
- **الميزات**: إرسال الإشعارات، الإدارة، التتبع

#### `reminder_service.py` (177 سطر)
- **`ReminderService`** - خدمة التذكيرات
- **الميزات**: جدولة التذكيرات، الإشعارات

#### `email_service.py` (267 سطر)
- **`EmailService`** - خدمة البريد الإلكتروني
- **الميزات**: إرسال البريد الإلكتروني، القوالب

---

### 10. خدمات الموردين (Vendor Services)

#### `vendor_service.py` (222 سطر)
- **`VendorService`** - خدمة الموردين
- **الميزات**: إدارة الموردين، التقييم

#### `vendor_portal.py` (430 سطر)
- **`VendorPortal`** - بوابة الموردين
- **الميزات**: واجهة للموردين، الطلبات، الفواتير

#### `vendor_rating_service.py` (134 سطر)
- **`VendorRatingService`** - خدمة تقييم الموردين
- **الميزات**: تقييم الموردين، الإحصائيات

---

### 11. خدمات التسويق والعلاقات (Marketing & CRM Services)

#### `marketing_service.py` (548 سطر)
- **`MarketingService`** - خدمة التسويق
- **الميزات**: الحملات التسويقية، التحليلات

#### `marketing_automation_service.py` (54 سطر)
- **`MarketingAutomationService`** - خدمة أتمتة التسويق
- **الميزات**: أتمتة الحملات التسويقية

#### `crm_service.py` (445 سطر)
- **`CRMService`** - خدمة إدارة علاقات العملاء
- **الميزات**: إدارة العملاء، التفاعلات، التحليلات

#### `loyalty_service.py` (343 سطر)
- **`LoyaltyService`** - خدمة برامج الولاء
- **الميزات**: نقاط الولاء، المكافآت، البرامج

#### `churn_service.py` (143 سطر)
- **`ChurnService`** - خدمة تحليل التسرب
- **الميزات**: تحليل تسرب العملاء، التنبؤ

---

### 12. خدمات المنتجات (Product Services)

#### `product_service_enhanced.py` (~33KB)
- **`ProductServiceEnhanced`** - خدمة منتجات محسّنة
- **الميزات**: ميزات إضافية للمنتجات

---

### 13. خدمات النسخ الاحتياطي والاستعادة (Backup & Restore Services)

#### `backup_service.py` (693 سطر)
- **`BackupService`** - خدمة النسخ الاحتياطي
- **الميزات**: نسخ احتياطي تلقائي، الاستعادة، التشفير

---

### 14. خدمات المراجعة والسجلات (Audit & Logging Services)

#### `audit_service.py` (350 سطر)
- **`AuditService`** - خدمة المراجعة
- **الميزات**: تسجيل العمليات، المراجعة

#### `audit_log_service.py` (655 سطر)
- **`AuditLogService`** - خدمة سجلات المراجعة
- **الميزات**: إدارة سجلات المراجعة، الاستعلامات

---

### 15. خدمات الاستيراد والتصدير (Import/Export Services)

#### `import_export_service.py` (541 سطر)
- **`ImportExportService`** - خدمة الاستيراد والتصدير
- **الميزات**: استيراد/تصدير البيانات، Excel, CSV

---

### 16. خدمات أخرى (Other Services)

#### `cache_service.py` (314 سطر)
- **`CacheService`** - خدمة التخزين المؤقت
- **الميزات**: تخزين مؤقت، LRU Cache

#### `cache_backends.py` (90 سطر)
- **`CacheBackends`** - واجهات التخزين المؤقت
- **الميزات**: واجهات مختلفة للتخزين المؤقت

#### `image_manager_service.py` (349 سطر)
- **`ImageManagerService`** - خدمة إدارة الصور
- **الميزات**: معالجة الصور، الصور المصغرة، التحسين

#### `encryption_service.py` (59 سطر)
- **`EncryptionService`** - خدمة التشفير
- **الميزات**: تشفير البيانات الحساسة

#### `task_scheduler_service.py` (143 سطر)
- **`TaskSchedulerService`** - خدمة جدولة المهام
- **الميزات**: جدولة المهام، التنفيذ التلقائي

#### `scheduler_service.py` (82 سطر)
- **`SchedulerService`** - خدمة جدولة بسيطة
- **الميزات**: جدولة أساسية

#### `notes_service.py` (89 سطر)
- **`NotesService`** - خدمة الملاحظات
- **الميزات**: إدارة الملاحظات

#### `support_service.py` (67 سطر)
- **`SupportService`** - خدمة الدعم
- **الميزات**: إدارة تذاكر الدعم

#### `ai_service.py` (345 سطر)
- **`AIService`** - خدمة الذكاء الاصطناعي
- **الميزات**: تحليلات ذكية، تنبؤات

#### `smart_assistant.py` (77 سطر)
- **`SmartAssistant`** - مساعد ذكي
- **الميزات**: مساعد ذكي للمستخدمين

---

## 🏗️ البنية المعمارية

### نمط التصميم
جميع الخدمات تتبع نمط **Service Pattern**:
- **Service Class** - منطق العمل
- **Integration with Models** - التكامل مع النماذج
- **Database Access** - الوصول إلى قاعدة البيانات

### الهيكل العام
```python
class Service:
    """خدمة"""
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        # تهيئة المديرين
        self.model_manager = ModelManager(db_manager, logger)
    
    def operation(self, *args, **kwargs):
        """عملية"""
        # منطق العمل
        pass
```

---

## 🔗 التكامل

### مع النماذج (Models)
```python
from src.models.product import ProductManager
from src.models.sale import SaleManager
from src.models.customer import CustomerManager

# في الخدمات
product_manager = ProductManager(db_manager, logger)
sale_manager = SaleManager(db_manager, logger)
customer_manager = CustomerManager(db_manager, logger)
```

### مع قاعدة البيانات
```python
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize()

service = Service(db_manager, logger)
```

---

## 📝 الميزات الرئيسية

### 1. إدارة البيانات (CRUD)
- ✅ Create - إنشاء سجلات جديدة
- ✅ Read - قراءة السجلات
- ✅ Update - تحديث السجلات
- ✅ Delete - حذف السجلات

### 2. منطق العمل (Business Logic)
- ✅ التحقق من صحة البيانات
- ✅ معالجة الأخطاء
- ✅ التحويلات والعمليات الحسابية

### 3. التقارير والتحليلات
- ✅ تقارير المبيعات
- ✅ تقارير المخزون
- ✅ التقارير المالية
- ✅ لوحات المعلومات

### 4. التكامل الخارجي
- ✅ البريد الإلكتروني
- ✅ الطباعة
- ✅ الاستيراد/التصدير
- ✅ APIs

---

## 🎯 أفضل الممارسات

### 1. استخدام الخدمات
```python
# ✅ صحيح - استخدام Service
from src.services.inventory_service import InventoryService

inventory_service = InventoryService(db_manager, logger)
products = inventory_service.get_low_stock_products()

# ❌ خطأ - الوصول المباشر لقاعدة البيانات
products = db.execute_query("SELECT * FROM products WHERE current_stock < min_stock")
```

### 2. معالجة الأخطاء
```python
try:
    result = service.operation()
except ValueError as e:
    logger.error(f"خطأ في القيمة: {e}")
    raise
except Exception as e:
    logger.error(f"خطأ غير متوقع: {e}")
    raise
```

### 3. استخدام Logger
```python
if self.logger:
    self.logger.info("عملية ناجحة")
    self.logger.warning("تحذير")
    self.logger.error("خطأ")
```

---

## 📚 المراجع

- `src/models/` - النماذج المستخدمة في الخدمات
- `src/core/database_manager.py` - مدير قاعدة البيانات
- `src/ui/` - واجهات المستخدم التي تستخدم الخدمات

---

## ✅ الخلاصة

- ✅ جميع الخدمات موثقة بشكل جيد
- ✅ استخدام نمط Service Pattern بشكل متسق
- ✅ تكامل جيد مع النماذج وقاعدة البيانات
- ✅ دعم كامل للعمليات الأساسية
- ✅ تقارير وتحليلات شاملة

**التقييم**: 5/5 ⭐⭐⭐⭐⭐


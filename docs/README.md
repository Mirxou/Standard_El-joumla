# 📚 دليل التوثيق الشامل - Documentation Guide

مرحباً بك في دليل التوثيق الشامل لنظام الإصدار المنطقي (Logical Version ERP System).

## 📋 الفهرس

### 🚀 البدء السريع

- **[API Documentation](API_DOCUMENTATION.md)** - توثيق API الشامل للمكونات الأساسية
- **[Configuration Guide](CONFIGURATION_GUIDE.md)** - دليل إعداد وتكوين النظام
- **[Database Management Guide](DATABASE_MANAGEMENT_GUIDE.md)** - دليل إدارة قاعدة البيانات

### 🎨 واجهة المستخدم

- **[Interactive Dashboard Guide](INTERACTIVE_DASHBOARD_GUIDE.md)** - دليل الداشبورد التفاعلي والرسوم البيانية
- **[Invoice Printing Guide](INVOICE_PRINTING_GUIDE.md)** - دليل نظام طباعة الفواتير الاحترافي

### 🔧 الميزات المتقدمة

- **[Security Guide](SECURITY_GUIDE.md)** - دليل الأمان والتشفير
- **[Integration Guide](INTEGRATION_GUIDE.md)** - دليل التكاملات والواجهات البرمجية
- **[Reports Guide](REPORTS_GUIDE.md)** - دليل نظام التقارير المتقدم

---

## 🎯 للمطورين الجدد

### الخطوة 1: فهم البنية

ابدأ بقراءة:
1. **[API Documentation](API_DOCUMENTATION.md)** - لفهم المكونات الأساسية
2. **[Configuration Guide](CONFIGURATION_GUIDE.md)** - لإعداد بيئة التطوير

### الخطوة 2: استكشاف الميزات

- **[Interactive Dashboard Guide](INTERACTIVE_DASHBOARD_GUIDE.md)** - لفهم نظام الداشبورد
- **[Invoice Printing Guide](INVOICE_PRINTING_GUIDE.md)** - لفهم نظام الطباعة

### الخطوة 3: الميزات المتقدمة

- **[Security Guide](SECURITY_GUIDE.md)** - للأمان والتشفير
- **[Database Management Guide](DATABASE_MANAGEMENT_GUIDE.md)** - لإدارة قاعدة البيانات
- **[Integration Guide](INTEGRATION_GUIDE.md)** - للتكاملات
- **[Reports Guide](REPORTS_GUIDE.md)** - للتقارير

---

## 📖 روابط سريعة للمواضيع

### المكونات الأساسية
- [DatabaseManager](API_DOCUMENTATION.md#database-manager) - إدارة قاعدة البيانات
- [ProductManager](API_DOCUMENTATION.md#product-manager) - إدارة المنتجات
- [SaleManager](API_DOCUMENTATION.md#sales-manager) - إدارة المبيعات
- [ConfigManager](CONFIGURATION_GUIDE.md#config-manager) - إدارة الإعدادات

### واجهة المستخدم
- [ProductDialog](API_DOCUMENTATION.md#product-dialog) - حوار المنتجات
- [SalesDialog](API_DOCUMENTATION.md#sales-dialog) - حوار المبيعات
- [Dashboard](INTERACTIVE_DASHBOARD_GUIDE.md) - الداشبورد التفاعلي
- [Invoice Printing](INVOICE_PRINTING_GUIDE.md) - طباعة الفواتير

### الخدمات
- [InventoryService](API_DOCUMENTATION.md#inventory-service) - خدمة المخزون
- [SalesService](API_DOCUMENTATION.md#sales-service) - خدمة المبيعات
- [ReportExporter](REPORTS_GUIDE.md) - خدمة التقارير

### الأمان
- [Encryption](SECURITY_GUIDE.md#encryption) - التشفير
- [Authentication](SECURITY_GUIDE.md#authentication) - المصادقة
- [Access Control](SECURITY_GUIDE.md#access-control) - التحكم في الوصول

---

## 🔍 البحث السريع

### حسب الموضوع

**قاعدة البيانات:**
- [Database Management Guide](DATABASE_MANAGEMENT_GUIDE.md)
- [Backup & Restore](DATABASE_MANAGEMENT_GUIDE.md#backup--restore)
- [Performance Optimization](DATABASE_MANAGEMENT_GUIDE.md#performance-optimization)

**الإعدادات:**
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Environment Variables](CONFIGURATION_GUIDE.md#environment-variables)
- [Sensitive Data Encryption](CONFIGURATION_GUIDE.md#sensitive-data-encryption)

**التقارير:**
- [Reports Guide](REPORTS_GUIDE.md)
- [Report Types](REPORTS_GUIDE.md#report-types)
- [Export Formats](REPORTS_GUIDE.md#export-formats)

**التكاملات:**
- [Integration Guide](INTEGRATION_GUIDE.md)
- [API Integration](INTEGRATION_GUIDE.md#api-integration)
- [Email Integration](INTEGRATION_GUIDE.md#email-integration)

---

## 📝 أمثلة سريعة

### إنشاء منتج جديد

```python
from src.models.product import Product, ProductManager
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize()

product_manager = ProductManager(db_manager)

product = Product(
    name="منتج جديد",
    cost_price=100.0,
    selling_price=150.0,
    current_stock=50
)

product_id = product_manager.create_product(product)
```

### إنشاء فاتورة

```python
from src.models.sale import Sale, SaleItem, SaleStatus, SaleManager

sale_manager = SaleManager(db_manager)

sale = Sale(
    customer_id=1,
    invoice_number="INV-001",
    items=[
        SaleItem(product_id=1, quantity=5, unit_price=100)
    ],
    status=SaleStatus.CONFIRMED
)

sale_id = sale_manager.create_sale(sale)
```

### طباعة فاتورة

```python
from src.services.invoice_print_service import InvoicePrintService

service = InvoicePrintService()
success, message = service.print_invoice(invoice_data)
```

---

## 🛠️ المساهمة في التوثيق

نرحب بمساهماتك في تحسين التوثيق! يرجى:

1. قراءة الملفات الموجودة أولاً
2. إضافة أمثلة عملية عند الإمكان
3. تحديث التوثيق عند إضافة ميزات جديدة
4. استخدام Markdown بشكل صحيح

---

## 📞 الدعم

إذا واجهت أي مشاكل أو لديك أسئلة:

1. راجع الدليل المناسب من القائمة أعلاه
2. ابحث في [API Documentation](API_DOCUMENTATION.md)
3. راجع أمثلة الكود في الملفات

---

## 📅 آخر تحديث

**التاريخ:** 2025-01-15  
**الإصدار:** 5.3.0

---

**تم إنشاء هذا الدليل بواسطة:** Logical Version Team


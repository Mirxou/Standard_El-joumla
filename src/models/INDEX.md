# Models Module Index - فهرس نماذج البيانات

## 📋 قائمة سريعة بالملفات

### النماذج الأساسية (Core Models)
1. **`product.py`** (414 سطر) - المنتجات
   - `Product`, `ProductManager`

2. **`customer.py`** (564 سطر) - العملاء
   - `Customer`, `CustomerManager`

3. **`sale.py`** (1,558 سطر) ⭐ - المبيعات
   - `Sale`, `SaleItem`, `SaleManager`, `SaleStatus`, `PaymentMethod`

4. **`supplier.py`** (546 سطر) - الموردين
   - `Supplier`, `SupplierManager`

5. **`user.py`** (665 سطر) - المستخدمين
   - `User`, `UserManager`, `UserRole`

---

### نماذج المشتريات والمخزون (Purchase & Inventory)
6. **`purchase.py`** (939 سطر) - المشتريات
   - `Purchase`, `PurchaseItem`, `PurchaseManager`, `PurchaseStatus`, `PaymentStatus`

7. **`purchase_order.py`** (597 سطر) - أوامر الشراء
   - `PurchaseOrder`, `PurchaseOrderItem`, `PurchaseOrderManager`

8. **`receiving_note.py`** (502 سطر) - إيصالات الاستلام
   - `ReceivingNote`, `ReceivingNoteItem`, `ReceivingNoteManager`

9. **`physical_count.py`** (387 سطر) - الجرد الفعلي
   - `PhysicalCount`, `PhysicalCountItem`, `PhysicalCountManager`

10. **`inventory_optimization.py`** (563 سطر) - تحسين المخزون
    - `InventoryOptimization`, `ReorderPoint`, `SafetyStock`

---

### النماذج المالية (Financial Models)
11. **`payment.py`** (486 سطر) - المدفوعات
    - `Payment`, `PaymentManager`, `PaymentType`

12. **`payment_plan.py`** (532 سطر) - خطط الدفع
    - `PaymentPlan`, `PaymentPlanItem`, `PaymentPlanManager`

13. **`account.py`** (134 سطر) - الحسابات المحاسبية
    - `Account`, `AccountManager`

14. **`journal_entry.py`** (169 سطر) - القيود المحاسبية
    - `JournalEntry`, `JournalEntryManager`

---

### نماذج التقارير والتحليلات (Reporting & Analytics)
15. **`report.py`** (435 سطر) - التقارير
    - `Report`, `ReportData`, `ReportTemplate`, `ReportType`, `ReportPeriod`, `ReportFormat`, `ExportFormat`, `ChartType`, `ReportFilter`, `SalesReportLine`, `SalesReportSummary`, `InventoryReportLine`, `InventoryReportSummary`, `FinancialReportLine`, `FinancialReportSummary`, `ChartData`

16. **`dashboard.py`** (59 سطر) - لوحات المعلومات
    - `DashboardData`, `DashboardWidget`, `KPI`, `TimeSeriesPoint`, `ChartSeries`

---

### النماذج الأخرى (Other Models)
17. **`quote.py`** (346 سطر) - عروض الأسعار
    - `Quote`, `QuoteItem`, `QuoteManager`

18. **`return_invoice.py`** (421 سطر) - فواتير المرتجعات
    - `ReturnInvoice`, `ReturnInvoiceItem`, `ReturnInvoiceManager`

19. **`category.py`** (358 سطر) - الفئات
    - `Category`, `CategoryManager`

20. **`permission.py`** (247 سطر) - الصلاحيات
    - `Permission`, `PermissionManager`

21. **`search.py`** (192 سطر) - البحث المتقدم
    - `SearchResult`, `SearchManager`, `SearchEntity`, `FilterOperator`, `SortDirection`, `SearchFilter`

22. **`pydantic_schemas.py`** (599 سطر) - Schemas للتحقق من صحة البيانات
    - `UserCreate`, `UserUpdate`, `UserResponse`, `ProductCreate`, `ProductUpdate`, `ProductResponse`, `SaleCreate`, `SaleUpdate`, `SaleResponse`, `CustomerCreate`, `CustomerUpdate`, `CustomerResponse`, `InvoiceCreate`, `InvoiceUpdate`, `InvoiceResponse`, `PaymentCreate`, `PaymentUpdate`, `PaymentResponse`

23. **`product_enhanced.py`** (594 سطر) - منتج محسّن
    - `ProductEnhanced`

---

## 📊 الإحصائيات

- **إجمالي الملفات**: 23 ملف Python
- **إجمالي الأسطر**: 11,291 سطر
- **متوسط الأسطر لكل ملف**: 490 سطر
- **أكبر ملف**: `sale.py` (1,558 سطر)
- **أصغر ملف**: `dashboard.py` (59 سطر)

---

## 🔍 البحث السريع

### حسب الوظيفة:
- **CRUD Operations**: جميع الملفات تحتوي على Manager classes
- **Enums**: `sale.py`, `purchase.py`, `report.py`, `search.py`, `pydantic_schemas.py`
- **Financial**: `payment.py`, `payment_plan.py`, `account.py`, `journal_entry.py`
- **Inventory**: `product.py`, `purchase.py`, `physical_count.py`, `inventory_optimization.py`
- **Reporting**: `report.py`, `dashboard.py`

### حسب الحجم:
- **كبيرة (> 500 سطر)**: `sale.py`, `purchase.py`, `customer.py`, `supplier.py`, `user.py`, `purchase_order.py`, `inventory_optimization.py`, `payment_plan.py`, `pydantic_schemas.py`, `product_enhanced.py`
- **متوسطة (200-500 سطر)**: `product.py`, `report.py`, `quote.py`, `return_invoice.py`, `category.py`, `payment.py`, `receiving_note.py`, `physical_count.py`, `permission.py`
- **صغيرة (< 200 سطر)**: `dashboard.py`, `account.py`, `journal_entry.py`, `search.py`

---

## 🔗 روابط سريعة

- [README.md](README.md) - دليل شامل
- [../core/README.md](../core/README.md) - دليل الوحدات الأساسية
- [../services/README.md](../services/README.md) - دليل الخدمات
- [../database/README.md](../database/README.md) - دليل قاعدة البيانات

---

## 💡 نصائح الاستخدام

### استيراد النماذج:
```python
# استيراد نموذج واحد
from src.models.product import Product, ProductManager

# استيراد متعدد
from src.models import Product, ProductManager, Sale, SaleManager

# استيراد من __init__.py
from src.models import (
    Product, ProductManager,
    Sale, SaleItem, SaleManager,
    Customer, CustomerManager
)
```

### استخدام Manager:
```python
# تهيئة Manager
product_manager = ProductManager(db_manager, logger)

# استخدام العمليات
product = product_manager.get_product(1)
products = product_manager.get_all_products()
new_id = product_manager.create_product(product)
success = product_manager.update_product(product)
success = product_manager.delete_product(1)
```

---

## ✅ الحالة

- ✅ جميع الملفات موثقة بشكل جيد
- ✅ استخدام نمط Manager Pattern بشكل متسق
- ✅ دعم كامل للـ CRUD operations
- ✅ تحقق من صحة البيانات
- ✅ تكامل جيد مع قاعدة البيانات والخدمات


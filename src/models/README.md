# Models Module - نماذج البيانات

## نظرة عامة
هذا المجلد يحتوي على جميع نماذج البيانات (Data Models) والمنطق التجاري (Business Logic) للتطبيق. النماذج تستخدم `dataclasses` و `Pydantic` للتحقق من صحة البيانات.

## 📊 الإحصائيات

- **إجمالي الملفات**: 23 ملف Python
- **إجمالي الأسطر**: 11,291 سطر
- **متوسط الأسطر لكل ملف**: 490 سطر
- **Syntax Check**: ✅ جميع الملفات صحيحة
- **Linter**: ✅ لا توجد أخطاء

## 📁 التصنيف

### 1. النماذج الأساسية (Core Models)

#### `product.py` (414 سطر)
- **`Product`** - نموذج بيانات المنتج
- **`ProductManager`** - مدير المنتجات (CRUD operations)
- **الميزات**: إدارة المخزون، حساب هامش الربح، البحث

#### `customer.py` (564 سطر)
- **`Customer`** - نموذج بيانات العميل
- **`CustomerManager`** - مدير العملاء (CRUD operations)
- **الميزات**: إدارة الائتمان، تاريخ المشتريات، الإحصائيات

#### `sale.py` (1,558 سطر) ⭐ أكبر ملف
- **`Sale`** - نموذج بيانات الفاتورة
- **`SaleItem`** - عنصر الفاتورة
- **`SaleManager`** - مدير المبيعات (CRUD operations)
- **`SaleStatus`** - حالات الفاتورة (Enum)
- **`PaymentMethod`** - طرق الدفع (Enum)
- **الميزات**: إنشاء الفواتير، معالجة المرتجعات، إدارة المدفوعات

#### `supplier.py` (546 سطر)
- **`Supplier`** - نموذج بيانات المورد
- **`SupplierManager`** - مدير الموردين (CRUD operations)
- **الميزات**: إدارة الموردين، تاريخ المشتريات، التقييم

#### `user.py` (665 سطر)
- **`User`** - نموذج بيانات المستخدم
- **`UserManager`** - مدير المستخدمين (CRUD operations)
- **`UserRole`** - أدوار المستخدمين (Enum)
- **الميزات**: إدارة المستخدمين، الصلاحيات، المصادقة

---

### 2. نماذج المشتريات والمخزون (Purchase & Inventory)

#### `purchase.py` (939 سطر)
- **`Purchase`** - نموذج بيانات المشتريات
- **`PurchaseItem`** - عنصر المشتريات
- **`PurchaseManager`** - مدير المشتريات (CRUD operations)
- **`PurchaseStatus`** - حالات المشتريات (Enum)
- **`PaymentStatus`** - حالات الدفع (Enum)
- **الميزات**: إدارة المشتريات، تتبع الاستلام، إدارة المدفوعات

#### `purchase_order.py` (597 سطر)
- **`PurchaseOrder`** - نموذج بيانات أمر الشراء
- **`PurchaseOrderItem`** - عنصر أمر الشراء
- **`PurchaseOrderManager`** - مدير أوامر الشراء (CRUD operations)
- **الميزات**: إدارة أوامر الشراء، تتبع الحالة، الموافقات

#### `receiving_note.py` (502 سطر)
- **`ReceivingNote`** - نموذج بيانات إيصال الاستلام
- **`ReceivingNoteItem`** - عنصر إيصال الاستلام
- **`ReceivingNoteManager`** - مدير إيصالات الاستلام (CRUD operations)
- **الميزات**: تسجيل الاستلام، مطابقة الطلبات، تحديث المخزون

#### `physical_count.py` (387 سطر)
- **`PhysicalCount`** - نموذج بيانات الجرد الفعلي
- **`PhysicalCountItem`** - عنصر الجرد الفعلي
- **`PhysicalCountManager`** - مدير الجرد الفعلي (CRUD operations)
- **الميزات**: إدارة الجرد الفعلي، حساب الفروقات، التصحيح

#### `inventory_optimization.py` (563 سطر)
- **`InventoryOptimization`** - تحسين المخزون
- **`ReorderPoint`** - نقطة إعادة الطلب
- **`SafetyStock`** - المخزون الآمن
- **الميزات**: حساب نقاط إعادة الطلب، تحليل ABC، تحسين المخزون

---

### 3. النماذج المالية (Financial Models)

#### `payment.py` (486 سطر)
- **`Payment`** - نموذج بيانات الدفع
- **`PaymentManager`** - مدير المدفوعات (CRUD operations)
- **`PaymentType`** - أنواع المدفوعات (Enum)
- **الميزات**: تسجيل المدفوعات، تتبع الحسابات، التقارير

#### `payment_plan.py` (532 سطر)
- **`PaymentPlan`** - نموذج بيانات خطة الدفع
- **`PaymentPlanItem`** - عنصر خطة الدفع
- **`PaymentPlanManager`** - مدير خطط الدفع (CRUD operations)
- **الميزات**: إدارة خطط الدفع، الجدولة، التتبع

#### `account.py` (134 سطر)
- **`Account`** - نموذج بيانات الحساب المحاسبي
- **`AccountManager`** - مدير الحسابات (CRUD operations)
- **الميزات**: إدارة الحسابات المحاسبية، التصنيف

#### `journal_entry.py` (169 سطر)
- **`JournalEntry`** - نموذج بيانات القيد المحاسبي
- **`JournalEntryManager`** - مدير القيود المحاسبية (CRUD operations)
- **الميزات**: تسجيل القيود المحاسبية، التوازن

---

### 4. نماذج التقارير والتحليلات (Reporting & Analytics)

#### `report.py` (435 سطر)
- **`Report`** - نموذج بيانات التقرير
- **`ReportData`** - بيانات التقرير
- **`ReportTemplate`** - قالب التقرير
- **`ReportType`** - أنواع التقارير (Enum)
- **`ReportPeriod`** - فترات التقارير (Enum)
- **`ReportFormat`** - تنسيقات التقارير (Enum)
- **`ExportFormat`** - تنسيقات التصدير (Enum)
- **`ChartType`** - أنواع الرسوم البيانية (Enum)
- **`ReportFilter`** - فلتر التقرير
- **`SalesReportLine`**, **`SalesReportSummary`** - تقارير المبيعات
- **`InventoryReportLine`**, **`InventoryReportSummary`** - تقارير المخزون
- **`FinancialReportLine`**, **`FinancialReportSummary`** - التقارير المالية
- **`ChartData`** - بيانات الرسم البياني
- **الميزات**: إنشاء التقارير، التصدير، الرسوم البيانية

#### `dashboard.py` (59 سطر)
- **`DashboardData`** - بيانات لوحة المعلومات
- **`DashboardWidget`** - ويدجت لوحة المعلومات
- **`KPI`** - مؤشر أداء رئيسي
- **`TimeSeriesPoint`** - نقطة سلسلة زمنية
- **`ChartSeries`** - سلسلة الرسم البياني
- **الميزات**: لوحات المعلومات، مؤشرات الأداء، الرسوم البيانية

---

### 5. النماذج الأخرى (Other Models)

#### `quote.py` (346 سطر)
- **`Quote`** - نموذج بيانات عرض السعر
- **`QuoteItem`** - عنصر عرض السعر
- **`QuoteManager`** - مدير عروض الأسعار (CRUD operations)
- **الميزات**: إدارة عروض الأسعار، التحويل إلى فاتورة

#### `return_invoice.py` (421 سطر)
- **`ReturnInvoice`** - نموذج بيانات فاتورة المرتجع
- **`ReturnInvoiceItem`** - عنصر فاتورة المرتجع
- **`ReturnInvoiceManager`** - مدير فواتير المرتجعات (CRUD operations)
- **الميزات**: إدارة المرتجعات، استرداد المخزون، المبالغ

#### `category.py` (358 سطر)
- **`Category`** - نموذج بيانات الفئة
- **`CategoryManager`** - مدير الفئات (CRUD operations)
- **الميزات**: إدارة الفئات، التصنيف الهرمي

#### `permission.py` (247 سطر)
- **`Permission`** - نموذج بيانات الصلاحية
- **`PermissionManager`** - مدير الصلاحيات (CRUD operations)
- **الميزات**: إدارة الصلاحيات، RBAC

#### `search.py` (192 سطر)
- **`SearchResult`** - نتيجة البحث
- **`SearchManager`** - مدير البحث
- **`SearchEntity`** - الكيانات القابلة للبحث (Enum)
- **`FilterOperator`** - عوامل الفلترة (Enum)
- **`SortDirection`** - اتجاه الترتيب (Enum)
- **`SearchFilter`** - فلتر البحث
- **الميزات**: البحث المتقدم، الفلترة، الترتيب

#### `pydantic_schemas.py` (599 سطر)
- **Schemas للتحقق من صحة البيانات** (Pydantic)
- **`UserCreate`**, **`UserUpdate`**, **`UserResponse`**
- **`ProductCreate`**, **`ProductUpdate`**, **`ProductResponse`**
- **`SaleCreate`**, **`SaleUpdate`**, **`SaleResponse`**
- **`CustomerCreate`**, **`CustomerUpdate`**, **`CustomerResponse`**
- **`InvoiceCreate`**, **`InvoiceUpdate`**, **`InvoiceResponse`**
- **`PaymentCreate`**, **`PaymentUpdate`**, **`PaymentResponse`**
- **الميزات**: التحقق من صحة البيانات، API schemas

#### `product_enhanced.py` (594 سطر)
- **`ProductEnhanced`** - نموذج منتج محسّن
- **الميزات**: ميزات إضافية للمنتجات (variants, bundles, etc.)

---

## 🏗️ البنية المعمارية

### نمط التصميم
جميع النماذج تتبع نمط **Manager Pattern**:
- **Model Class** (`Product`, `Sale`, etc.) - بيانات الكيان
- **Manager Class** (`ProductManager`, `SaleManager`, etc.) - منطق العمل

### الهيكل العام
```python
@dataclass
class Model:
    """نموذج البيانات"""
    id: Optional[int] = None
    # ... الحقول الأخرى
    
    def to_dict(self) -> Dict:
        """تحويل إلى قاموس"""
        pass

class ModelManager:
    """مدير النموذج"""
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
    
    def create(self, model: Model) -> int:
        """إنشاء سجل جديد"""
        pass
    
    def get(self, id: int) -> Optional[Model]:
        """الحصول على سجل"""
        pass
    
    def update(self, model: Model) -> bool:
        """تحديث سجل"""
        pass
    
    def delete(self, id: int) -> bool:
        """حذف سجل"""
        pass
```

---

## 🔗 التكامل

### الاستخدام في الخدمات
```python
from src.models.product import ProductManager
from src.models.sale import SaleManager
from src.models.customer import CustomerManager

# في الخدمات
product_manager = ProductManager(db_manager, logger)
sale_manager = SaleManager(db_manager, logger)
customer_manager = CustomerManager(db_manager, logger)
```

### الاستخدام في UI
```python
from src.models.product import Product, ProductManager
from src.models.sale import Sale, SaleItem, SaleManager

# في النوافذ والحوارات
products = product_manager.get_all_products()
sale = sale_manager.create_sale(customer_id, items)
```

---

## 📝 الميزات الرئيسية

### 1. إدارة البيانات (CRUD)
- ✅ Create - إنشاء سجلات جديدة
- ✅ Read - قراءة السجلات
- ✅ Update - تحديث السجلات
- ✅ Delete - حذف السجلات

### 2. التحقق من صحة البيانات
- ✅ استخدام `dataclasses` للتحقق الأساسي
- ✅ استخدام `Pydantic` للتحقق المتقدم (في `pydantic_schemas.py`)
- ✅ استخدام `Decimal` للقيم المالية الدقيقة

### 3. إدارة العلاقات
- ✅ Foreign Keys بين الجداول
- ✅ Cascade operations
- ✅ Referential integrity

### 4. البحث والفلترة
- ✅ بحث متقدم في `search.py`
- ✅ فلترة متعددة المعايير
- ✅ ترتيب متعدد الأعمدة

### 5. التقارير والتحليلات
- ✅ تقارير المبيعات
- ✅ تقارير المخزون
- ✅ التقارير المالية
- ✅ لوحات المعلومات

---

## 🎯 أفضل الممارسات

### 1. استخدام Decimal للقيم المالية
```python
from decimal import Decimal

price = Decimal('100.50')  # ✅ صحيح
price = 100.50  # ❌ خطأ - قد يسبب مشاكل في الدقة
```

### 2. استخدام Optional للقيم الاختيارية
```python
from typing import Optional

description: Optional[str] = None  # ✅ صحيح
description: str = None  # ❌ خطأ - يجب استخدام Optional
```

### 3. استخدام Enum للحالات
```python
from enum import Enum

class SaleStatus(Enum):
    DRAFT = "مسودة"
    CONFIRMED = "مؤكدة"
    PAID = "مدفوعة"
```

### 4. استخدام Manager Pattern
```python
# ✅ صحيح - استخدام Manager
product_manager = ProductManager(db_manager, logger)
product = product_manager.get_product(1)

# ❌ خطأ - الوصول المباشر لقاعدة البيانات
product = db.execute_query("SELECT * FROM products WHERE id = ?", (1,))
```

---

## 📚 المراجع

- `src/core/database_manager.py` - مدير قاعدة البيانات
- `src/services/` - الخدمات التي تستخدم النماذج
- `src/ui/` - واجهات المستخدم التي تستخدم النماذج

---

## ✅ الخلاصة

- ✅ جميع النماذج موثقة بشكل جيد
- ✅ استخدام نمط Manager Pattern بشكل متسق
- ✅ دعم كامل للـ CRUD operations
- ✅ تحقق من صحة البيانات
- ✅ تكامل جيد مع قاعدة البيانات والخدمات

**التقييم**: 5/5 ⭐⭐⭐⭐⭐


# Next Steps - الخطوات التالية

## 🗺️ خارطة الطريق للمستقبل

---

## 🎯 المرحلة القادمة: Service Layer (طبقة الخدمات)

### الهدف:
بناء طبقة خدمات قوية تفصل المنطق الحسابي عن واجهة المستخدم.

---

## 📋 الخطوات المقترحة

### 1. إنشاء Service Base Class

```python
# src/services/base_service.py
from abc import ABC, abstractmethod
from src.core.database_manager import DatabaseManager
from src.core.window_manager import WindowManager

class BaseService(ABC):
    """فئة أساسية لجميع الخدمات"""
    
    def __init__(self, db_manager: DatabaseManager, window_manager: WindowManager = None):
        self.db_manager = db_manager
        self.window_manager = window_manager
        self.logger = setup_logger(self.__class__.__name__)
    
    @abstractmethod
    def initialize(self):
        """تهيئة الخدمة"""
        pass
```

---

### 2. تحسين InventoryService

```python
# src/services/inventory_service.py
from src.services.base_service import BaseService

class InventoryService(BaseService):
    """خدمة إدارة المخزون"""
    
    def __init__(self, db_manager, window_manager=None):
        super().__init__(db_manager, window_manager)
        self._products_cache = {}
    
    def get_product(self, product_id: int):
        """الحصول على منتج (مع Cache)"""
        if product_id in self._products_cache:
            return self._products_cache[product_id]
        
        product = self.db_manager.get_product(product_id)
        self._products_cache[product_id] = product
        return product
    
    def calculate_stock_value(self, products):
        """حساب قيمة المخزون"""
        total = 0
        for product in products:
            total += product.price * product.stock
        return total
    
    def show_product_details(self, product_id: int):
        """فتح نافذة تفاصيل المنتج"""
        if self.window_manager:
            self.window_manager.open_window(
                "product_details",
                product_id=product_id
            )
    
    def show_low_stock_report(self):
        """فتح تقرير المخزون المنخفض"""
        if self.window_manager:
            self.window_manager.open_window("low_stock_report")
```

---

### 3. استخدام الخدمات في النوافذ

```python
# في InventoryWindow
class InventoryWindow(QMainWindow):
    def __init__(self, inventory_service: InventoryService, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        
        # استخدام الخدمة بدلاً من الكود المباشر
        self.load_data()
    
    def load_data(self):
        """تحميل البيانات عبر الخدمة"""
        products = self.inventory_service.get_all_products()
        self.update_table(products)
    
    def calculate_total_value(self):
        """حساب القيمة الإجمالية عبر الخدمة"""
        value = self.inventory_service.calculate_stock_value(self.products)
        self.total_value_label.setText(f"{value:,.2f}")
```

---

## 🔄 Workflow المقترح

### قبل:
```
UI → Database مباشرة
```

### بعد:
```
UI → Service → Database
     ↓
WindowManager (للنوافذ)
```

---

## ✅ Checklist للمرحلة القادمة

### المرحلة 1: Base Service
- [ ] إنشاء `BaseService` class
- [ ] إضافة Error Handling
- [ ] إضافة Logging

### المرحلة 2: Inventory Service
- [ ] تحسين `InventoryService`
- [ ] إضافة Caching
- [ ] ربط بـ WindowManager
- [ ] نقل المنطق من `InventoryWindow`

### المرحلة 3: Sales Service
- [ ] تحسين `SalesService`
- [ ] إضافة Background Processing
- [ ] ربط بـ WindowManager
- [ ] نقل المنطق من `SalesWindow`

### المرحلة 4: Reports Service
- [ ] تحسين `ReportsService`
- [ ] إضافة Async Report Generation
- [ ] ربط بـ WindowManager
- [ ] نقل المنطق من `ReportsWindow`

---

## 🎯 الأولويات

1. **Inventory Service** (الأهم)
2. **Sales Service** (مهم)
3. **Reports Service** (مهم)
4. **Other Services** (لاحقاً)

---

## 📚 الملفات المرجعية

- `PROJECT_COMPLETE.md` - ملخص المشروع
- `COMMIT_MESSAGE.md` - رسالة Commit
- `DEPLOYMENT_GUIDE.md` - دليل النشر

---

## 🚀 الخلاصة

**الآن، الأساسات جاهزة!** ✅

المرحلة القادمة: بناء **Service Layer قوي** فوق هذه الأساسات.

**نلتقي في المرحلة القادمة!** 👋🚀


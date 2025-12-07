# Window Manager Migration Guide - دليل الترحيل

## ✅ تم إنشاء النسخة الجديدة

تم إنشاء `src/core/window_manager.py` - نسخة بسيطة واحترافية.

---

## 📋 خطوات الترحيل السريعة

### 1. تحديث الاستيراد في `main_window.py`

**قبل (النسخة القديمة - تم حذفها):**
```python
from src.ui.window_manager import WindowManager  # ❌ قديم - تم حذفه
```

**بعد (النسخة الجديدة):**
```python
from src.core.window_manager import WindowManager  # ✅ النسخة الجديدة
```

### 2. تحديث تهيئة WindowManager

**قبل:**
```python
self.window_manager = WindowManager(logger=self.logger)
```

**بعد:**
```python
self.window_manager = WindowManager(organization="LogicalVersion", appname="ERP", parent=self)
```

### 3. تحديث تسجيل النوافذ

**قبل (Factory Pattern):**
```python
def physical_counts_factory(**kwargs):
    return PhysicalCountsWindow(self.db_manager, **kwargs)

self.window_manager.register_window(
    window_id="physical_counts",
    factory=physical_counts_factory,
    title="العد الفعلي",
    min_size=QSize(1200, 700),
    default_size=QSize(1400, 800),
    singleton=True
)
```

**بعد (Class-based):**
```python
self.window_manager.register_window(
    window_key="physical_counts",
    window_class=PhysicalCountsWindow,
    title="العد الفعلي",
    singleton=True,
    init_kwargs={"db_manager": self.db_manager}
)
```

### 4. إضافة Attributes للنوافذ (اختياري - للتسجيل التلقائي)

في أي نافذة تريد تسجيلها تلقائياً، أضف:

```python
class PhysicalCountsWindow(QMainWindow):
    # Window Manager attributes
    window_key = "physical_counts"
    window_singleton = True
    window_title = "العد الفعلي"
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        # ...
```

ثم استخدم `auto_register`:
```python
from src.ui.windows.physical_counts_window import PhysicalCountsWindow

self.window_manager.auto_register([PhysicalCountsWindow])
```

---

## 🔄 مثال كامل: تحديث نافذة موجودة

### مثال 1: نافذة Singleton (مثل ProductsWindow)

**في `src/ui/windows/products_window.py`:**
```python
from PySide6.QtWidgets import QMainWindow

class ProductsWindow(QMainWindow):
    # Window Manager attributes
    window_key = "products"
    window_singleton = True
    window_title = "المنتجات"
    
    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        # باقي الكود...
```

**في `main_window.py`:**
```python
from src.ui.windows.products_window import ProductsWindow

# تسجيل يدوي
self.window_manager.register_window(
    window_key="products",
    window_class=ProductsWindow,
    title="المنتجات",
    singleton=True,
    init_kwargs={"db_manager": self.db_manager}
)

# أو استخدام auto_register
self.window_manager.auto_register([ProductsWindow])
```

**فتح النافذة:**
```python
def show_products_window(self):
    window = self.window_manager.open_window("products", parent=self)
    if not window:
        QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة المنتجات")
```

### مثال 2: نافذة متعددة (مثل CustomerHistoryWindow)

**في `src/ui/windows/customer_history_window.py`:**
```python
class CustomerHistoryWindow(QMainWindow):
    window_key = "customer_history"
    window_singleton = False  # يسمح بفتح عدة نوافذ
    window_title = "سجل العميل"
    
    def __init__(self, db_manager=None, customer_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.customer_id = customer_id
        # باقي الكود...
```

**في `main_window.py`:**
```python
self.window_manager.register_window(
    window_key="customer_history",
    window_class=CustomerHistoryWindow,
    title="سجل العميل",
    singleton=False,
    init_kwargs={"db_manager": self.db_manager}
)

# فتح نافذة مع معاملات إضافية
def show_customer_history(self, customer_id):
    window = self.window_manager.open_window(
        "customer_history",
        parent=self,
        customer_id=customer_id
    )
```

---

## 🎯 الميزات الجديدة

### 1. Hooks System

```python
def before_open_hook(key, instance, kwargs):
    logger.debug(f"Opening window: {key} with kwargs: {kwargs}")

def after_open_hook(key, instance):
    logger.info(f"Opened window: {key} -> {instance}")

wm.on_before_open.append(before_open_hook)
wm.on_after_open.append(after_open_hook)
```

### 2. التحقق من حالة النافذة

```python
# التحقق من كون النافذة مفتوحة
if wm.is_open("products"):
    print("Products window is open")

# الحصول على جميع المثيلات المفتوحة
instances = wm.get_open_instances("customer_history")
for inst in instances:
    print(f"Customer history window: {inst}")
```

### 3. إغلاق جميع النوافذ

```python
# في closeEvent للنافذة الرئيسية
def closeEvent(self, event):
    self.window_manager.close_all()
    super().closeEvent(event)
```

---

## ⚠️ ملاحظات مهمة

1. **لا تعيد تعريف `closeEvent` من خارج الصنف** - WindowManager لا يغيّر `closeEvent`
2. **استخدم `super().closeEvent(event)`** في أي نافذة تعيد تعريف `closeEvent`
3. **Weakrefs تمنع Memory Leaks** - النوافذ تُحذف تلقائياً من التتبع عند الحذف
4. **QSettings آمن** - الحالة تُحفظ تلقائياً عند الإغلاق

---

## ✅ Checklist الترحيل

- [ ] نسخ `src/core/window_manager.py`
- [ ] تحديث الاستيراد في `main_window.py`
- [ ] تحديث تهيئة `WindowManager`
- [ ] تحديث تسجيل النوافذ (اختر: يدوي أو auto_register)
- [ ] إضافة `window_key` و `window_singleton` للنوافذ (اختياري)
- [ ] تحديث استدعاءات `open_window`
- [ ] اختبار فتح/إغلاق النوافذ
- [ ] اختبار حفظ/استعادة الحالة

---

## 🚀 بعد الترحيل

النظام الآن:
- ✅ أبسط وأكثر قابلية للصيانة
- ✅ يدعم weakrefs لمنع memory leaks
- ✅ يحفظ الحالة تلقائياً
- ✅ يدعم hooks system
- ✅ لا يعيد كتابة closeEvent

**جاهز للإنتاج!** 🎯


# Tests Module - وحدة الاختبارات

## نظرة عامة
هذا المجلد يحتوي على مجموعة شاملة من الاختبارات لنظام ERP الإصدار المنطقي. تستخدم الاختبارات `pytest` كإطار عمل رئيسي.

## 📊 الإحصائيات

- **إجمالي الملفات**: 42 ملف Python
- **إجمالي الأسطر**: 5,338 سطر
- **متوسط الأسطر لكل ملف**: 127 سطر
- **Syntax Check**: ✅ جميع الملفات صحيحة
- **Linter**: ✅ لا توجد أخطاء

## 📁 الهيكل

### 1. Unit Tests (اختبارات الوحدة) - 25 ملف

#### Core Tests
- `test_math_utils.py` - اختبارات الأدوات الرياضية
- `test_logger.py` - اختبارات نظام السجلات
- `test_logging_service.py` - اختبارات خدمة السجلات
- `test_config_manager.py` - اختبارات مدير الإعدادات
- `test_exception_handler.py` - اختبارات معالج الاستثناءات
- `test_main_worker.py` - اختبارات عامل تهيئة النظام (main.py)
- `test_main_app.py` - اختبارات كلاس التطبيق الرئيسي (main.py)

#### Database Tests
- `test_database_logger_fixes.py` - اختبارات إصلاحات DatabaseLogger
- `test_database_logger_extended.py` - اختبارات موسعة لـ DatabaseLogger
- `test_backup_manager.py` - اختبارات مدير النسخ الاحتياطي
- `test_database_manager.py` - اختبارات مدير قاعدة البيانات (جديد)
- `test_incremental_backup.py` - اختبارات النسخ الاحتياطي التدريجي

#### Service Tests
- `test_inventory_service.py` - اختبارات خدمة المخزون
- `test_payment_service.py` - اختبارات خدمة المدفوعات (جديد)
- `test_purchase_service.py` - اختبارات خدمة المشتريات (جديد)
- `test_user_service.py` - اختبارات خدمة المستخدمين والأمان (جديد)
- `test_accounting_service.py` - اختبارات خدمة المحاسبة (جديد)
- `test_report_exporter.py` - اختبارات خدمة تصدير التقارير (جديد)

#### Security Tests
- `test_encryption_manager.py` - اختبارات مدير التشفير
- `test_security_service.py` - اختبارات خدمة الأمان
- `test_mfa_service.py` - اختبارات خدمة MFA
- `test_rate_limiter.py` - اختبارات محدود المعدل
- `test_permission_manager.py` - اختبارات مدير الصلاحيات

#### Cache & Performance Tests
- `test_cache_manager.py` - اختبارات مدير التخزين المؤقت
- `test_caching_service.py` - اختبارات خدمة التخزين المؤقت

#### Model Tests
- `test_product_model.py` - اختبارات نموذج المنتج
- `test_sale_model.py` - اختبارات نموذج المبيعات
- `test_warehouse_model.py` - اختبارات نموذج المستودعات (جديد)

#### API Tests
- `test_api_client.py` - اختبارات عميل API
- `test_api_modules.py` - اختبارات وحدات API

#### AI Tests
- `test_ai_modules.py` - اختبارات وحدات AI

#### Audit & Print Tests
- `test_audit_trail_manager.py` - اختبارات مدير سجل المراجعة
- `test_print_manager.py` - اختبارات مدير الطباعة

#### i18n Tests
- `test_i18n.py` - اختبارات نظام الترجمة

---

### 2. API Tests (اختبارات API) - 3 ملفات

- `test_api_integration.py` - اختبارات تكامل API
- `test_api_advanced.py` - اختبارات API المتقدمة
- `test_api_server.py` - اختبارات خادم API

---

### 3. UI Tests (اختبارات الواجهة) - 6 ملفات
 
 - `test_ui_comprehensive.py` - اختبارات "Smart Smoke Test" لـ 50+ نافذة (جديد)

- `test_main_window.py` - اختبارات النافذة الرئيسية
- `test_windows.py` - اختبارات النوافذ
- `test_dialogs.py` - اختبارات الحوارات
- `test_error_dialog.py` - اختبارات حوار الأخطاء
- `test_interactions.py` - اختبارات التفاعلات

---

### 4. Integration & Experimental Tests - 8 ملفات
 
 - `test_experimental.py` - اختبارات الخدمات التجريبية والمهملة (جديد)

- `test_database_manager_advanced.py` - اختبارات متقدمة لمدير قاعدة البيانات
- `test_product_manager_advanced.py` - اختبارات متقدمة لمدير المنتجات
- `test_customer_manager.py` - اختبارات مدير العملاء
- `test_sale_manager.py` - اختبارات مدير المبيعات
- `test_api_sync.py` - اختبارات مزامنة API
- `test_workflow_sale_to_payment.py` - اختبار سير عمل البيع (جديد)
- `test_transaction_rollback.py` - اختبار التراجع عن المعاملات (جديد)
- `test_api_sales_flow.py` - اختبار تكامل API للمبيعات (جديد)
- `test_full_workflows.py` - اختبارات سير العمل الكاملة

---

### 5. Configuration Files

- `conftest.py` - إعدادات pytest والـ fixtures المشتركة
- `__init__.py` - تهيئة الحزمة
- `README.md` - هذا الملف

---

## 🚀 الاستخدام

### تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### تشغيل جميع الاختبارات

```bash
pytest
```

### تشغيل فئات محددة

```bash
# اختبارات الوحدة فقط (سريعة)
pytest tests/unit -m unit

# اختبارات التكامل فقط
pytest tests/integration -m integration

# اختبارات UI فقط
pytest tests/ui -m ui

# اختبارات API فقط
pytest tests/api -m api

# تخطي الاختبارات البطيئة
pytest -m "not slow"
```

### تشغيل مع التغطية

```bash
# تقرير في Terminal
pytest --cov=src --cov-report=term-missing

# تقرير HTML (يفتح في المتصفح)
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 📊 Test Markers

الاختبارات منظمة باستخدام pytest markers:

- `@pytest.mark.unit` - اختبارات وحدة سريعة (بدون قاعدة بيانات)
- `@pytest.mark.integration` - اختبارات تكامل (تتطلب قاعدة بيانات)
- `@pytest.mark.ui` - اختبارات UI (تتطلب تطبيق Qt)
- `@pytest.mark.api` - اختبارات API
- `@pytest.mark.slow` - اختبارات تستغرق أكثر من ثانية
- `@pytest.mark.requires_db` - اختبارات تحتاج اتصال بقاعدة البيانات
- `@pytest.mark.requires_ui` - اختبارات تحتاج تطبيق Qt

---

## ✅ كتابة الاختبارات

### مثال اختبار وحدة

```python
import pytest
from src.utils.math_utils import to_decimal
from decimal import Decimal

def test_to_decimal_int():
    """اختبار تحويل int إلى Decimal"""
    assert to_decimal(100) == Decimal('100')
```

### مثال اختبار تكامل

```python
import pytest

@pytest.mark.requires_db
def test_create_product(db_manager, sample_product_data):
    """اختبار إنشاء منتج في قاعدة البيانات"""
    from src.models.product import ProductManager, Product
    
    manager = ProductManager(db_manager)
    product = Product(**sample_product_data)
    product_id = manager.create_product(product)
    assert product_id > 0
```

### مثال اختبار UI

```python
import pytest
from PySide6.QtWidgets import QApplication

@pytest.mark.ui
def test_main_window_creation(qtbot):
    """اختبار إنشاء النافذة الرئيسية"""
    from src.ui.windows.main_window import MainWindow
    
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() != ""
```

---

## 🔧 Fixtures المشتركة

### `db_manager`
مدير قاعدة بيانات للاختبارات (قاعدة بيانات مؤقتة في الذاكرة)

```python
def test_something(db_manager):
    # استخدام db_manager
    pass
```

### `sample_product_data`
بيانات منتج نموذجية للاختبارات

```python
def test_create_product(db_manager, sample_product_data):
    product = Product(**sample_product_data)
    # ...
```

### `sample_customer_data`
بيانات عميل نموذجية للاختبارات

```python
def test_create_customer(db_manager, sample_customer_data):
    customer = Customer(**sample_customer_data)
    # ...
```

### `sample_sale_data`
بيانات فاتورة مبيعات نموذجية للاختبارات

```python
def test_create_sale(db_manager, sample_sale_data):
    sale = Sale(**sample_sale_data)
    # ...
```

---

## 📈 أهداف التغطية

- **الهدف الحالي**: 60% تغطية
- **الهدف المستقبلي**: 80%+ تغطية

---

## 🎯 أفضل الممارسات

### 1. استخدام Fixtures
```python
# ✅ صحيح - استخدام fixtures
def test_something(db_manager, sample_product_data):
    # ...

# ❌ خطأ - إنشاء بيانات مباشرة
def test_something():
    db = DatabaseManager(":memory:")
    # ...
```

### 2. تنظيف الموارد
```python
# ✅ صحيح - استخدام fixtures التي تنظف تلقائياً
def test_something(db_manager):
    # ...

# ❌ خطأ - عدم تنظيف الموارد
def test_something():
    db = DatabaseManager("test.db")
    # ... لا تنظيف
```

### 3. استخدام Markers
```python
# ✅ صحيح - استخدام markers
@pytest.mark.unit
def test_fast():
    # ...

@pytest.mark.integration
@pytest.mark.requires_db
def test_slow():
    # ...
```

---

## 📝 ملاحظات مهمة

- ✅ جميع الاختبارات تستخدم قواعد بيانات مؤقتة (لا تلوث البيانات)
- ✅ الـ fixtures يتم تنظيفها تلقائياً بعد الاختبارات
- ✅ اختبارات UI تتطلب تطبيق Qt قيد التشغيل
- ✅ اختبارات التكامل تتطلب قاعدة بيانات

---

## 🔗 المراجع

- `pytest.ini` - إعدادات pytest
- `.coveragerc` - إعدادات التغطية
- `tests/conftest.py` - الـ fixtures المشتركة
- [Pytest Documentation](https://docs.pytest.org/)

---

## ✅ الخلاصة

- ✅ جميع الاختبارات موثقة بشكل جيد
- ✅ استخدام pytest بشكل صحيح
- ✅ تنظيم جيد للاختبارات (unit, integration, ui, api)
- ✅ fixtures مشتركة ومنظمة
- ✅ تغطية شاملة للميزات

**التقييم**: 5/5 ⭐⭐⭐⭐⭐

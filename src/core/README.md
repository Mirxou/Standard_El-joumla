# Core Module - الوحدات الأساسية

## نظرة عامة
هذا المجلد يحتوي على الوحدات الأساسية للتطبيق، بما في ذلك إدارة قاعدة البيانات، التكوين، معالجة الأخطاء، والأمان.

## الملفات

### Database Management (إدارة قاعدة البيانات)

#### `database_manager.py` (1,392 سطر)
**الوصف**: مدير قاعدة البيانات الرئيسي

**الميزات**:
- ✅ إدارة الاتصالات (Connection Pool)
- ✅ تنفيذ الاستعلامات (Query Execution)
- ✅ إدارة المعاملات (Transactions)
- ✅ Migrations تلقائية
- ✅ النسخ الاحتياطي
- ✅ تحسين الأداء (WAL mode, Indexes)

**الاستخدام**:
```python
from src.core.database_manager import DatabaseManager

# تهيئة قاعدة البيانات
db = DatabaseManager("data/inventory.db")
db.initialize()

# تنفيذ استعلام
products = db.execute_query("SELECT * FROM products")

# تنفيذ عملية
db.execute_non_query("INSERT INTO products (name) VALUES (?)", ("Product",))
```

### Configuration Management (إدارة التكوين)

#### `config_manager.py` (672 سطر)
**الوصف**: مدير التكوين للتطبيق

**الميزات**:
- ✅ تحميل وحفظ الإعدادات
- ✅ دعم ملفات JSON و YAML
- ✅ Validation للإعدادات
- ✅ إعدادات افتراضية
- ✅ التشفير للإعدادات الحساسة

**الاستخدام**:
```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
config.load_config()

# الحصول على إعداد
value = config.get("setting_name", default_value)

# حفظ إعداد
config.set("setting_name", value)
config.save_config()
```

### Exception Handling (معالجة الأخطاء)

#### `exception_handler.py` (566 سطر)
**الوصف**: معالج الأخطاء المركزي

**الميزات**:
- ✅ معالجة شاملة للأخطاء
- ✅ تسجيل الأخطاء
- ✅ تقارير الأعطال
- ✅ تصنيف الأخطاء
- ✅ Recovery تلقائي

**الاستخدام**:
```python
from src.core.exception_handler import handle_exception

try:
    # كود قد يسبب خطأ
    pass
except Exception as e:
    handle_exception(e, context={"module": "my_module"})
```

#### `exceptions.py` (421 سطر)
**الوصف**: استثناءات مخصصة للتطبيق

**الميزات**:
- ✅ استثناءات مخصصة لكل نوع خطأ
- ✅ رسائل خطأ واضحة
- ✅ تصنيف الأخطاء
- ✅ معلومات سياقية

### Security (الأمان)

#### `security_service.py` (642 سطر)
**الوصف**: خدمة الأمان الرئيسية

**الميزات**:
- ✅ إدارة المستخدمين
- ✅ الصلاحيات والصلاحيات
- ✅ تسجيل الدخول
- ✅ التشفير
- ✅ Rate Limiting

#### `encryption_manager.py` (242 سطر)
**الوصف**: مدير التشفير

**الميزات**:
- ✅ تشفير البيانات
- ✅ فك التشفير
- ✅ إدارة المفاتيح
- ✅ Hashing

### Backup & Recovery (النسخ الاحتياطي والاستعادة)

#### `backup_manager.py` (526 سطر)
**الوصف**: مدير النسخ الاحتياطي

**الميزات**:
- ✅ نسخ احتياطي تلقائي
- ✅ نسخ احتياطي يدوي
- ✅ استعادة من النسخ الاحتياطي
- ✅ جدولة النسخ الاحتياطي

#### `encrypted_backup_service.py` (523 سطر)
**الوصف**: خدمة النسخ الاحتياطي المشفر

**الميزات**:
- ✅ تشفير النسخ الاحتياطي
- ✅ ضغط الملفات
- ✅ إدارة المفاتيح
- ✅ التحقق من السلامة

#### `incremental_backup_service.py` (404 سطر)
**الوصف**: خدمة النسخ الاحتياطي التدريجي

**الميزات**:
- ✅ نسخ احتياطي تدريجي
- ✅ توفير المساحة
- ✅ استعادة سريعة
- ✅ تتبع التغييرات

### Caching (التخزين المؤقت)

#### `cache_manager.py` (347 سطر)
**الوصف**: مدير التخزين المؤقت

**الميزات**:
- ✅ تخزين مؤقت للبيانات
- ✅ إدارة TTL
- ✅ تنظيف تلقائي
- ✅ إحصائيات الاستخدام

#### `caching_service.py` (547 سطر)
**الوصف**: خدمة التخزين المؤقت المتقدمة

**الميزات**:
- ✅ تخزين مؤقت متعدد المستويات
- ✅ Cache invalidation
- ✅ Prefetching
- ✅ تحليل الأداء

### Logging (السجلات)

#### `logging_service.py` (557 سطر)
**الوصف**: خدمة السجلات

**الميزات**:
- ✅ تسجيل شامل
- ✅ مستويات مختلفة
- ✅ تنسيق مخصص
- ✅ Rotation تلقائي

### Audit & Permissions (التدقيق والصلاحيات)

#### `audit_trail_manager.py` (631 سطر)
**الوصف**: مدير سجل التدقيق

**الميزات**:
- ✅ تتبع جميع العمليات
- ✅ سجل كامل للتغييرات
- ✅ تقارير التدقيق
- ✅ البحث والتصفية

#### `permission_manager.py` (617 سطر)
**الوصف**: مدير الصلاحيات

**الميزات**:
- ✅ إدارة الصلاحيات
- ✅ RBAC (Role-Based Access Control)
- ✅ التحقق من الصلاحيات
- ✅ تقارير الصلاحيات

### Printing (الطباعة)

#### `print_manager.py` (862 سطر)
**الوصف**: مدير الطباعة

**الميزات**:
- ✅ طباعة الفواتير
- ✅ طباعة التقارير
- ✅ دعم طابعات متعددة
- ✅ معاينة قبل الطباعة

### UI Components (مكونات الواجهة)

#### `error_dialog.py` (441 سطر)
**الوصف**: نافذة عرض الأخطاء

**الميزات**:
- ✅ عرض الأخطاء بشكل واضح
- ✅ تصنيف الأخطاء
- ✅ إمكانية الإبلاغ
- ✅ واجهة مستخدم جيدة

### Signals (الإشارات)

#### `signals.py` (104 سطر)
**الوصف**: نظام الإشارات للتطبيق

**الميزات**:
- ✅ إشارات للتحديثات
- ✅ Event-driven architecture
- ✅ Decoupling بين الوحدات

**الاستخدام**:
```python
from src.core.signals import signals

# الاستماع لإشارة
signals.sales_updated.connect(self.refresh_sales)

# إطلاق إشارة
signals.sales_updated.emit()
```

## الإحصائيات

- **إجمالي الملفات**: 18 ملف Python
- **إجمالي الأسطر**: ~10,000+ سطر
- **أكبر ملف**: `database_manager.py` (1,392 سطر)
- **أصغر ملف**: `signals.py` (104 سطر)

## التكامل

جميع الوحدات الأساسية متكاملة مع:
- `main.py` - التطبيق الرئيسي
- `src/ui/` - واجهة المستخدم
- `src/services/` - الخدمات
- `src/models/` - النماذج

## الأمان

- ✅ تشفير البيانات الحساسة
- ✅ إدارة آمنة للمفاتيح
- ✅ التحقق من الصلاحيات
- ✅ تسجيل جميع العمليات

## الأداء

- ✅ Connection Pooling
- ✅ Caching متقدم
- ✅ Indexes محسّنة
- ✅ WAL mode لـ SQLite

## الاختبارات

جميع الوحدات الأساسية لديها اختبارات:
- `tests/unit/test_database_manager.py`
- `tests/unit/test_config_manager.py`
- `tests/unit/test_exception_handler.py`
- وغيرها...

## التطوير المستقبلي

- [ ] تحسين الأداء
- [ ] دعم المزيد من قواعد البيانات
- [ ] تحسين الأمان
- [ ] ميزات جديدة


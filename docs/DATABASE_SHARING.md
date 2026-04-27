# دليل مشاركة قاعدة البيانات
## Database Sharing Guide

**التاريخ:** 2025-01-16  
**النسخة:** 1.0

---

## نظرة عامة

يستخدم النظام قاعدة بيانات SQLite مشتركة بين تطبيق سطح المكتب (Desktop) و FastAPI (Web API). هذا الدليل يشرح كيفية عمل مشاركة قاعدة البيانات وأفضل الممارسات.

---

## البنية المعمارية

### مسار قاعدة البيانات الموحد

```
{project_root}/
└── data/
    └── logical_release.db  ← قاعدة البيانات المشتركة
```

**كلا التطبيقات يستخدمان نفس الملف:**
- Desktop App: `ConfigManager.get_database_path()`
- FastAPI: `ConfigManager.get_database_path()`

---

## SQLite WAL Mode

### ما هو WAL Mode؟

WAL (Write-Ahead Logging) هو وضع SQLite الذي يسمح بقراءة وكتابة متزامنة من عدة اتصالات.

### المزايا:
- ✅ قراءة متزامنة غير محظورة
- ✅ أداء أفضل في التطبيقات متعددة الخيوط
- ✅ تقليل احتمالية قفل قاعدة البيانات

### التفعيل:

تم تفعيل WAL mode تلقائياً في `DatabaseManager.initialize()`:

```python
self.connection.execute("PRAGMA journal_mode=WAL")
```

---

## معالجة أخطاء القفل (Lock Handling)

### متى تحدث أخطاء القفل؟

1. **كتابة متزامنة:** محاولة كتابة من اتصالات متعددة في نفس الوقت
2. **عمليات طويلة:** استعلامات تستغرق وقتاً طويلاً
3. **اتصالات معلقة:** اتصالات لم تُغلق بشكل صحيح

### آلية إعادة المحاولة

تم إضافة `DatabaseLockHandler` في `src/core/database_lock_handler.py`:

```python
from src.core.database_lock_handler import retry_on_lock_error, DatabaseLockHandler

# استخدام decorator
@retry_on_lock_error(max_retries=5)
def my_database_operation():
    # كود قاعدة البيانات
    pass

# أو استخدام class
handler = DatabaseLockHandler(max_retries=5)
result = handler.execute_with_retry(my_function, arg1, arg2)
```

### إعدادات إعادة المحاولة:

- **MAX_RETRIES:** 5 محاولات (افتراضي)
- **INITIAL_DELAY:** 0.1 ثانية
- **MAX_DELAY:** 2.0 ثانية
- **BACKOFF_MULTIPLIER:** 2.0 (exponential backoff)

---

## Connection Pooling

### ما هو Connection Pooling؟

Connection Pooling يحافظ على مجموعة من الاتصالات الجاهزة للاستخدام، مما يقلل من وقت إنشاء الاتصالات.

### الإعدادات الحالية:

```python
PoolConfig(
    pool_size=15,        # عدد الاتصالات الأساسية
    max_overflow=30,     # الحد الأقصى للاتصالات الإضافية
    timeout=60.0         # وقت انتظار الاتصال بالثواني
)
```

### الاستخدام:

```python
# DatabaseManager يستخدم ConnectionPool تلقائياً
db_manager = DatabaseManager()
db_manager.initialize()

# الحصول على اتصال من الـ pool
with db_manager.get_cursor() as cursor:
    cursor.execute("SELECT * FROM products")
    results = cursor.fetchall()
```

---

## أفضل الممارسات

### 1. استخدام Context Managers

**✅ جيد:**
```python
with db_manager.get_cursor() as cursor:
    cursor.execute("INSERT INTO products ...")
    # الاتصال يُغلق تلقائياً
```

**❌ سيء:**
```python
cursor = db_manager.connection.cursor()
cursor.execute("INSERT INTO products ...")
# قد ينسى إغلاق الاتصال
```

### 2. معالجة الأخطاء

**✅ جيد:**
```python
try:
    with db_manager.get_cursor() as cursor:
        cursor.execute("UPDATE products SET ...")
except sqlite3.OperationalError as e:
    if "database is locked" in str(e).lower():
        # إعادة المحاولة أو إعلام المستخدم
        pass
```

### 3. تجنب العمليات الطويلة

**✅ جيد:**
```python
# تقسيم العملية الكبيرة إلى عمليات صغيرة
for batch in batches:
    with db_manager.get_cursor() as cursor:
        cursor.executemany("INSERT INTO products ...", batch)
```

**❌ سيء:**
```python
# عملية واحدة كبيرة قد تحجب قاعدة البيانات
with db_manager.get_cursor() as cursor:
    cursor.executemany("INSERT INTO products ...", all_products)  # 10000+ منتج
```

### 4. استخدام Transactions

**✅ جيد:**
```python
with db_manager.get_cursor() as cursor:
    try:
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("INSERT INTO products ...")
        cursor.execute("UPDATE inventory ...")
        cursor.execute("COMMIT")
    except Exception:
        cursor.execute("ROLLBACK")
        raise
```

---

## مراقبة الأداء

### فحص حالة قاعدة البيانات:

```python
# معلومات قاعدة البيانات
info = db_manager.get_database_info()
print(f"الحجم: {info['size_mb']} MB")
print(f"عدد الجداول: {info['table_count']}")
print(f"عدد الاتصالات النشطة: {info['active_connections']}")
```

### فحص WAL Mode:

```python
cursor = db_manager.connection.cursor()
cursor.execute("PRAGMA journal_mode")
mode = cursor.fetchone()[0]
print(f"Journal Mode: {mode}")  # يجب أن يكون "wal"
```

---

## استكشاف الأخطاء

### المشكلة: "database is locked"

**الأسباب المحتملة:**
1. اتصال لم يُغلق بشكل صحيح
2. عملية طويلة قيد التنفيذ
3. عدد كبير من الاتصالات المتزامنة

**الحلول:**
1. استخدام `with` statements لضمان إغلاق الاتصالات
2. تقسيم العمليات الكبيرة
3. زيادة `timeout` في Connection Pool
4. استخدام `DatabaseLockHandler` لإعادة المحاولة

### المشكلة: "disk I/O error"

**الأسباب المحتملة:**
1. مساحة القرص ممتلئة
2. مشاكل في نظام الملفات
3. قاعدة البيانات تالفة

**الحلول:**
1. فحص مساحة القرص
2. تشغيل `VACUUM` على قاعدة البيانات
3. استعادة من backup

---

## الأمان

### 1. الوصول المتزامن

- SQLite يدعم قراءة متزامنة من عدة اتصالات
- الكتابة المتزامنة قد تسبب قفل - استخدم retry logic

### 2. النسخ الاحتياطي

- النسخ الاحتياطي التلقائي مفعل
- يتم إنشاء backups في `data/backups/`
- النسخ مشفر عند التمكين

### 3. التشفير

- يمكن تشفير قاعدة البيانات باستخدام `EncryptionManager`
- كلمة المرور مطلوبة للوصول

---

## الخلاصة

1. ✅ قاعدة البيانات موحدة بين Desktop و FastAPI
2. ✅ WAL mode مفعل للأداء الأفضل
3. ✅ Connection Pooling للكفاءة
4. ✅ Retry logic لأخطاء القفل
5. ✅ Context managers لضمان إغلاق الاتصالات

---

**آخر تحديث:** 2025-01-16


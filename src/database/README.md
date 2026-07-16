# Database Module - وحدات قاعدة البيانات

## نظرة عامة
هذا المجلد يحتوي على وحدات إدارة اتصالات قاعدة البيانات، بما في ذلك Connection Pooling.

## الملفات

### `connection_pool.py` (499 سطر)
**الوصف**: خدمة Connection Pooling لإدارة اتصالات قاعدة البيانات بكفاءة

**الميزات**:
- ✅ Pool بحجم قابل للتكوين (15 اتصال افتراضي)
- ✅ دعم Overflow (30 اتصال إضافي مؤقت)
- ✅ إعادة تدوير الاتصالات القديمة (بعد ساعة)
- ✅ فحص سلامة الاتصالات (كل 5 دقائق)
- ✅ Thread-safe (آمن للاستخدام في بيئة متعددة الخيوط)
- ✅ إحصائيات الاستخدام
- ✅ معالجة Timeout
- ✅ دعم Transactions

**الاستخدام**:
```python
from src.database import ConnectionPool, PoolConfig

# تهيئة Pool مع إعدادات مخصصة
config = PoolConfig(
    pool_size=15,
    max_overflow=30,
    timeout=60.0,
    recycle=3600
)

pool = ConnectionPool("data/inventory.db", config)

# استخدام الاتصال
with pool.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    results = cursor.fetchall()

# استخدام execute helper
products = pool.execute("SELECT * FROM products")

# استخدام transaction
with pool.transaction() as conn:
    conn.execute("INSERT INTO products (name) VALUES (?)", ("Product",))
    conn.execute("UPDATE products SET stock = stock - 1 WHERE id = ?", (1,))
```

**الكلاسات**:
- `PoolConfig` - تكوين Connection Pool
  - `pool_size`: حجم Pool (افتراضي: 15)
  - `max_overflow`: أقصى عدد اتصالات إضافية (افتراضي: 30)
  - `timeout`: مهلة انتظار اتصال بالثواني (افتراضي: 60.0)
  - `recycle`: إعادة تدوير الاتصال بعد ثواني (افتراضي: 3600)
  - `enable_health_check`: تفعيل فحص السلامة (افتراضي: True)
  - `health_check_interval`: فترة فحص السلامة بالثواني (افتراضي: 300)

- `PooledConnection` - اتصال في Pool
  - `connection`: الاتصال الفعلي
  - `created_at`: وقت الإنشاء
  - `last_used`: آخر استخدام
  - `in_use`: حالة الاستخدام
  - `uses`: عدد مرات الاستخدام
  - `is_expired()`: التحقق من انتهاء الصلاحية
  - `is_healthy()`: التحقق من السلامة
  - `mark_used()`: تعليم كمستخدم
  - `mark_returned()`: تعليم كمُعاد

- `ConnectionPool` - Pool الرئيسي
  - `get_connection()`: الحصول على اتصال (context manager)
  - `execute()`: تنفيذ استعلام مع إدارة تلقائية
  - `execute_many()`: تنفيذ استعلام متعدد
  - `transaction()`: بدء معاملة (context manager)
  - `get_stats()`: الحصول على إحصائيات
  - `close()`: إغلاق Pool

## المزايا

### 1. الأداء
- **تقليل وقت الاتصال**: إعادة استخدام الاتصالات الموجودة
- **تحسين الاستجابة**: لا حاجة لإنشاء اتصال جديد في كل مرة
- **معالجة الحمل**: دعم Overflow للذروات

### 2. الموثوقية
- **فحص السلامة**: التحقق من صحة الاتصالات تلقائياً
- **إعادة التدوير**: استبدال الاتصالات القديمة
- **معالجة الأخطاء**: معالجة شاملة للأخطاء

### 3. المراقبة
- **إحصائيات**: تتبع الاستخدام والأداء
- **Health Checks**: فحص دوري للاتصالات
- **Timeouts**: منع الانتظار اللانهائي

## التكامل مع DatabaseManager

يتم استخدام Connection Pool في `DatabaseManager`:

```python
from src.core.database_manager import DatabaseManager

# تهيئة مع Pool
db = DatabaseManager(
    db_path="data/inventory.db",
    pool_options={
        'enabled': True,
        'pool_size': 15,
        'max_overflow': 30,
        'timeout': 60.0
    }
)
db.initialize()

# استخدام تلقائي للـ Pool
products = db.execute_query("SELECT * FROM products")
```

## الإحصائيات

يمكن الحصول على إحصائيات Pool:

```python
stats = pool.get_stats()
print(f"Connections created: {stats['connections_created']}")
print(f"Checkouts: {stats['checkouts']}")
print(f"Checkins: {stats['checkins']}")
print(f"Timeouts: {stats['timeouts']}")
print(f"Health checks: {stats['health_checks']}")
print(f"Recycled: {stats['recycled']}")
```

## Thread Safety

Connection Pool آمن للاستخدام في بيئة متعددة الخيوط:
- ✅ استخدام `threading.RLock` للعمليات الحساسة
- ✅ Queue thread-safe للاتصالات
- ✅ SQLite في وضع WAL (يدعم القراءة المتزامنة)

## الأداء

### الإعدادات الموصى بها

**للتطبيقات الصغيرة (< 10K منتج)**:
```python
config = PoolConfig(
    pool_size=5,
    max_overflow=10,
    timeout=30.0
)
```

**للتطبيقات المتوسطة (10K - 100K منتج)**:
```python
config = PoolConfig(
    pool_size=10,
    max_overflow=20,
    timeout=45.0
)
```

**للتطبيقات الكبيرة (> 100K منتج)**:
```python
config = PoolConfig(
    pool_size=15,
    max_overflow=30,
    timeout=60.0
)
```

## الاختبارات

يمكن اختبار Connection Pool:

```bash
python src/database/connection_pool.py
```

هذا سيقوم بتشغيل اختبارات شاملة للـ Pool.

## الأمان

- ✅ معالجة آمنة للأخطاء
- ✅ إغلاق آمن للاتصالات
- ✅ منع تسريب الاتصالات
- ✅ Thread-safe

## التطوير المستقبلي

- [ ] دعم قواعد بيانات أخرى (PostgreSQL, MySQL)
- [ ] Connection Pooling متقدم
- [ ] Load Balancing
- [ ] Monitoring متقدم

## المراجع

- `src/core/database_manager.py` - استخدام Connection Pool
- `docs/DATABASE_MANAGEMENT_GUIDE.md` - دليل إدارة قاعدة البيانات


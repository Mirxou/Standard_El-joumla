# دليل معالجة قفل قاعدة البيانات
## Database Lock Handling Guide

**التاريخ:** 2025-01-16

---

## نظرة عامة

تم إضافة `DatabaseLockHandler` لمعالجة أخطاء قفل قاعدة البيانات تلقائياً باستخدام retry logic مع exponential backoff.

---

## الاستخدام

### 1. استخدام Decorator

```python
from src.core.database_lock_handler import retry_on_lock_error

@retry_on_lock_error(max_retries=5)
def update_product(db_manager, product_id, data):
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "UPDATE products SET name = ?, price = ? WHERE id = ?",
            (data['name'], data['price'], product_id)
        )
        cursor.connection.commit()
```

### 2. استخدام Class

```python
from src.core.database_lock_handler import DatabaseLockHandler

handler = DatabaseLockHandler(max_retries=5)

def my_operation():
    with db_manager.get_cursor() as cursor:
        cursor.execute("INSERT INTO products ...")
        cursor.connection.commit()

# تنفيذ مع retry
result = handler.execute_with_retry(my_operation)
```

### 3. دمج مع DatabaseManager

لدمج `DatabaseLockHandler` مع `DatabaseManager`، يمكن إضافة wrapper methods:

```python
# في DatabaseManager
from src.core.database_lock_handler import DatabaseLockHandler

class DatabaseManager:
    def __init__(self, ...):
        # ...
        self.lock_handler = DatabaseLockHandler(max_retries=5)
    
    def execute_with_retry(self, query, params=None):
        """تنفيذ استعلام مع retry logic"""
        return self.lock_handler.execute_with_retry(
            self.execute_query,
            query,
            params
        )
```

---

## الإعدادات

### القيم الافتراضية:

- **MAX_RETRIES:** 5
- **INITIAL_DELAY:** 0.1 ثانية
- **MAX_DELAY:** 2.0 ثانية
- **BACKOFF_MULTIPLIER:** 2.0

### تخصيص الإعدادات:

```python
handler = DatabaseLockHandler(
    max_retries=10,        # 10 محاولات
    initial_delay=0.05,    # 50ms
    max_delay=5.0,         # 5 ثواني
    backoff_multiplier=1.5 # backoff أبطأ
)
```

---

## أنواع الأخطاء المعالجة

### 1. OperationalError
- "database is locked"
- "database locked"
- "unable to open database"

### 2. DatabaseError
- SQLITE_BUSY (5)
- SQLITE_LOCKED (6)
- SQLITE_IOERR (10)
- SQLITE_PROTOCOL (15)

---

## أمثلة

### مثال 1: تحديث منتج

```python
@retry_on_lock_error(max_retries=3)
def update_product_safe(db_manager, product_id, name, price):
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "UPDATE products SET name = ?, price = ? WHERE id = ?",
            (name, price, product_id)
        )
        cursor.connection.commit()
```

### مثال 2: إدراج متعدد

```python
handler = DatabaseLockHandler(max_retries=5)

def insert_products_batch(products):
    def _insert():
        with db_manager.get_cursor() as cursor:
            cursor.executemany(
                "INSERT INTO products (name, price) VALUES (?, ?)",
                products
            )
            cursor.connection.commit()
    
    return handler.execute_with_retry(_insert)
```

---

## أفضل الممارسات

1. **استخدم retry logic للعمليات الحرجة:**
   - تحديثات مهمة
   - إدراج بيانات جديدة
   - عمليات مزامنة

2. **لا تستخدم retry للعمليات السريعة:**
   - قراءة بسيطة
   - استعلامات SELECT فقط

3. **راقب عدد المحاولات:**
   - إذا فشلت جميع المحاولات، قد تكون هناك مشكلة أكبر
   - تحقق من حالة قاعدة البيانات

---

**آخر تحديث:** 2025-01-16


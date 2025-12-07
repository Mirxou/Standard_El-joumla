# 🗄️ دليل إدارة قاعدة البيانات - Database Management Guide

## نظرة عامة

يستخدم نظام الإصدار المنطقي SQLite مع ميزات متقدمة لإدارة قاعدة البيانات:
- Connection Pooling
- WAL Mode
- النسخ الاحتياطي التلقائي
- التشفير
- التنظيف والتحسين

## DatabaseManager

### التهيئة

```python
from src.core.database_manager import DatabaseManager

# تهيئة بسيطة
db_manager = DatabaseManager()
db_manager.initialize()

# تهيئة مخصصة
db_manager = DatabaseManager(
    db_path="data/custom.db",
    encryption_password="your_password",
    pool_options={
        "enabled": True,
        "pool_size": 10,
        "max_overflow": 20,
        "timeout": 30
    }
)
db_manager.initialize()
```

### الوظائف الأساسية

#### `get_connection()`

الحصول على اتصال من الـ Pool:

```python
with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    results = cursor.fetchall()
```

#### `execute_query(query, params=())`

تنفيذ استعلام والحصول على النتائج:

```python
# SELECT query (يرجع list of dicts)
results = db_manager.execute_query(
    "SELECT * FROM products WHERE category_id = ?",
    (category_id,)
)

# INSERT/UPDATE/DELETE query
db_manager.execute_query(
    "INSERT INTO products (name, price) VALUES (?, ?)",
    ("Product Name", 100.0)
)
```

#### `execute_scalar(query, params=())`

تنفيذ استعلام والحصول على قيمة واحدة:

```python
count = db_manager.execute_scalar("SELECT COUNT(*) FROM products")
```

## Backup & Restore

### إنشاء نسخة احتياطية

```python
# نسخة احتياطية عادية
success = db_manager.backup_database()

# نسخة احتياطية مشفرة
backup_file = db_manager.backup_database_encrypted(
    metadata={
        'type': 'manual',
        'description': 'Backup before update'
    }
)
```

### استعادة نسخة احتياطية

```python
# استعادة عادية
success = db_manager.restore_database("data/backups/backup_20250115.db")

# استعادة مشفرة
success = db_manager.restore_database_encrypted(
    "data/backups/backup_20250115.db.encrypted",
    password="your_password"
)
```

### تنظيف النسخ القديمة

```python
# الاحتفاظ بآخر 30 نسخة فقط
db_manager.cleanup_old_backups(max_backups=30)
```

## WAL Management

### دمج ملفات WAL

```python
# دمج WAL في قاعدة البيانات الرئيسية
success = db_manager.checkpoint_wal()

if success:
    print("تم دمج WAL بنجاح")
```

### معلومات الحجم

```python
size_info = db_manager.get_database_size_info()

print(f"حجم قاعدة البيانات: {size_info['database_size_mb']} MB")
print(f"حجم WAL: {size_info['wal_size_mb']} MB")
print(f"الحجم الإجمالي: {size_info['total_size_mb']} MB")
```

## Database Optimization

### تنظيف قاعدة البيانات

```python
# تنظيف وتحسين قاعدة البيانات
success = db_manager.vacuum_database()

if success:
    print("تم تنظيف قاعدة البيانات بنجاح")
```

### تنظيف البيانات القديمة

```python
# حذف البيانات الأقدم من 90 يوم
deleted = db_manager.cleanup_old_data(days=90)

print(f"تم حذف {sum(deleted.values())} سجل")
for table, count in deleted.items():
    print(f"  - {table}: {count} سجل")
```

### الجداول المدعومة للتنظيف

- `audit_logs` - سجلات التدقيق
- `login_history` - سجل تسجيلات الدخول
- `slow_queries` - الاستعلامات البطيئة
- `backup_history` - سجل النسخ الاحتياطية
- `session_logs` - سجلات الجلسات

### مثال متقدم

```python
# تنظيف مخصص
deleted = db_manager.cleanup_old_data(
    days=30,
    tables=['audit_logs', 'login_history']
)
```

## Database Info

### الحصول على معلومات قاعدة البيانات

```python
info = db_manager.get_database_info()

print(f"عدد الجداول: {info['tables_count']}")
print(f"حجم قاعدة البيانات: {info['size_mb']} MB")
print(f"عدد السجلات:")
for table, count in info['records'].items():
    print(f"  - {table}: {count}")
```

## Performance Optimization

### Connection Pooling

```python
# إعدادات الـ Pool من الإعدادات
from src.core.config_manager import ConfigManager

config = ConfigManager()
config.load_config()
pool_settings = config.get_database_pool_settings()

db_manager = DatabaseManager(
    pool_options=pool_settings
)
```

### PRAGMA Settings

يتم تعيين PRAGMA تلقائياً عند التهيئة:

```python
# WAL Mode
PRAGMA journal_mode=WAL

# Synchronous
PRAGMA synchronous=NORMAL

# Cache Size
PRAGMA cache_size=10000

# Foreign Keys
PRAGMA foreign_keys=ON
```

## Encryption

### تفعيل التشفير

```python
from src.core.encryption_manager import EncryptionManager

encryption_manager = EncryptionManager()
encryption_manager.encrypt_database(
    db_path="data/database.db",
    password="your_password",
    backup_original=True
)
```

### فك التشفير

```python
encryption_manager.decrypt_database(
    encrypted_db_path="data/database.db",
    password="your_password",
    output_path="data/database_decrypted.db"
)
```

## Migration Management

### تشغيل Migrations

يتم تشغيل Migrations تلقائياً عند التهيئة:

```python
db_manager.initialize()  # يشغل migrations تلقائياً
```

### إنشاء Migration جديد

1. أنشئ ملف SQL في `migrations/`:

```sql
-- migrations/016_add_new_table.sql
CREATE TABLE IF NOT EXISTS new_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

2. سيتم تشغيله تلقائياً عند التهيئة التالية

## Monitoring

### مراقبة الأداء

```python
# معلومات الحجم
size_info = db_manager.get_database_size_info()

# معلومات قاعدة البيانات
db_info = db_manager.get_database_info()

# عدد الاتصالات النشطة
active_connections = db_manager.pool.get_active_connections_count()
```

### Slow Query Logging

يتم تسجيل الاستعلامات البطيئة تلقائياً في جدول `slow_queries`:

```python
# الحصول على الاستعلامات البطيئة
slow_queries = db_manager.execute_query("""
    SELECT * FROM slow_queries 
    ORDER BY duration_ms DESC 
    LIMIT 10
""")
```

## أمثلة عملية

### مثال 1: نسخ احتياطي يومي

```python
from datetime import datetime
import schedule
import time

def daily_backup():
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    # إنشاء نسخة احتياطية
    backup_file = db_manager.backup_database_encrypted(
        metadata={'type': 'daily', 'date': datetime.now().isoformat()}
    )
    
    if backup_file:
        print(f"تم إنشاء النسخة الاحتياطية: {backup_file}")
        
        # تنظيف النسخ القديمة (الاحتفاظ بآخر 30)
        db_manager.cleanup_old_backups(max_backups=30)

# جدولة النسخ اليومي الساعة 2 صباحاً
schedule.every().day.at("02:00").do(daily_backup)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### مثال 2: تنظيف أسبوعي

```python
def weekly_cleanup():
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    # دمج WAL
    db_manager.checkpoint_wal()
    
    # تنظيف البيانات القديمة (أقدم من 90 يوم)
    deleted = db_manager.cleanup_old_data(days=90)
    
    # تنظيف قاعدة البيانات
    db_manager.vacuum_database()
    
    print(f"تم تنظيف {sum(deleted.values())} سجل")

# جدولة التنظيف الأسبوعي
schedule.every().sunday.at("03:00").do(weekly_cleanup)
```

### مثال 3: مراقبة الحجم

```python
def monitor_database_size():
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    size_info = db_manager.get_database_size_info()
    
    # تحذير إذا تجاوز الحجم 100 MB
    if size_info['total_size_mb'] > 100:
        print(f"تحذير: حجم قاعدة البيانات كبير ({size_info['total_size_mb']} MB)")
        
        # دمج WAL
        db_manager.checkpoint_wal()
        
        # تنظيف البيانات القديمة
        db_manager.cleanup_old_data(days=60)
        
        # تنظيف قاعدة البيانات
        db_manager.vacuum_database()

# مراقبة كل ساعة
schedule.every().hour.do(monitor_database_size)
```

## استكشاف الأخطاء

### المشكلة: "database is locked"

**الحل:**
1. تأكد من إغلاق جميع الاتصالات
2. استخدم Connection Pool
3. تحقق من وجود عمليات أخرى تستخدم قاعدة البيانات

### المشكلة: "WAL file كبير"

**الحل:**
```python
db_manager.checkpoint_wal()  # دمج WAL
```

### المشكلة: "قاعدة البيانات بطيئة"

**الحل:**
```python
# تنظيف وتحسين
db_manager.vacuum_database()

# تنظيف البيانات القديمة
db_manager.cleanup_old_data(days=90)
```

---

**تم إنشاء هذا الدليل بواسطة:** Logical Version Team  
**التاريخ:** 2025-01-15  
**الإصدار:** 5.3.0


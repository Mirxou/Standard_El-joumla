# مجلد البيانات - Data Directory

هذا المجلد يحتوي على جميع بيانات التطبيق والملفات المولدة.

## البنية

```
data/
├── logical_release.db          # قاعدة البيانات الرئيسية
├── logical_release.db-wal      # ملف WAL (Write-Ahead Logging)
├── logical_release.db-shm      # ملف الذاكرة المشتركة
├── backups/                    # النسخ الاحتياطية
│   └── .gitkeep
├── exports/                    # الملفات المُصدّرة (تقارير، إلخ)
│   └── .gitkeep
├── templates/                  # القوالب المخصصة
│   └── .gitkeep
└── cache/                      # التخزين المؤقت (إذا كان مفعلاً)
```

## الوظائف المتاحة

### 1. تنظيف ملفات WAL

دمج ملفات WAL في قاعدة البيانات الرئيسية:

```python
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize()
db_manager.checkpoint_wal()  # دمج WAL
```

### 2. مراقبة حجم قاعدة البيانات

الحصول على معلومات حجم قاعدة البيانات:

```python
size_info = db_manager.get_database_size_info()
print(f"حجم قاعدة البيانات: {size_info['database_size_mb']} MB")
print(f"حجم WAL: {size_info['wal_size_mb']} MB")
print(f"الحجم الإجمالي: {size_info['total_size_mb']} MB")
```

### 3. تنظيف قاعدة البيانات

تنظيف وتحسين قاعدة البيانات:

```python
db_manager.vacuum_database()  # تنظيف وتحسين
```

### 4. تنظيف البيانات القديمة

حذف البيانات القديمة من الجداول:

```python
# حذف البيانات الأقدم من 90 يوم
deleted = db_manager.cleanup_old_data(days=90)
print(f"تم حذف {sum(deleted.values())} سجل")
```

### 5. تنظيف النسخ الاحتياطية القديمة

حذف النسخ الاحتياطية الزائدة:

```python
# الاحتفاظ بآخر 30 نسخة فقط
db_manager.cleanup_old_backups(max_backups=30)
```

## الإعدادات

يمكن تخصيص إعدادات البيانات من `config/app_config.json`:

- `database.path`: مسار قاعدة البيانات
- `database.backups.backup_dir`: مجلد النسخ الاحتياطية
- `reports.save_path`: مجلد التصدير
- `cache.disk_path`: مجلد التخزين المؤقت

## ملاحظات

- ملفات `.db-wal` و `.db-shm` يتم إنشاؤها تلقائياً بواسطة SQLite
- المجلدات الفارغة تحتوي على `.gitkeep` للحفاظ على البنية في Git
- يتم إنشاء المجلدات تلقائياً عند تحميل الإعدادات


# ⚙️ دليل إعداد النظام - Configuration Guide

## نظرة عامة

يستخدم نظام ستاندرد الجملة نظام إعدادات مرن يدعم:
- ملفات JSON للإعدادات
- متغيرات البيئة
- تشفير القيم الحساسة
- التحقق من صحة الإعدادات

## الملفات

### `config/app_config.json`

الملف الرئيسي لإعدادات التطبيق:

```json
{
  "database": {
    "path": "data/logical_release.db",
    "backup_interval": 24,
    "max_backups": 30,
    "pool": {
      "enabled": true,
      "pool_size": 10,
      "max_overflow": 20,
      "timeout": 30
    },
    "backups": {
      "encrypted": true,
      "backup_dir": "data/backups",
      "max_backups": 30,
      "encryption_key_path": null
    }
  },
  "ui": {
    "language": "ar",
    "theme": "light",
    "rtl": true,
    "font_family": "Segoe UI",
    "font_size": 10
  },
  "security": {
    "session_timeout": 480,
    "password_min_length": 6,
    "enable_audit_log": true,
    "encrypt_sensitive_config": true,
    "encryption_key_env": "APP_ENCRYPTION_KEY"
  }
}
```

### `config/dev_config.json`

إعدادات التطوير:

```json
{
  "debug": true,
  "log_level": "DEBUG",
  "auto_reload": true,
  "test_data": true
}
```

## ConfigManager

### الاستخدام الأساسي

```python
from src.core.config_manager import ConfigManager

# إنشاء مدير الإعدادات
config = ConfigManager()
config.load_config()

# الحصول على قيمة
db_path = config.get('database.path')
language = config.get('ui.language', 'ar')  # مع قيمة افتراضية

# تعيين قيمة
config.set('ui.theme', 'dark')
config.save_config()
```

### الدوال المتاحة

#### `get(key, default=None, use_env=True)`

الحصول على قيمة إعداد:

```python
# من ملف الإعدادات
value = config.get('database.path')

# مع قيمة افتراضية
value = config.get('database.path', 'data/default.db')

# بدون استخدام متغيرات البيئة
value = config.get('database.path', use_env=False)
```

#### `set(key, value)`

تعيين قيمة إعداد:

```python
config.set('ui.theme', 'dark')
config.set('database.backup_interval', 48)
config.save_config()  # حفظ التغييرات
```

#### دوال الإعدادات المتخصصة

```python
# إعدادات قاعدة البيانات
db_settings = config.get_database_path()
backup_settings = config.get_backup_settings()
pool_settings = config.get_database_pool_settings()

# إعدادات واجهة المستخدم
ui_settings = config.get_ui_settings()

# إعدادات الأمان
security_settings = config.get_security_settings()

# إعدادات البريد الإلكتروني
email_settings = config.get_email_settings()

# إعدادات الطباعة
printing_settings = config.get_printing_settings()

# إعدادات API
api_settings = config.get_api_settings()

# إعدادات الإشعارات
notifications_settings = config.get_notifications_settings()

# إعدادات القوالب
templates_settings = config.get_templates_settings()

# إعدادات الشركة
company_settings = config.get_company_settings()

# إعدادات التخزين المؤقت
cache_settings = config.get_cache_settings()
```

## Environment Variables

### دعم متغيرات البيئة

يدعم النظام استخدام متغيرات البيئة لتجاوز الإعدادات في الملف:

```bash
# Windows
set DATABASE_PATH=C:\data\custom.db
set SMTP_SERVER=smtp.example.com
set API_KEY=your_api_key_here

# Linux/Mac
export DATABASE_PATH=/data/custom.db
export SMTP_SERVER=smtp.example.com
export API_KEY=your_api_key_here
```

### المفاتيح المدعومة

- `DATABASE_PATH` → `database.path`
- `SMTP_SERVER` → `email.smtp_server`
- `SMTP_PORT` → `email.smtp_port`
- `SMTP_USERNAME` → `email.smtp_username`
- `SMTP_PASSWORD` → `email.smtp_password`
- `API_BASE_URL` → `api.base_url`
- `API_KEY` → `api.api_key`
- `COMPANY_NAME` → `company.name`
- `COMPANY_EMAIL` → `company.email`
- `COMPANY_PHONE` → `company.phone`

### مثال

```python
# في ملف الإعدادات
"email": {
  "smtp_server": "smtp.default.com"
}

# متغير البيئة
export SMTP_SERVER=smtp.production.com

# النتيجة: سيستخدم smtp.production.com
```

## Sensitive Data Encryption

### تفعيل التشفير

1. تعيين متغير البيئة:

```bash
export APP_ENCRYPTION_KEY=your_secret_key_here
```

2. تفعيل التشفير في الإعدادات:

```json
{
  "security": {
    "encrypt_sensitive_config": true,
    "encryption_key_env": "APP_ENCRYPTION_KEY"
  }
}
```

### المفاتيح المشفرة تلقائياً

- `email.smtp_password`
- `email.smtp_username`
- `api.api_key`
- `security.encryption_key`
- `company.tax_number`
- `company.commercial_registration`

### مثال

```python
# قبل التشفير
config.set('email.smtp_password', 'my_password')
config.save_config()
# في الملف: "smtp_password": "my_password"

# بعد تفعيل التشفير
config.set('email.smtp_password', 'my_password')
config.save_config()
# في الملف: "smtp_password": "encrypted:base64_encoded_string"
```

## Validation

### التحقق من صحة الإعدادات

```python
errors = config.validate_config()

if errors:
    for error in errors:
        print(f"خطأ: {error}")
else:
    print("جميع الإعدادات صحيحة")
```

### التحققات المتاحة

- إعدادات البريد الإلكتروني (إذا كان مفعلاً)
- إعدادات API (إذا كان مفعلاً)
- إعدادات الطباعة (حجم الورق، الاتجاه)
- وجود القوالب المطلوبة
- صحة البريد الإلكتروني والموقع الإلكتروني

## أمثلة عملية

### مثال 1: إعداد البريد الإلكتروني

```python
config = ConfigManager()
config.load_config()

# تعيين إعدادات البريد
config.set('email.enabled', True)
config.set('email.smtp_server', 'smtp.gmail.com')
config.set('email.smtp_port', 587)
config.set('email.smtp_username', 'your_email@gmail.com')
config.set('email.smtp_password', 'your_password')
config.set('email.smtp_use_tls', True)
config.set('email.from_email', 'your_email@gmail.com')
config.set('email.from_name', 'Your Company')

# التحقق من الصحة
errors = config.validate_config()
if errors:
    print("أخطاء في الإعدادات:", errors)
else:
    config.save_config()
    print("تم حفظ إعدادات البريد بنجاح")
```

### مثال 2: إعداد الشركة

```python
config.set('company.name', 'شركة ستاندرد الجملة')
config.set('company.name_ar', 'شركة ستاندرد الجملة')
config.set('company.name_en', 'Standard El-Joumla Company')
config.set('company.address', 'الجزائر العاصمة')
config.set('company.phone', '0123456789')
config.set('company.email', 'info@logicalversion.com')
config.set('company.website', 'https://logicalversion.com')
config.set('company.tax_number', '123456789012')
config.set('company.logo_path', 'assets/images/logo.png')

config.save_config()
```

### مثال 3: استخدام متغيرات البيئة

```python
import os

# تعيين متغيرات البيئة
os.environ['DATABASE_PATH'] = '/custom/path/database.db'
os.environ['SMTP_SERVER'] = 'smtp.production.com'
os.environ['API_KEY'] = 'production_api_key'

# تحميل الإعدادات (ستستخدم متغيرات البيئة)
config = ConfigManager()
config.load_config()

# التحقق من القيم
print(config.get('database.path'))  # /custom/path/database.db
print(config.get('email.smtp_server'))  # smtp.production.com
```

## أفضل الممارسات

1. **استخدام متغيرات البيئة للإنتاج:**
   - لا تحفظ كلمات المرور في ملفات الإعدادات
   - استخدم متغيرات البيئة للقيم الحساسة

2. **تفعيل التشفير:**
   - فعّل تشفير القيم الحساسة في الإنتاج
   - استخدم مفتاح تشفير قوي

3. **التحقق من الصحة:**
   - تحقق من صحة الإعدادات قبل الحفظ
   - راجع الأخطاء بعناية

4. **النسخ الاحتياطي:**
   - احتفظ بنسخة احتياطية من ملفات الإعدادات
   - لا تشارك ملفات الإعدادات في Git إذا كانت تحتوي على بيانات حساسة

## استكشاف الأخطاء

### المشكلة: "متغير البيئة غير موجود"

**الحل:** تأكد من تعيين متغير البيئة قبل تحميل الإعدادات:

```bash
export APP_ENCRYPTION_KEY=your_key
```

### المشكلة: "فشل التشفير"

**الحل:** تأكد من:
1. وجود متغير البيئة `APP_ENCRYPTION_KEY`
2. تفعيل `encrypt_sensitive_config` في الإعدادات

### المشكلة: "أخطاء في التحقق"

**الحل:** راجع الأخطاء وأصلحها:

```python
errors = config.validate_config()
for error in errors:
    print(error)  # اقرأ الخطأ وأصلحه
```

---

**تم إنشاء هذا الدليل بواسطة:** Standard El-Joumla Team  
**التاريخ:** 2025-01-15  
**الإصدار:** 5.3.0


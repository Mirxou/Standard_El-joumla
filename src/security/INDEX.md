# Security Module Index - فهرس وحدات الأمان

## 📋 قائمة سريعة بالملفات

### 1. `mfa_service.py` (530 سطر) ⭐
**الوصف**: نظام المصادقة متعددة العوامل (Multi-Factor Authentication)

**الكلاسات**:
- `MFAMethod` (Enum) - طرق المصادقة
  - `SMS` - الرسائل النصية
  - `EMAIL` - البريد الإلكتروني
  - `TOTP` - تطبيقات المصادقة
  - `BACKUP_CODE` - الرموز الاحتياطية
- `MFAConfig` (Dataclass) - إعدادات MFA
- `MFAService` - خدمة المصادقة متعددة العوامل

**الوظائف الرئيسية**:
- `enable_mfa()` - تفعيل MFA
- `disable_mfa()` - تعطيل MFA
- `send_otp()` - إرسال OTP
- `verify_otp()` - التحقق من OTP
- `generate_totp_secret()` - إنشاء سر TOTP
- `get_totp_qr_code()` - الحصول على QR Code
- `verify_totp()` - التحقق من TOTP
- `generate_backup_codes()` - توليد رموز احتياطية
- `verify_backup_code()` - التحقق من رمز احتياطي

---

### 2. `rate_limiter.py` (93 سطر)
**الوصف**: تحديد معدل الطلبات (Rate Limiting)

**الكلاسات**:
- `RateLimiter` - محدد معدل الطلبات

**المحددات مسبقاً**:
- `login_rate_limiter` - لتسجيلات الدخول (10 محاولات كل 5 دقائق)
- `api_rate_limiter` - لـ API (100 طلب كل دقيقة)

**الوظائف الرئيسية**:
- `is_allowed(identifier)` - التحقق من السماح بالطلب
- `reset(identifier)` - إعادة تعيين الحد
- `cleanup_old_entries(hours)` - تنظيف الإدخالات القديمة

---

## 📊 الإحصائيات

- **إجمالي الملفات**: 2 ملف Python + 1 ملف `__init__.py`
- **إجمالي الأسطر**: 621 سطر
- **متوسط الأسطر لكل ملف**: 310 سطر
- **أكبر ملف**: `mfa_service.py` (530 سطر)
- **أصغر ملف**: `rate_limiter.py` (93 سطر)

---

## 🔍 البحث السريع

### حسب الوظيفة:
- **MFA**: `mfa_service.py`
- **Rate Limiting**: `rate_limiter.py`

### حسب الحجم:
- **كبيرة (> 500 سطر)**: `mfa_service.py`
- **صغيرة (< 100 سطر)**: `rate_limiter.py`

---

## 💻 أمثلة الاستخدام السريع

### MFA
```python
from src.security import MFAService, MFAMethod

mfa_service = MFAService(db_manager)

# تفعيل MFA
mfa_service.enable_mfa(user_id=1, methods=[MFAMethod.SMS])

# إرسال OTP
mfa_service.send_otp(user_id=1, method=MFAMethod.SMS)

# التحقق من OTP
mfa_service.verify_otp(user_id=1, method=MFAMethod.SMS, code="123456")
```

### Rate Limiting
```python
from src.security import login_rate_limiter, api_rate_limiter

# لتسجيلات الدخول
is_allowed, remaining = login_rate_limiter.is_allowed(ip_address)

# لـ API
is_allowed, remaining = api_rate_limiter.is_allowed(api_token)
```

---

## 🔗 روابط سريعة

- [README.md](README.md) - دليل شامل
- [../core/README.md](../core/README.md) - دليل الوحدات الأساسية
- [../models/README.md](../models/README.md) - دليل النماذج
- [../../docs/SECURITY_GUIDE.md](../../docs/SECURITY_GUIDE.md) - دليل الأمان الشامل

---

## ✅ الحالة

- ✅ جميع الملفات موثقة بشكل جيد
- ✅ دعم كامل لـ MFA (SMS, Email, TOTP, Backup Codes)
- ✅ Rate Limiting آمن وفعال
- ✅ Thread-safe للاستخدام في بيئة متعددة الخيوط
- ✅ تسجيل الأحداث (Audit Logging)


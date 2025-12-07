# Security Module - وحدات الأمان

## نظرة عامة
هذا المجلد يحتوي على وحدات الأمان للتطبيق، بما في ذلك المصادقة متعددة العوامل (MFA) وتحديد معدل الطلبات (Rate Limiting).

## 📊 الإحصائيات

- **إجمالي الملفات**: 2 ملف Python + 1 ملف `__init__.py`
- **إجمالي الأسطر**: 621 سطر
- **متوسط الأسطر لكل ملف**: 310 سطر
- **Syntax Check**: ✅ جميع الملفات صحيحة
- **Linter**: ✅ لا توجد أخطاء

## 📁 الملفات

### 1. `mfa_service.py` (530 سطر) ⭐ أكبر ملف

**الوصف**: نظام المصادقة متعددة العوامل (Multi-Factor Authentication)

**الميزات**:
- ✅ SMS OTP - إرسال رمز OTP عبر الرسائل النصية
- ✅ Email OTP - إرسال رمز OTP عبر البريد الإلكتروني
- ✅ TOTP (Time-based One-Time Password) - دعم تطبيقات المصادقة (Google Authenticator, Authy)
- ✅ Backup Codes - رموز احتياطية للوصول
- ✅ تسجيل محاولات التحقق (Audit Log)
- ✅ حماية من Brute Force attacks

**الكلاسات**:
- `MFAMethod` (Enum) - طرق المصادقة
  - `SMS` - الرسائل النصية
  - `EMAIL` - البريد الإلكتروني
  - `TOTP` - تطبيقات المصادقة
  - `BACKUP_CODE` - الرموز الاحتياطية

- `MFAConfig` (Dataclass) - إعدادات MFA للمستخدم
  - `user_id` - معرف المستخدم
  - `methods_enabled` - الطرق المفعلة
  - `phone_number` - رقم الهاتف
  - `email` - البريد الإلكتروني
  - `totp_secret` - السر السري لـ TOTP
  - `backup_codes` - الرموز الاحتياطية

- `MFAService` - خدمة المصادقة متعددة العوامل
  - `enable_mfa()` - تفعيل MFA للمستخدم
  - `disable_mfa()` - تعطيل MFA
  - `send_otp()` - إرسال رمز OTP
  - `verify_otp()` - التحقق من رمز OTP
  - `generate_totp_secret()` - إنشاء سر TOTP
  - `get_totp_qr_code()` - الحصول على QR Code للربط
  - `verify_totp()` - التحقق من TOTP
  - `generate_backup_codes()` - توليد رموز احتياطية
  - `verify_backup_code()` - التحقق من رمز احتياطي
  - `is_mfa_enabled()` - التحقق من تفعيل MFA
  - `get_user_mfa_config()` - الحصول على إعدادات MFA

**الإعدادات**:
- `OTP_LENGTH = 6` - طول رمز OTP
- `OTP_VALIDITY_MINUTES = 5` - صلاحية رمز OTP (5 دقائق)
- `MAX_ATTEMPTS = 3` - أقصى عدد محاولات
- `TOTP_PERIOD = 30` - فترة TOTP (30 ثانية)
- `BACKUP_CODE_LENGTH = 8` - طول الرمز الاحتياطي
- `BACKUP_CODE_COUNT = 10` - عدد الرموز الاحتياطية

**قاعدة البيانات**:
- `mfa_settings` - إعدادات MFA للمستخدمين
- `mfa_verification_log` - سجل محاولات التحقق

---

### 2. `rate_limiter.py` (93 سطر)

**الوصف**: تحديد معدل الطلبات (Rate Limiting) لحماية API من الهجمات

**الميزات**:
- ✅ Thread-safe - آمن للاستخدام في بيئة متعددة الخيوط
- ✅ In-memory - سريع وفعال
- ✅ تنظيف تلقائي للإدخالات القديمة
- ✅ دعم IP addresses و API tokens

**الكلاسات**:
- `RateLimiter` - محدد معدل الطلبات
  - `is_allowed(identifier)` - التحقق من السماح بالطلب
  - `reset(identifier)` - إعادة تعيين الحد
  - `cleanup_old_entries(hours)` - تنظيف الإدخالات القديمة

**المحددات مسبقاً**:
- `login_rate_limiter` - لتسجيلات الدخول (10 محاولات كل 5 دقائق)
- `api_rate_limiter` - لـ API (100 طلب كل دقيقة)

**الإعدادات**:
- `max_requests` - أقصى عدد طلبات مسموح
- `window_seconds` - نافذة الوقت بالثواني

---

## 🔐 الأمان

### الميزات الأمنية

#### 1. المصادقة متعددة العوامل (MFA)
- **SMS OTP**: إرسال رمز OTP عبر الرسائل النصية
- **Email OTP**: إرسال رمز OTP عبر البريد الإلكتروني
- **TOTP**: دعم تطبيقات المصادقة (Google Authenticator, Authy)
- **Backup Codes**: رموز احتياطية للوصول في حالة فقدان الجهاز

#### 2. تحديد معدل الطلبات (Rate Limiting)
- **حماية من Brute Force**: تحديد عدد محاولات تسجيل الدخول
- **حماية API**: تحديد عدد الطلبات لكل IP/token
- **Thread-safe**: آمن للاستخدام في بيئة متعددة الخيوط

#### 3. تسجيل الأحداث (Audit Logging)
- **تسجيل محاولات التحقق**: تسجيل جميع محاولات التحقق من MFA
- **تتبع IP addresses**: تتبع عناوين IP للمحاولات
- **تتبع User Agents**: تتبع معلومات المتصفح

---

## 💻 الاستخدام

### 1. المصادقة متعددة العوامل (MFA)

#### تفعيل MFA
```python
from src.security.mfa_service import MFAService, MFAMethod
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize()

mfa_service = MFAService(db_manager)

# تفعيل MFA
result = mfa_service.enable_mfa(
    user_id=1,
    methods=[MFAMethod.SMS, MFAMethod.EMAIL],
    phone_number="+966501234567",
    email="user@example.com"
)

# حفظ Backup Codes (تُعرض مرة واحدة فقط)
backup_codes = result["backup_codes"]
print("Backup Codes:", backup_codes)
```

#### إرسال OTP
```python
# إرسال OTP عبر SMS
otp_sent = mfa_service.send_otp(
    user_id=1,
    method=MFAMethod.SMS
)

# إرسال OTP عبر Email
otp_sent = mfa_service.send_otp(
    user_id=1,
    method=MFAMethod.EMAIL
)
```

#### التحقق من OTP
```python
# التحقق من OTP
is_valid = mfa_service.verify_otp(
    user_id=1,
    method=MFAMethod.SMS,
    code="123456"
)

if is_valid:
    print("✅ تم التحقق بنجاح")
else:
    print("❌ رمز OTP غير صحيح")
```

#### TOTP (Authenticator Apps)
```python
# إنشاء سر TOTP
secret = mfa_service.generate_totp_secret(user_id=1)

# الحصول على QR Code للربط
qr_code_url = mfa_service.get_totp_qr_code(user_id=1)

# التحقق من TOTP
is_valid = mfa_service.verify_totp(
    user_id=1,
    code="123456"
)
```

#### Backup Codes
```python
# توليد Backup Codes
backup_codes = mfa_service.generate_backup_codes(user_id=1)

# التحقق من Backup Code
is_valid = mfa_service.verify_backup_code(
    user_id=1,
    code="ABCD1234"
)
```

---

### 2. تحديد معدل الطلبات (Rate Limiting)

#### استخدام Rate Limiter مخصص
```python
from src.security.rate_limiter import RateLimiter

# إنشاء Rate Limiter
rate_limiter = RateLimiter(
    max_requests=5,      # 5 طلبات
    window_seconds=60    # في 60 ثانية
)

# التحقق من IP
is_allowed, remaining = rate_limiter.is_allowed("192.168.1.1")

if is_allowed:
    print(f"✅ الطلب مسموح. متبقي: {remaining} طلبات")
else:
    print("❌ تم تجاوز الحد المسموح")
```

#### استخدام Rate Limiters المحددة مسبقاً
```python
from src.security.rate_limiter import login_rate_limiter, api_rate_limiter

# Rate Limiter لتسجيلات الدخول
is_allowed, remaining = login_rate_limiter.is_allowed(ip_address)

# Rate Limiter لـ API
is_allowed, remaining = api_rate_limiter.is_allowed(api_token)
```

#### إعادة تعيين Rate Limit
```python
# إعادة تعيين لـ IP معين
rate_limiter.reset("192.168.1.1")
```

#### تنظيف الإدخالات القديمة
```python
# حذف الإدخالات الأقدم من ساعة
rate_limiter.cleanup_old_entries(hours=1)
```

---

## 🔗 التكامل

### مع Login Dialog
```python
from src.security.rate_limiter import login_rate_limiter
from src.security.mfa_service import MFAService, MFAMethod

# التحقق من Rate Limit
is_allowed, remaining = login_rate_limiter.is_allowed(ip_address)
if not is_allowed:
    return "تم تجاوز الحد المسموح. يرجى المحاولة لاحقاً."

# التحقق من MFA
mfa_service = MFAService(db_manager)
if mfa_service.is_mfa_enabled(user_id):
    # إرسال OTP
    mfa_service.send_otp(user_id, MFAMethod.SMS)
    # التحقق من OTP
    is_valid = mfa_service.verify_otp(user_id, MFAMethod.SMS, otp_code)
```

### مع API Endpoints
```python
from src.security.rate_limiter import api_rate_limiter

def protected_api_endpoint(request):
    # التحقق من Rate Limit
    api_token = request.headers.get('Authorization')
    is_allowed, remaining = api_rate_limiter.is_allowed(api_token)
    
    if not is_allowed:
        return {
            "error": "Rate limit exceeded",
            "retry_after": 60
        }, 429
    
    # تنفيذ الطلب
    return process_request(request)
```

---

## 📝 أفضل الممارسات

### 1. استخدام MFA
- ✅ **فعّل MFA للمستخدمين المهمين**: المديرين والمستخدمين ذوي الصلاحيات العالية
- ✅ **استخدم TOTP**: أكثر أماناً من SMS/Email
- ✅ **احفظ Backup Codes**: في مكان آمن
- ✅ **راقب Audit Logs**: راجع السجلات بانتظام

### 2. استخدام Rate Limiting
- ✅ **فعّل Rate Limiting**: لتسجيلات الدخول و API Endpoints
- ✅ **اضبط الحدود**: حسب احتياجات التطبيق
- ✅ **نظف الإدخالات القديمة**: بانتظام لتوفير الذاكرة
- ✅ **استخدم IP addresses**: لتحديد المستخدمين

### 3. الأمان العام
- ✅ **شفر البيانات الحساسة**: كلمات المرور، معلومات الدفع
- ✅ **استخدم HTTPS**: لجميع الاتصالات
- ✅ **راقب Audit Logs**: راجع السجلات بانتظام
- ✅ **حدّث المكتبات**: بانتظام للأمان

---

## 🧪 الاختبار

### اختبار MFA
```python
# اختبار تفعيل MFA
result = mfa_service.enable_mfa(user_id=1, methods=[MFAMethod.SMS])
assert result["mfa_enabled"] == True

# اختبار إرسال OTP
otp_sent = mfa_service.send_otp(user_id=1, method=MFAMethod.SMS)
assert otp_sent == True

# اختبار التحقق من OTP
# (يحتاج إلى رمز OTP فعلي)
```

### اختبار Rate Limiting
```python
# اختبار Rate Limiter
rate_limiter = RateLimiter(max_requests=5, window_seconds=60)

# اختبار الطلبات المتعددة
for i in range(5):
    is_allowed, remaining = rate_limiter.is_allowed("192.168.1.1")
    assert is_allowed == True

# اختبار تجاوز الحد
is_allowed, remaining = rate_limiter.is_allowed("192.168.1.1")
assert is_allowed == False
```

---

## 📚 المراجع

- `src/core/encryption_manager.py` - مدير التشفير
- `src/core/database_manager.py` - مدير قاعدة البيانات
- `docs/SECURITY_GUIDE.md` - دليل الأمان الشامل

---

## ✅ الخلاصة

- ✅ جميع الوحدات موثقة بشكل جيد
- ✅ دعم كامل لـ MFA (SMS, Email, TOTP, Backup Codes)
- ✅ Rate Limiting آمن وفعال
- ✅ Thread-safe للاستخدام في بيئة متعددة الخيوط
- ✅ تسجيل الأحداث (Audit Logging)

**التقييم**: 5/5 ⭐⭐⭐⭐⭐


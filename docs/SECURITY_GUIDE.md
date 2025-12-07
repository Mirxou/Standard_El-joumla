# 🔒 دليل الأمان - Security Guide

## نظرة عامة

يستخدم نظام الإصدار المنطقي عدة طبقات من الأمان:
- تشفير البيانات الحساسة
- المصادقة متعددة العوامل (MFA)
- Rate Limiting
- Audit Logging
- Session Management

## Encryption

### EncryptionManager

#### التهيئة

```python
from src.core.encryption_manager import EncryptionManager

# تهيئة مع كلمة مرور
encryption_manager = EncryptionManager("your_password")
```

#### تشفير البيانات

```python
# تشفير نص
encrypted_data = encryption_manager.encrypt_data("sensitive data")

# فك التشفير
decrypted_data = encryption_manager.decrypt_data(encrypted_data)
decrypted_text = decrypted_data.decode('utf-8')
```

#### تشفير الملفات

```python
# تشفير ملف
encrypted_path = encryption_manager.encrypt_file(
    "data/sensitive.txt",
    "data/sensitive.txt.encrypted"
)

# فك تشفير ملف
decrypted_path = encryption_manager.decrypt_file(
    "data/sensitive.txt.encrypted",
    "data/sensitive_decrypted.txt"
)
```

#### تشفير قاعدة البيانات

```python
# تشفير قاعدة البيانات
encryption_manager.encrypt_database(
    db_path="data/database.db",
    password="your_password",
    backup_original=True
)

# فك تشفير قاعدة البيانات
encryption_manager.decrypt_database(
    encrypted_db_path="data/database.db",
    password="your_password",
    output_path="data/database_decrypted.db"
)
```

#### توليد كلمة مرور آمنة

```python
# توليد كلمة مرور آمنة (16 حرف)
secure_password = EncryptionManager.generate_secure_password(length=16)

# تشفير كلمة مرور للتخزين
password_hash, salt = EncryptionManager.hash_password("user_password")

# التحقق من كلمة المرور
is_valid = EncryptionManager.verify_password(
    stored_password=password_hash,
    stored_salt=salt,
    provided_password="user_password"
)
```

### تشفير الإعدادات الحساسة

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
config.load_config()

# تفعيل التشفير
config.set('security.encrypt_sensitive_config', True)
config.set('security.encryption_key_env', 'APP_ENCRYPTION_KEY')
config.save_config()

# تعيين قيمة حساسة (سيتم تشفيرها تلقائياً)
config.set('email.smtp_password', 'my_password')
config.save_config()
```

## Authentication

### Multi-Factor Authentication (MFA)

#### MFAService

```python
from src.security.mfa_service import MFAService, MFAMethod
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize()

mfa_service = MFAService(db_manager)
```

#### تفعيل MFA للمستخدم

```python
# تفعيل MFA
mfa_service.enable_mfa(
    user_id=1,
    methods=[MFAMethod.SMS, MFAMethod.EMAIL]
)

# إعداد معلومات الاتصال
mfa_service.setup_user_mfa(
    user_id=1,
    phone_number="+966501234567",
    email="user@example.com"
)
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
    print("تم التحقق بنجاح")
else:
    print("رمز OTP غير صحيح")
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

## Rate Limiting

### RateLimiter

```python
from src.security.rate_limiter import RateLimiter

# إنشاء Rate Limiter
rate_limiter = RateLimiter(
    max_requests=5,      # 5 طلبات
    window_seconds=60     # في 60 ثانية
)
```

#### التحقق من Rate Limit

```python
# التحقق من IP
is_allowed, remaining = rate_limiter.is_allowed("192.168.1.1")

if is_allowed:
    print(f"الطلب مسموح. متبقي: {remaining} طلبات")
else:
    print("تم تجاوز الحد المسموح")
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

### Rate Limiters المحددة مسبقاً

```python
from src.security.rate_limiter import login_rate_limiter, api_rate_limiter

# Rate Limiter لتسجيلات الدخول
is_allowed, remaining = login_rate_limiter.is_allowed(ip_address)

# Rate Limiter لـ API
is_allowed, remaining = api_rate_limiter.is_allowed(api_token)
```

## Access Control

### Session Management

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
config.load_config()

# الحصول على إعدادات الجلسة
security_settings = config.get_security_settings()

session_timeout = security_settings['session_timeout']  # بالدقائق
password_min_length = security_settings['password_min_length']
enable_audit_log = security_settings['enable_audit_log']
```

### Audit Logging

```python
# يتم تسجيل جميع العمليات المهمة تلقائياً في جدول audit_logs
# يمكنك الاستعلام عنها:

audit_logs = db_manager.execute_query("""
    SELECT * FROM audit_logs 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT 100
""", (user_id,))
```

## أمثلة عملية

### مثال 1: تسجيل دخول آمن مع MFA

```python
def secure_login(username, password, otp_code):
    # 1. التحقق من Rate Limit
    is_allowed, remaining = login_rate_limiter.is_allowed(request.remote_addr)
    if not is_allowed:
        return {"success": False, "message": "تم تجاوز الحد المسموح"}
    
    # 2. التحقق من اسم المستخدم وكلمة المرور
    user = authenticate_user(username, password)
    if not user:
        return {"success": False, "message": "بيانات الدخول غير صحيحة"}
    
    # 3. التحقق من MFA
    mfa_service = MFAService(db_manager)
    if mfa_service.is_mfa_enabled(user.id):
        is_valid = mfa_service.verify_otp(
            user_id=user.id,
            method=MFAMethod.SMS,
            code=otp_code
        )
        if not is_valid:
            return {"success": False, "message": "رمز OTP غير صحيح"}
    
    # 4. إنشاء جلسة
    session = create_session(user.id)
    
    # 5. تسجيل في Audit Log
    log_audit_event(
        user_id=user.id,
        action="login",
        details={"ip": request.remote_addr}
    )
    
    return {"success": True, "session": session}
```

### مثال 2: حماية API Endpoint

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
    
    # التحقق من API Key
    if not verify_api_key(api_token):
        return {"error": "Invalid API key"}, 401
    
    # تنفيذ الطلب
    return process_request(request)
```

### مثال 3: تشفير البيانات الحساسة

```python
from src.core.encryption_manager import EncryptionManager

# تشفير بيانات العميل الحساسة
encryption_manager = EncryptionManager("master_password")

customer_data = {
    "credit_card": "1234-5678-9012-3456",
    "ssn": "123-45-6789"
}

# تشفير كل حقل
encrypted_data = {}
for key, value in customer_data.items():
    encrypted = encryption_manager.encrypt_data(value)
    encrypted_data[key] = base64.b64encode(encrypted).decode('utf-8')

# حفظ المشفر
save_to_database(encrypted_data)

# فك التشفير عند الحاجة
decrypted_data = {}
for key, encrypted_value in encrypted_data.items():
    encrypted_bytes = base64.b64decode(encrypted_value)
    decrypted = encryption_manager.decrypt_data(encrypted_bytes)
    decrypted_data[key] = decrypted.decode('utf-8')
```

## أفضل الممارسات

1. **استخدم MFA للمستخدمين المهمين:**
   - المديرين
   - المستخدمين ذوي الصلاحيات العالية

2. **فعّل Rate Limiting:**
   - لتسجيلات الدخول
   - لـ API Endpoints
   - للعمليات الحساسة

3. **شفر البيانات الحساسة:**
   - كلمات المرور
   - معلومات الدفع
   - البيانات الشخصية

4. **راقب Audit Logs:**
   - راجع السجلات بانتظام
   - ابحث عن الأنماط المشبوهة

5. **استخدم كلمات مرور قوية:**
   ```python
   secure_password = EncryptionManager.generate_secure_password(length=16)
   ```

## استكشاف الأخطاء

### المشكلة: "فشل التشفير"

**الحل:** تأكد من:
1. وجود كلمة مرور صحيحة
2. توفر مكتبة `cryptography`

### المشكلة: "Rate Limit دائماً محظور"

**الحل:**
```python
# إعادة تعيين Rate Limit
rate_limiter.reset(identifier)
```

### المشكلة: "OTP لا يصل"

**الحل:** تأكد من:
1. إعدادات البريد الإلكتروني/SMS صحيحة
2. رقم الهاتف/البريد الإلكتروني صحيح
3. التحقق من السجلات

---

**تم إنشاء هذا الدليل بواسطة:** Logical Version Team  
**التاريخ:** 2025-01-15  
**الإصدار:** 5.3.0


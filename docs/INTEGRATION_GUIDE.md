# دليل التكامل
## Integration Guide

**التاريخ:** 2025-01-16  
**النسخة:** 1.0

---

## نظرة عامة

هذا الدليل يشرح كيفية ربط التطبيقات الثلاثة (Desktop, Web, Mobile) مع بعضها البعض.

---

## البنية المعمارية

```
┌─────────────────┐
│  Desktop App    │
│   (PySide6)     │
└────────┬────────┘
         │
         │ SQLite (مشترك)
         │
         ▼
┌─────────────────┐
│  logical_release│
│      .db        │
└────────┬────────┘
         │
         │ SQLite (مشترك)
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│  (REST API)     │
└────────┬────────┘
         │
         │ HTTP/REST
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│  Web   │ │ Mobile │
│  App   │ │  App   │
│(Next.js)│ │(React │
│        │ │Native) │
└────────┘ └────────┘
```

---

## قاعدة البيانات المشتركة

### المسار الموحد

```
{project_root}/data/logical_release.db
```

### الاستخدام

**Desktop App:**
```python
from src.core.config_manager import ConfigManager

config_manager = ConfigManager()
config_manager.load_config()
db_path = config_manager.get_database_path()
db_manager = DatabaseManager(db_path=db_path)
```

**FastAPI:**
```python
from src.core.config_manager import ConfigManager

config_manager = ConfigManager()
config_manager.load_config()
db_path = config_manager.get_database_path()
db_manager = DatabaseManager(db_path=db_path)
```

---

## API Configuration

### Base URL

**Development:**
- Desktop: `http://127.0.0.1:8000`
- Web: `http://localhost:8000`
- Mobile: `http://localhost:8000`

**Production:**
- تحديث في `config/app_config.json` → `api.api_url`
- أو في environment variables

### API Versioning

جميع endpoints تستخدم prefix: `/api/v1/`

**مثال:**
- Login: `/api/v1/auth/login`
- Products: `/api/v1/products`
- Sales: `/api/v1/sales`

---

## Authentication

### JWT Tokens

جميع التطبيقات تستخدم JWT tokens للمصادقة.

**Desktop:**
- يستخدم `UserService` المحلي
- يمكن ربطه بـ API للتحقق من الجلسات

**Web & Mobile:**
- يستخدمان JWT tokens من API
- Token storage:
  - Web: `localStorage`
  - Mobile: `AsyncStorage`

### Token Refresh

```typescript
// Web App
const refreshToken = localStorage.getItem('refresh_token');
const response = await fetch('/api/v1/auth/refresh', {
  method: 'POST',
  body: JSON.stringify({ refresh_token: refreshToken })
});
```

---

## Hybrid Mode (Desktop)

### الوضع الهجين

Desktop App يدعم الوضع الهجين:
- **Online:** الاتصال بـ API
- **Offline:** استخدام قاعدة البيانات المحلية

### Sync Queue

العمليات التي تتم أثناء offline تُضاف إلى `sync_queue`:

```python
# في HybridDataService
def create_product(self, product_data):
    if self.api.is_online():
        # إرسال إلى API
        result = self.api.post("products", product_data)
    else:
        # حفظ محلياً وإضافة للمزامنة
        product_id = self._create_local(product_data)
        self._mark_for_sync("product", product_id, "create")
```

### Sync Status Indicator

مؤشر في StatusBar يعرض:
- 🟢 متصل / 🔴 غير متصل
- عدد العمليات المعلقة

### المزامنة التلقائية

- تحديث الحالة كل 5 ثوان
- مزامنة تلقائية كل 30 ثانية (عند الاتصال)

---

## CORS Configuration

### Development

```python
# src/api/app.py
cors_origins = ["*"]  # للجميع
```

### Production

```python
# config/app_config.json
{
  "api": {
    "cors_origins": [
      "https://yourdomain.com",
      "https://app.yourdomain.com"
    ]
  }
}
```

أو environment variable:
```bash
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## Error Handling

### توحيد Error Response

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "status_code": 400
}
```

### Error Codes

- `VALIDATION_ERROR`: خطأ في التحقق
- `NOT_FOUND`: المورد غير موجود
- `UNAUTHORIZED`: غير مصرح
- `FORBIDDEN`: محظور
- `INTERNAL_ERROR`: خطأ داخلي

---

## Database Lock Handling

### WAL Mode

تم تفعيل WAL mode تلقائياً:
```python
self.connection.execute("PRAGMA journal_mode=WAL")
```

### Retry Logic

استخدام `DatabaseLockHandler`:
```python
from src.core.database_lock_handler import retry_on_lock_error

@retry_on_lock_error(max_retries=5)
def update_product():
    # كود قاعدة البيانات
    pass
```

---

## أفضل الممارسات

### 1. استخدام Context Managers

```python
with db_manager.get_cursor() as cursor:
    cursor.execute("SELECT * FROM products")
    # الاتصال يُغلق تلقائياً
```

### 2. معالجة الأخطاء

```python
try:
    result = api_client.get("products")
except requests.RequestException as e:
    # العودة للقاعدة المحلية
    result = get_local_products()
```

### 3. المزامنة

- مزامنة تلقائية كل 30 ثانية
- مزامنة يدوية عند النقر على مؤشر الحالة

---

## الاختبار

### 1. اختبار قاعدة البيانات المشتركة

```python
# Desktop: إنشاء منتج
db_manager.execute_query("INSERT INTO products ...")

# FastAPI: قراءة المنتج
products = db_manager.fetch_all("SELECT * FROM products")
assert len(products) > 0
```

### 2. اختبار API

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### 3. اختبار CORS

```javascript
// Web App
fetch('http://localhost:8000/api/v1/products', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

---

## استكشاف الأخطاء

### المشكلة: "database is locked"

**الحل:**
1. استخدام `DatabaseLockHandler` مع retry logic
2. التأكد من إغلاق الاتصالات
3. تقسيم العمليات الكبيرة

### المشكلة: CORS errors

**الحل:**
1. التحقق من `cors_origins` في config
2. التأكد من أن origin صحيح
3. فحص environment variables

### المشكلة: Authentication failed

**الحل:**
1. التحقق من token expiration
2. استخدام refresh token
3. التحقق من JWT secret key

---

## الخلاصة

1. ✅ قاعدة البيانات موحدة بين Desktop و FastAPI
2. ✅ API endpoints موحدة (`/api/v1/`)
3. ✅ CORS configurable
4. ✅ Hybrid mode في Desktop
5. ✅ Sync status indicator
6. ✅ Database lock handling

---

**آخر تحديث:** 2025-01-16

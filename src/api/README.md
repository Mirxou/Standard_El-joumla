# API Module - نظام API للتكامل الخارجي

## نظرة عامة
هذا المجلد يحتوي على وحدات API للتطبيق، بما في ذلك عميل API وخدمة البيانات الهجينة.

## الملفات

### `api_client.py` (343 سطر)
**الوصف**: عميل API هجين يدعم الوضع المحلي والسحابي

**الميزات**:
- ✅ دعم الوضع المحلي (Offline) والوضع السحابي (Online)
- ✅ اكتشاف تلقائي لاتصال API
- ✅ دعم JWT Authentication
- ✅ طلبات HTTP كاملة (GET, POST, PUT, DELETE)
- ✅ معالجة أخطاء مناسبة
- ✅ Caching للتحقق من الاتصال

**الاستخدام**:
```python
from src.api.api_client import APIClient, HybridDataService
from src.core.database_manager import DatabaseManager

# تهيئة عميل API
api_client = APIClient(base_url="http://127.0.0.1:8000", timeout=5)

# التحقق من الاتصال
if api_client.is_online():
    print("✅ API متاح")
    
    # تسجيل الدخول
    if api_client.login("username", "password"):
        # الحصول على البيانات
        products = api_client.get("products")
        print(products)
else:
    print("⚠️ الوضع المحلي: API غير متاح")
```

**الكلاسات**:
- `APIClient` - عميل API الرئيسي
  - `is_online()` - التحقق من توفر الاتصال
  - `login()` - تسجيل الدخول والحصول على Token
  - `get()` - طلب GET
  - `post()` - طلب POST
  - `put()` - طلب PUT
  - `delete()` - طلب DELETE
- `HybridDataService` - خدمة بيانات هجينة
  - `get_products()` - الحصول على المنتجات (هجين)
  - `create_product()` - إنشاء منتج جديد (هجين)
  - `sync_pending_changes()` - مزامنة التغييرات المعلقة

### `integration_models.py` (30 سطر)
**الوصف**: نماذج التكاملات الخارجية (Webhooks & Integrations)

**الميزات**:
- ✅ نماذج Pydantic للتكاملات
- ✅ Fallback إذا لم يكن Pydantic متاحاً
- ✅ نماذج جاهزة للـ Webhooks

**الاستخدام**:
```python
from src.api.integration_models import (
    AccountingWebhookPayload,
    PaymentWebhookPayload,
    SMSNotificationPayload
)

# استخدام النماذج
payload = AccountingWebhookPayload(
    invoice_id=123,
    amount=1000.0,
    customer="John Doe",
    date="2025-12-05"
)
```

**الكلاسات**:
- `AccountingWebhookPayload` - نموذج Webhook للمحاسبة
- `PaymentWebhookPayload` - نموذج Webhook للمدفوعات
- `SMSNotificationPayload` - نموذج إشعار SMS

### `__init__.py` (28 سطر)
**الوصف**: ملف التهيئة للمودول

**الميزات**:
- ✅ استيراد اختياري للـ API Server
- ✅ Fallback إذا لم يكن API Server متاحاً
- ✅ دعم الوضع المحلي فقط (Desktop-only mode)

## التكامل مع التطبيق

### في `main.py`
يتم استخدام API Client في:
```python
# تهيئة عميل API الهجين
api_url = self.config_manager.get("api_url", "http://127.0.0.1:8000")
self.api_client = APIClient(base_url=api_url, timeout=5)
self.hybrid_service = HybridDataService(self.db_manager, self.api_client)

if self.api_client.is_online():
    self.logger.info(f"✅ الاتصال بـ API متاح: {api_url}")
else:
    self.logger.info("⚠️ الوضع المحلي: API غير متاح")
```

## الوضع الهجين (Hybrid Mode)

### كيف يعمل؟
1. **محاولة API أولاً**: يحاول الاتصال بـ API
2. **الرجوع للوضع المحلي**: إذا فشل الاتصال، يستخدم قاعدة البيانات المحلية
3. **المزامنة**: يحفظ التغييرات في queue للمزامنة لاحقاً

### مثال:
```python
# الحصول على المنتجات
products = hybrid_service.get_products(page=1, page_size=50)

# إذا كان API متاحاً → يحصل من API
# إذا لم يكن متاحاً → يحصل من قاعدة البيانات المحلية
```

## المزامنة (Synchronization)

### Sync Queue
يتم حفظ التغييرات في جدول `sync_queue` للمزامنة لاحقاً:
- `entity_type`: نوع الكيان (product, sale, etc.)
- `entity_id`: معرف الكيان
- `operation`: نوع العملية (create, update, delete)
- `synced`: حالة المزامنة (0 = معلق، 1 = مزامن)

### مزامنة يدوية
```python
# مزامنة التغييرات المعلقة
stats = hybrid_service.sync_pending_changes()
print(f"مزامن: {stats['synced']}, فشل: {stats['failed']}, معلق: {stats['pending']}")
```

## TODO / التحسينات المطلوبة

### في `api_client.py`:
1. **السطر 271**: `_mark_for_sync()` - تحسين منطق المزامنة
2. **السطر 327**: `sync_pending_changes()` - تنفيذ منطق المزامنة الكامل

**ملاحظة**: هذه الدوال تحتاج إلى تنفيذ منطق المزامنة الكامل بدلاً من التعليقات.

## الأمان

- ✅ JWT Token Authentication
- ✅ معالجة آمنة للأخطاء
- ✅ Timeout للطلبات
- ✅ لا يوجد كود تنفيذي خطير

## التبعيات

- `requests` - طلبات HTTP
- `typing` - Type hints
- `datetime` - التعامل مع التواريخ
- `json` - تحويل JSON
- `pydantic` (اختياري) - نماذج البيانات

## الأداء

- **التحقق من الاتصال**: Cached لمدة 10 ثوانٍ
- **الطلبات**: Timeout افتراضي 5 ثوانٍ
- **المزامنة**: تعمل في الخلفية

## الاختبارات

### اختبارات Unit
```bash
python -m pytest tests/unit/test_api_client.py -v
```

### اختبارات Integration
```bash
python -m pytest tests/api/test_api_integration.py -v
```

## التطوير المستقبلي

### APIClient
- [ ] Retry logic للطلبات الفاشلة
- [ ] Exponential backoff
- [ ] Rate limiting
- [ ] Request/Response logging
- [ ] WebSocket support

### HybridDataService
- [ ] مزامنة تلقائية دورية
- [ ] حل النزاعات (Conflict resolution)
- [ ] مزامنة ثنائية الاتجاه
- [ ] Compress البيانات قبل الإرسال

### Integration Models
- [ ] المزيد من نماذج Webhooks
- [ ] Validation محسّن
- [ ] دعم المزيد من أنواع التكاملات

## المراجع

- `main.py` - استخدام API Client
- `tests/unit/test_api_client.py` - اختبارات Unit
- `tests/api/test_api_integration.py` - اختبارات Integration
- `docs/API_EXAMPLES.md` - أمثلة استخدام API
- `docs/API_DOCUMENTATION.md` - التوثيق الكامل للـ API

## أمثلة سريعة

### Python - استخدام APIClient

```python
from src.api.api_client import APIClient

# تهيئة العميل
api_client = APIClient(base_url="http://localhost:8000")

# تسجيل الدخول
if api_client.login("username", "password"):
    # الحصول على المنتجات
    products = api_client.get("products")
    print(products)
    
    # إنشاء منتج جديد
    new_product = {
        "name": "منتج جديد",
        "barcode": "123456",
        "cost_price": 50.0,
        "selling_price": 100.0
    }
    result = api_client.post("products", new_product)
    print(result)
```

### Python - استخدام FastAPI TestClient

```python
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

# تسجيل الدخول
response = client.post("/api/v1/auth/login", json={
    "username": "admin",
    "password": "password"
})
token = response.json()["access_token"]

# استخدام Token
headers = {"Authorization": f"Bearer {token}"}
products = client.get("/api/v1/products/", headers=headers)
print(products.json())
```

### JavaScript/TypeScript - استخدام fetch

```typescript
// تسجيل الدخول
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'password' })
});

const { access_token } = await loginResponse.json();

// استخدام Token
const productsResponse = await fetch('http://localhost:8000/api/v1/products/', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

const products = await productsResponse.json();
console.log(products);
```

لمزيد من الأمثلة التفصيلية، راجع [docs/API_EXAMPLES.md](../../docs/API_EXAMPLES.md)


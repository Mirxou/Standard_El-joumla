# دليل التكامل بين Web و Desktop Application

## نظرة عامة

هذا الدليل يشرح كيفية ربط تطبيق الويب (Next.js) مع تطبيق سطح المكتب (PySide6) لاستخدام قاعدة بيانات SQLite واحدة مشتركة (`data/logical_release.db`)، مع إمكانية التحكم من الويب عبر الشبكة المحلية وتحديث فوري للبيانات.

## البنية المعمارية

```
┌──────────────────┐         HTTP REST         ┌──────────────┐
│   Web App        │◄─────────────────────────►│  FastAPI     │
│  (Next.js)       │         WebSocket         │  Backend     │
│  :3000           │◄─────────────────────────►│  :8000       │
└──────────────────┘                            └──────┬───────┘
                                                       │
                                              SQLite (WAL mode)
                                                       │
┌──────────────────┐                                 │
│  Desktop App     │                                 │
│  (PySide6)       │◄────────────────────────────────┘
│                  │          Direct SQLite
└──────────────────┘
```

## المتطلبات الأساسية

### 1. قاعدة البيانات المشتركة

- **المسار**: `data/logical_release.db`
- **الوضع**: WAL Mode (Write-Ahead Logging) مفعل تلقائياً
- **الميزة**: يدعم قراءات متزامنة وكتابات متعددة

### 2. Backend API

- **المسار**: `src/api/app.py`
- **المنفذ**: `8000`
- **البروتوكول**: HTTP REST + WebSocket

### 3. Web Application

- **المسار**: `web/`
- **المنفذ**: `3000`
- **التقنية**: Next.js 14 + React 18

## خطوات التشغيل

### الخطوة 1: تشغيل Backend API

#### للوصول من localhost فقط:
```bash
cd "C:\Users\pc\Desktop\Standard El-Joumla trae"
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
```

#### للوصول من الشبكة المحلية:
```bash
cd "C:\Users\pc\Desktop\Standard El-Joumla trae"
python scripts/start-backend.py
```

سيعمل Backend على `0.0.0.0:8000` ويمكن الوصول إليه من أي جهاز في نفس الشبكة.

**التحقق من التشغيل:**
- افتح المتصفح وانتقل إلى: `http://localhost:8000/docs`
- يجب أن ترى Swagger UI documentation

### الخطوة 2: تشغيل Desktop Application

```bash
cd "C:\Users\pc\Desktop\Standard El-Joumla trae"
python main.py
```

**ملاحظة**: Desktop App سيتصل تلقائياً بـ Backend WebSocket للاستماع للتحديثات.

### الخطوة 3: تشغيل Web Application

```bash
cd "C:\Users\pc\Desktop\Standard El-Joumla trae\web"
npm install  # أول مرة فقط
npm run dev
```

سيعمل Web App على `http://localhost:3000`

**التحقق من الاتصال:**
- افتح المتصفح وانتقل إلى: `http://localhost:3000`
- يجب أن ترى واجهة التطبيق

## الوصول من الشبكة المحلية

### 1. معرفة IP Address

#### على Windows:
```powershell
ipconfig
```
ابحث عن `IPv4 Address` تحت `Ethernet adapter` أو `Wireless LAN adapter`.

مثال: `192.168.1.100`

#### على Linux/Mac:
```bash
ifconfig
# أو
ip addr
```

### 2. تحديث إعدادات Web App

#### الطريقة 1: Environment Variable

أنشئ أو حدث ملف `web/.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=http://192.168.1.100:8000
```

#### الطريقة 2: الكشف التلقائي

الكود في `web/lib/config/api.ts` يقوم بالكشف التلقائي عن IP إذا كان Web App يعمل على نفس الجهاز.

### 3. الوصول من جهاز آخر

من جهاز آخر في نفس الشبكة:
1. تأكد من تشغيل Backend على `0.0.0.0:8000`
2. افتح المتصفح وانتقل إلى: `http://[IP]:3000`
   - مثال: `http://192.168.1.100:3000`

## الأمان

### 1. Authentication

جميع endpoints محمية بـ JWT Authentication:
- تسجيل الدخول: `POST /api/v1/auth/login`
- الحصول على Token: يتم إرجاع `access_token` و `refresh_token`
- استخدام Token: إضافة في Header: `Authorization: Bearer <token>`

### 2. Rate Limiting

- **الحد الافتراضي**: 100 طلب/دقيقة لكل IP
- **تسجيل الدخول**: 5 طلبات/دقيقة

### 3. Network Security

**للإنتاج:**
- استخدم HTTPS
- حدد IPs المسموح بها في CORS
- استخدم Firewall للحد من الوصول

**للاختبار المحلي:**
- CORS يسمح بالوصول من `localhost` و IPs في الشبكة المحلية
- يمكن تحديث `config_manager.get_cors_origins()` لتحديد IPs محددة

## WebSocket للتحديثات الفورية

### Endpoints

1. **`/ws`** - WebSocket عام
   - Parameters: `room` (اختياري), `token` (اختياري)
   - مثال: `ws://localhost:8000/ws?room=default&token=<token>`

2. **`/ws/data-updates`** - مخصص لتحديثات البيانات
   - للاستخدام من Desktop App
   - مثال: `ws://localhost:8000/ws/data-updates`

### أنواع الرسائل

#### من Server إلى Client:

**Connection:**
```json
{
  "type": "connection",
  "status": "connected",
  "room": "data_updates",
  "timestamp": "2024-01-01T12:00:00"
}
```

**Data Update:**
```json
{
  "type": "data_update",
  "data": {
    "entity_type": "product",
    "entity_id": 123,
    "action": "updated",
    "data": { /* entity data */ },
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

**Notification:**
```json
{
  "type": "notification",
  "data": {
    "title": "تحديث",
    "message": "تم تحديث المنتج",
    "notification_type": "info",
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

#### من Client إلى Server:

**Ping (Keep-alive):**
```json
{
  "type": "ping"
}
```

### الاستخدام في Web App

```typescript
import { getWebSocketClient } from '@/lib/websocket-client';

const ws = getWebSocketClient('data_updates', token);

ws.on('data_update', (message) => {
  console.log('Data updated:', message.data);
  // تحديث UI
});

ws.connect();
```

### الاستخدام في Desktop App

```python
from src.ui.websocket_client import WebSocketClient

ws_client = WebSocketClient(
    api_base_url="http://localhost:8000",
    room="data_updates"
)

ws_client.data_update_received.connect(on_data_update)
ws_client.connect()
```

## استكشاف الأخطاء

### مشكلة: لا يمكن الوصول إلى Backend من Web

**الحلول:**
1. تأكد من تشغيل Backend على `0.0.0.0:8000` وليس `127.0.0.1:8000`
2. تحقق من Firewall - قد تحتاج لفتح port 8000
3. تحقق من CORS settings في `src/core/config_manager.py`
4. تحقق من `NEXT_PUBLIC_API_BASE_URL` في `web/.env.local`

### مشكلة: WebSocket connection فاشل

**الحلول:**
1. تأكد من أن Backend يعمل
2. تحقق من URL - يجب أن يكون `ws://` وليس `http://`
3. تحقق من Firewall - قد تحتاج لفتح WebSocket connections
4. راجع logs في Backend للحصول على تفاصيل الخطأ

### مشكلة: البيانات لا تتحدث فورياً

**الحلول:**
1. تحقق من أن WebSocket متصل (انظر statusbar في Desktop)
2. تأكد من أن البيانات تُرسل عبر WebSocket عند التحديث
3. راجع logs في Backend للتأكد من إرسال الرسائل

### مشكلة: Database locks

**الحلول:**
1. تأكد من تفعيل WAL mode (`PRAGMA journal_mode=WAL`)
2. قلل عدد الكتابات المتزامنة
3. راجع `scripts/test_sqlite_wal_performance.py` لاختبار الأداء

### مشكلة: بطء في الاستجابة

**الحلول:**
1. راجع Database Metrics في Desktop App (Performance Tab > Database Metrics)
2. تحقق من slow queries
3. فكر في استخدام PostgreSQL إذا كان الأداء غير مقبول (راجع `docs/POSTGRESQL_MIGRATION_CRITERIA.md`)

## اختبار التكامل

### اختبار 1: قاعدة البيانات المشتركة

1. افتح Desktop App
2. أضف منتج جديد
3. افتح Web App
4. **النتيجة المتوقعة**: يجب أن يظهر المنتج الجديد في Web App

### اختبار 2: التحديث الفوري

1. افتح Desktop App و Web App معاً
2. من Web App، عدّل منتج
3. **النتيجة المتوقعة**: يجب أن يتحدث Desktop App تلقائياً

### اختبار 3: الوصول من الشبكة

1. شغّل Backend على `0.0.0.0:8000`
2. من جهاز آخر في نفس الشبكة، افتح Web App
3. **النتيجة المتوقعة**: يجب أن يعمل التطبيق بشكل طبيعي

## الملفات المهمة

### Backend:
- `scripts/start-backend.py` - سكريبت تشغيل Backend للشبكة
- `src/api/app.py` - FastAPI application
- `src/api/routes.py` - REST API routes + WebSocket endpoints
- `src/api/websocket_manager.py` - WebSocket manager

### Desktop:
- `src/ui/websocket_client.py` - WebSocket client
- `src/ui/windows/main_window.py` - Main window with WebSocket integration

### Web:
- `web/lib/websocket-client.ts` - WebSocket client
- `web/lib/config/api.ts` - API configuration

## دعم إضافي

للمزيد من المعلومات:
- Database Abstraction: راجع `src/database/backend.py`
- Database Metrics: راجع `src/core/database_metrics.py`
- PostgreSQL Migration: راجع `docs/POSTGRESQL_MIGRATION_CRITERIA.md`


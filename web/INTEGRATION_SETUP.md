# دليل التكامل الفعلي - Integration Setup Guide

## 🎯 نظرة عامة

هذا الدليل يشرح كيفية ربط تطبيق الويب (Next.js) مع Backend API (FastAPI) بشكل فعلي.

---

## 📋 المتطلبات

1. ✅ Python 3.13+ مثبت
2. ✅ Node.js 18+ مثبت
3. ✅ قاعدة البيانات جاهزة (`data/logical_release.db`)
4. ✅ جميع المتطلبات مثبتة

---

## 🚀 الخطوة 1: إعداد Environment Variables

### إنشاء ملف `.env.local` في مجلد `web/`

```bash
# في مجلد web/
cd web
```

أنشئ ملف `.env.local` بالمحتوى التالي:

```env
# إعدادات API للتكامل مع Backend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000

# إعدادات البيئة
NODE_ENV=development
```

**ملاحظة**: إذا كان الملف موجوداً، تأكد من أن القيم صحيحة.

---

## 🚀 الخطوة 2: تشغيل Backend API

### في Terminal منفصل:

```bash
# الانتقال إلى المجلد الرئيسي
cd "C:\Users\pc\Desktop\Logical Version trae"

# تشغيل Backend API
python -m uvicorn src.api.app:app --reload --port 8000 --host 0.0.0.0
```

### التحقق من التشغيل:

افتح المتصفح: **http://localhost:8000/health**

يجب أن ترى:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "api_version": "v1"
}
```

---

## 🚀 الخطوة 3: تشغيل تطبيق الويب

### في Terminal آخر:

```bash
# الانتقال إلى مجلد web
cd web

# تشغيل Development Server
npm run dev
```

### التحقق من التشغيل:

افتح المتصفح: **http://localhost:3000**

---

## ✅ الخطوة 4: اختبار التكامل

### 1. اختبار Health Check من الويب

افتح Console في المتصفح (F12) وجرب:

```javascript
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
```

يجب أن ترى: `{status: "healthy", ...}`

### 2. اختبار تسجيل الدخول

1. افتح: **http://localhost:3000/login**
2. أدخل:
   - **البريد**: `admin@standard.com`
   - **كلمة المرور**: `123456`
3. اضغط "تسجيل الدخول"

### 3. التحقق من API Calls

افتح **Network Tab** في DevTools (F12) وتحقق من:
- ✅ طلبات API تذهب إلى `http://localhost:8000/api/v1/...`
- ✅ لا توجد أخطاء CORS
- ✅ الردود تأتي بنجاح

---

## 🔧 إعدادات CORS

Backend API مُعدّ لدعم CORS من:
- ✅ `http://localhost:3000` (Frontend Dev Server)
- ✅ `*` (في وضع التطوير)

إذا واجهت مشاكل CORS، تحقق من:
1. Backend يعمل على المنفذ 8000
2. Frontend يعمل على المنفذ 3000
3. CORS origins في `src/api/app.py` صحيحة

---

## 📊 Endpoints المتاحة

### Authentication
- `POST /api/v1/auth/login` - تسجيل الدخول
- `POST /api/v1/auth/refresh` - تحديث Token
- `GET /api/v1/auth/me` - معلومات المستخدم
- `GET /api/v1/auth/companies` - قائمة الشركات

### Products
- `GET /api/v1/products` - قائمة المنتجات
- `POST /api/v1/products` - إنشاء منتج
- `GET /api/v1/products/{id}` - منتج محدد
- `PUT /api/v1/products/{id}` - تحديث منتج
- `DELETE /api/v1/products/{id}` - حذف منتج

### Sales
- `GET /api/v1/sales` - قائمة المبيعات
- `POST /api/v1/sales` - إنشاء فاتورة
- `GET /api/v1/sales/{id}` - فاتورة محددة

### Dashboard
- `GET /api/v1/dashboard/stats` - إحصائيات Dashboard

---

## 🐛 حل المشاكل الشائعة

### المشكلة 1: "Failed to fetch" أو CORS Error

**الحل**:
1. تأكد من أن Backend يعمل
2. تحقق من `NEXT_PUBLIC_API_BASE_URL` في `.env.local`
3. أعد تشغيل Frontend بعد تغيير `.env.local`

### المشكلة 2: "401 Unauthorized"

**الحل**:
1. تأكد من تسجيل الدخول أولاً
2. تحقق من أن Token موجود في localStorage
3. جرب تحديث Token

### المشكلة 3: "500 Internal Server Error"

**الحل**:
1. تحقق من logs في Backend Terminal
2. تأكد من أن قاعدة البيانات موجودة
3. تحقق من إعدادات قاعدة البيانات

### المشكلة 4: Port 8000 مستخدم

**الحل**:
```bash
# استخدم منفذ آخر
python -m uvicorn src.api.app:app --reload --port 8001

# ثم غيّر في .env.local:
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

---

## 📝 ملاحظات مهمة

1. **يجب تشغيل Backend قبل Frontend**
2. **يجب إعادة تشغيل Frontend بعد تغيير `.env.local`**
3. **استخدم `--reload` في Backend للتطوير (auto-reload)**
4. **تحقق من Console في المتصفح للأخطاء**

---

## 🎯 الخطوات التالية

بعد إتمام التكامل:

1. ✅ اختبار جميع Endpoints
2. ✅ اختبار Authentication Flow
3. ✅ اختبار CRUD Operations
4. ✅ اختبار Real-time Updates (WebSocket)

---

## 📚 مراجع إضافية

- [Backend Start Guide](./BACKEND_START_GUIDE.md)
- [API Configuration](../docs/API_GUIDE.md)
- [Authentication Guide](../docs/AUTH_GUIDE.md)

---

**تاريخ الإنشاء**: 31 ديسمبر 2025
**آخر تحديث**: 31 ديسمبر 2025


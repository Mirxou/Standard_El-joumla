# دليل تشغيل Backend API - Backend Start Guide

## 📍 موقع Backend API

**الملف**: `src/api/app.py`
**النوع**: FastAPI Application
**المنفذ**: 8000

---

## 🚀 طريقة التشغيل

### الطريقة 1: استخدام uvicorn مباشرة
```bash
# من المجلد الرئيسي للمشروع
cd "C:\Users\pc\Desktop\Logical Version trae"
python -m uvicorn src.api.app:app --reload --port 8000 --host 0.0.0.0
```

### الطريقة 2: استخدام main.py (إن وجد)
```bash
# من المجلد الرئيسي
python main.py
```

### الطريقة 3: استخدام Docker (إن كان متوفر)
```bash
docker-compose up api
```

---

## ✅ التحقق من التشغيل

بعد تشغيل Backend، تحقق من:

1. **Health Check**:
   - افتح: http://localhost:8000/health
   - يجب أن ترى: `{"status":"healthy","version":"1.0.0","api_version":"v1"}`

2. **API Documentation**:
   - افتح: http://localhost:8000/docs
   - يجب أن ترى Swagger UI

3. **OpenAPI Schema**:
   - افتح: http://localhost:8000/openapi.json

---

## 🔍 اختبار Login Endpoint

### باستخدام PowerShell:
```powershell
$body = @{
    username = "admin@standard.com"
    password = "123456"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

### باستخدام curl (في Git Bash):
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@standard.com","password":"123456"}'
```

---

## 📋 Endpoints المتاحة

### Authentication
- `POST /api/v1/auth/login` - تسجيل الدخول
- `POST /api/v1/auth/logout` - تسجيل الخروج
- `POST /api/v1/auth/refresh` - تحديث Token
- `GET /api/v1/auth/companies` - جلب الشركات

### Health & Docs
- `GET /health` - فحص الصحة
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc Documentation
- `GET /openapi.json` - OpenAPI Schema

---

## ⚠️ المشاكل الشائعة

### المشكلة 1: Port 8000 مستخدم
**الحل**:
```bash
# استخدم منفذ آخر
python -m uvicorn src.api.app:app --reload --port 8001

# ثم غيّر في .env.local:
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

### المشكلة 2: Database Error
**الحل**:
- تأكد من وجود قاعدة البيانات
- تحقق من مسار قاعدة البيانات في config

### المشكلة 3: Import Errors
**الحل**:
```bash
# تأكد من تثبيت المتطلبات
pip install -r requirements.txt
```

---

## 🔧 إعدادات CORS

Backend يدعم CORS من:
- `http://localhost:3000` (Frontend Dev Server)
- `*` (في وضع التطوير)

---

## 📝 Logs

عند تشغيل Backend، ستظهر logs في Terminal:
- ✅ رسائل نجاح التهيئة
- ⚠️ تحذيرات
- ❌ أخطاء

---

## 🎯 الخطوات التالية

1. ✅ شغّل Backend API
2. ✅ تحقق من Health Check
3. ✅ جرب تسجيل الدخول من Frontend
4. ✅ تحقق من Console في Browser (F12)

---

**ملاحظة**: يجب أن يعمل Backend قبل محاولة تسجيل الدخول من Frontend!

---

**تاريخ الإنشاء**: 28 ديسمبر 2025


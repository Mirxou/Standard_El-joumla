# دليل حل مشاكل تسجيل الدخول - Login Troubleshooting Guide

## 🔍 المشكلة

خطأ في تسجيل الدخول: "حدث خطأ أثناء تسجيل الدخول"

## ✅ الحلول المقترحة

### 1. التحقق من Backend API

**التحقق من تشغيل Backend:**
```bash
# في terminal منفصل
cd ../src/api  # أو مسار Backend الخاص بك
python -m uvicorn app:app --reload --port 8000
```

**اختبار Backend:**
```bash
# في PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body '{"username":"test","password":"test"}' -ContentType "application/json"
```

### 2. التحقق من Environment Variables

**الملف**: `web/.env.local`

يجب أن يحتوي على:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**بعد التعديل:**
- أعد تشغيل Dev Server (`npm run dev`)

### 3. التحقق من API Endpoint

**Endpoint المتوقع**: `POST /api/v1/auth/login`

**Payload المتوقع**:
```json
{
  "username": "admin@standard.com",
  "password": "123456"
}
```

### 4. فحص Console Logs

افتح Developer Tools (F12) وتحقق من:
- Network tab: هل الطلب يصل للـ Backend؟
- Console tab: ما هي رسالة الخطأ الدقيقة؟

### 5. التحقق من CORS

إذا كان Backend يعمل لكن الطلب يفشل:
- تأكد من أن Backend يسمح بـ CORS من `http://localhost:3000`
- تحقق من headers في Network tab

## 🛠️ خطوات التشخيص

### الخطوة 1: فحص Backend
```bash
# اختبار Backend مباشرة
Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing
```

### الخطوة 2: فحص Network Request
1. افتح Developer Tools (F12)
2. اذهب إلى Network tab
3. حاول تسجيل الدخول
4. ابحث عن request إلى `/api/v1/auth/login`
5. تحقق من:
   - Status Code
   - Response Body
   - Request Headers

### الخطوة 3: فحص Console
- ابحث عن أي أخطاء في Console
- تحقق من رسائل الخطأ المفصلة

## 📝 رسائل الخطأ المحسنة

تم تحسين معالجة الأخطاء في `auth-context.tsx` لعرض رسائل أوضح:

- **401**: "البريد الإلكتروني أو كلمة المرور غير صحيحة"
- **404**: "الخادم غير متاح. تأكد من تشغيل Backend API"
- **500**: "خطأ في الخادم. يرجى المحاولة لاحقاً"
- **Network Error**: "لا يمكن الاتصال بالخادم. تأكد من تشغيل Backend API على http://localhost:8000"

## ✅ الحل السريع

1. **تأكد من تشغيل Backend:**
   ```bash
   # في terminal منفصل
   python -m uvicorn app:app --reload --port 8000
   ```

2. **تحقق من .env.local:**
   ```
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

3. **أعد تشغيل Dev Server:**
   ```bash
   cd web
   npm run dev
   ```

4. **جرب تسجيل الدخول مرة أخرى**

## 🔗 روابط مفيدة

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs (إذا كان متاحاً)

---

**تاريخ الإنشاء**: 28 ديسمبر 2025


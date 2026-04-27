# 🚀 دليل التكامل السريع - Quick Integration Guide

## البدء السريع

### 1. تشغيل Backend
```bash
cd "C:\Users\pc\Desktop\Logical Version trae"
python -m uvicorn src.api.app:app --reload --port 8000 --host 0.0.0.0
```

### 2. تشغيل Frontend
```bash
cd web
npm run dev
```

### 3. فتح التطبيق
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## اختبار التكامل

افتح `test-integration.html` في المتصفح لاختبار جميع Endpoints.

---

## بيانات تسجيل الدخول

- **البريد**: `admin@standard.com`
- **كلمة المرور**: `123456`

---

## للمزيد من التفاصيل

راجع: [INTEGRATION_SETUP.md](./INTEGRATION_SETUP.md)


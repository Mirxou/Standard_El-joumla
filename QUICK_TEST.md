# 🚀 اختبار سريع - Quick Test Guide

## اختبارات جاهزة للاستخدام

### 1. اختبار الخدمات (Services)

```bash
python scripts/test_services.py
```

**النتيجة المتوقعة:** ✅ جميع الاختبارات نجحت (13/13)

---

### 2. اختبار Docker Setup

```bash
python scripts/test_docker.py
```

**النتيجة المتوقعة:**
- ✅ Docker مثبت
- ✅ Docker Compose مثبت
- ✅ الملفات موجودة
- ✅ docker-compose.yml صحيح
- ⚠️ Docker Daemon يحتاج تشغيل Docker Desktop

**لتفعيل Docker Daemon:**
1. شغّل Docker Desktop
2. انتظر حتى يظهر "Docker is running"
3. أعد تشغيل الاختبار

---

### 3. اختبار REST API

```bash
# أولاً، شغّل API
docker-compose up -d api

# ثم اختبر
python scripts/test_api.py http://localhost:8000
```

**أو بدون Docker:**
```bash
# شغّل API محلياً
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# ثم اختبر
python scripts/test_api.py http://localhost:8000
```

---

### 4. اختبار شامل (جميع الاختبارات)

```bash
python scripts/run_all_tests.py
```

---

## نتائج الاختبار الحالية

### ✅ اختبار الخدمات: **نجح (13/13)**
- جميع الوحدات قابلة للاستيراد
- قاعدة البيانات تهيئة بنجاح
- جميع الخدمات قابلة للتهيئة

### ✅ اختبار Docker Setup: **نجح جزئياً (11/12)**
- Docker مثبت ✅
- Docker Compose مثبت ✅
- الملفات موجودة ✅
- docker-compose.yml صحيح ✅
- المنافذ متاحة ✅
- ⚠️ Docker Daemon يحتاج تشغيل Docker Desktop

---

## الخطوات التالية

### لتشغيل النظام بالكامل:

1. **شغّل Docker Desktop**
   - افتح Docker Desktop
   - انتظر حتى يظهر "Docker is running"

2. **عدّل ملف البيئة (اختياري)**
   ```bash
   # انسخ الملف
   cp .docker.env.example .docker.env
   
   # عدّل القيم حسب الحاجة
   # POSTGRES_PASSWORD=your_password
   # JWT_SECRET_KEY=your_secret_key
   ```

3. **شغّل الخدمات**
   ```bash
   docker-compose up -d
   ```

4. **تحقق من الحالة**
   ```bash
   docker-compose ps
   ```

5. **اختبر API**
   ```bash
   python scripts/test_api.py http://localhost:8000
   ```

---

## الوصول إلى الخدمات

بعد تشغيل `docker-compose up -d`:

- **REST API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

---

## استكشاف الأخطاء

### مشكلة: Docker Daemon غير يعمل

**الحل:**
1. شغّل Docker Desktop
2. انتظر حتى يظهر "Docker is running"
3. أعد تشغيل الاختبار

### مشكلة: Port مستخدم

**الحل:**
1. ابحث عن العملية:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```
2. أو غيّر المنفذ في `docker-compose.yml`

### مشكلة: API لا يستجيب

**الحل:**
1. تحقق من Logs:
   ```bash
   docker-compose logs api
   ```
2. تحقق من Health:
   ```bash
   curl http://localhost:8000/health
   ```

---

## ملاحظات

- ✅ جميع السكريبتات تعمل على Windows/Linux/Mac
- ✅ الاختبارات لا تحتاج تشغيل Docker (باستثناء test_docker.py)
- ✅ يمكن تشغيل API محلياً بدون Docker للاختبار


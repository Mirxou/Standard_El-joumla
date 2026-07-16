# 🧪 دليل الاختبار - Testing Guide

## نظرة عامة

هذا الدليل يشرح كيفية اختبار النظام بعد إعداد Docker والخدمات.

---

## الاختبارات المتاحة

### 1. اختبار الخدمات (Services Tests)

**Windows/Linux/Mac:**
```bash
python scripts/test_services.py
```

**Linux/Mac (Bash):**
```bash
bash scripts/test-services.sh
```

**ما يختبره:**
- ✅ استيراد جميع الوحدات Python
- ✅ تهيئة قاعدة البيانات
- ✅ تهيئة الخدمات (ComplianceService, SSOService, SecurityMonitor, IntrusionDetectionSystem)

---

### 2. اختبار Docker Setup

**Windows/Linux/Mac:**
```bash
python scripts/test_docker.py
```

**Linux/Mac (Bash):**
```bash
bash scripts/test-docker.sh
```

**ما يختبره:**
- ✅ تثبيت Docker و Docker Compose
- ✅ تشغيل Docker Daemon
- ✅ وجود الملفات المطلوبة
- ✅ صحة docker-compose.yml
- ✅ توفر المنافذ
- ✅ Health Check Endpoints

---

### 3. اختبار REST API

**Windows/Linux/Mac:**
```bash
python scripts/test_api.py [API_URL]
```

**مثال:**
```bash
python scripts/test_api.py http://localhost:8000
```

**Linux/Mac (Bash):**
```bash
bash scripts/test-api.sh http://localhost:8000
```

**ما يختبره:**
- ✅ Health Check (`/health`)
- ✅ API Health Check (`/api/v1/health`)
- ✅ OpenAPI Documentation (`/docs`)
- ✅ OpenAPI JSON (`/openapi.json`)
- ✅ Login Endpoint
- ✅ Rate Limiting

---

### 4. اختبار شامل (جميع الاختبارات)

**Windows/Linux/Mac:**
```bash
python scripts/run_all_tests.py
```

**Linux/Mac (Bash):**
```bash
bash scripts/run-all-tests.sh
```

يشغل جميع الاختبارات أعلاه بالتسلسل ويعرض ملخص نهائي.

---

## اختبارات الأداء (Performance Tests)

### Stress Test باستخدام Locust

```bash
bash scripts/stress-test.sh [endpoint] [users] [duration]
```

**مثال:**
```bash
bash scripts/stress-test.sh http://localhost:8000 100 60
```

**ما يختبره:**
- محاكاة 100 مستخدم لمدة 60 ثانية
- اختبار endpoints مختلفة (Products, Sales, Analytics)
- قياس Response Time و Throughput

**النتائج:**
- Report HTML في `reports/stress-test-report.html`

---

## اختبار Docker Containers

### 1. بناء Images

```bash
docker-compose build
```

### 2. تشغيل الخدمات

```bash
docker-compose up -d
```

### 3. فحص الحالة

```bash
docker-compose ps
```

### 4. عرض Logs

```bash
# جميع الخدمات
docker-compose logs -f

# خدمة محددة
docker-compose logs -f api
docker-compose logs -f postgres
```

### 5. اختبار Health Checks

```bash
# API Health
curl http://localhost:8000/health

# API v1 Health
curl http://localhost:8000/api/v1/health
```

### 6. إيقاف الخدمات

```bash
docker-compose down
```

---

## اختبار Super Admin Dashboard

1. شغّل التطبيق:
```bash
python main.py
```

2. افتح قائمة "✅ الامتثال والأمان"
3. اختر "🎛️ لوحة تحكم المدير الخارق"
4. تحقق من:
   - ✅ System Health (CPU, Memory, Disk)
   - ✅ Security Status
   - ✅ Database Status
   - ✅ Services Status
   - ✅ Recent Threats

---

## اختبارات التكامل (Integration Tests)

### اختبار API مع Authentication

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# 2. Use Token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/products
```

---

## اختبارات الأمان (Security Tests)

### اختبار Intrusion Detection

```python
from src.core.intrusion_detection import IntrusionDetectionSystem
from src.core.database_manager import DatabaseManager

db = DatabaseManager(':memory:')
db.initialize()

ids = IntrusionDetectionSystem(db)

# Test Brute Force Detection
threat = ids.detect_brute_force("192.168.1.100", "admin")
print(f"Threat detected: {threat}")

# Test SQL Injection Detection
threat = ids.detect_sql_injection("'; DROP TABLE users; --", "192.168.1.100")
print(f"SQL Injection detected: {threat}")
```

---

## اختبارات الأداء (Performance Benchmarks)

### Database Query Performance

```python
import time
from src.core.database_manager import DatabaseManager

db = DatabaseManager(':memory:')
db.initialize()

# Test query performance
start = time.time()
products = db.fetch_all("SELECT * FROM products LIMIT 1000")
end = time.time()

print(f"Query time: {(end - start) * 1000:.2f}ms")
```

---

## Troubleshooting

### مشكلة: Docker لا يعمل

```bash
# تحقق من حالة Docker
docker info

# أعد تشغيل Docker
sudo systemctl restart docker  # Linux
# أو أعد تشغيل Docker Desktop (Windows/Mac)
```

### مشكلة: Ports مستخدمة

```bash
# ابحث عن العملية التي تستخدم المنفذ
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# غيّر المنفذ في docker-compose.yml
```

### مشكلة: API لا يستجيب

```bash
# تحقق من Logs
docker-compose logs api

# تحقق من Health
curl http://localhost:8000/health
```

---

## النتائج المتوقعة

### ✅ اختبارات ناجحة

- جميع الخدمات قابلة للاستيراد
- قاعدة البيانات تهيئة بنجاح
- Docker Images مبنية بنجاح
- Health Checks تعمل
- API يستجيب بشكل صحيح

### ⚠️ تحذيرات متوقعة

- بعض المنافذ قد تكون مستخدمة (طبيعي)
- Rate Limiting قد لا يكون مفعّل في Development Mode
- بعض الخدمات قد تحتاج إعدادات إضافية

---

## الخطوات التالية بعد الاختبار

1. ✅ إذا نجحت جميع الاختبارات: النظام جاهز للنشر
2. ⚠️ إذا فشلت بعض الاختبارات: راجع الأخطاء وأصلحها
3. 📊 بعد النشر: راقب الأداء باستخدام Grafana Dashboard


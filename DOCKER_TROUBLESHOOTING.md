# 🔧 استكشاف أخطاء Docker - Troubleshooting Guide

## المشاكل الشائعة والحلول

### 1. خطأ BuildKit gRPC

**الخطأ:**
```
failed to dial gRPC: rpc error: code = Internal desc = header key "x-docker-expose-session-sharedkey" contains value with non-printable ASCII characters
```

**الحل:**
```powershell
# Windows PowerShell
$env:DOCKER_BUILDKIT = "0"
$env:COMPOSE_DOCKER_CLI_BUILD = "0"
docker-compose build

# أو استخدم السكريبت
.\scripts\docker-start.ps1
```

```bash
# Linux/Mac
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0
docker-compose build
```

---

### 2. تحذير `version` obsolete

**التحذير:**
```
the attribute `version` is obsolete, it will be ignored
```

**الحل:**
تم إزالة `version` من `docker-compose.yml` و `docker-compose.dev.yml` ✅

---

### 3. API لا يستجيب

**الخطأ:**
```
[WinError 10061] Aucune connexion n'a pu être établie
```

**الحل:**
1. تحقق من حالة الـ Containers:
   ```powershell
   docker-compose ps
   ```

2. شغّل الـ Containers:
   ```powershell
   .\scripts\docker-start.ps1
   ```

3. تحقق من Logs:
   ```powershell
   docker-compose logs api
   ```

---

### 4. Port مستخدم

**الخطأ:**
```
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**الحل:**
1. ابحث عن العملية:
   ```powershell
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```

2. أو غيّر المنفذ في `docker-compose.yml`:
   ```yaml
   ports:
     - "8001:8000"  # استخدم 8001 بدلاً من 8000
   ```

---

### 5. Database Connection Error

**الخطأ:**
```
could not connect to server: Connection refused
```

**الحل:**
1. تحقق من حالة PostgreSQL:
   ```powershell
   docker-compose ps postgres
   ```

2. تحقق من Logs:
   ```powershell
   docker-compose logs postgres
   ```

3. انتظر حتى يكون PostgreSQL جاهزاً:
   ```powershell
   docker-compose up -d postgres
   # انتظر 10-15 ثانية
   docker-compose up -d api
   ```

---

### 6. Health Check فشل

**الخطأ:**
```
Health check failed
```

**الحل:**
1. تحقق من أن API يعمل:
   ```powershell
   curl http://localhost:8000/health
   ```

2. زد وقت الانتظار في `docker-compose.yml`:
   ```yaml
   healthcheck:
     start_period: 60s  # بدلاً من 40s
   ```

---

## السكريبتات المتاحة

### Windows PowerShell

```powershell
# بدء الخدمات
.\scripts\docker-start.ps1

# عرض Logs
.\scripts\docker-logs.ps1
.\scripts\docker-logs.ps1 api  # لخدمة محددة

# إيقاف الخدمات
.\scripts\docker-stop.ps1

# بناء Images فقط
.\scripts\docker-build.ps1
```

### Linux/Mac

```bash
# بدء الخدمات
bash scripts/docker-start.sh

# عرض Logs
docker-compose logs -f
docker-compose logs -f api  # لخدمة محددة

# إيقاف الخدمات
docker-compose down

# بناء Images فقط
bash scripts/docker-build.sh
```

---

## خطوات التشخيص

### 1. تحقق من Docker

```powershell
docker --version
docker-compose --version
docker info
```

### 2. تحقق من الملفات

```powershell
# تحقق من وجود الملفات
Test-Path docker-compose.yml
Test-Path Dockerfile
Test-Path Dockerfile.api
```

### 3. تحقق من صحة docker-compose.yml

```powershell
docker-compose config
```

### 4. تحقق من حالة الـ Containers

```powershell
docker-compose ps
docker ps -a
```

### 5. تحقق من Logs

```powershell
# جميع الخدمات
docker-compose logs

# خدمة محددة
docker-compose logs api
docker-compose logs postgres
docker-compose logs redis
```

### 6. اختبار الاتصال

```powershell
# Health Check
curl http://localhost:8000/health

# API Health
curl http://localhost:8000/api/v1/health
```

---

## إعادة البناء الكاملة

إذا واجهت مشاكل مستمرة:

```powershell
# 1. إيقاف وإزالة كل شيء
docker-compose down -v

# 2. إزالة Images القديمة
docker rmi erp_api erp_web erp_worker 2>$null

# 3. إعادة البناء
$env:DOCKER_BUILDKIT = "0"
docker-compose build --no-cache

# 4. تشغيل
docker-compose up -d
```

---

## نصائح عامة

1. **استخدم SQLite للتطوير:** أسهل وأسرع من PostgreSQL
2. **راقب Logs:** استخدم `docker-compose logs -f` لمراقبة الأخطاء
3. **تحقق من Health Checks:** انتظر حتى تصبح جميع الخدمات healthy
4. **استخدم السكريبتات:** السكريبتات تعالج المشاكل تلقائياً

---

## الدعم

إذا استمرت المشاكل:

1. تحقق من Logs:
   ```powershell
   docker-compose logs > docker-logs.txt
   ```

2. تحقق من حالة النظام:
   ```powershell
   docker system df
   docker system prune  # احذر: يحذف البيانات غير المستخدمة
   ```

3. أعد تشغيل Docker Desktop (Windows/Mac)


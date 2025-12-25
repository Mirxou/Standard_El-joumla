# 🔧 إصلاح مشاكل Docker - Docker Fix Guide

## المشاكل والحلول

### المشكلة 1: BuildKit gRPC Error

**الخطأ:**
```
failed to dial gRPC: rpc error: code = Internal desc = header key "x-docker-expose-session-sharedkey" contains value with non-printable ASCII characters
```

**الحلول:**

#### الحل 1: استخدام السكريبت المصلح
```powershell
.\scripts\docker-start-fixed.ps1
```

#### الحل 2: تعطيل BuildKit يدوياً
```powershell
$env:DOCKER_BUILDKIT = "0"
$env:COMPOSE_DOCKER_CLI_BUILD = "0"
docker-compose build
docker-compose up -d
```

#### الحل 3: بناء مباشر بدون BuildKit
```powershell
docker build -f Dockerfile.api -t erp_api:latest . --no-cache
docker-compose up -d
```

---

### المشكلة 2: Encoding في PowerShell

**الخطأ:**
```
Le terminateur " est manquant dans la chaîne
```

**الحل:**
تم إصلاح جميع ملفات PowerShell وإزالة الأحرف العربية من الأوامر ✅

---

### المشكلة 3: Containers لا تبدأ

**الحل:**

1. **تحقق من حالة Docker:**
   ```powershell
   docker info
   ```

2. **شغّل بدون بناء (إذا كانت Images موجودة):**
   ```powershell
   .\scripts\docker-start-simple.ps1
   ```

3. **شغّل مع معالجة الأخطاء:**
   ```powershell
   .\scripts\docker-start-fixed.ps1
   ```

---

## السكريبتات المتاحة

### 1. docker-start-fixed.ps1 (موصى به)
- معالجة أفضل للأخطاء
- يحاول عدة طرق للبناء
- يعرض معلومات مفصلة

```powershell
.\scripts\docker-start-fixed.ps1
```

### 2. docker-start-simple.ps1
- يبدأ الخدمات بدون بناء
- سريع إذا كانت Images موجودة

```powershell
.\scripts\docker-start-simple.ps1
```

### 3. docker-start.ps1
- السكريبت الأساسي (محدث)

```powershell
.\scripts\docker-start.ps1
```

---

## خطوات التشخيص

### 1. تحقق من Docker
```powershell
docker --version
docker info
```

### 2. تحقق من الملفات
```powershell
Test-Path docker-compose.yml
Test-Path Dockerfile.api
```

### 3. بناء Image مباشرة
```powershell
docker build -f Dockerfile.api -t erp_api:latest .
```

### 4. تشغيل Container مباشرة
```powershell
docker run -d -p 8000:8000 --name erp_api erp_api:latest
```

### 5. تحقق من Logs
```powershell
docker logs erp_api
```

---

## حل بديل: تشغيل API محلياً

إذا استمرت مشاكل Docker، يمكن تشغيل API محلياً:

```powershell
# في Terminal منفصل
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# ثم اختبر
python scripts/test_api.py http://localhost:8000
```

---

## نصائح

1. **استخدم docker-start-fixed.ps1** - أفضل معالجة للأخطاء
2. **راقب Logs** - `docker-compose logs -f api`
3. **تحقق من Ports** - تأكد أن المنافذ متاحة
4. **أعد تشغيل Docker Desktop** - إذا استمرت المشاكل

---

## حالة الخدمات

بعد التشغيل، تحقق من:
```powershell
docker-compose ps
```

يجب أن ترى:
- `erp_api` - running
- `erp_redis` - running (إذا كان مفعّل)

---

## اختبار سريع

```powershell
# 1. شغّل الخدمات
.\scripts\docker-start-fixed.ps1

# 2. انتظر 15-20 ثانية

# 3. اختبر API
python scripts/test_api.py http://localhost:8000

# 4. أو اختبر يدوياً
curl http://localhost:8000/health
```


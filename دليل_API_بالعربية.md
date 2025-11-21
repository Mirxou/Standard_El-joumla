# 🌐 دليل استخدام REST API - الإصدار المنطقي v1.1.0

## 📋 نظرة عامة

واجهة برمجية احترافية مبنية على FastAPI تتيح الوصول لبيانات النظام عبر HTTP.

**العنوان الأساسي:** `http://localhost:8000`  
**التوثيق التفاعلي:** `http://localhost:8000/docs`  
**توثيق ReDoc:** `http://localhost:8000/redoc`

---

## 🚀 البدء السريع

### 1. تشغيل خادم API

```bash
# من المجلد الرئيسي
python scripts/run_api_server.py

# أو من النسخة المحمولة
انقر مزدوجاً على "تشغيل API Server.bat"
```

### 2. اختبار الاتصال

```bash
# PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health

# المتصفح
افتح http://localhost:8000/health
```

النتيجة المتوقعة:
```json
{
  "status": "ok"
}
```

---

## 🔐 المصادقة

### الحصول على رمز JWT

**نقطة النهاية:** `POST /auth/login`

**الطلب:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**مثال (PowerShell):**
```powershell
$body = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/auth/login `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$token = $response.access_token
Write-Host "Token: $token"
```

**الاستجابة:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### استخدام الرمز

أضف الرمز لرأس Authorization في كل طلب:

```
Authorization: Bearer <رمز_JWT>
```

---

## 📊 نقاط النهاية

### 1. العملاء (Customers)

**الحصول على قائمة العملاء**

```http
GET /customers?page=1&page_size=20
Authorization: Bearer <token>
```

**المعاملات:**
- `page` (اختياري): رقم الصفحة (افتراضي: 1)
- `page_size` (اختياري): حجم الصفحة (افتراضي: 20، الحد الأقصى: 100)

**مثال (PowerShell):**
```powershell
$headers = @{
    Authorization = "Bearer $token"
}

$customers = Invoke-RestMethod -Uri "http://localhost:8000/customers?page=1&page_size=10" `
    -Method GET `
    -Headers $headers

Write-Host "العدد الإجمالي: $($customers.total)"
Write-Host "عدد النتائج: $($customers.items.Count)"
```

**الاستجابة:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "أحمد محمد",
      "phone": "0501234567",
      "email": "ahmed@example.com",
      "balance": 1500.00
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "has_next": true
}
```

---

### 2. المنتجات (Products)

#### أ. عرض المنتجات + فلترة بالوسوم

```http
GET /products?page=1&page_size=20&tag=summer
Authorization: Bearer <token>
```

الاستجابة (مختصر):
```json
{
  "items": [{"id": 1, "name": "قميص", "sale_price": 80.0, "stock_quantity": 10}],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "has_next": false
}
```

#### ب. إنشاء منتج (Admin)

```http
POST /products
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "قميص قطن",
  "name_en": "Cotton Shirt",
  "unit": "قطعة",
  "cost_price": 50.0,
  "selling_price": 80.0,
  "barcode": "PRD-001"
}
```

الاستجابة:
```json
{ "id": 101 }
```

#### ج. تفاصيل المنتج + المتغيرات

```http
GET /products/{id}
Authorization: Bearer <token>
```

الاستجابة (مختصر):
```json
{
  "id": 101,
  "name": "قميص قطن",
  "selling_price": 80.0,
  "current_stock": 10,
  "barcodes": [{"barcode": "PRD-001", "is_primary": true}],
  "variants": [
    {"id": 5, "sku": "PRD-001-L-RED", "attributes": {"size": "L", "color": "Red"}}
  ]
}
```

#### د. إنشاء متغير (Admin)

```http
POST /products/{id}/variants
Authorization: Bearer <token>
Content-Type: application/json

{
  "sku": "PRD-001-L-RED",
  "attributes": {"size": "L", "color": "Red"},
  "selling_price": 85.0,
  "current_stock": 3
}
```

الاستجابة:
```json
{ "id": 5, "product_id": 101 }
```

---

### 3. الفواتير (Invoices)

**الحصول على قائمة الفواتير**

```http
GET /invoices?page=1&page_size=20
Authorization: Bearer <token>
```

**مثال (PowerShell):**
```powershell
$invoices = Invoke-RestMethod -Uri "http://localhost:8000/invoices?page=1&page_size=5" `
    -Method GET `
    -Headers $headers

foreach ($invoice in $invoices.items) {
    Write-Host "فاتورة #$($invoice.id) - المبلغ: $($invoice.total_amount)"
}
```

**الاستجابة:**
```json
{
  "items": [
    {
      "id": 1,
      "customer_name": "أحمد محمد",
      "total_amount": 5200.00,
      "paid_amount": 3000.00,
      "status": "جزئي",
      "created_at": "2025-11-19T10:30:00"
    }
  ],
  "total": 78,
  "page": 1,
  "page_size": 20,
  "has_next": true
}
```

---

### 4. الوسوم (Tags)

#### أ. إضافة وسم لمنتج (Admin)
```http
POST /products/{product_id}/tags
Authorization: Bearer <token>
Content-Type: application/json

{ "tag": "summer" }
```

#### ب. استعراض الوسوم
```http
GET /products/{product_id}/tags
Authorization: Bearer <token>
```

الاستجابة:
```json
{ "product_id": 101, "tags": ["summer", "cotton"] }
```

#### ج. حذف وسم (Admin)
```http
DELETE /products/{product_id}/tags/{tag}
Authorization: Bearer <token>
```

---

### 5. الحزم (Bundles)

#### أ. إنشاء حزمة (Admin)
```http
POST /products/{product_id}/bundles
Authorization: Bearer <token>
Content-Type: application/json

{ "name": "عرض المدرسة", "description": "حزمة قرطاسية" }
```

#### ب. إضافة عنصر للحزمة (منتج/متغير)
```http
POST /bundles/{bundle_id}/items
Authorization: Bearer <token>
Content-Type: application/json

{ "item_type": "product", "item_product_id": 55, "quantity": 2 }
```

#### ج. استعراض الحزم والتفاصيل
```http
GET /bundles?page=1&page_size=20
GET /bundles/{bundle_id}
Authorization: Bearer <token>
```

---

### 6. التسعير المتقدم (Pricing)

#### أ. إنشاء شريحة تسعير (Admin)
```http
POST /prices
Authorization: Bearer <token>
Content-Type: application/json

{ "product_id": 101, "price_type": "retail", "min_qty": 10, "price": 75.0 }
```

#### ب. استعراض شرائح التسعير
```http
GET /products/{product_id}/prices
GET /variants/{variant_id}/prices
Authorization: Bearer <token>
```

#### ج. حذف شريحة (Admin)
```http
DELETE /prices/{price_id}
Authorization: Bearer <token>
```

---

### 4. تقييم الموردين (Vendor Rating)

#### أ. إنشاء تقييم (للمدراء فقط)

**نقطة النهاية:** `POST /suppliers/{supplier_id}/evaluations`

**الطلب:**
```json
{
  "quality_score": 4.8,
  "delivery_score": 4.6,
  "pricing_score": 4.2,
  "communication_score": 4.7,
  "reliability_score": 4.9,
  "total_orders": 150,
  "on_time_deliveries": 142,
  "return_rate": 2.5,
  "notes": "مورد ممتاز، توصيل سريع"
}
```

**مثال (PowerShell):**
```powershell
$evaluation = @{
    quality_score = 4.8
    delivery_score = 4.6
    pricing_score = 4.2
    communication_score = 4.7
    reliability_score = 4.9
    total_orders = 150
    on_time_deliveries = 142
    return_rate = 2.5
    notes = "مورد ممتاز"
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:8000/suppliers/1/evaluations" `
    -Method POST `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $evaluation

Write-Host "التقييم الإجمالي: $($result.overall_score)"
Write-Host "التصنيف: $($result.grade)"
```

**الاستجابة:**
```json
{
  "id": 1,
  "supplier_id": 1,
  "quality_score": 4.8,
  "delivery_score": 4.6,
  "pricing_score": 4.2,
  "communication_score": 4.7,
  "reliability_score": 4.9,
  "overall_score": 4.64,
  "grade": "A",
  "total_orders": 150,
  "on_time_deliveries": 142,
  "return_rate": 2.5,
  "notes": "مورد ممتاز، توصيل سريع",
  "created_at": "2025-11-19T10:45:00"
}
```

**ملاحظة:** يتطلب صلاحيات مدير. المستخدمون الآخرون سيحصلون على خطأ 403.

#### ب. الحصول على التقييم

**نقطة النهاية:** `GET /suppliers/{supplier_id}/rating`

**مثال (PowerShell):**
```powershell
$rating = Invoke-RestMethod -Uri "http://localhost:8000/suppliers/1/rating" `
    -Method GET `
    -Headers $headers

Write-Host "الدرجة: $($rating.score)"
Write-Host "التصنيف: $($rating.grade)"
```

**الاستجابة:**
```json
{
  "supplier_id": 1,
  "score": 4.64,
  "grade": "A"
}
```

---

### 5. فحص الصحة (Health Check)

**نقطة النهاية:** `GET /health`

لا يتطلب مصادقة.

**مثال:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

**الاستجابة:**
```json
{
  "status": "ok"
}
```

---

## 📐 نظام التصنيف

### معايير التقييم (1-5)

| المعيار | الوصف |
|---------|--------|
| `quality_score` | جودة المنتجات المستلمة |
| `delivery_score` | التسليم في الوقت المحدد |
| `pricing_score` | تنافسية الأسعار |
| `communication_score` | فعالية التواصل |
| `reliability_score` | الموثوقية الإجمالية |

### التصنيفات (Grades)

| النطاق | التصنيف | الوصف |
|--------|---------|--------|
| 4.8-5.0 | A+ | ممتاز جداً |
| 4.5-4.79 | A | ممتاز |
| 4.0-4.49 | B+ | جيد جداً |
| 3.5-3.99 | B | جيد |
| 3.0-3.49 | C | مقبول |
| 2.0-2.99 | D | ضعيف |
| 0.0-1.99 | F | راسب |

---

## 🔒 الصلاحيات (RBAC)

### الأدوار المدعومة

- `admin` / `ADMIN` / `مدير`: كامل الصلاحيات
- `CASHIER` / `أمين_صندوق`: قراءة فقط
- `INVENTORY_MANAGER` / `مدير_مخزون`: قراءة فقط (حالياً)

### القيود

| النقطة | الصلاحية المطلوبة |
|--------|-------------------|
| `POST /suppliers/{id}/evaluations` | Admin فقط |
| `GET /customers` | أي مستخدم مصادق |
| `GET /products` | أي مستخدم مصادق |
| `POST /products` | Admin فقط |
| `POST /products/{id}/variants` | Admin فقط |
| `POST /products/{id}/tags` | Admin فقط |
| `DELETE /products/{id}/tags/{tag}` | Admin فقط |
| `POST /products/{id}/bundles` | Admin فقط |
| `POST /bundles/{id}/items` | Admin فقط |
| `DELETE /bundles/{id}/items/{item_id}` | Admin فقط |
| `POST /prices` | Admin فقط |
| `DELETE /prices/{price_id}` | Admin فقط |
| `GET /invoices` | أي مستخدم مصادق |
| `GET /suppliers/{id}/rating` | أي مستخدم مصادق |

---

## ⚠️ الأخطاء الشائعة

### 1. 401 Unauthorized

**السبب:** رمز JWT غير صالح أو منتهي الصلاحية

**الحل:**
```powershell
# أعد تسجيل الدخول للحصول على رمز جديد
$response = Invoke-RestMethod -Uri http://localhost:8000/auth/login `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{username="admin"; password="admin123"} | ConvertTo-Json)

$token = $response.access_token
```

### 2. 403 Forbidden

**السبب:** الصلاحيات غير كافية

**الحل:** استخدم حساب مدير لنقاط النهاية المحمية

### 3. 422 Unprocessable Entity

**السبب:** بيانات غير صحيحة

**الحل:** تحقق من صيغة JSON والقيم المطلوبة

---

## 🧪 الاختبار التلقائي

### سكريبت الفحص الصحي

```bash
python scripts/test_api_health.py
```

**يختبر:**
- نقطة /health
- تسجيل الدخول
- النقاط المحمية (customers, products)

**الخروج:**
- `0`: نجح جميع الاختبارات
- `1`: فشل أحد الاختبارات

---

## 🌐 الاستخدام من أجهزة أخرى

### 1. تحديد العنوان في .env

```env
API_HOST=0.0.0.0  # استمع على جميع الواجهات
API_PORT=8000
```

### 2. فتح المنفذ في جدار الحماية

```powershell
# Windows Firewall
New-NetFirewallRule -DisplayName "Logical Version API" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow
```

### 3. الوصول من جهاز آخر

```
http://[SERVER_IP]:8000
```

استبدل `[SERVER_IP]` بعنوان IP الخادم.

---

## 📚 أمثلة متقدمة

### مثال 1: الحصول على جميع الصفحات

```powershell
$allCustomers = @()
$page = 1
$hasNext = $true

while ($hasNext) {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/customers?page=$page&page_size=100" `
        -Method GET `
        -Headers @{Authorization = "Bearer $token"}
    
    $allCustomers += $response.items
    $hasNext = $response.has_next
    $page++
}

Write-Host "إجمالي العملاء: $($allCustomers.Count)"
```

### مثال 2: تقييم دفعة موردين

```powershell
$supplierIds = @(1, 2, 3, 4, 5)

foreach ($id in $supplierIds) {
    $eval = @{
        quality_score = Get-Random -Minimum 4.0 -Maximum 5.0
        delivery_score = Get-Random -Minimum 4.0 -Maximum 5.0
        pricing_score = Get-Random -Minimum 3.5 -Maximum 4.5
        communication_score = Get-Random -Minimum 4.0 -Maximum 5.0
        reliability_score = Get-Random -Minimum 4.0 -Maximum 5.0
        total_orders = Get-Random -Minimum 50 -Maximum 200
        on_time_deliveries = Get-Random -Minimum 40 -Maximum 190
        return_rate = Get-Random -Minimum 1.0 -Maximum 5.0
        notes = "تقييم تلقائي"
    } | ConvertTo-Json
    
    try {
        $result = Invoke-RestMethod -Uri "http://localhost:8000/suppliers/$id/evaluations" `
            -Method POST `
            -Headers @{Authorization = "Bearer $token"} `
            -ContentType "application/json" `
            -Body $eval
        
        Write-Host "المورد $id - التصنيف: $($result.grade)"
    } catch {
        Write-Host "خطأ في تقييم المورد $id"
    }
}
```

### مثال 3: تصدير البيانات إلى CSV

```powershell
# الحصول على جميع المنتجات
$products = Invoke-RestMethod -Uri "http://localhost:8000/products?page=1&page_size=100" `
    -Method GET `
    -Headers @{Authorization = "Bearer $token"}

# تصدير إلى CSV
$products.items | Export-Csv -Path "products_export.csv" `
    -Encoding UTF8 `
    -NoTypeInformation

Write-Host "تم التصدير إلى products_export.csv"
```

---

## 🔧 الإعدادات المتقدمة

### ملف .env

```env
# إعدادات الخادم
API_HOST=0.0.0.0
API_PORT=8000

# أمان JWT
JWT_SECRET_KEY=YOUR_SECURE_SECRET_KEY_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# قاعدة البيانات
DATABASE_PATH=data/logical_version.db

# السجلات
LOG_LEVEL=INFO
LOG_FILE=logs/api_server.log

# تحديد المعدل (قريباً)
RATE_LIMIT_ENABLED=false
RATE_LIMIT_PER_MINUTE=60

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 📞 الدعم

للمزيد من المعلومات، راجع:
- **API_IMPLEMENTATION_SUMMARY.md** - التوثيق التقني الكامل
- **DEPLOYMENT.md** - دليل النشر في الإنتاج
- **README.md** - الدليل الشامل

---

**الإصدار:** 1.1.0  
**تاريخ التحديث:** 19 نوفمبر 2025  
**الترخيص:** MIT

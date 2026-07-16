# مرجع API Endpoints
## API Endpoints Reference

**التاريخ:** 2025-01-16  
**API Version:** v1  
**Base URL:** `http://localhost:8000`

---

## Authentication Endpoints

### POST `/api/v1/auth/login`
تسجيل الدخول والحصول على JWT token

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST `/api/v1/auth/refresh`
تحديث access token

**Request:**
```json
{
  "refresh_token": "string"
}
```

### POST `/api/v1/auth/logout`
تسجيل الخروج

### GET `/api/v1/auth/companies`
الحصول على قائمة الشركات

### GET `/api/v1/auth/me`
الحصول على معلومات المستخدم الحالي

---

## Products Endpoints

### GET `/api/v1/products`
الحصول على قائمة المنتجات

**Query Parameters:**
- `page`: رقم الصفحة (افتراضي: 1)
- `page_size`: حجم الصفحة (افتراضي: 50)
- `search`: البحث بالاسم أو الباركود
- `category_id`: تصفية حسب الفئة

### GET `/api/v1/products/{id}`
الحصول على منتج محدد

### POST `/api/v1/products`
إنشاء منتج جديد

**Request:**
```json
{
  "name": "string",
  "barcode": "string",
  "unit": "string",
  "cost_price": 0.0,
  "selling_price": 0.0,
  "current_stock": 0
}
```

### PUT `/api/v1/products/{id}`
تحديث منتج

### DELETE `/api/v1/products/{id}`
حذف منتج

---

## Categories Endpoints

### GET `/api/v1/categories`
الحصول على قائمة الفئات

### GET `/api/v1/categories/{id}`
الحصول على فئة محددة

### POST `/api/v1/categories`
إنشاء فئة جديدة

### PUT `/api/v1/categories/{id}`
تحديث فئة

### DELETE `/api/v1/categories/{id}`
حذف فئة

---

## Sales Endpoints

### GET `/api/v1/sales`
الحصول على قائمة المبيعات

**Query Parameters:**
- `page`: رقم الصفحة
- `page_size`: حجم الصفحة
- `start_date`: تاريخ البداية
- `end_date`: تاريخ النهاية
- `customer_id`: تصفية حسب العميل

### GET `/api/v1/sales/{id}`
الحصول على بيع محدد

### POST `/api/v1/sales`
إنشاء بيع جديد

### PUT `/api/v1/sales/{id}`
تحديث بيع

### DELETE `/api/v1/sales/{id}`
حذف بيع

### POST `/api/v1/sales/invoice`
إنشاء فاتورة

---

## Inventory Endpoints

### GET `/api/v1/inventory`
الحصول على معلومات المخزون

### GET `/api/v1/inventory/alerts`
الحصول على تنبيهات المخزون

### POST `/api/v1/inventory/adjust`
تعديل المخزون

---

## Dashboard Endpoints

### GET `/api/v1/dashboard/stats`
الحصول على إحصائيات Dashboard

### GET `/api/v1/dashboard/sales`
الحصول على إحصائيات المبيعات

---

## Suppliers Endpoints

### GET `/api/v1/suppliers`
الحصول على قائمة الموردين

### GET `/api/v1/suppliers/{id}`
الحصول على مورد محدد

### POST `/api/v1/suppliers`
إنشاء مورد جديد

### PUT `/api/v1/suppliers/{id}`
تحديث مورد

### DELETE `/api/v1/suppliers/{id}`
حذف مورد

---

## Warehouses Endpoints

### GET `/api/v1/warehouses`
الحصول على قائمة المستودعات

### GET `/api/v1/warehouses/{id}`
الحصول على مستودع محدد

### POST `/api/v1/warehouses`
إنشاء مستودع جديد

### PUT `/api/v1/warehouses/{id}`
تحديث مستودع

### DELETE `/api/v1/warehouses/{id}`
حذف مستودع

---

## Users Endpoints

### GET `/api/v1/users`
الحصول على قائمة المستخدمين

### GET `/api/v1/users/{id}`
الحصول على مستخدم محدد

### POST `/api/v1/users`
إنشاء مستخدم جديد

### PUT `/api/v1/users/{id}`
تحديث مستخدم

### DELETE `/api/v1/users/{id}`
حذف مستخدم

---

## Error Responses

جميع الأخطاء تعيد نفس التنسيق:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "status_code": 400
}
```

### Error Codes:
- `VALIDATION_ERROR`: خطأ في التحقق من البيانات
- `NOT_FOUND`: المورد غير موجود
- `UNAUTHORIZED`: غير مصرح
- `FORBIDDEN`: محظور
- `INTERNAL_ERROR`: خطأ داخلي

---

## Authentication

جميع الطلبات (عدا `/auth/login` و `/health`) تتطلب JWT token في Header:

```
Authorization: Bearer <access_token>
```

---

## API Versioning

النسخة الحالية: `v1`

يتم تحديد النسخة في path: `/api/v1/...`

---

**آخر تحديث:** 2025-01-16


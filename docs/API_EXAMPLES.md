# API Examples - أمثلة API

دليل شامل بأمثلة استخدام API للتكامل مع النظام.

---

## جدول المحتويات

1. [Authentication](#authentication)
2. [Products API](#products-api)
3. [Sales API](#sales-api)
4. [Purchases API](#purchases-api)
5. [Customers API](#customers-api)
6. [Error Handling](#error-handling)

---

## Authentication

### تسجيل الدخول

**Request:**
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "Admin User",
    "role": "admin"
  }
}
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "password123"}
)

if response.status_code == 200:
    data = response.json()
    token = data["access_token"]
    print(f"✅ Login successful! Token: {token}")
else:
    print(f"❌ Login failed: {response.text}")
```

**JavaScript/TypeScript Example:**
```typescript
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'password123'
  })
});

if (response.ok) {
  const data = await response.json();
  const token = data.access_token;
  localStorage.setItem('access_token', token);
  console.log('✅ Login successful!');
} else {
  console.error('❌ Login failed:', await response.text());
}
```

### تحديث Token (Refresh)

**Request:**
```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Products API

### الحصول على قائمة المنتجات

**Request:**
```bash
GET /api/v1/products/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "منتج تجريبي",
      "barcode": "1234567890",
      "cost_price": 50.00,
      "selling_price": 100.00,
      "current_stock": 150,
      "category_id": 1,
      "category_name": "إلكترونيات"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

**Python Example:**
```python
import requests

token = "your_access_token"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://localhost:8000/api/v1/products/",
    headers=headers,
    params={"page": 1, "page_size": 10}
)

if response.status_code == 200:
    data = response.json()
    products = data["items"]
    for product in products:
        print(f"Product: {product['name']} - Price: {product['selling_price']}")
```

**JavaScript/TypeScript Example:**
```typescript
const token = localStorage.getItem('access_token');
const response = await fetch('http://localhost:8000/api/v1/products/?page=1&page_size=10', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

if (response.ok) {
  const data = await response.json();
  const products = data.items;
  products.forEach(product => {
    console.log(`Product: ${product.name} - Price: ${product.selling_price}`);
  });
}
```

### إنشاء منتج جديد

**Request:**
```bash
POST /api/v1/products/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "منتج جديد",
  "barcode": "9876543210",
  "cost_price": 75.00,
  "selling_price": 150.00,
  "current_stock": 100,
  "category_id": 1,
  "unit": "قطعة"
}
```

**Response:**
```json
{
  "success": true,
  "product_id": 2,
  "message": "تم إنشاء المنتج بنجاح"
}
```

**Python Example:**
```python
import requests

token = "your_access_token"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

product_data = {
    "name": "منتج جديد",
    "barcode": "9876543210",
    "cost_price": 75.00,
    "selling_price": 150.00,
    "current_stock": 100,
    "category_id": 1
}

response = requests.post(
    "http://localhost:8000/api/v1/products/",
    headers=headers,
    json=product_data
)

if response.status_code == 201:
    data = response.json()
    print(f"✅ Product created! ID: {data['product_id']}")
else:
    print(f"❌ Failed: {response.text}")
```

### تحديث منتج

**Request:**
```bash
PUT /api/v1/products/{product_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "منتج محدث",
  "selling_price": 160.00
}
```

**Response:**
```json
{
  "success": true,
  "message": "تم تحديث المنتج بنجاح"
}
```

### حذف منتج

**Request:**
```bash
DELETE /api/v1/products/{product_id}
Authorization: Bearer {token}
```

**Response:**
```
204 No Content
```

---

## Sales API

### إنشاء فاتورة بيع

**Request:**
```bash
POST /api/v1/sales/
Authorization: Bearer {token}
Content-Type: application/json

{
  "customer_id": 1,
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 100.00,
      "discount_amount": 0.00
    }
  ],
  "payment_method": "cash",
  "status": "confirmed"
}
```

**Response:**
```json
{
  "success": true,
  "sale_id": 1,
  "invoice_number": "INV-2025-0001",
  "total_amount": 200.00,
  "message": "تم إنشاء الفاتورة بنجاح"
}
```

**Python Example:**
```python
import requests

token = "your_access_token"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

sale_data = {
    "customer_id": 1,
    "items": [
        {
            "product_id": 1,
            "quantity": 2,
            "unit_price": 100.00
        }
    ],
    "payment_method": "cash",
    "status": "confirmed"
}

response = requests.post(
    "http://localhost:8000/api/v1/sales/",
    headers=headers,
    json=sale_data
)

if response.status_code == 201:
    data = response.json()
    print(f"✅ Sale created! Invoice: {data['invoice_number']}, Total: {data['total_amount']}")
```

### الحصول على قائمة المبيعات

**Request:**
```bash
GET /api/v1/sales/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "invoice_number": "INV-2025-0001",
      "customer_id": 1,
      "customer_name": "عميل تجريبي",
      "total_amount": 200.00,
      "status": "confirmed",
      "sale_date": "2025-01-15T10:30:00"
    }
  ],
  "total": 1
}
```

---

## Purchases API

### إنشاء فاتورة شراء

**Request:**
```bash
POST /api/v1/purchases/
Authorization: Bearer {token}
Content-Type: application/json

{
  "supplier_id": 1,
  "items": [
    {
      "product_id": 1,
      "quantity": 10,
      "unit_price": 50.00
    }
  ],
  "payment_status": "pending",
  "status": "confirmed"
}
```

**Response:**
```json
{
  "success": true,
  "purchase_id": 1,
  "invoice_number": "PUR-2025-0001",
  "total_amount": 500.00,
  "message": "تم إنشاء فاتورة الشراء بنجاح"
}
```

---

## Customers API

### إنشاء عميل جديد

**Request:**
```bash
POST /api/v1/customers/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "عميل جديد",
  "phone": "0501234567",
  "email": "customer@example.com",
  "address": "الرياض، السعودية"
}
```

**Response:**
```json
{
  "success": true,
  "customer_id": 1,
  "message": "تم إنشاء العميل بنجاح"
}
```

### الحصول على قائمة العملاء

**Request:**
```bash
GET /api/v1/customers/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "عميل جديد",
      "phone": "0501234567",
      "email": "customer@example.com",
      "total_purchases": 1500.00
    }
  ],
  "total": 1
}
```

---

## Error Handling

### مثال على معالجة الأخطاء

**Python Example:**
```python
import requests

def make_api_request(url, method="GET", headers=None, json_data=None):
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json_data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        # التحقق من حالة الاستجابة
        if response.status_code == 401:
            print("❌ Unauthorized: Please login again")
            return None
        elif response.status_code == 403:
            print("❌ Forbidden: You don't have permission")
            return None
        elif response.status_code == 404:
            print("❌ Not Found: Resource doesn't exist")
            return None
        elif response.status_code >= 400:
            error_data = response.json()
            print(f"❌ Error {response.status_code}: {error_data.get('detail', 'Unknown error')}")
            return None
        
        return response.json()
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot connect to API server")
        return None
    except requests.exceptions.Timeout:
        print("❌ Timeout: Request took too long")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

# استخدام
token = "your_token"
headers = {"Authorization": f"Bearer {token}"}
result = make_api_request("http://localhost:8000/api/v1/products/", headers=headers)
```

**JavaScript/TypeScript Example:**
```typescript
async function makeApiRequest(url: string, options: RequestInit = {}) {
  try {
    const response = await fetch(url, options);
    
    if (response.status === 401) {
      console.error('❌ Unauthorized: Please login again');
      // Redirect to login
      window.location.href = '/login';
      return null;
    }
    
    if (response.status === 403) {
      console.error('❌ Forbidden: You don\'t have permission');
      return null;
    }
    
    if (response.status === 404) {
      console.error('❌ Not Found: Resource doesn\'t exist');
      return null;
    }
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error(`❌ Error ${response.status}:`, errorData.detail || 'Unknown error');
      return null;
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof TypeError) {
      console.error('❌ Network Error: Cannot connect to API server');
    } else {
      console.error('❌ Unexpected error:', error);
    }
    return null;
  }
}

// استخدام
const token = localStorage.getItem('access_token');
const result = await makeApiRequest('http://localhost:8000/api/v1/products/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

---

## Rate Limiting

API يدعم Rate Limiting. عند تجاوز الحد المسموح:

**Response:**
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

**معالجة Rate Limiting:**
```python
import time

def handle_rate_limit(response):
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        print(f"⏳ Rate limit exceeded. Retry after {retry_after} seconds")
        time.sleep(retry_after)
        return True
    return False
```

---

## Health Check

### فحص صحة API

**Request:**
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "api_version": "v1"
}
```

---

## OpenAPI Documentation

للعرض التفاعلي لـ API Documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## ملاحظات مهمة

1. **Authentication**: جميع endpoints (ما عدا `/health` و `/auth/login`) تحتاج token في header
2. **Content-Type**: جميع POST/PUT requests يجب أن يكون Content-Type: `application/json`
3. **Pagination**: معظم endpoints تدعم `page` و `page_size` parameters
4. **Error Responses**: جميع الأخطاء تُرجع JSON مع `detail` field
5. **Multi-Company**: جميع requests تُفلتر تلقائياً حسب company_id من token

---

## روابط مفيدة

- [API Documentation](../src/api/README.md)
- [Main API Routes](../src/api/routes.py)
- [Authentication Guide](../src/api/auth.py)


# دليل API

## نظرة عامة

هذا الدليل يشرح كيفية استخدام API في تطبيق الويب.

## المصادقة

جميع طلبات API (عدا `/api/v1/auth/login`) تتطلب JWT token في header:

```
Authorization: Bearer <token>
```

## Endpoints الرئيسية

### المبيعات
- `GET /api/v1/sales` - جلب قائمة الفواتير
- `POST /api/v1/sales` - إنشاء فاتورة جديدة
- `GET /api/v1/sales/:id` - جلب تفاصيل فاتورة
- `PUT /api/v1/sales/:id` - تحديث فاتورة
- `DELETE /api/v1/sales/:id` - حذف فاتورة

### المنتجات
- `GET /api/v1/products` - جلب قائمة المنتجات
- `POST /api/v1/products` - إنشاء منتج جديد
- `GET /api/v1/products/:id` - جلب تفاصيل منتج
- `PUT /api/v1/products/:id` - تحديث منتج
- `DELETE /api/v1/products/:id` - حذف منتج

### المشتريات
- `GET /api/v1/purchases` - جلب قائمة المشتريات
- `POST /api/v1/purchases` - إنشاء فاتورة مشتريات
- `GET /api/v1/purchases/:id` - جلب تفاصيل مشتريات

### المرتجعات
- `GET /api/v1/returns` - جلب قائمة المرتجعات
- `POST /api/v1/returns` - إنشاء مرتجع جديد

## استخدام API Client

```typescript
import { apiClient } from '@/lib/api/client'
import { API_CONFIG } from '@/lib/config/api'

// GET request
const products = await apiClient.get(API_CONFIG.ENDPOINTS.PRODUCTS)

// POST request
const newProduct = await apiClient.post(API_CONFIG.ENDPOINTS.PRODUCTS, {
  name: 'منتج جديد',
  price: 100,
  stock: 50
})

// PUT request
await apiClient.put(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`, {
  price: 120
})

// DELETE request
await apiClient.delete(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`)
```

## معالجة الأخطاء

```typescript
try {
  const data = await apiClient.get('/api/v1/products')
} catch (error: any) {
  console.error('Error:', error.message)
  toast.error(error.message || 'حدث خطأ')
}
```


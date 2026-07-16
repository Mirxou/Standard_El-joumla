#!/usr/bin/env bash
# Migration Guide لـ Web Application

# ==========================================
# دليل الترقية إلى الهيكلة الجديدة
# ==========================================

## الخطوات التالية المطلوبة:

### 1️⃣ تحديث المكونات الموجودة (components)
# استبدال جميع استدعاءات fetchFromAPI و supabase.from() بـ apiClient
# مثال:
# OLD: const { data } = await supabase.from('products').select('*')
# NEW: const data = await apiClient.get('/api/v1/products')

### 2️⃣ إضافة Types إلى جميع المكونات
# استخدام الأنواع من @/lib/types بدلاً من any

### 3️⃣ تحديث الـ useEffect dependencies
# التأكد من أن جميع useEffect تحتوي على dependencies صحيحة
# مثال:
# useEffect(() => {
#   loadData()
# }, [currentCompanyId]) // إضافة dependency

### 4️⃣ التوصيات الفورية:

## أ) استخدام useAPI Hook الجديد
```tsx
import { useAPI } from '@/lib/hooks/useAPI'

function MyComponent() {
  const { data, loading, error, refetch } = useAPI('/api/v1/products')
  
  return (
    // استخدام البيانات
  )
}
```

## ب) استخدام useAPIMutation للـ POST/PUT/DELETE
```tsx
import { useAPIMutation } from '@/lib/hooks/useAPI'

function CreateProduct() {
  const { mutate, loading } = useAPIMutation('/api/v1/products')
  
  const handleSubmit = async (data) => {
    await mutate(data, 'POST')
  }
}
```

## ج) استخدام apiClient مباشرة عند الحاجة
```tsx
import { apiClient } from '@/lib/api/client'

const response = await apiClient.post('/api/v1/products', {
  name: 'Product Name',
  price: 100
})
```

### 5️⃣ معالجة التوكن Refresh تلقائياً
# apiClient يتعامل مع 401 وتحديث التوكن تلقائياً
# لا تحتاج لفعل شيء - يعمل بشكل خلفي

### 6️⃣ اختبار التطبيق
```bash
cd web
npm install  # تثبيت الـ dependencies
npm run dev  # تشغيل التطبيق
```

### 7️⃣ قائمة الملفات الجديدة المهمة:
- lib/config/api.ts          ← إعدادات API مركزية
- lib/types/index.ts         ← جميع الأنواع TypeScript
- lib/api/client.ts          ← عميل API الموحد
- lib/hooks/useAPI.ts        ← React Hooks للـ API
- lib/utils/helpers.ts       ← دوال مساعدة

### 8️⃣ الملفات التي تحتاج تحديث:

#### Priority 1 (حرجة):
- components/dashboard.tsx       (✓ تم تصحيح duplicate cases)
- components/inventory-management.tsx
- components/products-management.tsx
- components/sales-management.tsx

#### Priority 2 (مهمة):
- components/dashboard-home.tsx
- components/create-invoice.tsx
- components/auth-guard.tsx

#### Priority 3 (إضافية):
- جميع المكونات الأخرى

### 9️⃣ اختبار Quick:

```tsx
// في أي مكون:
import { useAPI } from '@/lib/hooks/useAPI'
import type { Product } from '@/lib/types'

export default function Test() {
  const { data: products, loading, error } = useAPI<Product[]>('/api/v1/products')
  
  if (loading) return <div>جاري التحميل...</div>
  if (error) return <div>خطأ: {error.message}</div>
  
  return (
    <ul>
      {products?.map(p => <li key={p.id}>{p.name}</li>)}
    </ul>
  )
}
```

## 🎯 ملخص الفوائد:

✅ توحيد جميع استدعاءات API
✅ معالجة متقدمة للأخطاء
✅ Token refresh تلقائي
✅ Retry logic ذكية
✅ Type safety كامل
✅ أداء محسّن
✅ حماية أفضل للبيانات
✅ سهولة الصيانة والتطوير

## 🔧 نقاط مهمة:

⚠️ لا تستخدم window.location.reload()
⚠️ استخدم proper error handling
⚠️ أضف loading states
⚠️ استخدم types بدلاً من any
⚠️ تجنب infinite loops في useEffect

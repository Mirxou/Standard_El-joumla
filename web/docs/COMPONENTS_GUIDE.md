# دليل المكونات

## نظرة عامة

هذا الدليل يشرح المكونات الرئيسية في التطبيق.

## المكونات الرئيسية

### ProductsManagement
مكون إدارة المنتجات مع:
- عرض قائمة المنتجات
- البحث والفلترة
- Bulk operations
- Sorting

### SalesManagement
مكون إدارة المبيعات مع:
- عرض الفواتير
- إنشاء فواتير جديدة
- طباعة وتحميل PDF
- Quick actions

### DashboardHome
لوحة المعلومات الرئيسية مع:
- إحصائيات مباشرة
- Charts تفاعلية
- Customizable widgets
- Real-time updates

### NotificationCenter
مركز الإشعارات مع:
- عرض جميع الإشعارات
- فلترة حسب النوع
- Mark as read
- Real-time updates

## استخدام المكونات

```tsx
import ProductsManagement from '@/components/products-management'
import SalesManagement from '@/components/sales-management'

export default function Page() {
  return (
    <div>
      <ProductsManagement />
      <SalesManagement />
    </div>
  )
}
```

## Props المشتركة

معظم المكونات تدعم:
- `onSaved` - callback عند الحفظ
- `onCancel` - callback عند الإلغاء
- `initialData` - البيانات الأولية

## State Management

المكونات تستخدم React hooks:
- `useState` للـ local state
- `useEffect` للـ side effects
- Context API للـ global state


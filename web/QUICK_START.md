# دليل البدء السريع - Quick Start Guide

## 🚀 البدء السريع

### 1. التثبيت
```bash
cd web
npm install
```

### 2. إعداد Environment Variables
```bash
# إنشاء ملف .env.local
cp .env.example .env.local

# تعديل القيم حسب الحاجة
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. تشغيل Development Server
```bash
npm run dev
```

افتح [http://localhost:3000](http://localhost:3000) في المتصفح.

---

## 🧪 الاختبار

### تشغيل الاختبارات
```bash
npm test                # جميع الاختبارات
npm run test:watch      # وضع المراقبة
npm run test:coverage   # تقرير التغطية
```

---

## 📦 Build للإنتاج

```bash
npm run build           # بناء التطبيق
npm run start           # تشغيل نسخة الإنتاج
```

---

## 🔍 التحقق من الجودة

```bash
npm run lint            # فحص الكود
npm run build -- --analyze  # تحليل bundle size
```

---

## 📚 التوثيق

- [API Guide](./docs/API_GUIDE.md)
- [Components Guide](./docs/COMPONENTS_GUIDE.md)
- [Developer Guide](./docs/DEVELOPER_GUIDE.md)
- [Next Steps](./NEXT_STEPS.md)

---

## ⚡ الميزات الرئيسية

- ✅ إدارة المنتجات (Products Management)
- ✅ إدارة المبيعات (Sales Management)
- ✅ إدارة المشتريات (Purchases Management)
- ✅ إدارة المرتجعات (Returns Management)
- ✅ Dashboard تفاعلي
- ✅ نظام الإشعارات
- ✅ AI Features
- ✅ Reports & Analytics
- ✅ طباعة PDF
- ✅ Export (PDF/Excel/CSV)

---

## 🐛 حل المشاكل الشائعة

### مشكلة: API connection failed
**الحل:** تأكد من تشغيل Backend API على `http://localhost:8000`

### مشكلة: Build errors
**الحل:** 
```bash
rm -rf .next node_modules
npm install
npm run build
```

### مشكلة: Tests failing
**الحل:**
```bash
npm run test -- --clearCache
npm test
```

---

## 📞 المساعدة

راجع [Next Steps](./NEXT_STEPS.md) للخطوات التفصيلية.

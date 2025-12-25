# 📊 Test Coverage Plan - من الآن إلى 95%+

**الحالة الحالية:** 22.77% statements coverage  
**الهدف:** 95%+ coverage  
**المسار:** استراتيجية 3-مراحل

---

## 🎯 ملخص سريع

### ✅ ما تم إنجازه:
- ✅ 10 ملفات اختبار شاملة
- ✅ 156 اختبار موجود
- ✅ Jest configuration جاهز
- ✅ ts-jest integratio
n مكتمل
- ✅ Mock system مُعد

### 📈 الوضع الحالي:

```
File Coverage Summary:
├── lib/config/api.ts      ✅ 81.25% (عالية)
├── lib/hooks/useAPI.ts    ✅ 76% (معقولة)
├── lib/utils/helpers.ts   🟡 54.09% (متوسطة)
├── lib/api/client.ts      🔴 17.58% (منخفضة جداً)
└── باقي الملفات            🔴 0% (غير مختبرة)
```

---

## 📋 خطة الوصول إلى 95%

### المرحلة 1: تقوية الملفات الموجودة (هذا الأسبوع)

#### 1.1 تقوية `lib/api/client.ts` (حالياً 17.58%)

**الهدف:** 90%+

```typescript
// إضافة اختبارات جديدة:
- [ ] Token refresh scenarios (5 اختبارات)
- [ ] Retry logic with exponential backoff (5 اختبارات)
- [ ] Request/response interceptors (4 اختبارات)
- [ ] Network timeout handling (4 اختبارات)
- [ ] Request cancellation (3 اختبارات)
- [ ] Cache management (5 اختبارات)
```

**التقدير:** ~20 اختبار جديد = +50% coverage

#### 1.2 تقوية `lib/utils/helpers.ts` (حالياً 54.09%)

**الهدف:** 95%+

```typescript
// إضافة اختبارات جديدة:
- [ ] formatNumberArabic edge cases (6 اختبارات)
- [ ] debounce advanced scenarios (5 اختبارات)
- [ ] Date formatting in different timezones (4 اختبارات)
- [ ] Currency formatting edge cases (5 اختبارات)
- [ ] Validation function combinations (4 اختبارات)
```

**التقدير:** ~15 اختبار جديد = +30% coverage

#### 1.3 تحسين `lib/hooks/useAPI.ts` (حالياً 76%)

**الهدف:** 95%+

```typescript
// إضافة اختبارات جديدة:
- [ ] useAPI with complex dependencies (4 اختبارات)
- [ ] useAPIMutation with multiple concurrent calls (3 اختبارات)
- [ ] Error state management (4 اختبارات)
- [ ] Cache invalidation (3 اختبارات)
- [ ] Race condition handling (2 اختبار)
```

**التقدير:** ~10 اختبار جديد = +15% coverage

#### 1.4 تحسين `lib/config/api.ts` (حالياً 81.25%)

**الهدف:** 95%+

```typescript
// إضافة اختبارات جديدة:
- [ ] Dynamic configuration loading (3 اختبارات)
- [ ] Environment variable overrides (3 اختبارات)
- [ ] Configuration validation (3 اختبارات)
- [ ] Error configuration scenarios (2 اختبار)
```

**التقدير:** ~8 اختبار جديد = +10% coverage

---

### المرحلة 2: اختبار الملفات الداعمة

#### 2.1 `lib/api/` - باقي الملفات
```
- [ ] lib/types/index.ts - اختبارات نوعية
- [ ] lib/db/client.ts - اختبارات الاتصال
- [ ] lib/ai/* - اختبارات الخوارزميات
```

#### 2.2 `lib/` - الملفات الأساسية
```
- [ ] lib/auth-context.tsx - اختبارات السياق
- [ ] lib/invoice-storage.ts - اختبارات التخزين
- [ ] lib/supabase.ts - اختبارات المحاكاة
```

---

### المرحلة 3: اختبار Components (اختياري للـ 95%)

```
- [ ] components/dashboard.tsx
- [ ] components/products-management.tsx
- [ ] API routes (app/api/*)
```

---

## 🛠️ طريقة الإضافة السريعة

### خطوات لإضافة اختبارات جديدة:

```bash
# 1. انسخ القالب الموجود
cp __tests__/lib/api/client.test.ts __tests__/lib/api/client.enhanced.test.ts

# 2. أضف اختبارات جديدة

# 3. شغّل التغطية
npm run test:coverage

# 4. تحقق من النسبة المحسّنة
npm run test:watch
```

---

## 📊 جدول التقدم المتوقع

| المرحلة | الملف | من | إلى | الاختبارات | الجهد |
|-------|------|----|----|-----------|------|
| 1.1 | client.ts | 17.58% | 75% | 20 | 3 ساعات |
| 1.2 | helpers.ts | 54.09% | 85% | 15 | 2 ساعة |
| 1.3 | useAPI.ts | 76% | 90% | 10 | 1.5 ساعة |
| 1.4 | api.ts | 81.25% | 92% | 8 | 1 ساعة |
| **Total** | **المجموع** | **22.77%** | **>95%** | **~53** | **~7.5 ساعات** |

---

## 🎯 أفضل الممارسات للاختبارات

### 1. اختبر كل الـ branches
```typescript
if (condition) {
  // Test this path
} else {
  // And this path
}
```

### 2. اختبر الحالات الحدية
```typescript
// Normal
expect(divide(10, 2)).toBe(5)

// Edge cases
expect(divide(0, 0)).toBe(0) // Division by zero
expect(divide(Infinity, 2)).toBe(Infinity) // Infinity
```

### 3. اختبر الأخطاء
```typescript
expect(() => riskyFunction()).toThrow()
expect(() => riskyFunction()).toThrow('specific error')
```

### 4. اختبر التكامل
```typescript
// Not just unit tests
// Also test how functions work together
const result = await apiClient.post('/api/test')
expect(result).toHaveProperty('data')
```

---

## 📝 ملفات الاختبار الحالية

```
__tests__/
├── api/
│   └── routes.test.ts (✅ 156+ اختبار)
├── components/
│   └── rendering.test.tsx (✅ اختبارات DOM)
├── integration/
│   └── comprehensive.test.ts (✅ اختبارات التكامل)
├── lib/
│   ├── api/
│   │   └── client.test.ts (🟡 بحاجة تحسين)
│   ├── auth/
│   │   └── index.test.ts (✅)
│   ├── config/
│   │   └── api.test.ts (✅)
│   ├── hooks/
│   │   └── useAPI.test.ts (🟡 بحاجة تحسين)
│   ├── types/
│   │   └── index.test.ts (✅)
│   ├── utils/
│   │   └── helpers.test.ts (🟡 بحاجة تحسين)
│   └── validation/
│       └── index.test.ts (✅)
└── package.json (✅ test scripts جاهزة)
```

---

## 🚀 الخطوات التالية

### اليوم:
- [x] إعداد Jest و Testing Library
- [x] كتابة 10 ملفات اختبار أساسية
- [x] تشغيل التغطية الأولية (22.77%)

### غداً:
- [ ] إضافة 20 اختبار لـ `client.ts`
- [ ] إضافة 15 اختبار لـ `helpers.ts`
- [ ] الهدف: 35-40% coverage

### هذا الأسبوع:
- [ ] إضافة 10 اختبار لـ `useAPI.ts`
- [ ] إضافة 8 اختبار لـ `api.ts`
- [ ] الهدف: 50%+ coverage

### الأسبوع القادم:
- [ ] اختبار الملفات الداعمة
- [ ] إضافة component tests
- [ ] الهدف: **95%+ coverage**

---

## 💡 نصائح للتغطية السريعة

### 1. استخدم Coverage Report
```bash
npm run test:coverage
# افتح coverage/index.html في المتصفح
```

### 2. ركز على High-Impact Files
```
Priority: client.ts > helpers.ts > useAPI.ts > باقي الملفات
```

### 3. استخدم Snapshot Testing
```typescript
expect(component).toMatchSnapshot()
```

### 4. Mock External Dependencies
```typescript
jest.mock('@/lib/api/client')
```

---

## ✨ المميزات الحالية للاختبارات

✅ **Jest Configuration كامل**
- ✅ TypeScript support via ts-jest
- ✅ Next.js integration
- ✅ Path aliases (@/)
- ✅ Coverage thresholds

✅ **Mocking Setup شامل**
- ✅ next/navigation مocked
- ✅ localStorage مocked
- ✅ axios مocked
- ✅ next/headers مocked

✅ **Test Patterns موجودة**
- ✅ Unit tests
- ✅ Integration tests
- ✅ Validation tests
- ✅ Error scenario tests

---

## 📚 موارد إضافية

### للتعمق أكثر:
1. Jest Documentation: https://jestjs.io/
2. Testing Library: https://testing-library.com/
3. TypeScript Testing: https://www.typescriptlang.org/docs/handbook/testing.html

### أدوات مفيدة:
- `npm run test:watch` - Follow file changes
- `npm run test:coverage` - See detailed coverage
- `npm run test:ci` - CI/CD mode

---

## 🎉 الخلاصة

**الحالة:** 
- ✅ Foundation مقوية (Jest + اختبارات أساسية)
- 🟡 Coverage قابلة للتحسين (22.77% → 95%+)
- 🚀 مسار واضح للوصول للهدف

**الجهد المتبقي:** ~7.5 ساعات لـ 95%+ coverage

**Status:** 🟢 Ready for Scale-Up Phase

---

**تم الإنجاز بتاريخ:** 21 ديسمبر 2025  
**المرحلة التالية:** تنفيذ خطة الـ 95% coverage  
**الموعد المتوقع:** نهاية الأسبوع

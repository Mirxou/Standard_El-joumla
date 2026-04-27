# 🔍 دليل الملفات المكررة - Duplicate Files Guide

هذا الدليل يوضح كيفية التعامل مع الملفات المكررة وغير المفيدة في المشروع.

---

## 📋 الملفات المتوفرة

1. **`DUPLICATE_FILES_REPORT.md`** - تقرير شامل بالملفات المكررة
2. **`remove-duplicate-files.ps1`** - سكريبت PowerShell لحذف الملفات المكررة

---

## 🚀 الاستخدام السريع

### 1. عرض الملفات التي سيتم حذفها (بدون حذف فعلي)

```powershell
.\remove-duplicate-files.ps1 -WhatIf
```

أو

```powershell
.\remove-duplicate-files.ps1 -DryRun
```

### 2. حذف الملفات فعلياً

```powershell
.\remove-duplicate-files.ps1
```

سيطلب منك التأكيد قبل الحذف.

---

## 📊 ما سيتم حذفه

السكريبت يحذف الملفات التالية بأمان:

### ✅ ملفات Backup (3 ملفات)
- `src/ui/dialogs/sales_dialog.py.backup`
- `web/components/inventory-management.tsx.backup`
- `web/__tests__/lib/api/client.test.ts.bak`

### ✅ ملفات قديمة في Root (4 ملفات)
- `App.tsx` (في root - قديم)
- `InventoryPage.tsx` (في root - قديم)
- `index.ts` (في root - قديم)
- `productService.ts` (في root - قديم)

### ✅ ملفات مكررة (1 ملف)
- `web/components/ui/use-toast.ts` (مكرر - المستخدم هو `web/hooks/use-toast.ts`)

### ✅ ملفات مؤقتة (3 ملفات)
- `tree-full.txt`
- `file_tree_raw.txt`
- `test_output.txt`

**إجمالي:** ~11 ملف

---

## ⚠️ تحذيرات مهمة

1. **عمل نسخة احتياطية:** تأكد من عمل نسخة احتياطية من المشروع قبل التشغيل
2. **مراجعة الملفات:** راجع قائمة الملفات قبل الحذف
3. **استخدام WhatIf:** استخدم `-WhatIf` أولاً لمعرفة ما سيتم حذفه

---

## 🔍 ملفات مكررة أخرى (تحتاج إعادة تسمية)

هناك ملفات أخرى مكررة لكنها **ملفات مختلفة** بنفس الاسم:

1. **`cache_manager.py`**
   - `src/api/cache_manager.py` (Redis Cache)
   - `src/core/cache_manager.py` (Memory Cache)

2. **`rate_limiter.py`**
   - `src/api/rate_limiter.py` (API Rate Limiter)
   - `src/security/rate_limiter.py` (Security Rate Limiter)

3. **`security_service.py`**
   - `src/core/security_service.py` (Core Security)
   - `src/services/security_service.py` (Business Security)

4. **`mfa_service.py`**
   - `src/security/mfa_service.py` (Security MFA)
   - `src/services/mfa_service.py` (Business MFA)

**ملاحظة:** هذه الملفات **مختلفة** لكن بنفس الاسم. يُنصح بإعادة تسميتها لتوضيح الفرق.

راجع `DUPLICATE_FILES_REPORT.md` للتفاصيل الكاملة.

---

## 📝 ملاحظات

- السكريبت آمن ولا يحذف ملفات مهمة
- جميع الملفات المحددة للحذف هي ملفات backup أو قديمة أو مكررة
- الملفات المكررة الأخرى تحتاج إعادة تسمية يدوية

---

**تم الإنشاء:** 2025-12-21


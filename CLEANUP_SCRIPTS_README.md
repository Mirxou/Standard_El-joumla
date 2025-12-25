# 🧹 دليل سكريبتات التنظيف - Cleanup Scripts Guide

هذا الدليل يوضح كيفية استخدام سكريبتات التنظيف التلقائي.

---

## 📋 السكريبتات المتوفرة

1. **`cleanup-python-files.ps1`** - حذف الملفات المؤقتة والقديمة
2. **`move-files-to-scripts.ps1`** - نقل ملفات Python من Root إلى scripts/
3. **`fix-database-paths.ps1`** - إصلاح مسارات قاعدة البيانات المبرمجة

---

## 🚀 الاستخدام السريع

### 1. حذف الملفات المؤقتة

```powershell
# عرض الملفات التي سيتم حذفها (بدون حذف)
.\cleanup-python-files.ps1 -WhatIf

# حذف الملفات فعلياً
.\cleanup-python-files.ps1
```

**ما سيتم حذفه:**
- `standard.db` و `test_db.db` (قواعد بيانات قديمة)
- `_gen_tree.py` و `_tree_gen.py` (سكريبتات مؤقتة)
- `DEADLOCK_FIX_SUMMARY.py` و `SOLUTION_SUMMARY.py` (ملفات توثيق)
- `package.json` و `package-lock.json` (في Root - قديمة)

---

### 2. نقل الملفات إلى scripts/

```powershell
# عرض الملفات التي سيتم نقلها (بدون نقل)
.\move-files-to-scripts.ps1 -WhatIf

# نقل الملفات فعلياً
.\move-files-to-scripts.ps1
```

**ما سيتم نقله:**
- `check_*.py` (10 ملفات) → `scripts/utilities/`
- `fix_*.py` (3 ملفات) → `scripts/utilities/`
- `setup_*.py` (3 ملفات) → `scripts/utilities/`
- `generate_dummy_data.py` → `scripts/`
- `simulate_inventory_load.py` → `scripts/`
- `run_migration.py` → `scripts/`
- `clear_cache.py` → `scripts/utilities/`
- `reset_password.py` → `scripts/utilities/`
- `test_*.py` (8 ملفات) → `tests/` (حسب النوع)

---

### 3. إصلاح مسارات قاعدة البيانات

```powershell
# عرض الملفات التي سيتم إصلاحها (بدون إصلاح)
.\fix-database-paths.ps1 -WhatIf

# إصلاح الملفات فعلياً
.\fix-database-paths.ps1
```

**ما سيتم إصلاحه:**
- `src/api/server.py` - استبدال المسار المبرمج بمسار نسبي
- `fix_email.py` - استبدال المسار المبرمج بمسار نسبي

---

## 📊 ترتيب التنفيذ الموصى به

### المرحلة 1: الحذف الآمن (أولاً)
```powershell
.\cleanup-python-files.ps1 -WhatIf  # مراجعة
.\cleanup-python-files.ps1          # تنفيذ
```

### المرحلة 2: إصلاح الاتساق (ثانياً)
```powershell
.\fix-database-paths.ps1 -WhatIf    # مراجعة
.\fix-database-paths.ps1            # تنفيذ
```

### المرحلة 3: نقل الملفات (ثالثاً)
```powershell
.\move-files-to-scripts.ps1 -WhatIf # مراجعة
.\move-files-to-scripts.ps1         # تنفيذ
```

---

## ⚠️ تحذيرات مهمة

1. **عمل نسخة احتياطية:** تأكد من عمل نسخة احتياطية قبل التشغيل
2. **استخدام WhatIf:** استخدم `-WhatIf` أولاً لمراجعة التغييرات
3. **التحقق من Git:** تأكد من أن جميع التغييرات في Git قبل التنفيذ

---

## 📝 ملاحظات

- جميع السكريبتات آمنة ولا تحذف ملفات مهمة
- السكريبتات تنشئ المجلدات المطلوبة تلقائياً
- في حالة وجود ملفات مكررة، سيتم تخطيها

---

**تم الإنشاء:** 2025-12-21


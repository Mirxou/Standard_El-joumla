# Scripts Index - دليل السكريبتات

## نظرة عامة
هذا المجلد يحتوي على جميع السكريبتات المساعدة لإدارة وصيانة التطبيق.

## 📋 قائمة السكريبتات

### 🔧 Migrations (الترحيلات)

#### `apply_migrations.py`
**الوصف**: تطبيق جميع migrations على قاعدة البيانات  
**الاستخدام**:
```bash
python scripts/apply_migrations.py [--db PATH] [--migrations PATH] [--force]
```
**الميزات**:
- نسخ احتياطي تلقائي قبل التطبيق
- تتبع الـ migrations المطبقة
- معالجة أخطاء SQL (تجاهل الأعمدة/الفهارس الموجودة)
- إحصائيات مفصلة

#### `validate_migrations.py`
**الوصف**: التحقق من صحة ملفات migrations  
**الاستخدام**:
```bash
python scripts/validate_migrations.py
```
**الميزات**:
- التحقق من عدم وجود أرقام مكررة
- التحقق من عدم وجود أرقام مفقودة
- التحقق من صحة أسماء الملفات
- التحقق من وجود PRAGMA foreign_keys
- اقتراح إعادة التسمية

---

### 📊 Monitoring (المراقبة)

#### `monitor_logs.py`
**الوصف**: مراقبة السجلات للكشف عن أخطاء جديدة  
**الاستخدام**:
```bash
# فحص واحد
python scripts/monitor_logs.py

# مراقبة مستمرة (كل 5 دقائق)
python scripts/monitor_logs.py --continuous 300
```
**الميزات**:
- فحص تلقائي لملفات السجلات الرئيسية
- كشف الأخطاء الجديدة فقط
- تقارير مفصلة
- دعم المراقبة المستمرة

#### `start_monitor_background.ps1`
**الوصف**: تشغيل مراقبة السجلات في الخلفية (PowerShell)  
**الاستخدام**:
```powershell
.\scripts\start_monitor_background.ps1 [-Interval SECONDS] [-Hidden]
```

#### `stop_monitor.ps1`
**الوصف**: إيقاف عمليات مراقبة السجلات النشطة  
**الاستخدام**:
```powershell
.\scripts\stop_monitor.ps1
```

#### `setup_scheduled_tasks.ps1`
**الوصف**: إعداد مهام مجدولة في Windows Task Scheduler  
**الاستخدام**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
```
**المهام**:
- تنظيف يومي في الساعة 2:00 صباحاً
- مراقبة مستمرة كل 5 دقائق (اختيارية)

---

### 🧹 Cleanup (التنظيف)

#### `cleanup_test_logs.py`
**الوصف**: حذف تقارير الأعطال من الاختبارات وملفات السجلات القديمة  
**الاستخدام**:
```bash
python scripts/cleanup_test_logs.py
```
**الميزات**:
- حذف تقارير الأعطال من الاختبارات
- تنظيف ملفات السجلات القديمة (أقدم من 30 يوم)
- الاحتفاظ بالملفات المهمة

---

### 🧪 Testing (الاختبارات)

#### `test_dashboard_chart.py`
**الوصف**: اختبار رسم المخططات في Dashboard  
**الاستخدام**:
```bash
python scripts/test_dashboard_chart.py
```

#### `monitor_test.py`
**الوصف**: اختبار نظام المراقبة  
**الاستخدام**:
```bash
python scripts/monitor_test.py
```

---

### 🔍 Database Utilities (أدوات قاعدة البيانات)

#### `check_wal_mode.py`
**الوصف**: التحقق من وضع WAL (Write-Ahead Logging) في SQLite  
**الاستخدام**:
```bash
python scripts/check_wal_mode.py [--db PATH]
```
**الميزات**:
- التحقق من وضع WAL
- اقتراحات لتحسين الأداء
- معلومات عن حالة قاعدة البيانات

#### `verify_safety_nets.py`
**الوصف**: التحقق من شبكات الأمان في قاعدة البيانات  
**الاستخدام**:
```bash
python scripts/verify_safety_nets.py
```
**الميزات**:
- التحقق من القيود (Constraints)
- التحقق من الفهارس
- التحقق من Foreign Keys
- تقرير شامل عن حالة قاعدة البيانات

---

### ⚡ Performance (الأداء)

#### `benchmark_app.py`
**الوصف**: قياس أداء التطبيق  
**الاستخدام**:
```bash
python scripts/benchmark_app.py [--iterations N] [--warmup N]
```
**الميزات**:
- قياس سرعة العمليات الأساسية
- تحليل الأداء
- تقارير مفصلة
- مقارنة النتائج

---

## 📁 المجلدات الفرعية

### `utilities/`
يحتوي على أدوات مساعدة إضافية (إن وجدت)

---

## 📚 التوثيق

- `README.md` - دليل شامل لجميع السكريبتات
- `MONITORING_README.md` - دليل خاص بنظام المراقبة
- `INDEX.md` - هذا الملف (دليل سريع)

---

## 🔄 التحديثات الأخيرة

### Migrations
- ✅ إصلاح الأرقام المكررة
- ✅ إضافة PRAGMA foreign_keys لجميع الملفات
- ✅ تحسين معالجة الأخطاء

### Monitoring
- ✅ إضافة مراقبة مستمرة
- ✅ سكريبتات PowerShell للخلفية
- ✅ جدولة تلقائية

### Cleanup
- ✅ تنظيف تلقائي لملفات الاختبارات
- ✅ تنظيف ملفات السجلات القديمة

---

## 💡 نصائح الاستخدام

1. **قبل تطبيق migrations**: استخدم `validate_migrations.py` للتحقق من الصحة
2. **للمراقبة المستمرة**: استخدم `setup_scheduled_tasks.ps1` لإعداد الجدولة
3. **للاستكشاف**: استخدم `verify_safety_nets.py` للتحقق من سلامة قاعدة البيانات
4. **للأداء**: استخدم `benchmark_app.py` لقياس الأداء قبل وبعد التحديثات

---

## ⚠️ ملاحظات مهمة

- جميع سكريبتات PowerShell تتطلب صلاحيات المسؤول لتسجيل المهام
- تأكد من وجود نسخة احتياطية قبل تطبيق migrations
- استخدم `--force` بحذر في `apply_migrations.py`


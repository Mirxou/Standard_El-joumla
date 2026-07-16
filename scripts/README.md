# سكريبتات الصيانة والمراقبة
# Maintenance and Monitoring Scripts

## نظرة عامة
هذه المجموعة من السكريبتات تساعد في صيانة ومراقبة التطبيق.

## السكريبتات المتاحة

### 1. `cleanup_test_logs.py` - تنظيف السجلات القديمة

**الوصف**: حذف تقارير الأعطال من الاختبارات وملفات السجلات القديمة.

**الاستخدام**:
```bash
# تنظيف تلقائي (حذف ملفات الاختبارات + الملفات القديمة)
python scripts/cleanup_test_logs.py

# تنظيف ملفات الاختبارات فقط (بغض النظر عن التاريخ)
python -c "from scripts.cleanup_test_logs import clean_test_crash_reports; clean_test_crash_reports(force_delete_tests=True)"
```

**الميزات**:
- حذف تقارير الأعطال من الاختبارات تلقائياً
- تنظيف ملفات السجلات القديمة (أقدم من 30 يوم)
- الاحتفاظ بالملفات المهمة (`__main__.log`, `database_operations.log`, `exception_handler.log`)

### 2. `monitor_logs.py` - مراقبة السجلات

**الوصف**: مراقبة السجلات للكشف عن أخطاء جديدة.

**الاستخدام**:
```bash
# فحص واحد
python scripts/monitor_logs.py

# مراقبة مستمرة (كل 5 دقائق)
python scripts/monitor_logs.py --continuous 300

# مراقبة مستمرة (كل دقيقة)
python scripts/monitor_logs.py --continuous 60
```

**الميزات**:
- فحص تلقائي لملفات السجلات الرئيسية
- كشف الأخطاء الجديدة فقط (تجاهل الأخطاء المعروفة)
- تقارير مفصلة عن الأخطاء المكتشفة
- دعم المراقبة المستمرة

**أنماط الأخطاء المراقبة**:
- `FOREIGN KEY constraint failed`
- `AttributeError`
- `ValueError`
- `ImportError`
- `DatabaseError`
- `PermissionError`
- `FileNotFoundError`

### 3. `setup_scheduled_tasks.ps1` - إعداد الجدولة التلقائية

**الوصف**: إعداد مهام مجدولة في Windows Task Scheduler.

**الاستخدام**:
```powershell
# تشغيل السكريبت (يطلب صلاحيات المسؤول)
.\scripts\setup_scheduled_tasks.ps1

# أو من PowerShell كمسؤول
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup_scheduled_tasks.ps1
```

**المهام المجدولة**:
1. **LogicalRelease_CleanupLogs**: تنظيف يومي في الساعة 2:00 صباحاً
2. **LogicalRelease_MonitorLogs**: مراقبة مستمرة كل 5 دقائق (اختيارية)

**ملاحظات**:
- يتطلب صلاحيات المسؤول لتسجيل المهام
- يمكن إدارة المهام من Task Scheduler (`taskschd.msc`)

### 4. `start_monitor_background.ps1` - تشغيل المراقبة في الخلفية

**الوصف**: تشغيل مراقبة السجلات في الخلفية كعملية منفصلة.

**الاستخدام**:
```powershell
# تشغيل في الخلفية (نافذة مخفية)
.\scripts\start_monitor_background.ps1

# تشغيل في نافذة مرئية
.\scripts\start_monitor_background.ps1 -Hidden:$false

# تحديد فترة فحص مخصصة (كل دقيقة)
.\scripts\start_monitor_background.ps1 -Interval 60
```

**الميزات**:
- تشغيل في الخلفية كعملية منفصلة
- إمكانية إخفاء النافذة
- فترة فحص قابلة للتخصيص

### 5. `stop_monitor.ps1` - إيقاف المراقبة

**الوصف**: إيقاف عمليات مراقبة السجلات النشطة.

**الاستخدام**:
```powershell
.\scripts\stop_monitor.ps1
```

**الميزات**:
- البحث عن جميع عمليات المراقبة النشطة
- إيقاف آمن للعمليات
- تأكيد قبل الإيقاف

## التوصيات

### جدولة التنظيف التلقائي

#### الطريقة 1: استخدام PowerShell Script (موصى به)
```powershell
# تشغيل السكريبت
.\scripts\setup_scheduled_tasks.ps1
```

#### الطريقة 2: استخدام Task Scheduler يدوياً
1. افتح Task Scheduler (`taskschd.msc`)
2. أنشئ مهمة أساسية جديدة
3. الإجراء: `python C:\path\to\cleanup_test_logs.py`
4. المشغل: يومياً في الساعة 2:00 صباحاً

#### الطريقة 3: استخدام schtasks من سطر الأوامر
```bash
schtasks /create /tn "LogicalRelease_CleanupLogs" /tr "python C:\path\to\cleanup_test_logs.py" /sc daily /st 02:00
```

### مراقبة مستمرة

#### الطريقة 1: استخدام PowerShell Script
```powershell
# تشغيل في الخلفية
.\scripts\start_monitor_background.ps1

# إيقاف المراقبة
.\scripts\stop_monitor.ps1
```

#### الطريقة 2: استخدام Task Scheduler
```powershell
# إعداد مهمة مجدولة
.\scripts\setup_scheduled_tasks.ps1
# اختر "Y" عند السؤال عن المراقبة المستمرة
```

#### الطريقة 3: تشغيل يدوي
```bash
# في نافذة PowerShell منفصلة
python scripts/monitor_logs.py --continuous 300
```

## الاختبارات

### اختبارات DatabaseLogger الأساسية
```bash
python -m pytest tests/unit/test_database_logger_fixes.py -v
```

### اختبارات DatabaseLogger الإضافية
```bash
python -m pytest tests/unit/test_database_logger_extended.py -v
```

### جميع اختبارات DatabaseLogger
```bash
python -m pytest tests/unit/test_database_logger*.py -v
```

## ملاحظات

- السكريبتات آمنة ولا تحذف ملفات مهمة
- يتم الاحتفاظ بجميع ملفات السجلات الرئيسية
- تقارير الأعطال من الاختبارات فقط يتم حذفها
- المراقبة المستمرة تستهلك موارد قليلة جداً

## استكشاف الأخطاء

### مشكلة: "ExecutionPolicy"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### مشكلة: "Permission Denied"
- تأكد من تشغيل PowerShell كمسؤول
- أو استخدم Task Scheduler يدوياً

### مشكلة: "Python not found"
- تأكد من تثبيت Python
- أو حدد المسار يدوياً في السكريبتات

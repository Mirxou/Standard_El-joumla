# Deployment Guide - دليل النشر

## 🚀 دليل النشر الكامل

---

## 1. النسخ الاحتياطي (قبل أي شيء)

### Windows PowerShell:
```powershell
# نسخ احتياطي كامل للمشروع
Copy-Item -Path "C:\Users\pc\Desktop\ستاندرد الجملة trae" -Destination "C:\Users\pc\Desktop\ستاندرد الجملة trae_backup" -Recurse

# نسخ احتياطي لقاعدة البيانات
Copy-Item -Path "C:\Users\pc\Desktop\ستاندرد الجملة trae\data\logical_release.db" -Destination "C:\Users\pc\Desktop\ستاندرد الجملة trae\data\logical_release.db.backup"
```

### Linux/Mac:
```bash
# نسخ احتياطي كامل للمشروع
cp -r "project" "project_backup"

# نسخ احتياطي لقاعدة البيانات
cp "data/logical_release.db" "data/logical_release.db.backup"
```

---

## 2. التحقق من البيئة

### تفعيل البيئة الافتراضية:
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# Linux/Mac
source .venv/bin/activate
```

### تثبيت الاعتماديات:
```bash
pip install -r requirements.txt
```

---

## 3. الاختبارات

### اختبارات الوحدة والتكامل:
```bash
# جميع الاختبارات
pytest -q

# اختبارات محددة
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### اختبار Window Manager Smoke Test:
```bash
python test_window_manager_smoke_test.py
```

### اختبار Window Manager Integration:
```bash
python test_window_manager_integration.py
```

**النتيجة المتوقعة:** ✅ جميع الاختبارات نجحت

---

## 4. تشغيل التطبيق

### التشغيل العادي:
```bash
python main.py
```

### التشغيل مع Telemetry:
```python
# في main.py أو ملف منفصل
from src.core.telemetry_hook import WindowTelemetry, create_telemetry_hooks

# إنشاء telemetry
telemetry = WindowTelemetry()

# إنشاء hooks
hooks = create_telemetry_hooks(telemetry)

# إضافة hooks إلى WindowManager
main_window.window_manager.on_before_open.append(hooks['before_open'])
main_window.window_manager.on_after_open.append(hooks['after_open'])
main_window.window_manager.on_before_close.append(hooks['before_close'])
main_window.window_manager.on_after_close.append(hooks['after_close'])
```

---

## 5. المراقبة

### مراقبة السجلات:
```powershell
# Windows PowerShell - متابعة السجل
Get-Content .\logs\__main__.log -Wait

# Windows PowerShell - آخر 50 سطر
Get-Content .\logs\__main__.log -Tail 50
```

### مراقبة الذاكرة:
```powershell
# Windows PowerShell - مراقبة عمليات Python
Get-Process python | Select-Object Id,ProcessName,WorkingSet64

# مراقبة مستمرة
while ($true) {
    Get-Process python | Select-Object Id,ProcessName,WorkingSet64
    Start-Sleep -Seconds 5
}
```

### مراقبة Telemetry:
```python
# عرض تقرير telemetry
from src.core.telemetry_hook import WindowTelemetry

telemetry = WindowTelemetry()
print(telemetry.generate_report())

# أو قراءة ملف JSON
import json
with open('logs/window_telemetry.json', 'r') as f:
    data = json.load(f)
    print(json.dumps(data, indent=2, ensure_ascii=False))
```

---

## 6. Rollback (التراجع)

### استرجاع النسخة الاحتياطية:

#### Windows PowerShell:
```powershell
# حذف المشروع الحالي
Remove-Item -Path "C:\Users\pc\Desktop\ستاندرد الجملة trae" -Recurse -Force

# استرجاع النسخة الاحتياطية
Move-Item -Path "C:\Users\pc\Desktop\ستاندرد الجملة trae_backup" -Destination "C:\Users\pc\Desktop\ستاندرد الجملة trae"

# استرجاع قاعدة البيانات
Move-Item -Path "C:\Users\pc\Desktop\ستاندرد الجملة trae\data\logical_release.db.backup" -Destination "C:\Users\pc\Desktop\ستاندرد الجملة trae\data\logical_release.db"
```

#### Linux/Mac:
```bash
# حذف المشروع الحالي
rm -rf "project"

# استرجاع النسخة الاحتياطية
mv "project_backup" "project"

# استرجاع قاعدة البيانات
mv "project/data/logical_release.db.backup" "project/data/logical_release.db"
```

### التحقق من الاسترجاع:
```bash
python main.py
```

---

## 7. CI/CD (GitHub Actions)

### الملف: `.github/workflows/ci.yml`

يتم تشغيله تلقائياً عند:
- Push إلى `main` أو `develop`
- Pull Request إلى `main` أو `develop`

### الخطوات:
1. ✅ Checkout code
2. ✅ Set up Python
3. ✅ Install dependencies
4. ✅ Run linting
5. ✅ Run unit tests
6. ✅ Run integration tests
7. ✅ Run Window Manager smoke test
8. ✅ Run Window Manager integration test
9. ✅ Upload test results

---

## 8. نصائح الإنتاج

### 1. نسخ احتياطي مجدول:
```powershell
# Windows Task Scheduler
# إنشاء مهمة يومية لنسخ قاعدة البيانات
```

### 2. مراقبة الأداء:
- راقب `logs/__main__.log` للأخطاء
- راقب `logs/window_telemetry.json` للأداء
- راقب استخدام الذاكرة

### 3. تحديثات آمنة:
- اختبر في بيئة staging أولاً
- احتفظ بنسخة احتياطية دائماً
- راجع السجلات بعد كل تحديث

---

## 9. استكشاف الأخطاء

### إذا فشل التسجيل التلقائي:
1. تحقق من السجلات: `logs/__main__.log`
2. تحقق من أن جميع النوافذ تحتوي على `window_key`
3. تحقق من أن `init_kwargs` صحيحة

### إذا فشل فتح النافذة:
1. تحقق من أن النافذة مسجلة
2. تحقق من `init_kwargs` (خاصة `db_manager`)
3. راجع السجلات لأي أخطاء

### إذا فشل حفظ الحالة:
1. تحقق من أن النافذة تُغلق بشكل صحيح
2. تحقق من QSettings
3. تحقق من أن `tab_widgets`, `filter_widgets`, `table_widgets` مسجلة

---

## 10. Checklist النهائي

### قبل النشر:
- [ ] نسخ احتياطي كامل
- [ ] جميع الاختبارات نجحت
- [ ] لا توجد أخطاء في السجلات
- [ ] Telemetry يعمل (اختياري)

### بعد النشر:
- [ ] التطبيق يعمل بشكل صحيح
- [ ] النوافذ تفتح وتغلق بدون أخطاء
- [ ] الحالة محفوظة بشكل صحيح
- [ ] لا توجد memory leaks

---

## ✅ الخلاصة

**النظام جاهز للنشر!** 🚀

اتبع الخطوات أعلاه للتأكد من نشر آمن ومستقر.

**حظاً موفقاً!** 🎉


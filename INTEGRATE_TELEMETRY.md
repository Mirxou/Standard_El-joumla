# Integrate Telemetry - دليل دمج Telemetry

## 📊 كيفية دمج Telemetry في التطبيق

---

## 1. الطريقة البسيطة (موصى به)

### في `main_window.py`:

```python
# في __init__ بعد إنشاء window_manager
from src.core.telemetry_hook import WindowTelemetry, create_telemetry_hooks

# إنشاء telemetry
self.telemetry = WindowTelemetry()

# إنشاء hooks
telemetry_hooks = create_telemetry_hooks(self.telemetry)

# إضافة hooks إلى WindowManager
self.window_manager.on_before_open.append(telemetry_hooks['before_open'])
self.window_manager.on_after_open.append(telemetry_hooks['after_open'])
self.window_manager.on_before_close.append(telemetry_hooks['before_close'])
self.window_manager.on_after_close.append(telemetry_hooks['after_close'])
```

---

## 2. عرض التقرير

### في أي مكان في التطبيق:

```python
# عرض تقرير telemetry
from src.core.telemetry_hook import WindowTelemetry

telemetry = WindowTelemetry()
report = telemetry.generate_report()
print(report)

# أو الحصول على metrics محددة
metrics = telemetry.get_metrics("reports")
print(f"Reports window opened {metrics['open_count']} times")
print(f"Average open time: {metrics['avg_open_time_ms']:.2f}ms")
```

---

## 3. حفظ البيانات

### البيانات تُحفظ تلقائياً في:
- `logs/window_telemetry.json`

### حفظ يدوي:
```python
telemetry.save_and_reset()  # يحفظ ويُعيد تعيين الإحصائيات
```

---

## 4. قراءة البيانات

### من ملف JSON:
```python
import json
from pathlib import Path

telemetry_file = Path("logs/window_telemetry.json")
if telemetry_file.exists():
    with open(telemetry_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(json.dumps(data, indent=2, ensure_ascii=False))
```

---

## 5. مثال كامل

```python
# في main_window.py
class MainWindow(QMainWindow):
    def __init__(self, ...):
        # ... باقي الكود ...
        
        # إنشاء WindowManager
        self.window_manager = WindowManager(...)
        
        # إضافة Telemetry (اختياري)
        try:
            from src.core.telemetry_hook import WindowTelemetry, create_telemetry_hooks
            self.telemetry = WindowTelemetry()
            hooks = create_telemetry_hooks(self.telemetry)
            
            self.window_manager.on_before_open.append(hooks['before_open'])
            self.window_manager.on_after_open.append(hooks['after_open'])
            self.window_manager.on_before_close.append(hooks['before_close'])
            self.window_manager.on_after_close.append(hooks['after_close'])
            
            if self.logger:
                self.logger.info("✅ تم تفعيل Telemetry")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️  فشل تفعيل Telemetry: {e}")
```

---

## ✅ الخلاصة

**Telemetry جاهز للاستخدام!** 📊

بعد الدمج، سيتم جمع إحصائيات تلقائياً في `logs/window_telemetry.json`.


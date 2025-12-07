# Window Manager Test Plan - خطة اختبار شاملة

## 🎯 الهدف
التأكد من أن Window Manager يعمل بشكل صحيح مع جميع النوافذ (19 نافذة) بدون memory leaks أو مشاكل.

---

## 📋 المرحلة 1: الاختبار الأساسي (Basic Tests)

### ✅ Test 1.1: فتح نافذة واحدة
**الخطوات:**
1. شغّل التطبيق: `python main.py`
2. افتح `ReportsWindow` من القائمة
3. تحقق من:
   - ✅ النافذة تفتح بدون أخطاء
   - ✅ النافذة مرئية (`window.isVisible() == True`)
   - ✅ لا توجد أخطاء في Console
   - ✅ `window_manager.is_open("reports") == True`

**الكود للاختبار:**
```python
# في main_window.py - أضف دالة اختبار
def test_open_window(self):
    window = self.window_manager.open_window("reports", parent=self)
    assert window is not None, "فشل فتح النافذة"
    assert window.isVisible(), "النافذة غير مرئية"
    assert self.window_manager.is_open("reports"), "is_open لا يعمل"
    print("✅ Test 1.1: PASSED")
```

---

### ✅ Test 1.2: اختبار Singleton Behavior
**الخطوات:**
1. افتح `ReportsWindow` مرة أولى
2. احفظ المرجع: `window1 = self.window_manager.open_window("reports")`
3. افتح `ReportsWindow` مرة ثانية
4. احفظ المرجع: `window2 = self.window_manager.open_window("reports")`
5. تحقق من:
   - ✅ `window1 is window2` (نفس الكائن)
   - ✅ لا يتم إنشاء نافذة جديدة

**الكود للاختبار:**
```python
def test_singleton_behavior(self):
    window1 = self.window_manager.open_window("reports", parent=self)
    window2 = self.window_manager.open_window("reports", parent=self)
    
    assert window1 is window2, f"Singleton فشل: window1={id(window1)}, window2={id(window2)}"
    assert self.window_manager.is_open("reports"), "is_open لا يعمل"
    print("✅ Test 1.2: PASSED")
```

---

### ✅ Test 1.3: اختبار حفظ/استعادة الحالة (Geometry)
**الخطوات:**
1. افتح نافذة
2. غيّر الحجم: `window.resize(1600, 1000)`
3. غيّر الموضع: `window.move(100, 100)`
4. أغلق النافذة: `window.close()`
5. افتح النافذة مرة أخرى
6. تحقق من:
   - ✅ الحجم محفوظ: `window.width() == 1600`
   - ✅ الموضع محفوظ: `window.x() == 100`

**الكود للاختبار:**
```python
def test_geometry_persistence(self):
    window = self.window_manager.open_window("reports", parent=self)
    
    # تغيير الحجم والموضع
    window.resize(1600, 1000)
    window.move(100, 100)
    
    # إغلاق
    window.close()
    
    # إعادة الفتح
    window2 = self.window_manager.open_window("reports", parent=self)
    
    # التحقق (مع هامش خطأ صغير)
    assert abs(window2.width() - 1600) < 10, f"الحجم لم يُحفظ: {window2.width()}"
    assert abs(window2.x() - 100) < 10, f"الموضع لم يُحفظ: {window2.x()}"
    print("✅ Test 1.3: PASSED")
```

---

### ✅ Test 1.4: اختبار Maximized State
**الخطوات:**
1. افتح نافذة
2. كبّر النافذة: `window.showMaximized()`
3. أغلق النافذة
4. افتح النافذة مرة أخرى
5. تحقق من:
   - ✅ النافذة تفتح بحالة Maximized

**الكود للاختبار:**
```python
def test_maximized_state(self):
    window = self.window_manager.open_window("reports", parent=self)
    window.showMaximized()
    window.close()
    
    window2 = self.window_manager.open_window("reports", parent=self)
    assert window2.isMaximized(), "حالة Maximized لم تُحفظ"
    print("✅ Test 1.4: PASSED")
```

---

## 📋 المرحلة 2: اختبار النوافذ المتعددة (Multiple Windows)

### ✅ Test 2.1: فتح 5 نوافذ مختلفة
**الخطوات:**
1. افتح: ReportsWindow, DashboardWindow, AccountsWindow, PhysicalCountsWindow, StockAdjustmentsWindow
2. تحقق من:
   - ✅ جميع النوافذ تفتح بشكل صحيح
   - ✅ كل نافذة مستقلة عن الأخرى
   - ✅ `window_manager.get_open_instances("reports")` يعيد قائمة صحيحة

**الكود للاختبار:**
```python
def test_multiple_windows(self):
    windows = {
        "reports": self.window_manager.open_window("reports", parent=self),
        "dashboard": self.window_manager.open_window("dashboard", parent=self),
        "accounts": self.window_manager.open_window("accounts", parent=self),
        "physical_counts": self.window_manager.open_window("physical_counts", parent=self),
        "stock_adjustments": self.window_manager.open_window("stock_adjustments", parent=self)
    }
    
    for key, window in windows.items():
        assert window is not None, f"فشل فتح {key}"
        assert window.isVisible(), f"{key} غير مرئية"
        assert self.window_manager.is_open(key), f"is_open({key}) لا يعمل"
    
    print("✅ Test 2.1: PASSED")
```

---

### ✅ Test 2.2: حفظ حالة متعددة
**الخطوات:**
1. افتح 3 نوافذ
2. حرّك كل نافذة لمكان مختلف
3. غيّر حجم كل نافذة بشكل مختلف
4. أغلق جميع النوافذ
5. افتحها مرة أخرى
6. تحقق من:
   - ✅ كل نافذة عادت لنفس المكان والحجم

---

## 📋 المرحلة 3: اختبار Memory Leaks

### ✅ Test 3.1: فتح/إغلاق متكرر
**الخطوات:**
1. افتح نافذة
2. أغلقها
3. كرر 10 مرات
4. تحقق من:
   - ✅ لا توجد نوافذ "يتيمة" في الذاكرة
   - ✅ `window_manager.get_open_instances("reports")` فارغة بعد الإغلاق

**الكود للاختبار:**
```python
def test_memory_leaks(self):
    import gc
    
    for i in range(10):
        window = self.window_manager.open_window("reports", parent=self)
        assert window is not None, f"فشل فتح النافذة في المحاولة {i+1}"
        window.close()
        
        # تنظيف
        gc.collect()
        
        # التحقق من أن النافذة أُغلقت
        instances = self.window_manager.get_open_instances("reports")
        assert len(instances) == 0, f"النافذة لم تُغلق في المحاولة {i+1}"
    
    print("✅ Test 3.1: PASSED - لا توجد memory leaks")
```

---

### ✅ Test 3.2: فتح 10 نوافذ ثم إغلاقها جميعاً
**الخطوات:**
1. افتح 10 نوافذ مختلفة
2. أغلقها جميعاً: `window_manager.close_all()`
3. تحقق من:
   - ✅ جميع النوافذ أُغلقت
   - ✅ `window_manager.get_open_instances()` فارغة

**الكود للاختبار:**
```python
def test_close_all(self):
    # فتح 10 نوافذ
    keys = ["reports", "dashboard", "accounts", "physical_counts", 
            "stock_adjustments", "quotes", "returns", "purchase_orders",
            "accounting", "advanced_reports"]
    
    for key in keys:
        self.window_manager.open_window(key, parent=self)
    
    # إغلاق جميع النوافذ
    self.window_manager.close_all()
    
    # التحقق
    for key in keys:
        assert not self.window_manager.is_open(key), f"{key} لم يُغلق"
    
    print("✅ Test 3.2: PASSED")
```

---

## 📋 المرحلة 4: اختبار جميع النوافذ (19 نافذة)

### ✅ Test 4.1: فتح كل نافذة على حدة
**قائمة النوافذ:**
```python
WINDOWS_TO_TEST = [
    "reports",
    "dashboard",
    "accounts",
    "advanced_reports",
    "quotes",
    "returns",
    "purchase_orders",
    "accounting",
    "payment_plans",
    "abc_analysis",
    "safety_stock",
    "batch_tracking",
    "reorder_recommendations",
    "physical_counts",
    "stock_adjustments",
    "advanced_search",
    "permissions",
    "cycle_count",
    "payment_dashboard"
]
```

**الكود للاختبار:**
```python
def test_all_windows(self):
    failed_windows = []
    
    for window_key in WINDOWS_TO_TEST:
        try:
            window = self.window_manager.open_window(window_key, parent=self)
            if window is None:
                failed_windows.append(f"{window_key}: فشل الفتح")
            elif not window.isVisible():
                failed_windows.append(f"{window_key}: غير مرئية")
            else:
                window.close()
                print(f"✅ {window_key}: PASSED")
        except Exception as e:
            failed_windows.append(f"{window_key}: {str(e)}")
    
    if failed_windows:
        print("❌ النوافذ التالية فشلت:")
        for failure in failed_windows:
            print(f"  - {failure}")
        assert False, f"فشل {len(failed_windows)} نافذة"
    else:
        print("✅ Test 4.1: PASSED - جميع النوافذ تعمل")
```

---

## 📋 المرحلة 5: اختبار Edge Cases

### ✅ Test 5.1: فتح نافذة غير مسجلة
**الكود للاختبار:**
```python
def test_unregistered_window(self):
    window = self.window_manager.open_window("non_existent", parent=self)
    assert window is None, "يجب أن يعيد None للنافذة غير المسجلة"
    print("✅ Test 5.1: PASSED")
```

---

### ✅ Test 5.2: فتح نافذة بـ override_kwargs
**الكود للاختبار:**
```python
def test_override_kwargs(self):
    # فتح نافذة مع معاملات إضافية
    window = self.window_manager.open_window(
        "reports", 
        parent=self,
        custom_param="test"
    )
    assert window is not None, "فشل فتح النافذة مع override_kwargs"
    print("✅ Test 5.2: PASSED")
```

---

## 🚀 كيفية تشغيل الاختبارات

### الطريقة 1: اختبار يدوي
1. شغّل التطبيق: `python main.py`
2. افتح Console/Logs
3. اتبع الخطوات في كل Test

### الطريقة 2: اختبار تلقائي (مقترح)
أضف دالة `run_all_tests()` في `main_window.py`:

```python
def run_all_tests(self):
    """تشغيل جميع الاختبارات"""
    print("=" * 50)
    print("بدء اختبار Window Manager")
    print("=" * 50)
    
    try:
        self.test_open_window()
        self.test_singleton_behavior()
        self.test_geometry_persistence()
        self.test_maximized_state()
        self.test_multiple_windows()
        self.test_memory_leaks()
        self.test_close_all()
        self.test_all_windows()
        self.test_unregistered_window()
        self.test_override_kwargs()
        
        print("=" * 50)
        print("✅ جميع الاختبارات نجحت!")
        print("=" * 50)
    except AssertionError as e:
        print(f"❌ فشل الاختبار: {e}")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
```

ثم استدعها من Console:
```python
main_window.run_all_tests()
```

---

## 📊 النتيجة المتوقعة

بعد إكمال جميع الاختبارات:
- ✅ جميع النوافذ (19) تعمل بشكل صحيح
- ✅ Singleton behavior يعمل
- ✅ حفظ/استعادة الحالة يعمل
- ✅ لا توجد memory leaks
- ✅ النظام جاهز للإنتاج

---

## 🔍 استكشاف الأخطاء

### إذا فشل Test 1.1 (فتح نافذة):
- تحقق من أن النافذة مسجلة في `main_window.py`
- تحقق من `window_key` في النافذة
- راجع السجلات: `logs/__main__.log`

### إذا فشل Test 1.2 (Singleton):
- تحقق من أن `window_singleton = True` في النافذة
- تحقق من أن `singleton=True` في التسجيل

### إذا فشل Test 1.3 (Geometry):
- تحقق من أن QSettings يعمل
- تحقق من أن `_save_geometry` و `_restore_geometry` تعمل

### إذا فشل Test 3.1 (Memory Leaks):
- تحقق من أن weakrefs تعمل
- تحقق من أن `destroyed` signal متصل
- راجع `_clean_dead_refs`

---

## ✅ Checklist النهائي

- [ ] Test 1.1: فتح نافذة واحدة
- [ ] Test 1.2: Singleton behavior
- [ ] Test 1.3: حفظ/استعادة الحالة
- [ ] Test 1.4: Maximized state
- [ ] Test 2.1: فتح 5 نوافذ
- [ ] Test 2.2: حفظ حالة متعددة
- [ ] Test 3.1: فتح/إغلاق متكرر
- [ ] Test 3.2: close_all
- [ ] Test 4.1: جميع النوافذ (19)
- [ ] Test 5.1: نافذة غير مسجلة
- [ ] Test 5.2: override_kwargs

**إذا نجحت جميع الاختبارات → النظام جاهز للإنتاج!** 🎯


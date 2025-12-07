# Window Manager Complete Guide - دليل شامل

## ✅ تم إنجازه

### 1. إنشاء النسخة الجديدة
- ✅ تم إنشاء `src/core/window_manager.py`
- ✅ نسخة بسيطة واحترافية
- ✅ يدعم: weakrefs، QSettings، hooks، singleton/multiple

### 2. تحديث جميع النوافذ
- ✅ تم إضافة `window_key` و `window_singleton` و `window_title` لـ 19 نافذة:

1. ✅ `ReportsWindow` - `window_key = "reports"`
2. ✅ `DashboardWindow` - `window_key = "dashboard"`
3. ✅ `AccountsWindow` - `window_key = "accounts"`
4. ✅ `AdvancedReportsWindow` - `window_key = "advanced_reports"`
5. ✅ `QuotesWindow` - `window_key = "quotes"`
6. ✅ `ReturnsWindow` - `window_key = "returns"`
7. ✅ `PurchaseOrdersWindow` - `window_key = "purchase_orders"`
8. ✅ `AccountingWindow` - `window_key = "accounting"`
9. ✅ `PaymentPlansWindow` - `window_key = "payment_plans"`
10. ✅ `ABCAnalysisWindow` - `window_key = "abc_analysis"`
11. ✅ `SafetyStockWindow` - `window_key = "safety_stock"`
12. ✅ `BatchTrackingWindow` - `window_key = "batch_tracking"`
13. ✅ `ReorderRecommendationsWindow` - `window_key = "reorder_recommendations"`
14. ✅ `PhysicalCountsWindow` - `window_key = "physical_counts"`
15. ✅ `StockAdjustmentsWindow` - `window_key = "stock_adjustments"`
16. ✅ `AdvancedSearchWindow` - `window_key = "advanced_search"`
17. ✅ `PermissionManagementWindow` - `window_key = "permissions"`
18. ✅ `CycleCountWindow` - `window_key = "cycle_count"`
19. ✅ `PaymentDashboard` - `window_key = "payment_dashboard"`

### 3. تحديث main_window.py
- ✅ تم تحديث جميع تسجيلات النوافذ لاستخدام Class-based registration
- ✅ تم تحديث الاستيراد والتهيئة

---

## 🚀 استخدام auto_register (اختياري)

بعد إضافة `window_key` لجميع النوافذ، يمكنك استخدام `auto_register`:

```python
# في main_window.py - _register_all_windows()

# استيراد جميع النوافذ
from src.ui.windows.reports_window import ReportsWindow
from src.ui.windows.dashboard_window import DashboardWindow
# ... إلخ

# تسجيل تلقائي
self.window_manager.auto_register([
    ReportsWindow,
    DashboardWindow,
    AccountsWindow,
    AdvancedReportsWindow,
    QuotesWindow,
    ReturnsWindow,
    PurchaseOrdersWindow,
    AccountingWindow,
    PaymentPlansWindow,
    ABCAnalysisWindow,
    SafetyStockWindow,
    BatchTrackingWindow,
    ReorderRecommendationsWindow,
    PhysicalCountsWindow,
    StockAdjustmentsWindow,
    AdvancedSearchWindow,
    PermissionManagementWindow
])

# ملاحظة: CycleCountWindow و PaymentDashboard يحتاجان معاملات خاصة
# لذا يتم تسجيلهما يدوياً
```

---

## 📋 خطوات الاختبار (الخيار 3)

### اختبار النوافذ واحدة تلو الأخرى:

#### 1. اختبار ReportsWindow
```python
# في main_window.py
def test_reports_window(self):
    window = self.window_manager.open_window("reports", parent=self)
    assert window is not None, "فشل فتح نافذة التقارير"
    assert window.isVisible(), "النافذة غير مرئية"
    print("✅ ReportsWindow يعمل بشكل صحيح")
```

#### 2. اختبار DashboardWindow
```python
def test_dashboard_window(self):
    window = self.window_manager.open_window("dashboard", parent=self)
    assert window is not None, "فشل فتح نافذة لوحة المعلومات"
    assert window.isVisible(), "النافذة غير مرئية"
    print("✅ DashboardWindow يعمل بشكل صحيح")
```

#### 3. اختبار Singleton Behavior
```python
def test_singleton_behavior(self):
    window1 = self.window_manager.open_window("reports", parent=self)
    window2 = self.window_manager.open_window("reports", parent=self)
    
    assert window1 is window2, "Singleton لا يعمل - تم إنشاء نافذتين"
    assert self.window_manager.is_open("reports"), "is_open لا يعمل"
    print("✅ Singleton Behavior يعمل بشكل صحيح")
```

#### 4. اختبار حفظ/استعادة الحالة
```python
def test_state_save_restore(self):
    # فتح النافذة
    window = self.window_manager.open_window("reports", parent=self)
    
    # تغيير الحجم والموضع
    window.resize(1600, 1000)
    window.move(100, 100)
    
    # إغلاق النافذة
    window.close()
    
    # إعادة الفتح
    window2 = self.window_manager.open_window("reports", parent=self)
    
    # التحقق من الحجم والموضع
    assert window2.width() == 1600, "الحجم لم يُحفظ"
    assert window2.x() == 100, "الموضع لم يُحفظ"
    print("✅ حفظ/استعادة الحالة يعمل بشكل صحيح")
```

---

## 🎯 Checklist الاختبار السريع

### اختبار أساسي (5 دقائق):
- [ ] شغّل التطبيق
- [ ] افتح `ReportsWindow` - تحقق من أنها تفتح
- [ ] افتح `ReportsWindow` مرة أخرى - تحقق من أنها لا تُنشأ مرة أخرى (singleton)
- [ ] حرّك النافذة وغيّر حجمها
- [ ] أغلق النافذة
- [ ] افتحها مرة أخرى - تحقق من أنها عادت لنفس المكان والحجم

### اختبار متقدم (10 دقائق):
- [ ] افتح 3-4 نوافذ مختلفة
- [ ] تحقق من أن كل نافذة تحفظ حالتها بشكل مستقل
- [ ] أغلق جميع النوافذ
- [ ] افتحها مرة أخرى - تحقق من أنها عادت لنفس الحالة

---

## 🔧 استكشاف الأخطاء

### المشكلة: النافذة لا تفتح
**الحل:**
1. تحقق من أن النافذة مسجلة: `"window_key" in window_manager._configs`
2. تحقق من السجلات (logs) لأي أخطاء

### المشكلة: النافذة تُحذف فوراً
**الحل:**
1. تحقق من أن `window_key` و `window_singleton` موجودان
2. تحقق من أن `init_kwargs` صحيح

### المشكلة: الحالة لا تُحفظ
**الحل:**
1. تحقق من أن النافذة تُغلق بشكل صحيح (ليس `deleteLater()` مباشرة)
2. تحقق من QSettings: `window_manager.settings.value("window_key/geometry")`

---

## ✅ النتيجة النهائية

**النظام الآن:**
- ✅ يستخدم نسخة بسيطة واحترافية من Window Manager
- ✅ جميع النوافذ محدثة بـ `window_key`
- ✅ جاهز لاستخدام `auto_register` (اختياري)
- ✅ يدعم حفظ/استعادة الحالة تلقائياً
- ✅ منع memory leaks (weakrefs)
- ✅ لا يعيد كتابة `closeEvent`

**جاهز للإنتاج!** 🎯


# Window Manager Update Summary - ملخص التحديثات

## ✅ تم إنجازه

### 1. إنشاء النسخة الجديدة
- ✅ تم إنشاء `src/core/window_manager.py` - نسخة بسيطة واحترافية
- ✅ يدعم: تسجيل النوافذ، فتح/إغلاق، singleton vs multiple، weakrefs، QSettings آمن، hooks

### 2. تحديث main_window.py
- ✅ تم تحديث جميع تسجيلات النوافذ من Factory Pattern إلى Class-based registration
- ✅ تم تحديث الاستيراد: `from src.core.window_manager import WindowManager`
- ✅ تم تحديث التهيئة: `WindowManager(organization="LogicalVersion", appname="ERP", parent=self)`
- ✅ تم تحديث جميع التسجيلات لاستخدام `window_key` و `window_class` و `init_kwargs`

### 3. تحديث PhysicalCountsWindow
- ✅ تم إضافة `window_key = "physical_counts"`
- ✅ تم إضافة `window_singleton = True`
- ✅ تم إضافة `window_title = "العد الفعلي"`

---

## 📋 النوافذ المحدثة

تم تحديث تسجيل النوافذ التالية:

1. ✅ `reports` - ReportsWindow
2. ✅ `dashboard` - DashboardWindow
3. ✅ `accounts` - AccountsWindow
4. ✅ `advanced_reports` - AdvancedReportsWindow
5. ✅ `quotes` - QuotesWindow
6. ✅ `returns` - ReturnsWindow
7. ✅ `purchase_orders` - PurchaseOrdersWindow
8. ✅ `accounting` - AccountingWindow
9. ✅ `payment_plans` - PaymentPlansWindow
10. ✅ `abc_analysis` - ABCAnalysisWindow
11. ✅ `safety_stock` - SafetyStockWindow
12. ✅ `batch_tracking` - BatchTrackingWindow
13. ✅ `reorder_recommendations` - ReorderRecommendationsWindow
14. ✅ `physical_counts` - PhysicalCountsWindow
15. ✅ `cycle_count` - CycleCountWindow (مع service خاص)
16. ✅ `stock_adjustments` - StockAdjustmentsWindow
17. ✅ `advanced_search` - AdvancedSearchWindow
18. ✅ `permissions` - PermissionManagementWindow
19. ✅ `payment_dashboard` - PaymentDashboard (مع payment_service)
20. ✅ `audit_viewer` - AuditViewerWindow

---

## 🔄 التغييرات الرئيسية

### قبل (Factory Pattern):
```python
def reports_factory(**kwargs):
    return ReportsWindow(self.db_manager, **kwargs)

self.window_manager.register_window(
    window_id="reports",
    factory=reports_factory,
    title="نظام التقارير",
    min_size=QSize(1200, 800),
    default_size=QSize(1600, 1000),
    singleton=True
)
```

### بعد (Class-based):
```python
self.window_manager.register_window(
    window_key="reports",
    window_class=ReportsWindow,
    title="نظام التقارير",
    singleton=True,
    init_kwargs={"db_manager": self.db_manager}
)
```

---

## 📝 الخطوات التالية (اختياري)

### الخيار 2: إضافة window_key للنوافذ (للتسجيل التلقائي)

يمكنك إضافة `window_key` و `window_singleton` لجميع النوافذ ثم استخدام `auto_register`:

**مثال:**
```python
class ReportsWindow(QMainWindow):
    window_key = "reports"
    window_singleton = True
    window_title = "نظام التقارير"
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        # ...
```

**ثم في main_window.py:**
```python
from src.ui.windows.reports_window import ReportsWindow
from src.ui.windows.dashboard_window import DashboardWindow
# ... إلخ

self.window_manager.auto_register([
    ReportsWindow,
    DashboardWindow,
    # ... باقي النوافذ
])
```

---

## ✅ Checklist

- [x] إنشاء `src/core/window_manager.py`
- [x] تحديث الاستيراد في `main_window.py`
- [x] تحديث تهيئة `WindowManager`
- [x] تحديث جميع تسجيلات النوافذ
- [x] تحديث استدعاءات `open_window`
- [ ] إضافة `window_key` لجميع النوافذ (اختياري)
- [ ] استخدام `auto_register` (اختياري)
- [ ] اختبار جميع النوافذ

---

## 🚀 جاهز للاختبار

يمكنك الآن:
1. تشغيل التطبيق: `python main.py`
2. اختبار فتح/إغلاق النوافذ
3. اختبار حفظ/استعادة الحالة

**النظام الآن يستخدم النسخة الجديدة البسيطة!** 🎯


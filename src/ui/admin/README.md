# Admin UI Module - واجهات لوحة الإدارة

## نظرة عامة
هذا المجلد يحتوي على لوحات الإدارة (Admin Panels) للتطبيق. هذه اللوحات توفر أدوات إدارية متقدمة لمراقبة وإدارة النظام.

## 📊 الإحصائيات

- **إجمالي الملفات**: 5 ملفات Python + 1 ملف `__init__.py`
- **إجمالي الأسطر**: 627 سطر
- **متوسط الأسطر لكل ملف**: 125 سطر
- **Syntax Check**: ✅ جميع الملفات صحيحة
- **Linter**: ✅ لا توجد أخطاء

## 📁 الملفات

### 1. `audit_viewer.py` (51 سطر)

**الوصف**: عارض سجلات التدقيق (Audit Log Viewer)

**الميزات**:
- ✅ عرض سجلات التدقيق
- ✅ تحديث يدوي
- ✅ عرض الوقت، المستخدم، الحدث، الكيان، التفاصيل

**الكلاسات**:
- `AuditViewerWidget` - ويدجت عارض سجلات التدقيق
- `AuditViewer` - توافق مع الاستيراد الموجود

**الاستخدام**:
```python
from src.ui.admin import AuditViewer
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
audit_viewer = AuditViewer(db_manager)
audit_viewer.show()
```

**التكامل**:
- يستخدم `AuditLogService` من `src/services/audit_log_service.py`
- متكامل مع `SystemManagementWindow` و `MainWindow`

---

### 2. `cache_stats_panel.py` (155 سطر) ⭐

**الوصف**: لوحة إحصائيات الذاكرة المؤقتة (Cache Statistics Panel)

**الميزات**:
- ✅ عرض إحصائيات جميع الذاكرات المؤقتة
- ✅ عرض العناصر الأعلى استخداماً
- ✅ تحديث تلقائي كل 10 ثواني
- ✅ مسح ذاكرة محددة أو كل الذاكرات
- ✅ إحصائيات مفصلة: الحجم، الحد الأقصى، نسبة الاستخدام، Hits، Misses، Hit Rate، Evictions، Expirations

**الكلاسات**:
- `CacheStatsPanel` - لوحة إحصائيات الذاكرة المؤقتة

**الميزات التفصيلية**:
- جدول ملخص لكل ذاكرة مؤقتة
- جدول العناصر الأعلى استخداماً (Top Items)
- تحديث تلقائي كل 10 ثواني
- أزرار التحكم: تحديث يدوي، مسح محددة، مسح كل الذاكرات

**الاستخدام**:
```python
from src.ui.admin import CacheStatsPanel
from src.services.cache_service import get_cache_service

cache_service = get_cache_service()
cache_panel = CacheStatsPanel(cache_service)
cache_panel.show()
```

**التكامل**:
- يستخدم `CacheService` من `src/services/cache_service.py`
- متكامل مع `SystemManagementWindow` و `MainWindow`

---

### 3. `performance_panel.py` (97 سطر)

**الوصف**: لوحة الأداء (Performance Panel)

**الميزات**:
- ✅ مراقبة الأداء في الوقت الفعلي
- ✅ تحديث تلقائي كل 5 ثواني
- ✅ عرض مقاييس الأداء: CPU%, RAM%, حجم قاعدة البيانات، عدد الاستعلامات، متوسط وقت الاستعلام، Cache Hit Rate
- ✅ عرض الاستعلامات البطيئة (من الذاكرة ومن قاعدة البيانات)

**الكلاسات**:
- `PerformancePanelWidget` - ويدجت لوحة الأداء
- `PerformancePanel` - توافق مع الاستيراد الموجود

**الميزات التفصيلية**:
- جدول المقاييس الرئيسية
- جدول الاستعلامات البطيئة (من الذاكرة)
- جدول الاستعلامات البطيئة (من قاعدة البيانات)
- تحديث تلقائي كل 5 ثواني

**الاستخدام**:
```python
from src.ui.admin import PerformancePanel
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
perf_panel = PerformancePanel(db_manager)
perf_panel.show()
```

**التكامل**:
- يستخدم `PerformanceService` من `src/services/performance_service.py`
- يستخدم `CacheService` من `src/services/cache_service.py`
- متكامل مع `SystemManagementWindow` و `MainWindow`

---

### 4. `roles_manager.py` (277 سطر) ⭐⭐ أكبر ملف

**الوصف**: مدير الأدوار والصلاحيات (Roles & Permissions Manager)

**الميزات**:
- ✅ عرض جميع الأدوار والصلاحيات
- ✅ إضافة أدوار جديدة
- ✅ تعديل الأدوار والصلاحيات
- ✅ حذف الأدوار
- ✅ تعيين جماعي للصلاحيات
- ✅ عرض المستخدمين لكل دور

**الكلاسات**:
- `RolesManagerWidget` - ويدجت مدير الأدوار
- `RolesManager` - توافق مع الاستيراد الموجود

**الميزات التفصيلية**:
- جدول الأدوار مع الصلاحيات والمستخدمين
- حوار إضافة دور جديد
- حوار تعديل دور
- حوار التعيين الجماعي
- تحديث يدوي

**الاستخدام**:
```python
from src.ui.admin import RolesManager
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
roles_manager = RolesManager(db_manager)
roles_manager.show()
```

**التكامل**:
- يستخدم `RBACService` من `src/services/rbac_service.py`
- متكامل مع `SystemManagementWindow` و `MainWindow`

---

### 5. `sessions_panel.py` (49 سطر)

**الوصف**: لوحة الجلسات النشطة (Active Sessions Panel)

**الميزات**:
- ✅ عرض الجلسات النشطة
- ✅ عرض معلومات الجلسة: معرف الجلسة، المستخدم، IP، آخر نشاط، حالة النشاط
- ✅ تحديث يدوي

**الكلاسات**:
- `SessionsPanelWidget` - ويدجت لوحة الجلسات
- `SessionsPanel` - توافق مع الاستيراد الموجود

**الاستخدام**:
```python
from src.ui.admin import SessionsPanel
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
sessions_panel = SessionsPanel(db_manager)
sessions_panel.show()
```

**التكامل**:
- يستخدم `AuditLogService` من `src/services/audit_log_service.py`
- متكامل مع `SystemManagementWindow` و `MainWindow`

---

## 🔗 التكامل

### مع SystemManagementWindow
```python
from src.ui.system_management_window import SystemManagementWindow
from src.ui.admin import (
    PerformancePanel, RolesManager, CacheStatsPanel,
    AuditViewer, SessionsPanel
)

# في SystemManagementWindow
self.performance_panel = PerformancePanel(db_manager)
self.roles_manager = RolesManager(db_manager)
self.cache_panel = CacheStatsPanel(cache_service)
self.audit_viewer = AuditViewer(db_manager)
self.sessions_panel = SessionsPanel(db_manager)
```

### مع MainWindow
```python
from src.ui.admin import (
    PerformancePanel, RolesManager, CacheStatsPanel,
    AuditViewer, SessionsPanel
)

# في MainWindow
def show_performance_panel_admin(self):
    panel = PerformancePanel(self.db_manager)
    panel.show()

def show_roles_manager_admin(self):
    manager = RolesManager(self.db_manager)
    manager.show()

def show_cache_stats_panel_admin(self):
    panel = CacheStatsPanel(self.cache_service)
    panel.show()

def show_audit_viewer_admin(self):
    viewer = AuditViewer(self.db_manager)
    viewer.show()

def show_sessions_panel_admin(self):
    panel = SessionsPanel(self.db_manager)
    panel.show()
```

---

## 📝 الميزات الرئيسية

### 1. مراقبة الأداء
- ✅ مراقبة CPU و RAM
- ✅ مراقبة قاعدة البيانات
- ✅ مراقبة الاستعلامات البطيئة
- ✅ مراقبة Cache Hit Rate

### 2. إدارة الصلاحيات
- ✅ إدارة الأدوار
- ✅ إدارة الصلاحيات
- ✅ تعيين جماعي
- ✅ عرض المستخدمين

### 3. مراقبة النظام
- ✅ سجلات التدقيق
- ✅ الجلسات النشطة
- ✅ إحصائيات الذاكرة المؤقتة

### 4. التحديث التلقائي
- ✅ تحديث تلقائي للأداء (كل 5 ثواني)
- ✅ تحديث تلقائي للذاكرة المؤقتة (كل 10 ثواني)

---

## 🎯 أفضل الممارسات

### 1. استخدام اللوحات
```python
# ✅ صحيح - استخدام اللوحات في نافذة منفصلة
panel = PerformancePanel(db_manager)
panel.show()

# ✅ صحيح - استخدام اللوحات في SystemManagementWindow
self.tabs.addTab(self.performance_panel, "الأداء")
```

### 2. إدارة الموارد
```python
def closeEvent(self, event):
    # إيقاف التحديث التلقائي
    if hasattr(self, '_timer'):
        self._timer.stop()
    event.accept()
```

### 3. معالجة الأخطاء
```python
try:
    data = self.service.get_data()
    self.update_ui(data)
except Exception as e:
    self.show_error(str(e))
```

---

## 📚 المراجع

- `src/services/performance_service.py` - خدمة الأداء
- `src/services/rbac_service.py` - خدمة RBAC
- `src/services/cache_service.py` - خدمة التخزين المؤقت
- `src/services/audit_log_service.py` - خدمة سجلات المراجعة
- `src/ui/system_management_window.py` - نافذة إدارة النظام
- `src/ui/windows/main_window.py` - النافذة الرئيسية

---

## ✅ الخلاصة

- ✅ جميع اللوحات موثقة بشكل جيد
- ✅ استخدام PySide6 بشكل صحيح
- ✅ تحديث تلقائي للأداء والذاكرة المؤقتة
- ✅ تكامل جيد مع الخدمات
- ✅ واجهات مستخدم واضحة وسهلة الاستخدام

**التقييم**: 5/5 ⭐⭐⭐⭐⭐


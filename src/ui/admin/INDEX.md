# Admin UI Module Index - فهرس لوحات الإدارة

## 📋 قائمة سريعة باللوحات (5 لوحات)

### 1. `audit_viewer.py` (51 سطر)
**الوصف**: عارض سجلات التدقيق

**الكلاسات**:
- `AuditViewerWidget` - ويدجت عارض سجلات التدقيق
- `AuditViewer` - توافق مع الاستيراد الموجود

**الميزات**:
- عرض سجلات التدقيق
- تحديث يدوي
- عرض الوقت، المستخدم، الحدث، الكيان، التفاصيل

---

### 2. `cache_stats_panel.py` (155 سطر) ⭐
**الوصف**: لوحة إحصائيات الذاكرة المؤقتة

**الكلاسات**:
- `CacheStatsPanel` - لوحة إحصائيات الذاكرة المؤقتة

**الميزات**:
- عرض إحصائيات جميع الذاكرات المؤقتة
- عرض العناصر الأعلى استخداماً
- تحديث تلقائي كل 10 ثواني
- مسح ذاكرة محددة أو كل الذاكرات

---

### 3. `performance_panel.py` (97 سطر)
**الوصف**: لوحة الأداء

**الكلاسات**:
- `PerformancePanelWidget` - ويدجت لوحة الأداء
- `PerformancePanel` - توافق مع الاستيراد الموجود

**الميزات**:
- مراقبة الأداء في الوقت الفعلي
- تحديث تلقائي كل 5 ثواني
- عرض مقاييس الأداء: CPU%, RAM%, حجم قاعدة البيانات، عدد الاستعلامات، متوسط وقت الاستعلام، Cache Hit Rate
- عرض الاستعلامات البطيئة

---

### 4. `roles_manager.py` (277 سطر) ⭐⭐ أكبر ملف
**الوصف**: مدير الأدوار والصلاحيات

**الكلاسات**:
- `RolesManagerWidget` - ويدجت مدير الأدوار
- `RolesManager` - توافق مع الاستيراد الموجود

**الميزات**:
- عرض جميع الأدوار والصلاحيات
- إضافة أدوار جديدة
- تعديل الأدوار والصلاحيات
- حذف الأدوار
- تعيين جماعي للصلاحيات
- عرض المستخدمين لكل دور

---

### 5. `sessions_panel.py` (49 سطر)
**الوصف**: لوحة الجلسات النشطة

**الكلاسات**:
- `SessionsPanelWidget` - ويدجت لوحة الجلسات
- `SessionsPanel` - توافق مع الاستيراد الموجود

**الميزات**:
- عرض الجلسات النشطة
- عرض معلومات الجلسة: معرف الجلسة، المستخدم، IP، آخر نشاط، حالة النشاط
- تحديث يدوي

---

## 📊 الإحصائيات

- **إجمالي الملفات**: 5 ملفات Python + 1 ملف `__init__.py`
- **إجمالي الأسطر**: 627 سطر
- **متوسط الأسطر لكل ملف**: 125 سطر
- **أكبر ملف**: `roles_manager.py` (277 سطر)
- **أصغر ملف**: `audit_viewer.py` (51 سطر)

---

## 🔍 البحث السريع

### حسب الوظيفة:
- **Performance**: `performance_panel.py`
- **Cache**: `cache_stats_panel.py`
- **Audit**: `audit_viewer.py`
- **Roles**: `roles_manager.py`
- **Sessions**: `sessions_panel.py`

### حسب الحجم:
- **كبيرة (> 200 سطر)**: `roles_manager.py`
- **متوسطة (100-200 سطر)**: `cache_stats_panel.py`, `performance_panel.py`
- **صغيرة (< 100 سطر)**: `audit_viewer.py`, `sessions_panel.py`

---

## 💻 أمثلة الاستخدام السريع

### Audit Viewer
```python
from src.ui.admin import AuditViewer
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
audit_viewer = AuditViewer(db_manager)
audit_viewer.show()
```

### Cache Stats Panel
```python
from src.ui.admin import CacheStatsPanel
from src.services.cache_service import get_cache_service

cache_service = get_cache_service()
cache_panel = CacheStatsPanel(cache_service)
cache_panel.show()
```

### Performance Panel
```python
from src.ui.admin import PerformancePanel
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
perf_panel = PerformancePanel(db_manager)
perf_panel.show()
```

### Roles Manager
```python
from src.ui.admin import RolesManager
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
roles_manager = RolesManager(db_manager)
roles_manager.show()
```

### Sessions Panel
```python
from src.ui.admin import SessionsPanel
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager()
sessions_panel = SessionsPanel(db_manager)
sessions_panel.show()
```

---

## 🔗 روابط سريعة

- [README.md](README.md) - دليل شامل
- [../README.md](../README.md) - دليل واجهات المستخدم
- [../../services/README.md](../../services/README.md) - دليل الخدمات
- [../../core/README.md](../../core/README.md) - دليل الوحدات الأساسية

---

## ✅ الحالة

- ✅ جميع اللوحات موثقة بشكل جيد
- ✅ استخدام PySide6 بشكل صحيح
- ✅ تحديث تلقائي للأداء والذاكرة المؤقتة
- ✅ تكامل جيد مع الخدمات
- ✅ واجهات مستخدم واضحة وسهلة الاستخدام


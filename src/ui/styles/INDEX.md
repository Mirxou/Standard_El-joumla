# Styles Module Index - فهرس الأنماط

## 📋 قائمة سريعة بالملفات (12 ملف)

### ملفات Python (2 ملف)
1. **`main.py`** (105 سطر) - محمل الأنماط الرئيسية
   - `load_qss_file()` - تحميل ملف QSS
   - `load_main_style()` - تحميل الأنماط الرئيسي
   - `apply_style_to_app()` - تطبيق الأنماط
   - `get_available_themes()` - السمات المتاحة

2. **`icon_loader.py`** (179 سطر) ⭐ - محمل الأيقونات
   - `IconLoader` - محمل الأيقونات
   - `get_icon_loader()` - الحصول على محمل الأيقونات
   - دعم SVG مع إعادة تلوين ديناميكية

### ملفات QSS (10 ملفات)
3. **`main.qss`** (17 سطر) - ملف الأنماط الرئيسي
   - يجمع جميع ملفات الأنماط الأخرى
   - يستخدم @import

4. **`variables.qss`** (35 سطر) - متغيرات الألوان والمسافات
   - تعريف الألوان الأساسية
   - تعريف المسافات والحدود

5. **`buttons.qss`** (119 سطر) - أنماط الأزرار
   - Primary, Secondary, Danger, Success buttons
   - حالات: hover, pressed, disabled

6. **`inputs.qss`** (248 سطر) ⭐ - أنماط حقول الإدخال
   - QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit
   - حالات: focus, hover, disabled

7. **`tables.qss`** (70 سطر) - أنماط الجداول
   - QTableView, QTableWidget
   - رؤوس الجداول والعناصر

8. **`dialogs.qss`** (98 سطر) - أنماط الحوارات
   - QDialog, QMessageBox, QGroupBox, QLabel, QFrame

9. **`scrollbars.qss`** (62 سطر) - أنماط أشرطة التمرير
   - QScrollBar (عمودي وأفقي)
   - أنماط الـ handle

10. **`tabs.qss`** (44 سطر) - أنماط التبويبات
    - QTabWidget, QTabBar
    - حالات: selected, hover

11. **`progress.qss`** (34 سطر) - أنماط أشرطة التقدم
    - QProgressBar
    - أنماط الـ chunk

12. **`general.qss`** (92 سطر) - الأنماط العامة
    - QMenu, QMenuBar, QToolBar, QStatusBar, QSplitter

---

## 📊 الإحصائيات

- **إجمالي الملفات**: 12 ملف (2 Python + 10 QSS)
- **Python total lines**: 282 سطر
- **QSS total lines**: 809 سطر
- **أكبر ملف Python**: `icon_loader.py` (179 سطر)
- **أكبر ملف QSS**: `inputs.qss` (248 سطر)
- **أصغر ملف**: `main.qss` (17 سطر)

---

## 🔍 البحث السريع

### حسب النوع:
- **Loaders**: `main.py`, `icon_loader.py`
- **Component Styles**: `buttons.qss`, `inputs.qss`, `tables.qss`, `dialogs.qss`
- **System Styles**: `scrollbars.qss`, `tabs.qss`, `progress.qss`, `general.qss`
- **Configuration**: `main.qss`, `variables.qss`

### حسب الحجم:
- **كبيرة (> 200 سطر)**: `icon_loader.py`, `inputs.qss`
- **متوسطة (100-200 سطر)**: `main.py`, `buttons.qss`, `dialogs.qss`
- **صغيرة (< 100 سطر)**: باقي الملفات

---

## 💻 أمثلة الاستخدام السريع

### تطبيق الأنماط
```python
from src.ui.styles.main import apply_style_to_app

apply_style_to_app(app, theme='light')
```

### تحميل الأنماط
```python
from src.ui.styles.main import load_main_style

style_sheet = load_main_style(theme='light')
app.setStyleSheet(style_sheet)
```

### استخدام الأيقونات
```python
from src.ui.styles.icon_loader import get_icon_loader, IconLoader

icon_loader = get_icon_loader()
icon = icon_loader.load_icon(IconLoader.ICON_EDIT, size=24)
button.setIcon(icon)
```

---

## 🎨 نظام الألوان

### الألوان الأساسية:
- **Primary**: `#3b82f6` (أزرق)
- **Danger**: `#ef4444` (أحمر)
- **Success**: `#10b981` (أخضر)
- **Warning**: `#f59e0b` (برتقالي)

### المسافات:
- **XS**: 4px, **SM**: 8px, **MD**: 12px, **LG**: 16px, **XL**: 24px

### الحدود:
- **Small**: 4px, **Medium**: 6px, **Large**: 8px

---

## 🔗 روابط سريعة

- [README.md](README.md) - دليل شامل
- [../README.md](../README.md) - دليل واجهات المستخدم
- [../theme_manager.py](../theme_manager.py) - مدير السمات
- [../../core/README.md](../../core/README.md) - دليل الوحدات الأساسية

---

## ✅ الحالة

- ✅ جميع ملفات الأنماط موثقة بشكل جيد
- ✅ نظام QSS modular ومنظم
- ✅ دعم كامل للأيقونات SVG
- ✅ تصميم حديث ومتسق
- ✅ سهولة الصيانة والتحديث


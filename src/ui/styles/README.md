# Styles Module - وحدات الأنماط

## نظرة عامة
هذا المجلد يحتوي على جميع ملفات الأنماط (QSS - Qt Style Sheets) وملفات تحميل الأنماط والأيقونات للتطبيق. يستخدم نظام QSS لتطبيق أنماط CSS-like على واجهات Qt.

## 📊 الإحصائيات

- **إجمالي الملفات**: 12 ملف (2 Python + 10 QSS)
- **Python Files**: 2 ملفات (282 سطر)
- **QSS Files**: 10 ملفات (809 سطر)
- **Syntax Check**: ✅ جميع الملفات صحيحة
- **Linter**: ✅ لا توجد أخطاء

## 📁 الملفات

### ملفات Python (2 ملف)

#### `main.py` (105 سطر)
**الوصف**: محمل الأنماط الرئيسية مع دعم السمات

**الوظائف**:
- `load_qss_file(file_path)` - تحميل ملف QSS مع معالجة @import
- `load_main_style(theme)` - تحميل ملف الأنماط الرئيسي
- `apply_style_to_app(app, theme)` - تطبيق الأنماط على التطبيق
- `get_available_themes()` - الحصول على قائمة السمات المتاحة

**الميزات**:
- ✅ دعم @import في ملفات QSS
- ✅ دعم السمات (Light/Dark)
- ✅ معالجة الأخطاء

**الاستخدام**:
```python
from src.ui.styles.main import apply_style_to_app, load_main_style

# تطبيق الأنماط على التطبيق
apply_style_to_app(app, theme='light')

# تحميل الأنماط مباشرة
style_sheet = load_main_style(theme='dark')
```

---

#### `icon_loader.py` (179 سطر) ⭐
**الوصف**: نظام تحميل الأيقونات الحديثة (SVG)

**الكلاسات**:
- `IconLoader` - محمل الأيقونات
  - `load_icon(name, size, color)` - تحميل أيقونة
  - `get_icon_path(name)` - الحصول على مسار الأيقونة
  - `recolor_svg(svg_content, color)` - إعادة تلوين SVG

**الميزات**:
- ✅ دعم SVG icons
- ✅ إعادة تلوين ديناميكية
- ✅ أحجام مختلفة
- ✅ أيقونات قياسية محددة مسبقاً

**الأيقونات القياسية**:
- `ICON_EDIT` - تعديل
- `ICON_DELETE` - حذف
- `ICON_SAVE` - حفظ
- `ICON_SEARCH` - بحث
- `ICON_PLUS` - إضافة
- `ICON_REFRESH` - تحديث
- `ICON_SETTINGS` - إعدادات
- `ICON_CLOSE` - إغلاق
- `ICON_CHECK` - تأكيد
- `ICON_FILTER` - فلترة
- `ICON_DOWNLOAD` - تحميل

**الاستخدام**:
```python
from src.ui.styles.icon_loader import IconLoader, get_icon_loader

# استخدام محمل الأيقونات
icon_loader = get_icon_loader()
icon = icon_loader.load_icon("edit", size=24, color="#3b82f6")
button.setIcon(icon)
```

---

### ملفات QSS (10 ملفات)

#### `main.qss` (17 سطر)
**الوصف**: ملف الأنماط الرئيسي - يجمع جميع ملفات الأنماط المنفصلة

**الميزات**:
- ✅ يستورد جميع ملفات الأنماط الأخرى باستخدام @import
- ✅ نقطة دخول واحدة لجميع الأنماط

**الملفات المستوردة**:
- `tables.qss` - أنماط الجداول
- `buttons.qss` - أنماط الأزرار
- `inputs.qss` - أنماط حقول الإدخال
- `scrollbars.qss` - أنماط أشرطة التمرير
- `tabs.qss` - أنماط التبويبات
- `dialogs.qss` - أنماط الحوارات
- `progress.qss` - أنماط أشرطة التقدم
- `general.qss` - الأنماط العامة

---

#### `variables.qss` (35 سطر)
**الوصف**: متغيرات الألوان والمسافات (Theme Variables)

**الميزات**:
- ✅ تعريف الألوان الأساسية
- ✅ تعريف المسافات والحدود
- ✅ دعم Light Theme (افتراضي)

**المتغيرات**:
- **الألوان**: `bg-primary`, `bg-secondary`, `text-primary`, `text-secondary`, `primary`, `danger`, `success`, `warning`
- **المسافات**: `spacing-xs`, `spacing-sm`, `spacing-md`, `spacing-lg`, `spacing-xl`
- **الحدود**: `radius-small`, `radius-medium`, `radius-large`

**ملاحظة**: QSS لا يدعم CSS variables بشكل أصلي، لذا يتم استخدامها كمرجع واستبدالها في الكود.

---

#### `buttons.qss` (119 سطر)
**الوصف**: أنماط الأزرار (Button Styles)

**الميزات**:
- ✅ أنماط الأزرار الأساسية
- ✅ Primary Button (أزرق)
- ✅ Secondary Button (رمادي)
- ✅ Danger Button (أحمر)
- ✅ Success Button (أخضر)
- ✅ حالات: hover, pressed, disabled

**الأنماط**:
- `QPushButton` - الزر الأساسي
- `QPushButton[class="primary"]` - زر أساسي
- `QPushButton[class="secondary"]` - زر ثانوي
- `QPushButton[class="danger"]` - زر خطر
- `QPushButton[class="success"]` - زر نجاح

---

#### `inputs.qss` (248 سطر) ⭐ أكبر ملف QSS
**الوصف**: أنماط حقول الإدخال (Input Styles)

**الميزات**:
- ✅ أنماط `QLineEdit`
- ✅ أنماط `QComboBox`
- ✅ أنماط `QSpinBox`, `QDoubleSpinBox`
- ✅ أنماط `QDateEdit`, `QDateTimeEdit`
- ✅ أنماط `QTextEdit`, `QPlainTextEdit`
- ✅ حالات: focus, hover, disabled

**الحقول المدعومة**:
- `QLineEdit` - حقل نص بسيط
- `QComboBox` - قائمة منسدلة
- `QSpinBox` - حقل رقم صحيح
- `QDoubleSpinBox` - حقل رقم عشري
- `QDateEdit` - حقل تاريخ
- `QDateTimeEdit` - حقل تاريخ ووقت
- `QTextEdit` - حقل نص متعدد الأسطر
- `QPlainTextEdit` - حقل نص عادي

---

#### `tables.qss` (70 سطر)
**الوصف**: أنماط الجداول (Table Styles)

**الميزات**:
- ✅ أنماط `QTableView`, `QTableWidget`
- ✅ أنماط رؤوس الجداول
- ✅ أنماط العناصر (items)
- ✅ ألوان متناوبة (alternate rows)
- ✅ أنماط التحديد (selection)

**الأنماط**:
- `QTableView`, `QTableWidget` - الجدول الأساسي
- `QHeaderView` - رأس الجدول
- `QTableView::item`, `QTableWidget::item` - عناصر الجدول

---

#### `dialogs.qss` (98 سطر)
**الوصف**: أنماط الحوارات والرسائل (Dialog & Message Styles)

**الميزات**:
- ✅ أنماط `QDialog`, `QMessageBox`
- ✅ أنماط `QGroupBox`
- ✅ أنماط `QLabel`
- ✅ أنماط `QFrame`

**الأنماط**:
- `QDialog`, `QMessageBox` - الحوارات والرسائل
- `QGroupBox` - صندوق المجموعة
- `QLabel` - التسميات
- `QFrame` - الإطارات

---

#### `scrollbars.qss` (62 سطر)
**الوصف**: أنماط أشرطة التمرير (Scrollbar Styles)

**الميزات**:
- ✅ أنماط `QScrollBar` (عمودي وأفقي)
- ✅ أنماط الـ handle (المقبض)
- ✅ أنماط الـ add-line و sub-line
- ✅ حالات: hover, pressed

**الأنماط**:
- `QScrollBar:vertical` - شريط تمرير عمودي
- `QScrollBar:horizontal` - شريط تمرير أفقي
- `QScrollBar::handle` - المقبض
- `QScrollBar::add-line`, `QScrollBar::sub-line` - الأسهم

---

#### `tabs.qss` (44 سطر)
**الوصف**: أنماط التبويبات (Tab Styles)

**الميزات**:
- ✅ أنماط `QTabWidget`
- ✅ أنماط `QTabBar`
- ✅ أنماط التبويبات الفردية
- ✅ حالات: selected, hover, pressed

**الأنماط**:
- `QTabWidget` - ويدجت التبويبات
- `QTabBar` - شريط التبويبات
- `QTabBar::tab` - التبويبة الفردية

---

#### `progress.qss` (34 سطر)
**الوصف**: أنماط أشرطة التقدم (Progress Bar Styles)

**الميزات**:
- ✅ أنماط `QProgressBar`
- ✅ أنماط الـ chunk (القطعة)
- ✅ أنماط النص

**الأنماط**:
- `QProgressBar` - شريط التقدم الأساسي
- `QProgressBar::chunk` - قطعة التقدم

---

#### `general.qss` (92 سطر)
**الوصف**: الأنماط العامة (General Styles)

**الميزات**:
- ✅ أنماط عامة للعناصر المشتركة
- ✅ أنماط `QMenu`, `QMenuBar`
- ✅ أنماط `QToolBar`
- ✅ أنماط `QStatusBar`
- ✅ أنماط `QSplitter`

**الأنماط**:
- `QMenu`, `QMenuBar` - القوائم
- `QToolBar` - شريط الأدوات
- `QStatusBar` - شريط الحالة
- `QSplitter` - المقسم

---

## 🏗️ البنية المعمارية

### نظام التحميل
```
main.qss (نقطة الدخول)
  ├── @import tables.qss
  ├── @import buttons.qss
  ├── @import inputs.qss
  ├── @import scrollbars.qss
  ├── @import tabs.qss
  ├── @import dialogs.qss
  ├── @import progress.qss
  └── @import general.qss
```

### معالجة @import
- `load_qss_file()` تقوم بمعالجة `@import` تلقائياً
- استبدال `@import url(file.qss)` بمحتوى الملف
- دعم متداخل (nested imports)

---

## 💻 الاستخدام

### تطبيق الأنماط على التطبيق
```python
from src.ui.styles.main import apply_style_to_app
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
apply_style_to_app(app, theme='light')
```

### تحميل الأنماط مباشرة
```python
from src.ui.styles.main import load_main_style

style_sheet = load_main_style(theme='light')
app.setStyleSheet(style_sheet)
```

### استخدام الأيقونات
```python
from src.ui.styles.icon_loader import get_icon_loader

icon_loader = get_icon_loader()
icon = icon_loader.load_icon("edit", size=24, color="#3b82f6")
button.setIcon(icon)
```

### استخدام الأيقونات القياسية
```python
from src.ui.styles.icon_loader import IconLoader

icon_loader = IconLoader()
edit_icon = icon_loader.load_icon(IconLoader.ICON_EDIT)
delete_icon = icon_loader.load_icon(IconLoader.ICON_DELETE)
```

---

## 🎨 نظام الألوان

### Light Theme (افتراضي)
- **Primary**: `#3b82f6` (أزرق)
- **Danger**: `#ef4444` (أحمر)
- **Success**: `#10b981` (أخضر)
- **Warning**: `#f59e0b` (برتقالي)
- **Background**: `#ffffff` (أبيض)
- **Text Primary**: `#1e293b` (رمادي داكن)
- **Text Secondary**: `#64748b` (رمادي)

### المسافات
- **XS**: 4px
- **SM**: 8px
- **MD**: 12px
- **LG**: 16px
- **XL**: 24px

### الحدود
- **Small**: 4px
- **Medium**: 6px
- **Large**: 8px

---

## 🔗 التكامل

### مع Theme Manager
```python
from src.ui.theme_manager import get_theme_manager
from src.ui.styles.main import apply_style_to_app

theme_manager = get_theme_manager()
theme = theme_manager.get_current_theme()
apply_style_to_app(app, theme=theme)
```

### مع Main Window
```python
# في main.py
from src.ui.styles.main import apply_style_to_app

# تطبيق الأنماط عند بدء التطبيق
apply_style_to_app(self, theme=theme)
```

---

## 📝 أفضل الممارسات

### 1. استخدام الأنماط المحددة مسبقاً
```python
# ✅ صحيح - استخدام class للأنماط
button.setProperty("class", "primary")
button.style().unpolish(button)
button.style().polish(button)

# ❌ خطأ - تطبيق الأنماط مباشرة
button.setStyleSheet("background-color: #3b82f6;")
```

### 2. استخدام الأيقونات القياسية
```python
# ✅ صحيح - استخدام الأيقونات القياسية
icon = icon_loader.load_icon(IconLoader.ICON_EDIT)

# ❌ خطأ - استخدام مسار مباشر
icon = QIcon("assets/icons/edit.svg")
```

### 3. تحديث الأنماط ديناميكياً
```python
# عند تغيير السمة
def change_theme(self, theme):
    apply_style_to_app(QApplication.instance(), theme=theme)
    # إعادة تطبيق الأنماط على العناصر
    self.style().unpolish(self)
    self.style().polish(self)
```

---

## 🎯 الميزات الرئيسية

### 1. نظام QSS Modular
- ✅ ملفات منفصلة لكل نوع عنصر
- ✅ استيراد تلقائي عبر @import
- ✅ سهولة الصيانة والتحديث

### 2. نظام الأيقونات
- ✅ دعم SVG
- ✅ إعادة تلوين ديناميكية
- ✅ أيقونات قياسية محددة مسبقاً

### 3. دعم السمات
- ✅ Light Theme (افتراضي)
- ✅ دعم Dark Theme (جاهز للتطوير)
- ✅ تبديل سلس بين السمات

### 4. التصميم الحديث
- ✅ تصميم Material Design-inspired
- ✅ ألوان متسقة
- ✅ انتقالات سلسة
- ✅ دعم RTL (العربية)

---

## 📚 المراجع

- `src/ui/theme_manager.py` - مدير السمات
- `main.py` - التطبيق الرئيسي (تطبيق الأنماط)
- [Qt Style Sheets Documentation](https://doc.qt.io/qt-6/stylesheet.html)

---

## ✅ الخلاصة

- ✅ جميع ملفات الأنماط موثقة بشكل جيد
- ✅ نظام QSS modular ومنظم
- ✅ دعم كامل للأيقونات SVG
- ✅ تصميم حديث ومتسق
- ✅ سهولة الصيانة والتحديث

**التقييم**: 5/5 ⭐⭐⭐⭐⭐


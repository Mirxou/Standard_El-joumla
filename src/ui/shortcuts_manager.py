"""
Keyboard Shortcuts Manager - مدير اختصارات لوحة المفاتيح
نظام شامل لإدارة اختصارات لوحة المفاتيح
"""

from typing import Callable, Dict, Optional

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class KeyboardShortcut:
    """تمثيل اختصار واحد"""

    def __init__(self, key: str, description: str, category: str, default_key: str):
        self.key = key
        self.description = description
        self.category = category
        self.default_key = default_key
        self.shortcut: Optional[QShortcut] = None


class KeyboardShortcutsManager:
    """
    مدير اختصارات لوحة المفاتيح

    Features:
    - مجموعة شاملة من الاختصارات
    - حفظ واسترجاع الإعدادات
    - نافذة مساعدة تفاعلية
    """

    # تعريف جميع الاختصارات الافتراضية
    DEFAULT_SHORTCUTS = {
        # ملف
        "new_invoice": KeyboardShortcut("Ctrl+N", "فاتورة جديدة", "ملف", "Ctrl+N"),
        "save": KeyboardShortcut("Ctrl+S", "حفظ", "ملف", "Ctrl+S"),
        "print": KeyboardShortcut("Ctrl+P", "طباعة", "ملف", "Ctrl+P"),
        "backup": KeyboardShortcut("Ctrl+B", "نسخة احتياطية", "ملف", "Ctrl+B"),
        "quit": KeyboardShortcut("Ctrl+Q", "خروج", "ملف", "Ctrl+Q"),
        # عرض
        "theme": KeyboardShortcut("Ctrl+T", "تغيير السمة", "عرض", "Ctrl+T"),
        "fullscreen": KeyboardShortcut("F11", "ملء الشاشة", "عرض", "F11"),
        "refresh": KeyboardShortcut("F5", "تحديث", "عرض", "F5"),
        # بحث
        "search": KeyboardShortcut("Ctrl+F", "بحث", "بحث", "Ctrl+F"),
        "advanced_search": KeyboardShortcut("Ctrl+Shift+F", "بحث متقدم", "بحث", "Ctrl+Shift+F"),
        "find_next": KeyboardShortcut("F3", "البحث التالي", "بحث", "F3"),
        # تحرير
        "copy": KeyboardShortcut("Ctrl+C", "نسخ", "تحرير", "Ctrl+C"),
        "paste": KeyboardShortcut("Ctrl+V", "لصق", "تحرير", "Ctrl+V"),
        "cut": KeyboardShortcut("Ctrl+X", "قص", "تحرير", "Ctrl+X"),
        "undo": KeyboardShortcut("Ctrl+Z", "تراجع", "تحرير", "Ctrl+Z"),
        "redo": KeyboardShortcut("Ctrl+Y", "إعادة", "تحرير", "Ctrl+Y"),
        # مبيعات
        "new_sale": KeyboardShortcut("Ctrl+Shift+N", "بيع جديد", "مبيعات", "Ctrl+Shift+N"),
        "new_quote": KeyboardShortcut("Ctrl+Shift+Q", "عرض سعر جديد", "مبيعات", "Ctrl+Shift+Q"),
        "new_return": KeyboardShortcut("Ctrl+Shift+R", "مرتجع جديد", "مبيعات", "Ctrl+Shift+R"),
        # مخزون
        "new_product": KeyboardShortcut("Ctrl+Shift+P", "منتج جديد", "مخزون", "Ctrl+Shift+P"),
        "stock_check": KeyboardShortcut("Ctrl+Shift+S", "فحص المخزون", "مخزون", "Ctrl+Shift+S"),
        # عملاء وموردون
        "new_customer": KeyboardShortcut("Ctrl+Shift+C", "عميل جديد", "عملاء", "Ctrl+Shift+C"),
        "new_supplier": KeyboardShortcut("Ctrl+Shift+V", "مورد جديد", "موردون", "Ctrl+Shift+V"),
        # تقارير
        "sales_report": KeyboardShortcut("Alt+R", "تقرير المبيعات", "تقارير", "Alt+R"),
        "inventory_report": KeyboardShortcut("Alt+I", "تقرير المخزون", "تقارير", "Alt+I"),
        "financial_report": KeyboardShortcut("Alt+F", "تقرير مالي", "تقارير", "Alt+F"),
        # نوافذ
        "dashboard": KeyboardShortcut("Ctrl+D", "لوحة المعلومات", "نوافذ", "Ctrl+D"),
        "payments": KeyboardShortcut("Ctrl+M", "المدفوعات", "نوافذ", "Ctrl+M"),
        "accounting": KeyboardShortcut("Ctrl+A", "المحاسبة", "نوافذ", "Ctrl+A"),
        # مساعدة
        "help": KeyboardShortcut("F1", "مساعدة", "مساعدة", "F1"),
        "shortcuts": KeyboardShortcut("Ctrl+K", "الاختصارات", "مساعدة", "Ctrl+K"),
        "about": KeyboardShortcut("Ctrl+H", "حول البرنامج", "مساعدة", "Ctrl+H"),
    }

    def __init__(self, main_window):
        self.main_window = main_window
        self.settings = QSettings("StandardElJoumla", "ERP")
        self.shortcuts: Dict[str, KeyboardShortcut] = {}
        self.active_shortcuts: Dict[str, QShortcut] = {}

        # تحميل الاختصارات
        self.load_shortcuts()

    def load_shortcuts(self):
        """تحميل الاختصارات من الإعدادات"""
        for name, default_shortcut in self.DEFAULT_SHORTCUTS.items():
            # محاولة تحميل من الإعدادات أو استخدام الافتراضي
            saved_key = self.settings.value(f"shortcuts/{name}", default_shortcut.default_key)

            shortcut = KeyboardShortcut(
                key=saved_key,
                description=default_shortcut.description,
                category=default_shortcut.category,
                default_key=default_shortcut.default_key,
            )

            self.shortcuts[name] = shortcut

    def register_shortcut(self, name: str, handler: Callable):
        """
        تسجيل اختصار

        Args:
            name: اسم الاختصار
            handler: الدالة المراد تنفيذها
        """
        if name not in self.shortcuts:
            return

        shortcut_info = self.shortcuts[name]

        # إنشاء الاختصار
        qshortcut = QShortcut(QKeySequence(shortcut_info.key), self.main_window)
        qshortcut.activated.connect(handler)

        self.active_shortcuts[name] = qshortcut
        shortcut_info.shortcut = qshortcut

    def unregister_shortcut(self, name: str):
        """إلغاء تسجيل اختصار"""
        if name in self.active_shortcuts:
            self.active_shortcuts[name].setEnabled(False)
            del self.active_shortcuts[name]

    def update_shortcut(self, name: str, new_key: str):
        """
        تحديث اختصار

        Args:
            name: اسم الاختصار
            new_key: المفتاح الجديد
        """
        if name not in self.shortcuts:
            return

        # تحديث الاختصار
        self.shortcuts[name].key = new_key

        # حفظ في الإعدادات
        self.settings.setValue(f"shortcuts/{name}", new_key)

        # إعادة تسجيل إذا كان نشطًا
        if name in self.active_shortcuts:
            handler = self.active_shortcuts[name].activated
            self.unregister_shortcut(name)
            self.register_shortcut(name, handler)

    def reset_to_defaults(self):
        """إعادة تعيين جميع الاختصارات للافتراضية"""
        for name, shortcut in self.shortcuts.items():
            shortcut.key = shortcut.default_key
            self.settings.setValue(f"shortcuts/{name}", shortcut.default_key)

        # إعادة تسجيل الاختصارات النشطة
        for name in list(self.active_shortcuts.keys()):
            handler = self.active_shortcuts[name].activated
            self.unregister_shortcut(name)
            self.register_shortcut(name, handler)

    def get_shortcuts_by_category(self) -> Dict[str, list]:
        """الحصول على الاختصارات مجموعة حسب الفئة"""
        categories = {}

        for name, shortcut in self.shortcuts.items():
            category = shortcut.category
            if category not in categories:
                categories[category] = []

            categories[category].append({"name": name, "key": shortcut.key, "description": shortcut.description})

        return categories

    def show_shortcuts_dialog(self):
        """عرض نافذة الاختصارات"""
        dialog = ShortcutsHelpDialog(self, self.main_window)
        dialog.exec()


class ShortcutsHelpDialog(QDialog):
    """نافذة مساعدة الاختصارات"""

    def __init__(self, shortcuts_manager: KeyboardShortcutsManager, parent=None):
        super().__init__(parent)
        self.shortcuts_manager = shortcuts_manager
        self.setup_ui()

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("اختصارات لوحة المفاتيح - Keyboard Shortcuts")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # عنوان
        title = QLabel("<h2>⌨️ اختصارات لوحة المفاتيح</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # جدول الاختصارات
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["الاختصار", "الوصف", "الفئة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setMinimumSectionSize(120)
        self.table.horizontalHeader().setDefaultSectionSize(150)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

        # ملء الجدول
        self.populate_table()

        # معلومات
        info = QLabel("💡 <b>ملاحظة:</b> يمكنك استخدام هذه الاختصارات في أي مكان في البرنامج.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        reset_btn = QPushButton("🔄 إعادة تعيين للافتراضي")
        reset_btn.clicked.connect(self.reset_shortcuts)
        buttons_layout.addWidget(reset_btn)

        print_btn = QPushButton("🖨️ طباعة")
        print_btn.clicked.connect(self.print_shortcuts)
        buttons_layout.addWidget(print_btn)

        close_btn = QPushButton("✗ إغلاق")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def populate_table(self):
        """ملء الجدول بالاختصارات"""
        categories = self.shortcuts_manager.get_shortcuts_by_category()

        # حساب عدد الصفوف
        total_rows = sum(len(shortcuts) for shortcuts in categories.values())
        self.table.setRowCount(total_rows)

        row = 0
        for category in sorted(categories.keys()):
            shortcuts = categories[category]

            for shortcut in sorted(shortcuts, key=lambda x: x["description"]):
                self.table.setItem(row, 0, QTableWidgetItem(shortcut["key"]))
                self.table.setItem(row, 1, QTableWidgetItem(shortcut["description"]))
                self.table.setItem(row, 2, QTableWidgetItem(category))
                row += 1

    def reset_shortcuts(self):
        """إعادة تعيين الاختصارات"""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد إعادة تعيين جميع الاختصارات إلى الافتراضية؟",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.shortcuts_manager.reset_to_defaults()
            self.populate_table()
            QMessageBox.information(self, "نجح", "تم إعادة تعيين جميع الاختصارات")

    def print_shortcuts(self):
        """طباعة الاختصارات"""
        # يمكن تنفيذ الطباعة هنا
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(self, "قريبًا", "ميزة الطباعة قيد التطوير")


def setup_main_window_shortcuts(main_window):
    """
    إعداد اختصارات النافذة الرئيسية

    Args:
        main_window: النافذة الرئيسية
    """
    shortcuts_manager = KeyboardShortcutsManager(main_window)

    # تسجيل الاختصارات الأساسية
    # ملف
    if hasattr(main_window, "backup_database"):
        shortcuts_manager.register_shortcut("backup", main_window.backup_database)

    # عرض
    if hasattr(main_window, "show_theme_selector"):
        shortcuts_manager.register_shortcut("theme", main_window.show_theme_selector)

    # بحث
    if hasattr(main_window, "show_advanced_search_window"):
        shortcuts_manager.register_shortcut("search", main_window.show_advanced_search_window)
        shortcuts_manager.register_shortcut("advanced_search", main_window.show_advanced_search_window)

    # نوافذ
    if hasattr(main_window, "show_main_dashboard"):
        shortcuts_manager.register_shortcut("dashboard", main_window.show_main_dashboard)

    if hasattr(main_window, "show_payment_dashboard"):
        shortcuts_manager.register_shortcut("payments", main_window.show_payment_dashboard)

    if hasattr(main_window, "show_accounting_window"):
        shortcuts_manager.register_shortcut("accounting", main_window.show_accounting_window)

    # مساعدة
    if hasattr(main_window, "show_about"):
        shortcuts_manager.register_shortcut("about", main_window.show_about)

    shortcuts_manager.register_shortcut("shortcuts", shortcuts_manager.show_shortcuts_dialog)

    # حفظ المرجع في النافذة الرئيسية
    main_window.shortcuts_manager = shortcuts_manager

    return shortcuts_manager

#!/usr/bin/env python3
"""
محوّل الواجهة حسب الدور - Role Based Morpher
"""

from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class RoleBasedMorpher:
    """محوّل الواجهة حسب دور المستخدم"""

    ROLES = {
        "sales": {"name": "مبيعات", "color": "#4CAF50", "tabs": ["العملاء", "المنتجات", "الفواتير"]},
        "warehouse": {"name": "المخازن", "color": "#FF9800", "tabs": ["الجرد", "الطلبات", "الشحن"]},
        "cfo": {"name": "المدير المالي", "color": "#2196F3", "tabs": ["التقارير", "الميزانية", "التحليلات"]},
        "admin": {"name": "المدير", "color": "#9C27B0", "tabs": ["الإعدادات", "المستخدمون", "النظام"]}
    }

    def __init__(self, main_window):
        self.main_window = main_window
        self.current_role = "sales"

    def morph_to_role(self, role):
        """تحويل الواجهة لدور معين"""
        if role not in self.ROLES:
            return False

        self.current_role = role
        role_config = self.ROLES[role]

        # تطبيق نظام الألوان
        self._apply_color_scheme(role_config["color"])

        # تحديث التبويبات الرئيسية
        self._update_main_tabs(role_config["tabs"])

        # تحديث العنوان
        self.main_window.setWindowTitle(f"نظام ERP - {role_config['name']}")

        return True

    def _apply_color_scheme(self, color):
        """تطبيق نظام الألوان"""
        style = f"""
        QMainWindow {{
            background-color: {color}10;
        }}
        QTabBar::tab:selected {{
            background-color: {color};
            color: white;
        }}
        """
        self.main_window.setStyleSheet(style)

    def _update_main_tabs(self, tabs):
        """تحديث التبويبات الرئيسية"""
        if hasattr(self.main_window, 'main_tabs'):
            # مسح التبويبات الحالية
            self.main_window.main_tabs.clear()

            # إضافة التبويبات الجديدة
            for tab_name in tabs:
                tab = QWidget()
                layout = QVBoxLayout()
                layout.addWidget(QLabel(f"محتوى تبويب {tab_name}"))
                tab.setLayout(layout)
                self.main_window.main_tabs.addTab(tab, tab_name)

    def get_available_roles(self):
        """الحصول على الأدوار المتاحة"""
        return list(self.ROLES.keys())

    def get_current_role_config(self):
        """الحصول على إعدادات الدور الحالي"""
        return self.ROLES.get(self.current_role, {})
import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsDropShadowEffect,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SmartCommandPalette(QDialog):
    """
    واجهة تحكم شاملة للوصول السريع لأي وظيفة في النظام (رؤية 2030)
    """

    command_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # حاوية رئيسية لتطبيق التأثيرات والحدود
        self.main_container = QWidget()
        self.main_container.setObjectName("ContentContainer")  # To match new QSS
        self.main_container.setStyleSheet("""
            QWidget#ContentContainer {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #e5e7eb;
            }
        """)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(10, 10, 10, 10)

        # حقل البحث الذكي
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن أمر، فاتورة، عميل، أو إجراء... (Esc للإغلاق)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                background-color: #f9fafb;
                color: #1f2937;
                font-size: 16px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
        """)
        self.search_input.textChanged.connect(self.filter_commands)

        # قائمة النتائج
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #374151;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #2563eb;
            }
        """)
        self.results_list.itemActivated.connect(self.execute_command)

        container_layout.addWidget(self.search_input)
        container_layout.addWidget(self.results_list)

        layout.addWidget(self.main_container)

        # إضافة ظل للجمالية
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.main_container.setGraphicsEffect(shadow)

        self.commands = [
            {"name": "فاتورة جديدة", "action": "new_invoice", "icon": "🛒"},
            {"name": "إضافة منتج", "action": "add_product", "icon": "📦"},
            {"name": "تقرير المبيعات اليومي", "action": "daily_report", "icon": "📊"},
            {"name": "الوضع الليلي/النهاري", "action": "toggle_theme", "icon": "🌗"},
            {"name": "تحليل الذكاء الاصطناعي", "action": "ai_analyze", "icon": "🤖"},
            {"name": "إعدادات النظام", "action": "settings", "icon": "⚙️"},
            {"name": "خروج", "action": "exit", "icon": "❌"},
        ]
        # Try to load tracking data for sorting
        try:
            # We assume DB manager is not needed for just reading JSON in constructor for now
            # Or we pass it. For now, we will just read the JSON directly or create a dummy service
            # Simpler: Just read the JSON directly here to avoid dependency hell if DB is required Init
            import json
            import os

            behavior_data = {}
            if os.path.exists("data/user_behavior.json"):
                with open("data/user_behavior.json", "r", encoding="utf-8") as f:
                    behavior_data = json.load(f)

            actions_count = behavior_data.get("actions", {})

            # Sort commands by count (descending)
            def get_sort_key(cmd):
                # Map command action to tracking key (e.g. 'new_invoice' -> 'nav_sales' or exact match)
                # This is a loose mapping for now
                key = cmd["action"]
                return actions_count.get(key, 0)

            self.commands.sort(key=get_sort_key, reverse=True)

            # Mark top 3 as "🔥"
            for i in range(min(3, len(self.commands))):
                if get_sort_key(self.commands[i]) > 0:
                    self.commands[i]["name"] = f"🔥 {self.commands[i]['name']}"

        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in command_palette.py")

        self.filter_commands("")

        # التركيز على البحث مباشرة
        self.search_input.setFocus()

    def filter_commands(self, text):
        self.results_list.clear()
        for cmd in self.commands:
            if text.lower() in cmd["name"].lower():
                item = QListWidgetItem(f"{cmd['icon']}  {cmd['name']}")
                item.setData(Qt.UserRole, cmd["action"])
                self.results_list.addItem(item)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def execute_command(self, item):
        action = item.data(Qt.UserRole)
        self.command_selected.emit(action)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.results_list.currentItem():
                self.execute_command(self.results_list.currentItem())
        elif event.key() == Qt.Key_Down:
            idx = self.results_list.currentRow()
            if idx < self.results_list.count() - 1:
                self.results_list.setCurrentRow(idx + 1)
        elif event.key() == Qt.Key_Up:
            idx = self.results_list.currentRow()
            if idx > 0:
                self.results_list.setCurrentRow(idx - 1)
        else:
            super().keyPressEvent(event)

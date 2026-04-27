#!/usr/bin/env python3
"""
بحث محادثي - Conversational Search
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt


class ConversationalSearch(QWidget):
    """مكون البحث المحادثي"""

    def __init__(self, conversational_service=None, parent=None):
        super().__init__(parent)
        self.conversational_service = conversational_service
        self._setup_ui()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout()

        # عنوان
        title = QLabel("البحث المحادثي")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # منطقة النتائج
        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

        self.setLayout(layout)

    def search(self, query):
        """تنفيذ البحث"""
        if not self.conversational_service:
            self._show_message("خدمة المحادثة غير متاحة")
            return

        try:
            result = self.conversational_service.process_natural_language_query(query)
            self._display_results(result)
        except Exception as e:
            self._show_message(f"خطأ في البحث: {str(e)}")

    def _display_results(self, result):
        """عرض النتائج"""
        self.results_list.clear()

        # إضافة النتيجة الرئيسية
        main_item = QListWidgetItem(f"النتيجة: {result.explanation}")
        self.results_list.addItem(main_item)

        # إضافة الاقتراحات
        if result.suggested_actions:
            for suggestion in result.suggested_actions:
                suggestion_item = QListWidgetItem(f"اقتراح: {suggestion}")
                suggestion_item.setForeground(Qt.blue)
                self.results_list.addItem(suggestion_item)

    def _show_message(self, message):
        """عرض رسالة"""
        self.results_list.clear()
        item = QListWidgetItem(message)
        item.setForeground(Qt.red)
        self.results_list.addItem(item)
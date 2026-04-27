#!/usr/bin/env python3
"""
مكونات ذكية - AI Components
"""

from PySide6.QtWidgets import QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QWidget
from PySide6.QtCore import Signal


class AIButton(QPushButton):
    """زر ذكي"""
    ai_clicked = Signal(str)

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.clicked.connect(self._on_click)

    def _on_click(self):
        self.ai_clicked.emit("button_clicked")


class AIPromptInput(QLineEdit):
    """حقل إدخال ذكي"""
    ai_submitted = Signal(str)

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.returnPressed.connect(self._on_submit)

    def _on_submit(self):
        text = self.text()
        if text:
            self.ai_submitted.emit(text)
            self.clear()


class AIRichTextEditor(QTextEdit):
    """محرر نص غني ذكي"""
    ai_content_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        self.ai_content_changed.emit(self.toPlainText())





def create_ai_button(text="AI", parent=None):
    return AIButton(text, parent)


def create_ai_prompt_input(placeholder="اسألني أي شيء...", parent=None):
    return AIPromptInput(placeholder, parent)


def create_ai_rich_editor(placeholder="اكتب هنا...", parent=None):
    return AIRichTextEditor(placeholder, parent)
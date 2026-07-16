#!/usr/bin/env python3
"""
اختبارات AI Components
"""

import pytest
from PySide6.QtWidgets import QApplication, QWidget

from src.ui.components.ai_components import AIButton, AIPromptInput, AIRichTextEditor

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestAIButton:
    """اختبارات زر الذكاء الاصطناعي"""

    def test_initialization(self):
        """اختبار تهيئة الزر"""
        button = AIButton("Test Button")
        assert button is not None
        assert button.text() == "Test Button"

    def test_button_is_qwidget(self):
        """اختبار أن الزر من نوع QWidget"""
        button = AIButton("Test")
        assert isinstance(button, QWidget)


class TestAIPromptInput:
    """اختبارات حقل إدخال الأوامر"""

    def test_initialization(self):
        """اختبار تهيئة حقل الإدخال"""
        prompt_input = AIPromptInput()
        assert prompt_input is not None

    def test_prompt_input_is_qwidget(self):
        """اختبار أن حقل الإدخال من نوع QWidget"""
        prompt_input = AIPromptInput()
        assert isinstance(prompt_input, QWidget)

    def test_set_prompt(self):
        """اختبار تعيين نص الأمر"""
        prompt_input = AIPromptInput()
        prompt_input.setText("Test prompt")
        assert prompt_input.text() == "Test prompt"


class TestAIRichTextEditor:
    """اختبارات محرر النصوص المتقدم"""

    def test_initialization(self):
        """اختبار تهيئة المحرر"""
        editor = AIRichTextEditor()
        assert editor is not None

    def test_editor_is_qwidget(self):
        """اختبار أن المحرر من نوع QWidget"""
        editor = AIRichTextEditor()
        assert isinstance(editor, QWidget)

    def test_set_html_content(self):
        """اختبار تعيين محتوى HTML"""
        editor = AIRichTextEditor()
        editor.setHtml("<p>Test content</p>")
        assert "Test content" in editor.toPlainText()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

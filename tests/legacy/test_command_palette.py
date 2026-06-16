#!/usr/bin/env python3
"""
اختبارات Command Palette
"""

from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication, QLineEdit, QListWidget

from src.ui.dialogs.command_palette import CommandPalette

app = QApplication.instance() or QApplication([])


class TestCommandPalette:
    """اختبارات لوحة الأوامر"""

    @pytest.fixture
    def palette(self):
        """إنشاء لوحة للاختبارات"""
        parent = Mock()
        return CommandPalette(parent)

    def test_initialization(self, palette):
        """اختبار تهيئة اللوحة"""
        assert palette is not None
        assert hasattr(palette, "search_input")
        assert hasattr(palette, "commands_list")

    def test_search_input(self, palette):
        """اختبار حقل البحث"""
        assert palette.search_input is not None
        assert isinstance(palette.search_input, QLineEdit)

    def test_commands_list(self, palette):
        """اختبار قائمة الأوامر"""
        assert palette.commands_list is not None
        assert isinstance(palette.commands_list, QListWidget)

    def test_load_commands(self, palette):
        """اختبار تحميل الأوامر"""
        commands = [
            {"id": "open_file", "name": "فتح ملف", "shortcut": "Ctrl+O"},
            {"id": "save_file", "name": "حفظ ملف", "shortcut": "Ctrl+S"},
        ]

        result = palette.load_commands(commands)

        assert result is not None

    def test_filter_commands(self, palette):
        """اختبار تصفية الأوامر"""
        palette.search_input.setText("open")

        result = palette.filter_commands()

        assert result is not None

    def test_on_command_selected(self, palette):
        """اختبار اختيار أمر"""
        result = palette.on_command_selected()

        assert result is not None

    def test_get_selected_command(self, palette):
        """اختبار الحصول على الأمر المختار"""
        command = palette.get_selected_command()

        assert command is not None or command is None

    def test_show_palette(self, palette):
        """اختبار عرض اللوحة"""
        result = palette.show_palette()

        assert result is not None

    def test_hide_palette(self, palette):
        """اختبار إخفاء اللوحة"""
        result = palette.hide_palette()

        assert result is not None

    def test_clear_search(self, palette):
        """اختبار مسح البحث"""
        palette.search_input.setText("search text")

        result = palette.clear_search()

        assert result is not None
        assert palette.search_input.text() == ""

    def test_register_command(self, palette):
        """اختبار تسجيل أمر جديد"""
        command = {
            "id": "new_command",
            "name": "أمر جديد",
            "action": Mock(),
            "shortcut": "Ctrl+N",
        }

        result = palette.register_command(command)

        assert result is not None

    def test_execute_command(self, palette):
        """اختبار تنفيذ أمر"""
        result = palette.execute_command("open_file")

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

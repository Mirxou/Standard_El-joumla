#!/usr/bin/env python3
"""Tests for Shortcuts Manager"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.shortcuts_manager import ShortcutsManager

app = QApplication.instance() or QApplication([])


class TestShortcutsManager:
    @pytest.fixture
    def manager(self):
        return ShortcutsManager()

    def test_initialization(self, manager):
        assert manager is not None

    def test_register_shortcut(self, manager):
        result = manager.register_shortcut("Ctrl+S", "save", lambda: None)
        assert result is not None

    def test_unregister_shortcut(self, manager):
        manager.register_shortcut("Ctrl+S", "save", lambda: None)
        result = manager.unregister_shortcut("save")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

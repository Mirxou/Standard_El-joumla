#!/usr/bin/env python3
"""Tests for Quick Actions Toolbar"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.quick_actions_toolbar import QuickActionsToolbar

app = QApplication.instance() or QApplication([])


class TestQuickActionsToolbar:
    @pytest.fixture
    def toolbar(self):
        return QuickActionsToolbar()

    def test_initialization(self, toolbar):
        assert toolbar is not None

    def test_add_quick_action(self, toolbar):
        result = toolbar.add_quick_action("Save", lambda: None, "save_icon")
        assert result is not None

    def test_remove_quick_action(self, toolbar):
        toolbar.add_quick_action("Action", lambda: None)
        result = toolbar.remove_quick_action("Action")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

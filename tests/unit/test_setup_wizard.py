#!/usr/bin/env python3
"""Tests for Setup Wizard"""
import pytest
from unittest.mock import Mock, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.setup_wizard import SetupWizard

app = QApplication.instance() or QApplication([])

class TestSetupWizard:
    @pytest.fixture
    def wizard(self):
        mock_db = MagicMock()
        return SetupWizard(db_manager=mock_db)
    
    def test_initialization(self, wizard):
        assert wizard is not None
        assert wizard.db_manager is not None
    
    def test_next_page(self, wizard):
        # QWizard has a next() method
        result = wizard.next()
        assert result is None # next() returns None
    
    def test_previous_page(self, wizard):
        # QWizard has a back() method
        result = wizard.back()
        assert result is None # back() returns None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

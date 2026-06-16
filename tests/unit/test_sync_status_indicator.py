#!/usr/bin/env python3
"""Tests for Sync Status Indicator"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.sync_status_indicator import SyncStatusIndicator

app = QApplication.instance() or QApplication([])


class TestSyncStatusIndicator:
    @pytest.fixture
    def indicator(self):
        return SyncStatusIndicator()

    def test_initialization(self, indicator):
        assert indicator is not None

    def test_set_syncing(self, indicator):
        result = indicator.set_syncing(True)
        assert result is not None

    def test_set_sync_complete(self, indicator):
        result = indicator.set_sync_complete()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

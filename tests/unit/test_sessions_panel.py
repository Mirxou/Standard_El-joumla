#!/usr/bin/env python3
"""
اختبارات Sessions Panel
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.admin.sessions_panel import SessionsPanel

app = QApplication.instance() or QApplication([])

class TestSessionsPanel:
    """اختبارات لوحة الجلسات"""
    
    @pytest.fixture
    def panel(self):
        """إنشاء لوحة للاختبارات"""
        mock_db = MagicMock()
        with patch('src.ui.admin.sessions_panel.AuditLogService') as mock_audit:
            instance = mock_audit.return_value
            instance.get_active_sessions.return_value = [
                {"session_id": "1", "user_id": "admin", "ip_address": "127.0.0.1", "last_activity": "now", "is_active": True}
            ]
            return SessionsPanel(mock_db)
    
    def test_initialization(self, panel):
        """اختبار التهيئة"""
        assert panel is not None
        assert hasattr(panel, 'audit')
        assert hasattr(panel, 'table')
    
    def test_refresh(self, panel):
        """اختبار تحديث الجلسات"""
        panel.refresh()
        assert panel.table.rowCount() == 1
        assert panel.table.item(0, 0).text() == "1"
        assert panel.table.item(0, 4).text() == "نعم"
        
    def test_refresh_error(self, panel):
        """اختبار التحديث عند وجود خطأ"""
        panel.audit.get_active_sessions.side_effect = Exception("Test Error")
        panel.refresh()
        assert panel.table.rowCount() == 1
        assert panel.table.item(0, 0).text() == "خطأ"
        assert panel.table.item(0, 1).text() == "Test Error"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

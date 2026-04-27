#!/usr/bin/env python3
"""
اختبارات Webhook Management Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.webhook_management_window import WebhookManagementWindow

app = QApplication.instance() or QApplication([])


class TestWebhookManagementWindow:
    """اختبارات نافذة إدارة Webhook"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return WebhookManagementWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_webhooks(self, window):
        """اختبار تحميل Webhooks"""
        window.load_webhooks()
    
    def test_create_webhook(self, window):
        """اختبار إنشاء Webhook"""
        window.create_webhook("https://example.com/webhook", ["order.created"])
    
    def test_edit_webhook(self, window):
        """اختبار تعديل Webhook"""
        window.edit_webhook("webhook_id", {"url": "https://new.example.com"})
    
    def test_delete_webhook(self, window):
        """اختبار حذف Webhook"""
        window.delete_webhook("webhook_id")
    
    def test_enable_webhook(self, window):
        """اختبار تمكين Webhook"""
        window.enable_webhook("webhook_id", True)
    
    def test_test_webhook(self, window):
        """اختبار اختبار Webhook"""
        window.test_webhook("webhook_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




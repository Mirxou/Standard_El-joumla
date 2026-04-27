#!/usr/bin/env python3
"""
اختبارات AI Service UI
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

try:
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel
    from PySide6.QtCore import Qt
    from src.ui.ai_service_ui import AIServiceUI
    HAS_PYSIDE6 = True
    app = QApplication.instance() or QApplication([])
except ImportError:
    HAS_PYSIDE6 = False
    pytest.skip("PySide6 not installed", allow_module_level=True)


class TestAIServiceUI:
    """اختبارات واجهة خدمة الذكاء الاصطناعي"""
    
    @pytest.fixture
    def ui(self):
        """إنشاء واجهة للاختبارات"""
        ai_service = MagicMock()
        ai_service.get_recent_insights.return_value = []
        ai_service.get_all_ai_models.return_value = []
        ai_service.chat_with_ai.return_value = {"response": "Test", "confidence": 0.9}
        ai_service.analyze_image.return_value = {"result": "Test"}
        
        db_manager = MagicMock()
        ui = AIServiceUI(ai_service)
        ui.db_manager = db_manager
        return ui
    
    def test_initialization(self, ui):
        """اختبار التهيئة"""
        assert ui is not None
        assert hasattr(ui, 'ai_service')
    
    def test_service_connection(self, ui):
        """اختبار اتصال الخدمة"""
        result = ui.connect_to_service()
        assert result is not None
    
    def test_disconnect_service(self, ui):
        """اختبار قطع الاتصال"""
        result = ui.disconnect_service()
        assert result is not None
    
    def test_send_request(self, ui):
        """اختبار إرسال طلب"""
        ui.input_text.setPlainText("Test query")
        result = ui.send_request()
        assert result is not None
    
    def test_display_response(self, ui):
        """اختبار عرض الرد"""
        response = {"result": "Test response", "confidence": 0.95}
        result = ui.display_response(response)
        assert result is not None
    
    def test_clear_input(self, ui):
        """اختبار مسح الإدخال"""
        ui.input_text.setPlainText("Test text")
        ui.clear_input()
        assert ui.input_text.toPlainText() == ""
    
    def test_show_loading(self, ui):
        """اختبار إظهار التحميل"""
        result = ui.show_loading(True)
        assert result is not None
    
    def test_get_service_status(self, ui):
        """اختبار الحصول على حالة الخدمة"""
        status = ui.get_service_status()
        assert isinstance(status, dict)
    
    def test_configure_service(self, ui):
        """اختبار تكوين الخدمة"""
        config = {"model": "gpt-4", "temperature": 0.7}
        result = ui.configure_service(config)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




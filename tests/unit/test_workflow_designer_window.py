#!/usr/bin/env python3
"""
اختبارات Workflow Designer Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.workflow_designer_window import WorkflowDesignerWindow

app = QApplication.instance() or QApplication([])


class TestWorkflowDesignerWindow:
    """اختبارات نافذة مصمم سير العمل"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return WorkflowDesignerWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_workflows(self, window):
        """اختبار تحميل سير العمل"""
        window.load_workflows()
    
    def test_create_workflow(self, window):
        """اختبار إنشاء سير عمل"""
        window.create_workflow()
    
    def test_add_workflow_step(self, window):
        """اختبار إضافة خطوة لسير العمل"""
        window.add_workflow_step("workflow_id", {"name": "Approval", "type": "approval"})
    
    def test_connect_steps(self, window):
        """اختبار ربط الخطوات"""
        window.connect_steps("workflow_id", "step_1", "step_2")
    
    def test_save_workflow(self, window):
        """اختبار حفظ سير العمل"""
        window.save_workflow("workflow_id")
    
    def test_activate_workflow(self, window):
        """اختبار تفعيل سير العمل"""
        window.activate_workflow("workflow_id", True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




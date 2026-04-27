import pytest
import os

# Ensure Qt runs in offscreen mode for headless test environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from unittest.mock import Mock, MagicMock

# اجعل كل عناصر Mock قابلة للتكرار (ترجع قائمة فارغة) لتجنب أخطاء "Mock is not iterable"


# تعطيل الحوارات التي تمنع تنفيذ الاختبارات (blocking dialogs)
from PySide6.QtWidgets import QDialog, QMessageBox

def mock_exec(self):
    return QDialog.Accepted

QDialog.exec = mock_exec
QDialog.exec_ = mock_exec

QMessageBox.information = MagicMock(return_value=QMessageBox.Ok)
QMessageBox.warning = MagicMock(return_value=QMessageBox.Ok)
QMessageBox.critical = MagicMock(return_value=QMessageBox.Ok)
QMessageBox.question = MagicMock(return_value=QMessageBox.Yes)
 
import logging

def fail_on_error(self, msg, *args, **kwargs):
    # Format message like the logger would
    try:
        if args:
            formatted_msg = msg % args
        else:
            formatted_msg = msg
    except:
        formatted_msg = msg
    pytest.fail(f"Application logged an ERROR in {self.name}: {formatted_msg}")

# Monkey-patch the base Logger class to catch ALL loggers
logging.Logger.error = fail_on_error
logging.Logger.critical = fail_on_error

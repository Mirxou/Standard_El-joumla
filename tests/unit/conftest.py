import os
import logging

import pytest

# Ensure Qt runs in offscreen mode for headless test environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from unittest.mock import MagicMock

# تعطيل الحوارات التي تمنع تنفيذ الاختبارات (blocking dialogs)
from PySide6.QtWidgets import QDialog, QMessageBox

# اجعل كل عناصر Mock قابلة للتكرار (ترجع قائمة فارغة) لتجنب أخطاء "Mock is not iterable"


def mock_exec(self):
    return QDialog.Accepted


QDialog.exec = mock_exec
QDialog.exec_ = mock_exec

QMessageBox.information = MagicMock(return_value=QMessageBox.Ok)
QMessageBox.warning = MagicMock(return_value=QMessageBox.Ok)
QMessageBox.critical = MagicMock(return_value=QMessageBox.Ok)
QMessageBox.question = MagicMock(return_value=QMessageBox.Yes)

_original_error = logging.Logger.error
_original_critical = logging.Logger.critical

def fail_on_error(self, msg, *args, **kwargs):
    # Suppress fail_on_error for logger-testing and database operations loggers
    if "test_" in self.name or self.name in ("database_operations", "src.utils.logger"):
        return _original_error(self, msg, *args, **kwargs)

    # Format message like the logger would
    try:
        if args:
            formatted_msg = msg % args
        else:
            formatted_msg = msg
    except Exception:
        formatted_msg = msg
    pytest.fail(f"Application logged an ERROR in {self.name}: {formatted_msg}")


# Monkey-patch the base Logger class to catch ALL loggers
logging.Logger.error = fail_on_error
logging.Logger.critical = fail_on_error


def pytest_sessionfinish(session, exitstatus):
    """Clean exit on successful test session to bypass PySide6's access violation on headless teardown."""
    if exitstatus == 0:
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.closeAllWindows()
                app.processEvents()
        except Exception:
            pass
        import sys
        sys.exit(0)


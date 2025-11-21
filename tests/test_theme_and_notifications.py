import os
import json
import time
import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

from src.ui.theme_manager import get_theme_manager
from src.ui.notifications_manager import SmartNotificationsManager, Notification, NotificationType


@pytest.fixture(scope="module")
def qapp():
    # Minimal Qt app for QSettings usage
    app = QApplication.instance() or QApplication([])
    yield app


def test_theme_toggle_persists(qapp):
    tm = get_theme_manager()
    orig = tm.get_current_theme()
    new_theme = tm.toggle_theme()
    assert new_theme in ("light", "dark")

    # Ensure a second manager sees the saved value
    tm2 = get_theme_manager()
    assert tm2.get_current_theme() == new_theme

    # Restore
    tm.apply_theme(orig)


def test_notifications_persist(qapp, tmp_path):
    # Use a temp QSettings scope
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    s = QSettings('LogicalVersion', 'ERP')

    # Create manager (no DB needed for persistence path)
    mgr = SmartNotificationsManager(db_manager=None, main_window=None)
    mgr.notifications.clear()

    n = Notification(
        id="test_1",
        type=NotificationType.INFO,
        title="Test",
        message="Message",
        timestamp=__import__('datetime').datetime.now(),
    )
    mgr.add_notification(n)

    # Ensure value written
    raw = s.value('notifications', '[]')
    data = json.loads(raw)
    assert any(item.get('id') == 'test_1' for item in data)

    # Reload
    mgr2 = SmartNotificationsManager(db_manager=None, main_window=None)
    assert any(n2.id == 'test_1' for n2 in mgr2.get_all_notifications())

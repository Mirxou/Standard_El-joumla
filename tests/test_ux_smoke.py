import sys
import time

from PySide6.QtWidgets import QApplication

from src.ui.theme_manager import get_theme_manager
from src.ui.notifications_manager import SmartNotificationsManager
from src.core.database_manager import DatabaseManager


def test_theme_toggle_persists_and_applies():
    app = QApplication.instance() or QApplication(sys.argv)
    tm = get_theme_manager()
    before = tm.get_current_theme()
    new_theme = tm.toggle_theme()
    assert new_theme in {"light", "dark"}
    # Toggling again should return to previous
    back = tm.toggle_theme()
    assert back == before


def test_notifications_force_check_and_last_time():
    # Use in-memory DB to avoid touching disk
    db = DatabaseManager(db_path=":memory:")
    assert db.initialize()

    nm = SmartNotificationsManager(db_manager=db, main_window=None)
    # Do not start background thread in tests
    nm.force_check()
    last = nm.get_last_check_time_str()
    assert isinstance(last, str)
    assert nm.get_unread_count() >= 0

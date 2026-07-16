"""
Style Manager - نظام إدارة المظهر الموحد
Provides a single, high-professional dark theme (Quantum Dark) for the entire system.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class StyleManager:
    """
    مدير المظهر الموحد - يطبق سمة Quantum Dark بشكل دائم.
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.qss_path = self.project_root / "src" / "ui" / "styles" / "modern_glass.qss"

    def get_stylesheet(self) -> str:
        """تحميل وقراءة ملف الأنماط الرئيسي"""
        if not self.qss_path.exists():
            return ""

        try:
            with open(self.qss_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def apply_theme(self):
        """تطبيق السمة الداكنة على التطبيق بالكامل"""
        app = QApplication.instance()
        if not app:
            return

        # 1. تطبيق لوحة الألوان الداكنة (Dark Palette) لتحسين مظهر النوافذ الأصلية
        palette = QPalette()
        dark_bg = QColor("#020617")
        surface = QColor("#1e293b")
        cyan = QColor("#00f3ff")
        white = QColor("#ffffff")

        palette.setColor(QPalette.Window, dark_bg)
        palette.setColor(QPalette.WindowText, white)
        palette.setColor(QPalette.Base, surface)
        palette.setColor(QPalette.AlternateBase, dark_bg)
        palette.setColor(QPalette.ToolTipBase, dark_bg)
        palette.setColor(QPalette.ToolTipText, white)
        palette.setColor(QPalette.Text, white)
        palette.setColor(QPalette.Button, surface)
        palette.setColor(QPalette.ButtonText, white)
        palette.setColor(QPalette.Highlight, cyan)
        palette.setColor(QPalette.HighlightedText, dark_bg)

        app.setPalette(palette)

        # 2. تطبيق ملف QSS
        stylesheet = self.get_stylesheet()
        if stylesheet:
            app.setStyleSheet(stylesheet)


# Global Singleton instance
_style_manager: Optional[StyleManager] = None


def get_style_manager() -> StyleManager:
    """الحصول على مدير المظهر العام"""
    global _style_manager
    if _style_manager is None:
        _style_manager = StyleManager()
    return _style_manager


# Alias for backward compatibility during transition
def get_modern_theme():
    return get_style_manager()

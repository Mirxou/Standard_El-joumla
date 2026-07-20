"""
Style Manager — نظام إدارة المظهر الموحد
Provides the AURORA NOIR v4.0 theme for the entire Standard El-Joumla ERP system.
Deep Noir + Emerald Gold accents — world-class Arabic financial ERP.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from src.ui.styles.design_tokens import C  # Design tokens (Aurora Noir)


class StyleManager:
    """
    مدير المظهر الموحد — يطبق سمة Aurora Noir v4.0 بشكل دائم.
    Uses design tokens from design_tokens.py for palette consistency.
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

    def _build_palette(self) -> QPalette:
        """Build QPalette from Aurora Noir v4.0 design tokens."""
        palette = QPalette()

        palette.setColor(QPalette.Window,          QColor(C.BG_DEEP))
        palette.setColor(QPalette.WindowText,      QColor(C.TEXT_PRIMARY))
        palette.setColor(QPalette.Base,            QColor(C.BG_RAISED))
        palette.setColor(QPalette.AlternateBase,   QColor(C.BG_PRIMARY))
        palette.setColor(QPalette.ToolTipBase,     QColor(C.BG_ELEVATED))
        palette.setColor(QPalette.ToolTipText,     QColor(C.TEXT_PRIMARY))
        palette.setColor(QPalette.Text,            QColor(C.TEXT_PRIMARY))
        palette.setColor(QPalette.Button,          QColor(C.BG_RAISED))
        palette.setColor(QPalette.ButtonText,      QColor(C.TEXT_PRIMARY))
        palette.setColor(QPalette.Highlight,       QColor(C.ACCENT_GOLD))
        palette.setColor(QPalette.HighlightedText, QColor(C.TEXT_INVERSE))

        return palette

    def apply_theme(self):
        """تطبيق سمة Aurora Noir v4.0 على التطبيق بالكامل"""
        app = QApplication.instance()
        if not app:
            return

        # 1. Set dark palette from design tokens (covers native dialogs, etc.)
        app.setPalette(self._build_palette())

        # 2. Apply QSS stylesheet
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
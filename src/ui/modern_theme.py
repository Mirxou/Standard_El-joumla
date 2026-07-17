"""
Style Manager — نظام إدارة المظهر الموحد
Provides a single, world-class dark theme (Royal Dark v2.0) with gold accents
for the entire Standard El-Joumla ERP system.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from src.ui.styles.design_tokens import C  # Design tokens (Colors, etc.)


class StyleManager:
    """
    مدير المظهر الموحد — يطبق سمة Royal Dark v2.0 بشكل دائم.
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
        """Build QPalette from design tokens for native widget consistency."""
        palette = QPalette()

        palette.setColor(QPalette.Window,          QColor(C.BG_VOID))
        palette.setColor(QPalette.WindowText,      QColor(C.TEXT_PRIMARY))
        palette.setColor(QPalette.Base,            QColor(C.BG_TERTIARY))
        palette.setColor(QPalette.AlternateBase,   QColor(C.BG_PRIMARY))
        palette.setColor(QPalette.ToolTipBase,     QColor(C.BG_SECONDARY))
        palette.setColor(QPalette.ToolTipText,     QColor(C.TEXT_PRIMARY))
        palette.setColor(QPalette.Text,            QColor(C.TEXT_PRIMARY))
        palette.setColor(QPalette.Button,          QColor(C.BG_TERTIARY))
        palette.setColor(QPalette.ButtonText,      QColor(C.TEXT_PRIMARY))
        palette.setColor(QPalette.Highlight,       QColor(C.ACCENT_GOLD))
        palette.setColor(QPalette.HighlightedText, QColor(C.TEXT_INVERSE))

        return palette

    def apply_theme(self):
        """تطبيق السمة الداكنة على التطبيق بالكامل"""
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
"""
Theme Manager - نظام إدارة السمات
Provides Dark/Light theme switching with smooth transitions
"""

from typing import Optional, Dict
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QSettings


class Theme:
    """تعريف سمة واحدة"""
    
    def __init__(self, name: str, stylesheet: str, palette: Optional[QPalette] = None):
        self.name = name
        self.stylesheet = stylesheet
        self.palette = palette


class ThemeManager:
    """
    مدير السمات
    
    Features:
    - Dark/Light themes
    - Smooth transitions
    - Persistent settings
    - Custom color schemes
    """
    
    # Light Theme Colors
    LIGHT_COLORS = {
        'primary': '#2196F3',
        'primary_dark': '#1976D2',
        'primary_light': '#BBDEFB',
        'accent': '#FF9800',
        'background': '#FFFFFF',
        'surface': '#F5F5F5',
        'text_primary': '#212121',
        'text_secondary': '#757575',
        'border': '#E0E0E0',
        'success': '#4CAF50',
        'warning': '#FF9800',
        'error': '#F44336',
        'info': '#2196F3',
    }
    
    # Dark Theme Colors
    DARK_COLORS = {
        'primary': '#2196F3',
        'primary_dark': '#1565C0',
        'primary_light': '#42A5F5',
        'accent': '#FF9800',
        'background': '#1E1E1E',
        'surface': '#2D2D2D',
        'text_primary': '#E0E0E0',
        'text_secondary': '#B0B0B0',
        'border': '#3E3E3E',
        'success': '#66BB6A',
        'warning': '#FFA726',
        'error': '#EF5350',
        'info': '#42A5F5',
    }
    
    def __init__(self):
        self.settings = QSettings('LogicalVersion', 'ERP')
        self.current_theme = self.settings.value('theme', 'light')
        
    def get_light_theme(self) -> Theme:
        """السمة الفاتحة"""
        colors = self.LIGHT_COLORS
        
        stylesheet = f"""
        /* Global Styles */
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            font-family: 'Segoe UI', Tahoma, sans-serif;
            font-size: 10pt;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors['border']};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['primary_light']};
            color: {colors['primary_dark']};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        /* Menus */
        QMenu {{
            background-color: {colors['background']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
            margin: 2px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors['primary_light']};
            color: {colors['primary_dark']};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {colors['border']};
            margin: 4px 8px;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['primary_dark']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['primary_light']};
        }}
        
        QPushButton:disabled {{
            background-color: {colors['border']};
            color: {colors['text_secondary']};
        }}
        
        /* Secondary Button */
        QPushButton[class="secondary"] {{
            background-color: transparent;
            color: {colors['primary']};
            border: 2px solid {colors['primary']};
        }}
        
        QPushButton[class="secondary"]:hover {{
            background-color: {colors['primary_light']};
        }}
        
        /* Tables */
        QTableWidget, QTableView {{
            background-color: {colors['background']};
            alternate-background-color: {colors['surface']};
            gridline-color: {colors['border']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
        }}
        
        QTableWidget::item, QTableView::item {{
            padding: 8px;
            border: none;
        }}
        
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {colors['primary_light']};
            color: {colors['primary_dark']};
        }}
        
        QHeaderView::section {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            padding: 10px;
            border: none;
            border-bottom: 2px solid {colors['primary']};
            font-weight: 600;
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            border: 2px solid {colors['border']};
            border-radius: 6px;
            padding: 8px;
            selection-background-color: {colors['primary_light']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {colors['primary']};
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            border: 2px solid {colors['border']};
            border-radius: 6px;
            padding: 8px;
            min-height: 32px;
        }}
        
        QComboBox:hover {{
            border-color: {colors['primary_light']};
        }}
        
        QComboBox:focus {{
            border-color: {colors['primary']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            padding-right: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors['background']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            selection-background-color: {colors['primary_light']};
            padding: 4px;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            border-radius: 6px;
            background-color: {colors['background']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['surface']};
            color: {colors['text_secondary']};
            border: none;
            padding: 12px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['background']};
            color: {colors['primary']};
            font-weight: 600;
            border-bottom: 3px solid {colors['primary']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {colors['primary_light']};
        }}
        
        /* Scrollbars */
        QScrollBar:vertical {{
            background-color: {colors['surface']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['border']};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['text_secondary']};
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors['surface']};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors['border']};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors['text_secondary']};
        }}
        
        /* Group Box */
        QGroupBox {{
            border: 2px solid {colors['border']};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: 600;
        }}
        
        QGroupBox::title {{
            color: {colors['primary']};
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {colors['surface']};
            border: 2px solid {colors['border']};
            border-radius: 6px;
            text-align: center;
            height: 24px;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['primary']};
            border-radius: 4px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {colors['surface']};
            color: {colors['text_secondary']};
            border-top: 1px solid {colors['border']};
        }}
        
        /* Tool Tip */
        QToolTip {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 8px;
        }}
        """
        
        return Theme('light', stylesheet)
    
    def get_dark_theme(self) -> Theme:
        """السمة الداكنة"""
        colors = self.DARK_COLORS
        
        stylesheet = f"""
        /* Global Styles */
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            font-family: 'Segoe UI', Tahoma, sans-serif;
            font-size: 10pt;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors['border']};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        QMenuBar::item:pressed {{
            background-color: {colors['primary_dark']};
        }}
        
        /* Menus */
        QMenu {{
            background-color: {colors['surface']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
            margin: 2px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {colors['border']};
            margin: 4px 8px;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['primary_light']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['primary_dark']};
        }}
        
        QPushButton:disabled {{
            background-color: {colors['border']};
            color: {colors['text_secondary']};
        }}
        
        /* Secondary Button */
        QPushButton[class="secondary"] {{
            background-color: transparent;
            color: {colors['primary_light']};
            border: 2px solid {colors['primary']};
        }}
        
        QPushButton[class="secondary"]:hover {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        /* Tables */
        QTableWidget, QTableView {{
            background-color: {colors['background']};
            alternate-background-color: {colors['surface']};
            gridline-color: {colors['border']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
        }}
        
        QTableWidget::item, QTableView::item {{
            padding: 8px;
            border: none;
            color: {colors['text_primary']};
        }}
        
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        QHeaderView::section {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            padding: 10px;
            border: none;
            border-bottom: 2px solid {colors['primary']};
            font-weight: 600;
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border: 2px solid {colors['border']};
            border-radius: 6px;
            padding: 8px;
            selection-background-color: {colors['primary']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {colors['primary']};
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border: 2px solid {colors['border']};
            border-radius: 6px;
            padding: 8px;
            min-height: 32px;
        }}
        
        QComboBox:hover {{
            border-color: {colors['primary']};
        }}
        
        QComboBox:focus {{
            border-color: {colors['primary_light']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            padding-right: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors['surface']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            selection-background-color: {colors['primary']};
            padding: 4px;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            border-radius: 6px;
            background-color: {colors['background']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['surface']};
            color: {colors['text_secondary']};
            border: none;
            padding: 12px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['background']};
            color: {colors['primary_light']};
            font-weight: 600;
            border-bottom: 3px solid {colors['primary']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        /* Scrollbars */
        QScrollBar:vertical {{
            background-color: {colors['surface']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['border']};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['text_secondary']};
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors['surface']};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors['border']};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors['text_secondary']};
        }}
        
        /* Group Box */
        QGroupBox {{
            border: 2px solid {colors['border']};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: 600;
            color: {colors['text_primary']};
        }}
        
        QGroupBox::title {{
            color: {colors['primary_light']};
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {colors['surface']};
            border: 2px solid {colors['border']};
            border-radius: 6px;
            text-align: center;
            height: 24px;
            color: {colors['text_primary']};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['primary']};
            border-radius: 4px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {colors['surface']};
            color: {colors['text_secondary']};
            border-top: 1px solid {colors['border']};
        }}
        
        /* Tool Tip */
        QToolTip {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 8px;
        }}
        """
        
        return Theme('dark', stylesheet)
    
    def apply_theme(self, theme_name: str = 'light'):
        """
        تطبيق سمة
        
        Args:
            theme_name: 'light' or 'dark'
        """
        app = QApplication.instance()
        if not app:
            return
        
        if theme_name == 'dark':
            theme = self.get_dark_theme()
        else:
            theme = self.get_light_theme()
        
        # Apply stylesheet
        app.setStyleSheet(theme.stylesheet)
        
        # Save preference
        self.current_theme = theme_name
        self.settings.setValue('theme', theme_name)
    
    def toggle_theme(self):
        """تبديل السمة"""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme(new_theme)
        return new_theme
    
    def get_current_theme(self) -> str:
        """الحصول على السمة الحالية"""
        return self.current_theme


# Global instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """الحصول على مدير السمات العام"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager

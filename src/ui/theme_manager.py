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
    
    # Dark Theme Colors - مطابقة لتطبيق الويب
    DARK_COLORS = {
        'primary': '#06b6d4',  # Electric Cyan - مطابق للويب
        'primary_dark': '#0891b2',  # Darker Cyan
        'primary_light': '#22d3ee',  # Lighter Cyan
        'accent': '#a855f7',  # Neon Purple - مطابق للويب
        'accent_dark': '#9333ea',  # Darker Purple
        'accent_light': '#c084fc',  # Lighter Purple
        'background': '#0f172a',  # Deep Charcoal - مطابق للويب
        'surface': '#1e293b',  # Slate 800
        'surface_light': '#334155',  # Slate 700
        'text_primary': '#f8fafc',  # Almost White - مطابق للويب
        'text_secondary': '#cbd5e1',  # Slate 300
        'text_muted': '#94a3b8',  # Slate 400
        'border': '#1e293b',  # Slate 800 with opacity
        'border_light': 'rgba(255, 255, 255, 0.1)',  # White with 10% opacity
        'success': '#10b981',  # Emerald 500
        'warning': '#f59e0b',  # Amber 500
        'error': '#ef4444',  # Red 500
        'info': '#06b6d4',  # Cyan 500
        'glass_bg': 'rgba(255, 255, 255, 0.05)',  # Glass effect background
        'glass_border': 'rgba(255, 255, 255, 0.1)',  # Glass effect border
    }

    # Vision 2030 Theme Colors
    VISION_COLORS = {
        'primary': '#3b82f6',
        'primary_gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb)',
        'background': '#f3f4f6',
        'surface': '#ffffff',
        'text': '#1f2937'
    }

    # Luxury Corporate Colors (UI/UX Pro Max)
    LUXURY_COLORS = {
        'primary': '#2563eb',     # blue-600
        'primary_dark': '#1d4ed8',# blue-700
        'primary_light': '#bfdbfe',# blue-200
        'accent': '#f97316',      # orange-500
        'background': '#f8fafc',  # slate-50
        'surface': '#ffffff',     # white
        'text_primary': '#1e293b',# slate-800
        'text_secondary': '#475569',# slate-600
        'border': '#e2e8f0',      # slate-200
    }
    
    def __init__(self):
        self.settings = QSettings('LogicalVersion', 'ERP')
        # Default to light theme for Universal look, use new key to force reset
        self.current_theme = self.settings.value('theme_mode_v2', 'light')
        
    def get_light_theme(self) -> Theme:
        """السمة الفاتحة - Universal Light"""
        from pathlib import Path
        
        # محاولة تحميل ملف QSS الحديث
        qss_path = Path(__file__).parent / "styles" / "modern_light.qss"
        if qss_path.exists():
            try:
                with open(qss_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                return Theme('light', stylesheet)
            except Exception as e:
                print(f"Error loading modern_light.qss: {e}")
        
        colors = self.LIGHT_COLORS
        
        stylesheet = f"""
        /* Global Styles */
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
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

    def get_vision_theme(self) -> Theme:
        """السمة الحديثة - Vision 2030"""
        from pathlib import Path
        
        qss_path = Path(__file__).parent / "styles" / "vision_2030.qss"
        if qss_path.exists():
            try:
                with open(qss_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                return Theme('vision', stylesheet)
            except Exception as e:
                print(f"Error loading vision_2030.qss: {e}")
        
        # Fallback
        return self.get_light_theme()

    def get_luxury_theme(self) -> Theme:
        """السمة الفاخرة - Luxury Corporate / Soft Minimalism"""
        from pathlib import Path
        
        qss_path = Path(__file__).parent / "styles" / "luxury_corporate.qss"
        if qss_path.exists():
            try:
                with open(qss_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                return Theme('luxury', stylesheet)
            except Exception as e:
                print(f"Error loading luxury_corporate.qss: {e}")
        
        # Fallback
        return self.get_light_theme()
    
    def get_dark_theme(self) -> Theme:
        """السمة الداكنة - Modern Glass"""
        from pathlib import Path
        
        # محاولة تحميل ملف QSS الحديث
        qss_path = Path(__file__).parent / "styles" / "modern_glass.qss"
        if qss_path.exists():
            try:
                with open(qss_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                return Theme('dark', stylesheet)
            except Exception as e:
                print(f"Error loading modern_glass.qss: {e}")
        
        # Fallback to legacy style if file not found
        colors = self.DARK_COLORS
        stylesheet = f"""
        /* Global Styles */
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
            font-size: 10pt;
        }}
        /* ... (rest of legacy inline style omitted for brevity, fallback only) ... */
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
        elif theme_name == 'vision':
            theme = self.get_vision_theme()
        elif theme_name == 'luxury':
            theme = self.get_luxury_theme()
        else:
            theme = self.get_light_theme()
        
        # Apply stylesheet
        app.setStyleSheet(theme.stylesheet)
        
        # Save preference
        self.current_theme = theme_name
        self.settings.setValue('theme_mode_v2', theme_name)
    
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

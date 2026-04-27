#!/usr/bin/env python3
"""
Modern Theme System - نظام تصميم حديث
Professional UI/UX Design System for Desktop Application
Based on Glassmorphism, Neumorphism, and Modern Design Principles
"""

from typing import Optional, Dict, Tuple
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QFrame, QLabel
from PySide6.QtGui import QColor, QPalette, QLinearGradient, QBrush, QFont, QFontDatabase, QPainter, QPaintEvent
from PySide6.QtCore import Qt, QSettings, QTimer, QPropertyAnimation, QEasingCurve, Signal, QObject


class ModernTheme(QObject):
    """
    نظام التصميم الحديث
    Features:
    - Glassmorphism effects
    - Neumorphism depth
    - Smooth animations
    - WCAG 2.1 AA compliant colors
    """
    
    theme_changed = Signal(str)
    
    # Color Palette - Professional Dashboard (Palette #18 from skiLL)
    COLORS = {
        # Primary - Electric Cyan
        'primary': '#06b6d4',
        'primary_dark': '#0891b2',
        'primary_light': '#22d3ee',
        'primary_50': '#ecfeff',
        'primary_100': '#cffafe',
        
        # Accent - Neon Purple
        'accent': '#a855f7',
        'accent_dark': '#9333ea',
        'accent_light': '#c084fc',
        
        # Background - Deep Charcoal
        'bg_primary': '#0f172a',
        'bg_secondary': '#1e293b',
        'bg_tertiary': '#334155',
        'bg_card': 'rgba(30, 41, 59, 0.7)',
        
        # Glass Effect
        'glass_bg': 'rgba(255, 255, 255, 0.05)',
        'glass_border': 'rgba(255, 255, 255, 0.1)',
        'glass_blur': 'blur(20px)',
        
        # Text
        'text_primary': '#f8fafc',
        'text_secondary': '#cbd5e1',
        'text_muted': '#94a3b8',
        'text_inverse': '#0f172a',
        
        # Status
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'info': '#06b6d4',
        
        # Borders
        'border': 'rgba(255, 255, 255, 0.1)',
        'border_strong': 'rgba(255, 255, 255, 0.2)',
        
        # Gold Series (for premium elements)
        'gold': '#D4AF37',
        'gold_light': '#F4E4A6',
    }
    
    # Typography Scale
    TYPOGRAPHY = {
        'font_family': 'Segoe UI, SF Pro Display, -apple-system, sans-serif',
        'font_arabic': 'Segoe UI, Dubai, Arial, sans-serif',
        
        # Sizes (px)
        'h1': 32,
        'h2': 24,
        'h3': 20,
        'h4': 18,
        'body': 14,
        'small': 12,
        'caption': 11,
        
        # Weights
        'weight_normal': 400,
        'weight_medium': 500,
        'weight_semibold': 600,
        'weight_bold': 700,
    }
    
    # Spacing Scale
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 16,
        'lg': 24,
        'xl': 32,
        'xxl': 48,
    }
    
    # Border Radius
    RADIUS = {
        'sm': 6,
        'md': 12,
        'lg': 16,
        'xl': 24,
        'full': 9999,
    }
    
    # Animation Durations (ms)
    ANIMATION = {
        'fast': 150,
        'normal': 250,
        'slow': 350,
    }
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark'
        self.settings = QSettings('LogicalERP', 'Theme')
        self.animations = []
        self._load_fonts()
    
    def _load_fonts(self):
        """تحميل الخطوط المخصصة"""
        # Load Google Fonts if available
        font_db = QFontDatabase()
        # Add any custom fonts here
    
    def get_stylesheet(self) -> str:
        """الحصول على CSS stylesheet كامل"""
        c = self.COLORS
        t = self.TYPOGRAPHY
        r = self.RADIUS
        
        return f"""
        /* ===== Global Styles ===== */
        QWidget {{
            font-family: {t['font_arabic']};
            font-size: {t['body']}px;
            color: {c['text_primary']};
        }}
        
        QMainWindow {{
            background: {c['bg_primary']};
            border: none;
        }}
        
        /* ===== Glassmorphism Cards ===== */
        QFrame[class="glass-card"] {{
            background: {c['glass_bg']};
            border: 1px solid {c['glass_border']};
            border-radius: {r['lg']}px;
        }}
        
        /* ===== Neumorphism Buttons ===== */
        QPushButton[class="neumorphism"] {{
            background: {c['bg_secondary']};
            border: none;
            border-radius: {r['md']}px;
            padding: 12px 24px;
            color: {c['text_primary']};
            font-weight: {t['weight_semibold']};
        }}
        
        QPushButton[class="neumorphism"]:hover {{
            background: {c['bg_tertiary']};
        }}
        
        QPushButton[class="neumorphism"]:pressed {{
            background: {c['primary']};
        }}
        
        /* ===== Primary Button (Glow Effect) ===== */
        QPushButton[class="primary-glow"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {c['primary']}, stop:1 {c['accent']});
            border: none;
            border-radius: {r['md']}px;
            padding: 12px 24px;
            color: white;
            font-weight: {t['weight_bold']};
        }}
        
        QPushButton[class="primary-glow"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {c['primary_light']}, stop:1 {c['accent_light']});
        }}
        
        /* ===== KPI Cards ===== */
        QFrame[class="kpi-card"] {{
            background: {c['glass_bg']};
            border: 1px solid {c['glass_border']};
            border-radius: {r['lg']}px;
            padding: 20px;
        }}
        
        QFrame[class="kpi-card-success"] {{
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: {r['lg']}px;
            padding: 20px;
        }}
        
        QFrame[class="kpi-card-warning"] {{
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: {r['lg']}px;
            padding: 20px;
        }}
        
        /* ===== Typography ===== */
        QLabel[class="h1"] {{
            font-size: {t['h1']}px;
            font-weight: {t['weight_bold']};
            color: {c['text_primary']};
        }}
        
        QLabel[class="h2"] {{
            font-size: {t['h2']}px;
            font-weight: {t['weight_semibold']};
            color: {c['text_primary']};
        }}
        
        QLabel[class="h3"] {{
            font-size: {t['h3']}px;
            font-weight: {t['weight_semibold']};
            color: {c['text_secondary']};
        }}
        
        QLabel[class="caption"] {{
            font-size: {t['caption']}px;
            color: {c['text_muted']};
        }}
        
        /* ===== Scrollbars ===== */
        QScrollBar:vertical {{
            background: {c['bg_secondary']};
            width: 8px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {c['border_strong']};
            border-radius: 4px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {c['text_muted']};
        }}
        
        /* ===== Input Fields ===== */
        QLineEdit, QTextEdit, QComboBox {{
            background: {c['glass_bg']};
            border: 1px solid {c['border']};
            border-radius: {r['md']}px;
            padding: 8px 12px;
            color: {c['text_primary']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 2px solid {c['primary']};
        }}
        
        /* ===== Tables ===== */
        QTableWidget {{
            background: transparent;
            border: 1px solid {c['border']};
            border-radius: {r['md']}px;
            gridline-color: {c['border']};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {c['border']};
        }}
        
        QTableWidget::item:selected {{
            background: {c['primary']};
            color: white;
        }}
        
        QHeaderView::section {{
            background: {c['bg_secondary']};
            color: {c['text_secondary']};
            padding: 10px;
            border: none;
            border-bottom: 2px solid {c['primary']};
            font-weight: {t['weight_semibold']};
        }}
        """
    
    def apply_theme(self, widget: QWidget = None):
        """تطبيق الثيم على التطبيق"""
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.get_stylesheet())
        
        # Apply palette
        self._apply_palette(app)
        
        self.theme_changed.emit(self.current_theme)
    
    def _apply_palette(self, app: QApplication):
        """تطبيق لوحة الألوان"""
        c = self.COLORS
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(c['bg_primary']))
        palette.setColor(QPalette.WindowText, QColor(c['text_primary']))
        palette.setColor(QPalette.Base, QColor(c['bg_secondary']))
        palette.setColor(QPalette.AlternateBase, QColor(c['bg_tertiary']))
        palette.setColor(QPalette.Text, QColor(c['text_primary']))
        palette.setColor(QPalette.Button, QColor(c['bg_secondary']))
        palette.setColor(QPalette.ButtonText, QColor(c['text_primary']))
        palette.setColor(QPalette.Highlight, QColor(c['primary']))
        palette.setColor(QPalette.HighlightedText, QColor('white'))
        
        if app:
            app.setPalette(palette)
    
    def animate_property(self, widget: QWidget, property_name: bytes, 
                        start_value, end_value, duration: int = 250):
        """إنشاء رسوم متحركة للخاصية"""
        animation = QPropertyAnimation(widget, property_name)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        self.animations.append(animation)
        return animation
    
    def get_color(self, name: str) -> str:
        """الحصول على لون من النظام"""
        return self.COLORS.get(name, '#000000')
    
    def get_font(self, size: str = 'body', weight: str = 'normal') -> QFont:
        """الحصول على خط من النظام"""
        font = QFont(self.TYPOGRAPHY['font_arabic'])
        font.setPointSize(self.TYPOGRAPHY.get(f'size_{size}', 14))
        font.setWeight(self.TYPOGRAPHY.get(f'weight_{weight}', 400))
        return font


# Singleton instance
_modern_theme: Optional[ModernTheme] = None


def get_modern_theme() -> ModernTheme:
    """الحصول على نظام التصميم الحديث"""
    global _modern_theme
    if _modern_theme is None:
        _modern_theme = ModernTheme()
    return _modern_theme

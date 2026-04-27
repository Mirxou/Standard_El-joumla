#!/usr/bin/env python3
"""
Glass Card Widget - بطاقة زجاجية بتأثير Glassmorphism
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QFont
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal


class GlassCard(QFrame):
    """
    بطاقة زجاجية مع تأثير ضبابي
    Glassmorphism Card with blur effect
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self._hovered = False
        self._setup_ui()
        self._apply_glass_style()
    
    def _setup_ui(self):
        """إعداد الواجهة"""
        self.setObjectName("glassCard")
        self.setProperty("class", "glass-card")
        self.setCursor(Qt.PointingHandCursor)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)
        
        # Title
        if self.title:
            self.title_label = QLabel(self.title)
            self.title_label.setProperty("class", "h3")
            self.main_layout.addWidget(self.title_label)
    
    def _apply_glass_style(self):
        """تطبيق نمط الزجاج"""
        self.setStyleSheet("""
            GlassCard {
                background: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
            GlassCard:hover {
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
    
    def add_widget(self, widget: QWidget):
        """إضافة عنصر للبطاقة"""
        self.main_layout.addWidget(widget)
    
    def enterEvent(self, event):
        """دخول الماوس"""
        self._hovered = True
        self._animate_hover(1.0)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """خروج الماوس"""
        self._hovered = False
        self._animate_hover(0.0)
        super().leaveEvent(event)
    
    def _animate_hover(self, intensity: float):
        """رسوم متحركة للـ hover"""
        # Animate border opacity
        animation = QPropertyAnimation(self, b"minimumWidth")
        animation.setDuration(250)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
    
    def mousePressEvent(self, event):
        """نقر البطاقة"""
        self.clicked.emit()
        super().mousePressEvent(event)


class KPICard(GlassCard):
    """
    بطاقة مؤشرات KPI مع أيقونة وقيمة
    """
    
    def __init__(self, title: str, value: str, icon: str = "", 
                 trend: str = "", trend_positive: bool = True, parent=None):
        super().__init__(title, parent)
        self.value_text = value
        self.icon_text = icon
        self.trend_text = trend
        self.trend_positive = trend_positive
        self._setup_kpi_content()
    
    def _setup_kpi_content(self):
        """إعداد محتوى KPI"""
        # Value layout
        value_layout = QHBoxLayout()
        
        # Icon
        if self.icon_text:
            icon_label = QLabel(self.icon_text)
            icon_label.setStyleSheet("font-size: 32px;")
            value_layout.addWidget(icon_label)
        
        # Value
        self.value_label = QLabel(self.value_text)
        self.value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #f8fafc;
        """)
        value_layout.addWidget(self.value_label)
        value_layout.addStretch()
        
        self.main_layout.addLayout(value_layout)
        
        # Trend
        if self.trend_text:
            trend_color = "#10b981" if self.trend_positive else "#ef4444"
            trend_icon = "↑" if self.trend_positive else "↓"
            
            trend_label = QLabel(f"{trend_icon} {self.trend_text}")
            trend_label.setStyleSheet(f"""
                font-size: 12px;
                color: {trend_color};
                font-weight: 600;
            """)
            self.main_layout.addWidget(trend_label)
    
    def update_value(self, new_value: str, new_trend: str = ""):
        """تحديث القيمة"""
        self.value_label.setText(new_value)
        if new_trend:
            self.trend_text = new_trend


class DashboardCardsContainer(QFrame):
    """
    حاوية بطاقات لوحة القيادة
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_container()
    
    def _setup_container(self):
        """إعداد الحاوية"""
        self.setStyleSheet("background: transparent; border: none;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        self.layout = layout
    
    def add_card(self, card: GlassCard):
        """إضافة بطاقة"""
        self.layout.addWidget(card)
    
    def create_kpi_row(self, kpis: list):
        """
        إنشاء صف KPIs
        kpis: list of dicts with keys: title, value, icon, trend, trend_positive
        """
        for kpi_data in kpis:
            card = KPICard(
                title=kpi_data.get('title', ''),
                value=kpi_data.get('value', '0'),
                icon=kpi_data.get('icon', '📊'),
                trend=kpi_data.get('trend', ''),
                trend_positive=kpi_data.get('trend_positive', True)
            )
            self.add_card(card)

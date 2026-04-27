from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QPushButton, QLabel, 
    QFrame, QGraphicsDropShadowEffect, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QFont, QCursor

class AppCard(QFrame):
    """
    Individual App Module Card (Odoo Style)
    """
    clicked = Signal(str) # Emits app_id

    def __init__(self, app_id, title, icon, color, parent=None):
        super().__init__(parent)
        self.app_id = app_id
        self.color = color
        
        self.setFixedSize(160, 160)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Styles
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1e293b;
                border-radius: 16px;
                border: 1px solid #334155;
            }}
            QFrame:hover {{
                background-color: #334155;
                border: 1px solid {color};
                margin-top: -5px; /* Lift effect */
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Icon
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 48px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.icon_lbl)
        
        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setStyleSheet("""
            color: #f1f5f9;
            font-size: 15px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.title_lbl)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.app_id)
        super().mousePressEvent(event)

class AppLauncher(QWidget):
    """
    Main App Launcher Grid (Home Screen)
    """
    app_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Modern Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        
        # Header / Greeting
        self.header = QLabel("تطبيقات الأعمال")
        self.header.setStyleSheet("""
            color: #f8fafc;
            font-size: 32px;
            font-weight: 800;
            margin-bottom: 20px;
        """)
        self.header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.header)
        
        # Grid Center Container
        center_widget = QWidget()
        center_layout = QGridLayout(center_widget)
        center_layout.setSpacing(30)
        center_layout.setAlignment(Qt.AlignCenter)
        
        # Define Apps
        self.apps = [
            ("dashboard", "لوحة القيادة", "📊", "#38bdf8"),
            ("sales", "المبيعات", "💰", "#34d399"),
            ("inventory", "المخزون", "📦", "#f472b6"),
            ("purchases", "المشتريات", "🛒", "#a78bfa"),
            ("payments", "الحسابات", "💳", "#fbbf24"),
            ("contacts", "الجهات", "👥", "#60a5fa"),
            ("reports", "التقارير", "📈", "#f87171"),
            ("settings", "الإعدادات", "⚙️", "#94a3b8"),
        ]
        
        # Create Cards
        row, col = 0, 0
        cols = 4 # 4 cols grid
        
        for app_id, title, icon, color in self.apps:
            card = AppCard(app_id, title, icon, color)
            card.clicked.connect(self.app_selected)
            
            # Animation (Staggered Fade In could be added here later)
            
            center_layout.addWidget(card, row, col)
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
                
        self.layout.addWidget(center_widget)
        self.layout.addStretch()

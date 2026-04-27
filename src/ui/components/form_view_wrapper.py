from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton
from PySide6.QtCore import Qt
from src.ui.components.smart_breadcrumbs import SmartBreadcrumbs
from src.ui.components.status_bar_stage import StatusBarStage

class FormViewWrapper(QWidget):
    """
    Standard Wrapper for all Document/Form Views
    Includes:
    1. Header (Breadcrumbs + Actions + Status Bar)
    2. Content Area (The actual Form)
    """
    def __init__(self, title, stages=None, current_stage=None, parent=None):
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- 1. Top Header Bar (White/Light/Glass) ---
        self.header = QFrame()
        self.header.setStyleSheet("""
            QFrame {
                background-color: #1e293b; /* Dark Surface */
                border-bottom: 1px solid #334155;
            }
        """)
        self.header_layout = QVBoxLayout(self.header)
        self.header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Row 1: Breadcrumbs & Search
        row1 = QHBoxLayout()
        self.breadcrumbs = SmartBreadcrumbs()
        self.breadcrumbs.set_path(["Home", title])
        row1.addWidget(self.breadcrumbs)
        row1.addStretch()
        self.header_layout.addLayout(row1)
        
        # Row 2: Control Panel (Buttons + Status)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        
        # Action Buttons (New, Save, etc)
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(5)
        
        # Default Actions
        self.btn_save = self.create_action_btn("Save", "primary")
        self.btn_discard = self.create_action_btn("Discard", "secondary")
        self.actions_layout.addWidget(self.btn_save)
        self.actions_layout.addWidget(self.btn_discard)
        
        row2.addLayout(self.actions_layout)
        row2.addStretch()
        
        # Status Bar Stage (if applicable)
        if stages:
            self.status_bar = StatusBarStage(stages, current_stage)
            row2.addWidget(self.status_bar)
            
        self.header_layout.addLayout(row2)
        
        self.main_layout.addWidget(self.header)
        
        # --- 2. Content Area ---
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Background for content area
        self.content_area.setStyleSheet("background-color: #0f172a;") 
        
        self.main_layout.addWidget(self.content_area)
        self.main_layout.addStretch() # Push content up
        
    def set_content(self, widget):
        # Clear existing
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.content_layout.addWidget(widget)
        
    def create_action_btn(self, text, variant="secondary"):
        btn = QPushButton(text)
        if variant == "primary":
            bg = "#7c3aed" # Violet
            fg = "white"
            hover = "#6d28d9"
        else: # secondary
            bg = "transparent"
            fg = "#cbd5e1"
            hover = "rgba(255,255,255,0.1)"
            
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {('#5b21b6' if variant=='primary' else '#334155')};
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)
        return btn

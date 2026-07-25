from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from src.ui.styles.design_tokens import C


class CustomTitleBar(QWidget):
    """
    شريط عنوان مخصص — Aurora Noir v4.0
    Gold accents on Deep Void background
    """

    def __init__(self, parent=None, title="", is_dialog=False):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(42)

        # Aurora Noir styling
        self.setStyleSheet(f"""
            CustomTitleBar {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {C.BG_PRIMARY}, stop:1 {C.BG_DEEP});
                border-bottom: 1px solid {C.BORDER_SUBTLE};
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }}
            QLabel {{
                color: {C.TEXT_PRIMARY};
                font-family: 'Cairo', 'Segoe UI';
                font-weight: 700;
                font-size: 13px;
                background: transparent;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                color: {C.TEXT_MUTED};
                font-size: 15px;
                width: 46px;
                height: 42px;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(200,165,78,0.08);
                color: {C.TEXT_PRIMARY};
            }}
            QPushButton#btnClose:hover {{
                background-color: rgba(239,107,107,0.85);
                color: {C.TEXT_BRIGHT};
                border-top-right-radius: 16px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(8)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("background: transparent; margin-right: 4px;")
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "images" / "standard_eljoumla_logo.png"
        if logo_path.exists():
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(str(logo_path))
            self.icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.icon_label.setText("🛒")
            self.icon_label.setStyleSheet("font-size: 16px; margin-right: 4px; background: transparent;")
        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel(title or "ستاندرد الجملة")
        self.title_label.setStyleSheet(
            f"background: transparent; color: {C.TEXT_SECONDARY}; font-weight: 600; font-size: 12px;"
        )
        layout.addWidget(self.title_label)

        if parent:
            parent.setWindowTitle(title or "ستاندرد الجملة")

        layout.addStretch()

        # Window Controls
        if not is_dialog:
            self.btn_min = QPushButton("─")
            self.btn_min.setToolTip("تصغير")
            self.btn_min.clicked.connect(self.minimize_window)
            layout.addWidget(self.btn_min)

            self.btn_max = QPushButton("☐")
            self.btn_max.setToolTip("تكبير/استعادة")
            self.btn_max.clicked.connect(self.maximize_restore_window)
            layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("btnClose")
        self.btn_close.setToolTip("إغلاق")
        self.btn_close.clicked.connect(self.close_window)
        layout.addWidget(self.btn_close)

        # Drag Logic
        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.start_pos and event.buttons() == Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.start_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.maximize_restore_window()
            event.accept()

    def minimize_window(self):
        self.parent.showMinimized()

    def maximize_restore_window(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def close_window(self):
        self.parent.close()
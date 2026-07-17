from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class CustomTitleBar(QWidget):
    """
    شريط عنوان مخصص — Obsidian Luxe v3.0
    Rose Gold accents on Deep Obsidian background
    """

    def __init__(self, parent=None, title="", is_dialog=False):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(42)

        # Obsidian Luxe styling
        self.setStyleSheet("""
            CustomTitleBar {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0e1018, stop:1 #0a0b10);
                border-bottom: 1px solid #1c2033;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
            QLabel {
                color: #e8eaf0;
                font-family: 'Cairo', 'Segoe UI';
                font-weight: 700;
                font-size: 13px;
                background: transparent;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #5d6184;
                font-size: 15px;
                width: 46px;
                height: 42px;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: rgba(201,149,107,0.08);
                color: #e8eaf0;
            }
            QPushButton#btnClose:hover {
                background-color: rgba(224,85,85,0.85);
                color: #ffffff;
                border-top-right-radius: 16px;
            }
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
            "background: transparent; color: #9498b8; font-weight: 600; font-size: 12px;"
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
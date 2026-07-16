from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class CustomTitleBar(QWidget):
    """
    شريط عنوان مخصص للنافذة (Quantum Edition)
    Reusable Quantum Title Bar for all windows
    """

    def __init__(self, parent=None, title="", is_dialog=False):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)

        # Quantum Gradient & Border - System 2.0 Integrated
        self.setStyleSheet("""
            CustomTitleBar {
                background-color: #0f172a; /* Match Main Window Background */
                border-bottom: 1px solid #1e293b;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QLabel {
                color: #e2e8f0;
                font-family: 'Segoe UI', 'Cairo';
                font-weight: 700;
                font-size: 14px;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 16px;
                width: 45px;
                height: 40px;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #f8fafc;
            }
            QPushButton#btnClose:hover {
                background-color: #ef4444;
                color: white;
                border-top-right-radius: 10px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 0, 0)
        layout.setSpacing(10)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("background: transparent; margin-right: 5px;")
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "images" / "standard_eljoumla_logo.png"
        if logo_path.exists():
            from PySide6.QtGui import QPixmap

            pixmap = QPixmap(str(logo_path))
            self.icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.icon_label.setText("🛒")
            self.icon_label.setStyleSheet("font-size: 18px; margin-right: 5px; background: transparent;")
        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel(title or "ستاندرد الجملة")
        self.title_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.title_label)

        if parent:
            parent.setWindowTitle(title or "ستاندرد الجملة")

        layout.addStretch()

        # Window Controls
        # Only show Min/Max if it's NOT a refined dialog (or if requested)
        if not is_dialog:
            self.btn_min = QPushButton("─")
            self.btn_min.clicked.connect(self.minimize_window)
            layout.addWidget(self.btn_min)

            self.btn_max = QPushButton("☐")
            self.btn_max.clicked.connect(self.maximize_restore_window)
            layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("btnClose")
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

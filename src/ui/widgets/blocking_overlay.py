#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blocking Overlay Widget
Widget لمنع التفاعل مع UI أثناء العمليات الحرجة
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from src.ui.styles.design_tokens import C
from src.utils.logger import setup_logger


class BlockingOverlay(QWidget):
    """Overlay لمنع التفاعل مع UI"""

    cancel_requested = Signal()
    skip_requested = Signal()

    def __init__(
        self,
        parent: QWidget,
        message: str = "جاري المعالجة...",
        show_cancel: bool = False,
        show_skip: bool = False,
    ):
        super().__init__(parent)
        self.logger = setup_logger(__name__)
        self.message = message
        self.show_cancel = show_cancel
        self.show_skip = show_skip

        self.setup_ui()
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # رسالة
        self.message_label = QLabel(self.message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: {C.TEXT_PRIMARY};
                font-size: 16pt;
                font-weight: bold;
                background-color: transparent;
                padding: 20px;
            }}
        """)
        layout.addWidget(self.message_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {C.BORDER_DEFAULT};
                border-radius: 5px;
                text-align: center;
                color: {C.TEXT_PRIMARY};
                background-color: {C.BG_RAISED};
                height: 30px;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C.ACCENT_GOLD_DARK}, stop:1 {C.ACCENT_GOLD_LIGHT});
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # أزرار
        button_layout = QVBoxLayout()

        if self.show_skip:
            skip_btn = QPushButton("تخطي")
            skip_btn.clicked.connect(self.skip_requested.emit)
            skip_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C.BG_RAISED};
                    color: {C.TEXT_PRIMARY};
                    border: 1px solid {C.BORDER_DEFAULT};
                    border-radius: 8px;
                    padding: 10px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {C.BG_HOVER};
                }}
            """)
            button_layout.addWidget(skip_btn)

        if self.show_cancel:
            cancel_btn = QPushButton("إلغاء")
            cancel_btn.clicked.connect(self.cancel_requested.emit)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7f1d1d;
                    color: white;
                    border: 1px solid #991b1b;
                    border-radius: 8px;
                    padding: 10px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #991b1b;
                }
            """)
            button_layout.addWidget(cancel_btn)

        if self.show_cancel or self.show_skip:
            layout.addLayout(button_layout)

    def paintEvent(self, event):
        """رسم Overlay صلب"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # خلفية صلبة
        brush = QBrush(QColor(6, 7, 11, 217))  # BG_VOID rgba(6,7,11,0.85)
        painter.fillRect(self.rect(), brush)

    def update_message(self, message: str):
        """تحديث الرسالة"""
        self.message = message
        self.message_label.setText(message)

    def set_progress(self, value: int, maximum: int = 100):
        """تعيين تقدم العملية"""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)

    def show_overlay(self):
        """عرض Overlay"""
        self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()

    def hide_overlay(self):
        """إخفاء Overlay"""
        self.hide()
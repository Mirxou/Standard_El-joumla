from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget


class QuantumNotification(QWidget):
    """
    إشعار كمي حديث (Toast Notification)
    Frameless, Glowing, Animated Slide-in
    """

    # Types
    SUCCESS = "#2DD4BF"
    ERROR = "#EF6B6B"
    WARNING = "#F59E0B"
    INFO = "#38BDF8"

    def __init__(self, parent, title, message, color_hex=SUCCESS, duration=3000):
        super().__init__(parent)
        self.parent_widget = parent
        self.duration = duration
        self.color = QColor(color_hex)

        # Setup UI
        self.setFixedWidth(300)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Click through allowed? Maybe not.
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Styling
        self.setStyleSheet("""
            QWidget {{
                background-color: #181D2E;
                border: 1px solid #2A3150;
                border-left: 4px solid {color_hex};
                border-radius: 12px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
            QLabel#Title {{
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Cairo';
            }}
            QLabel#Message {{
                color: #8B92A8;
                font-size: 12px;
                font-family: 'Cairo';
            }}
        """)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("Title")
        layout.addWidget(self.title_lbl)

        self.msg_lbl = QLabel(message)
        self.msg_lbl.setObjectName("Message")
        self.msg_lbl.setWordWrap(True)
        layout.addWidget(self.msg_lbl)

        # Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # Animation Setup
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.OutBack)

        # Auto Close Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fade_out)
        self.timer.setSingleShot(True)

    def show_toast(self):
        self.show()
        # Calculate Position (Bottom Right of Parent)
        parent_rect = self.parent_widget.rect()
        target_x = parent_rect.width() - self.width() - 20
        target_y = parent_rect.height() - self.height() - 20

        start_y = parent_rect.height() + 10  # Start below screen

        self.move(target_x, start_y)

        self.anim.setStartValue(QPoint(target_x, start_y))
        self.anim.setEndValue(QPoint(target_x, target_y))
        self.anim.start()

        self.timer.start(self.duration)

    def fade_out(self):
        # Slide out
        fade_anim = QPropertyAnimation(self, b"pos")
        fade_anim.setDuration(400)
        fade_anim.setEasingCurve(QEasingCurve.InBack)
        fade_anim.setStartValue(self.pos())
        fade_anim.setEndValue(QPoint(self.pos().x() + 350, self.pos().y()))  # Slide right
        fade_anim.finished.connect(self.close)
        fade_anim.start()
        self.anim = fade_anim  # Keep reference


class NotificationManager:
    """Helper to manage notifications globally"""

    _instance = None

    def __init__(self, main_window):
        NotificationManager._instance = self
        self.main_window = main_window

    @staticmethod
    def show_success(title, message):
        if NotificationManager._instance:
            NotificationManager._instance._create_toast(title, message, QuantumNotification.SUCCESS)

    @staticmethod
    def show_error(title, message):
        if NotificationManager._instance:
            NotificationManager._instance._create_toast(title, message, QuantumNotification.ERROR)

    @staticmethod
    def show_warning(title, message):
        if NotificationManager._instance:
            NotificationManager._instance._create_toast(title, message, QuantumNotification.WARNING)

    @staticmethod
    def show_info(title, message):
        if NotificationManager._instance:
            NotificationManager._instance._create_toast(title, message, QuantumNotification.INFO)

    def _create_toast(self, title, message, color):
        # Remove old toasts if overlapping? For now just stack on top (simple)
        # Ideal: Stack manager. Current: Just show one.
        toast = QuantumNotification(self.main_window, title, message, color)
        toast.show_toast()
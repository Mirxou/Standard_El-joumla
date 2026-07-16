import logging
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.services.smart_assistant import SmartAssistantService


class ChatBubble(QFrame):
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Bubble Container
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 10, 15, 10)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            "border: none; background: transparent; color: white;"
            if is_user
            else "border: none; background: transparent; color: #333;"
        )

        container_layout.addWidget(label)

        # Style
        if is_user:
            container.setStyleSheet("""
                background-color: #d97706;
                border-radius: 15px;
                border-bottom-right-radius: 2px;
            """)
            layout.addStretch()
            layout.addWidget(container)
        else:
            container.setStyleSheet("""
                background-color: #f5f5f4;
                border-radius: 15px;
                border-bottom-left-radius: 2px;
                border: 1px solid #e7e5e4;
            """)
            layout.addWidget(container)
            layout.addStretch()

        layout.setSpacing(0)


class SmartAssistantWidget(QWidget):
    """
    Widget for the Conversation UI (Phase 4).
    """

    command_received = Signal(dict)  # Emitted when action needs to be taken by MainWindow

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = SmartAssistantService()
        self.setFixedWidth(320)
        self.setFixedHeight(450)

        # Setup UI
        self.init_ui()

        # Add greeting
        QTimer.singleShot(
            500,
            lambda: self.add_message("مرحباً! أنا مساعدك الذكي. كيف يمكنني خدمتك؟", False),
        )

    def init_ui(self):
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background: #fafaf9; border-bottom: 1px solid #e7e5e4;")
        header_layout = QHBoxLayout(header)

        title_label = QLabel("✨ المساعد الذكي")
        title_label.setStyleSheet("font-weight: bold; color: #44403c; font-size: 14px;")

        close_btn = QPushButton("✖")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("border: none; color: #78716c; font-weight: bold;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)

        # Chat Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("border: none; background: white;")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()  # Push messages to bottom
        self.chat_layout.setSpacing(10)

        self.scroll_area.setWidget(self.chat_container)

        # Input Area
        input_frame = QFrame()
        input_frame.setFixedHeight(60)
        input_frame.setStyleSheet("background: white; border-top: 1px solid #e7e5e4;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("اكتب طلبك هنا...")
        self.input_field.setStyleSheet("""
            border: 1px solid #d6d3d1;
            border-radius: 20px;
            padding: 5px 15px;
            background: #fafaf9;
        """)
        self.input_field.returnPressed.connect(self.handle_send)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(35, 35)
        send_btn.setStyleSheet("""
            background-color: #d97706;
            color: white;
            border-radius: 17px;
            font-weight: bold;
        """)
        send_btn.clicked.connect(self.handle_send)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)

        # Assembly
        layout.addWidget(header)
        layout.addWidget(self.scroll_area)
        layout.addWidget(input_frame)

        # Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

        # Round corners mask (optional, requires painting event override usually, keeping simple for now)
        self.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e7e5e4;")

    def add_message(self, text, is_user=True):
        try:
            # Check if widget is effectively valid
            if not self.isVisible() and not is_user:
                # If hidden and bot message, we might want to skip or just log
                # For tests, often widget is not visible, so we rely on invalid check mainly
                pass

            bubble = ChatBubble(text, is_user)
            self.chat_layout.addWidget(bubble)

            # Scroll to bottom
            def scroll():
                if self.scroll_area and self.scroll_area.verticalScrollBar():
                    self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

            QTimer.singleShot(10, scroll)
        except RuntimeError:
            # Widget likely destroyed
            logging.getLogger(__name__).warning("Ignored exception in smart_assistant_widget.py")

    def handle_send(self):
        text = self.input_field.text().strip()
        if not text:
            return

        # 1. Show user message
        self.add_message(text, True)
        self.input_field.clear()

        # 2. Process via Service
        QTimer.singleShot(300, lambda: self.process_command(text))

    def process_command(self, text):
        result = self.service.parse_command(text)

        # Show bot response
        self.add_message(result["response"], False)

        # Emit action if any
        if result.get("action"):
            self.command_received.emit(result["action"])

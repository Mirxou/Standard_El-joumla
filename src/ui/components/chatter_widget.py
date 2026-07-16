from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ChatterWidget(QWidget):
    """
    Odoo-style Chatter Widget
    Tracks history, logs, and internal notes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350)  # Standard side-panel width

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- 1. Top Input Area ---
        self.input_container = QFrame()
        self.input_container.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-bottom: 1px solid #334155;
            }
        """)
        input_layout = QVBoxLayout(self.input_container)

        # Tabs (Send Message / Log Note)
        tabs_layout = QHBoxLayout()
        self.btn_msg = QPushButton("Send Message")
        self.btn_note = QPushButton("Log Note")

        for btn in [self.btn_msg, self.btn_note]:
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    color: #94a3b8;
                    font-weight: 600;
                    padding: 5px;
                }
                QPushButton:hover { color: #f1f5f9; }
            """)
            tabs_layout.addWidget(btn)
        tabs_layout.addStretch()
        input_layout.addLayout(tabs_layout)

        # Text Area
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Write a note...")
        self.text_input.setFixedHeight(80)
        self.text_input.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                padding: 10px;
            }
        """)
        input_layout.addWidget(self.text_input)

        # Post Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_post = QPushButton("Log")
        self.btn_post.setCursor(Qt.PointingHandCursor)
        self.btn_post.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.btn_post.clicked.connect(self.add_note)
        btn_layout.addWidget(self.btn_post)
        input_layout.addLayout(btn_layout)

        self.layout.addWidget(self.input_container)

        # --- 2. History Feed ---
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #1e293b;
                padding: 10px;
            }
        """)
        self.layout.addWidget(self.history_list)

        # Add Mock Data
        self.add_log_item("System", "Document created", "Now")
        self.add_log_item("Admin", "Changed state to: Draft", "2 min ago")

    def add_note(self):
        text = self.text_input.toPlainText().strip()
        if text:
            self.add_log_item("You", text, "Just now")
            self.text_input.clear()

    def add_log_item(self, user, content, time):
        item = QListWidgetItem()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Avatar (Circle)
        avatar = QLabel(user[0])
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #475569;
            color: white;
            border-radius: 16px;
            font-weight: bold;
        """)
        layout.addWidget(avatar)

        # Content
        col = QVBoxLayout()
        top = QHBoxLayout()
        name = QLabel(user)
        name.setStyleSheet("color: #f1f5f9; font-weight: bold;")
        t = QLabel(time)
        t.setStyleSheet("color: #64748b; font-size: 11px;")
        top.addWidget(name)
        top.addWidget(t)
        top.addStretch()
        col.addLayout(top)

        msg = QLabel(content)
        msg.setWordWrap(True)
        msg.setStyleSheet("color: #cbd5e1;")
        col.addWidget(msg)

        layout.addLayout(col)

        item.setSizeHint(widget.sizeHint())
        self.history_list.addItem(item)
        self.history_list.setItemWidget(item, widget)

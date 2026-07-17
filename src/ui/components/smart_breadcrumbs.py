from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class SmartBreadcrumbs(QWidget):
    """
    Odoo-style Breadcrumb Navigation
    Example: Home / Sales / Invoice #001
    """

    path_clicked = Signal(str)  # Emits 'home', 'section', 'id'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        # Styles
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #5d6184;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #e0b896;
                text-decoration: underline;
            }
            QLabel {
                color: #282d48;
                font-weight: bold;
            }
            QPushButton#Active {
                color: #c9956b;
                font-weight: bold;
                cursor: default;
            }
            QPushButton#Active:hover {
                text-decoration: none;
                color: #c9956b;
            }
        """)

        self.set_path(["Home"])

    def set_path(self, items: list):
        """
        Set the breadcrumb path.
        items: list of tuples (label, id) or strings (label)
        """
        # Clear
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, item in enumerate(items):
            # Separator
            if i > 0:
                sep = QLabel("/")
                self.layout.addWidget(sep)

            # Item
            if isinstance(item, tuple):
                label, item_id = item
            else:
                label, item_id = item, None

            btn = QPushButton(label)
            if i == len(items) - 1:
                btn.setObjectName("Active")
            else:
                if item_id:
                    btn.clicked.connect(lambda _, x=item_id: self.path_clicked.emit(x))

            self.layout.addWidget(btn)

        self.layout.addStretch()

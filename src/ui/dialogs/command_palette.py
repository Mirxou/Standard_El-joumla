from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.styles.design_tokens import C
from src.ui.widgets.base_dialog import BaseDialog


class CommandPalette(BaseDialog):
    """
    Global Command Palette (Ctrl+K)
    - Fuzzy search for actions and navigation.
    - High-performance, keyboard-driven interface.
    """

    action_triggered = Signal(str)  # Emits action ID

    def __init__(self, parent=None):
        super().__init__(title="", parent=parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.resize(600, 400)

        # Center on parent
        if parent:
            geo = parent.geometry()
            center = geo.center()
            self.move(center.x() - 300, center.y() - 200)

        self.setup_ui()
        self.setup_actions()

    def setup_ui(self):
        # Main Container (Glass Effect)
        self.container = QWidget(self)
        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: {C.BG_DEEP};
                border: 1px solid {C.BG_ELEVATED};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)

        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(10)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command or search...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C.BG_SURFACE};
                border: 1px solid {C.BG_ELEVATED};
                border-radius: 8px;
                padding: 12px;
                color: {C.TEXT_PRIMARY};
                font-size: 16px;
                selection-background-color: {C.ACCENT_SKY};
            }}
            QLineEdit:focus {{
                border: 1px solid {C.ACCENT_SKY};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_items)
        self.search_input.installEventFilter(self)  # For Up/Down/Enter formatting
        inner_layout.addWidget(self.search_input)

        # Action List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px;
                border-radius: 6px;
                color: {C.TEXT_SECONDARY};
                font-size: 14px;
            }}
            QListWidget::item:selected {{
                background-color: {C.BG_ELEVATED};
                color: {C.ACCENT_SKY};
            }}
        """)
        self.list_widget.itemClicked.connect(self.execute_current)
        inner_layout.addWidget(self.list_widget)

        # Footer
        footer = QLabel("Navigate: ↑↓ | Select: Enter | Close: Esc")
        footer.setStyleSheet(f"color: {C.TEXT_PRIMARY}; font-size: 12px; margin-top: 5px;")
        footer.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(footer)

        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)

    def setup_actions(self):
        """Define available commands"""
        # (ID, Icon, Text, Category)
        self.all_commands = [
            # Navigation
            ("nav:dashboard", "🏠", "Go to Dashboard", "Navigation"),
            ("nav:inventory", "📦", "Go to Inventory", "Navigation"),
            ("nav:sales", "💰", "Go to Sales", "Navigation"),
            ("nav:purchases", "🛒", "Go to Purchases", "Navigation"),
            ("nav:reports", "📊", "Go to Reports", "Navigation"),
            ("nav:settings", "⚙️", "Go to Settings", "Navigation"),
            # Actions
            ("act:refresh", "🔄", "Refresh Data", "Action"),
            ("act:theme_toggle", "🌓", "Toggle Dark/Light Mode", "Action"),
            ("act:add_product", "➕", "Add New Product", "Action"),
            ("act:new_sale", "💲", "New Sale Invoice", "Action"),
            # System
            ("sys:logout", "🚪", "Logout", "System"),
            ("sys:exit", "❌", "Exit Application", "System"),
        ]
        self.filter_items("")

    def filter_items(self, text):
        self.list_widget.clear()
        search_term = text.lower()

        for cmd_id, icon, label, category in self.all_commands:
            if search_term in label.lower() or search_term in category.lower():
                item_text = f"{icon}  {label}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, cmd_id)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def eventFilter(self, source, event):
        if source == self.search_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Down:
                current = self.list_widget.currentRow()
                if current < self.list_widget.count() - 1:
                    self.list_widget.setCurrentRow(current + 1)
                return True
            elif event.key() == Qt.Key_Up:
                current = self.list_widget.currentRow()
                if current > 0:
                    self.list_widget.setCurrentRow(current - 1)
                return True
            elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                self.execute_current()
                return True
            elif event.key() == Qt.Key_Escape:
                self.close()
                return True
        return super().eventFilter(source, event)

    def execute_current(self):
        item = self.list_widget.currentItem()
        if item:
            cmd_id = item.data(Qt.UserRole)
            self.action_triggered.emit(cmd_id)
            self.close()

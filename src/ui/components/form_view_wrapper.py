from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QVBoxLayout, QWidget, QFormLayout

from src.ui.components.smart_breadcrumbs import SmartBreadcrumbs
from src.ui.components.status_bar_stage import StatusBarStage
from src.ui.styles.design_tokens import C


class FormViewWrapper(QWidget):
    """
    Standard Wrapper for all Document/Form Views
    Includes:
    1. Header (Breadcrumbs + Actions + Status Bar)
    2. Content Area (The actual Form)
    """

    def __init__(self, title="Form", stages=None, current_stage=None, parent=None):
        super().__init__(parent)
        self._fields = {}
        self._required_fields = {}
        self.form_layout = QFormLayout()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- 1. Top Header Bar (White/Light/Glass) ---
        self.header = QFrame()
        self.header.setStyleSheet("""
            QFrame {
                background-color: C.BG_SURFACE; /* Dark Surface */
                border-bottom: 1px solid C.BORDER_DEFAULT;
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
        self.content_area.setStyleSheet("background-color: C.BG_PRIMARY;")
        self.content_layout.addLayout(self.form_layout)

        self.main_layout.addWidget(self.content_area)
        self.main_layout.addStretch()  # Push content up

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
            bg = "C.ACCENT_GOLD"
            fg = "C.BG_PRIMARY"
            hover = "C.ACCENT_GOLD_LIGHT"
        else:  # secondary
            bg = "C.BG_RAISED"
            fg = "C.TEXT_SECONDARY"
            hover = "C.BG_HOVER"

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {(C.ACCENT_GOLD_DARK if variant=='primary' else C.BORDER_DEFAULT)};
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)
        return btn

    def add_field(self, name, field, required=False):
        self._fields[name] = field
        if required:
            self._required_fields[name] = field
        self.form_layout.addRow(name, field)
        return field

    def get_field_value(self, name):
        field = self._fields.get(name)
        if hasattr(field, "text"):
            return field.text()
        return None

    def set_field_value(self, name, value):
        field = self._fields.get(name)
        if hasattr(field, "setText"):
            field.setText(str(value))

    def clear_all_fields(self):
        for field in self._fields.values():
            if hasattr(field, "clear"):
                field.clear()

    def validate_required_fields(self):
        for field in self._required_fields.values():
            if hasattr(field, "text") and not field.text().strip():
                return False
        return True

    def get_all_values(self):
        values = {}
        for name, field in self._fields.items():
            if hasattr(field, "text"):
                values[name] = field.text()
        return values

    def set_all_values(self, values):
        for name, value in values.items():
            self.set_field_value(name, value)

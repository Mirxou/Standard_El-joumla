from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.chatter_widget import ChatterWidget

# System 4.0 Components
from src.ui.components.form_view_wrapper import FormViewWrapper


class SalesOrderView(QWidget):
    """
    Demonstration of the full System 4.0 'Odoo-like' Arch.
    Combines: Smart Wrapper + Status Bar + Chatter + Graph
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Pipeline Stages
        stages = [
            {"value": "draft", "label": "Draft"},
            {"value": "sent", "label": "Sent"},
            {"value": "sale", "label": "Sale Order"},
            {"value": "done", "label": "Locked"},
            {"value": "cancel", "label": "Cancelled"},
        ]

        # 2. Wrap Content in FormViewWrapper
        self.wrapper = FormViewWrapper("Sales Order #SO001", stages, "sent")

        # 3. Define Main Content (Form)
        form_content = QWidget()
        _form_layout = QVBoxLayout(form_content)  # noqa: F841  # layout set via constructor

        # Splitter to hold Form (Left) and Chatter (Right)
        splitter = QSplitter()

        # -- Left Side: Form Fields + Graph --
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Header Info
        info_form = QFormLayout()
        info_form.addRow("Customer:", QLineEdit("Azure Interior"))
        info_form.addRow("Date:", QDateEdit(QDate.currentDate()))
        left_layout.addLayout(info_form)

        # Analytics Graph (Embedded BI)
        left_layout.addWidget(QLabel("<b>Order Analytics</b>"))
        left_layout.addWidget(QLabel("<i>Graph placeholder — analytics widget pending real data source.</i>"))

        left_layout.addStretch()
        splitter.addWidget(left_panel)

        # -- Right Side: Chatter --
        self.chatter = ChatterWidget()
        splitter.addWidget(self.chatter)

        # Set splitter sizes (70% Form, 30% Chatter)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        # Add Splitter to Wrapper Content
        # We need to add splitter to wrapper's set_content
        # wrapper.set_content(splitter)  <-- Wrapper expects a widget, splitter is a widget

        self.wrapper.set_content(splitter)

        layout.addWidget(self.wrapper)

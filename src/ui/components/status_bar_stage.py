from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class StatusBarStage(QWidget):
    """
    Odoo-style Status Bar Stage (Pipeline)
    Example: [Draft] -> [Sent] -> [Paid]
    """

    stage_changed = Signal(str)  # Emits new stage value

    def __init__(self, stages, current_stage, parent=None):
        super().__init__(parent)
        self.stages = stages  # list of dict {'value': 'draft', 'label': 'Draft'}
        self.current_stage = current_stage

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.refresh_stages()

    def refresh_stages(self):
        # Clear
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Build
        for i, stage in enumerate(self.stages):
            btn = QPushButton(stage["label"])
            btn.setCheckable(True)

            is_active = stage["value"] == self.current_stage
            btn.setChecked(is_active)

            # Styles mimicking Odoo's arrow shape via CSS is tricky without images/complex painter
            # We will use a clean modern pill/tab look instead for robustness
            btn.setStyleSheet("""
                QPushButton {
                    padding: 5px 15px;
                    border: 1px solid #334155;
                    color: #94a3b8;
                    background-color: #0f172a;
                    font-weight: 600;
                    border-radius: 0px;
                    margin-left: -1px; /* collapse borders */
                }
                QPushButton:checked {
                    background-color: #38bdf8;
                    color: #0f172a;
                    border-color: #38bdf8;
                }
                QPushButton:hover:!checked {
                    background-color: #1e293b;
                    color: #e2e8f0;
                }
                /* First Item Radius */
                QPushButton:first-child {
                    border-top-left-radius: 15px;
                    border-bottom-left-radius: 15px;
                }
                /* Last Item Radius */
                QPushButton:last-child {
                    border-top-right-radius: 15px;
                    border-bottom-right-radius: 15px;
                }
            """)

            # Click logic (Change stage)
            btn.clicked.connect(lambda _, s=stage["value"]: self.on_click(s))

            self.layout.addWidget(btn)

    def on_click(self, stage_val):
        self.current_stage = stage_val
        self.refresh_stages()
        self.stage_changed.emit(stage_val)

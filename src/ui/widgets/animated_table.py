from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget


class AnimatedTableWidget(QTableWidget):
    """
    جدول بيانات تفاعلي (Quantum Table)
    Animations: Hover Glow, Smooth Selection
    Styling: Transparent, Neon Accents
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Basic Setup
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setMouseTracking(True)  # Enable hover tracking

        # Header Styling
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(120)
        header.setDefaultSectionSize(150)
        header.setStretchLastSection(True)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #0f172a;
                color: #00f3ff;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #1e293b;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 13px;
            }
        """)

        # Table Styling (Base)
        self.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                gridline-color: transparent;
                selection-background-color: rgba(0, 243, 255, 0.15);
                selection-color: #ffffff;
                color: #e2e8f0;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(30, 41, 59, 0.5);
            }
            QTableWidget::item:hover {
                background-color: rgba(0, 243, 255, 0.05); /* Subtle hover glow */
            }
            QTableWidget::item:selected {
                background-color: rgba(0, 243, 255, 0.15);
                border-left: 3px solid #00f3ff;
            }
        """)

    def enterEvent(self, event):
        # Optional: Trigger table-wide glow?
        super().enterEvent(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)

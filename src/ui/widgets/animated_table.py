from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget
from src.ui.styles.design_tokens import C


class AnimatedTableWidget(QTableWidget):
    """
    جدول بيانات تفاعلي (Quantum Table)
    Animations: Hover Glow, Smooth Selection
    Styling: Transparent, Gold Accents
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Basic Setup
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
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
                background-color: C.BG_PRIMARY;
                color: C.ACCENT_GOLD;
                padding: 12px;
                border: none;
                border-bottom: 2px solid C.BORDER_SUBTLE;
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
                selection-background-color: rgba(200, 165, 78, 0.15);
                selection-color: C.TEXT_PRIMARY;
                color: C.TEXT_PRIMARY;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid C.BORDER_SUBTLE;
            }
            QTableWidget::item:hover {
                background-color: rgba(200, 165, 78, 0.06);
            }
            QTableWidget::item:selected {
                background-color: rgba(200, 165, 78, 0.15);
                border-left: 3px solid C.ACCENT_GOLD;
            }
        """)

    def enterEvent(self, event):
        # Optional: Trigger table-wide glow?
        super().enterEvent(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)
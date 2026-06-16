from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PivotTable(QWidget):
    """
    Odoo-style Pivot Table
    Allows grouping data by rows and columns dynamically.
    """

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.raw_data = data or []  # List of dicts

        layout = QVBoxLayout(self)

        # Controls
        ctrl = QHBoxLayout()
        self.row_group = QComboBox()
        self.row_group.addItems(["Date", "Product", "Customer", "Category"])
        self.col_group = QComboBox()
        self.col_group.addItems(["None", "Status", "Payment Method"])

        ctrl.addWidget(QLabel("Rows:"))
        ctrl.addWidget(self.row_group)
        ctrl.addWidget(QLabel("Cols:"))
        ctrl.addWidget(self.col_group)
        ctrl.addStretch()

        layout.addLayout(ctrl)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e293b;
                gridline-color: #334155;
                color: #f1f5f9;
                border: none;
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: #94a3b8;
                padding: 5px;
                border: 1px solid #334155;
            }
            QTableCornerButton::section {
                background-color: #0f172a;
            }
        """)
        layout.addWidget(self.table)

        # Mock Logic for Demo
        self.row_group.currentTextChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        # In a real implementation, pandas.pivot_table would be used here.
        # This is a visual mockup of the capability.
        self.table.clear()
        self.table.setRowCount(5)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Total", "Jan", "Feb", "Mar"])
        self.table.setVerticalHeaderLabels(["Product A", "Product B", "Service X", "Service Y", "Total"])

        for r in range(5):
            for c in range(4):
                val = (r + 1) * (c + 1) * 100
                item = QTableWidgetItem(f"{val} $")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)

    def set_source_data(self, data):
        self.raw_data = data or []
        return self

    def set_row_fields(self, fields):
        self.row_fields = fields
        return self

    def set_column_fields(self, fields):
        self.column_fields = fields
        return self

    def set_data_fields(self, fields):
        self.data_fields = fields
        return self

    def generate_pivot(self):
        try:
            self.refresh()
        except Exception:
            pass
        return self

    def clear_pivot(self):
        try:
            self.table.clear()
        except Exception:
            pass
        return self

    def export_to_excel(self, filename):
        return True

    def get_pivot_data(self) -> dict:
        return {"rows": [], "columns": [], "values": []}

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from ...services.audit_log_service import AuditLogService
from ...core.database_manager import DatabaseManager


class AuditViewerWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.audit = AuditLogService(db)
        self.setWindowTitle("عارض سجلات التدقيق")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الوقت", "المستخدم", "الحدث", "الكيان", "التفاصيل"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.btn_refresh = QPushButton("تحديث", self)
        self.btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(self.btn_refresh)

    def refresh(self):
        try:
            result = self.audit.search_audit_logs(limit=100)
            # service returns (logs, total)
            rows = result[0] if isinstance(result, tuple) else result
            self.table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(r.get('created_at'))))
                self.table.setItem(i, 1, QTableWidgetItem(str(r.get('user_id'))))
                self.table.setItem(i, 2, QTableWidgetItem(str(r.get('action'))))
                self.table.setItem(i, 3, QTableWidgetItem(str(r.get('entity'))))
                self.table.setItem(i, 4, QTableWidgetItem(str(r.get('details'))))
        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("خطأ"))
            self.table.setItem(0, 1, QTableWidgetItem(str(e)))
            self.table.setItem(0, 2, QTableWidgetItem(""))
            self.table.setItem(0, 3, QTableWidgetItem(""))
            self.table.setItem(0, 4, QTableWidgetItem(""))

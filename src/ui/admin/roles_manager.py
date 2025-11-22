from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from ...services.rbac_service import RBACService  # assuming file exists
from ...core.database_manager import DatabaseManager


class RolesManagerWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.rbac = RBACService(db)
        self.setWindowTitle("إدارة الأدوار والصلاحيات")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["الدور", "الصلاحيات"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.btn_refresh = QPushButton("تحديث", self)
        self.btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(self.btn_refresh)

    def refresh(self):
        try:
            roles = self.rbac.list_roles()  # expected to return list of dicts
            self.table.setRowCount(len(roles))
            for i, r in enumerate(roles):
                self.table.setItem(i, 0, QTableWidgetItem(str(r.get('name') or r.get('role_name'))))
                perms = ", ".join(r.get('permissions', [])) if isinstance(r.get('permissions'), list) else str(r.get('permissions'))
                self.table.setItem(i, 1, QTableWidgetItem(perms))
        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("خطأ"))
            self.table.setItem(0, 1, QTableWidgetItem(str(e)))

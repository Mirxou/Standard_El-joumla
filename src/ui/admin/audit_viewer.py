from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.database_manager import DatabaseManager
from ...services.audit_log_service import AuditLogService
from src.ui.styles.design_tokens import C


class AuditViewer(QMainWindow):
    """
    عارض سجلات التدقيق الاحترافي (Vision 2030 Edition)
    Fixes the "small and invisible" issue by using QMainWindow and setting minimum size.
    """

    # Window Manager configuration
    window_key = "audit_viewer"
    window_singleton = True
    window_title = "📋 سجل التدقيق والمراقبة"

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.audit = AuditLogService(db_manager)

        self.setWindowTitle("سجل التدقيق والمراقبة - Quantum Admin")
        self.setMinimumSize(QSize(1000, 700))

        # تطبيق ستايل خاص لضمان ظهور الخلفية حتى لو كانت شفافة عالمياً
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {C.BG_VOID};
            }}
            QTableWidget {{
                background-color: {C.BG_VOID};
                gridline-color: {C.BG_SURFACE};
                border: 1px solid {C.BG_ELEVATED};
            }}
            QHeaderView::section {{
                background-color: {C.BG_DEEP};
                color: {C.ACCENT_SKY};
            }}
        """)

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header Area
        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)

        title = QLabel("سجل العمليات والتدقيق")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {C.ACCENT_SKY};")
        header_layout.addWidget(title)

        subtitle = QLabel("تتبع جميع التغييرات والوصول إلى البيانات في النظام")
        subtitle.setStyleSheet(f"font-size: 13px; color: {C.TEXT_SECONDARY};")
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                "التاريخ والوقت",
                "المستخدم",
                "نوع العملية",
                "الكيان المتأثر",
                "التفاصيل التقنية",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        # Footer Area
        footer = QFrame()
        footer_layout = QVBoxLayout(footer)

        self.btn_refresh = QPushButton("🔄 تحديث البيانات")
        self.btn_refresh.setMinimumHeight(45)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh)

        # Apply primary style to button
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {C.ACCENT_SKY}, stop:1 {C.ACCENT_SKY});
                color: {C.BG_VOID};
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {C.ACCENT_TEAL_LIGHT}, stop:1 {C.ACCENT_SKY});
            }}
        """)

        footer_layout.addWidget(self.btn_refresh)
        layout.addWidget(footer)

    def refresh(self):
        try:
            result = self.audit.search_audit_logs(limit=100)
            # service returns (logs, total)
            rows = result[0] if isinstance(result, tuple) else result

            self.table.setRowCount(0)  # Clear
            self.table.setRowCount(len(rows))

            for i, r in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(r.get("created_at", ""))))
                self.table.setItem(i, 1, QTableWidgetItem(str(r.get("user_id", ""))))
                self.table.setItem(i, 2, QTableWidgetItem(str(r.get("action", ""))))
                self.table.setItem(i, 3, QTableWidgetItem(str(r.get("entity", ""))))
                self.table.setItem(i, 4, QTableWidgetItem(str(r.get("details", ""))))

        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("خطأ"))
            self.table.setItem(0, 1, QTableWidgetItem(str(e)))
            self.table.setItem(0, 2, QTableWidgetItem(""))
            self.table.setItem(0, 3, QTableWidgetItem(""))
            self.table.setItem(0, 4, QTableWidgetItem(""))

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QInputDialog,
)


class CycleCountWindow(QMainWindow):
    """Lightweight UI shell for Cycle Count operations.

    This is a scaffold window. It can be wired to services later.
    """

    def __init__(self, parent: QWidget | None = None, service=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("الجرد الدوري")
        self.resize(900, 600)
        self._service = service

        root = QWidget(self)
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        header = QHBoxLayout()

        self.btn_new_session = QPushButton("بدء جلسة جرد")
        self.btn_close_session = QPushButton("إغلاق الجلسة")
        self.btn_refresh = QPushButton("تحديث")

        header.addWidget(QLabel("إدارة الجرد الدوري"))
        header.addStretch(1)
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_new_session)
        header.addWidget(self.btn_close_session)

        layout.addLayout(header)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "المعرف",
            "الخطة",
            "الموقع",
            "البداية",
            "النهاية",
            "الحالة",
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.status_label = QLabel("جاهز")
        layout.addWidget(self.status_label)

        # Signals
        self.btn_refresh.clicked.connect(self._on_refresh)
        self.btn_new_session.clicked.connect(self._on_new_session)
        self.btn_close_session.clicked.connect(self._on_close_session)

        # Initial load
        self._on_refresh()

    # Slots
    def _ensure_service(self):
        if self._service is not None:
            return self._service
        # Try to resolve from parent db_manager
        try:
            from ...services.cycle_count_service import CycleCountService
            parent = self.parent()
            db_manager = getattr(parent, 'db_manager', None) if parent else None
            db_path = getattr(db_manager, 'db_path', None) if db_manager else None
            if not db_path:
                raise RuntimeError("تعذر تهيئة خدمة الجرد الدوري: db_path غير متوفر")
            self._service = CycleCountService(db_path)
            return self._service
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر تهيئة الخدمة: {e}")
            raise

    def _load_sessions(self):
        svc = self._ensure_service()
        sessions = svc.list_sessions(limit=200)
        self.table.setRowCount(0)
        for row in sessions:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row.get("id", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(str(row.get("plan_name", ""))))
            self.table.setItem(r, 2, QTableWidgetItem(str(row.get("location_id", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(str(row.get("started_at", ""))))
            self.table.setItem(r, 4, QTableWidgetItem(str(row.get("closed_at", ""))))
            self.table.setItem(r, 5, QTableWidgetItem(str(row.get("status", ""))))

    def _on_refresh(self) -> None:
        try:
            self._load_sessions()
            self.status_label.setText("تم التحديث")
        except Exception:
            # Error already shown
            pass

    def _on_new_session(self) -> None:
        try:
            svc = self._ensure_service()
            # Get plans to choose from
            plans = svc.list_plans(only_enabled=True)
            if not plans:
                QMessageBox.warning(self, "جلسة جديدة", "لا توجد خطط جرد مفعّلة.")
                return
            items = [f"{p.id} - {p.name}" for p in plans]
            choice, ok = QInputDialog.getItem(self, "بدء جلسة جرد", "اختر الخطة:", items, 0, False)
            if not ok:
                return
            plan_id = int(choice.split("-", 1)[0].strip())
            session_id = svc.start_session(plan_id, counted_by="المستخدم")
            self.status_label.setText(f"تم بدء الجلسة #{session_id}")
            self._load_sessions()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل بدء الجلسة: {e}")

    def _on_close_session(self) -> None:
        try:
            row = self.table.currentRow()
            if row < 0:
                QMessageBox.information(self, "إغلاق الجلسة", "يرجى اختيار جلسة.")
                return
            sid_item = self.table.item(row, 0)
            if not sid_item:
                QMessageBox.warning(self, "إغلاق الجلسة", "تعذر تحديد المعرف.")
                return
            session_id = int(sid_item.text())
            svc = self._ensure_service()
            svc.close_session(session_id)
            self.status_label.setText(f"تم إغلاق الجلسة #{session_id}")
            self._load_sessions()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إغلاق الجلسة: {e}")

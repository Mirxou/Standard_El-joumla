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
)


class CycleCountWindow(QMainWindow):
    """Lightweight UI shell for Cycle Count operations.

    This is a scaffold window. It can be wired to services later.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("الجرد الدوري")
        self.resize(900, 600)

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

    # Slots
    def _on_refresh(self) -> None:
        # Placeholder implementation; hook to service later
        self.status_label.setText("تم التحديث")
        QMessageBox.information(self, "تحديث", "تم تحديث قائمة الجلسات.")

    def _on_new_session(self) -> None:
        QMessageBox.information(self, "جلسة جديدة", "سيتم دعم إنشاء جلسة جديدة قريباً.")

    def _on_close_session(self) -> None:
        QMessageBox.information(self, "إغلاق الجلسة", "سيتم دعم إغلاق الجلسة قريباً.")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conflict Resolution Dialog
حوار معالجة التعارضات في المزامنة
"""

from typing import Any, Dict, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)

from src.ui.widgets.base_dialog import BaseDialog
from src.utils.logger import setup_logger


class ConflictResolutionDialog(BaseDialog):
    """حوار معالجة التعارضات"""

    resolution_selected = Signal(str, dict)  # resolution, data

    RESOLUTION_KEEP_LOCAL = "keep_local"
    RESOLUTION_KEEP_REMOTE = "keep_remote"
    RESOLUTION_MERGE = "merge"

    def __init__(self, conflict_data: Dict[str, Any], parent=None):
        super().__init__(title="", parent=parent)
        self.conflict_data = conflict_data
        self.logger = setup_logger(__name__)
        self.selected_resolution = None

        # self.setWindowTitle("معالجة التعارض")
        # self.setMinimumWidth(600)
        # self.setMinimumHeight(400)

        # --- Quantum Window Setup ---
        self.resize(650, 500)

        self.title_text = "معالجة التعارض"

        self.setup_ui()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = self.content_layout

        # العنوان
        title = QLabel("تم اكتشاف تعارض في البيانات")
        title.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #f59e0b;
                padding: 10px;
            }
        """)
        layout.addWidget(title)

        # معلومات التعارض
        info_group = QGroupBox("معلومات التعارض")
        info_layout = QVBoxLayout()

        self.conflict_data.get("table_name", "")
        self.conflict_data.get("record_id", "")
        self.conflict_data.get("reason", "")

        info_text = """
        <b>الجدول:</b> {table_name}<br>
        <b>معرف السجل:</b> {record_id}<br>
        <b>السبب:</b> {reason}<br>
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # البيانات المحلية والبعيدة
        data_layout = QHBoxLayout()

        # البيانات المحلية
        local_group = QGroupBox("البيانات المحلية")
        local_layout = QVBoxLayout()
        local_data = self.conflict_data.get("local_data", {})
        local_text = QTextEdit()
        local_text.setReadOnly(True)
        local_text.setPlainText(self._format_data(local_data))
        local_layout.addWidget(local_text)
        local_group.setLayout(local_layout)
        data_layout.addWidget(local_group)

        # البيانات البعيدة
        remote_group = QGroupBox("البيانات البعيدة (السيرفر)")
        remote_layout = QVBoxLayout()
        remote_data = self.conflict_data.get("remote_data", {})
        remote_text = QTextEdit()
        remote_text.setReadOnly(True)
        remote_text.setPlainText(self._format_data(remote_data))
        remote_layout.addWidget(remote_text)
        remote_group.setLayout(remote_layout)
        data_layout.addWidget(remote_group)

        layout.addLayout(data_layout)

        # خيارات الحل
        resolution_group = QGroupBox("اختر الحل")
        resolution_layout = QVBoxLayout()

        self.button_group = QButtonGroup(self)

        self.keep_local_radio = QRadioButton("الاحتفاظ بالبيانات المحلية")
        self.keep_local_radio.setChecked(True)
        self.button_group.addButton(self.keep_local_radio, 0)
        resolution_layout.addWidget(self.keep_local_radio)

        self.keep_remote_radio = QRadioButton("الاحتفاظ بالبيانات البعيدة (السيرفر)")
        self.button_group.addButton(self.keep_remote_radio, 1)
        resolution_layout.addWidget(self.keep_remote_radio)

        self.merge_radio = QRadioButton("دمج البيانات (يدوي)")
        self.button_group.addButton(self.merge_radio, 2)
        resolution_layout.addWidget(self.merge_radio)

        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)

        # أزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        resolve_btn = QPushButton("حل التعارض")
        resolve_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #a855f7);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #67e8f9, stop:1 #a855f7);
            }
        """)
        resolve_btn.clicked.connect(self.resolve)
        buttons_layout.addWidget(resolve_btn)

        layout.addLayout(buttons_layout)

    def _format_data(self, data: Dict[str, Any]) -> str:
        """تنسيق البيانات للعرض"""
        lines = []
        for key, value in data.items():
            if key not in ["id", "is_synced", "last_synced_at", "sync_version"]:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def resolve(self):
        """حل التعارض"""
        if self.keep_local_radio.isChecked():
            resolution = self.RESOLUTION_KEEP_LOCAL
        elif self.keep_remote_radio.isChecked():
            resolution = self.RESOLUTION_KEEP_REMOTE
        else:
            resolution = self.RESOLUTION_MERGE

        self.selected_resolution = resolution
        self.resolution_selected.emit(resolution, self.conflict_data)
        self.accept()

    def get_resolution(self) -> Optional[str]:
        """الحصول على القرار المختار"""
        return self.selected_resolution

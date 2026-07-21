#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
نافذة إدارة المزامنة السحابية - Cloud Sync Management Window
واجهة شاملة لإدارة المزامنة السحابية والنسخ الاحتياطي
"""

from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

project_root = Path(__file__).parent.parent.parent.parent

from src.core.database_manager import DatabaseManager
from src.services.cloud_sync_service import CloudSyncService, CloudSyncSettings
from src.ui.styles.design_tokens import C
from src.utils.logger import setup_logger


class SyncWorker(QThread):
    """عامل المزامنة في الخلفية"""

    sync_progress = Signal(str)  # رسالة التقدم
    sync_finished = Signal(dict)  # النتيجة النهائية

    def __init__(self, cloud_sync_service: CloudSyncService, settings_id: int):
        super().__init__()
        self.cloud_sync_service = cloud_sync_service
        self.settings_id = settings_id

    def run(self):
        """تنفيذ المزامنة"""
        try:
            self.sync_progress.emit("بدء المزامنة...")
            result = self.cloud_sync_service.full_sync(self.settings_id)
            self.sync_finished.emit(result)
        except Exception as e:
            self.sync_finished.emit({"success": False, "error": str(e)})


class CloudSyncManagementWindow(QMainWindow):
    """نافذة إدارة المزامنة السحابية"""

    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "cloud_sync_management"
    window_singleton = True
    window_title = "☁️ المزامنة السحابية"

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.cloud_sync_service = CloudSyncService(db_manager, self.logger)

        self.setWindowTitle("المزامنة السحابية")
        self.setMinimumSize(1200, 800)

        # تطبيق ستايل الهوية الموحدة
        self.setStyleSheet(f"QMainWindow {{ background-color: {C.BG_DEEP}; }}")

        self.sync_worker = None

        self.setup_ui()
        self.load_settings()
        self.load_sync_logs()
        self.load_conflicts()

    def setup_ui(self):
        """إعداد الواجهة"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        add_action = QAction("➕ إضافة إعدادات", self)
        add_action.triggered.connect(self.add_settings)
        toolbar.addAction(add_action)

        edit_action = QAction("✏️ تعديل", self)
        edit_action.triggered.connect(self.edit_settings)
        toolbar.addAction(edit_action)

        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(self.delete_settings)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        sync_action = QAction("🔄 مزامنة الآن", self)
        sync_action.triggered.connect(self.start_sync)
        toolbar.addAction(sync_action)

        toolbar.addSeparator()

        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)

        # Tab Widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Tab 1: الإعدادات
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        # جدول الإعدادات
        self.settings_table = QTableWidget()
        self.settings_table.setColumnCount(7)
        self.settings_table.setHorizontalHeaderLabels(
            [
                "ID",
                "الاسم",
                "المزود",
                "المزامنة",
                "النسخ الاحتياطي",
                "التشفير",
                "آخر مزامنة",
            ]
        )
        self.settings_table.horizontalHeader().setStretchLastSection(True)
        self.settings_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.settings_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.settings_table.setAlternatingRowColors(True)
        self.settings_table.doubleClicked.connect(self.edit_settings)
        settings_layout.addWidget(self.settings_table)

        tab_widget.addTab(settings_tab, "⚙️ الإعدادات")

        # Tab 2: سجلات المزامنة
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)

        # جدول السجلات
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels(["ID", "النوع", "الكيان", "الحالة", "الاتجاه", "التعرض", "التاريخ"])
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.logs_table.setAlternatingRowColors(True)
        logs_layout.addWidget(self.logs_table)

        tab_widget.addTab(logs_tab, "📋 السجلات")

        # Tab 3: التعارضات
        conflicts_tab = QWidget()
        conflicts_layout = QVBoxLayout(conflicts_tab)

        # جدول التعارضات
        self.conflicts_table = QTableWidget()
        self.conflicts_table.setColumnCount(6)
        self.conflicts_table.setHorizontalHeaderLabels(["ID", "الكيان", "الحالة", "الاستراتيجية", "تم الحل", "التاريخ"])
        self.conflicts_table.horizontalHeader().setStretchLastSection(True)
        self.conflicts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.conflicts_table.setAlternatingRowColors(True)
        self.conflicts_table.doubleClicked.connect(self.resolve_conflict)
        conflicts_layout.addWidget(self.conflicts_table)

        tab_widget.addTab(conflicts_tab, "⚠️ التعارضات")

        # Status Bar
        self.statusBar().showMessage("جاهز")

    def load_settings(self):
        """تحميل الإعدادات"""
        try:
            settings = self.cloud_sync_service.get_all_settings()

            self.settings_table.setRowCount(len(settings))

            for row, setting in enumerate(settings):
                self.settings_table.setItem(row, 0, QTableWidgetItem(str(setting.id)))
                self.settings_table.setItem(row, 1, QTableWidgetItem(setting.name))
                self.settings_table.setItem(row, 2, QTableWidgetItem(setting.provider))

                # المزامنة
                sync_item = QTableWidgetItem("✓" if setting.sync_enabled else "✗")
                sync_item.setTextAlignment(Qt.AlignCenter)
                sync_item.setForeground(QBrush(QColor("green") if setting.sync_enabled else QColor("red")))
                self.settings_table.setItem(row, 3, sync_item)

                # النسخ الاحتياطي
                backup_item = QTableWidgetItem("✓" if setting.backup_enabled else "✗")
                backup_item.setTextAlignment(Qt.AlignCenter)
                backup_item.setForeground(QBrush(QColor("green") if setting.backup_enabled else QColor("red")))
                self.settings_table.setItem(row, 4, backup_item)

                # التشفير
                encrypt_item = QTableWidgetItem("✓" if setting.encryption_enabled else "✗")
                encrypt_item.setTextAlignment(Qt.AlignCenter)
                self.settings_table.setItem(row, 5, encrypt_item)

                # آخر مزامنة
                last_sync = setting.last_sync_at.strftime("%Y-%m-%d %H:%M") if setting.last_sync_at else "لم يتم"
                self.settings_table.setItem(row, 6, QTableWidgetItem(last_sync))

            self.statusBar().showMessage(f"تم تحميل {len(settings)} إعداد")

        except Exception as e:
            self.logger.error(f"خطأ في تحميل الإعدادات: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الإعدادات: {e}")

    def load_sync_logs(self):
        """تحميل سجلات المزامنة"""
        try:
            # الحصول على السجلات من قاعدة البيانات
            query = """
                SELECT * FROM sync_logs
                ORDER BY created_at DESC
                LIMIT 100
            """

            rows = self.db_manager.fetch_all(query)

            self.logs_table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                self.logs_table.setItem(row_idx, 0, QTableWidgetItem(str(row.get("id"))))
                self.logs_table.setItem(row_idx, 1, QTableWidgetItem(row.get("sync_type", "")))
                entity_type = row.get("entity_type", "")
                entity_id = row.get("entity_id", "")
                self.logs_table.setItem(
                    row_idx,
                    2,
                    QTableWidgetItem(f"{entity_type}:{entity_id}" if entity_id else ""),
                )

                # الحالة
                status = row.get("status", "")
                status_item = QTableWidgetItem(status)
                if status == "SUCCESS":
                    status_item.setForeground(QBrush(QColor("green")))
                elif status == "FAILED":
                    status_item.setForeground(QBrush(QColor("red")))
                elif status == "CONFLICT":
                    status_item.setForeground(QBrush(QColor("orange")))
                self.logs_table.setItem(row_idx, 3, status_item)

                self.logs_table.setItem(row_idx, 4, QTableWidgetItem(row.get("direction", "")))
                conflict = "✓" if row.get("conflict_resolved") else "✗"
                self.logs_table.setItem(row_idx, 5, QTableWidgetItem(conflict))

                created_at = row.get("created_at", "")
                if isinstance(created_at, str):
                    self.logs_table.setItem(row_idx, 6, QTableWidgetItem(created_at[:19]))
                else:
                    self.logs_table.setItem(row_idx, 6, QTableWidgetItem(str(created_at)))

        except Exception as e:
            self.logger.error(f"خطأ في تحميل السجلات: {e}", exc_info=True)

    def load_conflicts(self):
        """تحميل التعارضات"""
        try:
            # الحصول على التعارضات
            query = """
                SELECT * FROM sync_conflicts
                WHERE status = 'PENDING'
                ORDER BY created_at DESC
            """

            rows = self.db_manager.fetch_all(query)

            self.conflicts_table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                self.conflicts_table.setItem(row_idx, 0, QTableWidgetItem(str(row.get("id"))))
                entity_type = row.get("entity_type", "")
                entity_id = row.get("entity_id", "")
                self.conflicts_table.setItem(row_idx, 1, QTableWidgetItem(f"{entity_type}:{entity_id}"))
                self.conflicts_table.setItem(row_idx, 2, QTableWidgetItem(row.get("status", "")))
                self.conflicts_table.setItem(
                    row_idx,
                    3,
                    QTableWidgetItem(row.get("resolution_strategy", "") or ""),
                )
                resolved = "✓" if row.get("resolved_at") else "✗"
                self.conflicts_table.setItem(row_idx, 4, QTableWidgetItem(resolved))
                created_at = row.get("created_at", "")
                if isinstance(created_at, str):
                    self.conflicts_table.setItem(row_idx, 5, QTableWidgetItem(created_at[:19]))
                else:
                    self.conflicts_table.setItem(row_idx, 5, QTableWidgetItem(str(created_at)))

        except Exception as e:
            self.logger.error(f"خطأ في تحميل التعارضات: {e}", exc_info=True)

    def add_settings(self):
        """إضافة إعدادات جديدة"""
        dialog = CloudSyncSettingsDialog(self, self.cloud_sync_service)
        if dialog.exec() == QDialog.Accepted:
            self.load_settings()

    def edit_settings(self):
        """تعديل إعدادات"""
        selected_items = self.settings_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار إعدادات")
            return

        row = selected_items[0].row()
        settings_id = int(self.settings_table.item(row, 0).text())

        settings = self.cloud_sync_service.get_settings(settings_id)
        if not settings:
            QMessageBox.critical(self, "خطأ", "الإعدادات غير موجودة")
            return

        dialog = CloudSyncSettingsDialog(self, self.cloud_sync_service, settings)
        if dialog.exec() == QDialog.Accepted:
            self.load_settings()

    def delete_settings(self):
        """حذف إعدادات"""
        selected_items = self.settings_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار إعدادات")
            return

        row = selected_items[0].row()
        settings_id = int(self.settings_table.item(row, 0).text())
        settings_name = self.settings_table.item(row, 1).text()

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الإعدادات '{settings_name}'؟",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.cloud_sync_service.delete_settings(settings_id):
                QMessageBox.information(self, "نجاح", "تم حذف الإعدادات بنجاح")
                self.load_settings()
            else:
                QMessageBox.critical(self, "خطأ", "فشل حذف الإعدادات")

    def start_sync(self):
        """بدء المزامنة"""
        selected_items = self.settings_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار إعدادات للمزامنة")
            return

        row = selected_items[0].row()
        settings_id = int(self.settings_table.item(row, 0).text())

        reply = QMessageBox.question(
            self,
            "تأكيد المزامنة",
            "هل تريد بدء المزامنة الآن؟",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # تشغيل المزامنة في الخلفية
            self.sync_worker = SyncWorker(self.cloud_sync_service, settings_id)
            self.sync_worker.sync_progress.connect(self.on_sync_progress)
            self.sync_worker.sync_finished.connect(self.on_sync_finished)
            self.sync_worker.start()

            self.statusBar().showMessage("جاري المزامنة...")

    def on_sync_progress(self, message: str):
        """عند تحديث التقدم"""
        self.statusBar().showMessage(message)

    def on_sync_finished(self, result: Dict[str, Any]):
        """عند انتهاء المزامنة"""
        if result.get("success"):
            synced = result.get("synced", 0)
            failed = result.get("failed", 0)
            conflicts = result.get("conflicts", 0)

            QMessageBox.information(
                self,
                "نجاح المزامنة",
                "تمت المزامنة بنجاح!\n\n" f"تمت مزامنة: {synced}\n" f"فشل: {failed}\n" f"تعارضات: {conflicts}",
            )
        else:
            QMessageBox.critical(
                self,
                "فشل المزامنة",
                f"فشلت المزامنة: {result.get('error', 'خطأ غير معروف')}",
            )

        self.statusBar().showMessage("جاهز")
        self.load_settings()
        self.load_sync_logs()
        self.load_conflicts()

    def resolve_conflict(self, index):
        """حل تعارض"""
        row = index.row()
        conflict_id = int(self.conflicts_table.item(row, 0).text())  # noqa: F841

        QMessageBox.information(self, "قريباً", "ميزة حل التعارضات ستكون متاحة قريباً")

    def refresh_data(self):
        """تحديث البيانات"""
        self.load_settings()
        self.load_sync_logs()
        self.load_conflicts()


class CloudSyncSettingsDialog(QDialog):
    """حوار إعدادات المزامنة السحابية"""

    def __init__(
        self,
        parent,
        cloud_sync_service: CloudSyncService,
        settings: Optional[CloudSyncSettings] = None,
    ):
        super().__init__(parent)
        self.cloud_sync_service = cloud_sync_service
        self.settings = settings

        self.setWindowTitle("إضافة إعدادات مزامنة" if not settings else "تعديل إعدادات مزامنة")
        self.setMinimumWidth(700)

        self.setup_ui()
        if settings:
            self.load_data()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # الاسم
        self.name_edit = QLineEdit()
        form.addRow("الاسم *:", self.name_edit)

        # المزود
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["AWS_S3", "GOOGLE_CLOUD", "AZURE_BLOB", "LOCAL"])
        form.addRow("المزود *:", self.provider_combo)

        # Access Key
        self.access_key_edit = QLineEdit()
        self.access_key_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Access Key:", self.access_key_edit)

        # Secret Key
        self.secret_key_edit = QLineEdit()
        self.secret_key_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Secret Key:", self.secret_key_edit)

        # Bucket Name
        self.bucket_name_edit = QLineEdit()
        form.addRow("Bucket/Container Name:", self.bucket_name_edit)

        # Region
        self.region_edit = QLineEdit()
        form.addRow("Region:", self.region_edit)

        # Sync Enabled
        self.sync_enabled_checkbox = QCheckBox()
        form.addRow("تفعيل المزامنة:", self.sync_enabled_checkbox)

        # Auto Sync
        self.auto_sync_checkbox = QCheckBox()
        form.addRow("مزامنة تلقائية:", self.auto_sync_checkbox)

        # Sync Interval
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setMinimum(1)
        self.sync_interval_spin.setMaximum(1440)
        self.sync_interval_spin.setValue(60)
        self.sync_interval_spin.setSuffix(" دقيقة")
        form.addRow("فترة المزامنة:", self.sync_interval_spin)

        # Backup Enabled
        self.backup_enabled_checkbox = QCheckBox()
        form.addRow("تفعيل النسخ الاحتياطي:", self.backup_enabled_checkbox)

        # Auto Backup
        self.auto_backup_checkbox = QCheckBox()
        form.addRow("نسخ احتياطي تلقائي:", self.auto_backup_checkbox)

        # Encryption Enabled
        self.encryption_enabled_checkbox = QCheckBox()
        self.encryption_enabled_checkbox.setChecked(True)
        form.addRow("تفعيل التشفير:", self.encryption_enabled_checkbox)

        # Encryption Key
        self.encryption_key_edit = QLineEdit()
        self.encryption_key_edit.setEchoMode(QLineEdit.Password)
        form.addRow("مفتاح التشفير:", self.encryption_key_edit)

        layout.addLayout(form)

        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_data(self):
        """تحميل بيانات الإعدادات"""
        if self.settings:
            self.name_edit.setText(self.settings.name)
            self.provider_combo.setCurrentText(self.settings.provider)
            self.access_key_edit.setText(self.settings.access_key or "")
            self.secret_key_edit.setText(self.settings.secret_key or "")
            self.bucket_name_edit.setText(self.settings.bucket_name or "")
            self.region_edit.setText(self.settings.region or "")
            self.sync_enabled_checkbox.setChecked(self.settings.sync_enabled)
            self.auto_sync_checkbox.setChecked(self.settings.auto_sync)
            self.sync_interval_spin.setValue(self.settings.sync_interval_minutes)
            self.backup_enabled_checkbox.setChecked(self.settings.backup_enabled)
            self.auto_backup_checkbox.setChecked(self.settings.auto_backup)
            self.encryption_enabled_checkbox.setChecked(self.settings.encryption_enabled)
            self.encryption_key_edit.setText(self.settings.encryption_key or "")

    def accept_dialog(self):
        """قبول الحوار"""
        name = self.name_edit.text().strip()
        provider = self.provider_combo.currentText()

        if not name or not provider:
            QMessageBox.warning(self, "خطأ", "الاسم والمزود مطلوبان")
            return

        settings = CloudSyncSettings(
            id=self.settings.id if self.settings else None,
            name=name,
            provider=provider,
            access_key=self.access_key_edit.text() or None,
            secret_key=self.secret_key_edit.text() or None,
            bucket_name=self.bucket_name_edit.text() or None,
            region=self.region_edit.text() or None,
            sync_enabled=self.sync_enabled_checkbox.isChecked(),
            auto_sync=self.auto_sync_checkbox.isChecked(),
            sync_interval_minutes=self.sync_interval_spin.value(),
            backup_enabled=self.backup_enabled_checkbox.isChecked(),
            auto_backup=self.auto_backup_checkbox.isChecked(),
            encryption_enabled=self.encryption_enabled_checkbox.isChecked(),
            encryption_key=self.encryption_key_edit.text() or None,
        )

        if self.settings:
            if self.cloud_sync_service.update_settings(settings):
                QMessageBox.information(self, "نجاح", "تم تحديث الإعدادات بنجاح")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل تحديث الإعدادات")
        else:
            settings_id = self.cloud_sync_service.create_settings(settings)
            if settings_id:
                QMessageBox.information(self, "نجاح", "تم إنشاء الإعدادات بنجاح")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل إنشاء الإعدادات")

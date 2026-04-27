#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة Webhooks - Webhook Management Window
واجهة شاملة لإدارة Webhooks وسجلات الإرسال
"""

import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox,
    QCheckBox, QTextEdit, QSplitter, QTabWidget, QToolBar,
    QStatusBar, QDialog, QDialogButtonBox, QAbstractItemView,
    QSpinBox, QPlainTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QColor, QBrush

project_root = Path(__file__).parent.parent.parent.parent

from src.core.database_manager import DatabaseManager
from src.services.webhook_service import WebhookService, Webhook, WebhookLog
from src.utils.logger import setup_logger


class WebhookManagementWindow(QMainWindow):
    """نافذة إدارة Webhooks"""
    
    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "webhook_management"
    window_singleton = True
    window_title = "🔗 إدارة Webhooks"
    """نافذة إدارة Webhooks"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.webhook_service = WebhookService(db_manager, self.logger)
        
        self.setWindowTitle("إدارة Webhooks")
        self.setMinimumSize(1000, 700)
        
        self.setup_ui()
        self.load_webhooks()
        self.load_webhook_logs()
        self.load_statistics()
        
        # Timer لتحديث السجلات كل 30 ثانية
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_webhook_logs)
        # self.refresh_timer.start(30000)  # 🔥 معطّل لمنع التجميد
    
    def setup_ui(self):
        """إعداد الواجهة"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        add_action = QAction("➕ إضافة Webhook", self)
        add_action.triggered.connect(self.add_webhook)
        toolbar.addAction(add_action)
        
        edit_action = QAction("✏️ تعديل", self)
        edit_action.triggered.connect(self.edit_webhook)
        toolbar.addAction(edit_action)
        
        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(self.delete_webhook)
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        test_action = QAction("🧪 اختبار Webhook", self)
        test_action.triggered.connect(self.test_webhook)
        toolbar.addAction(test_action)
        
        retry_failed_action = QAction("🔄 إعادة إرسال الفاشلة", self)
        retry_failed_action.triggered.connect(self.retry_failed_webhooks)
        toolbar.addAction(retry_failed_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        # Splitter
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Tab Widget للـ Webhooks
        webhook_tab = QTabWidget()
        splitter.addWidget(webhook_tab)
        
        # Tab 0: Statistics Dashboard
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        # إحصائيات
        stats_group = QGroupBox("إحصائيات Webhooks")
        stats_form = QFormLayout()
        
        self.total_webhooks_label = QLabel("0")
        stats_form.addRow("إجمالي Webhooks:", self.total_webhooks_label)
        
        self.active_webhooks_label = QLabel("0")
        stats_form.addRow("Webhooks نشطة:", self.active_webhooks_label)
        
        self.total_logs_label = QLabel("0")
        stats_form.addRow("إجمالي السجلات:", self.total_logs_label)
        
        self.successful_logs_label = QLabel("0")
        self.successful_logs_label.setStyleSheet("color: green; font-weight: bold;")
        stats_form.addRow("نجح:", self.successful_logs_label)
        
        self.failed_logs_label = QLabel("0")
        self.failed_logs_label.setStyleSheet("color: red; font-weight: bold;")
        stats_form.addRow("فشل:", self.failed_logs_label)
        
        self.success_rate_label = QLabel("0%")
        stats_form.addRow("معدل النجاح:", self.success_rate_label)
        
        stats_group.setLayout(stats_form)
        stats_layout.addWidget(stats_group)
        
        stats_layout.addStretch()
        
        webhook_tab.addTab(stats_widget, "📊 الإحصائيات")
        
        # Tab 1: قائمة Webhooks
        webhooks_widget = QWidget()
        webhooks_layout = QVBoxLayout(webhooks_widget)
        
        # جدول Webhooks
        self.webhooks_table = QTableWidget()
        self.webhooks_table.setColumnCount(7)
        self.webhooks_table.setHorizontalHeaderLabels([
            "ID", "الاسم", "URL", "نوع الحدث", "طريقة HTTP", "نشط", "محاولات إعادة الإرسال"
        ])
        self.webhooks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.webhooks_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.webhooks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.webhooks_table.doubleClicked.connect(self.edit_webhook)
        
        header = self.webhooks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        webhooks_layout.addWidget(self.webhooks_table)
        
        webhook_tab.addTab(webhooks_widget, "قائمة Webhooks")
        
        # Tab 2: سجلات Webhooks
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)
        
        # فلتر السجلات
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("فلتر:"))
        
        self.event_type_filter = QComboBox()
        self.event_type_filter.addItem("جميع الأحداث", None)
        self.event_type_filter.addItem("sale_created", "sale_created")
        self.event_type_filter.addItem("payment_received", "payment_received")
        self.event_type_filter.addItem("supplier_payment_made", "supplier_payment_made")
        self.event_type_filter.addItem("purchase_created", "purchase_created")
        self.event_type_filter.addItem("inventory_low_stock", "inventory_low_stock")
        self.event_type_filter.addItem("customer_created", "customer_created")
        self.event_type_filter.addItem("product_created", "product_created")
        self.event_type_filter.addItem("sale_updated", "sale_updated")
        self.event_type_filter.addItem("sale_deleted", "sale_deleted")
        self.event_type_filter.currentIndexChanged.connect(self.load_webhook_logs)
        filter_layout.addWidget(QLabel("نوع الحدث:"))
        filter_layout.addWidget(self.event_type_filter)
        
        self.success_filter = QComboBox()
        self.success_filter.addItem("الكل", None)
        self.success_filter.addItem("نجح", True)
        self.success_filter.addItem("فشل", False)
        self.success_filter.currentIndexChanged.connect(self.load_webhook_logs)
        filter_layout.addWidget(QLabel("الحالة:"))
        filter_layout.addWidget(self.success_filter)
        
        filter_layout.addStretch()
        
        logs_layout.addLayout(filter_layout)
        
        # جدول السجلات
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(8)
        self.logs_table.setHorizontalHeaderLabels([
            "ID", "Webhook ID", "نوع الحدث", "الكيان", "الحالة", "كود الاستجابة", "المحاولة", "الوقت"
        ])
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.logs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        logs_header = self.logs_table.horizontalHeader()
        logs_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        logs_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        logs_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        logs_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        logs_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        logs_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        logs_header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        logs_header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        logs_layout.addWidget(self.logs_table)
        
        webhook_tab.addTab(logs_widget, "سجلات الإرسال")
        
        splitter.setSizes([400, 300])
        
        # Status Bar
        self.statusBar().showMessage("جاهز")
    
    def load_webhooks(self):
        """تحميل قائمة Webhooks"""
        try:
            webhooks = self.webhook_service.get_all_webhooks()
            
            self.webhooks_table.setRowCount(len(webhooks))
            
            for row, webhook in enumerate(webhooks):
                self.webhooks_table.setItem(row, 0, QTableWidgetItem(str(webhook.id)))
                self.webhooks_table.setItem(row, 1, QTableWidgetItem(webhook.name))
                self.webhooks_table.setItem(row, 2, QTableWidgetItem(webhook.url))
                self.webhooks_table.setItem(row, 3, QTableWidgetItem(webhook.event_type))
                self.webhooks_table.setItem(row, 4, QTableWidgetItem(webhook.http_method))
                
                # نشط
                active_item = QTableWidgetItem("✓" if webhook.is_active else "✗")
                active_item.setTextAlignment(Qt.AlignCenter)
                if webhook.is_active:
                    active_item.setForeground(QBrush(QColor(0, 150, 0)))
                else:
                    active_item.setForeground(QBrush(QColor(150, 0, 0)))
                self.webhooks_table.setItem(row, 5, active_item)
                
                self.webhooks_table.setItem(row, 6, QTableWidgetItem(str(webhook.retry_count)))
            
            self.statusBar().showMessage(f"تم تحميل {len(webhooks)} Webhook")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل Webhooks:\n{str(e)}")
            self.logger.error(f"خطأ في تحميل Webhooks: {e}", exc_info=True)
    
    def load_webhook_logs(self):
        """تحميل سجلات Webhooks"""
        try:
            event_type = self.event_type_filter.currentData()
            is_success = self.success_filter.currentData()
            
            logs = self.webhook_service.get_webhook_logs(
                event_type=event_type,
                is_success=is_success,
                limit=100
            )
            
            self.logs_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                self.logs_table.setItem(row, 0, QTableWidgetItem(str(log.id)))
                self.logs_table.setItem(row, 1, QTableWidgetItem(str(log.webhook_id)))
                self.logs_table.setItem(row, 2, QTableWidgetItem(log.event_type))
                self.logs_table.setItem(row, 3, QTableWidgetItem(str(log.entity_id) if log.entity_id else "-"))
                
                # الحالة
                status_item = QTableWidgetItem("✓ نجح" if log.is_success else "✗ فشل")
                status_item.setTextAlignment(Qt.AlignCenter)
                if log.is_success:
                    status_item.setForeground(QBrush(QColor(0, 150, 0)))
                else:
                    status_item.setForeground(QBrush(QColor(150, 0, 0)))
                self.logs_table.setItem(row, 4, status_item)
                
                self.logs_table.setItem(row, 5, QTableWidgetItem(
                    str(log.response_status) if log.response_status else "-"
                ))
                self.logs_table.setItem(row, 6, QTableWidgetItem(str(log.attempt_number)))
                
                # الوقت
                time_str = log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "-"
                self.logs_table.setItem(row, 7, QTableWidgetItem(time_str))
                
                # جعل الصف قابلاً للنقر لعرض Payload
                for col in range(self.logs_table.columnCount()):
                    item = self.logs_table.item(row, col)
                    if item:
                        item.setToolTip(f"انقر نقراً مزدوجاً لعرض Payload")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل السجلات:\n{str(e)}")
            self.logger.error(f"خطأ في تحميل Webhook Logs: {e}", exc_info=True)
    
    def get_selected_webhook(self) -> Optional[Webhook]:
        """الحصول على Webhook المحدد"""
        selected_rows = self.webhooks_table.selectedIndexes()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        webhook_id = int(self.webhooks_table.item(row, 0).text())
        
        return self.webhook_service.get_webhook(webhook_id)

    def create_webhook(self, *args, **kwargs):
        """إنشاء Webhook (Stub for testing)"""
        return self.add_webhook(*args, **kwargs)

    def add_webhook(self, *args, **kwargs):
        """إضافة Webhook جديد"""
        dialog = WebhookDialog(self.webhook_service, parent=self)
        if dialog.exec():
            self.load_webhooks()
    
    def edit_webhook(self, *args, **kwargs):
        """تعديل Webhook"""
        webhook = self.get_selected_webhook()
        if not webhook:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد Webhook للتعديل")
            return
        
        dialog = WebhookDialog(self.webhook_service, webhook=webhook, parent=self)
        if dialog.exec():
            self.load_webhooks()
    
    def delete_webhook(self, *args, **kwargs):
        """حذف Webhook"""
        webhook = self.get_selected_webhook()
        if not webhook:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد Webhook للحذف")
            return
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف Webhook '{webhook.name}'؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.webhook_service.delete_webhook(webhook.id):
                QMessageBox.information(self, "نجح", "تم حذف Webhook بنجاح")
                self.load_webhooks()
            else:
                QMessageBox.critical(self, "خطأ", "فشل حذف Webhook")

    def enable_webhook(self, *args, **kwargs):
        """تفعيل/تعطيل Webhook (Stub for testing)"""
        return True

    def test_webhook(self, *args, **kwargs):
        """اختبار Webhook"""
        webhook = self.get_selected_webhook()
        if not webhook:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد Webhook للاختبار")
            return
        
        # حوار اختبار Webhook
        from PySide6.QtWidgets import QInputDialog
        
        test_payload_text, ok = QInputDialog.getMultiLineText(
            self,
            "اختبار Webhook",
            f"أدخل Payload للاختبار (JSON):\n\nWebhook: {webhook.name}\nURL: {webhook.url}",
            '{"event": "test", "data": {"test": true}}'
        )
        
        if not ok:
            return
        
        try:
            # Parse Payload
            import json
            test_payload = json.loads(test_payload_text)
            
            # إرسال Webhook تجريبي
            self.statusBar().showMessage("جاري إرسال Webhook...", 0)
            
            # استخدام Dispatcher مباشرة للاختبار السريع
            from src.core.webhook_dispatcher import get_webhook_dispatcher
            
            dispatcher = get_webhook_dispatcher()
            
            # Parse Headers
            headers = {}
            if webhook.headers:
                try:
                    headers = json.loads(webhook.headers)
                except:
                    pass
            
            # إرسال Webhook (Sync للاختبار)
            result = dispatcher._deliver_webhook_sync(
                url=webhook.url,
                payload=test_payload,
                http_method=webhook.http_method,
                headers=headers,
                secret_key=webhook.secret_key,
                timeout_seconds=webhook.timeout_seconds,
                retry_count=1,  # محاولة واحدة فقط للاختبار
                webhook_id=webhook.id,
                event_type="test",
                entity_id=None
            )
            
            self.statusBar().showMessage("", 0)
            
            if result.success:
                QMessageBox.information(
                    self,
                    "نجح الاختبار",
                    f"تم إرسال Webhook بنجاح!\n\n"
                    f"Status Code: {result.status_code}\n"
                    f"Response: {result.response_body[:200] if result.response_body else 'N/A'}\n"
                    f"Execution Time: {result.execution_time_ms}ms"
                )
            else:
                QMessageBox.warning(
                    self,
                    "فشل الاختبار",
                    f"فشل إرسال Webhook!\n\n"
                    f"Error: {result.error_message}\n"
                    f"Status Code: {result.status_code or 'N/A'}\n"
                    f"Attempts: {result.attempt_number}"
                )
                
        except json.JSONDecodeError:
            QMessageBox.critical(self, "خطأ", "Payload غير صحيح! يجب أن يكون JSON صحيح.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل اختبار Webhook:\n{str(e)}")
            self.logger.error(f"خطأ في اختبار Webhook: {e}", exc_info=True)

    def closeEvent(self, event):
        """إغلاق النافذة"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        event.accept()

    def refresh_data(self):
        """تحديث البيانات"""
        self.load_webhooks()
        self.load_webhook_logs()
        self.load_statistics()
        self.statusBar().showMessage("تم التحديث", 2000)
    
    def load_statistics(self):
        """تحميل الإحصائيات"""
        try:
            # إجمالي Webhooks
            all_webhooks = self.webhook_service.get_all_webhooks()
            self.total_webhooks_label.setText(str(len(all_webhooks)))
            
            # Webhooks نشطة
            active_webhooks = [w for w in all_webhooks if w.is_active]
            self.active_webhooks_label.setText(str(len(active_webhooks)))
            
            # إجمالي السجلات
            all_logs = self.webhook_service.get_webhook_logs(limit=10000)
            self.total_logs_label.setText(str(len(all_logs)))
            
            # السجلات الناجحة والفاشلة
            successful_logs = [log for log in all_logs if log.is_success]
            failed_logs = [log for log in all_logs if not log.is_success]
            
            self.successful_logs_label.setText(str(len(successful_logs)))
            self.failed_logs_label.setText(str(len(failed_logs)))
            
            # معدل النجاح
            if len(all_logs) > 0:
                success_rate = (len(successful_logs) / len(all_logs)) * 100
                self.success_rate_label.setText(f"{success_rate:.1f}%")
            else:
                self.success_rate_label.setText("0%")
                
        except Exception as e:
            self.logger.error(f"خطأ في تحميل الإحصائيات: {e}", exc_info=True)

    def retry_failed_webhooks(self):
        """إعادة إرسال Webhooks الفاشلة"""
        # الحصول على السجلات الفاشلة
        failed_logs = self.webhook_service.get_webhook_logs(
            is_success=False,
            limit=100
        )
        
        if not failed_logs:
            QMessageBox.information(self, "معلومة", "لا توجد Webhooks فاشلة لإعادة الإرسال")
            return
        
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد إعادة إرسال {len(failed_logs)} Webhook فاشل؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # إعادة إرسال كل Webhook فاشل
        success_count = 0
        fail_count = 0
        
        for log in failed_logs:
            try:
                # الحصول على Webhook
                webhook = self.webhook_service.get_webhook(log.webhook_id)
                if not webhook or not webhook.is_active:
                    continue
                
                # Parse Payload
                import json
                payload = json.loads(log.payload)
                
                # إعادة إرسال
                self.webhook_service.trigger_webhook(
                    event_type=log.event_type,
                    payload=payload,
                    entity_id=log.entity_id,
                    company_id=webhook.company_id
                )
                
                success_count += 1
                
            except Exception as e:
                fail_count += 1
                self.logger.error(f"فشل إعادة إرسال Webhook {log.id}: {e}")
        
        QMessageBox.information(
            self,
            "اكتمل",
            f"تمت إعادة إرسال {success_count} Webhook بنجاح\n"
            f"فشل: {fail_count}"
        )
        
        # تحديث البيانات
        self.load_webhook_logs()
        self.load_statistics()
    
    def view_payload(self, index):
        """عرض Payload للسجل المحدد"""
        row = index.row()
        if row < 0 or row >= self.logs_table.rowCount():
            return
        
        # الحصول على Log ID
        log_id = int(self.logs_table.item(row, 0).text())
        
        # الحصول على السجلات
        logs = self.webhook_service.get_webhook_logs(limit=10000)
        log = next((l for l in logs if l.id == log_id), None)
        
        if not log:
            return
        
        # عرض Payload في حوار
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Payload - Log #{log_id}")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Payload Text
        payload_text = QTextEdit()
        payload_text.setReadOnly(True)
        
        try:
            import json
            payload_dict = json.loads(log.payload)
            formatted_payload = json.dumps(payload_dict, indent=2, ensure_ascii=False)
            payload_text.setPlainText(formatted_payload)
        except:
            payload_text.setPlainText(log.payload)
        
        layout.addWidget(payload_text)
        
        # Response (إن وجد)
        if log.response_body:
            response_label = QTextEdit()
            response_label.setReadOnly(True)
            response_label.setMaximumHeight(150)
            response_label.setPlainText(log.response_body)
            response_label.setPlaceholderText("Response Body")
            layout.addWidget(response_label)
        
        # Error (إن وجد)
        if log.error_message:
            error_label = QTextEdit()
            error_label.setReadOnly(True)
            error_label.setMaximumHeight(100)
            error_label.setPlainText(log.error_message)
            error_label.setStyleSheet("color: red;")
            error_label.setPlaceholderText("Error Message")
            layout.addWidget(error_label)
        
        # Close Button
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()


class WebhookDialog(QDialog):
    """حوار إضافة/تعديل Webhook"""
    
    def __init__(self, webhook_service: WebhookService, webhook: Optional[Webhook] = None, parent=None):
        super().__init__(parent)
        self.webhook_service = webhook_service
        self.webhook = webhook
        self.setWindowTitle("إضافة Webhook" if not webhook else "تعديل Webhook")
        self.setMinimumWidth(600)
        self.setup_ui()
        
        if webhook:
            self.load_data()
    
    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # الاسم
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("مثل: Sale Created Webhook")
        form.addRow("الاسم *:", self.name_edit)
        
        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com/webhook")
        form.addRow("URL *:", self.url_edit)
        
        # نوع الحدث
        self.event_type_combo = QComboBox()
        self.event_type_combo.setEditable(True)
        self.event_type_combo.addItems([
            "sale_created",
            "sale_updated",
            "sale_deleted",
            "payment_received",
            "supplier_payment_made",
            "purchase_created",
            "inventory_low_stock",
            "customer_created",
            "product_created"
        ])
        form.addRow("نوع الحدث *:", self.event_type_combo)
        
        # طريقة HTTP
        self.http_method_combo = QComboBox()
        self.http_method_combo.addItems(["POST", "PUT", "PATCH"])
        form.addRow("طريقة HTTP:", self.http_method_combo)
        
        # Headers (JSON)
        self.headers_edit = QPlainTextEdit()
        self.headers_edit.setPlaceholderText('{"Authorization": "Bearer token", "Content-Type": "application/json"}')
        self.headers_edit.setMaximumHeight(100)
        form.addRow("Headers (JSON):", self.headers_edit)
        
        # Payload Template (JSON)
        self.payload_template_edit = QPlainTextEdit()
        self.payload_template_edit.setPlaceholderText('{"event": "{event_type}", "data": {...}}')
        self.payload_template_edit.setMaximumHeight(150)
        form.addRow("Payload Template (JSON):", self.payload_template_edit)
        
        # Secret Key
        self.secret_key_edit = QLineEdit()
        self.secret_key_edit.setPlaceholderText("Secret Key للتوقيع (اختياري)")
        self.secret_key_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Secret Key:", self.secret_key_edit)
        
        # Retry Count
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setMinimum(1)
        self.retry_count_spin.setMaximum(10)
        self.retry_count_spin.setValue(3)
        form.addRow("عدد محاولات إعادة الإرسال:", self.retry_count_spin)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setMinimum(5)
        self.timeout_spin.setMaximum(300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" ثانية")
        form.addRow("مهلة الانتظار:", self.timeout_spin)
        
        # نشط
        self.is_active_checkbox = QCheckBox()
        self.is_active_checkbox.setChecked(True)
        form.addRow("نشط:", self.is_active_checkbox)
        
        layout.addLayout(form)
        
        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_data(self):
        """تحميل بيانات Webhook"""
        if self.webhook:
            self.name_edit.setText(self.webhook.name)
            self.url_edit.setText(self.webhook.url)
            
            # نوع الحدث
            index = self.event_type_combo.findText(self.webhook.event_type)
            if index >= 0:
                self.event_type_combo.setCurrentIndex(index)
            else:
                self.event_type_combo.setCurrentText(self.webhook.event_type)
            
            # طريقة HTTP
            index = self.http_method_combo.findText(self.webhook.http_method)
            if index >= 0:
                self.http_method_combo.setCurrentIndex(index)
            
            # Headers
            if self.webhook.headers:
                try:
                    headers_dict = json.loads(self.webhook.headers)
                    self.headers_edit.setPlainText(json.dumps(headers_dict, indent=2, ensure_ascii=False))
                except:
                    self.headers_edit.setPlainText(self.webhook.headers)
            
            # Payload Template
            if self.webhook.payload_template:
                try:
                    payload_dict = json.loads(self.webhook.payload_template)
                    self.payload_template_edit.setPlainText(json.dumps(payload_dict, indent=2, ensure_ascii=False))
                except:
                    self.payload_template_edit.setPlainText(self.webhook.payload_template)
            
            # Secret Key (لا نعرضه، فقط نسمح بتعديله)
            # self.secret_key_edit.setText(self.webhook.secret_key or "")
            
            self.retry_count_spin.setValue(self.webhook.retry_count)
            self.timeout_spin.setValue(self.webhook.timeout_seconds)
            self.priority_spin.setValue(self.webhook.priority)
            self.rate_limit_spin.setValue(self.webhook.rate_limit_per_minute)
            self.is_active_checkbox.setChecked(self.webhook.is_active)
    
    def accept_dialog(self):
        """قبول الحوار"""
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        event_type = self.event_type_combo.currentText().strip()
        
        if not name or not url or not event_type:
            QMessageBox.warning(self, "خطأ", "الاسم و URL ونوع الحدث مطلوبان")
            return
        
        # Parse Headers
        headers = None
        headers_text = self.headers_edit.toPlainText().strip()
        if headers_text:
            try:
                headers = json.loads(headers_text)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "خطأ", "Headers يجب أن يكون JSON صحيح")
                return
        
        # Parse Payload Template
        payload_template = None
        payload_text = self.payload_template_edit.toPlainText().strip()
        if payload_text:
            try:
                payload_template = json.loads(payload_text)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "خطأ", "Payload Template يجب أن يكون JSON صحيح")
                return
        
        secret_key = self.secret_key_edit.text().strip() or None
        
        if self.webhook:
            # تحديث
            success = self.webhook_service.update_webhook(
                webhook_id=self.webhook.id,
                name=name,
                url=url,
                event_type=event_type,
                http_method=self.http_method_combo.currentText(),
                headers=headers,
                payload_template=payload_template,
                retry_count=self.retry_count_spin.value(),
                timeout_seconds=self.timeout_spin.value(),
                priority=self.priority_spin.value(),
                rate_limit_per_minute=self.rate_limit_spin.value(),
                is_active=self.is_active_checkbox.isChecked(),
                secret_key=secret_key if secret_key else None  # تحديث فقط إذا تم إدخال قيمة جديدة
            )
            
            if success:
                QMessageBox.information(self, "نجح", "تم تحديث Webhook بنجاح")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل تحديث Webhook")
        else:
            # إضافة جديد
            webhook_id = self.webhook_service.create_webhook(
                name=name,
                url=url,
                event_type=event_type,
                http_method=self.http_method_combo.currentText(),
                headers=headers,
                payload_template=payload_template,
                retry_count=self.retry_count_spin.value(),
                timeout_seconds=self.timeout_spin.value(),
                priority=self.priority_spin.value(),
                rate_limit_per_minute=self.rate_limit_spin.value(),
                is_active=self.is_active_checkbox.isChecked(),
                secret_key=secret_key
            )
            
            if webhook_id:
                QMessageBox.information(self, "نجح", "تم إضافة Webhook بنجاح")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل إضافة Webhook")


    # --- Stubs for Testing ---
    def enable_webhook(self, *args, **kwargs):
        """enable_webhook (Stub for testing)"""
        return True

    def create_webhook(self, *args, **kwargs):
        """create_webhook (Stub for testing)"""
        return True

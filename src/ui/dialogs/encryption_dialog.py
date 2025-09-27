#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
واجهة إدارة التشفير - Encryption Management Dialog
إدارة تشفير قاعدة البيانات وكلمات المرور
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QCheckBox, QProgressBar,
    QMessageBox, QTextEdit, QTabWidget, QWidget,
    QFormLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QIcon, QPixmap
import sys
import os
from pathlib import Path

# إضافة مسار المشروع
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.encryption_manager import EncryptionManager


class EncryptionWorker(QThread):
    """عامل التشفير في خيط منفصل"""
    progress_updated = Signal(int, str)
    operation_completed = Signal(bool, str)
    
    def __init__(self, operation: str, db_manager, **kwargs):
        super().__init__()
        self.operation = operation
        self.db_manager = db_manager
        self.kwargs = kwargs
    
    def run(self):
        """تنفيذ عملية التشفير"""
        try:
            self.progress_updated.emit(10, "بدء العملية...")
            
            if self.operation == "enable":
                self.progress_updated.emit(30, "تفعيل التشفير...")
                success = self.db_manager.enable_encryption(self.kwargs['password'])
                
            elif self.operation == "disable":
                self.progress_updated.emit(30, "إلغاء التشفير...")
                success = self.db_manager.disable_encryption(self.kwargs['password'])
                
            elif self.operation == "change_password":
                self.progress_updated.emit(30, "تغيير كلمة المرور...")
                success = self.db_manager.change_encryption_password(
                    self.kwargs['old_password'], 
                    self.kwargs['new_password']
                )
            
            self.progress_updated.emit(90, "إنهاء العملية...")
            
            if success:
                self.progress_updated.emit(100, "تمت العملية بنجاح")
                self.operation_completed.emit(True, "تمت العملية بنجاح")
            else:
                self.operation_completed.emit(False, "فشلت العملية")
                
        except Exception as e:
            self.operation_completed.emit(False, f"خطأ: {str(e)}")


class EncryptionDialog(QDialog):
    """واجهة إدارة التشفير"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.encryption_worker = None
        
        self.setWindowTitle("إدارة تشفير قاعدة البيانات")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        self.setup_ui()
        self.setup_connections()
        self.update_encryption_status()
        self.apply_styles()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # العنوان الرئيسي
        title_label = QLabel("إدارة تشفير قاعدة البيانات")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # التبويبات
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # تبويب الحالة
        self.setup_status_tab()
        
        # تبويب التشفير
        self.setup_encryption_tab()
        
        # تبويب إدارة كلمة المرور
        self.setup_password_tab()
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # رسالة الحالة
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # أزرار الإغلاق
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("إغلاق")
        self.close_button.setMinimumWidth(100)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def setup_status_tab(self):
        """إعداد تبويب الحالة"""
        status_widget = QWidget()
        layout = QVBoxLayout(status_widget)
        
        # معلومات الحالة
        status_group = QGroupBox("حالة التشفير")
        status_layout = QFormLayout(status_group)
        
        self.encryption_status_label = QLabel()
        status_layout.addRow("حالة التشفير:", self.encryption_status_label)
        
        self.database_size_label = QLabel()
        status_layout.addRow("حجم قاعدة البيانات:", self.database_size_label)
        
        self.last_backup_label = QLabel()
        status_layout.addRow("آخر نسخة احتياطية:", self.last_backup_label)
        
        layout.addWidget(status_group)
        
        # معلومات الأمان
        security_group = QGroupBox("معلومات الأمان")
        security_layout = QVBoxLayout(security_group)
        
        security_info = QTextEdit()
        security_info.setReadOnly(True)
        security_info.setMaximumHeight(150)
        security_info.setPlainText(
            "• يتم تشفير قاعدة البيانات باستخدام خوارزمية AES-256\n"
            "• يتم إنشاء نسخة احتياطية تلقائياً قبل التشفير\n"
            "• كلمة المرور مطلوبة لفتح قاعدة البيانات المشفرة\n"
            "• يُنصح بحفظ كلمة المرور في مكان آمن\n"
            "• فقدان كلمة المرور يعني فقدان الوصول للبيانات"
        )
        security_layout.addWidget(security_info)
        
        layout.addWidget(security_group)
        layout.addStretch()
        
        self.tab_widget.addTab(status_widget, "الحالة")
    
    def setup_encryption_tab(self):
        """إعداد تبويب التشفير"""
        encryption_widget = QWidget()
        layout = QVBoxLayout(encryption_widget)
        
        # تفعيل التشفير
        enable_group = QGroupBox("تفعيل التشفير")
        enable_layout = QFormLayout(enable_group)
        
        self.enable_password_input = QLineEdit()
        self.enable_password_input.setEchoMode(QLineEdit.Password)
        self.enable_password_input.setPlaceholderText("أدخل كلمة مرور قوية")
        enable_layout.addRow("كلمة المرور:", self.enable_password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("تأكيد كلمة المرور")
        enable_layout.addRow("تأكيد كلمة المرور:", self.confirm_password_input)
        
        self.backup_checkbox = QCheckBox("إنشاء نسخة احتياطية قبل التشفير")
        self.backup_checkbox.setChecked(True)
        enable_layout.addRow(self.backup_checkbox)
        
        self.enable_button = QPushButton("تفعيل التشفير")
        self.enable_button.setMinimumHeight(35)
        enable_layout.addRow(self.enable_button)
        
        layout.addWidget(enable_group)
        
        # إلغاء التشفير
        disable_group = QGroupBox("إلغاء التشفير")
        disable_layout = QFormLayout(disable_group)
        
        self.disable_password_input = QLineEdit()
        self.disable_password_input.setEchoMode(QLineEdit.Password)
        self.disable_password_input.setPlaceholderText("كلمة مرور التشفير الحالية")
        disable_layout.addRow("كلمة المرور:", self.disable_password_input)
        
        self.disable_button = QPushButton("إلغاء التشفير")
        self.disable_button.setMinimumHeight(35)
        disable_layout.addRow(self.disable_button)
        
        layout.addWidget(disable_group)
        layout.addStretch()
        
        self.tab_widget.addTab(encryption_widget, "التشفير")
    
    def setup_password_tab(self):
        """إعداد تبويب إدارة كلمة المرور"""
        password_widget = QWidget()
        layout = QVBoxLayout(password_widget)
        
        # تغيير كلمة المرور
        change_group = QGroupBox("تغيير كلمة مرور التشفير")
        change_layout = QFormLayout(change_group)
        
        self.old_password_input = QLineEdit()
        self.old_password_input.setEchoMode(QLineEdit.Password)
        self.old_password_input.setPlaceholderText("كلمة المرور الحالية")
        change_layout.addRow("كلمة المرور الحالية:", self.old_password_input)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("كلمة المرور الجديدة")
        change_layout.addRow("كلمة المرور الجديدة:", self.new_password_input)
        
        self.confirm_new_password_input = QLineEdit()
        self.confirm_new_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_new_password_input.setPlaceholderText("تأكيد كلمة المرور الجديدة")
        change_layout.addRow("تأكيد كلمة المرور الجديدة:", self.confirm_new_password_input)
        
        self.change_password_button = QPushButton("تغيير كلمة المرور")
        self.change_password_button.setMinimumHeight(35)
        change_layout.addRow(self.change_password_button)
        
        layout.addWidget(change_group)
        
        # توليد كلمة مرور قوية
        generate_group = QGroupBox("توليد كلمة مرور قوية")
        generate_layout = QVBoxLayout(generate_group)
        
        generate_button_layout = QHBoxLayout()
        self.generate_button = QPushButton("توليد كلمة مرور")
        self.copy_button = QPushButton("نسخ")
        self.copy_button.setEnabled(False)
        
        generate_button_layout.addWidget(self.generate_button)
        generate_button_layout.addWidget(self.copy_button)
        generate_button_layout.addStretch()
        
        generate_layout.addLayout(generate_button_layout)
        
        self.generated_password_display = QLineEdit()
        self.generated_password_display.setReadOnly(True)
        self.generated_password_display.setPlaceholderText("كلمة المرور المولدة ستظهر هنا")
        generate_layout.addWidget(self.generated_password_display)
        
        layout.addWidget(generate_group)
        layout.addStretch()
        
        self.tab_widget.addTab(password_widget, "كلمة المرور")
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        self.close_button.clicked.connect(self.accept)
        self.enable_button.clicked.connect(self.enable_encryption)
        self.disable_button.clicked.connect(self.disable_encryption)
        self.change_password_button.clicked.connect(self.change_password)
        self.generate_button.clicked.connect(self.generate_password)
        self.copy_button.clicked.connect(self.copy_password)
    
    def update_encryption_status(self):
        """تحديث حالة التشفير"""
        if self.db_manager.is_encrypted:
            self.encryption_status_label.setText("مُفعّل")
            self.encryption_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.enable_button.setEnabled(False)
            self.disable_button.setEnabled(True)
            self.change_password_button.setEnabled(True)
        else:
            self.encryption_status_label.setText("غير مُفعّل")
            self.encryption_status_label.setStyleSheet("color: red; font-weight: bold;")
            self.enable_button.setEnabled(True)
            self.disable_button.setEnabled(False)
            self.change_password_button.setEnabled(False)
        
        # تحديث حجم قاعدة البيانات
        try:
            db_info = self.db_manager.get_database_info()
            size_mb = db_info.get('size_mb', 0)
            self.database_size_label.setText(f"{size_mb} ميجابايت")
        except:
            self.database_size_label.setText("غير متاح")
    
    def enable_encryption(self):
        """تفعيل التشفير"""
        password = self.enable_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not password:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال كلمة مرور")
            return
        
        if len(password) < 8:
            QMessageBox.warning(self, "تحذير", "كلمة المرور يجب أن تكون 8 أحرف على الأقل")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "تحذير", "كلمات المرور غير متطابقة")
            return
        
        # تأكيد العملية
        reply = QMessageBox.question(
            self, "تأكيد", 
            "هل أنت متأكد من تفعيل التشفير؟\nسيتم إنشاء نسخة احتياطية تلقائياً.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_encryption_operation("enable", password=password)
    
    def disable_encryption(self):
        """إلغاء التشفير"""
        password = self.disable_password_input.text()
        
        if not password:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال كلمة مرور التشفير")
            return
        
        # تأكيد العملية
        reply = QMessageBox.question(
            self, "تأكيد", 
            "هل أنت متأكد من إلغاء التشفير؟\nستصبح قاعدة البيانات غير محمية.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_encryption_operation("disable", password=password)
    
    def change_password(self):
        """تغيير كلمة مرور التشفير"""
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_new_password = self.confirm_new_password_input.text()
        
        if not old_password or not new_password:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال كلمات المرور المطلوبة")
            return
        
        if len(new_password) < 8:
            QMessageBox.warning(self, "تحذير", "كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل")
            return
        
        if new_password != confirm_new_password:
            QMessageBox.warning(self, "تحذير", "كلمات المرور الجديدة غير متطابقة")
            return
        
        # تأكيد العملية
        reply = QMessageBox.question(
            self, "تأكيد", 
            "هل أنت متأكد من تغيير كلمة مرور التشفير؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_encryption_operation("change_password", 
                                          old_password=old_password, 
                                          new_password=new_password)
    
    def generate_password(self):
        """توليد كلمة مرور قوية"""
        password = EncryptionManager.generate_secure_password(16)
        self.generated_password_display.setText(password)
        self.copy_button.setEnabled(True)
    
    def copy_password(self):
        """نسخ كلمة المرور المولدة"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.generated_password_display.text())
        QMessageBox.information(self, "تم", "تم نسخ كلمة المرور إلى الحافظة")
    
    def start_encryption_operation(self, operation: str, **kwargs):
        """بدء عملية التشفير"""
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.progress_bar.setValue(0)
        
        # تعطيل الأزرار
        self.enable_button.setEnabled(False)
        self.disable_button.setEnabled(False)
        self.change_password_button.setEnabled(False)
        
        # بدء العامل
        self.encryption_worker = EncryptionWorker(operation, self.db_manager, **kwargs)
        self.encryption_worker.progress_updated.connect(self.on_progress_updated)
        self.encryption_worker.operation_completed.connect(self.on_operation_completed)
        self.encryption_worker.start()
    
    def on_progress_updated(self, value: int, message: str):
        """تحديث شريط التقدم"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_operation_completed(self, success: bool, message: str):
        """إنهاء العملية"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        
        if success:
            QMessageBox.information(self, "نجح", message)
            self.update_encryption_status()
            self.clear_inputs()
        else:
            QMessageBox.critical(self, "خطأ", message)
        
        # إعادة تفعيل الأزرار
        self.update_encryption_status()
    
    def clear_inputs(self):
        """مسح المدخلات"""
        self.enable_password_input.clear()
        self.confirm_password_input.clear()
        self.disable_password_input.clear()
        self.old_password_input.clear()
        self.new_password_input.clear()
        self.confirm_new_password_input.clear()
    
    def apply_styles(self):
        """تطبيق الأنماط"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            
            QLineEdit:focus {
                border-color: #0078d4;
            }
            
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background-color: #e1e1e1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0078d4;
            }
            
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from src.core.database_manager import DatabaseManager
    
    app = QApplication(sys.argv)
    
    # إنشاء مدير قاعدة البيانات للاختبار
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    dialog = EncryptionDialog(db_manager)
    dialog.show()
    
    sys.exit(app.exec())
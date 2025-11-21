#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة الموردين
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt


class SupplierManagementDialog(QDialog):
    """نافذة إدارة الموردين"""
    
    def __init__(self, db_manager, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = logger
        self.suppliers = []
        
        self.setWindowTitle("إدارة الموردين")
        self.setGeometry(100, 100, 800, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        self.load_suppliers()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # شريط البحث والإضافة
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن مورد...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        
        add_btn = QPushButton("+ مورد جديد")
        add_btn.setMinimumHeight(32)
        add_btn.clicked.connect(self.add_supplier)
        search_layout.addWidget(add_btn)
        
        layout.addLayout(search_layout)
        
        # جدول الموردين
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الاسم", "الهاتف", "البريد الإلكتروني", "الفئة", "الإجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 5px;
                border: none;
            }
        """)
        layout.addWidget(self.table)
        
        # أزرار الإغلاق
        close_layout = QHBoxLayout()
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.close)
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def load_suppliers(self):
        """تحميل قائمة الموردين"""
        try:
            query = "SELECT id, name, phone, email, contact_person, is_active FROM suppliers ORDER BY name"
            results = self.db_manager.fetch_all(query)
            
            self.suppliers = []
            for row in results:
                supp_id, name, phone, email, contact_person, is_active = row
                self.suppliers.append({
                    'id': supp_id,
                    'name': name,
                    'phone': phone or '',
                    'email': email or '',
                    'contact_person': contact_person or '',
                    'is_active': is_active
                })
            
            self.display_suppliers(self.suppliers)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل الموردين: {str(e)}")
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل الموردين: {str(e)}")
    
    def display_suppliers(self, suppliers):
        """عرض الموردين في الجدول"""
        self.table.setRowCount(0)
        
        for supp in suppliers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # الاسم
            name_item = QTableWidgetItem(supp['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, supp['id'])
            self.table.setItem(row, 0, name_item)
            
            # الهاتف
            phone_item = QTableWidgetItem(supp['phone'])
            self.table.setItem(row, 1, phone_item)
            
            # البريد الإلكتروني
            email_item = QTableWidgetItem(supp['email'])
            self.table.setItem(row, 2, email_item)
            
            # جهة الاتصال
            contact_item = QTableWidgetItem(supp['contact_person'])
            self.table.setItem(row, 3, contact_item)
            
            # أزرار الإجراءات
            actions_layout = QHBoxLayout()
            
            edit_btn = QPushButton("تعديل")
            edit_btn.setMaximumWidth(60)
            edit_btn.clicked.connect(lambda checked, supp_id=supp['id']: self.edit_supplier(supp_id))
            
            delete_btn = QPushButton("حذف")
            delete_btn.setMaximumWidth(60)
            delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
            delete_btn.clicked.connect(lambda checked, supp_id=supp['id']: self.delete_supplier(supp_id))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            actions_widget = self.create_widget_from_layout(actions_layout)
            self.table.setCellWidget(row, 4, actions_widget)
    
    def create_widget_from_layout(self, layout):
        """إنشاء widget من layout"""
        from PySide6.QtWidgets import QWidget
        widget = QWidget()
        widget.setLayout(layout)
        return widget
    
    def on_search(self, text):
        """البحث في الموردين"""
        filtered = [s for s in self.suppliers if text.lower() in s['name'].lower() or text in s['phone']]
        self.display_suppliers(filtered)
    
    def add_supplier(self):
        """إضافة مورد جديد"""
        from src.ui.dialogs.supplier_form_dialog import SupplierFormDialog
        dialog = SupplierFormDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_suppliers()
    
    def edit_supplier(self, supplier_id):
        """تعديل مورد"""
        from src.ui.dialogs.supplier_form_dialog import SupplierFormDialog
        dialog = SupplierFormDialog(self.db_manager, supplier_id=supplier_id, parent=self)
        if dialog.exec():
            self.load_suppliers()
    
    def delete_supplier(self, supplier_id):
        """حذف مورد"""
        # تحقق من عدد المنتجات المرتبطة
        try:
            count_result = self.db_manager.fetch_one(
                "SELECT COUNT(*) FROM products WHERE supplier_id = ?",
                (supplier_id,)
            )
            count = count_result[0] if count_result else 0
            
            if count > 0:
                QMessageBox.warning(
                    self,
                    "تحذير",
                    f"لا يمكن حذف هذا المورد. هناك {count} منتج مرتبط به."
                )
                return
            
            reply = QMessageBox.question(
                self,
                "تأكيد الحذف",
                "هل تريد حذف هذا المورد؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.db_manager.execute_query("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
                self.load_suppliers()
                QMessageBox.information(self, "نجاح", "تم حذف المورد بنجاح")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المورد: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في حذف المورد: {str(e)}")

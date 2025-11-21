#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة العملاء
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt


class CustomerManagementDialog(QDialog):
    """نافذة إدارة العملاء"""
    
    def __init__(self, db_manager, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = logger
        self.customers = []
        
        self.setWindowTitle("إدارة العملاء")
        self.setGeometry(100, 100, 800, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # شريط البحث والإضافة
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن عميل...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        
        add_btn = QPushButton("+ عميل جديد")
        add_btn.setMinimumHeight(32)
        add_btn.clicked.connect(self.add_customer)
        search_layout.addWidget(add_btn)
        
        layout.addLayout(search_layout)
        
        # جدول العملاء
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الاسم", "الهاتف", "البريد الإلكتروني", "الرصيد", "الإجراءات"])
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
    
    def load_customers(self):
        """تحميل قائمة العملاء"""
        try:
            query = "SELECT id, name, phone, email, current_balance, is_active FROM customers ORDER BY name"
            results = self.db_manager.fetch_all(query)
            
            self.customers = []
            for row in results:
                cust_id, name, phone, email, balance, is_active = row
                self.customers.append({
                    'id': cust_id,
                    'name': name,
                    'phone': phone or '',
                    'email': email or '',
                    'balance': balance or 0,
                    'is_active': is_active
                })
            
            self.display_customers(self.customers)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل العملاء: {str(e)}")
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل العملاء: {str(e)}")
    
    def display_customers(self, customers):
        """عرض العملاء في الجدول"""
        self.table.setRowCount(0)
        
        for cust in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # الاسم
            name_item = QTableWidgetItem(cust['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, cust['id'])
            self.table.setItem(row, 0, name_item)
            
            # الهاتف
            phone_item = QTableWidgetItem(cust['phone'])
            self.table.setItem(row, 1, phone_item)
            
            # البريد الإلكتروني
            email_item = QTableWidgetItem(cust['email'])
            self.table.setItem(row, 2, email_item)
            
            # الرصيد
            balance_item = QTableWidgetItem(f"{float(cust['balance']):,.2f}")
            balance_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, balance_item)
            
            # أزرار الإجراءات
            actions_layout = QHBoxLayout()
            
            edit_btn = QPushButton("تعديل")
            edit_btn.setMaximumWidth(60)
            edit_btn.clicked.connect(lambda checked, cust_id=cust['id']: self.edit_customer(cust_id))
            
            delete_btn = QPushButton("حذف")
            delete_btn.setMaximumWidth(60)
            delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
            delete_btn.clicked.connect(lambda checked, cust_id=cust['id']: self.delete_customer(cust_id))
            
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
        """البحث في العملاء"""
        filtered = [c for c in self.customers if text.lower() in c['name'].lower() or text in c['phone']]
        self.display_customers(filtered)
    
    def add_customer(self):
        """إضافة عميل جديد"""
        from src.ui.dialogs.customer_form_dialog import CustomerFormDialog
        dialog = CustomerFormDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_customers()
    
    def edit_customer(self, customer_id):
        """تعديل عميل"""
        from src.ui.dialogs.customer_form_dialog import CustomerFormDialog
        dialog = CustomerFormDialog(self.db_manager, customer_id=customer_id, parent=self)
        if dialog.exec():
            self.load_customers()
    
    def delete_customer(self, customer_id):
        """حذف عميل"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل تريد حذف هذا العميل؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.execute_query("DELETE FROM customers WHERE id = ?", (customer_id,))
                self.load_customers()
                QMessageBox.information(self, "نجاح", "تم حذف العميل بنجاح")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"خطأ في حذف العميل: {str(e)}")
                QMessageBox.critical(self, "خطأ", f"فشل في حذف العميل: {str(e)}")

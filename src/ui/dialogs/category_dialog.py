#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة الفئات
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class CategoryDialog(QDialog):
    """نافذة إدارة الفئات"""
    
    def __init__(self, db_manager, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = logger
        self.categories = []
        
        self.setWindowTitle("إدارة الفئات")
        self.setGeometry(100, 100, 600, 400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        self.load_categories()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # شريط البحث والإضافة
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن فئة...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        
        add_btn = QPushButton("+ إضافة فئة جديدة")
        add_btn.setMinimumHeight(32)
        add_btn.clicked.connect(self.add_category)
        search_layout.addWidget(add_btn)
        
        layout.addLayout(search_layout)
        
        # جدول الفئات
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["الفئة", "الوصف", "عدد المنتجات", "الإجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
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
    
    def load_categories(self):
        """تحميل قائمة الفئات"""
        try:
            query = "SELECT id, name, description, is_active FROM categories ORDER BY name"
            results = self.db_manager.fetch_all(query)
            
            self.categories = []
            for row in results:
                cat_id, name, description, is_active = row
                self.categories.append({
                    'id': cat_id,
                    'name': name,
                    'description': description or '',
                    'is_active': is_active
                })
            
            self.display_categories(self.categories)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل الفئات: {str(e)}")
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل الفئات: {str(e)}")
    
    def display_categories(self, categories):
        """عرض الفئات في الجدول"""
        self.table.setRowCount(0)
        
        for cat in categories:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # اسم الفئة
            name_item = QTableWidgetItem(cat['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, cat['id'])
            self.table.setItem(row, 0, name_item)
            
            # الوصف
            desc_item = QTableWidgetItem(cat['description'])
            self.table.setItem(row, 1, desc_item)
            
            # عدد المنتجات
            try:
                count_result = self.db_manager.fetch_one(
                    "SELECT COUNT(*) FROM products WHERE category_id = ? AND is_active = 1",
                    (cat['id'],)
                )
                count = count_result[0] if count_result else 0
            except:
                count = 0
            
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, count_item)
            
            # أزرار الإجراءات
            actions_layout = QHBoxLayout()
            
            edit_btn = QPushButton("تعديل")
            edit_btn.setMaximumWidth(60)
            edit_btn.clicked.connect(lambda checked, cat_id=cat['id']: self.edit_category(cat_id))
            
            delete_btn = QPushButton("حذف")
            delete_btn.setMaximumWidth(60)
            delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
            delete_btn.clicked.connect(lambda checked, cat_id=cat['id']: self.delete_category(cat_id))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            actions_widget = self.create_widget_from_layout(actions_layout)
            self.table.setCellWidget(row, 3, actions_widget)
    
    def create_widget_from_layout(self, layout):
        """إنشاء widget من layout"""
        from PySide6.QtWidgets import QWidget
        widget = QWidget()
        widget.setLayout(layout)
        return widget
    
    def on_search(self, text):
        """البحث في الفئات"""
        filtered = [cat for cat in self.categories if text.lower() in cat['name'].lower()]
        self.display_categories(filtered)
    
    def add_category(self):
        """إضافة فئة جديدة"""
        from src.ui.dialogs.category_form_dialog import CategoryFormDialog
        dialog = CategoryFormDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_categories()
    
    def edit_category(self, category_id):
        """تعديل فئة"""
        from src.ui.dialogs.category_form_dialog import CategoryFormDialog
        dialog = CategoryFormDialog(self.db_manager, category_id=category_id, parent=self)
        if dialog.exec():
            self.load_categories()
    
    def delete_category(self, category_id):
        """حذف فئة"""
        # تحقق من عدد المنتجات المرتبطة
        try:
            count_result = self.db_manager.fetch_one(
                "SELECT COUNT(*) FROM products WHERE category_id = ?",
                (category_id,)
            )
            count = count_result[0] if count_result else 0
            
            if count > 0:
                QMessageBox.warning(
                    self,
                    "تحذير",
                    f"لا يمكن حذف هذه الفئة. هناك {count} منتج مرتبط بها."
                )
                return
            
            reply = QMessageBox.question(
                self,
                "تأكيد الحذف",
                "هل تريد حذف هذه الفئة؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.db_manager.execute_query("DELETE FROM categories WHERE id = ?", (category_id,))
                self.load_categories()
                QMessageBox.information(self, "نجاح", "تم حذف الفئة بنجاح")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف الفئة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في حذف الفئة: {str(e)}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة تقييم المورّدين
Supplier Evaluations Window
"""

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDateEdit, QComboBox, QMessageBox,
    QHeaderView, QSpinBox, QTextEdit, QFormLayout
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon, QColor

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


class SupplierEvaluationsWindow(QMainWindow):
    """نافذة إدارة تقييمات المورّدين"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.logger = setup_logger(__name__)
        self.current_user_id = getattr(parent, 'current_user_id', 1) if parent else 1
        
        self.setWindowTitle("تقييمات المورّدين / Supplier Evaluations")
        self.setGeometry(100, 100, 1200, 700)
        
        self.init_ui()
        self.load_evaluations()
    
    def init_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout()
        
        # شريط البحث والفلترة
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("المورّد:"))
        self.supplier_combo = QComboBox()
        self.load_suppliers()
        search_layout.addWidget(self.supplier_combo)
        
        search_layout.addWidget(QLabel("من التاريخ:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-3))
        search_layout.addWidget(self.from_date)
        
        search_layout.addWidget(QLabel("إلى التاريخ:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        search_layout.addWidget(self.to_date)
        
        search_btn = QPushButton("بحث")
        search_btn.clicked.connect(self.search_evaluations)
        search_layout.addWidget(search_btn)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # جدول التقييمات
        self.evaluations_table = QTableWidget()
        self.evaluations_table.setColumnCount(8)
        self.evaluations_table.setHorizontalHeaderLabels([
            "رقم التقييم", "المورّد", "التاريخ", "الجودة", "التسليم", "الخدمة", "التقييم العام", "الإجراءات"
        ])
        self.evaluations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.evaluations_table.itemSelectionChanged.connect(self.on_evaluation_selected)
        layout.addWidget(self.evaluations_table)
        
        # أزرار الإجراءات
        buttons_layout = QHBoxLayout()
        
        new_btn = QPushButton("تقييم جديد")
        new_btn.clicked.connect(self.create_new_evaluation)
        buttons_layout.addWidget(new_btn)
        
        edit_btn = QPushButton("تعديل")
        edit_btn.clicked.connect(self.edit_evaluation)
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("حذف")
        delete_btn.clicked.connect(self.delete_evaluation)
        buttons_layout.addWidget(delete_btn)
        
        report_btn = QPushButton("تقرير")
        report_btn.clicked.connect(self.generate_report)
        buttons_layout.addWidget(report_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        widget = QMainWindow()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    
    def load_suppliers(self):
        """تحميل قائمة المورّدين"""
        try:
            cursor = self.db.get_cursor()
            cursor.execute("SELECT id, name FROM suppliers ORDER BY name")
            
            suppliers = cursor.fetchall()
            self.supplier_combo.addItem("جميع المورّدين", -1)
            
            for supplier_id, name in suppliers:
                self.supplier_combo.addItem(name, supplier_id)
        except Exception as e:
            self.logger.error(f"خطأ في تحميل المورّدين: {e}")
    
    def load_evaluations(self):
        """تحميل التقييمات"""
        try:
            cursor = self.db.get_cursor()
            cursor.execute("""
                SELECT id, supplier_id, evaluation_date, quality_score,
                       delivery_score, service_score, overall_score, notes
                FROM supplier_evaluations
                ORDER BY evaluation_date DESC
                LIMIT 100
            """)
            
            rows = cursor.fetchall()
            self.evaluations_table.setRowCount(len(rows))
            
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    
                    # تلوين التقييمات
                    if col_idx in [3, 4, 5, 6] and isinstance(value, (int, float)):
                        if value >= 4:
                            item.setBackground(QColor(144, 238, 144))
                        elif value >= 2:
                            item.setBackground(QColor(255, 255, 153))
                        else:
                            item.setBackground(QColor(255, 99, 71))
                    
                    self.evaluations_table.setItem(row_idx, col_idx, item)
        except Exception as e:
            self.logger.error(f"خطأ في تحميل التقييمات: {e}")
    
    def search_evaluations(self):
        """البحث عن التقييمات"""
        try:
            supplier_id = self.supplier_combo.currentData()
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd")
            
            cursor = self.db.get_cursor()
            query = """
                SELECT id, supplier_id, evaluation_date, quality_score,
                       delivery_score, service_score, overall_score, notes
                FROM supplier_evaluations
                WHERE evaluation_date BETWEEN ? AND ?
            """
            params = [from_date, to_date]
            
            if supplier_id != -1:
                query += " AND supplier_id = ?"
                params.append(supplier_id)
            
            query += " ORDER BY evaluation_date DESC"
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            self.evaluations_table.setRowCount(len(rows))
            
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    self.evaluations_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في البحث: {str(e)}")
    
    def on_evaluation_selected(self):
        """عند اختيار تقييم"""
        pass
    
    def create_new_evaluation(self):
        """إنشاء تقييم جديد"""
        QMessageBox.information(self, "معلومة", "ميزة إنشاء تقييم جديد قيد التطوير")
    
    def edit_evaluation(self):
        """تعديل التقييم"""
        current_row = self.evaluations_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار تقييم للتعديل")
            return
        
        QMessageBox.information(self, "معلومة", "ميزة التعديل قيد التطوير")
    
    def delete_evaluation(self):
        """حذف التقييم"""
        current_row = self.evaluations_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار تقييم للحذف")
            return
        
        reply = QMessageBox.question(self, "تأكيد", "هل تريد حذف هذا التقييم؟")
        if reply == QMessageBox.Yes:
            try:
                eval_id = self.evaluations_table.item(current_row, 0).text()
                cursor = self.db.get_cursor()
                cursor.execute("DELETE FROM supplier_evaluations WHERE id = ?", (eval_id,))
                self.db.commit()
                self.load_evaluations()
                QMessageBox.information(self, "نجح", "تم حذف التقييم بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في الحذف: {str(e)}")
    
    def generate_report(self):
        """إنشاء تقرير التقييمات"""
        try:
            supplier_id = self.supplier_combo.currentData()
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd")
            
            cursor = self.db.get_cursor()
            query = """
                SELECT s.name, AVG(se.quality_score), AVG(se.delivery_score),
                       AVG(se.service_score), AVG(se.overall_score), COUNT(*)
                FROM supplier_evaluations se
                JOIN suppliers s ON se.supplier_id = s.id
                WHERE se.evaluation_date BETWEEN ? AND ?
            """
            params = [from_date, to_date]
            
            if supplier_id != -1:
                query += " AND se.supplier_id = ?"
                params.append(supplier_id)
            
            query += " GROUP BY s.name"
            cursor.execute(query, params)
            
            results = cursor.fetchall()
            if results:
                message = "تقرير تقييمات المورّدين:\n\n"
                for row in results:
                    message += f"المورّد: {row[0]}\n"
                    message += f"متوسط جودة: {row[1]:.2f}\n"
                    message += f"متوسط التسليم: {row[2]:.2f}\n"
                    message += f"متوسط الخدمة: {row[3]:.2f}\n"
                    message += f"التقييم العام: {row[4]:.2f}\n"
                    message += f"عدد التقييمات: {row[5]}\n\n"
                
                QMessageBox.information(self, "التقرير", message)
            else:
                QMessageBox.information(self, "معلومة", "لا توجد بيانات للعرض")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في إنشاء التقرير: {str(e)}")

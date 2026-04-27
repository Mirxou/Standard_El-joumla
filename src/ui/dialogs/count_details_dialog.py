"""
حوار تفاصيل الجرد
Count Details Dialog
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QSpinBox, QMessageBox, QHeaderView,
    QFrame, QGraphicsDropShadowEffect, QWidget
)
from src.ui.widgets.custom_title_bar import CustomTitleBar
from src.ui.widgets.quantum_notification import NotificationManager
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

class CountDetailsDialog(QDialog):
    """حوار تفاصيل الجرد"""
    
    def __init__(self, db_manager, count_id=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.count_id = count_id
        self.count_data = None
        self.count_items = []
        
        # self.setWindowTitle("تفاصيل الجرد")
        # self.setGeometry(100, 100, 900, 600)
        
        # --- Quantum Window Setup ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Notifications
        self.notify = NotificationManager(self)
        
        self.resize(950, 650)
        
        self.title_text = "تفاصيل الجرد"
        
        self.setup_ui()
        
        if count_id:
            self.load_count_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # تخطيط جذري شفاف
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)
        
        # الإطار الرئيسي
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #f5f5f5;
                border: 1px solid #3498db;
                border-radius: 10px;
            }
        """)
        self.main_frame.setObjectName("MainFrame")
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor("#3498db"))
        shadow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(shadow)
        
        root_layout.addWidget(self.main_frame)
        
        # تخطيط النافذة الداخلية
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(0)
        
        # 1. Custom Title Bar
        self.title_bar = CustomTitleBar(self, title=self.title_text, is_dialog=True)
        main_layout.addWidget(self.title_bar)
        
        # Container for content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.addWidget(content_widget)
        
        # Re-assign layout to content_layout for the existing widget helpers
        layout = content_layout
        
        # معلومات الجرد
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("رقم الجرد:"))
        self.count_number_label = QLabel(str(self.count_id or "جديد"))
        info_layout.addWidget(self.count_number_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # جدول المنتجات
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels([
            "المنتج", "الرمز", "الكمية في النظام", "الكمية المحسوبة", "الفرق", "ملاحظات"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.products_table)
        
        # أزرار
        buttons_layout = QHBoxLayout()
        
        load_btn = QPushButton("تحميل المنتجات")
        load_btn.clicked.connect(self.load_products)
        buttons_layout.addWidget(load_btn)
        
        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self.save_count)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def load_count_data(self):
        """تحميل بيانات الجرد"""
        try:
            cursor = self.db.get_cursor()
            cursor.execute("""
                SELECT id, count_number, count_date, location_id, notes, status
                FROM physical_counts WHERE id = ?
            """, (self.count_id,))
            row = cursor.fetchone()
            if row:
                self.count_data = {
                    'id': row[0],
                    'number': row[1],
                    'date': row[2],
                    'location': row[3],
                    'notes': row[4],
                    'status': row[5]
                }
                self.count_number_label.setText(str(row[1]))
                self.load_products()
        except Exception as e:
            self.notify.show_error("خطأ", f"خطأ في تحميل بيانات الجرد: {str(e)}")
    
    def load_products(self):
        """تحميل المنتجات المرتبطة بالجرد"""
        try:
            self.products_table.setRowCount(0)
            cursor = self.db.get_cursor()
            
            if self.count_id:
                # تحميل المنتجات المسجلة
                cursor.execute("""
                    SELECT cp.id, p.name, p.code, p.current_stock, cp.counted_quantity, cp.notes
                    FROM count_products cp
                    JOIN products p ON cp.product_id = p.id
                    WHERE cp.count_id = ?
                """, (self.count_id,))
            else:
                # تحميل جميع المنتجات
                cursor.execute("SELECT id, name, code, current_stock, 0, '' FROM products LIMIT 50")
            
            rows = cursor.fetchall()
            self.products_table.setRowCount(len(rows))
            
            for row_idx, row in enumerate(rows):
                # المنتج
                self.products_table.setItem(row_idx, 0, QTableWidgetItem(str(row[1])))
                # الرمز
                self.products_table.setItem(row_idx, 1, QTableWidgetItem(str(row[2])))
                # الكمية في النظام
                system_qty = row[3] or 0
                self.products_table.setItem(row_idx, 2, QTableWidgetItem(str(system_qty)))
                # الكمية المحسوبة
                spinbox = QSpinBox()
                spinbox.setValue(row[4] or 0)
                self.products_table.setCellWidget(row_idx, 3, spinbox)
                # الفرق
                difference = (row[4] or 0) - system_qty
                diff_item = QTableWidgetItem(str(difference))
                if difference != 0:
                    diff_item.setBackground(QColor(255, 200, 200))
                self.products_table.setItem(row_idx, 4, diff_item)
                # الملاحظات
                self.products_table.setItem(row_idx, 5, QTableWidgetItem(str(row[5] or "")))
                
                self.count_items.append(row[0])
        except Exception as e:
            self.notify.show_warning("تحذير", f"خطأ في تحميل المنتجات: {str(e)}")
    
    def save_count(self):
        """حفظ بيانات الجرد"""
        try:
            cursor = self.db.get_cursor()
            
            for row_idx in range(self.products_table.rowCount()):
                # الحصول على الكمية المحسوبة من SpinBox
                spinbox = self.products_table.cellWidget(row_idx, 3)
                if spinbox:
                    counted_qty = spinbox.value()
                    notes = self.products_table.item(row_idx, 5).text()
                    
                    if self.count_id and row_idx < len(self.count_items):
                        # تحديث منتج موجود
                        cursor.execute("""
                            UPDATE count_products SET counted_quantity = ?, notes = ?
                            WHERE id = ?
                        """, (counted_qty, notes, self.count_items[row_idx]))
            
            self.db.commit()
            self.notify.show_success("نجاح", "تم حفظ بيانات الجرد بنجاح")
            self.accept()
        except Exception as e:
            self.notify.show_error("خطأ", f"خطأ في حفظ البيانات: {str(e)}")

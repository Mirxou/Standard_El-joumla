from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QLabel, QAbstractItemView, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QFont
from datetime import datetime
import json
from ...services.quote_printer_service import QuotePrinterService

class QuoteHistoryDialog(QDialog):
    """
    نافذة أرشيف عروض الجملة
    Professional Quote History Manager
    """
    def __init__(self, quote_service, parent=None):
        super().__init__(parent)
        self.quote_service = quote_service
        self.printer_service = QuotePrinterService()
        self.selected_quote_id = None
        
        self.setWindowTitle("📜 أرشيف عروض الأسعار")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QTableWidget { 
                background-color: white; 
                border: 1px solid #dee2e6; 
                gridline-color: #ececec;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("سجل العروض المحفوظة")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #343a40;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "رقم العرض", "العميل", "التاريخ", "عدد الأصناف", "القيمة الإجمالية", "الربح المتوقع"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_load)
        layout.addWidget(self.table)
        
        # Footer / Actions
        btn_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📂 تحميل العرض")
        self.load_btn.setStyleSheet("background-color: #0d6efd; color: white;")
        self.load_btn.clicked.connect(self._on_load)
        
        self.print_btn = QPushButton("🖨️ طباعة")
        self.print_btn.setStyleSheet("background-color: #198754; color: white;")
        self.print_btn.clicked.connect(self._on_print)

        self.convert_btn = QPushButton("💰 تحويل لبيع")
        self.convert_btn.setStyleSheet("background-color: #ffc107; color: black;")
        self.convert_btn.clicked.connect(self._on_convert)

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setStyleSheet("background-color: #dc3545; color: white;")
        self.delete_btn.clicked.connect(self._on_delete)
        
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet("background-color: #6c757d; color: white;")
        close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.print_btn)
        btn_layout.addWidget(self.convert_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def _load_data(self):
        self.table.setRowCount(0)
        quotes = self.quote_service.get_recent_quotes()
        
        self.table.setRowCount(len(quotes))
        for row, quote in enumerate(quotes):
            # ID
            item_id = QTableWidgetItem(str(quote['id']))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item_id)
            
            # Customer
            self.table.setItem(row, 1, QTableWidgetItem(quote['customer_name']))
            
            # Date
            self.table.setItem(row, 2, QTableWidgetItem(str(quote['created_at'])))
            
            # Count
            item_count = QTableWidgetItem(str(quote['item_count']))
            item_count.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, item_count)
            
            # Value
            val_str = f"{quote['total_value']:,.2f}"
            item_val = QTableWidgetItem(val_str)
            item_val.setForeground(QColor("#198754")) # Green
            item_val.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.table.setItem(row, 4, item_val)
            
            # Profit
            prof_str = f"{quote['total_profit']:,.2f}"
            self.table.setItem(row, 5, QTableWidgetItem(prof_str))

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _on_load(self):
        quote_id = self._get_selected_id()
        if not quote_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار عرض للتحميل")
            return
            
        if QMessageBox.question(self, "تأكيد", "هل تريد تحميل هذا العرض؟ (سيتم استبدال السلة الحالية)") == QMessageBox.StandardButton.Yes:
            if self.quote_service.load_quote(quote_id):
                self.selected_quote_id = quote_id
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل تحميل العرض")

    def _on_delete(self):
        quote_id = self._get_selected_id()
        if not quote_id:
            return
            
        if QMessageBox.question(self, "حذف", "هل أنت متأكد من حذف هذا العرض نهائياً؟") == QMessageBox.StandardButton.Yes:
            if self.quote_service.delete_quote(quote_id):
                self._load_data() # Refresh
            else:
                QMessageBox.critical(self, "خطأ", "فشل الحذف")

    def _on_print(self):
        """طباعة العرض المحدد"""
        quote_id = self._get_selected_id()
        if not quote_id:
            return

        # Fetch full data from service logic (Need to fetch items)
        # Re-using the get_recent_quotes but we need raw items. 
        # Easier to fetch row manually or use load logic without setting self.items
        
        # Let's verify we can get data.
        # We can query the quote details from the table for basic info
        row = self.table.currentRow()
        customer = self.table.item(row, 1).text()
        date_str = self.table.item(row, 2).text()
        total_val = float(self.table.item(row, 4).text().replace(',',''))
        
        # We need items for the PDF
        # We can use a quick query here or add get_quote method to service.
        # Let's add a helper to service or query db directly via service instance.
        
        try:
            sql = "SELECT items_json FROM wholesale_quotes WHERE id = ?"
            db_row = self.quote_service.db.fetch_one(sql, [quote_id])
            if not db_row: 
                return
            items = json.loads(db_row[0])
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "حفظ ملف PDF", f"quote_{quote_id}.pdf", "PDF Files (*.pdf)"
            )
            
            if filename:
                data = {
                    'customer_name': customer,
                    'created_at': date_str,
                    'total_value': total_val
                }
                if self.printer_service.print_to_pdf(data, items, filename):
                     QMessageBox.information(self, "نجاح", "تمت الطباعة بنجاح")
                else:
                     QMessageBox.critical(self, "خطأ", "فشل الطباعة")
                     
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ أثناء التجهيز للطباعة: {e}")

    def _on_convert(self):
        """تحويل العرض لبيع"""
        quote_id = self._get_selected_id()
        if not quote_id:
            return
            
        msg = (
            "هل أنت متأكد من تحويل هذا العرض إلى فاتورة بيع؟\n"
            "سيتم:\n"
            "1. إنشاء فاتورة جديدة.\n"
            "2. خصم الكميات من المخزون.\n"
            "3. أرشفة العرض."
        )
        if QMessageBox.question(self, "تحويل لبيع", msg) != QMessageBox.StandardButton.Yes:
            return
            
        try:
            invoice_no = self.quote_service.convert_to_sale(quote_id)
            if invoice_no:
                QMessageBox.information(self, "نجاح", f"تم التحويل بنجاح!\nرقم الفاتورة: {invoice_no}")
                # Optional: Delete quote after conversion?
                # For now keep it but maybe mark it? 
                # Let's just refresh.
                self._load_data()
            else:
                QMessageBox.critical(self, "خطأ", "فشل التحويل لسبب غير معروف")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحويل: {e}")

"""
نافذة تسويات المخزون
Stock Adjustments Window
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QComboBox, QDateEdit,
    QLineEdit, QGroupBox, QMessageBox, QHeaderView, QMenu
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QBrush
from datetime import date
from typing import Optional, List

from core.database_manager import DatabaseManager
from services.inventory_count_service import InventoryCountService
from models.physical_count import StockAdjustment, AdjustmentStatus, AdjustmentType


class StockAdjustmentsWindow(QMainWindow):
    """نافذة إدارة تسويات المخزون"""
    
    adjustment_updated = Signal()
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.service = InventoryCountService(db_manager)
        self.current_user_id = 1
        self.current_user_name = "Admin"
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة تسويات المخزون")
        self.setMinimumSize(1200, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # العنوان
        title_label = QLabel("⚖️ إدارة تسويات المخزون")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # بطاقات الملخص
        summary_layout = self.create_summary_cards()
        layout.addLayout(summary_layout)
        
        # الفلاتر
        filters_group = self.create_filters_section()
        layout.addWidget(filters_group)
        
        # الجدول
        self.create_table()
        layout.addWidget(self.table)
        
        # الأزرار
        buttons_layout = self.create_buttons_section()
        layout.addLayout(buttons_layout)
    
    def create_summary_cards(self) -> QHBoxLayout:
        """إنشاء بطاقات الملخص"""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        self.total_card = self.create_summary_card("📊 إجمالي التسويات", "0", "#3498db")
        self.pending_card = self.create_summary_card("⏳ معلقة", "0", "#f39c12")
        self.approved_card = self.create_summary_card("✅ معتمدة", "0", "#27ae60")
        self.applied_card = self.create_summary_card("✔️ مطبقة", "0", "#16a085")
        
        layout.addWidget(self.total_card)
        layout.addWidget(self.pending_card)
        layout.addWidget(self.approved_card)
        layout.addWidget(self.applied_card)
        
        return layout
    
    def create_summary_card(self, title: str, value: str, color: str) -> QGroupBox:
        """إنشاء بطاقة ملخص"""
        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setObjectName("card_value")
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return card
    
    def create_filters_section(self) -> QGroupBox:
        """إنشاء قسم الفلاتر"""
        group = QGroupBox("🔍 فلاتر البحث")
        layout = QHBoxLayout(group)
        
        # البحث
        layout.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("رقم التسوية أو المنتج...")
        self.search_input.textChanged.connect(self.load_data)
        layout.addWidget(self.search_input)
        
        # الحالة
        layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("الكل", None)
        self.status_filter.addItem("⏳ معلقة", AdjustmentStatus.PENDING.value)
        self.status_filter.addItem("✅ معتمدة", AdjustmentStatus.APPROVED.value)
        self.status_filter.addItem("❌ مرفوضة", AdjustmentStatus.REJECTED.value)
        self.status_filter.addItem("✔️ مطبقة", AdjustmentStatus.APPLIED.value)
        self.status_filter.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.status_filter)
        
        # النوع
        layout.addWidget(QLabel("النوع:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("الكل", None)
        self.type_filter.addItem("📋 تسوية جرد", AdjustmentType.COUNT_ADJUSTMENT.value)
        self.type_filter.addItem("💔 تالف", AdjustmentType.DAMAGE.value)
        self.type_filter.addItem("📅 منتهي", AdjustmentType.EXPIRY.value)
        self.type_filter.addItem("🔍 وجدت", AdjustmentType.FOUND.value)
        self.type_filter.addItem("📝 تصحيح", AdjustmentType.CORRECTION.value)
        self.type_filter.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.type_filter)
        
        # من تاريخ
        layout.addWidget(QLabel("من:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.dateChanged.connect(self.load_data)
        layout.addWidget(self.from_date)
        
        # إلى تاريخ
        layout.addWidget(QLabel("إلى:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.dateChanged.connect(self.load_data)
        layout.addWidget(self.to_date)
        
        layout.addStretch()
        
        return group
    
    def create_table(self):
        """إنشاء الجدول"""
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "الرقم", "رقم التسوية", "التاريخ", "النوع", "المنتج",
            "الكمية قبل", "التسوية", "الكمية بعد", "القيمة",
            "الحالة", "المستخدم"
        ])
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        
        # قائمة السياق
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
    
    def create_buttons_section(self) -> QHBoxLayout:
        """إنشاء قسم الأزرار"""
        layout = QHBoxLayout()
        
        # زر اعتماد
        approve_btn = QPushButton("✅ اعتماد")
        approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        approve_btn.clicked.connect(self.approve_adjustment)
        layout.addWidget(approve_btn)
        
        # زر رفض
        reject_btn = QPushButton("❌ رفض")
        reject_btn.clicked.connect(self.reject_adjustment)
        layout.addWidget(reject_btn)
        
        # زر تطبيق
        apply_btn = QPushButton("✔️ تطبيق")
        apply_btn.clicked.connect(self.apply_adjustment)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        
        # زر تحديث
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        
        return layout
    
    def load_data(self):
        """تحميل البيانات"""
        try:
            status_value = self.status_filter.currentData()
            status = AdjustmentStatus(status_value) if status_value else None
            
            type_value = self.type_filter.currentData()
            adj_type = AdjustmentType(type_value) if type_value else None
            
            from_date_val = self.from_date.date().toPython()
            to_date_val = self.to_date.date().toPython()
            
            adjustments = self.service.get_all_adjustments(
                status=status,
                adjustment_type=adj_type,
                from_date=from_date_val,
                to_date=to_date_val
            )
            
            # فلتر البحث
            search_text = self.search_input.text().lower()
            if search_text:
                adjustments = [
                    a for a in adjustments
                    if search_text in a.adjustment_number.lower() or
                    search_text in a.product_name.lower()
                ]
            
            self.populate_table(adjustments)
            self.update_summary(adjustments)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل البيانات:\n{str(e)}")
    
    def populate_table(self, adjustments: List[StockAdjustment]):
        """ملء الجدول"""
        self.table.setRowCount(0)
        
        for adj in adjustments:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(adj.id)))
            self.table.setItem(row, 1, QTableWidgetItem(adj.adjustment_number))
            
            date_str = adj.adjustment_date.strftime("%Y-%m-%d") if isinstance(adj.adjustment_date, date) else str(adj.adjustment_date)
            self.table.setItem(row, 2, QTableWidgetItem(date_str))
            
            self.table.setItem(row, 3, QTableWidgetItem(adj.type_label))
            self.table.setItem(row, 4, QTableWidgetItem(f"{adj.product_code} - {adj.product_name}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{adj.quantity_before:,.2f}"))
            
            # التسوية مع لون
            adj_item = QTableWidgetItem(f"{adj.adjustment_quantity:+,.2f}")
            color = QColor("#27ae60") if adj.is_increase else QColor("#e74c3c")
            adj_item.setForeground(QBrush(color))
            self.table.setItem(row, 6, adj_item)
            
            self.table.setItem(row, 7, QTableWidgetItem(f"{adj.quantity_after:,.2f}"))
            
            value_item = QTableWidgetItem(f"{adj.adjustment_value:,.2f}")
            self.table.setItem(row, 8, value_item)
            
            # الحالة
            status_item = QTableWidgetItem(adj.status_label)
            status_item.setForeground(QBrush(self.get_status_color(adj.status)))
            self.table.setItem(row, 9, status_item)
            
            self.table.setItem(row, 10, QTableWidgetItem(adj.created_by_name or "-"))
    
    def update_summary(self, adjustments: List[StockAdjustment]):
        """تحديث بطاقات الملخص"""
        total = len(adjustments)
        pending = sum(1 for a in adjustments if a.status == AdjustmentStatus.PENDING)
        approved = sum(1 for a in adjustments if a.status == AdjustmentStatus.APPROVED)
        applied = sum(1 for a in adjustments if a.status == AdjustmentStatus.APPLIED)
        
        self.total_card.findChild(QLabel, "card_value").setText(str(total))
        self.pending_card.findChild(QLabel, "card_value").setText(str(pending))
        self.approved_card.findChild(QLabel, "card_value").setText(str(approved))
        self.applied_card.findChild(QLabel, "card_value").setText(str(applied))
    
    def get_status_color(self, status: AdjustmentStatus) -> QColor:
        """الحصول على لون الحالة"""
        colors = {
            AdjustmentStatus.PENDING: QColor("#f39c12"),
            AdjustmentStatus.APPROVED: QColor("#27ae60"),
            AdjustmentStatus.REJECTED: QColor("#e74c3c"),
            AdjustmentStatus.APPLIED: QColor("#16a085")
        }
        return colors.get(status, QColor("#000000"))
    
    def show_context_menu(self, position):
        """عرض قائمة السياق"""
        if self.table.rowCount() == 0:
            return
        
        menu = QMenu(self)
        
        approve_action = menu.addAction("✅ اعتماد")
        approve_action.triggered.connect(self.approve_adjustment)
        
        reject_action = menu.addAction("❌ رفض")
        reject_action.triggered.connect(self.reject_adjustment)
        
        apply_action = menu.addAction("✔️ تطبيق")
        apply_action.triggered.connect(self.apply_adjustment)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def get_selected_adjustment_id(self) -> Optional[int]:
        """الحصول على معرف التسوية المحددة"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار تسوية أولاً")
            return None
        
        row = selected[0].row()
        return int(self.table.item(row, 0).text())
    
    def approve_adjustment(self):
        """اعتماد التسوية"""
        adj_id = self.get_selected_adjustment_id()
        if not adj_id:
            return
        
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد اعتماد هذه التسوية؟\nسيتم تطبيقها تلقائياً على المخزون.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.service.approve_adjustment(
                    adj_id,
                    self.current_user_id,
                    self.current_user_name,
                    apply_immediately=True
                ):
                    self.load_data()
                    self.adjustment_updated.emit()
                    QMessageBox.information(self, "نجاح", "تم اعتماد وتطبيق التسوية بنجاح")
                else:
                    QMessageBox.warning(self, "تنبيه", "لا يمكن اعتماد التسوية")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل اعتماد التسوية:\n{str(e)}")
    
    def reject_adjustment(self):
        """رفض التسوية"""
        adj_id = self.get_selected_adjustment_id()
        if not adj_id:
            return
        
        from PySide6.QtWidgets import QInputDialog
        reason, ok = QInputDialog.getText(self, "سبب الرفض", "أدخل سبب رفض التسوية:")
        
        if ok and reason:
            try:
                if self.service.reject_adjustment(
                    adj_id,
                    self.current_user_id,
                    self.current_user_name,
                    reason
                ):
                    self.load_data()
                    self.adjustment_updated.emit()
                    QMessageBox.information(self, "نجاح", "تم رفض التسوية")
                else:
                    QMessageBox.warning(self, "تنبيه", "لا يمكن رفض التسوية")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل رفض التسوية:\n{str(e)}")
    
    def apply_adjustment(self):
        """تطبيق التسوية"""
        adj_id = self.get_selected_adjustment_id()
        if not adj_id:
            return
        
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد تطبيق هذه التسوية على المخزون؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.service.apply_adjustment(adj_id):
                    self.load_data()
                    self.adjustment_updated.emit()
                    QMessageBox.information(self, "نجاح", "تم تطبيق التسوية بنجاح")
                else:
                    QMessageBox.warning(self, "تنبيه", "لا يمكن تطبيق التسوية")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل تطبيق التسوية:\n{str(e)}")

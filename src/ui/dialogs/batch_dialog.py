"""
Batch Dialog - حوار إضافة/تعديل الدفعة
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QGroupBox, QMessageBox, QDateEdit, QTextEdit,
    QFrame, QGraphicsDropShadowEffect, QWidget
)
from PySide6.QtGui import QColor

from src.ui.widgets.custom_title_bar import CustomTitleBar
from src.ui.widgets.quantum_notification import NotificationManager
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from typing import Optional
from decimal import Decimal
from datetime import datetime, date

from ...core.database_manager import DatabaseManager
from ...services.inventory_optimization_service import InventoryOptimizationService
from ...services.product_service_enhanced import ProductService
from ...models.supplier import SupplierManager
from ...models.inventory_optimization import ProductBatch, BatchStatus


class BatchDialog(QDialog):
    """حوار إضافة/تعديل الدفعة"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None, batch: Optional[ProductBatch] = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.service = InventoryOptimizationService(db_manager)
        self.product_service = ProductService(db_manager)
        self.supplier_manager = SupplierManager(db_manager)
        self.batch = batch
        
        # self.setWindowTitle("إضافة دفعة جديدة" if not batch else "تعديل الدفعة")
        # self.setMinimumWidth(600)
        
        # --- Quantum Window Setup ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Notifications
        self.notify = NotificationManager(self)
        
        self.resize(650, 700) # Slightly larger
        
        self.title_text = "إضافة دفعة جديدة" if not batch else "تعديل الدفعة"
        
        self.setup_ui()
        if batch:
            self.load_batch_data()
    
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
        
        # العنوان
        title = QLabel("معلومات الدفعة")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # معلومات أساسية
        basic_group = self.create_basic_section()
        layout.addWidget(basic_group)
        
        # معلومات الموقع
        location_group = self.create_location_section()
        layout.addWidget(location_group)
        
        # معلومات إضافية
        additional_group = self.create_additional_section()
        layout.addWidget(additional_group)
        
        # الأزرار
        buttons = self.create_buttons()
        layout.addLayout(buttons)
    
    def create_basic_section(self) -> QGroupBox:
        """القسم الأساسي"""
        group = QGroupBox("المعلومات الأساسية")
        layout = QFormLayout()
        
        # رقم الدفعة
        self.batch_number_edit = QLineEdit()
        self.batch_number_edit.setPlaceholderText("مثال: BATCH-2024-001")
        layout.addRow("رقم الدفعة:", self.batch_number_edit)
        
        # المنتج
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        products = self.product_service.search_products("")
        for product in products:
            display_code = getattr(product, 'sku', None) or getattr(product, 'barcode', None) or "#"
            self.product_combo.addItem(
                f"{display_code} - {product.name}",
                product.id
            )
        layout.addRow("المنتج:", self.product_combo)
        
        # الكمية الأصلية
        self.initial_qty_spin = QDoubleSpinBox()
        self.initial_qty_spin.setRange(0, 999999)
        self.initial_qty_spin.setDecimals(2)
        self.initial_qty_spin.valueChanged.connect(self.on_initial_qty_changed)
        layout.addRow("الكمية الأصلية:", self.initial_qty_spin)
        
        # الكمية المتبقية
        self.remaining_qty_spin = QDoubleSpinBox()
        self.remaining_qty_spin.setRange(0, 999999)
        self.remaining_qty_spin.setDecimals(2)
        layout.addRow("الكمية المتبقية:", self.remaining_qty_spin)
        
        # الكمية المحجوزة
        self.reserved_qty_spin = QDoubleSpinBox()
        self.reserved_qty_spin.setRange(0, 999999)
        self.reserved_qty_spin.setDecimals(2)
        self.reserved_qty_spin.setEnabled(False)
        layout.addRow("الكمية المحجوزة:", self.reserved_qty_spin)
        
        # تاريخ التصنيع
        self.mfg_date_edit = QDateEdit()
        self.mfg_date_edit.setCalendarPopup(True)
        self.mfg_date_edit.setDate(QDate.currentDate())
        layout.addRow("تاريخ التصنيع:", self.mfg_date_edit)
        
        # تاريخ الانتهاء
        self.exp_date_edit = QDateEdit()
        self.exp_date_edit.setCalendarPopup(True)
        self.exp_date_edit.setDate(QDate.currentDate().addYears(1))
        layout.addRow("تاريخ الانتهاء:", self.exp_date_edit)
        
        # المورد
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("-- بدون مورد --", None)
        suppliers = self.supplier_manager.get_all_suppliers()
        for supplier in suppliers:
            self.supplier_combo.addItem(supplier.name, supplier.id)
        layout.addRow("المورد:", self.supplier_combo)
        
        # سعر التكلفة
        self.unit_cost_spin = QDoubleSpinBox()
        self.unit_cost_spin.setRange(0, 999999)
        self.unit_cost_spin.setDecimals(2)
        layout.addRow("سعر التكلفة للوحدة:", self.unit_cost_spin)
        
        # الحالة
        self.status_combo = QComboBox()
        self.status_combo.addItem("✅ نشط", BatchStatus.ACTIVE.value)
        self.status_combo.addItem("⚠️ ينتهي قريباً", BatchStatus.EXPIRING_SOON.value)
        self.status_combo.addItem("❌ منتهي", BatchStatus.EXPIRED.value)
        self.status_combo.addItem("🔧 تالف", BatchStatus.DAMAGED.value)
        self.status_combo.addItem("🚫 مسحوب", BatchStatus.RECALLED.value)
        layout.addRow("الحالة:", self.status_combo)
        
        group.setLayout(layout)
        return group
    
    def create_location_section(self) -> QGroupBox:
        """قسم الموقع"""
        group = QGroupBox("موقع التخزين")
        layout = QFormLayout()
        
        # المستودع
        self.warehouse_edit = QLineEdit()
        self.warehouse_edit.setPlaceholderText("مثال: المستودع الرئيسي")
        layout.addRow("المستودع:", self.warehouse_edit)
        
        # الرف
        self.rack_edit = QLineEdit()
        self.rack_edit.setPlaceholderText("مثال: A-1")
        layout.addRow("الرف:", self.rack_edit)
        
        # الصندوق
        self.bin_edit = QLineEdit()
        self.bin_edit.setPlaceholderText("مثال: 001")
        layout.addRow("الصندوق:", self.bin_edit)
        
        group.setLayout(layout)
        return group
    
    def create_additional_section(self) -> QGroupBox:
        """قسم المعلومات الإضافية"""
        group = QGroupBox("معلومات إضافية")
        layout = QVBoxLayout()
        
        # الأرقام التسلسلية
        serial_label = QLabel("الأرقام التسلسلية (سطر لكل رقم):")
        layout.addWidget(serial_label)
        
        self.serial_numbers_text = QTextEdit()
        self.serial_numbers_text.setMaximumHeight(100)
        self.serial_numbers_text.setPlaceholderText("SN001\nSN002\nSN003")
        layout.addWidget(self.serial_numbers_text)
        
        # ملاحظات
        notes_label = QLabel("ملاحظات:")
        layout.addWidget(notes_label)
        
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(80)
        layout.addWidget(self.notes_text)
        
        group.setLayout(layout)
        return group
    
    def create_buttons(self) -> QHBoxLayout:
        """أزرار الحوار"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.clicked.connect(self.save_batch)
        layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        return layout
    
    def on_initial_qty_changed(self, value: float):
        """عند تغيير الكمية الأصلية"""
        if not self.batch:
            # عند الإنشاء، الكمية المتبقية = الكمية الأصلية
            self.remaining_qty_spin.setValue(value)
    
    def load_batch_data(self):
        """تحميل بيانات الدفعة"""
        if not self.batch:
            return
        
        # معلومات أساسية
        self.batch_number_edit.setText(self.batch.batch_number)
        
        # تحديد المنتج
        index = self.product_combo.findData(self.batch.product_id)
        if index >= 0:
            self.product_combo.setCurrentIndex(index)
        
        # الكميات
        self.initial_qty_spin.setValue(float(self.batch.initial_quantity))
        self.remaining_qty_spin.setValue(float(self.batch.remaining_quantity))
        self.reserved_qty_spin.setValue(float(self.batch.reserved_quantity))
        
        # التواريخ
        if self.batch.manufacturing_date:
            if isinstance(self.batch.manufacturing_date, str):
                mfg_date = datetime.strptime(self.batch.manufacturing_date, "%Y-%m-%d").date()
            else:
                mfg_date = self.batch.manufacturing_date
            self.mfg_date_edit.setDate(QDate(mfg_date.year, mfg_date.month, mfg_date.day))
        
        if self.batch.expiry_date:
            if isinstance(self.batch.expiry_date, str):
                exp_date = datetime.strptime(self.batch.expiry_date, "%Y-%m-%d").date()
            else:
                exp_date = self.batch.expiry_date
            self.exp_date_edit.setDate(QDate(exp_date.year, exp_date.month, exp_date.day))
        
        # المورد
        if self.batch.supplier_id:
            index = self.supplier_combo.findData(self.batch.supplier_id)
            if index >= 0:
                self.supplier_combo.setCurrentIndex(index)
        
        # السعر
        if self.batch.unit_cost:
            self.unit_cost_spin.setValue(float(self.batch.unit_cost))
        
        # الحالة
        index = self.status_combo.findData(self.batch.status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        
        # الموقع
        if self.batch.warehouse_location:
            self.warehouse_edit.setText(self.batch.warehouse_location)
        if self.batch.rack_number:
            self.rack_edit.setText(self.batch.rack_number)
        if self.batch.bin_number:
            self.bin_edit.setText(self.batch.bin_number)
        
        # الأرقام التسلسلية
        if self.batch.serial_numbers:
            self.serial_numbers_text.setPlainText(self.batch.serial_numbers)
        
        # الملاحظات
        if self.batch.notes:
            self.notes_text.setPlainText(self.batch.notes)
    
    def save_batch(self):
        """حفظ الدفعة"""
        # التحقق من البيانات
        if not self.batch_number_edit.text().strip():
            self.notify.show_warning("تحذير", "الرجاء إدخال رقم الدفعة")
            return
        
        product_id = self.product_combo.currentData()
        if not product_id:
            self.notify.show_warning("تحذير", "الرجاء اختيار منتج")
            return
        
        if self.initial_qty_spin.value() <= 0:
            self.notify.show_warning("تحذير", "الرجاء إدخال كمية أصلية صحيحة")
            return
        
        try:
            # إعداد البيانات
            batch_data = {
                'batch_number': self.batch_number_edit.text().strip(),
                'product_id': product_id,
                'initial_quantity': Decimal(str(self.initial_qty_spin.value())),
                'remaining_quantity': Decimal(str(self.remaining_qty_spin.value())),
                'reserved_quantity': Decimal(str(self.reserved_qty_spin.value())),
                'manufacturing_date': self.mfg_date_edit.date().toPython(),
                'expiry_date': self.exp_date_edit.date().toPython(),
                'supplier_id': self.supplier_combo.currentData(),
                'warehouse_location': self.warehouse_edit.text().strip() or None,
                'rack_number': self.rack_edit.text().strip() or None,
                'bin_number': self.bin_edit.text().strip() or None,
                'unit_cost': Decimal(str(self.unit_cost_spin.value())) if self.unit_cost_spin.value() > 0 else None,
                'status': self.status_combo.currentData(),
                'serial_numbers': self.serial_numbers_text.toPlainText().strip() or None,
                'notes': self.notes_text.toPlainText().strip() or None
            }
            
            if self.batch:
                # تحديث (لاحقاً سنضيف update_batch للخدمة)
                batch_data['id'] = self.batch.id
                
                # تحديث مباشر في قاعدة البيانات
                query = """
                    UPDATE product_batches
                    SET batch_number = ?, product_id = ?, initial_quantity = ?,
                        remaining_quantity = ?, reserved_quantity = ?,
                        manufacturing_date = ?, expiry_date = ?,
                        supplier_id = ?, warehouse_location = ?,
                        rack_number = ?, bin_number = ?, unit_cost = ?,
                        status = ?, serial_numbers = ?, notes = ?
                    WHERE id = ?
                """
                
                self.db_manager.execute_query(
                    query,
                    (
                        batch_data['batch_number'],
                        batch_data['product_id'],
                        float(batch_data['initial_quantity']),
                        float(batch_data['remaining_quantity']),
                        float(batch_data['reserved_quantity']),
                        batch_data['manufacturing_date'].strftime("%Y-%m-%d"),
                        batch_data['expiry_date'].strftime("%Y-%m-%d"),
                        batch_data['supplier_id'],
                        batch_data['warehouse_location'],
                        batch_data['rack_number'],
                        batch_data['bin_number'],
                        float(batch_data['unit_cost']) if batch_data['unit_cost'] else None,
                        batch_data['status'],
                        batch_data['serial_numbers'],
                        batch_data['notes'],
                        batch_data['id']
                    )
                )
                
                self.notify.show_success("نجح", "تم تحديث الدفعة بنجاح")
            else:
                # إنشاء جديد
                self.service.create_batch(**batch_data)
                self.notify.show_success("نجح", "تم إنشاء الدفعة بنجاح")
            
            self.accept()
            
        except Exception as e:
            self.notify.show_error("خطأ", f"فشل حفظ الدفعة:\n{str(e)}")

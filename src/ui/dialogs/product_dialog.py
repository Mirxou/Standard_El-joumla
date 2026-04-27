#!/usr/bin/env python3
"""
نافذة إضافة/تعديل المنتجات - Product Dialog
واجهة شاملة لإدارة المنتجات مع دعم اللغة العربية
"""

import sys
import os
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QCheckBox, QFrame, QMessageBox, QProgressBar,
    QTabWidget, QWidget, QGroupBox, QDateEdit, QFileDialog,
    QScrollArea, QSizePolicy, QApplication, QCompleter, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
    QInputDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QDate, QStringListModel
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QValidator, QDoubleValidator, QShowEvent, QCloseEvent
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from ...ui.widgets.custom_title_bar import CustomTitleBar
from ...ui.widgets.quantum_notification import NotificationManager

from ...core.database_manager import DatabaseManager
from ...models.product import Product, ProductManager
from ...models.category import CategoryManager
from ...models.supplier import SupplierManager
from ...utils.logger import setup_logger
from ...ui.animations.animation_manager import AnimationManager

# Try to use enhanced product service/model if available
try:
    from ...services.product_service_enhanced import ProductService as EnhancedProductService
    from ...models.product_enhanced import Product as EnhancedProduct
except Exception:
    EnhancedProductService = None
    EnhancedProduct = None

# Try to use image manager service
try:
    from ...services.image_manager_service import ImageManagerService
except Exception:
    ImageManagerService = None


class ProductValidationWorker(QThread):
    """عامل التحقق من صحة بيانات المنتج"""
    validation_completed = Signal(bool, str, dict)  # success, message, data
    
    def __init__(self, product_manager: ProductManager, product_data: Dict[str, Any], product_id: Optional[int] = None):
        super().__init__()
        self.product_manager = product_manager
        self.product_data = product_data
        self.product_id = product_id
    
    def run(self):
        """تشغيل التحقق من صحة البيانات"""
        try:
            # التحقق من الحقول المطلوبة
            if not self.product_data.get('name', '').strip():
                self.validation_completed.emit(False, "اسم المنتج مطلوب", {})
                return
            
            if not self.product_data.get('selling_price') or self.product_data['selling_price'] <= 0:
                self.validation_completed.emit(False, "سعر البيع يجب أن يكون أكبر من صفر", {})
                return
            
            # التحقق من الباركود إذا تم إدخاله
            barcode = self.product_data.get('barcode')
            if barcode:
                existing_product = self.product_manager.get_product_by_barcode(barcode)
                if existing_product and (not self.product_id or existing_product.id != self.product_id):
                    self.validation_completed.emit(False, f"الباركود موجود مسبقاً للمنتج: {existing_product.name}", {})
                    return
            
            # التحقق من اسم المنتج
            name = self.product_data['name'].strip()
            existing_products = self.product_manager.search_products(name)
            for product in existing_products:
                if product.name.lower() == name.lower() and (not self.product_id or product.id != self.product_id):
                    self.validation_completed.emit(False, f"اسم المنتج موجود مسبقاً", {})
                    return
            
            # التحقق من منطقية الأسعار
            cost_price = self.product_data.get('cost_price', 0)
            selling_price = self.product_data.get('selling_price', 0)
            
            if cost_price > selling_price:
                # تحذير وليس خطأ
                pass
            
            # التحقق من مستويات المخزون
            if self.product_data.get('track_stock', True):
                min_stock = self.product_data.get('min_stock_level', 0)
                max_stock = self.product_data.get('max_stock_level', 0)
                current_stock = self.product_data.get('stock_quantity', 0)
                
                if max_stock > 0 and min_stock > max_stock:
                    self.validation_completed.emit(False, "الحد الأدنى للمخزون لا يمكن أن يكون أكبر من الحد الأقصى", {})
                    return
                
                if current_stock < 0:
                    self.validation_completed.emit(False, "كمية المخزون لا يمكن أن تكون سالبة", {})
                    return
            
            # إذا وصلنا هنا، فالبيانات صحيحة
            self.validation_completed.emit(True, "البيانات صحيحة", self.product_data)
            
        except Exception as e:
            self.validation_completed.emit(False, f"خطأ في التحقق من البيانات: {str(e)}", {})


class ProductDialog(QDialog):
    """نافذة إضافة/تعديل المنتج المحسنة"""
    
    product_saved = Signal(object)  # Product
    
    def __init__(self, db_manager: DatabaseManager, product: Optional[Product] = None, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.product = product
        self.is_edit_mode = product is not None
        self.validation_worker = None
        self.current_image_path = None
        self.original_image_path = None  # مسار الصورة الأصلية قبل التعديل
        
        # إعداد المدراء
        self.product_manager = ProductManager(db_manager)
        # if enhanced product service available, prefer it
        if EnhancedProductService:
            try:
                self.product_service = EnhancedProductService(db_manager, logger=setup_logger('product_service'))
            except Exception:
                self.product_service = None
        else:
            self.product_service = None
        
        # إعداد خدمة إدارة الصور
        if ImageManagerService:
            try:
                self.image_manager = ImageManagerService(logger=setup_logger('image_manager'))
            except Exception:
                self.image_manager = None
        else:
            self.image_manager = None
        self.category_manager = CategoryManager(db_manager)
        self.supplier_manager = SupplierManager(db_manager)
        
        # إعداد السجل
        self.logger = setup_logger(__name__)
        
        # تهيئة نظام الترجمة
        from pathlib import Path
        from ...utils.i18n_api import I18n
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))
        
        # تهيئة Animation Manager
        self.animation_manager = AnimationManager(self)
        
        # إعداد الواجهة
        self.setup_ui()
        self.setup_connections()
        self.setup_styles()
        
        # تحميل البيانات
        self.load_data()
        
        if self.is_edit_mode:
            self.populate_form()
        
        # إعداد Opacity للـ fade in
        self.setWindowOpacity(0.0)
        
        # --- Quantum Window Setup ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Notifications
        self.notify = NotificationManager(self)
    
    def setup_ui(self):
        """إعداد واجهة المستخدم المحسنة"""
        title = self.i18n.get_message("product_edit_title") if self.is_edit_mode else self.i18n.get_message("product_new_title")
        # self.setWindowTitle(title) # Handled by CustomTitleBar
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        self.setModal(True)
        
        # تخطيط جذري شفاف
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)
        
        # الإطار الرئيسي
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa; /* Light Background for Content */
                border: 1px solid #3498db;
                border-radius: 10px;
            }
        """)
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor("#3498db"))
        shadow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(shadow)
        
        root_layout.addWidget(self.main_frame)
        
        # تخطيط النافذة الداخلية
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Custom Title Bar
        self.title_bar = CustomTitleBar(self, title=title, is_dialog=True)
        main_layout.addWidget(self.title_bar)
        
        # Remove old header call if it duplicates title functionality, 
        # BUT setup_header adds specific product info, so we keep it but maybe simplify?
        # Let's keep existing setup_header for the "banner" look inside the dialog.
        self.setup_header(main_layout)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        main_layout.addWidget(self.progress_bar)
        
        # إنشاء مقسم أفقي للتخطيط المتقدم
        from PySide6.QtWidgets import QSplitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # الجانب الأيسر - النماذج
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # منطقة المحتوى مع التبويبات
        self.setup_tabs(left_layout)
        
        self.main_splitter.addWidget(left_widget)
        
        # الجانب الأيمن - معاينة وأدوات
        self.right_widget = QWidget()
        self.right_widget.setMaximumWidth(300)
        right_layout = QVBoxLayout(self.right_widget)
        
        # معاينة الصورة
        self.setup_image_preview(right_layout)
        
        # أدوات سريعة
        self.setup_quick_tools(right_layout)
        
        # معلومات المنتج السريعة
        self.setup_quick_info(right_layout)
        
        self.main_splitter.addWidget(self.right_widget)
        
        # تعيين نسب المقسم
        self.main_splitter.setSizes([700, 300])
        
        # منطقة الأزرار
        self.setup_buttons(main_layout)
    
    def setup_header(self, layout: QVBoxLayout):
        """إعداد منطقة الرأس"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #3498db;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # أيقونة المنتج
        icon_label = QLabel("📦")
        icon_label.setStyleSheet("font-size: 32px; color: white;")
        header_layout.addWidget(icon_label)
        
        # معلومات المنتج
        info_layout = QVBoxLayout()
        
        title = "تعديل المنتج" if self.is_edit_mode else "إضافة منتج جديد"
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
        """)
        info_layout.addWidget(title_label)
        
        if self.is_edit_mode and self.product:
            subtitle_label = QLabel(self.i18n.get_message("product_name_label", name=self.product.name))
            subtitle_label.setStyleSheet("font-size: 12px; color: #ecf0f1;")
            info_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        layout.addWidget(header_frame)
    
    def setup_tabs(self, layout: QVBoxLayout):
        """إعداد التبويبات"""
        self.tab_widget = QTabWidget()
        
        # تبويب المعلومات الأساسية
        self.basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(self.basic_tab, self.i18n.get_message("tab_basic_info"))
        
        # تبويب الأسعار والمخزون
        self.pricing_tab = self.create_pricing_tab()
        self.tab_widget.addTab(self.pricing_tab, self.i18n.get_message("tab_pricing_stock"))
        
        # تبويب التفاصيل الإضافية
        self.details_tab = self.create_details_tab()
        self.tab_widget.addTab(self.details_tab, self.i18n.get_message("tab_additional_details"))
        
        # تبويب سجل المخزون (للتعديل فقط)
        if self.is_edit_mode:
            self.history_tab = self.create_history_tab()
            self.tab_widget.addTab(self.history_tab, self.i18n.get_message("tab_stock_history"))
        
        layout.addWidget(self.tab_widget)
    
    def setup_image_preview(self, layout: QVBoxLayout):
        """إعداد معاينة الصورة"""
        self.image_preview_widget = QGroupBox(self.i18n.get_message("product_image"))
        image_layout = QVBoxLayout(self.image_preview_widget)
        
        # معاينة الصورة
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
                color: #7f8c8d;
            }
        """)
        self.image_label.setText(self.i18n.get_message("no_image"))
        self.image_label.mousePressEvent = self.select_image
        image_layout.addWidget(self.image_label)
        
        # أزرار الصورة
        image_buttons_layout = QHBoxLayout()
        
        self.select_image_btn = QPushButton(self.i18n.get_message("select_image"))
        self.select_image_btn.clicked.connect(self.select_image)
        image_buttons_layout.addWidget(self.select_image_btn)
        
        self.remove_image_btn = QPushButton(self.i18n.get_message("remove_image"))
        self.remove_image_btn.clicked.connect(self.remove_image)
        self.remove_image_btn.setEnabled(False)
        image_buttons_layout.addWidget(self.remove_image_btn)
        
        image_layout.addLayout(image_buttons_layout)
        layout.addWidget(self.image_preview_widget)
    
    def setup_quick_tools(self, layout: QVBoxLayout):
        """إعداد الأدوات السريعة"""
        self.quick_tools_widget = QGroupBox(self.i18n.get_message("quick_tools"))
        tools_layout = QVBoxLayout(self.quick_tools_widget)
        
        # بحث سريع في المنتجات المشابهة
        self.quick_search_btn = QPushButton(self.i18n.get_message("search_similar_products"))
        self.quick_search_btn.clicked.connect(self.search_similar_products)
        tools_layout.addWidget(self.quick_search_btn)
        
        # نسخ من منتج موجود
        self.copy_from_btn = QPushButton(self.i18n.get_message("copy_from_existing"))
        self.copy_from_btn.clicked.connect(self.copy_from_existing)
        tools_layout.addWidget(self.copy_from_btn)
        
        # حاسبة هامش الربح
        self.profit_calc_btn = QPushButton(self.i18n.get_message("profit_margin_calculator"))
        self.profit_calc_btn.clicked.connect(self.show_profit_calculator)
        tools_layout.addWidget(self.profit_calc_btn)
        
        layout.addWidget(self.quick_tools_widget)
    
    def setup_quick_info(self, layout: QVBoxLayout):
        """إعداد معلومات سريعة"""
        self.quick_info_widget = QGroupBox(self.i18n.get_message("quick_info"))
        info_layout = QVBoxLayout(self.quick_info_widget)
        
        # معلومات الربح
        self.profit_info_label = QLabel(self.i18n.get_message("profit_margin_label", percent="0.00"))
        self.profit_info_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        info_layout.addWidget(self.profit_info_label)
        
        # معلومات المخزون
        self.stock_info_label = QLabel(self.i18n.get_message("stock_status_good"))
        self.stock_info_label.setStyleSheet("color: #27ae60;")
        info_layout.addWidget(self.stock_info_label)
        
        # آخر تحديث
        if self.is_edit_mode and self.product:
            last_update = getattr(self.product, 'updated_at', 'غير محدد')
            self.last_update_label = QLabel(self.i18n.get_message("last_update", date=str(last_update)))
            self.last_update_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
            info_layout.addWidget(self.last_update_label)
        
        layout.addWidget(self.quick_info_widget)
        layout.addStretch()
    
    def create_basic_tab(self) -> QWidget:
        """إنشاء تبويب المعلومات الأساسية"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # مجموعة المعلومات الأساسية
        basic_group = QGroupBox("المعلومات الأساسية")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(10)
        
        # اسم المنتج
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.i18n.get_message("enter_product_name"))
        self.name_edit.setMaxLength(200)
        basic_layout.addRow("اسم المنتج *:", self.name_edit)
        
        # الباركود
        barcode_layout = QHBoxLayout()
        self.barcode_edit = QLineEdit()
        self.barcode_edit.setPlaceholderText(self.i18n.get_message("enter_barcode"))
        self.generate_barcode_btn = QPushButton(self.i18n.get_message("generate"))
        self.generate_barcode_btn.setMaximumWidth(80)
        barcode_layout.addWidget(self.barcode_edit)
        barcode_layout.addWidget(self.generate_barcode_btn)
        basic_layout.addRow("الباركود:", barcode_layout)
        
        # الفئة
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        basic_layout.addRow("الفئة:", self.category_combo)
        
        # المورد
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        basic_layout.addRow("المورد:", self.supplier_combo)
        
        # الوحدة
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText(self.i18n.get_message("enter_unit"))
        basic_layout.addRow("الوحدة:", self.unit_edit)
        
        layout.addWidget(basic_group)
        
        # مجموعة الوصف
        desc_group = QGroupBox("الوصف والملاحظات")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(self.i18n.get_message("enter_description"))
        self.description_edit.setMaximumHeight(100)
        desc_layout.addWidget(self.description_edit)
        
        layout.addWidget(desc_group)
        
        layout.addStretch()
        return tab
    
    def create_pricing_tab(self) -> QWidget:
        """إنشاء تبويب الأسعار والمخزون"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # مجموعة الأسعار
        pricing_group = QGroupBox("الأسعار")
        pricing_layout = QFormLayout(pricing_group)
        pricing_layout.setSpacing(10)
        
        # سعر التكلفة
        self.cost_price_spin = QDoubleSpinBox()
        self.cost_price_spin.setRange(0, 999999.99)
        self.cost_price_spin.setDecimals(2)
        self.cost_price_spin.setSuffix(" دج")
        pricing_layout.addRow("سعر التكلفة:", self.cost_price_spin)
        
        # سعر البيع
        self.selling_price_spin = QDoubleSpinBox()
        self.selling_price_spin.setRange(0.01, 999999.99)
        self.selling_price_spin.setDecimals(2)
        self.selling_price_spin.setSuffix(" دج")
        pricing_layout.addRow("سعر البيع *:", self.selling_price_spin)
        
        # هامش الربح (للعرض فقط)
        self.profit_margin_label = QLabel("0.00%")
        self.profit_margin_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        pricing_layout.addRow("هامش الربح:", self.profit_margin_label)
        
        layout.addWidget(pricing_group)
        
        # مجموعة المخزون
        stock_group = QGroupBox("المخزون")
        stock_layout = QFormLayout(stock_group)
        stock_layout.setSpacing(10)
        
        # الكمية الحالية
        self.stock_quantity_spin = QSpinBox()
        self.stock_quantity_spin.setRange(0, 999999)
        stock_layout.addRow("الكمية الحالية:", self.stock_quantity_spin)
        
        # الحد الأدنى للمخزون
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 999999)
        stock_layout.addRow("الحد الأدنى للمخزون:", self.min_stock_spin)
        
        # الحد الأقصى للمخزون
        self.max_stock_spin = QSpinBox()
        self.max_stock_spin.setRange(0, 999999)
        stock_layout.addRow("الحد الأقصى للمخزون:", self.max_stock_spin)
        
        # موقع المخزون
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText(self.i18n.get_message("enter_location"))
        stock_layout.addRow("موقع المخزون:", self.location_edit)
        
        layout.addWidget(stock_group)
        
        layout.addStretch()
        return tab
    
    def create_details_tab(self) -> QWidget:
        """إنشاء تبويب التفاصيل الإضافية"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # مجموعة الحالة والإعدادات
        status_group = QGroupBox("الحالة والإعدادات")
        status_layout = QFormLayout(status_group)
        status_layout.setSpacing(10)
        
        # حالة النشاط
        self.is_active_check = QCheckBox("المنتج نشط")
        self.is_active_check.setChecked(True)
        status_layout.addRow("", self.is_active_check)
        
        # قابل للبيع
        self.is_sellable_check = QCheckBox("قابل للبيع")
        self.is_sellable_check.setChecked(True)
        status_layout.addRow("", self.is_sellable_check)
        
        # قابل للشراء
        self.is_purchasable_check = QCheckBox("قابل للشراء")
        self.is_purchasable_check.setChecked(True)
        status_layout.addRow("", self.is_purchasable_check)
        
        # تتبع المخزون
        self.track_stock_check = QCheckBox("تتبع المخزون")
        self.track_stock_check.setChecked(True)
        status_layout.addRow("", self.track_stock_check)
        
        layout.addWidget(status_group)
        
        # مجموعة معلومات إضافية
        extra_group = QGroupBox("معلومات إضافية")
        extra_layout = QFormLayout(extra_group)
        extra_layout.setSpacing(10)
        
        # الوزن
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0, 999999.99)
        self.weight_spin.setDecimals(3)
        self.weight_spin.setSuffix(" كجم")
        extra_layout.addRow(self.i18n.get_message("weight"), self.weight_spin)
        
        # الأبعاد
        dimensions_layout = QHBoxLayout()
        
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0, 999999.99)
        self.length_spin.setDecimals(2)
        cm_unit = self.i18n.get_message("cm_unit")
        self.length_spin.setSuffix(f" {cm_unit}")
        dimensions_layout.addWidget(QLabel(self.i18n.get_message("length")))
        dimensions_layout.addWidget(self.length_spin)
        
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0, 999999.99)
        self.width_spin.setDecimals(2)
        self.width_spin.setSuffix(f" {cm_unit}")
        dimensions_layout.addWidget(QLabel(self.i18n.get_message("width")))
        dimensions_layout.addWidget(self.width_spin)
        
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0, 999999.99)
        self.height_spin.setDecimals(2)
        self.height_spin.setSuffix(f" {cm_unit}")
        dimensions_layout.addWidget(QLabel(self.i18n.get_message("height")))
        dimensions_layout.addWidget(self.height_spin)
        
        extra_layout.addRow(self.i18n.get_message("dimensions"), dimensions_layout)
        
        # تاريخ انتهاء الصلاحية
        self.expiry_date_edit = QDateEdit()
        self.expiry_date_edit.setDate(QDate.currentDate().addYears(1))
        self.expiry_date_edit.setCalendarPopup(True)
        extra_layout.addRow(self.i18n.get_message("expiry_date"), self.expiry_date_edit)
        
        # ملاحظات إضافية
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(self.i18n.get_message("enter_notes"))
        self.notes_edit.setMaximumHeight(80)
        extra_layout.addRow(self.i18n.get_message("notes_label"), self.notes_edit)
        
        layout.addWidget(extra_group)
        
        layout.addStretch()
        return tab
    
    def create_history_tab(self) -> QWidget:
        """إنشاء تبويب سجل المخزون"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # جدول سجل المخزون
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "التاريخ", "النوع", "الكمية", "السبب", "المستخدم"
        ])
        
        # إعداد الجدول
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.history_table)
        
        return tab
    
    def setup_buttons(self, layout: QVBoxLayout):
        """إعداد الأزرار"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # زر الحفظ
        self.save_button = QPushButton(self.i18n.get_message("save"))
        self.save_button.setMinimumHeight(40)
        self.save_button.setDefault(True)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        buttons_layout.addWidget(self.save_button)
        
        # زر الحفظ والإضافة الجديدة (للإضافة فقط)
        if not self.is_edit_mode:
            self.save_and_new_button = QPushButton(self.i18n.get_message("save_and_new"))
            self.save_and_new_button.setMinimumHeight(40)
            buttons_layout.addWidget(self.save_and_new_button)
        
        # زر الإلغاء
        self.cancel_button = QPushButton(self.i18n.get_message("cancel"))
        self.cancel_button.setMinimumHeight(40)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        # أزرار
        self.save_button.clicked.connect(self.handle_save)
        if not self.is_edit_mode:
            self.save_and_new_button.clicked.connect(self.handle_save_and_new)
        self.cancel_button.clicked.connect(self.reject)
        self.generate_barcode_btn.clicked.connect(self.generate_barcode)
        
        # حساب هامش الربح
        self.cost_price_spin.valueChanged.connect(self.calculate_profit_margin)
        self.selling_price_spin.valueChanged.connect(self.calculate_profit_margin)
        
        # تفعيل/تعطيل حقول المخزون
        self.track_stock_check.toggled.connect(self.toggle_stock_fields)
        
        # تحديث المعلومات السريعة
        self.cost_price_spin.valueChanged.connect(self.update_quick_info)
        self.selling_price_spin.valueChanged.connect(self.update_quick_info)
        self.stock_quantity_spin.valueChanged.connect(self.update_quick_info)
    
    def setup_styles(self):
        """إعداد الأنماط"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                border: 1px solid #ddd;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                min-height: 25px;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
                border-color: #3498db;
            }
            
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            
            QTextEdit:focus {
                border-color: #3498db;
            }
            
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton:pressed {
                background-color: #21618c;
            }
            
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            
            QCheckBox {
                font-size: 12px;
                spacing: 5px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #27ae60;
                border-radius: 3px;
                background-color: #27ae60;
            }
        """)
    
    def load_data(self):
        """تحميل البيانات من قاعدة البيانات"""
        try:
            # تحميل الفئات
            categories = self.category_manager.get_all_categories()
            self.category_combo.clear()
            self.category_combo.addItem("-- اختر الفئة --", None)
            for category in categories:
                if category.is_active:
                    self.category_combo.addItem(category.name, category.id)
            
            # تحميل الموردين
            suppliers = self.supplier_manager.get_all_suppliers()
            self.supplier_combo.clear()
            self.supplier_combo.addItem("-- اختر المورد --", None)
            for supplier in suppliers:
                if supplier.is_active:
                    self.supplier_combo.addItem(supplier.name, supplier.id)
                    
        except Exception as e:
            self.logger.error(f"خطأ في تحميل البيانات: {str(e)}")
            QMessageBox.critical(self, self.i18n.get_message("error"), f"{self.i18n.get_message('load_failed')}: {str(e)}")
    
    def populate_form(self):
        """ملء النموذج ببيانات المنتج (للتعديل)"""
        if not self.product:
            return
        
        try:
            # المعلومات الأساسية
            self.name_edit.setText(self.product.name or "")
            self.barcode_edit.setText(self.product.barcode or "")
            self.description_edit.setPlainText(self.product.description or "")
            self.unit_edit.setText(self.product.unit or "")
            
            # الفئة
            if self.product.category_id:
                index = self.category_combo.findData(self.product.category_id)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
            
            # المورد (supplier_id غير موجود في Product - استخدام getattr مع fallback)
            supplier_id = getattr(self.product, 'supplier_id', None)
            if supplier_id:
                index = self.supplier_combo.findData(supplier_id)
                if index >= 0:
                    self.supplier_combo.setCurrentIndex(index)
            
            # الأسعار والمخزون
            self.cost_price_spin.setValue(float(self.product.cost_price or 0))
            self.selling_price_spin.setValue(float(self.product.selling_price or 0))
            # stock_quantity -> current_stock
            stock_qty = getattr(self.product, 'stock_quantity', None) or getattr(self.product, 'current_stock', 0)
            self.stock_quantity_spin.setValue(stock_qty)
            # min_stock_level -> min_stock
            min_stock = getattr(self.product, 'min_stock_level', None) or getattr(self.product, 'min_stock', 0)
            self.min_stock_spin.setValue(min_stock)
            # max_stock_level (غير موجود في Product - استخدام 0 كقيمة افتراضية)
            max_stock = getattr(self.product, 'max_stock_level', None) or 0
            self.max_stock_spin.setValue(max_stock)
            # location (غير موجود في Product - استخدام "" كقيمة افتراضية)
            location = getattr(self.product, 'location', None) or ""
            self.location_edit.setText(location)
            
            # التفاصيل الإضافية
            self.is_active_check.setChecked(self.product.is_active)
            self.is_sellable_check.setChecked(getattr(self.product, 'is_sellable', True))
            self.is_purchasable_check.setChecked(getattr(self.product, 'is_purchasable', True))
            self.track_stock_check.setChecked(getattr(self.product, 'track_stock', True))
            
            # معلومات إضافية
            self.weight_spin.setValue(getattr(self.product, 'weight', 0))
            self.length_spin.setValue(getattr(self.product, 'length', 0))
            self.width_spin.setValue(getattr(self.product, 'width', 0))
            self.height_spin.setValue(getattr(self.product, 'height', 0))
            
            if hasattr(self.product, 'expiry_date') and self.product.expiry_date:
                self.expiry_date_edit.setDate(QDate.fromString(str(self.product.expiry_date), Qt.ISODate))
            
            self.notes_edit.setPlainText(getattr(self.product, 'notes', '') or "")
            
            # تحميل صورة المنتج
            if hasattr(self.product, 'image_path') and self.product.image_path:
                self.original_image_path = self.product.image_path
                self._load_product_image(self.product.image_path)
            
            # حساب هامش الربح
            self.calculate_profit_margin()
            
            # تحميل سجل المخزون
            self.load_stock_history()
            
        except Exception as e:
            self.logger.error(f"خطأ في ملء النموذج: {str(e)}")
            QMessageBox.critical(self, self.i18n.get_message("error"), f"{self.i18n.get_message('load_failed')}: {str(e)}")
    
    def load_stock_history(self):
        """تحميل سجل المخزون"""
        if not self.is_edit_mode or not self.product:
            return
        
        try:
            # هنا يمكن إضافة استعلام لجلب سجل المخزون من قاعدة البيانات
            # مؤقتاً سنضع بيانات وهمية
            self.history_table.setRowCount(0)
            
            # يمكن تطوير هذا لاحقاً لجلب البيانات الفعلية
            sample_data = [
                ["2024-01-15", "إضافة", "+50", "مخزون أولي", "admin"],
                ["2024-01-20", "بيع", "-5", "فاتورة #001", "user1"],
                ["2024-01-25", "تعديل", "+10", "تصحيح المخزون", "admin"],
            ]
            
            for row_data in sample_data:
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                for col, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.history_table.setItem(row, col, item)
                    
        except Exception as e:
            self.logger.error(f"خطأ في تحميل سجل المخزون: {str(e)}")
    
    def generate_barcode(self):
        """توليد باركود تلقائي"""
        try:
            import random
            import string
            
            # توليد باركود من 13 رقم (EAN-13)
            barcode = ''.join(random.choices(string.digits, k=12))
            
            # حساب رقم التحقق
            odd_sum = sum(int(barcode[i]) for i in range(0, 12, 2))
            even_sum = sum(int(barcode[i]) for i in range(1, 12, 2))
            check_digit = (10 - ((odd_sum + even_sum * 3) % 10)) % 10
            
            barcode += str(check_digit)
            self.barcode_edit.setText(barcode)
            
        except Exception as e:
            self.logger.error(f"خطأ في توليد الباركود: {str(e)}")
            QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("barcode_generation_failed"))
    
    def calculate_profit_margin(self):
        """حساب هامش الربح"""
        try:
            cost_price = self.cost_price_spin.value()
            selling_price = self.selling_price_spin.value()
            
            if cost_price > 0 and selling_price > 0:
                profit_margin = ((selling_price - cost_price) / selling_price) * 100
                self.profit_margin_label.setText(self.i18n.get_message("profit_margin_label", percent=f"{profit_margin:.2f}"))
                
                # تغيير لون النص حسب هامش الربح
                if profit_margin < 10:
                    color = "#e74c3c"  # أحمر
                elif profit_margin < 20:
                    color = "#f39c12"  # برتقالي
                else:
                    color = "#27ae60"  # أخضر
                
                self.profit_margin_label.setStyleSheet(f"font-weight: bold; color: {color};")
            else:
                self.profit_margin_label.setText(self.i18n.get_message("profit_margin_label", percent="0.00"))
                self.profit_margin_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")
                
        except Exception as e:
            self.logger.error(f"خطأ في حساب هامش الربح: {str(e)}")
    
    def toggle_stock_fields(self, enabled: bool):
        """تفعيل/تعطيل حقول المخزون"""
        self.stock_quantity_spin.setEnabled(enabled)
        self.min_stock_spin.setEnabled(enabled)
        self.max_stock_spin.setEnabled(enabled)
        self.location_edit.setEnabled(enabled)
    
    def collect_form_data(self) -> Dict[str, Any]:
        """جمع بيانات النموذج"""
        return {
            'name': self.name_edit.text().strip(),
            'name_en': getattr(self, 'name_en_edit', None) and self.name_en_edit.text().strip() or None,
            'barcode': self.barcode_edit.text().strip() or None,
            'description': self.description_edit.toPlainText().strip() or None,
            'unit': self.unit_edit.text().strip() or 'قطعة',
            'category_id': self.category_combo.currentData(),
            'supplier_id': self.supplier_combo.currentData(),
            'cost_price': Decimal(str(self.cost_price_spin.value())),
            'selling_price': Decimal(str(self.selling_price_spin.value())),
            'stock_quantity': self.stock_quantity_spin.value() if hasattr(self, 'stock_quantity_spin') and self.track_stock_check.isChecked() else 0,
            'min_stock_level': self.min_stock_spin.value() if hasattr(self, 'min_stock_spin') and self.track_stock_check.isChecked() else 0,
            'max_stock_level': self.max_stock_spin.value() if hasattr(self, 'max_stock_spin') and self.track_stock_check.isChecked() else 0,
            'location': getattr(self, 'location_edit', None) and self.location_edit.text().strip() or None,
            'is_active': self.is_active_check.isChecked(),
            'is_sellable': getattr(self, 'is_sellable_check', None) and self.is_sellable_check.isChecked() or True,
            'is_purchasable': getattr(self, 'is_purchasable_check', None) and self.is_purchasable_check.isChecked() or True,
            'track_stock': self.track_stock_check.isChecked(),
            'weight': getattr(self, 'weight_spin', None) and self.weight_spin.value() or None,
            'length': getattr(self, 'length_spin', None) and self.length_spin.value() or None,
            'width': getattr(self, 'width_spin', None) and self.width_spin.value() or None,
            'height': getattr(self, 'height_spin', None) and self.height_spin.value() or None,
            'expiry_date': getattr(self, 'expiry_date_edit', None) and self.expiry_date_edit.date().toString(Qt.ISODate) or None,
            'notes': getattr(self, 'notes_edit', None) and self.notes_edit.toPlainText().strip() or None,
            'image_path': self._process_image_path()  # معالجة الصورة باستخدام الخدمة
        }
    
    def handle_save(self):
        """معالجة حفظ المنتج"""
        self.save_product(close_after_save=True)
    
    def handle_save_and_new(self):
        """معالجة حفظ المنتج وإضافة جديد"""
        self.save_product(close_after_save=False)
    
    def save_product(self, close_after_save: bool = True):
        """حفظ المنتج"""
        try:
            # 🛡️ التحقق من صحة البيانات قبل الحفظ
            product_name = self.name_edit.text().strip()
            if not product_name:
                QMessageBox.warning(self, self.i18n.get_message("error"), self.i18n.get_message("product_name_required"))
                return
            
            # التحقق من السعر
            try:
                cost_price = self.cost_price_spin.value()
                selling_price = self.selling_price_spin.value()
                
                if cost_price < 0:
                    QMessageBox.warning(self, self.i18n.get_message("error"), self.i18n.get_message("cost_price_negative"))
                    return
                
                if selling_price <= 0:
                    QMessageBox.warning(self, self.i18n.get_message("error"), self.i18n.get_message("selling_price_zero"))
                    return
                
                if selling_price < cost_price:
                    reply = QMessageBox.question(
                        self,
                        "تحذير",
                        f"سعر البيع ({selling_price:.2f}) أقل من سعر التكلفة ({cost_price:.2f}). هل تريد المتابعة؟",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
            except (ValueError, TypeError) as e:
                QMessageBox.warning(self, self.i18n.get_message("error"), f"{self.i18n.get_message('invalid_prices')}: {str(e)}")
                return
            
            # التحقق من الكمية
            try:
                stock_quantity = self.stock_quantity_spin.value()
                if stock_quantity < 0:
                    QMessageBox.warning(self, self.i18n.get_message("error"), self.i18n.get_message("quantity_negative"))
                    return
            except (ValueError, TypeError) as e:
                QMessageBox.warning(self, self.i18n.get_message("error"), f"{self.i18n.get_message('invalid_quantity')}: {str(e)}")
                return
            
            # جمع البيانات
            product_data = self.collect_form_data()
            
            # تعطيل الواجهة أثناء الحفظ
            self.set_ui_enabled(False)
            self.progress_bar.setVisible(True)
            
            # بدء التحقق من صحة البيانات
            product_id = self.product.id if self.is_edit_mode else None
            self.validation_worker = ProductValidationWorker(
                self.product_manager,
                product_data,
                product_id
            )
            self.validation_worker.validation_completed.connect(
                lambda success, message, data: self.on_validation_completed(
                    success, message, data, close_after_save
                )
            )
            self.validation_worker.start()
            
        except Exception as e:
            self.set_ui_enabled(True)
            self.progress_bar.setVisible(False)
            self.logger.error(f"خطأ في حفظ المنتج: {str(e)}")
            QMessageBox.critical(self, self.i18n.get_message("error"), f"{self.i18n.get_message('save_failed')}: {str(e)}")
    
    def on_validation_completed(self, success: bool, message: str, data: Dict[str, Any], close_after_save: bool):
        """معالجة اكتمال التحقق من صحة البيانات"""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        
        if not success:
            QMessageBox.critical(self, self.i18n.get_message("data_error"), message)
            return
        
        try:
            if self.is_edit_mode:
                if self.product_service:
                    # build enhanced Product instance
                    try:
                        enhanced_product = EnhancedProduct(
                            id=self.product.id,
                            name=data['name'],
                            name_en=data.get('name_en'),
                            barcode=data.get('barcode'),
                            category_id=data.get('category_id'),
                            unit=data.get('unit', 'قطعة'),
                            cost_price=data.get('cost_price', 0),
                            base_price=data.get('selling_price', 0),
                            current_stock=data.get('stock_quantity', 0),
                            min_stock=data.get('min_stock_level', 0),
                            max_stock=data.get('max_stock_level', 0),
                            description=data.get('description'),
                            image_path=data.get('image_path'),
                            is_active=data.get('is_active', True)
                        )
                        success = self.product_service.update_product(enhanced_product)
                    except Exception as e:
                        self.logger.error(f"خطأ في تحضير المنتج المحسّن للتحديث: {str(e)}")
                        success = False

                    if success:
                        updated_product = self.product_service.get_product_by_id(self.product.id)
                        if updated_product:
                            self.product = updated_product
                            self.product_saved.emit(updated_product)
                            
                            # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                            try:
                                from ...core.signals import signals
                                signals.inventory_updated.emit()
                                signals.inventory_item_updated.emit(self.product.id)
                                if self.logger:
                                    self.logger.debug(f"✅ تم إطلاق إشارات: inventory_updated, inventory_item_updated")
                            except Exception as e:
                                if self.logger:
                                    self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")
                            
                            QMessageBox.information(self, self.i18n.get_message("success"), self.i18n.get_message("product_updated"))
                            if close_after_save:
                                self.accept()
                        else:
                            QMessageBox.critical(self, self.i18n.get_message("error"), self.i18n.get_message("load_failed"))
                    else:
                        QMessageBox.critical(self, self.i18n.get_message("error"), self.i18n.get_message("update_failed"))
                else:
                    # legacy update
                    success = self.product_manager.update_product(self.product.id, data)
                    if success:
                        updated_product = self.product_manager.get_product_by_id(self.product.id)
                        if updated_product:
                            self.product = updated_product
                            self.product_saved.emit(updated_product)
                            
                            # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                            try:
                                from ...core.signals import signals
                                signals.inventory_updated.emit()
                                signals.inventory_item_updated.emit(self.product.id)
                                if self.logger:
                                    self.logger.debug(f"✅ تم إطلاق إشارات: inventory_updated, inventory_item_updated")
                            except Exception as e:
                                if self.logger:
                                    self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")
                            
                            QMessageBox.information(self, self.i18n.get_message("success"), self.i18n.get_message("product_updated"))
                            if close_after_save:
                                self.accept()
                        else:
                            QMessageBox.critical(self, self.i18n.get_message("error"), self.i18n.get_message("load_failed"))
                    else:
                        QMessageBox.critical(self, self.i18n.get_message("error"), self.i18n.get_message("update_failed"))
            else:
                # إنشاء منتج جديد (افضلية للخدمة المحسنة)
                if self.product_service:
                    try:
                        enhanced_product = EnhancedProduct(
                            name=data['name'],
                            name_en=data.get('name_en'),
                            barcode=data.get('barcode'),
                            category_id=data.get('category_id'),
                            unit=data.get('unit', 'قطعة'),
                            cost_price=data.get('cost_price', 0),
                            base_price=data.get('selling_price', 0),
                            current_stock=data.get('stock_quantity', 0),
                            min_stock=data.get('min_stock_level', 0),
                            max_stock=data.get('max_stock_level', 0),
                            description=data.get('description'),
                            image_path=data.get('image_path'),
                            is_active=data.get('is_active', True)
                        )
                        product_id = self.product_service.create_product(enhanced_product)
                    except Exception as e:
                        self.logger.error(f"خطأ في إنشاء المنتج المحسّن: {str(e)}")
                        product_id = None

                    if product_id:
                        created_product = self.product_service.get_product_by_id(product_id)
                        if created_product:
                            self.product_saved.emit(created_product)
                            
                            # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                            try:
                                from ...core.signals import signals
                                signals.inventory_updated.emit()
                                signals.inventory_item_added.emit(product_id)
                                if self.logger:
                                    self.logger.debug(f"✅ تم إطلاق إشارات: inventory_updated, inventory_item_added")
                            except Exception as e:
                                if self.logger:
                                    self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")
                            
                            self.notify.show_success("نجح", f"تم إضافة المنتج بنجاح\nرقم المنتج: {product_id}")
                            if close_after_save:
                                self.accept()
                            else:
                                self.clear_form()
                        else:
                            QMessageBox.critical(self, "خطأ", "فشل في إعادة تحميل المنتج المُنشأ")
                    else:
                        QMessageBox.critical(self, "خطأ", "فشل في إضافة المنتج")
                else:
                    # تحويل البيانات إلى كائن Product (legacy)
                    product = Product(
                        name=data['name'],
                        name_en=data.get('name_en'),
                        barcode=data.get('barcode'),
                        category_id=data.get('category_id'),
                        unit=data.get('unit', 'قطعة'),
                        cost_price=data['cost_price'],
                        selling_price=data['selling_price'],
                        min_stock=data.get('min_stock_level', 0),
                        current_stock=data.get('stock_quantity', 0),
                        description=data.get('description'),
                        image_path=data.get('image_path'),
                        is_active=data.get('is_active', True)
                    )
                    product_id = self.product_manager.create_product(product)
                    if product_id:
                        # إعادة تحميل المنتج من قاعدة البيانات
                        created_product = self.product_manager.get_product_by_id(product_id)
                        if created_product:
                            self.product_saved.emit(created_product)
                            
                            # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                            try:
                                from ...core.signals import signals
                                signals.inventory_updated.emit()
                                signals.inventory_item_added.emit(product_id)
                                if self.logger:
                                    self.logger.debug(f"✅ تم إطلاق إشارات: inventory_updated, inventory_item_added")
                            except Exception as e:
                                if self.logger:
                                    self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")
                            
                            self.notify.show_success("نجح", f"تم إضافة المنتج بنجاح\nرقم المنتج: {product_id}")
                            if close_after_save:
                                self.accept()
                            else:
                                # مسح النموذج للإضافة الجديدة
                                self.clear_form()
                        else:
                            self.notify.show_error("خطأ", "فشل في إعادة تحميل المنتج المُنشأ")
                    else:
                        self.notify.show_error("خطأ", "فشل في إضافة المنتج")
                    
        except Exception as e:
            self.logger.error(f"خطأ في حفظ المنتج: {str(e)}")
            self.notify.show_error("خطأ", f"حدث خطأ أثناء الحفظ: {str(e)}")
    
    # الدوال الجديدة للميزات المتقدمة
    def select_image(self, event=None):
        """اختيار صورة للمنتج"""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self,
                "اختيار صورة المنتج",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            )
            
            if file_path:
                # تحميل وعرض الصورة
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # تغيير حجم الصورة للمعاينة
                    scaled_pixmap = pixmap.scaled(
                        200, 200, 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    # حفظ المسار المؤقت (سيتم نسخه عند الحفظ)
                    self.current_image_path = file_path
                    self.remove_image_btn.setEnabled(True)
                else:
                    self.notify.show_warning("تحذير", "فشل في تحميل الصورة")
                    
        except Exception as e:
            self.logger.error(f"خطأ في اختيار الصورة: {str(e)}")
            self.notify.show_error("خطأ", f"فشل في اختيار الصورة:\n{str(e)}")
    
    def remove_image(self):
        """حذف صورة المنتج"""
        self.image_label.clear()
        self.image_label.setText(self.i18n.get_message("no_image"))
        self.current_image_path = None
        self.original_image_path = None
        self.remove_image_btn.setEnabled(False)
    
    def _process_image_path(self) -> Optional[str]:
        """
        معالجة مسار الصورة باستخدام خدمة إدارة الصور
        
        Returns:
            مسار الصورة المحفوظة أو None
        """
        try:
            # إذا لم تكن هناك صورة جديدة، استخدم الصورة الأصلية
            if not self.current_image_path:
                return self.original_image_path
            
            # إذا كانت الصورة الجديدة هي نفس الصورة الأصلية (لم يتم التغيير)
            if self.current_image_path == self.original_image_path:
                return self.original_image_path
            
            # إذا كانت الصورة في مجلد المنتجات بالفعل (تم حفظها مسبقاً)
            if self.image_manager and 'assets/images/products' in str(self.current_image_path):
                return self.current_image_path
            
            # حفظ الصورة الجديدة باستخدام الخدمة
            if self.image_manager:
                product_id = self.product.id if self.is_edit_mode and self.product else None
                product_name = self.name_edit.text().strip() if hasattr(self, 'name_edit') else None
                
                saved_path = self.image_manager.save_product_image(
                    self.current_image_path,
                    product_id=product_id,
                    product_name=product_name,
                    create_thumbnails=True
                )
                
                if saved_path:
                    # حذف الصورة القديمة إذا كانت موجودة
                    if self.original_image_path and self.original_image_path != saved_path:
                        self.image_manager.delete_product_image(self.original_image_path)
                    
                    return saved_path
                else:
                    self.logger.warning("فشل في حفظ الصورة باستخدام الخدمة، استخدام المسار الأصلي")
                    return self.current_image_path
            else:
                # إذا لم تكن الخدمة متاحة، استخدم المسار الأصلي
                return self.current_image_path
                
        except Exception as e:
            self.logger.error(f"خطأ في معالجة مسار الصورة: {str(e)}", exc_info=True)
            return self.current_image_path if self.current_image_path else self.original_image_path
    
    def _load_product_image(self, image_path: str):
        """
        تحميل وعرض صورة المنتج
        
        Args:
            image_path: مسار الصورة (نسبي أو مطلق)
        """
        try:
            if not image_path:
                return
            
            # محاولة استخدام خدمة إدارة الصور للحصول على الصورة
            if self.image_manager:
                # محاولة استخدام صورة المعاينة أولاً
                preview_path = self.image_manager.get_image_path(image_path, 'preview')
                if preview_path and preview_path.exists():
                    pixmap = QPixmap(str(preview_path))
                else:
                    # استخدام الصورة الأصلية
                    original_path = self.image_manager.get_image_path(image_path, 'original')
                    if original_path and original_path.exists():
                        pixmap = QPixmap(str(original_path))
                    else:
                        # محاولة استخدام المسار مباشرة
                        full_path = Path(image_path)
                        if not full_path.is_absolute():
                            full_path = Path(__file__).parent.parent.parent.parent / image_path
                        if full_path.exists():
                            pixmap = QPixmap(str(full_path))
                        else:
                            self.logger.warning(f"لم يتم العثور على الصورة: {image_path}")
                            return
            else:
                # استخدام المسار مباشرة
                full_path = Path(image_path)
                if not full_path.is_absolute():
                    full_path = Path(__file__).parent.parent.parent.parent / image_path
                if full_path.exists():
                    pixmap = QPixmap(str(full_path))
                else:
                    self.logger.warning(f"لم يتم العثور على الصورة: {image_path}")
                    return
            
            if not pixmap.isNull():
                # تغيير حجم الصورة للمعاينة
                scaled_pixmap = pixmap.scaled(
                    200, 200,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.current_image_path = image_path
                self.remove_image_btn.setEnabled(True)
            else:
                self.logger.warning(f"فشل في تحميل الصورة: {image_path}")
                
        except Exception as e:
            self.logger.error(f"خطأ في تحميل صورة المنتج: {str(e)}", exc_info=True)
    
    def search_similar_products(self):
        """البحث عن منتجات مشابهة"""
        try:
            product_name = self.name_edit.text().strip()
            if not product_name:
                self.notify.show_info("معلومات", "يرجى إدخال اسم المنتج أولاً")
                return
            
            # البحث في قاعدة البيانات
            similar_products = self.product_manager.search_products(product_name)
            
            if similar_products:
                # عرض النتائج في رسالة
                products_list = "\n".join([f"- {p.name} (الباركود: {p.barcode})" 
                                         for p in similar_products[:5]])
                self.notify.show_info(
                    "منتجات مشابهة", 
                    f"تم العثور على المنتجات التالية:\n\n{products_list}"
                )
            else:
                self.notify.show_info("معلومات", "لم يتم العثور على منتجات مشابهة")
                
        except Exception as e:
            self.logger.error(f"خطأ في البحث عن منتجات مشابهة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في البحث:\n{str(e)}")
    
    def copy_from_existing(self):
        """نسخ بيانات من منتج موجود"""
        try:
            # الحصول على قائمة المنتجات
            products = self.product_manager.get_all_products()
            
            if not products:
                self.notify.show_info("معلومات", "لا توجد منتجات في قاعدة البيانات")
                return
            
            # إنشاء قائمة بأسماء المنتجات
            product_names = [f"{p.name} - {p.barcode}" for p in products]
            
            # عرض نافذة اختيار
            from PySide6.QtWidgets import QInputDialog
            item, ok = QInputDialog.getItem(
                self, 
                "اختيار منتج للنسخ", 
                "اختر المنتج المراد نسخ بياناته:",
                product_names, 
                0, 
                False
            )
            
            if ok and item:
                # العثور على المنتج المحدد
                selected_index = product_names.index(item)
                selected_product = products[selected_index]
                
                # نسخ البيانات (باستثناء الاسم والباركود)
                if hasattr(selected_product, 'category_name'):
                    self.category_combo.setCurrentText(selected_product.category_name or "")
                if hasattr(selected_product, 'supplier_name'):
                    self.supplier_combo.setCurrentText(selected_product.supplier_name or "")
                self.unit_edit.setText(selected_product.unit or "")
                self.cost_price_spin.setValue(float(selected_product.cost_price or 0))
                self.selling_price_spin.setValue(float(selected_product.selling_price or 0))
                
                self.notify.show_success("نجح", "تم نسخ بيانات المنتج بنجاح")
                
        except Exception as e:
            self.logger.error(f"خطأ في نسخ المنتج: {str(e)}")
            self.notify.show_error("خطأ", f"فشل في نسخ البيانات:\n{str(e)}")
    
    def show_profit_calculator(self):
        """عرض حاسبة هامش الربح"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton
            
            # إنشاء نافذة الحاسبة
            calc_dialog = QDialog(self)
            calc_dialog.setWindowTitle("حاسبة هامش الربح")
            calc_dialog.setFixedSize(300, 200)
            
            layout = QVBoxLayout(calc_dialog)
            
            # حقول الإدخال
            cost_layout = QHBoxLayout()
            cost_layout.addWidget(QLabel("سعر التكلفة:"))
            cost_spin = QDoubleSpinBox()
            cost_spin.setMaximum(999999.99)
            cost_spin.setValue(self.cost_price_spin.value())
            cost_layout.addWidget(cost_spin)
            layout.addLayout(cost_layout)
            
            selling_layout = QHBoxLayout()
            selling_layout.addWidget(QLabel("سعر البيع:"))
            selling_spin = QDoubleSpinBox()
            selling_spin.setMaximum(999999.99)
            selling_spin.setValue(self.selling_price_spin.value())
            selling_layout.addWidget(selling_spin)
            layout.addLayout(selling_layout)
            
            # عرض النتائج
            result_label = QLabel("هامش الربح: 0.00%")
            result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(result_label)
            
            profit_label = QLabel("الربح: 0.00")
            layout.addWidget(profit_label)
            
            # دالة حساب الربح
            def calculate():
                cost = cost_spin.value()
                selling = selling_spin.value()
                if cost > 0:
                    profit = selling - cost
                    margin = (profit / cost) * 100
                    result_label.setText(f"هامش الربح: {margin:.2f}%")
                    profit_label.setText(f"الربح: {profit:.2f}")
                    
                    # تلوين النتيجة
                    if margin > 20:
                        result_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
                    elif margin > 10:
                        result_label.setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")
                    else:
                        result_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
            
            # ربط الأحداث
            cost_spin.valueChanged.connect(calculate)
            selling_spin.valueChanged.connect(calculate)
            
            # أزرار
            buttons_layout = QHBoxLayout()
            apply_btn = QPushButton("تطبيق")
            apply_btn.clicked.connect(lambda: (
                self.cost_price_spin.setValue(cost_spin.value()),
                self.selling_price_spin.setValue(selling_spin.value()),
                calc_dialog.accept()
            ))
            buttons_layout.addWidget(apply_btn)
            
            close_btn = QPushButton("إغلاق")
            close_btn.clicked.connect(calc_dialog.reject)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            # حساب أولي
            calculate()
            
            calc_dialog.exec()
            
        except Exception as e:
            self.logger.error(f"خطأ في حاسبة الربح: {str(e)}")
            self.notify.show_error("خطأ", f"فشل في فتح الحاسبة:\n{str(e)}")
    
    def clear_form(self):
        """مسح النموذج"""
        # المعلومات الأساسية
        self.name_edit.clear()
        self.barcode_edit.clear()
        self.description_edit.clear()
        self.unit_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.supplier_combo.setCurrentIndex(0)
        
        # الأسعار والمخزون
        self.cost_price_spin.setValue(0)
        self.selling_price_spin.setValue(0)
        self.stock_quantity_spin.setValue(0)
        self.min_stock_spin.setValue(0)
        self.max_stock_spin.setValue(0)
        self.location_edit.clear()
        
        # التفاصيل الإضافية
        self.is_active_check.setChecked(True)
        self.is_sellable_check.setChecked(True)
        self.is_purchasable_check.setChecked(True)
        self.track_stock_check.setChecked(True)
        
        self.weight_spin.setValue(0)
        self.length_spin.setValue(0)
        self.width_spin.setValue(0)
        self.height_spin.setValue(0)
        self.expiry_date_edit.setDate(QDate.currentDate().addYears(1))
        self.notes_edit.clear()
        
        # التركيز على حقل الاسم
        self.name_edit.setFocus()
        self.tab_widget.setCurrentIndex(0)
    
    def update_quick_info(self):
        """تحديث المعلومات السريعة"""
        try:
            # تحديث معلومات الربح
            cost = self.cost_price_spin.value()
            selling = self.selling_price_spin.value()
            
            if cost > 0 and selling > 0:
                profit = selling - cost
                margin = (profit / selling) * 100
                self.profit_info_label.setText(f"هامش الربح: {margin:.2f}%")
                
                # تلوين حسب الهامش
                if margin > 20:
                    self.profit_info_label.setStyleSheet("font-weight: bold; color: #27ae60;")
                elif margin > 10:
                    self.profit_info_label.setStyleSheet("font-weight: bold; color: #f39c12;")
                else:
                    self.profit_info_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            else:
                self.profit_info_label.setText("هامش الربح: 0.00%")
                self.profit_info_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")
            
            # تحديث معلومات المخزون
            if hasattr(self, 'stock_info_label'):
                current_stock = self.stock_quantity_spin.value()
                min_stock = self.min_stock_spin.value()
                
                if current_stock <= min_stock and min_stock > 0:
                    self.stock_info_label.setText("حالة المخزون: منخفض")
                    self.stock_info_label.setStyleSheet("color: #e74c3c;")
                elif current_stock <= min_stock * 2 and min_stock > 0:
                    self.stock_info_label.setText("حالة المخزون: متوسط")
                    self.stock_info_label.setStyleSheet("color: #f39c12;")
                else:
                    self.stock_info_label.setText("حالة المخزون: جيد")
                    self.stock_info_label.setStyleSheet("color: #27ae60;")
                    
        except Exception as e:
            self.logger.error(f"خطأ في تحديث المعلومات السريعة: {str(e)}")
    
    def set_ui_enabled(self, enabled: bool):
        """تفعيل/تعطيل عناصر الواجهة"""
        self.tab_widget.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        if hasattr(self, 'save_and_new_button'):
            self.save_and_new_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
    
    def showEvent(self, event: QShowEvent):
        """معالجة حدث العرض مع fade in animation"""
        super().showEvent(event)
        # تطبيق fade in animation
        QTimer.singleShot(50, lambda: self.animation_manager.fade_in(self, duration=300))
    
    def closeEvent(self, event: QCloseEvent):
        """معالجة إغلاق النافذة مع fade out animation"""
        if self.validation_worker and self.validation_worker.isRunning():
            self.validation_worker.terminate()
            self.validation_worker.wait()
        
        # تطبيق fade out animation قبل الإغلاق
        if hasattr(self, 'animation_manager'):
            # حفظ event للاستخدام لاحقاً
            self._close_event = event
            self.animation_manager.fade_out(self, duration=200)
            QTimer.singleShot(250, self._finalize_close)
        else:
            super().closeEvent(event)
    
    def _finalize_close(self):
        """إتمام إغلاق النافذة بعد انتهاء animation"""
        if hasattr(self, '_close_event'):
            super().closeEvent(self._close_event)
            delattr(self, '_close_event')
        else:
            self.close()


# اختبار النافذة
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # إعداد الخط العربي
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # إعداد اتجاه النص
    app.setLayoutDirection(Qt.RightToLeft)
    
    # إنشاء قاعدة بيانات وهمية للاختبار
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager(":memory:")
    
    dialog = ProductDialog(db)
    
    if dialog.exec() == QDialog.Accepted:
        print("تم حفظ المنتج بنجاح")
    else:
        print("تم إلغاء العملية")
    
    sys.exit()
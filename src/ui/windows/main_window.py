#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
النافذة الرئيسية - Main Window
النافذة الرئيسية للتطبيق مع جميع الوحدات
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QStatusBar, QToolBar,
    QLabel, QPushButton, QMessageBox, QSplashScreen, QDialog,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QFrame,
    QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont, QColor
from typing import Optional
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.customer import CustomerManager
from src.models.supplier import SupplierManager
from src.core.caching_service import AdvancedCachingService

class MainWindow(QMainWindow):
    """النافذة الرئيسية للتطبيق"""
    
    def __init__(self, config_manager=None, db_manager=None, logger=None):
        super().__init__()
        
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.logger = logger
        
        # تهيئة الخدمات
        self.init_services()
        
        self.setWindowTitle("الإصدار المنطقي - نظام إدارة التجارة العامة")
        self.setMinimumSize(1200, 800)
        
        # إعداد الواجهة
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()
        
        # تطبيق الإعدادات
        self.apply_settings()
        
        if self.logger:
            self.logger.info("تم إنشاء النافذة الرئيسية")

    class BackupWorker(QThread):
        finished = Signal(bool, str)

        def __init__(self, db_manager, mode: str, logger=None, backup_file: Optional[str] = None, metadata: Optional[dict] = None):
            super().__init__()
            self.db_manager = db_manager
            self.mode = mode  # 'backup' or 'restore'
            self.logger = logger
            self.backup_file = backup_file
            self.metadata = metadata or {}

        def run(self):
            try:
                if self.mode == 'backup':
                    path = None
                    if hasattr(self.db_manager, 'backup_database_encrypted'):
                        path = self.db_manager.backup_database_encrypted(metadata=self.metadata)
                        ok = bool(path)
                        self.finished.emit(ok, str(path) if path else "")
                    else:
                        ok = self.db_manager.backup_database()
                        self.finished.emit(ok, "")
                elif self.mode == 'restore':
                    ok = False
                    if hasattr(self.db_manager, 'restore_database_encrypted') and self.backup_file:
                        ok = self.db_manager.restore_database_encrypted(self.backup_file)
                    self.finished.emit(ok, "")
                else:
                    self.finished.emit(False, "وضع غير معروف")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"خطأ في مهمة النسخ الاحتياطي/الاستعادة: {str(e)}")
                self.finished.emit(False, str(e))
    
    def init_services(self):
        """تهيئة الخدمات المطلوبة"""
        try:
            if self.db_manager:
                # حاول تهيئة النسخ المحسنة أولاً ثم الرجوع إلى النسخ القديمة إذا لم تتوفر
                try:
                    from src.services.inventory_service_enhanced import InventoryService as EnhancedInventoryService
                    from src.services.product_service_enhanced import ProductService as EnhancedProductService

                    self.inventory_service = EnhancedInventoryService(self.db_manager, self.logger)
                    # ProductService يحتوي على واجهات البحث والإحصاء
                    self.product_service = EnhancedProductService(self.db_manager, self.logger)

                    # توفير واجهة متوافقة مع الكود الحالي
                    # بعض أجزاء الواجهة تتوقع وجود product_manager و generate_inventory_report
                    self.inventory_service.product_manager = self.product_service
                    # ربط اسم الدالة المتوقع generate_inventory_report
                    if not hasattr(self.inventory_service, 'generate_inventory_report') and hasattr(self.inventory_service, 'get_inventory_report'):
                        self.inventory_service.generate_inventory_report = self.inventory_service.get_inventory_report

                except Exception:
                    # استرجاع الإصدارات التقليدية إن لم تتوفر النسخ المحسّنة
                    try:
                        from src.services.inventory_service import InventoryService
                        from src.services.product_service import ProductService
                        self.inventory_service = InventoryService(self.db_manager, self.logger)
                        self.product_service = ProductService(self.db_manager, self.logger)
                        self.inventory_service.product_manager = getattr(self.product_service, 'product_manager', None) or self.product_service
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"تعذر تهيئة خدمة المخزون: {e}")
                        self.inventory_service = None

                # تهيئة خدمة المبيعات (محسنة أو قديمة)
                try:
                    from src.services.sales_service_enhanced import SalesService as EnhancedSalesService
                    self.sales_service = EnhancedSalesService(self.db_manager, self.logger, inventory_service=getattr(self, 'inventory_service', None), product_service=getattr(self, 'product_service', None))
                except Exception:
                    try:
                        from src.services.sales_service import SalesService
                        self.sales_service = SalesService(self.db_manager, self.logger)
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"تعذر تهيئة خدمة المبيعات: {e}")
                        self.sales_service = None

                # تهيئة خدمة التقارير
                try:
                    from src.services.reports_service_enhanced import ReportsService as EnhancedReportsService
                    self.reports_service = EnhancedReportsService(self.db_manager, self.logger)
                except Exception:
                    try:
                        from src.services.reports_service import ReportsService
                        self.reports_service = ReportsService(self.db_manager)
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"تعذر تهيئة خدمة التقارير: {e}")
                        self.reports_service = None

                # تهيئة خدمة المدفوعات / الفواتير
                try:
                    from src.services.billing_service import BillingService
                    self.payment_service = BillingService(self.db_manager, self.logger)
                except Exception:
                    try:
                        from src.services.payment_service import PaymentService
                        self.payment_service = PaymentService(self.db_manager)
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"تعذر تهيئة خدمة المدفوعات: {e}")
                        self.payment_service = None

                # تهيئة مديري العملاء والموردين من النماذج
                try:
                    self.customer_manager = CustomerManager(self.db_manager, self.logger)
                except Exception:
                    self.customer_manager = None
                try:
                    self.supplier_manager = SupplierManager(self.db_manager, self.logger)
                except Exception:
                    self.supplier_manager = None

                if self.logger:
                    self.logger.info("تم تهيئة الخدمات (محسنة/تقليدية) في النافذة الرئيسية")

                # تهيئة خدمة التخزين المؤقت من الإعدادات
                try:
                    cache_enabled = True
                    default_ttl = 60
                    disk_cache = False
                    disk_path = str(Path(self.db_manager.db_path).parent / "cache") if hasattr(self.db_manager, 'db_path') else "data/cache"
                    if self.config_manager and hasattr(self.config_manager, 'get'):
                        cache_enabled = bool(self.config_manager.get('cache.enabled', True))
                        default_ttl = int(self.config_manager.get('cache.default_ttl', 60))
                        disk_cache = bool(self.config_manager.get('cache.disk_cache', False))
                        disk_path = self.config_manager.get('cache.disk_path', disk_path)
                    self.cache = AdvancedCachingService(default_ttl=default_ttl, enable_disk_cache=disk_cache, disk_cache_path=disk_path) if cache_enabled else None
                    if self.logger:
                        self.logger.info(f"خدمة التخزين المؤقت: {'مفعلة' if self.cache else 'معطلة'} (TTL={default_ttl}s, Disk={disk_cache})")
                except Exception as e:
                    self.cache = None
                    if self.logger:
                        self.logger.warning(f"تعذر تهيئة خدمة التخزين المؤقت: {e}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تهيئة الخدمات: {str(e)}")
            self.inventory_service = None
            self.sales_service = None
            self.reports_service = None
            self.payment_service = None
            self.customer_manager = None
            self.supplier_manager = None
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # الويدجت المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        
        # شريط الترحيب
        welcome_layout = QHBoxLayout()
        welcome_label = QLabel("مرحباً بك في الإصدار المنطقي")
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addStretch()
        
        main_layout.addLayout(welcome_layout)
        
        # التبويبات الرئيسية
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)
        
        # تبويب المخزون
        self.inventory_tab = self.create_inventory_tab()
        self.tab_widget.addTab(self.inventory_tab, "🏪 المخزون")
        
        # تبويب المبيعات
        self.sales_tab = self.create_sales_tab()
        self.tab_widget.addTab(self.sales_tab, "💰 المبيعات")
        
        # تبويب المشتريات
        self.purchases_tab = self.create_purchases_tab()
        self.tab_widget.addTab(self.purchases_tab, "📦 المشتريات")
        
        # تبويب التقارير
        self.reports_tab = self.create_reports_tab()
        self.tab_widget.addTab(self.reports_tab, "📊 التقارير")
        
        # تبويب العملاء والموردين
        self.contacts_tab = self.create_contacts_tab()
        self.tab_widget.addTab(self.contacts_tab, "👥 العملاء والموردين")
        
        # تبويب الإعدادات
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "⚙️ الإعدادات")
        
        main_layout.addWidget(self.tab_widget)
    
    def create_inventory_tab(self) -> QWidget:
        """إنشاء تبويب المخزون"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # عنوان القسم
        title = QLabel("إدارة المخزون")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60; margin-bottom: 4px;")
        layout.addWidget(title)
        
        # أزرار سريعة
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        add_product_btn = QPushButton("➕ إضافة منتج")
        add_product_btn.setMinimumHeight(36)
        add_product_btn.clicked.connect(self.add_product)
        buttons_layout.addWidget(add_product_btn)
        
        manage_categories_btn = QPushButton("📂 إدارة الفئات")
        manage_categories_btn.setMinimumHeight(36)
        manage_categories_btn.clicked.connect(self.manage_categories)
        buttons_layout.addWidget(manage_categories_btn)
        
        inventory_report_btn = QPushButton("📋 تقرير المخزون")
        inventory_report_btn.setMinimumHeight(36)
        inventory_report_btn.clicked.connect(self.inventory_report)
        buttons_layout.addWidget(inventory_report_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # منطقة المرشحات
        filters_frame = QFrame()
        filters_frame.setObjectName("inventoryFiltersFrame")
        filters_frame.setStyleSheet("""
            QFrame#inventoryFiltersFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e4e7;
                border-radius: 6px;
            }
        """)
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(12)
        
        search_label = QLabel("بحث:")
        search_label.setStyleSheet("color: #34495e; font-weight: 600;")
        filters_layout.addWidget(search_label)
        
        self.inventory_search_input = QLineEdit()
        self.inventory_search_input.setPlaceholderText("ابحث باسم المنتج أو الباركود...")
        self.inventory_search_input.textChanged.connect(self.on_inventory_filters_changed)
        filters_layout.addWidget(self.inventory_search_input, 2)
        
        category_label = QLabel("الفئة:")
        category_label.setStyleSheet("color: #34495e; font-weight: 600;")
        filters_layout.addWidget(category_label)
        
        self.inventory_category_combo = QComboBox()
        self.inventory_category_combo.setMinimumWidth(200)
        self.inventory_category_combo.currentIndexChanged.connect(self.on_inventory_filters_changed)
        filters_layout.addWidget(self.inventory_category_combo, 1)
        
        self.inventory_refresh_btn = QPushButton("🔄 تحديث")
        self.inventory_refresh_btn.setMinimumHeight(32)
        self.inventory_refresh_btn.clicked.connect(self.refresh_inventory_data)
        filters_layout.addWidget(self.inventory_refresh_btn)
        
        layout.addWidget(filters_frame)
        
        # ملخص المخزون
        summary_group = QGroupBox("ملخص المخزون")
        summary_layout = QHBoxLayout(summary_group)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(18)
        
        summary_items = [
            ("total_products", "إجمالي المنتجات"),
            ("total_categories", "إجمالي الفئات"),
            ("total_stock_value", "قيمة المخزون"),
            ("low_stock_items", "منتجات مخزون منخفض"),
            ("out_of_stock_items", "منتجات نفدت"),
            ("expired_items", "منتجات منتهية")
        ]
        
        self.inventory_summary_labels = {}
        for key, title_text in summary_items:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)
            
            title_label = QLabel(title_text)
            title_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            value_label = QLabel("-")
            value_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
            
            container_layout.addWidget(title_label)
            container_layout.addWidget(value_label)
            container_layout.addStretch()
            
            summary_layout.addWidget(container)
            self.inventory_summary_labels[key] = value_label
        
        summary_layout.addStretch()
        layout.addWidget(summary_group)
        
        # جدول المخزون
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(9)
        self.inventory_table.setHorizontalHeaderLabels([
            "المعرف", "الباركود", "اسم المنتج", "الفئة",
            "الوحدة", "الكمية الحالية", "الحد الأدنى",
            "سعر البيع", "حالة المخزون"
        ])
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inventory_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.inventory_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #ecf0f1;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                font-weight: bold;
                padding: 6px;
            }
        """)
        layout.addWidget(self.inventory_table)
        
        # تحميل البيانات الأولية
        self.load_inventory_filters()
        self.refresh_inventory_data()
        
        return tab
    
    def create_sales_tab(self) -> QWidget:
        """إنشاء تبويب المبيعات"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("إدارة المبيعات")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c; margin: 10px;")
        layout.addWidget(title)
        
        buttons_layout = QHBoxLayout()
        
        new_sale_btn = QPushButton("🛒 فاتورة جديدة")
        new_sale_btn.setMinimumHeight(40)
        new_sale_btn.clicked.connect(self.new_sale)
        buttons_layout.addWidget(new_sale_btn)
        
        pos_btn = QPushButton("💳 نقطة البيع")
        pos_btn.setMinimumHeight(40)
        pos_btn.clicked.connect(self.open_pos)
        buttons_layout.addWidget(pos_btn)
        
        sales_report_btn = QPushButton("📈 تقرير المبيعات")
        sales_report_btn.setMinimumHeight(40)
        sales_report_btn.clicked.connect(self.sales_report)
        buttons_layout.addWidget(sales_report_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        content_label = QLabel("سيتم إضافة جدول المبيعات والفواتير هنا")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("color: #7f8c8d; font-size: 14px; margin: 50px;")
        layout.addWidget(content_label)
        
        layout.addStretch()
        return tab
    
    # ===== إدارة المخزون =====
    def load_inventory_filters(self):
        """تحميل قائمة الفئات في مرشحات المخزون"""
        if not hasattr(self, "inventory_category_combo"):
            return
        
        try:
            self.inventory_category_combo.blockSignals(True)
            self.inventory_category_combo.clear()
            self.inventory_category_combo.addItem("جميع الفئات", None)
            
            if getattr(self, "inventory_service", None):
                try:
                    # محاولة استخدام category_manager إذا كان موجوداً
                    categories = self.inventory_service.category_manager.get_all_categories()
                    for category in categories:
                        if getattr(category, 'is_active', True):
                            self.inventory_category_combo.addItem(category.name, category.id)
                except (AttributeError, TypeError):
                    # إذا فشل، حاول طلب الفئات مباشرة من قاعدة البيانات
                    pass
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل مرشحات الفئات: {str(e)}")
        finally:
            self.inventory_category_combo.blockSignals(False)
    
    def on_inventory_filters_changed(self):
        """التعامل مع تغيير مرشحات المخزون"""
        self.refresh_inventory_data()
    
    def refresh_inventory_data(self):
        """تحديث بيانات جدول المخزون"""
        if not hasattr(self, "inventory_table"):
            return
        if not getattr(self, "inventory_service", None):
            self.inventory_table.setRowCount(0)
            return
        
        try:
            search_term = self.inventory_search_input.text().strip() if hasattr(self, "inventory_search_input") else ""
            category_id = self.inventory_category_combo.currentData() if hasattr(self, "inventory_category_combo") else None
            if category_id is None:
                category_id = None
            
            # Cache مفتاح لنتائج البحث
            cache_key = None
            if getattr(self, 'cache', None):
                cache_key = f"ui:inventory:search:{search_term}|{category_id}"
                products = self.cache.get(cache_key)
            else:
                products = None

            if products is None:
                # محاولة استخدام product_manager أو ProductService حسب ما هو متاح
                try:
                    products = self.inventory_service.product_manager.search_products(
                        search_term=search_term,
                        category_id=category_id
                    )
                except AttributeError:
                    # إذا لم يكن product_manager موجوداً، استخدم ProductService
                    from src.services.product_service_enhanced import ProductService
                    ps = ProductService(self.db_manager, self.logger)
                    products = ps.search_products(
                        search_term=search_term,
                        category_id=category_id,
                        active_only=True
                    )
                if getattr(self, 'cache', None) and cache_key:
                    self.cache.set(cache_key, products, ttl=30)
            
            self.inventory_table.setRowCount(len(products))
            
            for row_index, product in enumerate(products):
                row_data = [
                    str(product.id or ""),
                    product.barcode or "-",
                    product.name or "-",
                    product.category_name or "-",
                    product.unit or "-",
                    str(product.current_stock),
                    str(product.min_stock),
                    f"{float(product.selling_price):,.2f}",
                    ""
                ]
                
                status_text = "جيد"
                status_color = QColor("#27ae60")
                
                if product.current_stock == 0:
                    status_text = "نفد من المخزون"
                    status_color = QColor("#e74c3c")
                elif product.current_stock <= product.min_stock:
                    status_text = "مخزون منخفض"
                    status_color = QColor("#f39c12")
                
                row_data[-1] = status_text
                
                for col_index, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    if col_index in (0, 5, 6, 7):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    
                    if col_index == 0:
                        item.setData(Qt.UserRole, product.id)
                    
                    if col_index == len(row_data) - 1:
                        item.setForeground(status_color)
                    
                    self.inventory_table.setItem(row_index, col_index, item)
                
                self.inventory_table.setRowHeight(row_index, 40)
            
            # تحديث الملخص مع التخزين المؤقت
            report_filters = {"search": search_term or "", "category_id": category_id}
            if getattr(self, 'cache', None):
                cached_report = self.cache.get_cached_report("inventory_summary", report_filters)
            else:
                cached_report = None
            if cached_report is not None:
                report = cached_report
            else:
                report = self.inventory_service.generate_inventory_report()
                if getattr(self, 'cache', None):
                    self.cache.cache_report("inventory_summary", report_filters, report, ttl=60)
            self.update_inventory_summary(report)
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث بيانات المخزون: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات المخزون:\n{str(e)}")
    
    def update_inventory_summary(self, report):
        """تحديث ملخص المخزون"""
        if not hasattr(self, "inventory_summary_labels"):
            return
        
        try:
            def set_label(key, value):
                label = self.inventory_summary_labels.get(key)
                if label:
                    label.setText(value)
            
            set_label("total_products", f"{getattr(report, 'total_products', 0):,}")
            set_label("total_categories", f"{getattr(report, 'total_categories', 0):,}")
            set_label(
                "total_stock_value",
                f"{getattr(report, 'total_stock_value', 0):,.2f} ريال"
            )
            set_label("low_stock_items", f"{getattr(report, 'low_stock_items', 0):,}")
            set_label("out_of_stock_items", f"{getattr(report, 'out_of_stock_items', 0):,}")
            set_label("expired_items", f"{getattr(report, 'expired_items', 0):,}")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث ملخص المخزون: {str(e)}")
    
    # ===== إدارة العملاء والموردين =====
    def refresh_contacts_data(self):
        """تحديث بيانات تبويب العملاء والموردين"""
        if not hasattr(self, "contacts_tab_widget"):
            return
        
        current_index = self.contacts_tab_widget.currentIndex()
        if current_index == 0:
            self.refresh_customers_data()
        else:
            self.refresh_suppliers_data()
    
    def refresh_customers_data(self):
        """تحديث جدول العملاء"""
        if not hasattr(self, "customers_table"):
            return
        
        if not getattr(self, "customer_manager", None):
            self.customers_table.setRowCount(0)
            self.customers_summary_label.setText("تعذر تحميل بيانات العملاء (قاعدة البيانات غير متصلة).")
            return
        
        try:
            search_term = self.contacts_search_input.text().strip() if hasattr(self, "contacts_search_input") else ""
            # Cache نتائج العملاء
            cache_key = None
            if getattr(self, 'cache', None):
                cache_key = f"ui:customers:search:{search_term}"
                customers = self.cache.get(cache_key)
            else:
                customers = None
            if customers is None:
                customers = self.customer_manager.search_customers(search_term=search_term, active_only=True)
                if getattr(self, 'cache', None) and cache_key:
                    self.cache.set(cache_key, customers, ttl=45)
            
            self.customers_table.setRowCount(len(customers))
            for row_index, customer in enumerate(customers):
                row_data = [
                    str(customer.id or ""),
                    customer.name or "-",
                    customer.phone or customer.phone2 or "-",
                    customer.email or "-",
                    customer.city or "-",
                    f"{float(customer.current_balance):,.2f}",
                    f"{float(customer.credit_limit):,.2f}",
                    customer.last_purchase_date.isoformat() if customer.last_purchase_date else "-",
                    str(customer.purchases_count or 0)
                ]
                
                for col_index, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    if col_index in (0, 5, 6, 8):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.customers_table.setItem(row_index, col_index, item)
                
                # إضافة أزرار الإجراءات
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 0, 4, 0)
                actions_layout.setSpacing(4)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.setMaximumWidth(60)
                edit_btn.setMinimumHeight(28)
                edit_btn.clicked.connect(lambda checked, cid=customer.id: self.edit_customer(cid))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("حذف")
                delete_btn.setMaximumWidth(50)
                delete_btn.setMinimumHeight(28)
                delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                delete_btn.clicked.connect(lambda checked, cid=customer.id: self.delete_customer(cid))
                actions_layout.addWidget(delete_btn)
                
                actions_layout.addStretch()
                self.customers_table.setCellWidget(row_index, 9, actions_widget)
                
                self.customers_table.setRowHeight(row_index, 36)
            
            self.update_customers_summary()
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث بيانات العملاء: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات العملاء:\n{str(e)}")
    
    def update_customers_summary(self):
        """تحديث ملخص العملاء"""
        if not getattr(self, "customer_manager", None):
            return
        
        try:
            report = self.customer_manager.get_customers_report()
            summary_text = (
                f"إجمالي العملاء: {report.get('total_customers', 0):,} | "
                f"العملاء النشطون: {report.get('active_customers', 0):,} | "
                f"عملاء لديهم رصيد مستحق: {report.get('customers_with_balance', 0):,} | "
                f"إجمالي الأرصدة المستحقة: {report.get('total_outstanding_balance', 0):,.2f} ريال"
            )
            self.customers_summary_label.setText(summary_text)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث ملخص العملاء: {str(e)}")
    
    def refresh_suppliers_data(self):
        """تحديث جدول الموردين"""
        if not hasattr(self, "suppliers_table"):
            return
        
        if not getattr(self, "supplier_manager", None):
            self.suppliers_table.setRowCount(0)
            self.suppliers_summary_label.setText("تعذر تحميل بيانات الموردين (قاعدة البيانات غير متصلة).")
            return
        
        try:
            search_term = self.contacts_search_input.text().strip() if hasattr(self, "contacts_search_input") else ""
            # Cache نتائج الموردين
            cache_key = None
            if getattr(self, 'cache', None):
                cache_key = f"ui:suppliers:search:{search_term}"
                suppliers = self.cache.get(cache_key)
            else:
                suppliers = None
            if suppliers is None:
                suppliers = self.supplier_manager.search_suppliers(search_term=search_term, active_only=True)
                if getattr(self, 'cache', None) and cache_key:
                    self.cache.set(cache_key, suppliers, ttl=45)
            
            self.suppliers_table.setRowCount(len(suppliers))
            for row_index, supplier in enumerate(suppliers):
                row_data = [
                    str(supplier.id or ""),
                    supplier.name or "-",
                    supplier.contact_person or "-",
                    supplier.phone or supplier.phone2 or "-",
                    supplier.city or "-",
                    f"{float(supplier.current_balance):,.2f}",
                    f"{float(supplier.credit_limit):,.2f}",
                    supplier.last_purchase_date.isoformat() if supplier.last_purchase_date else "-",
                    str(supplier.purchases_count or 0)
                ]
                
                for col_index, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    if col_index in (0, 5, 6, 8):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.suppliers_table.setItem(row_index, col_index, item)
                
                # إضافة أزرار الإجراءات
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 0, 4, 0)
                actions_layout.setSpacing(4)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.setMaximumWidth(60)
                edit_btn.setMinimumHeight(28)
                edit_btn.clicked.connect(lambda checked, sid=supplier.id: self.edit_supplier(sid))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("حذف")
                delete_btn.setMaximumWidth(50)
                delete_btn.setMinimumHeight(28)
                delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                delete_btn.clicked.connect(lambda checked, sid=supplier.id: self.delete_supplier(sid))
                actions_layout.addWidget(delete_btn)
                
                actions_layout.addStretch()
                self.suppliers_table.setCellWidget(row_index, 9, actions_widget)
                
                self.suppliers_table.setRowHeight(row_index, 36)
            
            self.update_suppliers_summary()
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث بيانات الموردين: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات الموردين:\n{str(e)}")
    
    def update_suppliers_summary(self):
        """تحديث ملخص الموردين"""
        if not getattr(self, "supplier_manager", None):
            return
        
        try:
            report = self.supplier_manager.get_suppliers_report()
            summary_text = (
                f"إجمالي الموردين: {report.get('total_suppliers', 0):,} | "
                f"الموردون النشطون: {report.get('active_suppliers', 0):,} | "
                f"موردون لديهم رصيد مستحق: {report.get('suppliers_with_balance', 0):,} | "
                f"إجمالي الأرصدة المستحقة: {report.get('total_outstanding_balance', 0):,.2f} ريال"
            )
            self.suppliers_summary_label.setText(summary_text)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث ملخص الموردين: {str(e)}")
    
    # ===== عمليات إدارة العملاء والموردين =====
    def add_customer(self):
        """إضافة عميل جديد"""
        try:
            from src.ui.dialogs.customer_form_dialog import CustomerFormDialog
            dialog = CustomerFormDialog(self.db_manager, logger=self.logger, parent=self)
            if dialog.exec():
                self.refresh_contacts_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إضافة عميل: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إضافة عميل:\n{str(e)}")
    
    def add_supplier(self):
        """إضافة مورد جديد"""
        try:
            from src.ui.dialogs.supplier_form_dialog import SupplierFormDialog
            dialog = SupplierFormDialog(self.db_manager, logger=self.logger, parent=self)
            if dialog.exec():
                self.refresh_contacts_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إضافة مورد: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إضافة مورد:\n{str(e)}")
    
    def edit_customer(self, customer_id):
        """تعديل عميل"""
        try:
            from src.ui.dialogs.customer_form_dialog import CustomerFormDialog
            dialog = CustomerFormDialog(self.db_manager, customer_id=customer_id, logger=self.logger, parent=self)
            if dialog.exec():
                self.refresh_contacts_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة تعديل عميل: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تعديل عميل:\n{str(e)}")
    
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
                self.refresh_contacts_data()
                QMessageBox.information(self, "نجاح", "تم حذف العميل بنجاح")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"خطأ في حذف العميل: {str(e)}")
                QMessageBox.critical(self, "خطأ", f"فشل في حذف العميل: {str(e)}")
    
    def edit_supplier(self, supplier_id):
        """تعديل مورد"""
        try:
            from src.ui.dialogs.supplier_form_dialog import SupplierFormDialog
            dialog = SupplierFormDialog(self.db_manager, supplier_id=supplier_id, logger=self.logger, parent=self)
            if dialog.exec():
                self.refresh_contacts_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة تعديل مورد: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تعديل مورد:\n{str(e)}")
    
    def delete_supplier(self, supplier_id):
        """حذف مورد"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل تريد حذف هذا المورد؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.execute_query("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
                self.refresh_contacts_data()
                QMessageBox.information(self, "نجاح", "تم حذف المورد بنجاح")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"خطأ في حذف المورد: {str(e)}")
                QMessageBox.critical(self, "خطأ", f"فشل في حذف المورد: {str(e)}")
    
    def contacts_report(self):
        """عرض تقارير العملاء والموردين"""
        try:
            from src.ui.dialogs.contacts_report_dialog import ContactsReportDialog
            dialog = ContactsReportDialog(self.db_manager, logger=self.logger, parent=self)
            dialog.exec()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة التقارير: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة التقارير:\n{str(e)}")
    
    def refresh_data(self):
        """تحديث البيانات في الواجهة"""
        self.refresh_inventory_data()
        self.refresh_contacts_data()
    
    def create_purchases_tab(self) -> QWidget:
        """إنشاء تبويب المشتريات"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("إدارة المشتريات")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; margin: 10px;")
        layout.addWidget(title)
        
        buttons_layout = QHBoxLayout()
        
        new_purchase_btn = QPushButton("📥 فاتورة شراء جديدة")
        new_purchase_btn.setMinimumHeight(40)
        new_purchase_btn.clicked.connect(self.new_purchase)
        buttons_layout.addWidget(new_purchase_btn)
        
        manage_suppliers_btn = QPushButton("🏢 إدارة الموردين")
        manage_suppliers_btn.setMinimumHeight(40)
        manage_suppliers_btn.clicked.connect(self.manage_suppliers)
        buttons_layout.addWidget(manage_suppliers_btn)
        
        purchases_report_btn = QPushButton("📊 تقرير المشتريات")
        purchases_report_btn.setMinimumHeight(40)
        purchases_report_btn.clicked.connect(self.purchases_report)
        buttons_layout.addWidget(purchases_report_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        content_label = QLabel("سيتم إضافة جدول المشتريات والموردين هنا")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("color: #7f8c8d; font-size: 14px; margin: 50px;")
        layout.addWidget(content_label)
        
        layout.addStretch()
        return tab
    
    def create_reports_tab(self) -> QWidget:
        """إنشاء تبويب التقارير"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("التقارير والإحصائيات")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        buttons_layout = QHBoxLayout()
        
        daily_report_btn = QPushButton("📅 تقرير يومي")
        daily_report_btn.setMinimumHeight(40)
        daily_report_btn.clicked.connect(self.daily_report)
        buttons_layout.addWidget(daily_report_btn)
        
        monthly_report_btn = QPushButton("📆 تقرير شهري")
        monthly_report_btn.setMinimumHeight(40)
        monthly_report_btn.clicked.connect(self.monthly_report)
        buttons_layout.addWidget(monthly_report_btn)
        
        profit_report_btn = QPushButton("💹 تقرير الأرباح")
        profit_report_btn.setMinimumHeight(40)
        profit_report_btn.clicked.connect(self.profit_report)
        buttons_layout.addWidget(profit_report_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        content_label = QLabel("سيتم إضافة لوحة التقارير والرسوم البيانية هنا")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("color: #7f8c8d; font-size: 14px; margin: 50px;")
        layout.addWidget(content_label)
        
        layout.addStretch()
        return tab
    
    def create_contacts_tab(self) -> QWidget:
        """إنشاء تبويب العملاء والموردين"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        title = QLabel("إدارة العملاء والموردين")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f39c12; margin-bottom: 4px;")
        layout.addWidget(title)
        
        # أزرار سريعة
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        add_customer_btn = QPushButton("👤 إضافة عميل")
        add_customer_btn.setMinimumHeight(36)
        add_customer_btn.clicked.connect(self.add_customer)
        buttons_layout.addWidget(add_customer_btn)
        
        add_supplier_btn = QPushButton("🏭 إضافة مورد")
        add_supplier_btn.setMinimumHeight(36)
        add_supplier_btn.clicked.connect(self.add_supplier)
        buttons_layout.addWidget(add_supplier_btn)
        
        contacts_report_btn = QPushButton("📇 تقارير العملاء والموردين")
        contacts_report_btn.setMinimumHeight(36)
        contacts_report_btn.clicked.connect(self.contacts_report)
        buttons_layout.addWidget(contacts_report_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # منطقة البحث
        contacts_filters_frame = QFrame()
        contacts_filters_frame.setObjectName("contactsFiltersFrame")
        contacts_filters_frame.setStyleSheet("""
            QFrame#contactsFiltersFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e4e7;
                border-radius: 6px;
            }
        """)
        contacts_filters_layout = QHBoxLayout(contacts_filters_frame)
        contacts_filters_layout.setContentsMargins(12, 8, 12, 8)
        contacts_filters_layout.setSpacing(12)
        
        search_label = QLabel("بحث:")
        search_label.setStyleSheet("color: #34495e; font-weight: 600;")
        contacts_filters_layout.addWidget(search_label)
        
        self.contacts_search_input = QLineEdit()
        self.contacts_search_input.setPlaceholderText("ابحث بالاسم أو الهاتف أو البريد الإلكتروني...")
        self.contacts_search_input.textChanged.connect(self.refresh_contacts_data)
        contacts_filters_layout.addWidget(self.contacts_search_input, 2)
        
        self.contacts_refresh_btn = QPushButton("🔄 تحديث")
        self.contacts_refresh_btn.setMinimumHeight(32)
        self.contacts_refresh_btn.clicked.connect(self.refresh_contacts_data)
        contacts_filters_layout.addWidget(self.contacts_refresh_btn)
        
        layout.addWidget(contacts_filters_frame)
        
        # تبويبات العملاء والموردين
        self.contacts_tab_widget = QTabWidget()
        self.contacts_tab_widget.currentChanged.connect(self.refresh_contacts_data)
        
        # تبويب العملاء
        customers_tab = QWidget()
        customers_layout = QVBoxLayout(customers_tab)
        customers_layout.setSpacing(10)
        customers_layout.setContentsMargins(0, 0, 0, 0)
        
        customers_summary_group = QGroupBox("ملخص العملاء")
        customers_summary_layout = QVBoxLayout(customers_summary_group)
        customers_summary_layout.setContentsMargins(12, 12, 12, 12)
        self.customers_summary_label = QLabel("-")
        self.customers_summary_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
        customers_summary_layout.addWidget(self.customers_summary_label)
        customers_layout.addWidget(customers_summary_group)
        
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(10)
        self.customers_table.setHorizontalHeaderLabels([
            "المعرف", "الاسم", "الهاتف", "البريد الإلكتروني",
            "المدينة", "الرصيد الحالي", "الحد الائتماني",
            "آخر شراء", "عدد الفواتير", "الإجراءات"
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        customers_layout.addWidget(self.customers_table)
        
        self.contacts_tab_widget.addTab(customers_tab, "👥 العملاء")
        
        # تبويب الموردين
        suppliers_tab = QWidget()
        suppliers_layout = QVBoxLayout(suppliers_tab)
        suppliers_layout.setSpacing(10)
        suppliers_layout.setContentsMargins(0, 0, 0, 0)
        
        suppliers_summary_group = QGroupBox("ملخص الموردين")
        suppliers_summary_layout = QVBoxLayout(suppliers_summary_group)
        suppliers_summary_layout.setContentsMargins(12, 12, 12, 12)
        self.suppliers_summary_label = QLabel("-")
        self.suppliers_summary_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
        suppliers_summary_layout.addWidget(self.suppliers_summary_label)
        suppliers_layout.addWidget(suppliers_summary_group)
        
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(10)
        self.suppliers_table.setHorizontalHeaderLabels([
            "المعرف", "الاسم", "مسؤول الاتصال", "الهاتف",
            "المدينة", "الرصيد الحالي", "الحد الائتماني",
            "آخر شراء", "عدد فواتير الشراء", "الإجراءات"
        ])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.suppliers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        suppliers_layout.addWidget(self.suppliers_table)
        
        self.contacts_tab_widget.addTab(suppliers_tab, "🏭 الموردون")
        
        layout.addWidget(self.contacts_tab_widget)
        
        # تحميل البيانات الأولية
        self.refresh_contacts_data()
        
        return tab
    
    def create_settings_tab(self) -> QWidget:
        """إنشاء تبويب الإعدادات"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("إعدادات النظام")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e; margin: 10px;")
        layout.addWidget(title)
        
        buttons_layout = QHBoxLayout()
        
        general_settings_btn = QPushButton("⚙️ الإعدادات العامة")
        general_settings_btn.setMinimumHeight(40)
        buttons_layout.addWidget(general_settings_btn)
        
        backup_btn = QPushButton("💾 النسخ الاحتياطي")
        backup_btn.setMinimumHeight(40)
        backup_btn.clicked.connect(self.backup_database)
        buttons_layout.addWidget(backup_btn)
        
        users_btn = QPushButton("👥 إدارة المستخدمين")
        users_btn.setMinimumHeight(40)
        buttons_layout.addWidget(users_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        content_label = QLabel("سيتم إضافة لوحة الإعدادات هنا")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("color: #7f8c8d; font-size: 14px; margin: 50px;")
        layout.addWidget(content_label)
        
        layout.addStretch()
        return tab
    
    def setup_menus(self):
        """إعداد القوائم"""
        menubar = self.menuBar()
        
        # قائمة ملف
        file_menu = menubar.addMenu("ملف")
        
        new_action = QAction("جديد", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        backup_action = QAction("نسخة احتياطية", self)
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)

        backup_enc_action = QAction("نسخة احتياطية مشفرة…", self)
        backup_enc_action.setToolTip("إنشاء نسخة احتياطية مشفرة (AES-256-GCM)")
        backup_enc_action.triggered.connect(self.backup_database_encrypted_action)
        file_menu.addAction(backup_enc_action)

        restore_enc_action = QAction("استعادة نسخة مشفرة…", self)
        restore_enc_action.setToolTip("استعادة قاعدة البيانات من نسخة احتياطية مشفرة")
        restore_enc_action.triggered.connect(self.restore_database_encrypted_action)
        file_menu.addAction(restore_enc_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("خروج", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # قائمة عرض
        view_menu = menubar.addMenu("عرض")
        
        # قائمة أدوات
        tools_menu = menubar.addMenu("أدوات")
        
        # إضافة عنصر البحث المتقدم
        search_action = QAction("🔍 البحث المتقدم", self)
        search_action.setShortcut("Ctrl+F")
        search_action.setToolTip("البحث المتقدم في جميع بيانات النظام")
        search_action.triggered.connect(self.show_advanced_search_window)
        tools_menu.addAction(search_action)
        
        tools_menu.addSeparator()
        
        # إضافة عنصر إدارة التشفير
        encryption_action = QAction("🔒 إدارة التشفير", self)
        encryption_action.triggered.connect(self.show_encryption_dialog)
        tools_menu.addAction(encryption_action)
        
        # قائمة المدفوعات والحسابات
        payments_menu = menubar.addMenu("المدفوعات والحسابات")
        
        # لوحة تحكم المدفوعات
        dashboard_action = QAction("📊 لوحة تحكم المدفوعات", self)
        dashboard_action.triggered.connect(self.show_payment_dashboard)
        payments_menu.addAction(dashboard_action)
        
        payments_menu.addSeparator()
        
        # إضافة دفعة جديدة
        new_payment_action = QAction("💰 إضافة دفعة جديدة", self)
        new_payment_action.triggered.connect(self.show_payment_dialog)
        payments_menu.addAction(new_payment_action)
        
        payments_menu.addSeparator()
        
        # إدارة الحسابات المدينة والدائنة
        accounts_action = QAction("📊 إدارة الحسابات المدينة والدائنة", self)
        accounts_action.triggered.connect(self.show_accounts_window)
        payments_menu.addAction(accounts_action)
        
        payments_menu.addSeparator()
        
        # تقارير المدفوعات
        payment_reports_action = QAction("📈 تقارير المدفوعات", self)
        payment_reports_action.triggered.connect(self.show_payment_reports)
        payments_menu.addAction(payment_reports_action)

        # قائمة لوحات المعلومات العامة
        dashboards_menu = menubar.addMenu("لوحات المعلومات")
        open_dashboard_action = QAction("📊 لوحة المعلومات الرئيسية", self)
        open_dashboard_action.triggered.connect(self.show_main_dashboard)
        dashboards_menu.addAction(open_dashboard_action)

        # قائمة عروض الأسعار والمرتجعات
        quotes_menu = menubar.addMenu("عروض ومرتجعات")
        
        quotes_action = QAction("💼 عروض الأسعار", self)
        quotes_action.triggered.connect(self.show_quotes_window)
        quotes_menu.addAction(quotes_action)
        
        returns_action = QAction("↩️ المرتجعات", self)
        returns_action.triggered.connect(self.show_returns_window)
        quotes_menu.addAction(returns_action)

        # قائمة أوامر الشراء
        po_menu = menubar.addMenu("أوامر الشراء")
        
        po_action = QAction("📋 إدارة أوامر الشراء", self)
        po_action.triggered.connect(self.show_purchase_orders_window)
        po_menu.addAction(po_action)
        
        po_menu.addSeparator()
        
        receiving_action = QAction("📦 استلام الشحنات", self)
        receiving_action.triggered.connect(self.show_receiving_notes_window)
        po_menu.addAction(receiving_action)
        
        supplier_eval_action = QAction("⭐ تقييم الموردين", self)
        supplier_eval_action.triggered.connect(self.show_supplier_evaluations_window)
        po_menu.addAction(supplier_eval_action)

        # قائمة خطط الدفع والتقسيط
        payment_plans_menu = menubar.addMenu("خطط الدفع")
        
        payment_plans_action = QAction("💳 إدارة خطط الدفع", self)
        payment_plans_action.triggered.connect(self.show_payment_plans_window)
        payment_plans_menu.addAction(payment_plans_action)
        
        payment_plans_menu.addSeparator()
        
        upcoming_payments_action = QAction("📅 الأقساط القادمة", self)
        upcoming_payments_action.triggered.connect(self.show_upcoming_payments)
        payment_plans_menu.addAction(upcoming_payments_action)
        
        overdue_payments_action = QAction("⚠️ الأقساط المتأخرة", self)
        overdue_payments_action.triggered.connect(self.show_overdue_payments)
        payment_plans_menu.addAction(overdue_payments_action)

        # قائمة تحسين المخزون
        inventory_opt_menu = menubar.addMenu("تحسين المخزون")
        
        abc_analysis_action = QAction("📊 تحليل ABC", self)
        abc_analysis_action.setToolTip("تحليل ABC للمنتجات حسب القيمة")
        abc_analysis_action.triggered.connect(self.show_abc_analysis_window)
        inventory_opt_menu.addAction(abc_analysis_action)
        
        inventory_opt_menu.addSeparator()
        
        safety_stock_action = QAction("🛡️ الأرصدة الآمنة", self)
        safety_stock_action.setToolTip("إدارة الأرصدة الآمنة ونقاط إعادة الطلب")
        safety_stock_action.triggered.connect(self.show_safety_stock_window)
        inventory_opt_menu.addAction(safety_stock_action)
        
        batch_tracking_action = QAction("📦 تتبع الدفعات", self)
        batch_tracking_action.setToolTip("تتبع دفعات المنتجات وتواريخ الانتهاء")
        batch_tracking_action.triggered.connect(self.show_batch_tracking_window)
        inventory_opt_menu.addAction(batch_tracking_action)
        
        inventory_opt_menu.addSeparator()
        
        reorder_action = QAction("🔔 توصيات إعادة الطلب", self)
        reorder_action.setToolTip("توصيات ذكية لإعادة طلب المنتجات")
        reorder_action.triggered.connect(self.show_reorder_recommendations_window)
        inventory_opt_menu.addAction(reorder_action)
        
        inventory_opt_menu.addSeparator()
        
        physical_count_action = QAction("📋 الجرد الدوري", self)
        physical_count_action.setToolTip("إدارة الجرد الدوري للمخزون")
        physical_count_action.triggered.connect(self.show_physical_counts_window)
        inventory_opt_menu.addAction(physical_count_action)
        
        adjustments_action = QAction("⚖️ تسويات المخزون", self)
        adjustments_action.setToolTip("إدارة تسويات المخزون")
        adjustments_action.triggered.connect(self.show_stock_adjustments_window)
        inventory_opt_menu.addAction(adjustments_action)

        # قائمة التقارير
        reports_menu = menubar.addMenu("📊 التقارير")
        
        advanced_reports_action = QAction("📊 التقارير المتقدمة", self)
        advanced_reports_action.setToolTip("نظام التقارير المتقدمة الشامل")
        advanced_reports_action.triggered.connect(self.show_advanced_reports_window)
        reports_menu.addAction(advanced_reports_action)
        
        reports_menu.addSeparator()
        
        sales_reports_action = QAction("📈 تقارير المبيعات", self)
        sales_reports_action.setToolTip("تقارير المبيعات التفصيلية")
        sales_reports_action.triggered.connect(lambda: self.show_advanced_reports_window("sales"))
        reports_menu.addAction(sales_reports_action)
        
        inventory_reports_action = QAction("📦 تقارير المخزون", self)
        inventory_reports_action.setToolTip("تقارير المخزون والحركة")
        inventory_reports_action.triggered.connect(lambda: self.show_advanced_reports_window("inventory"))
        reports_menu.addAction(inventory_reports_action)
        
        financial_reports_action = QAction("💰 التقارير المالية", self)
        financial_reports_action.setToolTip("التقارير المحاسبية والمالية")
        financial_reports_action.triggered.connect(lambda: self.show_advanced_reports_window("financial"))
        reports_menu.addAction(financial_reports_action)

        # قائمة المحاسبة
        accounting_menu = menubar.addMenu("المحاسبة")
        open_accounting_action = QAction("📚 إدارة المحاسبة", self)
        open_accounting_action.triggered.connect(self.show_accounting_window)
        accounting_menu.addAction(open_accounting_action)
        
        # قائمة مساعدة
        help_menu = menubar.addMenu("مساعدة")
        
        about_action = QAction("حول البرنامج", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_accounting_window(self):
        """عرض نافذة إدارة المحاسبة"""
        try:
            from .accounting_window import AccountingWindow
            # احتفظ بالمرجع حتى لا تُجمّع
            if not hasattr(self, "_accounting_window") or self._accounting_window is None:
                self._accounting_window = AccountingWindow(self.db_manager, parent=self)
            self._accounting_window.show()
            self._accounting_window.raise_()
            self._accounting_window.activateWindow()
            if self.logger:
                self.logger.info("تم فتح نافذة إدارة المحاسبة")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة المحاسبة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة المحاسبة:\n{str(e)}")
    
    def show_quotes_window(self):
        """عرض نافذة إدارة عروض الأسعار"""
        try:
            from .quotes_window import QuotesWindow
            if not hasattr(self, "_quotes_window") or self._quotes_window is None:
                self._quotes_window = QuotesWindow(self.db_manager, parent=self)
            self._quotes_window.show()
            self._quotes_window.raise_()
            self._quotes_window.activateWindow()
            if self.logger:
                self.logger.info("تم فتح نافذة إدارة عروض الأسعار")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة عروض الأسعار: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة عروض الأسعار:\n{str(e)}")
    
    def show_returns_window(self):
        """عرض نافذة إدارة المرتجعات"""
        try:
            from .returns_window import ReturnsWindow
            if not hasattr(self, "_returns_window") or self._returns_window is None:
                self._returns_window = ReturnsWindow(self.db_manager, parent=self)
            self._returns_window.show()
            self._returns_window.raise_()
            self._returns_window.activateWindow()
            if self.logger:
                self.logger.info("تم فتح نافذة إدارة المرتجعات")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة المرتجعات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة المرتجعات:\n{str(e)}")
    
    def show_purchase_orders_window(self):
        """عرض نافذة أوامر الشراء"""
        try:
            from .purchase_orders_window import PurchaseOrdersWindow
            if not hasattr(self, "_purchase_orders_window") or self._purchase_orders_window is None:
                self._purchase_orders_window = PurchaseOrdersWindow(self.db_manager, parent=self)
            self._purchase_orders_window.show()
            self._purchase_orders_window.raise_()
            self._purchase_orders_window.activateWindow()
            if self.logger:
                self.logger.info("تم فتح نافذة أوامر الشراء")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة أوامر الشراء: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة أوامر الشراء:\n{str(e)}")
    
    def show_receiving_notes_window(self):
        """عرض نافذة استلام الشحنات"""
        try:
            # يمكن إضافة نافذة منفصلة للاستلام أو استخدام نفس نافذة أوامر الشراء
            self.show_purchase_orders_window()
            if self.logger:
                self.logger.info("تم فتح نافذة استلام الشحنات")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة استلام الشحنات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة استلام الشحنات:\n{str(e)}")
    
    def show_supplier_evaluations_window(self):
        """عرض نافذة تقييم الموردين"""
        try:
            # يمكن إضافة نافذة منفصلة للتقييم
            QMessageBox.information(self, "قريباً", "سيتم إضافة نافذة تقييم الموردين قريباً")
            if self.logger:
                self.logger.info("طلب فتح نافذة تقييم الموردين")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة تقييم الموردين: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تقييم الموردين:\n{str(e)}")
    
    def show_payment_plans_window(self):
        """عرض نافذة إدارة خطط الدفع"""
        try:
            from .payment_plans_window import PaymentPlansWindow
            
            window = PaymentPlansWindow(self.db_manager, parent=self)
            window.show()
            
            if self.logger:
                self.logger.info("فتح نافذة إدارة خطط الدفع")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة خطط الدفع: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة خطط الدفع:\n{str(e)}")
    
    def show_upcoming_payments(self):
        """عرض الأقساط القادمة"""
        try:
            from .payment_plans_window import PaymentPlansWindow
            
            window = PaymentPlansWindow(self.db_manager, parent=self)
            window.tabs.setCurrentIndex(1)  # تبويب الأقساط القادمة
            window.show()
            
            if self.logger:
                self.logger.info("عرض الأقساط القادمة")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في عرض الأقساط القادمة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في عرض الأقساط القادمة:\n{str(e)}")
    
    def show_overdue_payments(self):
        """عرض الأقساط المتأخرة"""
        try:
            from .payment_plans_window import PaymentPlansWindow
            
            window = PaymentPlansWindow(self.db_manager, parent=self)
            window.tabs.setCurrentIndex(2)  # تبويب الأقساط المتأخرة
            window.show()
            
            if self.logger:
                self.logger.info("عرض الأقساط المتأخرة")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في عرض الأقساط المتأخرة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في عرض الأقساط المتأخرة:\n{str(e)}")
    
    def show_abc_analysis_window(self):
        """عرض نافذة تحليل ABC"""
        try:
            from .abc_analysis_window import ABCAnalysisWindow
        
            if not hasattr(self, "_abc_analysis_window") or self._abc_analysis_window is None:
                self._abc_analysis_window = ABCAnalysisWindow(self.db_manager, parent=self)
        
            self._abc_analysis_window.show()
            self._abc_analysis_window.raise_()
            self._abc_analysis_window.activateWindow()
        
            if self.logger:
                self.logger.info("تم فتح نافذة تحليل ABC")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة تحليل ABC: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تحليل ABC:\n{str(e)}")
    
    def show_safety_stock_window(self):
        """عرض نافذة إدارة الأرصدة الآمنة"""
        try:
            from .safety_stock_window import SafetyStockWindow
        
            if not hasattr(self, "_safety_stock_window") or self._safety_stock_window is None:
                self._safety_stock_window = SafetyStockWindow(self.db_manager, parent=self)
        
            self._safety_stock_window.show()
            self._safety_stock_window.raise_()
            self._safety_stock_window.activateWindow()
        
            if self.logger:
                self.logger.info("تم فتح نافذة الأرصدة الآمنة")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة الأرصدة الآمنة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة الأرصدة الآمنة:\n{str(e)}")
    
    def show_batch_tracking_window(self):
        """عرض نافذة تتبع الدفعات"""
        try:
            from .batch_tracking_window import BatchTrackingWindow
        
            if not hasattr(self, "_batch_tracking_window") or self._batch_tracking_window is None:
                self._batch_tracking_window = BatchTrackingWindow(self.db_manager, parent=self)
        
            self._batch_tracking_window.show()
            self._batch_tracking_window.raise_()
            self._batch_tracking_window.activateWindow()
        
            if self.logger:
                self.logger.info("تم فتح نافذة تتبع الدفعات")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة تتبع الدفعات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تتبع الدفعات:\n{str(e)}")
    
    def show_reorder_recommendations_window(self):
        """عرض نافذة توصيات إعادة الطلب"""
        try:
            from .reorder_recommendations_window import ReorderRecommendationsWindow
        
            if not hasattr(self, "_reorder_window") or self._reorder_window is None:
                self._reorder_window = ReorderRecommendationsWindow(self.db_manager, parent=self)
        
            self._reorder_window.show()
            self._reorder_window.raise_()
            self._reorder_window.activateWindow()
        
            if self.logger:
                self.logger.info("تم فتح نافذة توصيات إعادة الطلب")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة توصيات إعادة الطلب: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة توصيات إعادة الطلب:\n{str(e)}")
    
    def show_physical_counts_window(self):
        """عرض نافذة الجرد الدوري"""
        try:
            from .physical_counts_window import PhysicalCountsWindow
            
            if not hasattr(self, "_physical_counts_window") or self._physical_counts_window is None:
                self._physical_counts_window = PhysicalCountsWindow(self.db_manager, parent=self)
            
            self._physical_counts_window.show()
            self._physical_counts_window.raise_()
            self._physical_counts_window.activateWindow()
            
            if self.logger:
                self.logger.info("تم فتح نافذة الجرد الدوري")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة الجرد الدوري: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة الجرد الدوري:\n{str(e)}")
    
    def show_stock_adjustments_window(self):
        """عرض نافذة تسويات المخزون"""
        try:
            from .stock_adjustments_window import StockAdjustmentsWindow
            
            if not hasattr(self, "_adjustments_window") or self._adjustments_window is None:
                self._adjustments_window = StockAdjustmentsWindow(self.db_manager, parent=self)
            
            self._adjustments_window.show()
            self._adjustments_window.raise_()
            self._adjustments_window.activateWindow()
            
            if self.logger:
                self.logger.info("تم فتح نافذة تسويات المخزون")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة تسويات المخزون: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تسويات المخزون:\n{str(e)}")
    
    def show_advanced_reports_window(self, report_category=None):
        """عرض نافذة التقارير المتقدمة"""
        try:
            from .advanced_reports_window import AdvancedReportsWindow
            
            if not hasattr(self, "_advanced_reports_window") or self._advanced_reports_window is None:
                self._advanced_reports_window = AdvancedReportsWindow(self.db_manager, parent=self)
            
            # إذا تم تحديد فئة، قم بتحديدها في النافذة
            if report_category and hasattr(self._advanced_reports_window, 'set_report_category'):
                self._advanced_reports_window.set_report_category(report_category)
            
            self._advanced_reports_window.show()
            self._advanced_reports_window.raise_()
            self._advanced_reports_window.activateWindow()
            
            if self.logger:
                self.logger.info(f"تم فتح نافذة التقارير المتقدمة - الفئة: {report_category or 'الكل'}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة التقارير المتقدمة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة التقارير المتقدمة:\n{str(e)}")
    
    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        toolbar = self.addToolBar("الأدوات الرئيسية")
        toolbar.setMovable(False)
        
        # أزرار سريعة
        new_sale_action = QAction("فاتورة جديدة", self)
        new_sale_action.triggered.connect(self.new_sale)
        toolbar.addAction(new_sale_action)
        
        toolbar.addSeparator()
        
        backup_action = QAction("نسخة احتياطية", self)
        backup_action.triggered.connect(self.backup_database)
        toolbar.addAction(backup_action)

        backup_enc_action = QAction("نسخة احتياطية مشفرة", self)
        backup_enc_action.triggered.connect(self.backup_database_encrypted_action)
        toolbar.addAction(backup_enc_action)
    
    def setup_statusbar(self):
        """إعداد شريط الحالة"""
        statusbar = self.statusBar()
        
        # معلومات قاعدة البيانات
        if self.db_manager:
            db_info = self.db_manager.get_database_info()
            db_status = f"قاعدة البيانات: متصلة | الحجم: {db_info.get('size_mb', 0)} MB"
            statusbar.showMessage(db_status)
        else:
            statusbar.showMessage("جاهز")
    
    def apply_settings(self):
        """تطبيق الإعدادات"""
        if not self.config_manager:
            return
        
        ui_settings = self.config_manager.get_ui_settings()
        
        # تطبيق الخط
        font = QFont(ui_settings['font_family'], ui_settings['font_size'])
        self.setFont(font)
        
        # تطبيق الثيم (سيتم تطويره لاحقاً)
        if ui_settings['theme'] == 'dark':
            self.setStyleSheet("QMainWindow { background-color: #2c3e50; color: white; }")
    
    # دوال الأحداث
    def add_product(self):
        """إضافة منتج جديد"""
        try:
            from src.ui.dialogs.product_dialog import ProductDialog
            dialog = ProductDialog(self.db_manager, parent=self)
            
            # ربط إشارة حفظ المنتج
            dialog.product_saved.connect(self.on_product_saved)
            
            if dialog.exec() == QDialog.Accepted:
                self.logger.info("تم إضافة منتج جديد بنجاح")
                self.show_success_message("تم إضافة المنتج بنجاح")
                self.refresh_inventory_data()
        except Exception as e:
            self.logger.error(f"خطأ في فتح نافذة إضافة المنتج: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إضافة المنتج: {str(e)}")
    
    def on_product_saved(self, product):
        """معالجة حفظ المنتج"""
        try:
            self.logger.info(f"تم حفظ المنتج: {product.name}")
            # تحديث المخزون
            if hasattr(self, 'inventory_service') and hasattr(self.inventory_service, "refresh_cache"):
                self.inventory_service.refresh_cache()
            # إبطال cache لتغييرات البيانات
            if getattr(self, 'cache', None):
                self.cache.clear()
            self.refresh_inventory_data()
        except Exception as e:
            self.logger.error(f"خطأ في معالجة حفظ المنتج: {str(e)}")
    
    def show_success_message(self, message: str):
        """عرض رسالة نجاح"""
        self.statusBar().showMessage(message, 3000)  # عرض لمدة 3 ثوان
    
    def manage_categories(self):
        """إدارة الفئات"""
        try:
            from src.ui.dialogs.category_dialog import CategoryDialog
            dialog = CategoryDialog(self.db_manager, logger=self.logger, parent=self)
            dialog.exec()
            # تحديث قائمة الفئات بعد الإغلاق
            self.load_inventory_filters()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة الفئات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الفئات:\n{str(e)}")
    
    def inventory_report(self):
        """تقرير المخزون"""
        if not getattr(self, "inventory_service", None):
            QMessageBox.warning(self, "تقرير المخزون", "خدمة المخزون غير متاحة حالياً.")
            return
        
        try:
            report = self.inventory_service.generate_inventory_report()
            report_text = (
                "<h3>ملخص المخزون</h3>"
                f"<p>إجمالي المنتجات: <b>{report.total_products:,}</b></p>"
                f"<p>إجمالي الفئات: <b>{report.total_categories:,}</b></p>"
                f"<p>قيمة المخزون: <b>{report.total_stock_value:,.2f} ريال</b></p>"
                f"<p>منتجات ذات مخزون منخفض: <b>{report.low_stock_items:,}</b></p>"
                f"<p>منتجات نفدت من المخزون: <b>{report.out_of_stock_items:,}</b></p>"
            )
            QMessageBox.information(self, "تقرير المخزون", report_text)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير المخزون: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء تقرير المخزون:\n{str(e)}")
    
    def new_sale(self):
        """فاتورة مبيعات جديدة"""
        try:
            from src.ui.dialogs.sales_dialog import SalesDialog
            dialog = SalesDialog(self.db_manager, parent=self)
            
            # ربط إشارة إتمام البيع
            dialog.sale_completed.connect(self.on_sale_completed)
            
            if dialog.exec():
                if self.logger:
                    self.logger.info("تم إنشاء فاتورة مبيعات جديدة")
                self.show_success_message("تم إنشاء الفاتورة بنجاح")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة المبيعات: {str(e)}")
            QMessageBox.warning(self, "خطأ", f"فشل في فتح نافذة المبيعات: {str(e)}")
    
    def on_sale_completed(self, sale):
        """معالجة إتمام البيع"""
        try:
            if self.logger:
                self.logger.info(f"تم إتمام البيع رقم: {sale.id}")
            # تحديث المخزون والمبيعات
            if hasattr(self, 'inventory_service') and hasattr(self.inventory_service, "refresh_cache"):
                self.inventory_service.refresh_cache()
            if hasattr(self, 'sales_service') and hasattr(self.sales_service, "refresh_cache"):
                self.sales_service.refresh_cache()
            if getattr(self, 'cache', None):
                self.cache.clear()
            self.refresh_inventory_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في معالجة إتمام البيع: {str(e)}")
    
    def open_pos(self):
        """فتح نقطة البيع"""
        QMessageBox.information(self, "نقطة البيع", "سيتم فتح واجهة نقطة البيع")
    
    def sales_report(self):
        """تقرير المبيعات"""
        QMessageBox.information(self, "تقرير المبيعات", "سيتم إنشاء تقرير المبيعات")
    
    def new_purchase(self):
        """فاتورة شراء جديدة"""
        QMessageBox.information(self, "فاتورة شراء", "سيتم فتح نافذة فاتورة الشراء")
    
    def manage_suppliers(self):
        """إدارة الموردين"""
        try:
            from src.ui.dialogs.supplier_management_dialog import SupplierManagementDialog
            dialog = SupplierManagementDialog(self.db_manager, logger=self.logger, parent=self)
            dialog.exec()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة الموردين: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الموردين:\n{str(e)}")
    
    def purchases_report(self):
        """تقرير المشتريات"""
        QMessageBox.information(self, "تقرير المشتريات", "سيتم إنشاء تقرير المشتريات")
    
    def backup_database(self):
        """إنشاء نسخة احتياطية"""
        if self.db_manager:
            if self.db_manager.backup_database():
                QMessageBox.information(self, "نسخة احتياطية", "تم إنشاء النسخة الاحتياطية بنجاح")
                if self.logger:
                    self.logger.info("تم إنشاء نسخة احتياطية من قاعدة البيانات")
            else:
                QMessageBox.warning(self, "خطأ", "فشل في إنشاء النسخة الاحتياطية")
        else:
            QMessageBox.warning(self, "خطأ", "قاعدة البيانات غير متصلة")

    def backup_database_encrypted_action(self):
        """إنشاء نسخة احتياطية مشفرة بدون حظر الواجهة"""
        if not self.db_manager:
            QMessageBox.warning(self, "خطأ", "قاعدة البيانات غير متصلة")
            return
        self.statusBar().showMessage("جاري إنشاء النسخة الاحتياطية المشفرة…")
        if self.logger:
            self.logger.info("بدء إنشاء نسخة احتياطية مشفرة")
        # تمرير بعض البيانات الوصفية البسيطة
        metadata = {"initiated_by": "ui", "context": "manual"}
        self._backup_thread = self.BackupWorker(self.db_manager, mode='backup', logger=self.logger, metadata=metadata)
        self._backup_thread.finished.connect(self._on_encrypted_backup_finished)
        self._backup_thread.start()

    def _on_encrypted_backup_finished(self, success: bool, path: str):
        self.statusBar().clearMessage()
        if success:
            msg = "تم إنشاء النسخة الاحتياطية المشفرة بنجاح"
            if path:
                msg += f"\nالمسار: {path}"
            QMessageBox.information(self, "نسخة احتياطية مشفرة", msg)
            if self.logger:
                self.logger.info(f"تم إنشاء نسخة احتياطية مشفرة: {path}")
        else:
            QMessageBox.warning(self, "خطأ", "فشل في إنشاء النسخة الاحتياطية المشفرة")
            if self.logger:
                self.logger.warning("فشل إنشاء النسخة الاحتياطية المشفرة")

    def restore_database_encrypted_action(self):
        """استعادة نسخة احتياطية مشفرة بدون حظر الواجهة"""
        if not self.db_manager:
            QMessageBox.warning(self, "خطأ", "قاعدة البيانات غير متصلة")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "اختر ملف النسخة المشفرة", str(Path.home()), "Encrypted Backups (*.encrypted);;All Files (*)")
        if not file_path:
            return
        self.statusBar().showMessage("جاري استعادة النسخة الاحتياطية المشفرة…")
        if self.logger:
            self.logger.info(f"بدء استعادة نسخة احتياطية مشفرة من: {file_path}")
        self._restore_thread = self.BackupWorker(self.db_manager, mode='restore', logger=self.logger, backup_file=file_path)
        self._restore_thread.finished.connect(self._on_encrypted_restore_finished)
        self._restore_thread.start()

    def _on_encrypted_restore_finished(self, success: bool, _msg: str):
        self.statusBar().clearMessage()
        if success:
            QMessageBox.information(self, "استعادة نسخة مشفرة", "تمت استعادة قاعدة البيانات بنجاح. سيتم تحديث البيانات.")
            if self.logger:
                self.logger.info("تمت استعادة قاعدة البيانات من نسخة مشفرة")
            # تحديث حالة شريط الحالة والبيانات بعد إعادة تهيئة الاتصال
            self.setup_statusbar()
            self.refresh_data()
        else:
            QMessageBox.warning(self, "خطأ", "فشل في استعادة النسخة الاحتياطية المشفرة")
            if self.logger:
                self.logger.warning("فشل استعادة النسخة الاحتياطية المشفرة")
    
    def daily_report(self):
        """عرض التقرير اليومي"""
        try:
            from ..windows.reports_window import ReportsWindow
            from ...services.reports_service import ReportType, ReportFilter
            from datetime import datetime, date
            
            # إنشاء نافذة التقارير
            reports_window = ReportsWindow(self.db_manager, parent=self)
            
            # تعيين فلتر التقرير اليومي
            today = date.today()
            filter_data = ReportFilter(
                start_date=datetime.combine(today, datetime.min.time()),
                end_date=datetime.combine(today, datetime.max.time())
            )
            
            # تعيين نوع التقرير
            reports_window.set_report_type(ReportType.SALES_SUMMARY)
            reports_window.set_filters(filter_data)
            
            # عرض النافذة
            reports_window.show()
            reports_window.generate_report()
            
            self.logger.info("تم فتح التقرير اليومي")
            
        except Exception as e:
            self.logger.error(f"خطأ في فتح التقرير اليومي: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح التقرير اليومي: {str(e)}")
    
    def monthly_report(self):
        """عرض التقرير الشهري"""
        try:
            from ..windows.reports_window import ReportsWindow
            from ...services.reports_service import ReportType, ReportFilter
            from datetime import datetime, date
            import calendar
            
            # إنشاء نافذة التقارير
            reports_window = ReportsWindow(self.db_manager, parent=self)
            
            # تعيين فلتر التقرير الشهري
            today = date.today()
            first_day = date(today.year, today.month, 1)
            last_day = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
            
            filter_data = ReportFilter(
                start_date=datetime.combine(first_day, datetime.min.time()),
                end_date=datetime.combine(last_day, datetime.max.time())
            )
            
            # تعيين نوع التقرير
            reports_window.set_report_type(ReportType.FINANCIAL_SUMMARY)
            reports_window.set_filters(filter_data)
            
            # عرض النافذة
            reports_window.show()
            reports_window.generate_report()
            
            self.logger.info("تم فتح التقرير الشهري")
            
        except Exception as e:
            self.logger.error(f"خطأ في فتح التقرير الشهري: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح التقرير الشهري: {str(e)}")
    
    def profit_report(self):
        """عرض تقرير الأرباح"""
        try:
            from ..windows.reports_window import ReportsWindow
            from ...services.reports_service import ReportType, ReportFilter
            from datetime import datetime, date, timedelta
            
            # إنشاء نافذة التقارير
            reports_window = ReportsWindow(self.db_manager, parent=self)
            
            # تعيين فلتر تقرير الأرباح (آخر 30 يوم)
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            filter_data = ReportFilter(
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.max.time())
            )
            
            # تعيين نوع التقرير
            reports_window.set_report_type(ReportType.PROFIT_LOSS)
            reports_window.set_filters(filter_data)
            
            # عرض النافذة
            reports_window.show()
            reports_window.generate_report()
            
            self.logger.info("تم فتح تقرير الأرباح")
            
        except Exception as e:
            self.logger.error(f"خطأ في فتح تقرير الأرباح: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح تقرير الأرباح: {str(e)}")
    
    def show_about(self):
        """عرض معلومات البرنامج"""
        about_text = """
        <h2>الإصدار المنطقي</h2>
        <p><b>نظام إدارة التجارة العامة</b></p>
        <p>الإصدار: 1.0.0</p>
        <p>نظام شامل لإدارة المخزون والمبيعات والمشتريات</p>
        <p>مطور بتقنية Python و PySide6</p>
        <p>© 2024 الإصدار المنطقي</p>
        """
        QMessageBox.about(self, "حول البرنامج", about_text)
    
    def show_encryption_dialog(self):
        """عرض واجهة إدارة التشفير"""
        try:
            from ..dialogs.encryption_dialog import EncryptionDialog
            
            dialog = EncryptionDialog(self.db_manager, self)
            dialog.exec()
            
            if self.logger:
                self.logger.info("تم فتح واجهة إدارة التشفير")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح واجهة إدارة التشفير: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح واجهة إدارة التشفير: {str(e)}")
    
    def show_payment_dialog(self):
        """عرض واجهة إضافة دفعة جديدة"""
        try:
            from ..dialogs.payment_dialog import PaymentDialog
            
            dialog = PaymentDialog(self.payment_service, self)
            if dialog.exec() == QDialog.Accepted:
                # تحديث البيانات إذا تم إضافة دفعة جديدة
                self.refresh_data()
            
            if self.logger:
                self.logger.info("تم فتح واجهة إضافة دفعة جديدة")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح واجهة إضافة دفعة جديدة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح واجهة إضافة دفعة جديدة: {str(e)}")
    
    def show_accounts_window(self):
        """عرض نافذة إدارة الحسابات المدينة والدائنة"""
        try:
            from .accounts_window import AccountsWindow
            
            accounts_window = AccountsWindow(self.payment_service, self)
            accounts_window.show()
            
            if self.logger:
                self.logger.info("تم فتح نافذة إدارة الحسابات")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة الحسابات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الحسابات: {str(e)}")
    
    def show_payment_reports(self):
        """عرض تقارير المدفوعات"""
        try:
            from .reports_window import ReportsWindow
            from src.core.enums import ReportType
            
            reports_window = ReportsWindow(self.db_manager, self)
            
            # تعيين نوع التقرير للمدفوعات
            reports_window.set_report_type(ReportType.PAYMENTS)
            
            # عرض النافذة
            reports_window.show()
            reports_window.generate_report()
            
            if self.logger:
                self.logger.info("تم فتح تقارير المدفوعات")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح تقارير المدفوعات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح تقارير المدفوعات: {str(e)}")
    
    def show_payment_dashboard(self):
        """عرض لوحة تحكم المدفوعات"""
        try:
            from .payment_dashboard import PaymentDashboard
            
            dashboard = PaymentDashboard(self.db_manager, self)
            dashboard.show()
            
            if self.logger:
                self.logger.info("تم فتح لوحة تحكم المدفوعات")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح لوحة تحكم المدفوعات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح لوحة تحكم المدفوعات: {str(e)}")

    def show_main_dashboard(self):
        """عرض لوحة المعلومات الرئيسية"""
        try:
            from .dashboard_window import DashboardWindow
            
            if not hasattr(self, "_dashboard_window") or self._dashboard_window is None:
                self._dashboard_window = DashboardWindow(self.db_manager, self)
            
            self._dashboard_window.show()
            self._dashboard_window.raise_()
            self._dashboard_window.activateWindow()
            
            if self.logger:
                self.logger.info("تم فتح لوحة المعلومات الرئيسية")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح لوحة المعلومات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح لوحة المعلومات: {str(e)}")
    
    def show_advanced_search_window(self):
        """عرض نافذة البحث المتقدم"""
        try:
            from .advanced_search_window import AdvancedSearchWindow
            
            if not hasattr(self, "_search_window") or self._search_window is None:
                self._search_window = AdvancedSearchWindow(self.db_manager, self)
            
            self._search_window.show()
            self._search_window.raise_()
            self._search_window.activateWindow()
            
            if self.logger:
                self.logger.info("تم فتح نافذة البحث المتقدم")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة البحث المتقدم: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة البحث المتقدم: {str(e)}")
    
    def closeEvent(self, event):
        """حدث إغلاق النافذة"""
        reply = QMessageBox.question(
            self, 
            "تأكيد الخروج",
            "هل تريد إغلاق البرنامج؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.logger:
                self.logger.info("تم إغلاق التطبيق بواسطة المستخدم")
            event.accept()
        else:
            event.ignore()
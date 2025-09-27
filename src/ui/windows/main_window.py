#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
النافذة الرئيسية - Main Window
النافذة الرئيسية للتطبيق مع جميع الوحدات
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QStatusBar, QToolBar,
    QLabel, QPushButton, QMessageBox, QSplashScreen, QDialog
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont
from typing import Optional
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
    
    def init_services(self):
        """تهيئة الخدمات المطلوبة"""
        try:
            if self.db_manager:
                # تهيئة خدمة المخزون
                from src.services.inventory_service import InventoryService
                self.inventory_service = InventoryService(self.db_manager, self.logger)
                
                # تهيئة خدمة المبيعات
                from src.services.sales_service import SalesService
                self.sales_service = SalesService(self.db_manager, self.logger)
                
                # تهيئة خدمة التقارير
                from src.services.reports_service import ReportsService
                self.reports_service = ReportsService(self.db_manager)
                
                # تهيئة خدمة المدفوعات
                from src.services.payment_service import PaymentService
                self.payment_service = PaymentService(self.db_manager)
                
                if self.logger:
                    self.logger.info("تم تهيئة جميع الخدمات في النافذة الرئيسية")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تهيئة الخدمات: {str(e)}")
            self.inventory_service = None
            self.sales_service = None
            self.reports_service = None
    
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
        
        # عنوان القسم
        title = QLabel("إدارة المخزون")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60; margin: 10px;")
        layout.addWidget(title)
        
        # أزرار سريعة
        buttons_layout = QHBoxLayout()
        
        add_product_btn = QPushButton("➕ إضافة منتج")
        add_product_btn.setMinimumHeight(40)
        add_product_btn.clicked.connect(self.add_product)
        buttons_layout.addWidget(add_product_btn)
        
        manage_categories_btn = QPushButton("📂 إدارة الفئات")
        manage_categories_btn.setMinimumHeight(40)
        manage_categories_btn.clicked.connect(self.manage_categories)
        buttons_layout.addWidget(manage_categories_btn)
        
        inventory_report_btn = QPushButton("📋 تقرير المخزون")
        inventory_report_btn.setMinimumHeight(40)
        inventory_report_btn.clicked.connect(self.inventory_report)
        buttons_layout.addWidget(inventory_report_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # منطقة المحتوى
        content_label = QLabel("سيتم إضافة جدول المنتجات والمخزون هنا")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("color: #7f8c8d; font-size: 14px; margin: 50px;")
        layout.addWidget(content_label)
        
        layout.addStretch()
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
        
        title = QLabel("إدارة العملاء والموردين")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f39c12; margin: 10px;")
        layout.addWidget(title)
        
        buttons_layout = QHBoxLayout()
        
        add_customer_btn = QPushButton("👤 إضافة عميل")
        add_customer_btn.setMinimumHeight(40)
        buttons_layout.addWidget(add_customer_btn)
        
        add_supplier_btn = QPushButton("🏭 إضافة مورد")
        add_supplier_btn.setMinimumHeight(40)
        buttons_layout.addWidget(add_supplier_btn)
        
        contacts_report_btn = QPushButton("📇 تقرير العملاء")
        contacts_report_btn.setMinimumHeight(40)
        buttons_layout.addWidget(contacts_report_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        content_label = QLabel("سيتم إضافة جداول العملاء والموردين هنا")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("color: #7f8c8d; font-size: 14px; margin: 50px;")
        layout.addWidget(content_label)
        
        layout.addStretch()
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
        
        file_menu.addSeparator()
        
        exit_action = QAction("خروج", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # قائمة عرض
        view_menu = menubar.addMenu("عرض")
        
        # قائمة أدوات
        tools_menu = menubar.addMenu("أدوات")
        
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
        
        # قائمة مساعدة
        help_menu = menubar.addMenu("مساعدة")
        
        about_action = QAction("حول البرنامج", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
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
        except Exception as e:
            self.logger.error(f"خطأ في فتح نافذة إضافة المنتج: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إضافة المنتج: {str(e)}")
    
    def on_product_saved(self, product):
        """معالجة حفظ المنتج"""
        try:
            self.logger.info(f"تم حفظ المنتج: {product.name}")
            # تحديث المخزون
            if hasattr(self, 'inventory_service'):
                self.inventory_service.refresh_cache()
        except Exception as e:
            self.logger.error(f"خطأ في معالجة حفظ المنتج: {str(e)}")
    
    def show_success_message(self, message: str):
        """عرض رسالة نجاح"""
        self.statusBar().showMessage(message, 3000)  # عرض لمدة 3 ثوان
    
    def manage_categories(self):
        """إدارة الفئات"""
        QMessageBox.information(self, "إدارة الفئات", "سيتم فتح نافذة إدارة الفئات")
    
    def inventory_report(self):
        """تقرير المخزون"""
        QMessageBox.information(self, "تقرير المخزون", "سيتم إنشاء تقرير المخزون")
    
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
            if hasattr(self, 'inventory_service'):
                self.inventory_service.refresh_cache()
            if hasattr(self, 'sales_service'):
                self.sales_service.refresh_cache()
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
        QMessageBox.information(self, "إدارة الموردين", "سيتم فتح نافذة إدارة الموردين")
    
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
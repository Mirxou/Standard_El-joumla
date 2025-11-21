#!/usr/bin/env python3
"""
التطبيق الرئيسي - نظام إدارة المخزون والمبيعات
Main Application - Inventory and Sales Management System

نقطة الدخول الرئيسية للنظام مع واجهة المستخدم الرئيسية
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

# إضافة مسار المشروع إلى sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QMessageBox, QDialog, QSplashScreen, QProgressBar,
    QSystemTrayIcon, QStyle, QFrame, QGridLayout, QPushButton,
    QGroupBox, QTextEdit, QTabWidget, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSettings, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QAction

# استيراد المكونات الأساسية
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager
from src.utils.logger import setup_logger

# استيراد الخدمات
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.services.reports_service import ReportsService
from src.services.user_service import UserService
from src.services.email_service import EmailService
from src.services.reminder_service import init_reminder_service, ReminderService
from src.services.scheduler_service import init_reminder_scheduler, ReminderScheduler
from src.ui.notifications_manager import get_notifications_manager, SmartNotificationsManager

# استيراد النوافذ والحوارات
from src.ui.windows.main_window import MainWindow
from src.ui.dialogs.login_dialog import LoginDialog
from src.ui.dialogs.product_dialog import ProductDialog
from src.ui.dialogs.sales_dialog import SalesDialog
from src.ui.windows.reports_window import ReportsWindow


class DatabaseInitWorker(QThread):
    """عامل تهيئة قاعدة البيانات"""
    progress_updated = Signal(int, str)
    initialization_completed = Signal(bool, str)
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
    
    def run(self):
        try:
            self.progress_updated.emit(10, "تهيئة قاعدة البيانات...")
            
            # تهيئة قاعدة البيانات
            success = self.db_manager.initialize()
            if not success:
                self.initialization_completed.emit(False, "فشل في تهيئة قاعدة البيانات")
                return
            
            self.progress_updated.emit(30, "إنشاء الجداول...")
            
            # إنشاء الجداول الأساسية
            # الجداول يتم إنشاؤها تلقائياً في initialize()
            
            self.progress_updated.emit(50, "تحميل البيانات الأولية...")
            
            # تحميل البيانات الأولية إذا لزم الأمر
            self.load_initial_data()
            
            self.progress_updated.emit(80, "التحقق من سلامة البيانات...")
            
            # التحقق من سلامة قاعدة البيانات
            if not self.verify_database_integrity():
                self.initialization_completed.emit(False, "فشل في التحقق من سلامة قاعدة البيانات")
                return
            
            self.progress_updated.emit(100, "تم الانتهاء من التهيئة")
            self.initialization_completed.emit(True, "تم تهيئة قاعدة البيانات بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة قاعدة البيانات: {str(e)}")
            self.initialization_completed.emit(False, f"خطأ في التهيئة: {str(e)}")
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            # إنشاء مستخدم افتراضي إذا لم يكن موجوداً
            from src.models.user import UserManager, User, UserRole
            from datetime import datetime
            user_manager = UserManager(self.db_manager, self.logger)
            
            # التحقق من وجود مستخدمين
            users = user_manager.get_all_users()
            if not users:
                try:
                    # إنشاء مستخدم المدير الافتراضي
                    admin_user = User(
                        username="admin",
                        full_name="مدير النظام",
                        email="admin@system.local",
                        role=UserRole.ADMIN.value,
                        created_at=datetime.now()
                    )
                    
                    # تعيين الصلاحيات الأساسية للمدير
                    admin_permissions = [
                        'users_create', 'users_read', 'users_update', 'users_delete',
                        'products_create', 'products_read', 'products_update', 'products_delete',
                        'purchases_create', 'purchases_read', 'purchases_update', 'purchases_delete',
                        'sales_create', 'sales_read', 'sales_update', 'sales_delete',
                        'reports_create', 'reports_read', 'reports_update', 'reports_delete',
                        'settings_create', 'settings_read', 'settings_update', 'settings_delete'
                    ]
                    admin_user.set_permissions(admin_permissions)
                    
                    self.logger.info(f"محاولة إنشاء المستخدم: {admin_user.username}")
                    self.logger.info(f"البيانات: {admin_user.to_dict()}")
                    
                    user_id = user_manager.create_user(admin_user, "admin123")
                    if user_id:
                        self.logger.info(f"تم إنشاء مستخدم المدير الافتراضي بنجاح - ID: {user_id}")
                    else:
                        self.logger.error("فشل في إنشاء مستخدم المدير الافتراضي - لم يتم إرجاع ID")
                except Exception as e:
                    self.logger.error(f"خطأ في إنشاء مستخدم المدير الافتراضي: {str(e)}")
                    import traceback
                    self.logger.error(f"تفاصيل الخطأ: {traceback.format_exc()}")
            
            # إنشاء فئات افتراضية
            from src.models.category import CategoryManager
            category_manager = CategoryManager(self.db_manager)
            
            categories = category_manager.get_all_categories()
            if not categories:
                # إنشاء فئات افتراضية
                default_categories = [
                    {"name": "إلكترونيات", "description": "الأجهزة الإلكترونية والكهربائية"},
                    {"name": "ملابس", "description": "الملابس والأزياء"},
                    {"name": "طعام ومشروبات", "description": "المواد الغذائية والمشروبات"},
                    {"name": "كتب وقرطاسية", "description": "الكتب والأدوات المكتبية"},
                    {"name": "منزل وحديقة", "description": "أدوات المنزل والحديقة"}
                ]
                
                for cat_data in default_categories:
                    from src.models.category import Category
                    category = Category(
                        name=cat_data["name"],
                        description=cat_data["description"]
                    )
                    category_manager.create_category(category)
                
                self.logger.info("تم إنشاء الفئات الافتراضية")
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل البيانات الأولية: {str(e)}")
    
    def verify_database_integrity(self) -> bool:
        """التحقق من سلامة قاعدة البيانات"""
        try:
            # التحقق من وجود الجداول الأساسية
            required_tables = [
                'users', 'categories', 'products', 'customers', 
                'suppliers', 'sales', 'sale_items', 'purchases', 
                'purchase_items', 'stock_movements'
            ]
            
            for table in required_tables:
                if not self.db_manager.table_exists(table):
                    self.logger.error(f"الجدول المطلوب غير موجود: {table}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من سلامة قاعدة البيانات: {str(e)}")
            return False


class SplashScreen(QSplashScreen):
    """شاشة البداية"""
    
    def __init__(self):
        # إنشاء صورة بسيطة للشاشة
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor(52, 152, 219))  # لون أزرق
        
        super().__init__(pixmap)
        
        # إعداد النص
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # شريط التقدم
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 250, 300, 20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #34495e;
                border-radius: 5px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 3px;
            }
        """)
        
        # تسمية الحالة
        self.status_label = QLabel("جاري التحميل...", self)
        self.status_label.setGeometry(50, 220, 300, 20)
        self.status_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # عنوان التطبيق
        title_label = QLabel("نظام إدارة المخزون والمبيعات", self)
        title_label.setGeometry(50, 100, 300, 40)
        title_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # معلومات الإصدار
        version_label = QLabel("الإصدار 1.0.0", self)
        version_label.setGeometry(50, 140, 300, 20)
        version_label.setStyleSheet("""
            color: white;
            font-size: 12px;
        """)
        version_label.setAlignment(Qt.AlignCenter)
    
    def update_progress(self, value: int, message: str):
        """تحديث شريط التقدم والرسالة"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        QApplication.processEvents()


class InventoryManagementApp(QApplication):
    """التطبيق الرئيسي لإدارة المخزون والمبيعات"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # إعداد التطبيق
        self.setApplicationName("نظام إدارة المخزون والمبيعات")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("شركة التطوير")
        self.setOrganizationDomain("development.com")
        
        # إعداد الخط العربي
        font = QFont("Arial", 10)
        self.setFont(font)
        
        # إعداد اتجاه النص
        self.setLayoutDirection(Qt.RightToLeft)
        
        # تطبيق السمة المحفوظة
        self.apply_saved_theme()
        
        # إعداد المتغيرات
        self.logger = setup_logger(__name__)
        self.config_manager = ConfigManager()
        self.db_manager: Optional[DatabaseManager] = None
        self.current_user = None
        
        # الخدمات
        self.inventory_service: Optional[InventoryService] = None
        self.sales_service: Optional[SalesService] = None
        self.reports_service: Optional[ReportsService] = None
        self.user_service: Optional[UserService] = None
        self.email_service: Optional[EmailService] = None
        self.reminder_service: Optional[ReminderService] = None
        self.reminder_scheduler: Optional[ReminderScheduler] = None
        self.notifications_manager: Optional[SmartNotificationsManager] = None
        
        # النوافذ
        self.main_window: Optional[MainWindow] = None
        self.reports_window: Optional[ReportsWindow] = None
        
        # شاشة البداية
        self.splash_screen: Optional[SplashScreen] = None
        
        # عامل التهيئة
        self.init_worker: Optional[DatabaseInitWorker] = None
        
        # إعداد معالج الإغلاق
        self.aboutToQuit.connect(self.cleanup)
    
    def apply_saved_theme(self):
        """تطبيق السمة المحفوظة"""
        try:
            from src.ui.theme_manager import get_theme_manager
            theme_manager = get_theme_manager()
            saved_theme = theme_manager.get_current_theme()
            theme_manager.apply_theme(saved_theme)
        except Exception as e:
            print(f"تحذير: فشل تحميل السمة: {e}")
    
    def run(self):
        """تشغيل التطبيق"""
        try:
            self.logger.info("بدء تشغيل التطبيق")
            
            # عرض شاشة البداية
            self.show_splash_screen()
            
            # تهيئة قاعدة البيانات
            self.initialize_database()
            
        except Exception as e:
            self.logger.error(f"خطأ في تشغيل التطبيق: {str(e)}")
            self.show_error_message("خطأ في التشغيل", f"فشل في تشغيل التطبيق: {str(e)}")
            return False
        
        return True
    
    def show_splash_screen(self):
        """عرض شاشة البداية"""
        self.splash_screen = SplashScreen()
        self.splash_screen.show()
        self.processEvents()
    
    def initialize_database(self):
        """تهيئة قاعدة البيانات"""
        try:
            # إنشاء مدير قاعدة البيانات
            db_path = self.config_manager.get_database_path()
            self.db_manager = DatabaseManager(db_path)
            
            # بدء تهيئة قاعدة البيانات في خيط منفصل
            self.init_worker = DatabaseInitWorker(self.db_manager)
            self.init_worker.progress_updated.connect(self.on_init_progress)
            self.init_worker.initialization_completed.connect(self.on_init_completed)
            self.init_worker.start()
            
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة قاعدة البيانات: {str(e)}")
            self.show_error_message("خطأ في قاعدة البيانات", f"فشل في تهيئة قاعدة البيانات: {str(e)}")
    
    def on_init_progress(self, value: int, message: str):
        """معالجة تقدم التهيئة"""
        if self.splash_screen:
            self.splash_screen.update_progress(value, message)
    
    def on_init_completed(self, success: bool, message: str):
        """معالجة اكتمال التهيئة"""
        if self.splash_screen:
            self.splash_screen.close()
            self.splash_screen = None
        
        if success:
            self.logger.info("تم تهيئة قاعدة البيانات بنجاح")
            self.initialize_services()
            # تسجيل الدخول إجباري - لا يمكن تجاوزه
            self.show_mandatory_login_dialog()
        else:
            self.logger.error(f"فشل في تهيئة قاعدة البيانات: {message}")
            self.show_error_message("خطأ في التهيئة", message)
            self.quit()
    
    def initialize_services(self):
        """تهيئة الخدمات"""
        try:
            self.inventory_service = InventoryService(self.db_manager, self.logger)
            self.sales_service = SalesService(self.db_manager, self.logger)
            self.reports_service = ReportsService(self.db_manager)
            self.user_service = UserService(self.db_manager)
            
            self.logger.info("تم تهيئة جميع الخدمات بنجاح")

            # تهيئة البريد + التذكيرات + المجدول (اختياري عبر متغيرات البيئة)
            try:
                self.email_service = EmailService()
                self.reminder_service = init_reminder_service(self.db_manager, self.email_service)
                # يبدأ تلقائياً إذا كانت البيئة مفعّلة SCHEDULER_ENABLED=true
                self.reminder_scheduler = init_reminder_scheduler(self.reminder_service)
                self.logger.info("Reminder scheduler initialized (env-controlled)")
            except Exception as e:
                self.logger.warning(f"تعذرت تهيئة المجدول/التذكيرات: {e}")
            
            # تهيئة نظام الإشعارات الذكية (سيبدأ بعد عرض النافذة الرئيسية)
            try:
                self.notifications_manager = get_notifications_manager(self.db_manager)
                self.logger.info("تم تهيئة نظام الإشعارات الذكية")
            except Exception as e:
                self.logger.warning(f"تعذرت تهيئة نظام الإشعارات: {e}")
            
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة الخدمات: {str(e)}")
            self.show_error_message("خطأ في الخدمات", f"فشل في تهيئة الخدمات: {str(e)}")
    
    def show_mandatory_login_dialog(self):
        """عرض نافذة تسجيل الدخول الإجباري مع إدارة جلسات محسنة"""
        max_attempts = 3
        current_attempt = 0
        
        while current_attempt < max_attempts:
            try:
                login_dialog = LoginDialog(self.user_service)
                login_dialog.setWindowTitle("تسجيل الدخول الإجباري - الإصدار المنطقي")
                
                # إضافة رسالة تحذيرية للمحاولات المتبقية
                if current_attempt > 0:
                    remaining_attempts = max_attempts - current_attempt
                    login_dialog.set_warning_message(f"تحذير: متبقي {remaining_attempts} محاولة/محاولات قبل إغلاق التطبيق")
                
                result = login_dialog.exec()
                
                if result == QDialog.Accepted:
                    session = login_dialog.get_current_session()
                    if session and self._validate_session_security(session):
                        # الحصول على بيانات المستخدم من الجلسة
                        from src.models.user import UserManager
                        user_manager = UserManager(self.db_manager, self.logger)
                        self.current_user = user_manager.get_user_by_id(session.user_id)
                        
                        if self.current_user:
                            self.logger.info(f"تم تسجيل دخول المستخدم بنجاح: {self.current_user.username}")
                            
                            # بدء مراقبة الجلسة
                            self._start_session_monitoring(session)
                            
                            # عرض النافذة الرئيسية
                            self.show_main_window()
                            return
                        else:
                            self.logger.error("فشل في الحصول على بيانات المستخدم")
                            self.show_error_message("خطأ في النظام", "فشل في الحصول على بيانات المستخدم")
                    else:
                        self.logger.error("جلسة غير صحيحة أو غير آمنة")
                        self.show_error_message("خطأ أمني", "جلسة غير صحيحة أو غير آمنة")
                else:
                    # المستخدم ألغى تسجيل الدخول
                    current_attempt += 1
                    if current_attempt >= max_attempts:
                        self.logger.warning("تم تجاوز الحد الأقصى لمحاولات تسجيل الدخول")
                        self.show_error_message(
                            "تم تجاوز الحد الأقصى", 
                            "تم تجاوز الحد الأقصى لمحاولات تسجيل الدخول.\nسيتم إغلاق التطبيق."
                        )
                        self.quit()
                        return
                    else:
                        # إعطاء المستخدم فرصة أخرى
                        reply = QMessageBox.question(
                            None,
                            "تأكيد الإغلاق",
                            f"هل تريد المحاولة مرة أخرى؟\nمتبقي {max_attempts - current_attempt} محاولة/محاولات",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.Yes
                        )
                        
                        if reply == QMessageBox.No:
                            self.quit()
                            return
                            
            except Exception as e:
                self.logger.error(f"خطأ في نافذة تسجيل الدخول: {str(e)}")
                self.show_error_message("خطأ في تسجيل الدخول", f"فشل في عرض نافذة تسجيل الدخول: {str(e)}")
                current_attempt += 1
        
        # إذا وصلنا هنا، فقد فشلت جميع المحاولات
        self.quit()
    
    def _validate_session_security(self, session: 'UserSession') -> bool:
        """التحقق من أمان الجلسة"""
        try:
            # التحقق من صحة الجلسة
            is_valid, validated_session = self.user_service.validate_session(session.session_id)
            
            if not is_valid or not validated_session:
                return False
            
            # التحقق من عدم انتهاء صلاحية الجلسة
            from datetime import datetime, timedelta
            session_timeout = timedelta(minutes=self.user_service.security_settings.session_timeout_minutes)
            
            if datetime.now() - session.last_activity > session_timeout:
                self.logger.warning("انتهت صلاحية الجلسة")
                return False
            
            # التحقق من صحة المستخدم
            if not session.user_id or session.user_id <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من أمان الجلسة: {e}")
            return False
    
    def _start_session_monitoring(self, session: 'UserSession'):
        """بدء مراقبة الجلسة"""
        try:
            # إنشاء مؤقت لمراقبة الجلسة
            self.session_monitor_timer = QTimer()
            self.session_monitor_timer.timeout.connect(lambda: self._check_session_validity(session))
            
            # فحص الجلسة كل دقيقة
            self.session_monitor_timer.start(60000)  # 60 ثانية
            
            # إنشاء مؤقت لتحديث نشاط الجلسة
            self.activity_timer = QTimer()
            self.activity_timer.timeout.connect(lambda: self._update_session_activity(session))
            
            # تحديث النشاط كل 5 دقائق
            self.activity_timer.start(300000)  # 5 دقائق
            
            self.logger.info("تم بدء مراقبة الجلسة")
            
        except Exception as e:
            self.logger.error(f"خطأ في بدء مراقبة الجلسة: {e}")
    
    def _check_session_validity(self, session: 'UserSession'):
        """فحص صحة الجلسة بشكل دوري"""
        try:
            is_valid, validated_session = self.user_service.validate_session(session.session_id)
            
            if not is_valid:
                self.logger.warning("الجلسة غير صحيحة - سيتم تسجيل الخروج")
                self._force_logout("انتهت صلاحية الجلسة")
                
        except Exception as e:
            self.logger.error(f"خطأ في فحص صحة الجلسة: {e}")
    
    def _update_session_activity(self, session: 'UserSession'):
        """تحديث نشاط الجلسة"""
        try:
            self.user_service.update_session_activity(session.session_id)
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث نشاط الجلسة: {e}")
    
    def _force_logout(self, reason: str):
        """إجبار تسجيل الخروج"""
        try:
            self.logger.info(f"إجبار تسجيل الخروج: {reason}")
            
            # إيقاف مراقبة الجلسة
            if hasattr(self, 'session_monitor_timer') and self.session_monitor_timer:
                self.session_monitor_timer.stop()
            
            if hasattr(self, 'activity_timer') and self.activity_timer:
                self.activity_timer.stop()
            
            # عرض رسالة للمستخدم
            QMessageBox.warning(
                self.main_window if self.main_window else None,
                "تسجيل خروج إجباري",
                f"تم تسجيل خروجك من النظام.\nالسبب: {reason}"
            )
            
            # تسجيل الخروج
            self.handle_logout()
            
        except Exception as e:
            self.logger.error(f"خطأ في إجبار تسجيل الخروج: {e}")
            self.quit()
    
    def show_main_window(self):
        """عرض النافذة الرئيسية"""
        try:
            self.main_window = MainWindow(
                config_manager=self.config_manager,
                db_manager=self.db_manager,
                logger=self.logger
            )
            
            self.main_window.show()
            self.logger.info("تم عرض النافذة الرئيسية")
            
            # بدء نظام الإشعارات بعد عرض النافذة
            if self.notifications_manager:
                try:
                    # ربط النافذة الرئيسية بمدير الإشعارات
                    self.notifications_manager.main_window = self.main_window
                    self.notifications_manager.start()
                    self.logger.info("تم بدء نظام الإشعارات الذكية")
                except Exception as e:
                    self.logger.warning(f"فشل بدء نظام الإشعارات: {e}")
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض النافذة الرئيسية: {str(e)}")
            self.show_error_message("خطأ في النافذة الرئيسية", f"فشل في عرض النافذة الرئيسية: {str(e)}")
    
    def show_reports_window(self):
        """عرض نافذة التقارير"""
        try:
            if not self.reports_window:
                self.reports_window = ReportsWindow(self.db_manager)
            
            self.reports_window.show()
            self.reports_window.raise_()
            self.reports_window.activateWindow()
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض نافذة التقارير: {str(e)}")
            self.show_error_message("خطأ في التقارير", f"فشل في عرض نافذة التقارير: {str(e)}")
    
    def handle_logout(self):
        """معالجة تسجيل الخروج"""
        try:
            # إغلاق النوافذ المفتوحة
            if self.main_window:
                self.main_window.close()
                self.main_window = None
            
            if self.reports_window:
                self.reports_window.close()
                self.reports_window = None
            
            # إنهاء جلسة المستخدم
            if self.current_user and self.user_service:
                self.user_service.logout_user(self.current_user.id)
            
            self.current_user = None
            
            # عرض نافذة تسجيل الدخول الإجباري مرة أخرى
            self.show_mandatory_login_dialog()
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الخروج: {str(e)}")
            self.show_error_message("خطأ في تسجيل الخروج", f"فشل في تسجيل الخروج: {str(e)}")
    
    def show_error_message(self, title: str, message: str):
        """عرض رسالة خطأ"""
        QMessageBox.critical(None, title, message)
    
    def cleanup(self):
        """تنظيف الموارد عند الإغلاق"""
        try:
            self.logger.info("بدء تنظيف الموارد")

            # إيقاف نظام الإشعارات
            if self.notifications_manager:
                try:
                    self.notifications_manager.stop()
                    self.logger.info("تم إيقاف نظام الإشعارات")
                except Exception as e:
                    self.logger.warning(f"خطأ في إيقاف الإشعارات: {e}")

            # إيقاف المجدول إن كان يعمل
            try:
                if self.reminder_scheduler and self.reminder_scheduler.is_running():
                    self.reminder_scheduler.stop()
            except Exception:
                pass
            
            # إيقاف العمال
            if self.init_worker and self.init_worker.isRunning():
                self.init_worker.terminate()
                self.init_worker.wait()
            
            # إنهاء جلسة المستخدم
            if self.current_user and self.user_service:
                self.user_service.logout_user(self.current_user.id)
            
            # إغلاق قاعدة البيانات
            if self.db_manager:
                self.db_manager.close()
            
            self.logger.info("تم تنظيف الموارد بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف الموارد: {str(e)}")


def setup_exception_handler():
    """إعداد معالج الاستثناءات العام"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = setup_logger("exception_handler")
        logger.critical(
            "استثناء غير معالج",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # عرض رسالة خطأ للمستخدم
        QMessageBox.critical(
            None,
            "خطأ غير متوقع",
            f"حدث خطأ غير متوقع في التطبيق:\n{str(exc_value)}\n\nيرجى إعادة تشغيل التطبيق."
        )
    
    sys.excepthook = handle_exception


def main():
    """الدالة الرئيسية"""
    try:
        # إعداد معالج الاستثناءات
        setup_exception_handler()
        
        # إنشاء التطبيق
        app = InventoryManagementApp(sys.argv)
        
        # تشغيل التطبيق
        if app.run():
            # تشغيل حلقة الأحداث
            return app.exec()
        else:
            return 1
            
    except Exception as e:
        print(f"خطأ فادح في التطبيق: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
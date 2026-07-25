#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
النافذة الرئيسية - Main Window
النافذة الرئيسية للتطبيق مع جميع الوحدات
"""

import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QCategoryAxis,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QPieSlice,
    QValueAxis,
)
from PySide6.QtCore import QDate, QModelIndex, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont, QIcon, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

project_root = Path(__file__).parent.parent.parent

from PySide6.QtGui import QKeySequence, QShortcut  # For Zen Mode Shortcut

from src.core.local_database_manager import LocalDatabaseManager
from src.core.window_manager import WindowManager
from src.models.customer import CustomerManager
from src.models.payment import PaymentType
from src.models.supplier import SupplierManager
from src.services.ai_prediction_service import AIPredictionService  # Phase 20: AI
from src.services.carbon_service import CarbonService  # Phase 21: Green Ledger
from src.services.dashboard_service import DashboardService
from src.services.fiscal_service import FiscalService  # Phase 19: Fiscal
from src.services.gamification_service import (
    GamificationService,
)  # Phase 22: Gamification
from src.services.hardware_service import HardwareService  # Phase 19: Hardware
from src.services.payment_service import PaymentService
from src.services.report_exporter import ExportFormat, ReportExporter, ReportFilter
from src.services.sentiment_service import SentimentService  # Phase 21: Emotion AI
from src.services.smart_assistant import SmartAssistantService  # Phase 20: NLP
from src.services.system_doctor_service import (
    SystemDoctorService,
)  # Phase 21: Self Healing
from src.services.workflow_service import WorkflowService  # Phase 20: Automation
from src.ui.animations.animation_manager import AnimationManager
from src.ui.components.modern_sidebar import ModernSidebar  # System 2.0 Sidebar
from src.ui.delegates.modern_action_delegate import ModernActionDelegate
from src.ui.dialogs.adjust_stock_dialog import AdjustStockDialog
from src.ui.dialogs.transfer_stock_dialog import TransferStockDialog
from src.ui.effects.visual_effects import VisualEffects
from src.ui.models.inventory_table_model import InventoryTableModel
from src.ui.models.sales_table_model import SalesTableModel
from src.ui.views.app_launcher import AppLauncher  # System 4.0 Launcher
# SalesOrderView removed — was overriding real sales tab with a static demo
from src.ui.widgets.animated_table import AnimatedTableWidget
from src.ui.widgets.custom_title_bar import CustomTitleBar
from src.ui.widgets.quantum_notification import NotificationManager  # Quantum Toasts
from src.ui.styles.design_tokens import C as Colors

# Import New Vision 2030 Windows
from src.ui.windows.ai_predictions_window import AIPredictionsWindow
from src.ui.windows.warehouse_management_window import WarehouseManagementWindow
from src.ui.windows.workflow_designer_window import WorkflowDesignerWindow
from src.utils.i18n_api import I18n

# Import pandas for high-performance data handling
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class DataLoaderWorker(QThread):
    """Worker لتحميل البيانات في الخلفية (لتجنب تجميد الواجهة)"""

    data_loaded = Signal(object)  # يمكنه حمل أي نوع بيانات (قائمة أو قاموس)
    error_occurred = Signal(str)  # signal للأخطاء

    def __init__(self, loader_func, *args, **kwargs):
        super().__init__()
        self.loader_func = loader_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """تنفيذ عملية التحميل في الخلفية"""
        try:
            data = self.loader_func(*self.args, **self.kwargs)
            self.data_loaded.emit(data if data else [])
        except Exception as e:
            import traceback

            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.error_occurred.emit(error_msg)


class InventoryDataLoaderThread(QThread):
    """خيط محسّن لتحميل بيانات المخزون مباشرة من SQLite باستخدام Pandas"""

    data_loaded = Signal(object)  # يرسل DataFrame
    progress_updated = Signal(str)  # يرسل رسالة التقدم
    error_occurred = Signal(str)  # يرسل رسالة خطأ

    def __init__(
        self,
        db_path: str = None,
        db_manager: Optional[LocalDatabaseManager] = None,
        search_term: str = "",
        category_id: int = None,
        warehouse_id: int = None,
        limit: int = None,
        offset: int = 0,
    ):
        super().__init__()
        self.db_path = db_path
        self.db_manager = db_manager
        self.search_term = search_term
        self.category_id = category_id
        self.warehouse_id = warehouse_id  # Multi-Warehouse Support
        self.limit = limit
        self.offset = offset

        from pathlib import Path

        from src.utils.i18n_api import I18n

        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

    def _connect(self):
        if self.db_manager:
            return self.db_manager.create_thread_connection(timeout=30.0, read_only=True)

        import sqlite3

        if not self.db_path:
            raise RuntimeError("No database path provided for InventoryDataLoaderThread")

        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")  # تحسين الأداء
        conn.execute("PRAGMA query_only=true")  # 🔥 Read-Only لتسريع الاستعلامات
        return conn

    def run(self):
        """تحميل البيانات مباشرة من SQLite في الخلفية"""
        try:
            # إرسال رسالة التقدم
            self.progress_updated.emit("جاري الاتصال بقاعدة البيانات...")

            # فتح اتصال خاص داخل الخيط (Thread-Safe)
            conn = self._connect()

            # بناء الاستعلام - دعم Multi-Warehouse
            if self.warehouse_id:
                # استخدام warehouse_inventory إذا كان warehouse_id محدداً
                query = """
                    SELECT
                        p.id,
                        p.barcode,
                        p.name,
                        COALESCE(c.name, 'غير محدد') as category,
                        COALESCE(p.unit, 'قطعة') as unit,
                        COALESCE(wi.quantity, 0) as current_stock,
                        COALESCE(wi.min_stock, p.min_stock, 0) as min_stock,
                        COALESCE(p.selling_price, 0.0) as selling_price,
                        COALESCE(p.cost_price, 0.0) as cost_price,
                        COALESCE(w.name, '') as warehouse_name
                    FROM products p
                    LEFT JOIN categories c ON p.category_id = c.id
                    LEFT JOIN warehouse_inventory wi ON p.id = wi.product_id AND wi.warehouse_id = ?
                    LEFT JOIN warehouses w ON wi.warehouse_id = w.id
                    WHERE COALESCE(p.is_active, 1) = 1
                """
                params = [self.warehouse_id]
            else:
                # الطريقة القديمة (إجمالي المخزون من جميع المستودعات)
                query = """
                    SELECT
                        p.id,
                        p.barcode,
                        p.name,
                        COALESCE(c.name, 'غير محدد') as category,
                        COALESCE(p.unit, 'قطعة') as unit,
                        COALESCE(p.current_stock, 0) as current_stock,
                        COALESCE(p.min_stock, 0) as min_stock,
                        COALESCE(p.selling_price, 0.0) as selling_price,
                        COALESCE(p.cost_price, 0.0) as cost_price,
                        '' as warehouse_name
                    FROM products p
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE COALESCE(p.is_active, 1) = 1
                """
                params = []

            # إضافة مرشحات
            if self.search_term:
                query += " AND (p.name LIKE ? OR p.barcode LIKE ?)"
                search_pattern = f"%{self.search_term}%"
                params.extend([search_pattern, search_pattern])

            if self.category_id:
                query += " AND p.category_id = ?"
                params.append(self.category_id)

            # إضافة الترتيب
            query += " ORDER BY p.id DESC"

            # إضافة LIMIT و OFFSET إذا كان محدداً
            if self.limit:
                query += " LIMIT ?"
                params.append(self.limit)
                if self.offset:
                    query += " OFFSET ?"
                    params.append(self.offset)

            # إرسال رسالة التقدم
            self.progress_updated.emit(self.i18n.get_message("loading", default="جاري تحميل المنتجات..."))

            # تحميل البيانات مباشرة باستخدام Pandas (أسرع بكثير)
            if PANDAS_AVAILABLE:
                df = pd.read_sql_query(query, conn, params=params if params else None)

                # إضافة عمود حالة المخزون
                if not df.empty:
                    conditions = [  # noqa: F841
                        df["current_stock"] == 0,
                        df["current_stock"] <= df["min_stock"],
                    ]
                    choices = ["نفد من المخزون", "مخزون منخفض"]  # noqa: F841
                    df["status"] = pd.Series(["جيد"] * len(df))
                    df.loc[df["current_stock"] == 0, "status"] = "نفد من المخزون"
                    df.loc[
                        (df["current_stock"] > 0) & (df["current_stock"] <= df["min_stock"]),
                        "status",
                    ] = "مخزون منخفض"

                    # إضافة عمود الإجراءات الفارغ
                    df["actions"] = ""

                    # إعادة ترتيب الأعمدة (مع عمود warehouse_name إذا كان موجوداً)
                    if "warehouse_name" in df.columns:
                        df = df[
                            [
                                "id",
                                "barcode",
                                "name",
                                "category",
                                "unit",
                                "current_stock",
                                "min_stock",
                                "selling_price",
                                "warehouse_name",
                                "status",
                                "actions",
                            ]
                        ]
                    else:
                        df = df[
                            [
                                "id",
                                "barcode",
                                "name",
                                "category",
                                "unit",
                                "current_stock",
                                "min_stock",
                                "selling_price",
                                "status",
                                "actions",
                            ]
                        ]
                else:
                    # DataFrame فارغ بنفس الأعمدة
                    df = pd.DataFrame(
                        columns=[
                            "id",
                            "barcode",
                            "name",
                            "category",
                            "unit",
                            "current_stock",
                            "min_stock",
                            "selling_price",
                            "status",
                            "actions",
                        ]
                    )

                # إرسال رسالة التقدم
                self.progress_updated.emit(
                    self.i18n.get_message("data_loaded_successfully", default="تم تحميل البيانات بنجاح!")
                )

                # إرسال البيانات
                self.data_loaded.emit(df)
            else:
                # Fallback: إذا لم يكن Pandas متاحاً
                self.progress_updated.emit("خطأ: Pandas غير متاح")
                self.data_loaded.emit(None)

        except Exception as e:
            import traceback

            error_msg = f"خطأ في تحميل البيانات: {str(e)}\n{traceback.format_exc()}"
            self.progress_updated.emit(f"خطأ: {str(e)}")
            self.error_occurred.emit(error_msg)
        finally:
            if "conn" in locals() and conn:
                try:
                    conn.close()
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")


class SalesDataLoaderThread(QThread):
    """خيط محسّن لتحميل بيانات المبيعات مباشرة من SQLite باستخدام Pandas"""

    data_loaded = Signal(object)  # يرسل DataFrame
    summary_loaded = Signal(object)  # يرسل قاموس الملخص
    error_occurred = Signal(str)

    def __init__(
        self,
        db_path: str = None,
        db_manager: Optional[LocalDatabaseManager] = None,
        search_term: str = "",
        status: str = None,
        payment_method: str = None,
        limit: int = 500,
        offset: int = 0,
    ):
        super().__init__()
        self.db_path = db_path
        self.db_manager = db_manager
        self.search_term = search_term
        self.status = status
        self.payment_method = payment_method
        self.limit = limit
        self.offset = offset

    def _connect(self):
        if self.db_manager:
            return self.db_manager.create_thread_connection(timeout=30.0, read_only=True)

        import sqlite3

        if not self.db_path:
            raise RuntimeError("No database path provided for SalesDataLoaderThread")

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def run(self):
        try:
            conn = self._connect()

            # بناء الاستعلام الرئيسي
            query = """
                SELECT
                    s.id,
                    s.invoice_number,
                    COALESCE(c.name, 'زبون نقدي') as customer_name,
                    s.sale_date,
                    s.total_amount,
                    s.paid_amount,
                    s.remaining_amount,
                    s.status,
                    s.payment_method
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE 1=1
            """
            params = []

            if self.search_term:
                query += " AND (s.invoice_number LIKE ? OR c.name LIKE ?)"
                search_pattern = f"%{self.search_term}%"
                params.extend([search_pattern, search_pattern])

            if self.status:
                query += " AND s.status = ?"
                params.append(self.status)

            if self.payment_method:
                query += " AND s.payment_method = ?"
                params.append(self.payment_method)

            query += " ORDER BY s.sale_date DESC"
            if self.limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([self.limit, self.offset])

            if PANDAS_AVAILABLE:
                df = pd.read_sql_query(query, conn, params=params if params else None)
                df["actions"] = ""  # إضافة عمود الإجراءات
                self.data_loaded.emit(df)
            else:
                self.error_occurred.emit("Pandas غير متاح — يرجى تثبيت pandas لتحميل بيانات المبيعات")

        except Exception as e:
            import traceback

            self.error_occurred.emit(f"خطأ في تحميل المبيعات: {str(e)}\n{traceback.format_exc()}")
        finally:
            if "conn" in locals() and conn:
                try:
                    conn.close()
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")


class MainWindow(QMainWindow):
    """النافذة الرئيسية للتطبيق"""

    logout_requested = Signal()

    def __init__(
        self,
        config_manager=None,
        db_manager=None,
        logger=None,
        inventory_service=None,
        sales_service=None,
        reports_service=None,
        user_service=None,
        payment_service=None,
        dashboard_service=None,
        notifications_manager=None,
        hybrid_service=None,
    ):
        super().__init__()

        # --- Modern Window Setup ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        # خلفية صلبة بدلاً من الشفافة
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_NoSystemBackground, False)

        # Initialize Notification Manager
        self.notify = NotificationManager(self)

        self.config_manager = config_manager
        self.db_manager = db_manager
        self.logger = logger
        self.hybrid_service = hybrid_service
        self.app_start_time = datetime.now()
        self._background_threads: List[QThread] = []
        self._managed_windows: List[QWidget] = []

        # تهيئة Window Manager المركزي (بدون db_manager - Factory Pattern)
        self.window_manager = WindowManager(organization="StandardElJoumla", appname="ERP", parent=self)

        # تهيئة متغيرات المخزون (لن يتم تحميلها إلا عند الطلب)
        self._inventory_loader = None
        self._inventory_offset = 0
        self._inventory_has_more = True
        self.inventory_model = None  # سيتم إنشاؤه فقط عند فتح صفحة المخزون
        self.sales_model = None  # سيتم إنشاؤه فقط عند فتح صفحة المبيعات

        # تحسينات السلاسة والتحكم - Debouncing و Throttling
        self._search_debounce_timer = QTimer(self)
        self._search_debounce_timer.setSingleShot(True)
        self._search_debounce_timer.timeout.connect(self._on_search_debounced)
        self._last_search_term = ""

        # Throttling للتحديثات
        self._update_throttle_timer = QTimer(self)
        self._update_throttle_timer.setSingleShot(True)
        self._pending_updates = {}

        # تحسينات الأداء
        self._is_updating = False
        self._update_queue = []

        # حفظ الخدمات الممررة (إن وجدت)
        self._passed_inventory_service = inventory_service
        self._passed_sales_service = sales_service
        self._passed_reports_service = reports_service
        self._passed_user_service = user_service
        self._passed_payment_service = payment_service
        self._passed_dashboard_service = dashboard_service
        self._passed_notifications_manager = notifications_manager
        self._passed_hybrid_service = hybrid_service

        # تهيئة الخدمات
        self.init_services()

        # تسجيل جميع النوافذ في Window Manager
        self._register_all_windows()

        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

        # تعيين أيقونة النافذة الرئيسية
        icon_path = Path(__file__).parent.parent.parent.parent / "assets" / "icons" / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setWindowTitle(self.i18n.get_message("system_title"))

        # تحسين حجم النوافذ - responsive حسب حجم الشاشة
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                screen_width = screen_geometry.width()
                screen_height = screen_geometry.height()

                # حساب الحجم الأمثل (85% من الشاشة كحد أقصى)
                optimal_width = min(1400, int(screen_width * 0.85))
                optimal_height = min(900, int(screen_height * 0.85))

                # الحد الأدنى والأقصى
                self.setMinimumSize(1000, 700)
                self.setMaximumSize(screen_width, screen_height)

                # الحجم الافتراضي
                self.resize(optimal_width, optimal_height)

                # مركز النافذة على الشاشة
                self._center_window()
            else:
                # قيم افتراضية إذا لم تتوفر معلومات الشاشة
                self.setMinimumSize(1000, 700)
                self.resize(1200, 800)
        else:
            # قيم افتراضية إذا لم يتوفر QApplication
            self.setMinimumSize(1000, 700)
            self.resize(1200, 800)

        # تهيئة Animation Manager و Visual Effects
        self.animation_manager = AnimationManager(self)
        self.visual_effects = VisualEffects()

        # إعداد الواجهة
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()

        # إعداد اختصارات لوحة المفاتيح
        self.setup_keyboard_shortcuts()

        # إعداد شريط الإجراءات السريعة
        self.setup_quick_actions()

        # تطبيق الإعدادات
        self.apply_settings()

        # إعداد Opacity للـ fade in
        self.setWindowOpacity(0.0)

        # مؤقت لتحديث مؤشرات الحالة
        try:
            self._status_timer = QTimer(self)
            self._status_timer.setInterval(5000)  # كل 5 ثوانٍ (خفيف: تحديث تسمية + إشعارات فقط)
            self._status_timer.timeout.connect(self.update_statusbar_metrics)
            self._status_timer.start()
        except (AttributeError, RuntimeError) as e:
            self.logger.debug(f"Status timer initialization skipped: {e}")

        # تهيئة WebSocket Client للتحديثات الفورية (Disabling to fix crash)
        # self.init_websocket_client()

        if self.logger:
            self.logger.info("تم إنشاء النافذة الرئيسية")

        # بدء نظام الإشعارات الذكية إن توفرت قاعدة البيانات
        try:
            if hasattr(self, "notifications_manager") and self.notifications_manager:
                self.notifications_manager.start()
        except (AttributeError, RuntimeError) as e:
            self.logger.debug(f"Notification system init skipped: {e}")

    def init_services(self):
        """تهيئة الخدمات المطلوبة"""
        # استخدام الخدمات الممررة إن وجدت، وإلا تهيئتها
        self.inventory_service = self._passed_inventory_service
        self.sales_service = self._passed_sales_service
        self.reports_service = self._passed_reports_service
        self.payment_service = self._passed_payment_service
        self.dashboard_service = self._passed_dashboard_service
        self.notifications_manager = getattr(self, "_passed_notifications_manager", None)
        self.hybrid_service = self._passed_hybrid_service

        # تهيئة الخدمات الأخرى
        self.product_service = None
        self.purchase_service = None
        self.customer_manager = None
        self.supplier_manager = None
        self.ai_service = None
        self.printing_service = None

        # Phase 19: New Services
        self.hardware_service = None
        self.fiscal_service = None

        # Phase 20: The Global Standard
        self.ai_prediction_service = None
        self.workflow_service = None
        self.smart_assistant = None

        # تهيئة خدمة المخزون إذا لم يتم تمريرها
        if not self.inventory_service:
            try:
                from src.services.inventory_service import InventoryService

                self.inventory_service = InventoryService(self.db_manager, self.logger)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"تعذر تهيئة خدمة المخزون: {e}")

        # تهيئة خدمة المبيعات إذا لم يتم تمريرها
        if not self.sales_service:
            try:
                from src.services.sales_service import SalesService

                self.sales_service = SalesService(self.db_manager, self.logger)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"تعذر تهيئة خدمة المبيعات: {e}")

        # تهيئة خدمة التقارير إذا لم يتم تمريرها
        if not self.reports_service:
            try:
                self.reports_service = ReportExporter(self.db_manager)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"تعذر تهيئة خدمة التقارير: {e}")

        # تهيئة خدمة المدفوعات إذا لم يتم تمريرها
        if not self.payment_service:
            try:
                self.payment_service = PaymentService(self.db_manager, self.logger)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"تعذر تهيئة خدمة المدفوعات: {e}")

        # تهيئة خدمة لوحات المعلومات إذا لم يتم تمريرها
        if not self.dashboard_service:
            try:
                self.dashboard_service = DashboardService(self.db_manager)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"تعذر تهيئة خدمة لوحات المعلومات: {e}")

        # تهيئة مديري العملاء والموردين
        try:
            self.customer_manager = CustomerManager(self.db_manager)
            self.supplier_manager = SupplierManager(self.db_manager)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة مديري العملاء/الموردين: {e}")

        # تهيئة خدمة المشتريات
        try:
            from src.services.purchase_service import PurchaseService

            self.purchase_service = PurchaseService(self.db_manager, self.logger)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة خدمة المشتريات: {e}")

        # تهيئة خدمة طباعة الفواتير (PrintService Advanced)
        try:
            from src.services.print_service import initialize_print_service

            self.print_service = initialize_print_service()
            if self.logger:
                self.logger.info("✅ تم تهيئة خدمة الطباعة المتقدمة (PrintService)")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة خدمة الطباعة: {e}")
            self.print_service = None

        # تهيئة خدمة العتاد (Hardware Service)
        try:
            hw_settings = self.config_manager.get_hardware_settings()
            self.hardware_service = HardwareService(
                port=hw_settings.get("customer_display_port", "COM3"),
                baudrate=hw_settings.get("customer_display_baudrate", 9600),
            )
            if self.logger:
                self.logger.info(f"✅ تم تهيئة خدمة العتاد على المنفذ: {self.hardware_service.port}")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة خدمة العتاد: {e}")

        # تهيئة الخدمة الجبائية (Fiscal Service)
        try:
            self.fiscal_service = FiscalService(self.db_manager)
            if self.logger:
                self.logger.info("✅ تم تهيئة الخدمة الجبائية (G50/Etat 104)")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة الخدمة الجبائية: {e}")

        # تهيئة خدمات Phase 20 (AI & Automation)
        try:
            self.ai_prediction_service = AIPredictionService(self.db_manager)
            self.ai_service = self.ai_prediction_service
            self.workflow_service = WorkflowService(self.db_manager, self.notify)
            self.smart_assistant = SmartAssistantService(self.logger)
            if self.logger:
                self.logger.info("✅ تم تهيئة خدمات الذكاء الاصطناعي والأتمتة (Oracle/Autopilot)")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة خدمات AI: {e}")

        # تهيئة خدمات Phase 21 (The 2030 Vision)
        try:
            self.carbon_service = CarbonService(self.db_manager)
            self.sentiment_service = SentimentService()
            self.system_doctor = SystemDoctorService(self.db_manager)

            # تشغيل الفحص الذاتي عند البدء Startup Check
            issues = self.system_doctor.diagnose()
            if issues:
                self.logger.warning(f"🩺 System Doctor Found Issues: {issues}")
            else:
                self.logger.info("🩺 System Doctor: النظام سليم 100%")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة خدمات Vision 2030: {e}")

        # تهيئة خدمات Phase 22 (Gamification)
        try:
            self.gamification_service = GamificationService(self.db_manager)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة خدمات Gamification: {e}")

        # ===== Vision 2030 Smart Assistant (Phase 4) =====
        from src.ui.widgets.smart_assistant_widget import SmartAssistantWidget

        self.smart_assistant_widget = SmartAssistantWidget(self)
        self.smart_assistant_widget.hide()
        self.smart_assistant_widget.command_received.connect(self.handle_smart_command_action)
        self.update_assistant_position()

        # Zen Mode Shortcut (Alt+Z)
        self.zen_shortcut = QShortcut(QKeySequence("Alt+Z"), self)
        self.zen_shortcut.activated.connect(self.toggle_zen_mode)
        if self.logger:
            self.logger.info("✅ تم تهيئة خدمات Gamification & Zen Mode")

        # تهيئة خدمات Phase 23 (The Dragon's Edge)
        try:
            from src.services.approval_service import ApprovalService
            from src.services.qrcode_service import QRCodeService

            self.approval_service = ApprovalService(self.db_manager, self.notify)
            self.qrcode_service = QRCodeService()

            if self.logger:
                self.logger.info("✅ تم تهيئة خدمات Super App (Shenpi/QR)")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر تهيئة خدمات Phase 23: {e}")

        if self.logger:
            self.logger.info("تم تهيئة الخدمات (محسنة/تقليدية) في النافذة الرئيسية")

        # تهيئة مراقب الاستقرار (Stability Watchdog - Vision 2030)
        try:
            self.stability_timer = QTimer(self)
            self.stability_timer.setInterval(120000)  # كل دقيقتين
            self.stability_timer.timeout.connect(self._run_stability_check)
            self.stability_timer.start()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    class BackupWorker(QThread):
        """Worker للنسخ الاحتياطي والاستعادة"""

        finished = Signal(bool, str)

        def __init__(
            self,
            db_manager,
            mode: str,
            logger=None,
            backup_file: Optional[str] = None,
            metadata: Optional[dict] = None,
        ):
            super().__init__()
            self.db_manager = db_manager
            self.mode = mode  # 'backup' or 'restore'
            self.logger = logger
            self.backup_file = backup_file
            self.metadata = metadata or {}

        def run(self):
            try:
                if self.mode == "backup":
                    if hasattr(self.db_manager, "backup_database_encrypted"):
                        path = self.db_manager.backup_database_encrypted(metadata=self.metadata)
                        ok = bool(path)
                        self.finished.emit(ok, str(path) if path else "")
                    else:
                        ok = self.db_manager.backup_database()
                        self.finished.emit(ok, "")
                elif self.mode == "restore":
                    ok = False
                    if hasattr(self.db_manager, "restore_database_encrypted") and self.backup_file:
                        ok = self.db_manager.restore_database_encrypted(self.backup_file)
                    self.finished.emit(ok, "")
                else:
                    self.finished.emit(False, "وضع غير معروف")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"خطأ في مهمة النسخ الاحتياطي/الاستعادة: {str(e)}")
                self.finished.emit(False, str(e))

    def setup_ui(self):
        """إعداد واجهة المستخدم - Modern Architecture"""
        # الويدجت المركزي مع خلفية صلبة
        central_container = QWidget()
        central_container.setStyleSheet(f"background-color: {Colors.BG_VOID};")
        self.setCentralWidget(central_container)

        # التخطيط الجذري
        root_layout = QVBoxLayout(central_container)
        root_layout.setContentsMargins(10, 10, 10, 10)  # Margin for shadow/border
        root_layout.setSpacing(0)

        # الإطار الرئيسي (The Window Border)
        self.main_frame = QFrame()
        self.main_frame.setObjectName("mainFrame")
        # خلفية صلبة داكنة احترافية
        self.main_frame.setStyleSheet(f"""
            QFrame#mainFrame {{
                background-color: {Colors.BG_VOID};
                border-radius: 12px;
                border: 2px solid {Colors.ACCENT_GOLD};
            }}
        """)
        # إضافة ظل للإطار الرئيسي (Subtle Gold Glow)
        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(212, 168, 83, 60))
        shadow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(shadow)

        root_layout.addWidget(self.main_frame)

        # تخطيط الإطار الرئيسي (TitleBar + Content)
        window_layout = QVBoxLayout(self.main_frame)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)

        # 1. شريط العنوان المخصص (Custom Title Bar)
        self.title_bar = CustomTitleBar(self)
        window_layout.addWidget(self.title_bar)

        # 2. جسم النافذة (Horizontal: Sidebar + Content)
        body_widget = QWidget()
        body_widget.setStyleSheet("background: transparent; border: none;")
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # --- Sidebar ---
        # --- Modern Sidebar (System 2.0) ---
        self.sidebar = ModernSidebar()
        self.sidebar.page_changed.connect(self.on_sidebar_navigation)

        # Initial State: Visible (Professional Mode)
        self.sidebar.show()

        # --- Content Area ---
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("""
            QStackedWidget {
                background: transparent;
                border: none;
            }
        """)

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.content_area, 1)

        window_layout.addWidget(body_widget)

        # 3. Size Grip (Bottom Right)
        from PySide6.QtWidgets import QSizeGrip

        grip_frame = QFrame()
        grip_frame.setFixedHeight(10)
        grip_frame.setStyleSheet("background: transparent; border: none;")
        grip_layout = QHBoxLayout(grip_frame)
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()
        grip = QSizeGrip(self)
        grip.setStyleSheet("""
            QSizeGrip {
                background: transparent;
                width: 20px;
                height: 20px;
            }
        """)
        grip_layout.addWidget(grip, 0, Qt.AlignBottom | Qt.AlignRight)
        window_layout.addWidget(grip_frame)

        # ---------------------------------------------------------
        # تهيئة الصفحات (Lazy Loading Engine)
        # ---------------------------------------------------------
        self.pages: Dict[str, QWidget] = {}
        self.page_names = {
            "launcher": 0,
            "dashboard": 1,
            "inventory": 2,
            "sales": 3,
            "purchases": 4,
            "payments": 5,
            "reports": 6,
            "contacts": 7,
            "settings": 8,
            "performance": 9,
        }

        # الصفحة الرئيسية: App Launcher (System 4.0)
        self.launcher = AppLauncher()
        self.launcher.app_selected.connect(lambda app_id: self.switch_page(app_id))
        self.content_area.addWidget(self.launcher)
        self.pages["launcher"] = self.launcher

        # Dashboard Tab
        self.dashboard_tab = self.create_dashboard_tab()
        self.content_area.addWidget(self.dashboard_tab)
        self.pages["dashboard"] = self.dashboard_tab

        # Sales Tab (lazy-loaded via _build_page)
        # SalesOrderView demo removed — real sales tab restored

        # Start at Launcher
        # Start at Launcher - handled by QTimer below
        # self.content_area.setCurrentWidget(self.launcher)

        # 🔥 LEGENDARY ANIMATION: Slide & Fade In Dashboard on Startup
        # try:
        #     self.animation_manager.fade_in(self.dashboard_tab, duration=1000)
        #     self.animation_manager.slide_in(self.dashboard_tab, direction="up", duration=800)
        #     if self.logger:
        #         self.logger.debug("✨ Legendary Animation: Dashboard entrance started")
        # except Exception as e:
        #     if self.logger:
        #         self.logger.warning(f"Failed to start startup animation: {e}")

        # الصفحات الأخرى (يتم تحميلها عند الطلب - Lazy Loading)
        for page_name in [
            "inventory",
            "sales",
            "purchases",
            "payments",
            "reports",
            "contacts",
            "settings",
            "performance",
        ]:
            placeholder = QWidget()
            placeholder.setStyleSheet("background-color: transparent;")
            self.content_area.addWidget(placeholder)

        # تشغيل الصفحة الأولى مع ضمان ضبط حالة السايدبار (إخفاءه)
        QTimer.singleShot(0, lambda: self.switch_page("dashboard"))

        if self.logger:
            self.logger.debug("✅ تم تحويل الواجهة إلى Sidebar Architecture مع Lazy Loading Engine")

        self.apply_global_table_styles()

    def apply_global_table_styles(self):
        """تطبيق ستايل موحد لجميع الجداول (خلفية سوداء، خط أبيض)"""
        table_style = f"""
            QTableWidget, QTableView {{
                background-color: {Colors.BG_DEEP};
                color: {Colors.TEXT_BRIGHT};
                gridline-color: {Colors.BORDER_DEFAULT};
                border: 1px solid {Colors.BORDER_DEFAULT};
                selection-background-color: {Colors.ACCENT_GOLD};
                selection-color: {Colors.TEXT_INVERSE};
            }}
            QTableWidget::item, QTableView::item {{
                border-bottom: 1px solid {Colors.BORDER_VOID};
            }}
            QHeaderView::section {{
                background-color: {Colors.BG_DEEP};
                color: {Colors.ACCENT_GOLD};
                font-weight: bold;
                border: 1px solid {Colors.BORDER_DEFAULT};
                padding: 4px;
            }}
            /* تحديث مظهر الـ Scrollbar ليتناسب مع النمط المظلم */
            QScrollBar:vertical {{
                border: none;
                background: {Colors.BG_DEEP};
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER_DEFAULT};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.ACCENT_GOLD};
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {Colors.BG_DEEP};
                height: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {Colors.BORDER_DEFAULT};
                min-width: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {Colors.ACCENT_GOLD};
            }}
        """
        self.setStyleSheet(self.styleSheet() + table_style)

    def _center_window(self):
        """توسيط النافذة على الشاشة"""
        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    screen_geometry = screen.geometry()
                    window = self.frameGeometry()
                    center_point = screen_geometry.center()
                    window.moveCenter(center_point)
                    self.move(window.topLeft())
        except (ValueError, TypeError, AttributeError) as e:
            if self.logger:
                self.logger.warning(f"Window centering failed: {e}")

    def logout(self):
        """طلب تسجيل الخروج من المستخدم"""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "تأكيد الخروج",
            "هل أنت متأكد أنك تريد تسجيل الخروج من النظام؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.logout_requested.emit()

    def on_sidebar_navigation(self, page_id: str, title: str):
        """Handle ModernSidebar navigation signals"""
        if page_id == "home":
            # Go back to Dashboard
            self.switch_page("dashboard")
            return

        # Handle Special Actions (Dialogs/Windows)
        if page_id == "users":
            self.show_user_management()
            return
        elif page_id == "system":
            self.show_system_management()
            return
        elif page_id == "audit":
            self.show_audit_viewer()
            return
        elif page_id == "notifications":
            self.show_notification_center()
            return
        elif page_id == "performance":
            self.show_performance_dashboard()
            return
        elif page_id == "logout":
            self.logout()
            return

        # Map Sidebar IDs to Page IDs
        mapping = {
            "dashboard": "dashboard",  # Special case if sidebar has dashboard btn
            "inventory": "inventory",
            "sales": "sales",  # 🔥 Now points to System 4.0 View
            "purchases": "purchases",
            "payments": "payments",
            "reports": "reports",
            "contacts": "contacts",  # Explicit mapping check
            "customers": "contacts",  # Map customers to contacts
            "settings": "settings",  # Explicit mapping check
        }

        if page_id in mapping:
            target_page = mapping[page_id]
            self.switch_page(target_page)
        else:
            self.logger.warning(f"Unmapped sidebar page: {page_id}")

    def switch_page(self, page_name: str):
        """
        التبديل بين الصفحات مع Lazy Loading Engine

        Args:
            page_name: اسم الصفحة ('dashboard', 'inventory', 'sales', etc.)
        """
        try:
            # Phase 5: Adaptive Intelligence Tracking
            if hasattr(self, "gamification_service"):
                try:
                    self.gamification_service.track_action(f"nav_{page_name}")
                except (AttributeError, RuntimeError) as e:
                    self.logger.debug(f"Gamification tracking skipped: {e}")

            # الحصول على الفهرس
            if page_name not in self.page_names:
                if self.logger:
                    self.logger.warning(f"صفحة غير معروفة: {page_name}")
                return

            index = self.page_names[page_name]

            # 🔥 Lazy Loading Engine: بناء الصفحة فقط عند الحاجة إليها 🔥
            # التحقق من وجود الصفحة وصحتها
            page_needs_rebuild = False
            if page_name not in self.pages:
                page_needs_rebuild = True
            else:
                # التحقق من أن الصفحة صالحة (لم يتم حذفها)
                try:
                    page_widget = self.pages[page_name]
                    if page_widget is None:
                        page_needs_rebuild = True
                    else:
                        # محاولة الوصول إلى الصفحة للتحقق من صحتها
                        _ = page_widget.isVisible()
                except RuntimeError:
                    # الصفحة محذوفة (Internal C++ object already deleted)
                    page_needs_rebuild = True
                    if self.logger:
                        self.logger.warning(f"⚠️ الصفحة '{page_name}' محذوفة - سيتم إعادة بنائها")
                    del self.pages[page_name]

            if page_needs_rebuild:
                # الصفحة غير موجودة - بناءها الآن
                if self.logger:
                    self.logger.debug(f"🔨 بناء الصفحة '{page_name}' (Lazy Loading)...")

                # إزالة الصفحة المؤقتة
                placeholder = self.content_area.widget(index)
                if placeholder:
                    self.content_area.removeWidget(placeholder)
                    placeholder.deleteLater()

                # بناء الصفحة الفعلية
                page_widget = self._build_page(page_name)

                # 🔥 تحديث إحصائيات Dashboard فوراً بعد البناء
                if page_name == "dashboard":
                    QTimer.singleShot(100, self.refresh_dashboard_stats)
                    # تحديث الرسوم البيانية بعد تحميل البيانات
                    QTimer.singleShot(500, lambda: self._update_dashboard_charts_initial())
                if page_widget:
                    self.content_area.insertWidget(index, page_widget)
                    self.pages[page_name] = page_widget
                    if self.logger:
                        self.logger.debug(f"✅ تم بناء الصفحة '{page_name}' بنجاح")
                else:
                    if self.logger:
                        self.logger.error(f"❌ فشل في بناء الصفحة '{page_name}'")
                    return
            else:
                # ✅ Smart Check: الصفحة موجودة بالفعل
                if page_name == "inventory" and hasattr(self, "inventory_model"):
                    if self.inventory_model and self.inventory_model.rowCount() > 0:
                        if self.logger:
                            self.logger.debug(f"✅ صفحة '{page_name}' محمّلة بالفعل - تخطي إعادة التحميل")

                # 🔥 Safety Check: التحقق من أن الصفحة صالحة (لم يتم حذفها)
                page_widget = self.pages.get(page_name)
                if page_widget is None:
                    # الصفحة غير موجودة - إعادة بنائها
                    page_needs_rebuild = True
                else:
                    try:
                        # محاولة الوصول إلى الصفحة للتحقق من صحتها
                        _ = page_widget.isVisible()
                    except RuntimeError:
                        # الصفحة محذوفة (Internal C++ object already deleted)
                        if self.logger:
                            self.logger.warning(f"⚠️ الصفحة '{page_name}' محذوفة - إعادة بنائها...")
                        del self.pages[page_name]
                        page_needs_rebuild = True

                if page_needs_rebuild:
                    # إعادة بناء الصفحة
                    page_widget = self._build_page(page_name)
                    if page_widget:
                        # إزالة الصفحة المؤقتة إن وجدت
                        placeholder = self.content_area.widget(index)
                        if placeholder:
                            self.content_area.removeWidget(placeholder)
                            placeholder.deleteLater()
                        self.content_area.insertWidget(index, page_widget)
                        self.pages[page_name] = page_widget
                    else:
                        if self.logger:
                            self.logger.error(f"❌ فشل في إعادة بناء الصفحة '{page_name}'")
                        return

            # تبديل الصفحة (بعد التأكد من صحتها)
            if page_name not in self.pages or self.pages[page_name] is None:
                if self.logger:
                    self.logger.error(f"❌ الصفحة '{page_name}' غير متاحة")
                return

            # 🔥 System 2.0 Transition: Cross-Fade Animation
            target_widget = self.pages[page_name]
            current_widget = self.content_area.currentWidget()

            if current_widget == target_widget:
                # Still ensure sidebar state is correct even if page is same
                # return # DON'T RETURN EARLY - Ensure sidebar state update
                pass

            # 🔥 Perform the Switch
            self.content_area.setCurrentWidget(target_widget)

            # 🔥 System 2.0 Transition: Fade-in Animation
            try:
                self.animation_manager.fade_in(target_widget, duration=250)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Could not apply fade-in animation: {e}")

            # Always show Sidebar in Professional Mode
            self.sidebar.show()

            # Sync sidebar active state
            self.sidebar.blockSignals(True)
            try:
                if page_name == "dashboard":
                    self.sidebar.set_active("home")
                else:
                    self.sidebar.set_active(page_name)
            finally:
                self.sidebar.blockSignals(False)

            # 🔥 ذكي: تشغيل/إيقاف dashboard_refresh_timer حسب الصفحة المعروضة
            if hasattr(self, "dashboard_refresh_timer"):
                try:
                    if page_name == "dashboard" and not self.dashboard_refresh_timer.isActive():
                        self.dashboard_refresh_timer.start()
                    elif page_name != "dashboard" and self.dashboard_refresh_timer.isActive():
                        self.dashboard_refresh_timer.stop()
                except (AttributeError, RuntimeError):
                    pass

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تبديل الصفحة '{page_name}': {e}")
            import traceback

            if self.logger:
                self.logger.error(traceback.format_exc())

    def _build_page(self, page_name: str) -> Optional[QWidget]:
        """
        بناء صفحة معينة عند الطلب (Lazy Loading)

        Args:
            page_name: اسم الصفحة

        Returns:
            QWidget: الصفحة المبنية أو None في حالة الفشل
        """
        # تتبع ما إذا تم إيقاف المؤقت (لإعادة تشغيله في finally)
        timer_was_stopped = False
        heavy_pages = ["inventory", "sales", "purchases", "payments"]  # noqa: F841

        try:
            if self.logger:
                self.logger.debug(f"🔨 بدء بناء الصفحة '{page_name}'...")

            page_widget = None

            if page_name == "dashboard":
                page_widget = self.create_dashboard_tab()
            elif page_name == "inventory":
                # 🛑 إيقاف مراقب الجلسة مؤقتاً لتوفير موارد قاعدة البيانات
                if (
                    hasattr(self, "session_monitor_timer")
                    and self.session_monitor_timer
                    and self.session_monitor_timer.isActive()
                ):
                    if self.logger:
                        self.logger.debug("⏸️ إيقاف session_monitor_timer مؤقتاً أثناء تحميل المخزون")
                    self.session_monitor_timer.stop()
                    timer_was_stopped = True

                # ⚠️ CRITICAL: InventoryTableModel يتم إنشاؤه هنا فقط (Lazy Loading)
                page_widget = self.create_inventory_tab()
            elif page_name == "sales":
                # 🛑 إيقاف مراقب الجلسة مؤقتاً لتوفير موارد قاعدة البيانات
                if (
                    hasattr(self, "session_monitor_timer")
                    and self.session_monitor_timer
                    and self.session_monitor_timer.isActive()
                ):
                    if self.logger:
                        self.logger.debug("⏸️ إيقاف session_monitor_timer مؤقتاً أثناء تحميل المبيعات")
                    self.session_monitor_timer.stop()
                    timer_was_stopped = True
                page_widget = self.create_sales_tab()
            elif page_name == "purchases":
                # 🛑 إيقاف مراقب الجلسة مؤقتاً لتوفير موارد قاعدة البيانات
                if (
                    hasattr(self, "session_monitor_timer")
                    and self.session_monitor_timer
                    and self.session_monitor_timer.isActive()
                ):
                    if self.logger:
                        self.logger.debug("⏸️ إيقاف session_monitor_timer مؤقتاً أثناء تحميل المشتريات")
                    self.session_monitor_timer.stop()
                    timer_was_stopped = True
                page_widget = self.create_purchases_tab()
            elif page_name == "payments":
                # 🛑 إيقاف مراقب الجلسة مؤقتاً لتوفير موارد قاعدة البيانات
                if (
                    hasattr(self, "session_monitor_timer")
                    and self.session_monitor_timer
                    and self.session_monitor_timer.isActive()
                ):
                    if self.logger:
                        self.logger.debug("⏸️ إيقاف session_monitor_timer مؤقتاً أثناء تحميل المدفوعات")
                    self.session_monitor_timer.stop()
                    timer_was_stopped = True
                page_widget = self.create_payments_tab()
            elif page_name == "reports":
                page_widget = self.create_reports_tab()
            elif page_name == "contacts":
                page_widget = self.create_contacts_tab()
            elif page_name == "settings":
                page_widget = self.create_settings_tab()
            elif page_name == "performance":
                page_widget = self.create_performance_tab()
            elif page_name == "ai_prediction":
                page_widget = self.create_ai_prediction_tab()
            elif page_name == "workflow":
                page_widget = self.create_workflow_tab()
            elif page_name == "warehouse":
                page_widget = self.create_warehouse_tab()
            else:
                if self.logger:
                    self.logger.warning(f"صفحة غير معروفة: {page_name}")
                return None

            if page_widget:
                if self.logger:
                    self.logger.debug(f"✅ تم بناء الصفحة '{page_name}' بنجاح")
                return page_widget
            else:
                if self.logger:
                    self.logger.error(f"❌ دالة create_{page_name}_tab() أرجعت None")
                return None

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            if self.logger:
                self.logger.error(f"❌ خطأ في بناء الصفحة '{page_name}': {e}")
                self.logger.error(f"تفاصيل الخطأ:\n{error_details}")
            else:
                # Fallback: استخدام logger افتراضي إذا لم يكن متاحاً

                logging.error(
                    f"❌ خطأ في بناء الصفحة '{page_name}': {e}\nتفاصيل الخطأ:\n{error_details}",
                    exc_info=True,
                )
            return None
        finally:
            # ✅ Safety Net: إعادة تشغيل مراقب الجلسة مضمونة 100% حتى لو حدث خطأ
            # (سيتم إعادة التشغيل مرة أخرى في دوال التحميل لكن هذا يضمن عدم الموت)
            if timer_was_stopped and hasattr(self, "session_monitor_timer") and self.session_monitor_timer:
                if not self.session_monitor_timer.isActive():
                    if self.logger:
                        self.logger.debug(
                            f"▶️ إعادة تشغيل session_monitor_timer (Safety Net في _build_page بعد {page_name})"
                        )
                    self.session_monitor_timer.start(60000)  # كل 60 ثانية

    def create_ai_prediction_tab(self) -> QWidget:
        """إنشاء تبويب التنبؤات الذكية"""
        try:
            win = AIPredictionsWindow(self.db_manager, parent=self)
            # نأخذ الـ central widget مع إمكانية إضافة الـ toolbar لاحقاً إذا لزم الأمر
            content = win.centralWidget()
            content.setParent(self)
            return content
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating AI tab: {e}")
            return QLabel(f"خطأ في تحميل واجهة التنبؤات: {e}")

    def create_workflow_tab(self) -> QWidget:
        """إنشاء تبويب مصمم سير العمل"""
        try:
            win = WorkflowDesignerWindow(self.db_manager, parent=self)
            content = win.centralWidget()
            content.setParent(self)
            return content
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating Workflow tab: {e}")
            return QLabel(f"خطأ في تحميل واجهة سير العمل: {e}")

    def create_warehouse_tab(self) -> QWidget:
        """إنشاء تبويب إدارة المستودعات"""
        try:
            win = WarehouseManagementWindow(self.db_manager, parent=self)
            content = win.centralWidget()
            content.setParent(self)
            return content
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating Warehouse tab: {e}")
            return QLabel(f"خطأ في تحميل واجهة المستودعات: {e}")

    def create_dashboard_tab(self) -> QWidget:
        """إنشاء تبويب الصفحة الرئيسية"""
        # 🔥 الربط العصبي: ربط الإشارات لتحديث تلقائي (مع منع الاتصالات المكررة)
        try:
            # فك الاتصال أولاً لتجنب الاتصالات المكررة (إذا كانت موجودة)
            # استخدام RuntimeWarning suppression لتجنب التحذيرات
            import warnings

            from src.core.signals import signals

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    signals.sales_updated.disconnect(self.refresh_dashboard_stats)
                except (TypeError, RuntimeError):
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")
                try:
                    signals.inventory_updated.disconnect(self.refresh_dashboard_stats)
                except (TypeError, RuntimeError):
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")
                try:
                    signals.purchases_updated.disconnect(self.refresh_dashboard_stats)
                except (TypeError, RuntimeError):
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")
                try:
                    signals.payments_updated.disconnect(self.refresh_dashboard_stats)
                except (TypeError, RuntimeError):
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")

            # ربط الإشارات
            signals.sales_updated.connect(self.refresh_dashboard_stats)
            signals.inventory_updated.connect(self.refresh_dashboard_stats)
            signals.purchases_updated.connect(self.refresh_dashboard_stats)
            signals.payments_updated.connect(self.refresh_dashboard_stats)

            if self.logger:
                self.logger.debug("✅ تم ربط إشارات الداشبورد بنجاح")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ فشل ربط إشارات الداشبورد: {e}")

        # إنشاء QScrollArea للتمرير
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # المحتوى الرئيسي
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # عنوان القسم مع أزرار التحكم المتقدمة
        header_frame = QFrame()
        header_frame.setStyleSheet("")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel(self.i18n.get_message("main_dashboard"))
        title.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {Colors.TEXT_BRIGHT}; font-family: 'Cairo'; letter-spacing: 0.3px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # أزرار الفترة الزمنية
        period_label = QLabel(self.i18n.get_message("period") + ":")
        period_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: 600; font-size: 13px; font-family: 'Cairo';")
        header_layout.addWidget(period_label)

        self.dashboard_period_combo = QComboBox()
        self.dashboard_period_combo.addItems(["اليوم", "أسبوع", "شهر", "3 أشهر", "سنة", "الكل"])
        self.dashboard_period_combo.setCurrentText("أسبوع")
        self.dashboard_period_combo.setMinimumWidth(120)
        self.dashboard_period_combo.setStyleSheet("")
        self.dashboard_period_combo.currentTextChanged.connect(self.refresh_dashboard_data)
        header_layout.addWidget(self.dashboard_period_combo)

        # زر التحديث التلقائي
        auto_refresh_check = QCheckBox("تحديث تلقائي")
        auto_refresh_check.setChecked(True)
        auto_refresh_check.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: 600; font-family: 'Cairo';")
        auto_refresh_check.stateChanged.connect(self.toggle_auto_refresh)
        header_layout.addWidget(auto_refresh_check)

        refresh_btn = QPushButton(self.i18n.get_message("refresh"))
        refresh_btn.setMinimumHeight(35)
        refresh_btn.setMinimumWidth(100)
        refresh_btn.setStyleSheet("")
        refresh_btn.clicked.connect(self.refresh_dashboard_data)
        header_layout.addWidget(refresh_btn)

        layout.addWidget(header_frame)

        # --- Glass KPI Grid (System 2.0) ---
        kpi_container = QWidget()
        kpi_layout = QGridLayout(kpi_container)
        kpi_layout.setContentsMargins(15, 0, 15, 10)
        kpi_layout.setSpacing(20)

        # Glass KPI Cards are created via self._create_glass_kpi method

        # --- Vision 2030 AI Insights Widget ---

        insights_frame = QFrame()
        insights_frame.setObjectName("AIInsightsFrame")
        # insights_frame.setStyleSheet("...")
        insights_layout = QHBoxLayout(insights_frame)

        ai_icon = QLabel("🤖")
        ai_icon.setStyleSheet("font-size: 24px;")

        self.ai_insight_label = QLabel("جاري تحليل البيانات... (Vision 2030 AI)")
        self.ai_insight_label.setStyleSheet("color: #e2e8f0; font-style: italic; font-size: 14px;")
        self.ai_insight_label.setWordWrap(True)
        # إضافة المساعد الذكي
        try:
            from src.ui.widgets.smart_assistant_widget import SmartAssistantWidget

            self.smart_assistant_widget = SmartAssistantWidget(self)
            self.smart_assistant_widget.hide()  # Start hidden
            self.smart_assistant_widget.command_received.connect(self.handle_ai_command)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to init Smart Assistant UI: {e}")
            self.smart_assistant_widget = None

        # زر المساعد الذكي العائم
        self.ai_action_btn = QPushButton("✨ تحليلات مفصلة", self)
        # self.ai_action_btn.setStyleSheet("...")
        self.ai_action_btn.clicked.connect(self.handle_ai_action)

        insights_layout.addWidget(ai_icon)
        insights_layout.addWidget(self.ai_insight_label, 1)
        insights_layout.addWidget(self.ai_action_btn)

        layout.addWidget(insights_frame)
        # --------------------------------------

        # Add Cards to Grid
        kpi_layout.addWidget(
            self._create_glass_kpi("total_sales", "المبيعات", "0 د.ج", "#6c9cef", "💰"),
            0,
            0,
        )
        kpi_layout.addWidget(
            self._create_glass_kpi("total_revenue", "الإيرادات", "0 د.ج", "#22d3ee", "📈"),
            0,
            1,
        )
        kpi_layout.addWidget(
            self._create_glass_kpi("total_profit", "الأرباح", "0 د.ج", "#4ade80", "💵"),
            0,
            2,
        )
        kpi_layout.addWidget(
            self._create_glass_kpi("total_orders", "الطلبات", "0", "#a78bfa", "🛍️"),
            0,
            3,
        )

        layout.addWidget(insights_frame)
        # --------------------------------------

        # --- Phase 5: Adaptive Suggestions Widget ---
        adaptive_frame = QFrame()
        # adaptive_frame.setStyleSheet("""
        #     background: rgba(255, 255, 255, 0.05);
        #     border-radius: 10px;
        #     border: 1px dashed rgba(255, 255, 255, 0.3);
        # """)
        adaptive_layout = QHBoxLayout(adaptive_frame)
        adaptive_layout.setContentsMargins(10, 5, 10, 5)

        adaptive_label = QLabel("🧠 اقتراحات ذكية:")
        adaptive_label.setStyleSheet(f"color: {Colors.ACCENT_AMBER_LIGHT}; font-weight: bold;")
        adaptive_layout.addWidget(adaptive_label)

        # Dynamic Suggestions
        if hasattr(self, "gamification_service"):
            top_actions = self.gamification_service.get_top_actions(3)
            if top_actions:
                for action in top_actions:
                    # Parse action name (e.g. "nav_sales")
                    clean_name = action.replace("nav_", "")
                    display_map = {
                        "sales": "💰 مبيعات جديدة",
                        "inventory": "📦 فحص المخزون",
                        "reports": "📊 التقارير",
                        "purchases": "🚚 مشتريات",
                        "settings": "⚙️ الإعدادات",
                    }
                    btn_text = display_map.get(clean_name, clean_name.capitalize())

                    s_btn = QPushButton(btn_text)
                    s_btn.setCursor(Qt.PointingHandCursor)
                    s_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: #451a03;
                            color: {Colors.ACCENT_AMBER_LIGHT};
                            border: 1px solid {Colors.ACCENT_AMBER_LIGHT};
                            border-radius: 15px;
                            padding: 3px 12px;
                            font-size: 12px;
                        }}
                        QPushButton:hover {{
                            background-color: #78350f;
                        }}
                    """)
                    # Use closure to capture loop variable
                    s_btn.clicked.connect(lambda checked, name=clean_name: self.switch_page(name))
                    adaptive_layout.addWidget(s_btn)
            else:
                layout_hint = QLabel("(سيظهر هنا اختصاراتك المفضلة قريباً)")
                layout_hint.setStyleSheet("color: #9ca3af; font-size: 11px;")
                adaptive_layout.addWidget(layout_hint)

        adaptive_layout.addStretch()
        layout.addWidget(adaptive_frame)
        # ---------------------------------------------

        # Add Cards to Grid

        # KPIs المخزون
        inventory_kpis = [
            ("total_products", "📦 إجمالي المنتجات", "#3498db", ""),
            ("total_stock_value", "💎 قيمة المخزون", "#27ae60", ""),
            ("low_stock_items", "⚠️ مخزون منخفض", "#f39c12", "↓"),
            ("out_of_stock_items", "🔴 منتجات نفدت", "#e74c3c", "↓"),
        ]

        # تعريف KPIs المالية (تم إضافتها لتجنب خطأ undefined)
        financial_kpis = [
            ("daily_revenue", "إيراد اليوم", "#10b981", "↑"),
            ("daily_expenses", "مصروفات اليوم", "#ef4444", "↓"),
            ("net_profit", "صافي الربح", "#3b82f6", "↑"),
            ("avg_basket", "متوسط السلة", f"{Colors.ACCENT_AMBER}", "-"),
        ]

        # إضافة KPIs المالية (ملخص نصي)
        summary_group = QGroupBox("💰 الملخص المالي")
        summary_group.setStyleSheet(
            "QGroupBox { border: 1px solid #333; border-radius: 8px; margin-top: 10px; font-weight: bold; color: white; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"  # noqa: E501
        )
        summary_layout = QHBoxLayout(summary_group)
        summary_layout.setContentsMargins(15, 15, 15, 15)
        summary_layout.setSpacing(20)

        for key, title_text, color, trend in financial_kpis:
            container = self._create_kpi_card(key, title_text, color, trend)

            summary_layout.addWidget(container)

        summary_layout.addStretch()
        layout.addWidget(summary_group)

        # KPIs المخزون
        inventory_summary_group = QGroupBox("📦 مؤشرات المخزون")
        inventory_summary_group.setStyleSheet(summary_group.styleSheet())
        inventory_summary_layout = QHBoxLayout(inventory_summary_group)
        inventory_summary_layout.setContentsMargins(15, 15, 15, 15)
        inventory_summary_layout.setSpacing(20)

        for key, title_text, color, trend in inventory_kpis:
            container = self._create_kpi_card(key, title_text, color, trend)
            inventory_summary_layout.addWidget(container)

        inventory_summary_layout.addStretch()
        layout.addWidget(inventory_summary_group)

        summary_layout.addStretch()
        layout.addWidget(summary_group)

        # الرسم البياني التفاعلي للمبيعات (PyQtGraph)
        try:
            from src.ui.widgets.sales_chart import SalesChartWidget

            self.sales_chart = SalesChartWidget()
            self.sales_chart.setMinimumHeight(350)
            layout.addWidget(self.sales_chart)
            if self.logger:
                self.logger.info("✅ تم إضافة الرسم البياني التفاعلي للمبيعات (PyQtGraph)")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"تعذر إضافة الرسم البياني: {e}")
            # Fallback: رسالة بدلاً من الرسم
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_layout.setSpacing(10)
            error_layout.setContentsMargins(15, 15, 15, 15)

            error_label = QLabel(self.i18n.get_message("chart_load_error"))
            error_label.setWordWrap(True)
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(
                "color: #e74c3c; padding: 15px; background-color: #fff3cd; border-radius: 5px; font-size: 13px;"
            )
            error_layout.addWidget(error_label)

            # إضافة زر للمساعدة في التثبيت
            help_btn = QPushButton(self.i18n.get_message("show_installation_instructions"))
            help_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            help_btn.clicked.connect(
                lambda: self.notify.show_info(
                    self.i18n.get_message("chart_load_error_title"),
                    self.i18n.get_message("chart_load_error_details"),
                )
            )
            error_layout.addWidget(help_btn, alignment=Qt.AlignCenter)

            layout.addWidget(error_widget)

        # الرسوم البيانية المتقدمة
        charts_group = QGroupBox("📈 التحليلات والرسوم البيانية")
        charts_group.setStyleSheet("")
        charts_main_layout = QVBoxLayout(charts_group)
        charts_main_layout.setContentsMargins(10, 15, 10, 10)
        charts_main_layout.setSpacing(15)

        # صف الرسوم البيانية الأولى
        charts_row1 = QHBoxLayout()
        charts_row1.setSpacing(15)

        # رسم بياني للمبيعات (خط)
        sales_line_chart_view = QChartView()
        sales_line_chart_view.setRenderHint(QPainter.Antialiasing)
        sales_line_chart_view.setMinimumHeight(300)
        sales_line_chart_view.setStyleSheet("")
        self.dashboard_sales_line_chart = sales_line_chart_view
        charts_row1.addWidget(sales_line_chart_view, 2)

        # رسم بياني للمقارنة (إيرادات vs مصروفات)
        revenue_expense_chart_view = QChartView()
        revenue_expense_chart_view.setRenderHint(QPainter.Antialiasing)
        revenue_expense_chart_view.setMinimumHeight(300)
        revenue_expense_chart_view.setStyleSheet("")
        self.dashboard_revenue_expense_chart = revenue_expense_chart_view
        charts_row1.addWidget(revenue_expense_chart_view, 2)

        charts_main_layout.addLayout(charts_row1)

        # صف الرسوم البيانية الثانية
        charts_row2 = QHBoxLayout()
        charts_row2.setSpacing(15)

        # رسم بياني لتوزيع المخزون (دائري)
        stock_chart_view = QChartView()
        stock_chart_view.setRenderHint(QPainter.Antialiasing)
        stock_chart_view.setMinimumHeight(300)
        stock_chart_view.setStyleSheet("")
        self.dashboard_stock_chart = stock_chart_view
        charts_row2.addWidget(stock_chart_view, 1)

        # رسم بياني لأفضل المنتجات (أعمدة)
        top_products_chart_view = QChartView()
        top_products_chart_view.setRenderHint(QPainter.Antialiasing)
        top_products_chart_view.setMinimumHeight(300)
        top_products_chart_view.setStyleSheet("")
        self.dashboard_top_products_chart = top_products_chart_view
        charts_row2.addWidget(top_products_chart_view, 1)

        charts_main_layout.addLayout(charts_row2)

        layout.addWidget(charts_group)

        # تحديث الرسوم البيانية مباشرة بعد بناء الصفحة (حتى لو كانت فارغة)
        QTimer.singleShot(200, lambda: self._update_dashboard_charts_initial())

        # تنبيهات المخزون وآخر العمليات
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)

        # تنبيهات المخزون
        alerts_group = QGroupBox("تنبيهات المخزون")
        alerts_group.setStyleSheet("")
        alerts_layout = QVBoxLayout(alerts_group)
        alerts_layout.setContentsMargins(10, 15, 10, 10)

        self.dashboard_alerts_table = AnimatedTableWidget()
        self.dashboard_alerts_table.setColumnCount(4)
        self.dashboard_alerts_table.setHorizontalHeaderLabels(["المنتج", "الحالة", "الكمية", "الرسالة"])
        self.dashboard_alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dashboard_alerts_table.horizontalHeader().setMinimumSectionSize(120)
        self.dashboard_alerts_table.horizontalHeader().setDefaultSectionSize(150)
        self.dashboard_alerts_table.horizontalHeader().setStretchLastSection(True)
        self.dashboard_alerts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dashboard_alerts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dashboard_alerts_table.setAlternatingRowColors(True)
        self.dashboard_alerts_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.dashboard_alerts_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.dashboard_alerts_table.setMinimumHeight(300)
        self.dashboard_alerts_table.setStyleSheet("")
        alerts_layout.addWidget(self.dashboard_alerts_table)
        bottom_layout.addWidget(alerts_group, 1)

        # آخر العمليات
        activities_group = QGroupBox("آخر العمليات")
        activities_group.setStyleSheet("")
        activities_layout = QVBoxLayout(activities_group)
        activities_layout.setContentsMargins(10, 15, 10, 10)

        self.dashboard_activities_table = AnimatedTableWidget()
        self.dashboard_activities_table.setColumnCount(6)
        self.dashboard_activities_table.setHorizontalHeaderLabels(
            ["التاريخ", "الوقت", "النوع", "الوصف", "المستخدم", "الحالة"]
        )
        self.dashboard_activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dashboard_activities_table.horizontalHeader().setMinimumSectionSize(120)
        self.dashboard_activities_table.horizontalHeader().setDefaultSectionSize(150)
        self.dashboard_activities_table.horizontalHeader().setStretchLastSection(True)
        self.dashboard_activities_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dashboard_activities_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dashboard_activities_table.setAlternatingRowColors(True)
        self.dashboard_activities_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.dashboard_activities_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.dashboard_activities_table.setMinimumHeight(300)
        self.dashboard_activities_table.setStyleSheet("")
        # فلاتر العمليات
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(10)

        filter_label = QLabel(self.i18n.get_message("filter") + ":")
        filter_label.setStyleSheet(f"font-weight: bold; color: {Colors.TEXT_BRIGHT};")
        filters_layout.addWidget(filter_label)

        self.dashboard_activity_filter = QComboBox()
        self.dashboard_activity_filter.addItems(["الكل", "مبيعات", "مشتريات", "حركة مخزون"])
        self.dashboard_activity_filter.currentTextChanged.connect(self.update_dashboard_activities_table)
        filters_layout.addWidget(self.dashboard_activity_filter)

        filters_layout.addStretch()
        activities_layout.addLayout(filters_layout)

        activities_layout.addWidget(self.dashboard_activities_table)
        bottom_layout.addWidget(activities_group, 1)

        layout.addLayout(bottom_layout)

        # جداول التحليلات المتقدمة
        analytics_layout = QHBoxLayout()
        analytics_layout.setSpacing(15)

        # أفضل العملاء
        top_customers_group = QGroupBox("🏆 أفضل العملاء")
        top_customers_group.setStyleSheet("")
        top_customers_layout = QVBoxLayout(top_customers_group)
        top_customers_layout.setContentsMargins(10, 15, 10, 10)

        self.dashboard_top_customers_table = AnimatedTableWidget()
        self.dashboard_top_customers_table.setColumnCount(4)
        self.dashboard_top_customers_table.setHorizontalHeaderLabels(
            ["الترتيب", "اسم العميل", "عدد المشتريات", "إجمالي الإنفاق"]
        )
        self.dashboard_top_customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dashboard_top_customers_table.horizontalHeader().setMinimumSectionSize(120)
        self.dashboard_top_customers_table.horizontalHeader().setDefaultSectionSize(150)
        self.dashboard_top_customers_table.horizontalHeader().setStretchLastSection(True)
        self.dashboard_top_customers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dashboard_top_customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dashboard_top_customers_table.setAlternatingRowColors(True)
        self.dashboard_top_customers_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.dashboard_top_customers_table.setMinimumHeight(250)
        self.dashboard_top_customers_table.setStyleSheet("")
        top_customers_layout.addWidget(self.dashboard_top_customers_table)
        analytics_layout.addWidget(top_customers_group, 1)

        # أفضل المنتجات
        top_products_group = QGroupBox("⭐ أفضل المنتجات مبيعاً")
        top_products_group.setStyleSheet("")
        top_products_layout = QVBoxLayout(top_products_group)
        top_products_layout.setContentsMargins(10, 15, 10, 10)

        self.dashboard_top_products_table = AnimatedTableWidget()
        self.dashboard_top_products_table.setColumnCount(4)
        self.dashboard_top_products_table.setHorizontalHeaderLabels(
            ["الترتيب", "اسم المنتج", "الكمية المباعة", "إجمالي المبيعات"]
        )
        self.dashboard_top_products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dashboard_top_products_table.horizontalHeader().setMinimumSectionSize(120)
        self.dashboard_top_products_table.horizontalHeader().setDefaultSectionSize(150)
        self.dashboard_top_products_table.horizontalHeader().setStretchLastSection(True)
        self.dashboard_top_products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dashboard_top_products_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dashboard_top_products_table.setAlternatingRowColors(True)
        self.dashboard_top_products_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.dashboard_top_products_table.setMinimumHeight(250)
        self.dashboard_top_products_table.setStyleSheet("")
        top_products_layout.addWidget(self.dashboard_top_products_table)
        analytics_layout.addWidget(top_products_group, 1)

        layout.addLayout(analytics_layout)

        # إحصائيات إضافية متقدمة
        advanced_stats_group = QGroupBox("📈 إحصائيات متقدمة")
        advanced_stats_group.setStyleSheet("")
        advanced_stats_layout = QHBoxLayout(advanced_stats_group)
        advanced_stats_layout.setContentsMargins(15, 15, 15, 15)
        advanced_stats_layout.setSpacing(20)

        advanced_stats_items = [
            ("avg_daily_sales", "📊 متوسط المبيعات اليومية", "#16a085"),
            ("conversion_rate", "🎯 معدل التحويل", "#8e44ad"),
            ("customer_retention", "👥 معدل الاحتفاظ", "#2980b9"),
            ("inventory_turnover", "🔄 معدل دوران المخزون", "#d35400"),
        ]

        self.dashboard_advanced_stats_labels = {}
        for key, title_text, color in advanced_stats_items:
            container = self._create_kpi_card(key, title_text, color, "")
            advanced_stats_layout.addWidget(container)

        advanced_stats_layout.addStretch()
        layout.addWidget(advanced_stats_group)

        layout.addStretch()

        # وضع المحتوى في QScrollArea
        scroll_area.setWidget(tab)

        # تحميل البيانات الأولية
        QTimer.singleShot(100, self.refresh_dashboard_data)

        # مؤقت التحديث التلقائي
        self.dashboard_refresh_timer = QTimer(self)
        self.dashboard_refresh_timer.timeout.connect(self.refresh_dashboard_data)
        self.dashboard_refresh_timer.setInterval(60000)  # 60 ثانية (لا يُفعَّل تلقائياً — يُفعَّل عند فتح الداشبورد فقط)
        # يتم تفعيله عند التبديل لصفحة الداشبورد لتجنب استهلاك الموارد في الخلفية

        return scroll_area

    class InteractiveCard(QFrame):
        """
        بطاقة تفاعلية متطورة (Quantum Card)
        تتفاعل مع حركة الماوس وتوفر تأثيرات بصرية متقدمة
        """

        def __init__(self, parent=None, color="#3498db", animation_manager=None):
            super().__init__(parent)
            self.color = color
            self.animation_manager = animation_manager
            self.setObjectName("kpiCard")
            self.setFrameStyle(QFrame.StyledPanel)

            # تأثير الظل (Glow)
            from PySide6.QtWidgets import QGraphicsDropShadowEffect

            self.shadow = QGraphicsDropShadowEffect(self)
            self.shadow.setBlurRadius(20)
            self.shadow.setColor(QColor(color))
            self.shadow.setOffset(0, 0)
            self.shadow.setEnabled(False)  # تفعيل عند التحويم فقط
            self.setGraphicsEffect(self.shadow)

        def enterEvent(self, event):
            # تشغيل تأثير الـ Scale والـ Glow
            if self.animation_manager:
                self.animation_manager.scale_animation(self, start_scale=1.0, end_scale=1.05, duration=200)

            self.shadow.setEnabled(True)
            self.setStyleSheet("""
                QFrame#kpiCard {{
                    background: qradialgradient(cx:0.5, cy:0.5, radius:1.5, fx:0.5, fy:0.5,
                        stop:0 #0c4a6e, stop:1 #0f172a);
                    border: 1px solid {self.color};
                    border-left: 4px solid {self.color};
                }}
            """)
            super().enterEvent(event)

        def leaveEvent(self, event):
            # إعادة الحجم والستايل
            if self.animation_manager:
                self.animation_manager.scale_animation(self, start_scale=1.05, end_scale=1.0, duration=200)

            self.shadow.setEnabled(False)
            self.setStyleSheet("""
                QFrame#kpiCard {{
                    border-left: 3px solid {self.color};
                }}
            """)
            super().leaveEvent(event)

    def _create_kpi_card(self, key, title_text, color, trend=""):
        """إنشاء بطاقة KPI احترافية تفاعلية"""
        # استخدام الكلاس الداخلي للتفاعل
        container = self.InteractiveCard(parent=None, color=color, animation_manager=self.animation_manager)

        # الستايل الأولي
        container.setStyleSheet("""
            QFrame#kpiCard {{
                border-left: 3px solid {color};
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(18, 15, 18, 15)
        container_layout.setSpacing(10)

        # العنوان مع الاتجاه
        title_layout = QHBoxLayout()
        title_label = QLabel(title_text)
        title_label.setStyleSheet(f"color: {Colors.TEXT_BRIGHT}; font-size: 15px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        if trend:
            trend_label = QLabel(trend)
            trend_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
            title_layout.addWidget(trend_label)

        container_layout.addLayout(title_layout)

        # القيمة
        value_label = QLabel("-")
        value_label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")
        container_layout.addWidget(value_label)

        # التغيير (سيتم تحديثه لاحقاً)
        change_label = QLabel("")
        change_label.setStyleSheet("color: rgb(127, 140, 141); font-size: 12px;")
        container_layout.addWidget(change_label)

        container_layout.addStretch()

        if not hasattr(self, "dashboard_summary_labels"):
            self.dashboard_summary_labels = {}
        if not hasattr(self, "dashboard_trend_labels"):
            self.dashboard_trend_labels = {}

        self.dashboard_summary_labels[key] = value_label
        self.dashboard_trend_labels[key] = change_label

        return container

    def toggle_auto_refresh(self, state):
        """تفعيل/تعطيل التحديث التلقائي"""
        if hasattr(self, "dashboard_refresh_timer"):
            if state == Qt.Checked:
                self.dashboard_refresh_timer.start()
            else:
                self.dashboard_refresh_timer.stop()

    def _db_fetch_one(self, query, params=()):
        """Helper: run a SELECT and return a single row tuple, or None."""
        try:
            if hasattr(self.db_manager, "connection") and self.db_manager.connection:
                cursor = self.db_manager.connection.execute(query, params)
                return cursor.fetchone()
            if hasattr(self.db_manager, "fetch_one"):
                return self.db_manager.fetch_one(query, params)
        except Exception:
            pass
        return None

    def refresh_dashboard_stats(self):
        """
        🛠️ محرك إحصائيات الداشبورد - استعلامات SQL سريعة جداً
        تقوم بجلب الأرقام الملخصة للصفحة الرئيسية باستخدام Aggregation Queries
        """
        try:
            if not self.db_manager:
                if self.logger:
                    self.logger.warning("db_manager غير متاح - تخطي تحديث إحصائيات Dashboard")
                return

            # استعلامات SQL سريعة جداً (COUNT/SUM فقط - لا جلب بيانات تفصيلية)
            query_stats = """
            SELECT
                (SELECT COUNT(*) FROM products WHERE COALESCE(is_active, 1) = 1) as total_products,
                (SELECT COALESCE(SUM(selling_price * current_stock), 0) FROM products WHERE COALESCE(is_active, 1) = 1) as total_stock_value,  # noqa: E501
                (SELECT COUNT(*) FROM products WHERE current_stock < min_stock AND current_stock > 0 AND COALESCE(is_active, 1) = 1) as low_stock_items,  # noqa: E501
                (SELECT COUNT(*) FROM products WHERE current_stock <= 0 AND COALESCE(is_active, 1) = 1) as out_of_stock_items,  # noqa: E501
                (SELECT COUNT(*) FROM sales WHERE status != 'ملغية' AND status != 'cancelled') as total_sales_count,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE status != 'ملغية' AND status != 'cancelled') as total_sales_amount,  # noqa: E501
                (SELECT COALESCE(SUM(paid_amount), 0) FROM sales WHERE status != 'ملغية' AND status != 'cancelled') as total_paid_amount,  # noqa: E501
                (SELECT COALESCE(SUM(total_amount - paid_amount), 0) FROM sales WHERE status != 'ملغية' AND status != 'cancelled') as total_remaining_amount  # noqa: E501
            """

            row = None
            if self.db_manager and hasattr(self.db_manager, "connection") and self.db_manager.connection:
                cursor = self.db_manager.connection.execute(query_stats)
                row = cursor.fetchone()
            else:
                import sqlite3

                db_path = getattr(self.db_manager, "db_path", None) or (
                    self.config_manager.get_database_path() if self.config_manager else "database.db"
                )
                conn = sqlite3.connect(db_path, timeout=5.0)
                conn.execute("PRAGMA query_only=true")
                cursor = conn.cursor()
                cursor.execute(query_stats)
                row = cursor.fetchone()
                conn.close()
            if not row:
                return

            # معالجة القيم الفارغة (None) وتحويلها لأصفار
            result = {
                "total_products": row[0] or 0,
                "total_stock_value": row[1] or 0.0,
                "low_stock_items": row[2] or 0,
                "out_of_stock_items": row[3] or 0,
                "total_sales_count": row[4] or 0,
                "total_sales_amount": row[5] or 0.0,
                "total_paid_amount": row[6] or 0.0,
                "total_remaining_amount": row[7] or 0.0,
            }

            total_products = int(result.get("total_products", 0) or 0)
            total_stock_value = float(result.get("total_stock_value", 0) or 0.0)
            low_stock_items = int(result.get("low_stock_items", 0) or 0)
            out_of_stock_items = int(result.get("out_of_stock_items", 0) or 0)
            total_sales_count = int(result.get("total_sales_count", 0) or 0)
            total_sales_amount = float(result.get("total_sales_amount", 0) or 0.0)
            total_paid_amount = float(result.get("total_paid_amount", 0) or 0.0)  # noqa: F841
            total_remaining_amount = float(result.get("total_remaining_amount", 0) or 0.0)  # noqa: F841

            # حساب متوسط الطلب
            avg_order = total_sales_amount / total_sales_count if total_sales_count > 0 else 0.0

            # حساب صافي الربح من قاعدة البيانات (مبيعات - تكلفة المشتريات)
            try:
                profit_query = """
                    SELECT COALESCE(SUM(
                        si.quantity * (si.unit_price - COALESCE(p.cost_price, si.unit_price * 0.7))
                    ), 0)
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    JOIN products p ON si.product_id = p.id
                    WHERE s.status NOT IN ('ملغية', 'cancelled', 'draft')
                """
                profit_result = None
                if hasattr(self.db_manager, "execute_query"):
                    profit_result = self.db_manager.execute_query(profit_query)
                elif hasattr(self.db_manager, "fetch_all"):
                    profit_result = self.db_manager.fetch_all(profit_query)
                if profit_result and profit_result[0]:
                    total_profit = float(profit_result[0][0])
                else:
                    total_profit = 0.0
            except Exception:
                total_profit = 0.0

            # ------------------------------------------------
            # استعلامات إضافية للـ KPIs المالية المتقدمة
            # ------------------------------------------------
            daily_expenses = 0.0
            avg_basket = 0.0
            daily_revenue = 0.0
            net_profit = 0.0
            avg_daily_sales = 0.0
            customer_retention = 0.0
            inventory_turnover = 0.0

            try:
                # مصروفات اليوم
                expenses_query = """
                    SELECT COALESCE(SUM(total_amount), 0)
                    FROM purchases WHERE DATE(purchase_date) = DATE('now')
                """
                expenses_result = self._db_fetch_one(expenses_query)
                daily_expenses = float(expenses_result[0]) if expenses_result else 0.0

                # إيراد اليوم
                daily_revenue_query = """
                    SELECT COALESCE(SUM(total_amount), 0)
                    FROM sales WHERE DATE(sale_date) = DATE('now')
                      AND status NOT IN ('ملغية', 'cancelled', 'draft')
                """
                daily_rev_result = self._db_fetch_one(daily_revenue_query)
                daily_revenue = float(daily_rev_result[0]) if daily_rev_result else 0.0

                # صافي الربح اليومي
                net_profit = daily_revenue - daily_expenses

                # متوسط السلة
                basket_query = """
                    SELECT AVG(final_amount) FROM sales
                    WHERE status NOT IN ('cancelled', 'draft', 'ملغية')
                      AND final_amount > 0
                """
                basket_result = self._db_fetch_one(basket_query)
                avg_basket = float(basket_result[0]) if basket_result and basket_result[0] else 0.0

                # متوسط المبيعات اليومية (آخر 30 يوم)
                avg_daily_query = """
                    SELECT COALESCE(SUM(total_amount), 0) /
                           (julianday('now') - julianday(MIN(sale_date)) + 1)
                    FROM sales
                    WHERE sale_date >= date('now', '-30 days')
                      AND status NOT IN ('ملغية', 'cancelled', 'draft')
                """
                avg_daily_result = self._db_fetch_one(avg_daily_query)
                avg_daily_sales = float(avg_daily_result[0]) if avg_daily_result and avg_daily_result[0] else 0.0

                # معدل الاحتفاظ بالعملاء
                # (عملاء اشتروا هذا الشهر AND الشهر الماضي) / عملاء اشتروا الشهر الماضي
                retention_query = """
                    WITH last_month AS (
                        SELECT DISTINCT customer_id FROM sales
                        WHERE sale_date >= date('now', 'start of month', '-1 month')
                          AND sale_date <  date('now', 'start of month')
                          AND customer_id IS NOT NULL AND customer_id != ''
                          AND status NOT IN ('ملغية', 'cancelled', 'draft')
                    ),
                    this_month AS (
                        SELECT DISTINCT customer_id FROM sales
                        WHERE sale_date >= date('now', 'start of month')
                          AND customer_id IS NOT NULL AND customer_id != ''
                          AND status NOT IN ('ملغية', 'cancelled', 'draft')
                    )
                    SELECT
                        (SELECT COUNT(*) FROM last_month) as last_m,
                        (SELECT COUNT(*) FROM this_month) as this_m,
                        (SELECT COUNT(*) FROM last_month lm
                         WHERE EXISTS (SELECT 1 FROM this_month tm WHERE tm.customer_id = lm.customer_id)) as retained
                """
                retention_result = self._db_fetch_one(retention_query)
                if retention_result:
                    last_m = float(retention_result[0]) if retention_result[0] else 0
                    retained = float(retention_result[2]) if retention_result[2] else 0
                    customer_retention = (retained / last_m * 100) if last_m > 0 else 0.0

                # معدل دوران المخزون
                turnover_query = """
                    SELECT
                        COALESCE(SUM(si.quantity * COALESCE(p.cost_price, si.unit_price * 0.7)), 0) as cogs,
                        COALESCE(AVG(selling_price * current_stock), 1) as avg_inventory
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    JOIN sales s ON si.sale_id = s.id
                    WHERE s.status NOT IN ('ملغية', 'cancelled', 'draft')
                """
                turnover_result = self._db_fetch_one(turnover_query)
                if turnover_result and turnover_result[0] and turnover_result[1]:
                    cogs = float(turnover_result[0])
                    avg_inv = float(turnover_result[1])
                    inventory_turnover = cogs / avg_inv if avg_inv > 0 else 0.0

            except Exception as e:
                if self.logger:
                    self.logger.warning(f"فشل جلب KPIs إضافية: {e}")

            # ------------------------------------------------
            # جلب بيانات الرسم البياني (آخر 7 أيام)
            # ------------------------------------------------
            chart_days = []
            chart_amounts = []

            try:
                # استعلام لجلب مجموع المبيعات لكل يوم من الأيام الـ 7 الماضية
                query_chart = """
                SELECT
                    date(sale_date) as sale_date,
                    COALESCE(SUM(total_amount), 0) as daily_total
                FROM sales
                WHERE sale_date >= date('now', '-7 days')
                  AND status != 'ملغية'
                  AND status != 'cancelled'
                GROUP BY date(sale_date)
                ORDER BY date(sale_date) ASC
                """

                chart_results = None
                if hasattr(self.db_manager, "execute_query"):
                    chart_results = self.db_manager.execute_query(query_chart)
                elif hasattr(self.db_manager, "fetch_all"):
                    chart_results = self.db_manager.fetch_all(query_chart)

                if chart_results:
                    # إنشاء قائمة بجميع الأيام الـ 7 الماضية
                    today = date.today()
                    all_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

                    # إنشاء قاموس للبيانات المحمّلة
                    sales_by_date = {}
                    for row in chart_results:
                        if isinstance(row, dict):
                            sale_date = row.get("sale_date", "")
                            daily_total = float(row.get("daily_total", 0) or 0)
                        else:
                            sale_date = str(row[0]) if len(row) > 0 else ""
                            daily_total = float(row[1] if len(row) > 1 else 0) or 0.0

                        if sale_date:
                            sales_by_date[sale_date] = daily_total

                    # ملء البيانات (0 للأيام التي لا توجد فيها مبيعات)
                    chart_days = list(range(1, 8))  # [1, 2, 3, 4, 5, 6, 7]
                    chart_amounts = []

                    for day_str in all_days:
                        amount = sales_by_date.get(day_str, 0.0)
                        chart_amounts.append(float(amount))

                    if self.logger:
                        self.logger.debug(
                            f"تم جلب بيانات الرسم البياني: {len(chart_days)} أيام، {sum(chart_amounts):,.2f} دج إجمالي"
                        )

            except Exception as e:
                if self.logger:
                    self.logger.warning(f"فشل جلب بيانات الرسم البياني: {e}")
                # بيانات وهمية للتجربة
                chart_days = [1, 2, 3, 4, 5, 6, 7]
                chart_amounts = [0, 0, 0, 0, 0, 0, 0]

            # ------------------------------------------------
            # تحديث واجهة المستخدم (UI)
            # ------------------------------------------------

            if hasattr(self, "dashboard_summary_labels"):
                try:
                    # 1. تحديث بطاقات المخزون (Inventory Cards)
                    if "total_products" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["total_products"].setText(f"{total_products:,}")

                    if "total_stock_value" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["total_stock_value"].setText(f"{total_stock_value:,.2f} دج")

                    if "low_stock_items" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["low_stock_items"].setText(f"{low_stock_items:,}")

                    if "out_of_stock_items" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["out_of_stock_items"].setText(f"{out_of_stock_items:,}")

                    # 2. تحديث بطاقات الأداء (KPI Cards) - الصف الثاني
                    if "total_sales" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["total_sales"].setText(f"{total_sales_amount:,.0f} دج")

                    if "total_revenue" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["total_revenue"].setText(f"{total_sales_amount:,.0f} دج")

                    if "total_profit" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["total_profit"].setText(f"{total_profit:,.0f} دج")

                    if "avg_order" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["avg_order"].setText(f"{avg_order:,.0f} دج")

                    # 3. تحديث KPIs المالية اليومية
                    if "daily_revenue" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["daily_revenue"].setText(f"{daily_revenue:,.0f} دج")
                    if "daily_expenses" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["daily_expenses"].setText(f"{daily_expenses:,.0f} دج")
                    if "net_profit" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["net_profit"].setText(f"{net_profit:,.0f} دج")
                    if "avg_basket" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["avg_basket"].setText(f"{avg_basket:,.0f} دج")

                    # 4. تحديث الإحصائيات المتقدمة
                    if "avg_daily_sales" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["avg_daily_sales"].setText(f"{avg_daily_sales:,.0f} دج")
                    if "customer_retention" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["customer_retention"].setText(f"{customer_retention:.1f}%")
                    if "inventory_turnover" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["inventory_turnover"].setText(f"{inventory_turnover:.2f}")
                    # conversion_rate — يحتاج بيانات إضافية؛ يُعرض 0 مؤقتاً
                    if "conversion_rate" in self.dashboard_summary_labels:
                        self.dashboard_summary_labels["conversion_rate"].setText("—")
                except RuntimeError:
                    # Qt C++ objects already deleted (e.g. after tab switch/reload) - reset refs
                    self.dashboard_summary_labels = {}
                    if self.logger:
                        self.logger.debug("dashboard_summary_labels stale refs cleared")

            # تحديث الرسم البياني التفاعلي
            if hasattr(self, "sales_chart") and self.sales_chart:
                try:
                    self.sales_chart.update_chart(chart_days, chart_amounts)
                    if self.logger:
                        self.logger.debug("✅ تم تحديث الرسم البياني للمبيعات")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل تحديث الرسم البياني: {e}")

            if self.logger:
                self.logger.debug(
                    f"✅ تم تحديث إحصائيات Dashboard: {total_products} منتج، {total_sales_amount:,.0f} دج مبيعات"
                )

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في refresh_dashboard_stats: {e}", exc_info=True)
            else:

                logging.error(f"Error updating dashboard stats: {e}", exc_info=True)

    def refresh_dashboard_data(self):
        """تحديث بيانات الصفحة الرئيسية (محسّنة - في الخلفية)"""
        # 🔥 استدعاء محرك الإحصائيات السريع أولاً
        self.refresh_dashboard_stats()

        if not getattr(self, "inventory_service", None):
            return

        # الحصول على الفترة المحددة
        period = getattr(self, "dashboard_period_combo", None)
        try:
            period_text = period.currentText() if period else "أسبوع"
        except RuntimeError:
            # Widget deleted
            return

        end_date = date.today()
        if period_text == "اليوم":
            start_date = end_date
        elif period_text == "أسبوع":
            start_date = end_date - timedelta(days=7)
        elif period_text == "شهر":
            start_date = end_date - timedelta(days=30)
        elif period_text == "3 أشهر":
            start_date = end_date - timedelta(days=90)
        elif period_text == "سنة":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = date(2020, 1, 1)  # كل البيانات

        # تحميل البيانات في الخلفية
        def load_dashboard_data():
            """تحميل جميع بيانات الصفحة الرئيسية"""
            try:
                sales_query = """
                SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
                FROM sales
                WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
                """
                sales_result = self.db_manager.fetch_one(sales_query, (start_date.isoformat(), end_date.isoformat()))
                total_sales = float(sales_result[0] or 0) if sales_result else 0
                sales_count = sales_result[1] or 0 if sales_result else 0

                # المقارنة مع الفترة السابقة
                period_days = (end_date - start_date).days
                prev_start = start_date - timedelta(days=period_days) if period_days > 0 else start_date
                prev_sales_result = self.db_manager.fetch_one(
                    sales_query, (prev_start.isoformat(), start_date.isoformat())
                )
                prev_total_sales = float(prev_sales_result[0] or 0) if prev_sales_result else 0
                sales_change = (
                    ((total_sales - prev_total_sales) / prev_total_sales * 100) if prev_total_sales > 0 else 0
                )

                # حساب الربح
                profit_query = """
                SELECT COALESCE(SUM(si.quantity * (si.unit_price - p.cost_price)), 0)
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
                """
                profit_result = self.db_manager.fetch_one(profit_query, (start_date.isoformat(), end_date.isoformat()))
                total_profit = float(profit_result[0] or 0) if profit_result else 0
                avg_order = total_sales / sales_count if sales_count > 0 else 0

                # ملخص المخزون
                report = self.inventory_service.generate_inventory_report()
                alerts = getattr(report, "alerts", []) if report else []

                return {
                    "financial_kpis": {
                        "total_sales": total_sales,
                        "total_revenue": total_sales,
                        "total_profit": total_profit,
                        "avg_order": avg_order,
                        "sales_change": sales_change,
                    },
                    "inventory_report": report,
                    "alerts": alerts,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            except Exception as e:
                if self.logger:
                    self.logger.error(f"خطأ في تحميل بيانات الصفحة الرئيسية: {str(e)}")
                return None

        # استخدام DataLoaderWorker لتجنب تجميد الواجهة
        self._dashboard_loader = DataLoaderWorker(load_dashboard_data)
        self._dashboard_loader.data_loaded.connect(self._populate_dashboard_data)
        self._dashboard_loader.error_occurred.connect(
            lambda err: self.notify.show_error("خطأ", f"فشل تحميل بيانات الصفحة الرئيسية: {err}")
        )
        self._start_worker(self._dashboard_loader)

    def _populate_dashboard_data(self, data):
        """ملء بيانات الصفحة الرئيسية (في UI thread)"""
        if not data:
            return

        try:
            # --- تحديث رؤى Vision 2030 AI ---
            try:
                if hasattr(self, "ai_insight_label"):
                    from src.services.ai_prediction_service import AIPredictionService

                    ai_service = AIPredictionService(self.db_manager)
                    insights = ai_service.get_proactive_insights()

                    if insights:
                        # عرض أهم رؤية (الأولى)
                        top_insight = insights[0]
                        self.current_ai_insight = top_insight
                        self.ai_insight_label.setText(top_insight["message"])

                        if top_insight.get("type") == "CRITICAL":
                            self.ai_insight_label.setStyleSheet("color: #f87171; font-weight: bold; font-size: 14px;")
                            # Agentic UI: تفعيل زر الإجراء الفوري
                            self.ai_action_btn.setText("⚡ معالجة فورية (Agentic)")
                            self.ai_action_btn.setStyleSheet("""
                                QPushButton {
                                    background-color: rgba(239, 68, 68, 0.2);
                                    border: 1px solid rgba(248, 113, 113, 0.5);
                                    color: #fecaca;
                                    border-radius: 6px;
                                    padding: 5px 15px;
                                    font-weight: bold;
                                }
                                QPushButton:hover {
                                    background-color: rgba(239, 68, 68, 0.4);
                                }
                            """)
                        else:
                            self.ai_insight_label.setStyleSheet("color: #e2e8f0; font-style: italic; font-size: 14px;")
                            self.ai_action_btn.setText("تحليلات مفصلة")
                            self.ai_action_btn.setStyleSheet("""
                                QPushButton {
                                    background-color: rgba(255, 255, 255, 0.1);
                                    border: 1px solid rgba(255, 255, 255, 0.2);
                                    color: white;
                                    border-radius: 6px;
                                    padding: 5px 15px;
                                }
                                QPushButton:hover {
                                    background-color: rgba(255, 255, 255, 0.2);
                                }
                            """)
                    else:
                        self.current_ai_insight = None
                        self.ai_insight_label.setText("✅ Vision 2030 AI: جميع المؤشرات طبيعية. النظام يعمل بكفاءة.")
                        self.ai_action_btn.setText("Scan")
                        self.ai_action_btn.setStyleSheet("""
                            QPushButton {
                                background-color: rgba(16, 185, 129, 0.1);
                                border: 1px solid rgba(52, 211, 153, 0.3);
                                color: #d1fae5;
                                border-radius: 6px;
                                padding: 5px 15px;
                            }
                            QPushButton:hover {
                                background-color: rgba(16, 185, 129, 0.2);
                            }
                        """)
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in main_window.py")
            # --------------------------------

            # تحديث ملخص المخزون أولاً
            financial_kpis = data.get("financial_kpis", {})

            # تحديث KPIs المالية
            if hasattr(self, "dashboard_summary_labels"):
                if "total_sales" in self.dashboard_summary_labels:
                    self.dashboard_summary_labels["total_sales"].setText(
                        f"{financial_kpis.get('total_sales', 0):,.0f} دج"
                    )
                if "total_revenue" in self.dashboard_summary_labels:
                    self.dashboard_summary_labels["total_revenue"].setText(
                        f"{financial_kpis.get('total_revenue', 0):,.0f} دج"
                    )
                if "total_profit" in self.dashboard_summary_labels:
                    self.dashboard_summary_labels["total_profit"].setText(
                        f"{financial_kpis.get('total_profit', 0):,.0f} دج"
                    )
                if "avg_order" in self.dashboard_summary_labels:
                    self.dashboard_summary_labels["avg_order"].setText(f"{financial_kpis.get('avg_order', 0):,.0f} دج")

            # تحديث الاتجاهات
            if hasattr(self, "dashboard_trend_labels"):
                sales_change = financial_kpis.get("sales_change", 0)
                trend_text = f"{sales_change:+.1f}% عن الفترة السابقة"
                trend_color = "#27ae60" if sales_change >= 0 else "#e74c3c"
                if "total_sales" in self.dashboard_trend_labels:
                    self.dashboard_trend_labels["total_sales"].setText(trend_text)
                    self.dashboard_trend_labels["total_sales"].setStyleSheet(f"color: {trend_color}; font-size: 12px;")
            report = data.get("inventory_report")
            if report and hasattr(self, "dashboard_summary_labels"):

                def set_label(key, value):
                    label = self.dashboard_summary_labels.get(key)
                    if label:
                        label.setText(value)

                set_label("total_products", f"{getattr(report, 'total_products', 0):,}")
                set_label(
                    "total_stock_value",
                    f"{getattr(report, 'total_stock_value', 0):,.0f} دج",
                )
                set_label("low_stock_items", f"{getattr(report, 'low_stock_items', 0):,}")
                set_label(
                    "out_of_stock_items",
                    f"{getattr(report, 'out_of_stock_items', 0):,}",
                )

            # تحديث تنبيهات المخزون
            alerts = data.get("alerts", [])
            self.update_dashboard_alerts_table(alerts)

            # تحديث الرسوم البيانية
            self._update_dashboard_charts(data)

            # تحديث آخر العمليات والتحليلات (في خيط منفصل)
            start_date = data.get("start_date", date.today())
            end_date = data.get("end_date", date.today())

            # تحميل بيانات العمليات والتحليلات في الخلفية
            def load_activities_and_analytics():
                """تحميل بيانات العمليات والتحليلات"""
                activities = []  # ✅ تعريف المتغير في البداية
                try:
                    if getattr(self, "inventory_service", None):
                        movements = self.inventory_service.get_stock_movements(limit=20)
                        for m in movements:
                            type_display = {
                                "in": "إدخال",
                                "out": "إخراج",
                                "adjustment": "تعديل",
                                "transfer": "نقل",
                            }.get(m.movement_type, m.movement_type)

                            activities.append(
                                {
                                    "date": (m.created_at.strftime("%Y-%m-%d") if m.created_at else "-"),
                                    "time": (m.created_at.strftime("%H:%M:%S") if m.created_at else "-"),
                                    "type": "حركة مخزون",
                                    "description": f"{type_display} - {getattr(m, 'product_name', 'منتج')} ({m.quantity})",  # noqa: E501
                                    "user": "-",
                                    "status": "✅",
                                }
                            )

                    # المبيعات
                    if getattr(self, "sales_service", None):
                        query = """
                        SELECT s.id, s.sale_date, s.total_amount, s.status, COALESCE(u.username, 'النظام') as username
                        FROM sales s
                        LEFT JOIN users u ON s.user_id = u.id
                        ORDER BY s.sale_date DESC
                        LIMIT 15
                        """
                        sales = self.db_manager.fetch_all(query)
                        for sale in sales:
                            sale_id = sale["id"]
                            sale_date = sale["sale_date"]
                            total = sale["total_amount"]
                            status = sale["status"]
                            username = sale["username"]
                            date_str = (
                                sale_date.strftime("%Y-%m-%d")
                                if hasattr(sale_date, "strftime")
                                else str(sale_date)[:10]
                            )
                            time_str = sale_date.strftime("%H:%M:%S") if hasattr(sale_date, "strftime") else "-"
                            activities.append(
                                {
                                    "date": date_str,
                                    "time": time_str,
                                    "type": "مبيعات",
                                    "description": f"فاتورة #{sale_id} - {float(total or 0):,.2f} دج",
                                    "user": username or "-",
                                    "status": "✅" if status == "completed" else "⏳",
                                }
                            )

                    # المشتريات
                    if getattr(self, "purchase_service", None):
                        query = """
                        SELECT p.id, p.purchase_date, p.total_amount, p.status, COALESCE(u.username, 'النظام') as username  # noqa: E501
                        FROM purchases p
                        LEFT JOIN users u ON p.user_id = u.id
                        ORDER BY p.purchase_date DESC
                        LIMIT 15
                        """
                        purchases = self.db_manager.fetch_all(query)
                        for purchase in purchases:
                            pur_id = purchase["id"]
                            pur_date = purchase["purchase_date"]
                            total = purchase["total_amount"]
                            status = purchase["status"]
                            username = purchase["username"]
                            date_str = (
                                pur_date.strftime("%Y-%m-%d") if hasattr(pur_date, "strftime") else str(pur_date)[:10]
                            )
                            time_str = pur_date.strftime("%H:%M:%S") if hasattr(pur_date, "strftime") else "-"
                            activities.append(
                                {
                                    "date": date_str,
                                    "time": time_str,
                                    "type": "مشتريات",
                                    "description": f"شراء #{pur_id} - {float(total or 0):,.2f} دج",
                                    "user": username or "-",
                                    "status": "✅" if status == "completed" else "⏳",
                                }
                            )

                    # ترتيب حسب التاريخ والوقت
                    activities.sort(key=lambda x: (x["date"], x["time"]), reverse=True)
                    activities = activities[:50]

                    # أفضل العملاء
                    customers_query = """
                    SELECT
                        c.id, c.name,
                        COUNT(s.id) as purchase_count,
                        COALESCE(SUM(s.total_amount), 0) as total_spent
                    FROM customers c
                    LEFT JOIN sales s ON c.id = s.customer_id
                    WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
                    GROUP BY c.id, c.name
                    HAVING purchase_count > 0
                    ORDER BY total_spent DESC
                    LIMIT 10
                    """
                    customers = self.db_manager.fetch_all(
                        customers_query, (start_date.isoformat(), end_date.isoformat())
                    )

                    # أفضل المنتجات
                    products_query = """
                    SELECT
                        p.id, p.name,
                        COALESCE(SUM(si.quantity), 0) as total_quantity,
                        COALESCE(SUM(si.quantity * si.unit_price), 0) as total_sales
                    FROM products p
                    JOIN sale_items si ON p.id = si.product_id
                    JOIN sales s ON si.sale_id = s.id
                    WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
                    GROUP BY p.id, p.name
                    ORDER BY total_sales DESC
                    LIMIT 10
                    """
                    products = self.db_manager.fetch_all(products_query, (start_date.isoformat(), end_date.isoformat()))

                    # الإحصائيات المتقدمة
                    period_days = (end_date - start_date).days or 1
                    sales_query = """
                    SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
                    FROM sales
                    WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
                    """
                    sales_result = self.db_manager.fetch_one(
                        sales_query, (start_date.isoformat(), end_date.isoformat())
                    )
                    total_sales = float(sales_result[0] or 0) if sales_result else 0
                    sales_count = sales_result[1] or 0 if sales_result else 0
                    avg_daily = total_sales / period_days if period_days > 0 else 0

                    customers_query_stats = """
                    SELECT COUNT(DISTINCT customer_id)
                    FROM sales
                    WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
                    """
                    customers_result = self.db_manager.fetch_one(
                        customers_query_stats,
                        (start_date.isoformat(), end_date.isoformat()),
                    )
                    active_customers = customers_result[0] or 0 if customers_result else 0
                    conversion_rate = (sales_count / active_customers * 100) if active_customers > 0 else 0

                    inventory_query = """
                    SELECT COALESCE(SUM(current_stock * cost_price), 0)
                    FROM products
                    WHERE is_active = 1
                    """
                    inventory_result = self.db_manager.fetch_one(inventory_query)
                    inventory_value = float(inventory_result[0] or 0) if inventory_result else 0
                    turnover = (total_sales / inventory_value) if inventory_value > 0 else 0

                    return {
                        "activities": activities,
                        "customers": customers,
                        "products": products,
                        "advanced_stats": {
                            "avg_daily_sales": avg_daily,
                            "conversion_rate": conversion_rate,
                            "inventory_turnover": turnover,
                        },
                    }
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"خطأ في تحميل بيانات العمليات والتحليلات: {str(e)}",
                            exc_info=True,
                        )
                    # إرجاع بيانات فارغة بدلاً من None لتجنب الأخطاء
                    return {
                        "activities": activities if "activities" in locals() else [],
                        "customers": [],
                        "products": [],
                        "advanced_stats": {
                            "avg_daily_sales": 0,
                            "conversion_rate": 0,
                            "inventory_turnover": 0,
                        },
                    }

            # تحميل في الخلفية
            self._dashboard_analytics_loader = DataLoaderWorker(load_activities_and_analytics)
            self._dashboard_analytics_loader.data_loaded.connect(self._populate_dashboard_analytics)
            self._dashboard_analytics_loader.error_occurred.connect(
                lambda err: (self.logger.error(f"خطأ في تحميل التحليلات: {err}") if self.logger else None)
            )
            self._start_worker(self._dashboard_analytics_loader)

            # تحديث الرسوم البيانية (هذه سريعة نسبياً)
            # سيتم تحديثها لاحقاً عند الحاجة

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Dashboard refresh failed: {e}")

    def _update_financial_kpis(self, start_date, end_date):
        """تحديث KPIs المالية مع الاتجاهات"""
        try:
            # إجمالي المبيعات
            sales_query = """
            SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
            """
            sales_result = self.db_manager.fetch_one(sales_query, (start_date.isoformat(), end_date.isoformat()))
            total_sales = float(sales_result[0] or 0) if sales_result else 0
            sales_count = sales_result[1] or 0 if sales_result else 0

            # المقارنة مع الفترة السابقة
            period_days = (end_date - start_date).days
            prev_start = start_date - timedelta(days=period_days)
            prev_sales_result = self.db_manager.fetch_one(sales_query, (prev_start.isoformat(), start_date.isoformat()))
            prev_total_sales = float(prev_sales_result[0] or 0) if prev_sales_result else 0

            sales_change = ((total_sales - prev_total_sales) / prev_total_sales * 100) if prev_total_sales > 0 else 0

            # حساب الربح
            profit_query = """
            SELECT COALESCE(SUM(si.quantity * (si.unit_price - p.cost_price)), 0)
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
            """
            profit_result = self.db_manager.fetch_one(profit_query, (start_date.isoformat(), end_date.isoformat()))
            total_profit = float(profit_result[0] or 0) if profit_result else 0

            # متوسط قيمة الطلب
            avg_order = total_sales / sales_count if sales_count > 0 else 0

            # تحديث التسميات
            if hasattr(self, "dashboard_summary_labels"):
                if "total_sales" in self.dashboard_summary_labels:
                    self.dashboard_summary_labels["total_sales"].setText(f"{total_sales:,.0f} دج")
                if "total_revenue" in self.dashboard_summary_labels:
                    self.dashboard_summary_labels["total_revenue"].setText(f"{total_sales:,.0f} دج")
                if "total_profit" in self.dashboard_summary_labels:
                    self.dashboard_summary_labels["total_profit"].setText(f"{total_profit:,.0f} دج")
                if "avg_order" in self.dashboard_summary_labels:
                    self.dashboard_summary_labels["avg_order"].setText(f"{avg_order:,.0f} دج")

            # تحديث الاتجاهات
            if hasattr(self, "dashboard_trend_labels"):
                trend_text = f"{sales_change:+.1f}% عن الفترة السابقة"
                trend_color = "#27ae60" if sales_change >= 0 else "#e74c3c"
                if "total_sales" in self.dashboard_trend_labels:
                    self.dashboard_trend_labels["total_sales"].setText(trend_text)
                    self.dashboard_trend_labels["total_sales"].setStyleSheet(f"color: {trend_color}; font-size: 12px;")

        except (KeyError, ValueError, TypeError) as e:
            self.logger.warning(f"Financial KPIs update failed: {e}")

    def update_dashboard_alerts_table(self, alerts):
        """تحديث جدول تنبيهات المخزون في الصفحة الرئيسية"""
        if not hasattr(self, "dashboard_alerts_table"):
            return

        table = self.dashboard_alerts_table
        alerts = alerts or []

        if not alerts:
            table.setRowCount(1)
            info_item = QTableWidgetItem("لا توجد تنبيهات حالياً")
            info_item.setTextAlignment(Qt.AlignCenter)
            table.setSpan(0, 0, 1, table.columnCount())
            table.setItem(0, 0, info_item)
            return

        # Quick Win: Disable updates during batch operations
        table.setUpdatesEnabled(False)

        table.clearSpans()
        table.setRowCount(len(alerts))

        severity_colors = {
            "low": "#2ecc71",
            "medium": "#f1c40f",
            "high": "#e67e22",
            "critical": "#e74c3c",
        }

        for row, alert in enumerate(alerts):
            if isinstance(alert, dict):
                product_name = alert.get("product_name", "-")
                alert_type = alert.get("alert_type", "")
                current_stock = alert.get("current_stock", "-")
                message = alert.get("message", "-")
                severity = alert.get("severity", "")
            else:
                product_name = getattr(alert, "product_name", "-")
                alert_type = getattr(alert, "alert_type", "")
                current_stock = getattr(alert, "current_stock", "-")
                message = getattr(alert, "message", "-")
                severity = getattr(alert, "severity", "")

            status_text = {
                "low_stock": "مخزون منخفض",
                "out_of_stock": "نفاد المخزون",
                "expired": "منتهي الصلاحية",
            }.get(alert_type, alert_type or "-")

            color = severity_colors.get(severity, "#94a3b8")

            items = [
                QTableWidgetItem(str(product_name)),
                QTableWidgetItem(status_text),
                QTableWidgetItem(str(current_stock)),
                QTableWidgetItem(str(message)),
            ]

            for idx, item in enumerate(items):
                if idx == 2:
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                item.setForeground(QColor(color))
                table.setItem(row, idx, item)

        # Quick Win: Re-enable updates after batch operations
        table.setUpdatesEnabled(True)

    def _populate_dashboard_analytics(self, data):
        """ملء بيانات التحليلات (في UI thread)"""
        if not data:
            return

        try:
            # تحديث الرسوم البيانية
            self._update_dashboard_charts(data)

            activities = data.get("activities", [])
            if hasattr(self, "dashboard_activities_table") and activities is not None:
                table = self.dashboard_activities_table
                if not activities:
                    table.setRowCount(1)
                    info_item = QTableWidgetItem("لا توجد عمليات حديثة")
                    info_item.setTextAlignment(Qt.AlignCenter)
                    table.setSpan(0, 0, 1, table.columnCount())
                    table.setItem(0, 0, info_item)
                else:
                    # Quick Win: Disable updates during batch operations
                    table.setUpdatesEnabled(False)

                    table.clearSpans()
                    table.setRowCount(len(activities))
                    for row, activity in enumerate(activities):
                        items = [
                            QTableWidgetItem(activity["date"]),
                            QTableWidgetItem(activity["time"]),
                            QTableWidgetItem(activity["type"]),
                            QTableWidgetItem(activity["description"]),
                            QTableWidgetItem(activity["user"]),
                            QTableWidgetItem(activity["status"]),
                        ]
                        for idx, item in enumerate(items):
                            if idx in [0, 1, 4, 5]:
                                item.setTextAlignment(Qt.AlignCenter)
                            else:
                                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                            if activity["type"] == "مبيعات":
                                item.setForeground(QColor("#27ae60"))
                            elif activity["type"] == "مشتريات":
                                item.setForeground(QColor("#3498db"))
                            elif activity["type"] == "حركة مخزون":
                                item.setForeground(QColor("#e67e22"))
                            table.setItem(row, idx, item)

                    # Quick Win: Re-enable updates after batch operations
                    table.setUpdatesEnabled(True)

            # تحديث أفضل العملاء
            customers = data.get("customers", [])
            if hasattr(self, "dashboard_top_customers_table") and customers:
                table = self.dashboard_top_customers_table
                # Quick Win: Disable updates during batch operations
                table.setUpdatesEnabled(False)

                table.clearSpans()
                table.setRowCount(len(customers))
                for row, customer_row in enumerate(customers):
                    customer_id = customer_row["id"]
                    name = customer_row["name"]
                    count = customer_row["purchase_count"]
                    total = customer_row["total_spent"]
                    items = [
                        QTableWidgetItem(f"#{row + 1}"),
                        QTableWidgetItem(name or "-"),
                        QTableWidgetItem(str(count)),
                        QTableWidgetItem(f"{float(total or 0):,.0f} دج"),
                    ]
                    for idx, item in enumerate(items):
                        if idx == 0:
                            item.setTextAlignment(Qt.AlignCenter)
                            item.setForeground(QColor("#9b59b6"))
                            item.setFont(QFont("Arial", 10, QFont.Bold))
                        elif idx == 2:
                            item.setTextAlignment(Qt.AlignCenter)
                        else:
                            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                        table.setItem(row, idx, item)

                # Quick Win: Re-enable updates after batch operations
                table.setUpdatesEnabled(True)

            # تحديث أفضل المنتجات
            products = data.get("products", [])
            if hasattr(self, "dashboard_top_products_table") and products:
                table = self.dashboard_top_products_table
                # Quick Win: Disable updates during batch operations
                table.setUpdatesEnabled(False)

                table.clearSpans()
                table.setRowCount(len(products))
                for row, product_row in enumerate(products):
                    product_id = product_row["id"]
                    name = product_row["name"]
                    quantity = product_row["total_quantity"]
                    sales = product_row["total_sales"]
                    items = [
                        QTableWidgetItem(f"#{row + 1}"),
                        QTableWidgetItem(name or "-"),
                        QTableWidgetItem(f"{float(quantity or 0):,.0f}"),
                        QTableWidgetItem(f"{float(sales or 0):,.0f} دج"),
                    ]
                    for idx, item in enumerate(items):
                        if idx == 0:
                            item.setTextAlignment(Qt.AlignCenter)
                            item.setForeground(QColor("#e67e22"))
                            item.setFont(QFont("Arial", 10, QFont.Bold))
                        elif idx == 2:
                            item.setTextAlignment(Qt.AlignCenter)
                        else:
                            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                        table.setItem(row, idx, item)

                # Quick Win: Re-enable updates after batch operations
                table.setUpdatesEnabled(True)

            # تحديث الإحصائيات المتقدمة
            advanced_stats = data.get("advanced_stats", {})
            if advanced_stats and hasattr(self, "dashboard_advanced_stats_labels"):
                stats = self.dashboard_advanced_stats_labels
                if "avg_daily_sales" in stats:
                    stats["avg_daily_sales"].setText(f"{advanced_stats.get('avg_daily_sales', 0):,.0f} دج/يوم")
                if "conversion_rate" in stats:
                    stats["conversion_rate"].setText(f"{advanced_stats.get('conversion_rate', 0):.1f}%")
                if "inventory_turnover" in stats:
                    stats["inventory_turnover"].setText(f"{advanced_stats.get('inventory_turnover', 0):.2f}x")

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            self.logger.debug(f"Advanced stats update failed: {e}")

    def update_dashboard_activities_table(self, filter_type=None):
        """تحديث جدول آخر العمليات (يتم استدعاؤه من الفلتر فقط)"""
        # إعادة تحميل البيانات عند تغيير الفلتر
        self.refresh_dashboard_data()

        activities = []

        try:
            # حركات المخزون
            if getattr(self, "inventory_service", None) and (filter_type == "الكل" or filter_type == "حركة مخزون"):
                movements = self.inventory_service.get_stock_movements(limit=20)
                for m in movements:
                    type_display = {
                        "in": "إدخال",
                        "out": "إخراج",
                        "adjustment": "تعديل",
                        "transfer": "نقل",
                    }.get(m.movement_type, m.movement_type)

                    activities.append(
                        {
                            "date": (m.created_at.strftime("%Y-%m-%d") if m.created_at else "-"),
                            "time": (m.created_at.strftime("%H:%M:%S") if m.created_at else "-"),
                            "type": "حركة مخزون",
                            "description": f"{type_display} - {getattr(m, 'product_name', 'منتج')} ({m.quantity})",
                            "user": "-",
                            "status": "✅",
                        }
                    )

            # المبيعات (إذا كانت متوفرة)
            if getattr(self, "sales_service", None) and (filter_type == "الكل" or filter_type == "مبيعات"):
                try:
                    query = """
                    SELECT s.id, s.sale_date, s.total_amount, s.status, COALESCE(u.username, 'النظام') as username
                    FROM sales s
                    LEFT JOIN users u ON s.user_id = u.id
                    ORDER BY s.sale_date DESC
                    LIMIT 15
                    """
                    sales = self.db_manager.fetch_all(query)
                    for sale in sales:
                        sale_id = sale["id"]
                        sale_date = sale["sale_date"]
                        total = sale["total_amount"]
                        status = sale["status"]
                        username = sale["username"]
                        date_str = (
                            sale_date.strftime("%Y-%m-%d") if hasattr(sale_date, "strftime") else str(sale_date)[:10]
                        )
                        time_str = sale_date.strftime("%H:%M:%S") if hasattr(sale_date, "strftime") else "-"
                        activities.append(
                            {
                                "date": date_str,
                                "time": time_str,
                                "type": "مبيعات",
                                "description": f"فاتورة #{sale_id} - {float(total or 0):,.2f} دج",
                                "user": username or "-",
                                "status": "✅" if status == "completed" else "⏳",
                            }
                        )
                except (KeyError, ValueError, TypeError, AttributeError) as e:
                    self.logger.debug(f"Sales activity processing failed: {e}")

            # المشتريات (إذا كانت متوفرة)
            if getattr(self, "purchase_service", None) and (filter_type == "الكل" or filter_type == "مشتريات"):
                try:
                    query = """
                    SELECT p.id, p.purchase_date, p.total_amount, p.status, COALESCE(u.username, 'النظام') as username
                    FROM purchases p
                    LEFT JOIN users u ON p.user_id = u.id
                    ORDER BY p.purchase_date DESC
                    LIMIT 15
                    """
                    purchases = self.db_manager.fetch_all(query)
                    for purchase in purchases:
                        pur_id = purchase["id"]
                        pur_date = purchase["purchase_date"]
                        total = purchase["total_amount"]
                        status = purchase["status"]
                        username = purchase["username"]
                        date_str = (
                            pur_date.strftime("%Y-%m-%d") if hasattr(pur_date, "strftime") else str(pur_date)[:10]
                        )
                        time_str = pur_date.strftime("%H:%M:%S") if hasattr(pur_date, "strftime") else "-"
                        activities.append(
                            {
                                "date": date_str,
                                "time": time_str,
                                "type": "مشتريات",
                                "description": f"شراء #{pur_id} - {float(total or 0):,.2f} دج",
                                "user": username or "-",
                                "status": "✅" if status == "completed" else "⏳",
                            }
                        )
                except (KeyError, ValueError, TypeError, AttributeError) as e:
                    self.logger.debug(f"Purchase activity processing failed: {e}")

            # ترتيب حسب التاريخ والوقت
            activities.sort(key=lambda x: (x["date"], x["time"]), reverse=True)
            activities = activities[:50]  # آخر 50 عملية

            if not hasattr(self, "dashboard_activities_table"):
                return

            table = self.dashboard_activities_table

            if not activities:
                table.setRowCount(1)
                info_item = QTableWidgetItem("لا توجد عمليات حديثة")
                info_item.setTextAlignment(Qt.AlignCenter)
                table.setSpan(0, 0, 1, table.columnCount())
                table.setItem(0, 0, info_item)
                return

            table.clearSpans()
            table.setRowCount(len(activities))

            for row, activity in enumerate(activities):
                items = [
                    QTableWidgetItem(activity["date"]),
                    QTableWidgetItem(activity["time"]),
                    QTableWidgetItem(activity["type"]),
                    QTableWidgetItem(activity["description"]),
                    QTableWidgetItem(activity["user"]),
                    QTableWidgetItem(activity["status"]),
                ]

                for col, item in enumerate(items):
                    table.setItem(row, col, item)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث جدول العمليات: {e}")

                for idx, item in enumerate(items):
                    if idx in [0, 1, 4, 5]:
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)

                    # تلوين حسب النوع
                    if activity["type"] == "مبيعات":
                        item.setForeground(QColor("#27ae60"))
                    elif activity["type"] == "مشتريات":
                        item.setForeground(QColor("#3498db"))
                    elif activity["type"] == "حركة مخزون":
                        item.setForeground(QColor("#e67e22"))

                    table.setItem(row, idx, item)

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Activities table update failed: {e}")
            if hasattr(self, "dashboard_activities_table"):
                table = self.dashboard_activities_table
                table.setRowCount(1)
                info_item = QTableWidgetItem("لا توجد نشاطات لعرضها حالياً")
                info_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(0, 0, info_item)

    # ===== Agentic AI Handlers (Vision 2030) =====

    def handle_ai_action(self):
        """
        تنفيذ الإجراء المقترح من الذكاء الاصطناعي (Agentic AI)
        يقوم هذا المعالج بتنفيذ الأمر (مثل إعادة الطلب) بشكل مستقل أو شبه مستقل.
        """
        try:
            if not hasattr(self, "current_ai_insight") or not self.current_ai_insight:
                # Fallback to Command Palette if no specific insight action
                self.open_command_palette()
                return

            insight = self.current_ai_insight
            action_type = insight.get("action_type")

            if action_type == "REORDER":
                # 1. استخراج المعلمات
                product_id = insight.get("product_id")
                quantity = insight.get("quantity", 10)

                # 2. تأكيد المستخدم (Semi-Autonomous Mode)
                # في المستقبل (2030) قد يكون هذا تلقائياً بالكامل للقيم المنخفضة
                from PySide6.QtWidgets import QMessageBox

                reply = QMessageBox.question(
                    self,
                    "Agentic AI Action",
                    f"هل تريد السماح للوكيل الذكي بإنشاء مسودة طلب شراء للمنتج (#{product_id}) بكمية {quantity}؟",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if reply == QMessageBox.Yes:
                    # 3. التنفيذ
                    from src.services.purchase_service import PurchaseService

                    # نحتاج لإنشاء خدمة مشتريات جديدة أو استخدام الموجودة إذا كانت متوفرة
                    # بما أننا في MainWindow، قد لا تكون purchase_service مهيأة كخاصية دائمة، لذا ننشؤها
                    purchase_service = PurchaseService(self.db_manager, self.logger)

                    purchase_id = purchase_service.create_auto_reorder_draft(product_id, quantity)

                    if purchase_id:
                        self.notify.show_success(
                            "تم التنفيذ بنجاح",
                            f"✅ قام الوكيل الذكي بإنشاء فاتورة شراء مسودة #{purchase_id}",
                        )
                        # تحديث الداشبورد لإخفاء التنبيه إذا تم حله
                        self.refresh_dashboard_data()

                        # الانتقال لصفحة المشتريات (اختياري)
                        # self.switch_page('purchases')
                    else:
                        self.notify.show_error("فشل التنفيذ", "❌ لم يتمكن الوكيل من إتمام العملية.")

            elif action_type == "PROMOTION":
                # منطق العروض الترويجية (للمرحلة القادمة)
                self.notify.show_info("قريباً", "سيتم تفعيل وكيل التسويق قريباً.")

            else:
                # إجراء افتراضي
                self.open_command_palette()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in handle_ai_action: {e}")
            self.notify.show_error("خطأ نظمي", "حدث خطأ أثناء تنفيذ الإجراء الذكي.")

    def handle_ai_command(self, command: str):
        """
        معالجة الأوامر الصوتية/النصية من المساعد الذكي (SmartAssistantWidget).
        يحلل الأمر ويوجهه للدالة المناسبة.
        """
        if not command:
            return
        try:
            cmd = command.strip().lower()

            if any(k in cmd for k in ["مبيعات", "فاتورة", "بيع", "sale", "invoice"]):
                self.switch_page("sales") if hasattr(self, "switch_page") else None
            elif any(k in cmd for k in ["مخزون", "منتج", "inventory", "product", "stock"]):
                self.switch_page("inventory") if hasattr(self, "switch_page") else None
            elif any(k in cmd for k in ["عميل", "customer", "client"]):
                self.switch_page("contacts") if hasattr(self, "switch_page") else None
            elif any(k in cmd for k in ["تقرير", "report"]):
                self.switch_page("reports") if hasattr(self, "switch_page") else None
            elif any(k in cmd for k in ["مشتريات", "مورد", "purchase", "supplier"]):
                self.switch_page("purchases") if hasattr(self, "switch_page") else None
            elif any(k in cmd for k in ["محاسبة", "حساب", "accounting", "finance"]):
                self.switch_page("accounting") if hasattr(self, "switch_page") else None
            elif any(k in cmd for k in ["إعدادات", "settings", "config"]):
                self.switch_page("settings") if hasattr(self, "switch_page") else None
            elif any(k in cmd for k in ["لوحة", "dashboard", "رئيسي"]):
                self.switch_page("dashboard") if hasattr(self, "switch_page") else None
            elif any(k in cmd for k in ["مساعد", "help", "مساعدة"]):
                if hasattr(self, "smart_assistant_widget") and self.smart_assistant_widget:
                    self.smart_assistant_widget.show()
            else:
                # Fallback: open command palette
                if hasattr(self, "open_command_palette"):
                    self.open_command_palette()

            if self.logger:
                self.logger.info(f"AI command handled: {command[:80]}")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"handle_ai_command error: {e}")

    def update_dashboard_analytics(self, start_date, end_date):
        """تحديث التحليلات المتقدمة (تم نقلها إلى _populate_dashboard_analytics)"""
        pass  # تم نقل الكود إلى _populate_dashboard_analytics

    def _update_dashboard_charts_initial(self):
        """تحديث الرسوم البيانية عند فتح الداشبورد لأول مرة"""
        try:
            if self.logger:
                self.logger.debug("🔄 بدء التحديث الأولي للرسوم البيانية...")

            # جلب بيانات حقيقية من قاعدة البيانات
            data = {}

            # جلب KPIs المالية
            if self.db_manager:
                try:
                    kpi_query = """
                    SELECT
                        COALESCE(SUM(total_amount), 0) as total_revenue,
                        COALESCE(SUM(paid_amount), 0) as total_paid
                    FROM sales
                    WHERE status != 'ملغية' AND status != 'cancelled'
                    """
                    kpi_result = self.db_manager.execute_query(kpi_query)
                    if kpi_result and len(kpi_result) > 0:
                        row = kpi_result[0]
                        if isinstance(row, dict):
                            revenue = float(row.get("total_revenue", 0) or 0)
                        else:
                            revenue = float(row[0] if len(row) > 0 else 0)

                        data["financial_kpis"] = {
                            "total_revenue": revenue,
                            "total_profit": revenue * 0.3,  # تقدير
                        }
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل جلب KPIs: {e}")

            # جلب أفضل المنتجات
            if self.db_manager:
                try:
                    products_query = """
                    SELECT
                        p.id,
                        p.name,
                        SUM(si.quantity) as total_quantity,
                        SUM(si.total_price) as total_sales
                    FROM products p
                    JOIN sale_items si ON p.id = si.product_id
                    JOIN sales s ON si.sale_id = s.id
                    WHERE s.status != 'ملغية' AND s.status != 'cancelled'
                    GROUP BY p.id, p.name
                    ORDER BY total_sales DESC
                    LIMIT 5
                    """
                    products_result = self.db_manager.execute_query(products_query)
                    if products_result:
                        data["products"] = products_result
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل جلب المنتجات: {e}")

            # إذا لم تكن هناك بيانات، استخدم بيانات فارغة
            if not data:
                data = {
                    "financial_kpis": {"total_revenue": 0, "total_profit": 0},
                    "products": [],
                }

            self._update_dashboard_charts(data)

            if self.logger:
                self.logger.debug("✅ انتهى التحديث الأولي للرسوم البيانية")
        except Exception as e:
            if self.logger:
                self.logger.error(f"فشل التحديث الأولي للرسوم البيانية: {e}", exc_info=True)

    def _update_dashboard_charts(self, data):
        """تحديث الرسوم البيانية في الداشبورد"""
        if not data:
            data = {}  # بيانات فارغة بدلاً من return

        # Guard against stale libshiboken references (widgets deleted after tab switch)
        for _chart_attr in (
            "dashboard_sales_line_chart",
            "dashboard_revenue_expense_chart",
            "dashboard_stock_chart",
            "dashboard_top_products_chart",
        ):
            _widget = getattr(self, _chart_attr, None)
            if _widget is not None:
                try:
                    _widget.isVisible()  # simple call to check C++ object is alive
                except RuntimeError:
                    setattr(self, _chart_attr, None)
                    if self.logger:
                        self.logger.debug(f"Cleared stale chart ref: {_chart_attr}")

        try:
            if self.logger:
                self.logger.debug("🔄 بدء تحديث الرسوم البيانية...")

            # 1. رسم بياني المبيعات (خط)
            if hasattr(self, "dashboard_sales_line_chart") and self.dashboard_sales_line_chart:
                try:
                    # جلب بيانات المبيعات آخر 7 أيام
                    if self.db_manager:
                        query = """
                        SELECT
                            date(sale_date) as sale_date,
                            COALESCE(SUM(total_amount), 0) as daily_total
                        FROM sales
                        WHERE sale_date >= date('now', '-7 days')
                          AND status != 'ملغية'
                          AND status != 'cancelled'
                        GROUP BY date(sale_date)
                        ORDER BY date(sale_date) ASC
                        """
                        results = self.db_manager.execute_query(query)

                        if results:
                            dates = []
                            amounts = []
                            for row in results:
                                if isinstance(row, dict):
                                    dates.append(row.get("sale_date", ""))
                                    amounts.append(float(row.get("daily_total", 0) or 0))
                                else:
                                    dates.append(str(row[0]) if len(row) > 0 else "")
                                    amounts.append(float(row[1] if len(row) > 1 else 0) or 0.0)

                            # إنشاء الرسم البياني
                            chart = QChart()
                            chart.setTitle("المبيعات (آخر 7 أيام)")

                            series = QLineSeries()
                            for i, amount in enumerate(amounts):
                                series.append(i, amount)

                            chart.addSeries(series)
                            chart.createDefaultAxes()
                            chart.legend().setVisible(False)

                            self.dashboard_sales_line_chart.setChart(chart)
                            if self.logger:
                                self.logger.debug(f"✅ تم تحديث رسم المبيعات: {len(amounts)} نقاط بيانات")
                        else:
                            if self.logger:
                                self.logger.debug("⚠️ لا توجد بيانات مبيعات للرسم")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل تحديث رسم المبيعات: {e}", exc_info=True)

            # 2. رسم بياني المقارنة (إيرادات vs مصروفات)
            if hasattr(self, "dashboard_revenue_expense_chart") and self.dashboard_revenue_expense_chart:
                try:
                    chart = QChart()
                    chart.setTitle("الإيرادات والمصروفات")

                    # بيانات الإيرادات والمصروفات من قاعدة البيانات
                    revenue = data.get("financial_kpis", {}).get("total_revenue", 0)

                    # حساب المصروفات الفعلية من المشتريات
                    try:
                        expense_query = """
                            SELECT COALESCE(SUM(total_amount), 0)
                            FROM purchases
                            WHERE status NOT IN ('ملغية', 'cancelled')
                        """
                        expense_result = None
                        if hasattr(self.db_manager, "execute_query"):
                            expense_result = self.db_manager.execute_query(expense_query)
                        elif hasattr(self.db_manager, "fetch_all"):
                            expense_result = self.db_manager.fetch_all(expense_query)
                        if expense_result and expense_result[0]:
                            expense = float(expense_result[0][0])
                        else:
                            expense = 0.0
                    except Exception:
                        expense = 0.0

                    series = QBarSeries()

                    revenue_set = QBarSet("الإيرادات")
                    revenue_set.append(revenue)
                    revenue_set.setColor(QColor("#27ae60"))

                    expense_set = QBarSet("المصروفات")
                    expense_set.append(expense)
                    expense_set.setColor(QColor("#e74c3c"))

                    series.append(revenue_set)
                    series.append(expense_set)

                    chart.addSeries(series)
                    chart.createDefaultAxes()
                    chart.legend().setVisible(True)

                    self.dashboard_revenue_expense_chart.setChart(chart)
                    if self.logger:
                        self.logger.debug(f"✅ تم تحديث رسم المقارنة: إيرادات={revenue:,.0f}, مصروفات={expense:,.0f}")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل تحديث رسم المقارنة: {e}", exc_info=True)

            # 3. رسم بياني توزيع المخزون (دائري)
            if hasattr(self, "dashboard_stock_chart") and self.dashboard_stock_chart:
                try:
                    chart = QChart()
                    chart.setTitle("توزيع المخزون")

                    series = QPieSeries()

                    # بيانات تجريبية (يمكن استبدالها ببيانات حقيقية)
                    if hasattr(self, "dashboard_summary_labels"):
                        # معالجة آمنة للنصوص (قد تكون "-" أو فارغة)
                        def safe_int_from_label(key, default=0):
                            try:
                                label = self.dashboard_summary_labels.get(key)
                                if not label:
                                    return default

                                text = label.text().replace(",", "").strip()

                                # تجاهل "-" والقيم الفارغة
                                if not text or text == "-" or text == "":
                                    return default

                                # محاولة التحويل - استخدام float أولاً ثم int
                                try:
                                    # إزالة أي مسافات إضافية
                                    text = text.replace(" ", "")
                                    # التحويل
                                    return int(float(text))
                                except (ValueError, TypeError, AttributeError):
                                    return default
                            except (ValueError, TypeError, AttributeError) as e:
                                self.logger.debug(f"Safe int conversion failed: {e}")
                                return default

                        low_stock = safe_int_from_label("low_stock_items", 0)
                        out_stock = safe_int_from_label("out_of_stock_items", 0)
                        total = safe_int_from_label("total_products", 0)
                        in_stock = max(0, total - low_stock - out_stock)

                        if total > 0:
                            if in_stock > 0:
                                slice1 = QPieSlice(f"متوفر ({in_stock})", in_stock)
                                slice1.setColor(QColor("#27ae60"))
                                series.append(slice1)

                            if low_stock > 0:
                                slice2 = QPieSlice(f"منخفض ({low_stock})", low_stock)
                                slice2.setColor(QColor("#f39c12"))
                                series.append(slice2)

                            if out_stock > 0:
                                slice3 = QPieSlice(f"نفد ({out_stock})", out_stock)
                                slice3.setColor(QColor("#e74c3c"))
                                series.append(slice3)

                    if series.count() > 0:
                        chart.addSeries(series)
                        chart.legend().setVisible(True)

                        self.dashboard_stock_chart.setChart(chart)
                        if self.logger:
                            self.logger.debug(f"✅ تم تحديث رسم المخزون: {series.count()} شرائح")
                    else:
                        if self.logger:
                            self.logger.debug("⚠️ لا توجد بيانات مخزون للرسم")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل تحديث رسم المخزون: {e}", exc_info=True)

            # 4. رسم بياني أفضل المنتجات (أعمدة)
            if hasattr(self, "dashboard_top_products_chart") and self.dashboard_top_products_chart:
                try:
                    products = data.get("products", [])[:5]  # أفضل 5 منتجات

                    if products:
                        chart = QChart()
                        chart.setTitle("أفضل 5 منتجات مبيعاً")

                        series = QBarSeries()
                        bar_set = QBarSet("المبيعات")

                        categories = []
                        for product in products:
                            if isinstance(product, (list, tuple)) and len(product) >= 4:
                                name = str(product[1] or "منتج")[:20]  # تقصير الاسم
                                sales = float(product[3] or 0)
                                categories.append(name)
                                bar_set.append(sales)

                        if categories:
                            bar_set.setColor(QColor("#3498db"))
                            series.append(bar_set)

                            chart.addSeries(series)
                            chart.createDefaultAxes()

                            axis_x = QBarCategoryAxis()
                            axis_x.append(categories)
                            chart.setAxisX(axis_x, series)

                            self.dashboard_top_products_chart.setChart(chart)
                            if self.logger:
                                self.logger.debug(f"✅ تم تحديث رسم أفضل المنتجات: {len(categories)} منتجات")
                        else:
                            if self.logger:
                                self.logger.debug("⚠️ لا توجد بيانات منتجات للرسم")
                    else:
                        if self.logger:
                            self.logger.debug("⚠️ لا توجد منتجات في البيانات")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل تحديث رسم أفضل المنتجات: {e}", exc_info=True)

            if self.logger:
                self.logger.debug("✅ انتهى تحديث الرسوم البيانية")

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث الرسوم البيانية: {e}", exc_info=True)

    def update_dashboard_advanced_stats(self, start_date, end_date):
        """تحديث الإحصائيات المتقدمة (تم نقلها إلى _populate_dashboard_analytics)"""
        pass  # تم نقل الكود إلى _populate_dashboard_analytics

    def create_performance_tab(self) -> QWidget:
        """إنشاء تبويب أداء خفيف الوزن مع مؤشرات بسيطة"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel(self.i18n.get_message("key_performance_indicators"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: rgb(41, 128, 185); margin-bottom: 4px;")
        layout.addWidget(title)

        grid = QHBoxLayout()

        # بطاقة: السمة الحالية
        theme_box = QGroupBox("السمة الحالية")
        theme_layout = QVBoxLayout(theme_box)
        self.perf_theme_label = QLabel("-")
        self.perf_theme_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")
        theme_layout.addWidget(self.perf_theme_label)
        grid.addWidget(theme_box)

        # بطاقة: إشعارات غير مقروءة
        notif_box = QGroupBox("الإشعارات غير المقروءة")
        notif_layout = QVBoxLayout(notif_box)
        self.perf_unread_label = QLabel("0")
        self.perf_unread_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")
        notif_layout.addWidget(self.perf_unread_label)
        grid.addWidget(notif_box)

        # بطاقة: حالة قاعدة البيانات
        db_box = QGroupBox("حالة قاعدة البيانات")
        db_layout = QVBoxLayout(db_box)
        self.perf_db_label = QLabel("-")
        self.perf_db_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")
        db_layout.addWidget(self.perf_db_label)
        grid.addWidget(db_box)

        # بطاقة: وقت التشغيل
        uptime_box = QGroupBox("وقت التشغيل")
        uptime_layout = QVBoxLayout(uptime_box)
        self.perf_uptime_label = QLabel("00:00:00")
        self.perf_uptime_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")
        uptime_layout.addWidget(self.perf_uptime_label)
        grid.addWidget(uptime_box)

        layout.addLayout(grid)

        # ملاحظات
        hint = QLabel(self.i18n.get_message("detailed_performance_hint"))
        hint.setStyleSheet("color: rgb(127, 140, 141);")
        layout.addWidget(hint)

        # زر فتح لوحة Database Metrics
        open_db_metrics_btn = QPushButton("📊 Database Metrics - مقاييس قاعدة البيانات")
        open_db_metrics_btn.setMinimumHeight(36)
        open_db_metrics_btn.clicked.connect(self.show_database_metrics)
        layout.addWidget(open_db_metrics_btn)

        # زر فتح اللوحة التفصيلية
        open_perf_btn = QPushButton(self.i18n.get_message("open_detailed_performance"))
        open_perf_btn.setMinimumHeight(36)
        open_perf_btn.clicked.connect(self.show_performance_dashboard)
        layout.addWidget(open_perf_btn)

        # مؤقت التحديث
        self.perf_timer = QTimer(self)
        self.perf_timer.setInterval(5000)  # كل 5 ثوانٍ (خفيف: وقت تشغيل + عداد إشعارات)
        self.perf_timer.timeout.connect(self.update_performance_tab)
        self.perf_timer.start()

        # تحديث أولي
        self.update_performance_tab()

        return tab

    def update_performance_tab(self):
        """تحديث قيم تبويب الأداء"""
        try:
            # الإشعارات
            unread = 0
            if hasattr(self, "notifications_manager") and self.notifications_manager:
                try:
                    unread = self.notifications_manager.unread_count()
                except (AttributeError, RuntimeError) as e:
                    self.logger.debug(f"Notification count failed: {e}")
            self.perf_unread_label.setText(str(unread))
            # لا يوجد حاجة لمحاولة التحقق مرتين من notifications_manager، السطر التالي يكفي:
            # قاعدة البيانات
            db_connected = bool(self.db_manager)
            self.perf_db_label.setText(
                self.i18n.get_message("connected") if db_connected else self.i18n.get_message("disconnected")
            )

            # وقت التشغيل
            if hasattr(self, "app_start_time") and isinstance(self.app_start_time, datetime):
                delta = datetime.now() - self.app_start_time
                total_seconds = int(delta.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                self.perf_uptime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        except (AttributeError, ValueError, TypeError) as e:
            self.logger.debug(f"Performance tab update failed: {e}")

    def create_inventory_tab(self) -> QWidget:
        """إنشاء تبويب المخزون"""
        try:
            if self.logger:
                self.logger.debug("🔨 بدء إنشاء تبويب المخزون...")

            # 🔥 الربط العصبي: ربط الإشارات لتحديث تلقائي (مع منع الاتصالات المكررة)
            try:
                import warnings

                from src.core.signals import signals

                # فك الاتصال أولاً لتجنب الاتصالات المكررة (إذا كانت موجودة)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    try:
                        signals.inventory_updated.disconnect(self.refresh_inventory_data)
                    except (TypeError, RuntimeError):
                        logging.getLogger(__name__).warning("Ignored exception in main_window.py")

                # إنشاء مراجع للـ lambda functions لتجنب الاتصالات المكررة
                if not hasattr(self, "_inventory_item_added_slot"):
                    self._inventory_item_added_slot = lambda product_id: self.refresh_inventory_data()
                if not hasattr(self, "_inventory_item_updated_slot"):
                    self._inventory_item_updated_slot = lambda product_id: self.refresh_inventory_data()
                if not hasattr(self, "_inventory_item_deleted_slot"):
                    self._inventory_item_deleted_slot = lambda product_id: self.refresh_inventory_data()

                # فك الاتصال من الـ slots المخصصة
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    try:
                        signals.inventory_item_added.disconnect(self._inventory_item_added_slot)
                    except (TypeError, RuntimeError):
                        logging.getLogger(__name__).warning("Ignored exception in main_window.py")
                    try:
                        signals.inventory_item_updated.disconnect(self._inventory_item_updated_slot)
                    except (TypeError, RuntimeError):
                        logging.getLogger(__name__).warning("Ignored exception in main_window.py")
                    try:
                        signals.inventory_item_deleted.disconnect(self._inventory_item_deleted_slot)
                    except (TypeError, RuntimeError):
                        logging.getLogger(__name__).warning("Ignored exception in main_window.py")

                # ربط الإشارات
                signals.inventory_updated.connect(self.refresh_inventory_data)
                signals.inventory_item_added.connect(self._inventory_item_added_slot)
                signals.inventory_item_updated.connect(self._inventory_item_updated_slot)
                signals.inventory_item_deleted.connect(self._inventory_item_deleted_slot)

                if self.logger:
                    self.logger.debug("✅ تم ربط إشارات المخزون بنجاح")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ فشل ربط إشارات المخزون: {e}")

            # إنشاء QScrollArea للتمرير
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setFrameShape(QFrame.NoFrame)

            # المحتوى الرئيسي
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setSpacing(12)
            layout.setContentsMargins(12, 12, 12, 12)

            # عنوان القسم
            title = QLabel(self.i18n.get_message("inventory_management"))
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: rgb(39, 174, 96); margin-bottom: 4px;")
            layout.addWidget(title)

            # أزرار سريعة
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(10)

            # تحسينات الأزرار - تصميم موحد مع hover effects
            button_style = """
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: rgb(41, 128, 185);
                }
                QPushButton:pressed {
                    background-color: rgb(32, 102, 148);
                }
                QPushButton:disabled {
                    background-color: rgb(189, 195, 199);
                    color: rgb(127, 140, 141);
                }
            """

            add_product_btn = QPushButton("➕ إضافة منتج")
            add_product_btn.setStyleSheet(button_style)
            add_product_btn.clicked.connect(self.add_product)
            buttons_layout.addWidget(add_product_btn)

            manage_categories_btn = QPushButton(self.i18n.get_message("manage_categories"))
            manage_categories_btn.setStyleSheet(button_style)
            manage_categories_btn.clicked.connect(self.manage_categories)
            buttons_layout.addWidget(manage_categories_btn)

            inventory_report_btn = QPushButton(self.i18n.get_message("inventory_report"))
            inventory_report_btn.setStyleSheet(button_style)
            inventory_report_btn.clicked.connect(self.inventory_report)
            buttons_layout.addWidget(inventory_report_btn)

            adjust_stock_btn = QPushButton("⚖️ تعديل المخزون")
            adjust_stock_btn.setStyleSheet(button_style)
            adjust_stock_btn.clicked.connect(self.open_adjust_stock_dialog)
            buttons_layout.addWidget(adjust_stock_btn)

            transfer_stock_btn = QPushButton("🔁 نقل بين المنتجات")
            transfer_stock_btn.setStyleSheet(button_style)
            transfer_stock_btn.clicked.connect(self.open_transfer_stock_dialog)
            buttons_layout.addWidget(transfer_stock_btn)

            # زر نقل المخزون بين المستودعات (Multi-Warehouse)
            warehouse_transfer_btn = QPushButton("🚚 نقل بين المستودعات")
            warehouse_transfer_btn.setStyleSheet(button_style)
            warehouse_transfer_btn.clicked.connect(self.show_warehouse_transfer_window)
            buttons_layout.addWidget(warehouse_transfer_btn)

            export_inventory_btn = QPushButton("📥 تصدير المنتجات")
            export_inventory_btn.setStyleSheet(button_style)
            export_inventory_btn.clicked.connect(self.export_inventory_data)
            buttons_layout.addWidget(export_inventory_btn)

            buttons_layout.addStretch()
            layout.addLayout(buttons_layout)

            # --- Bento Summary Cards for Inventory ---
            inventory_summary_layout = QHBoxLayout()
            inventory_summary_layout.setSpacing(15)

            # تهيئة قاموس الإحصائيات إذا لم يكن موجوداً
            if not hasattr(self, "inventory_summary_labels"):
                self.inventory_summary_labels = {}

            # Helper to create Bento Cards (Local to this tab or can be moved to class)
            def create_summary_card(title, value, color_code, icon="📊", key_name=None):
                card = QFrame()
                card.setMinimumHeight(100)
                card.setStyleSheet("""
                    QFrame {{
                        background-color: {color_code}15;
                        border: 1px solid {color_code}33;
                        border-radius: 15px;
                    }}
                """)
                c_layout = QVBoxLayout(card)
                c_layout.setContentsMargins(15, 15, 15, 15)

                h_layout = QHBoxLayout()
                t_label = QLabel(
                    f"<span style='font-size: 14px; font-weight: 500; color: {color_code};'>{title}</span>"
                )
                i_label = QLabel(icon)
                i_label.setStyleSheet("font-size: 20px;")
                h_layout.addWidget(t_label)
                h_layout.addStretch()
                h_layout.addWidget(i_label)

                v_label = QLabel(value)
                v_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color_code};")
                v_label.setObjectName(f"val_{title}")  # To update later

                if key_name:
                    self.inventory_summary_labels[key_name] = v_label

                c_layout.addLayout(h_layout)
                c_layout.addWidget(v_label)
                return card

            self.inv_total_products_card = create_summary_card(
                "إجمالي المنتجات", "0", "#2563EB", "📦", "total_products"
            )
            self.inv_total_value_card = create_summary_card(
                "قيمة المخزون", "0.00 دج", "#059669", "💰", "total_stock_value"
            )
            self.inv_low_stock_card = create_summary_card("نقص المخزون", "0", "#DC2626", "⚠️", "low_stock_items")

            inventory_summary_layout.addWidget(self.inv_total_products_card)
            inventory_summary_layout.addWidget(self.inv_total_value_card)
            inventory_summary_layout.addWidget(self.inv_low_stock_card)

            layout.addLayout(inventory_summary_layout)

            # منطقة المرشحات (Glassmorphism Style)
            filters_frame = QFrame()
            filters_frame.setObjectName("inventoryFiltersFrame")
            filters_frame.setStyleSheet(
                "QFrame { "
                "background-color: #000000; "
                "border: 1px solid #333333; "
                "border-radius: 6px; "
                "} "
                f"QLabel { color: {Colors.TEXT_BRIGHT}; font-weight: 600; } "
                f"QLineEdit, QComboBox { background-color: #111111; color: {Colors.TEXT_BRIGHT}; border: 1px solid #444444; border-radius: 4px; padding: 4px; } "  # noqa: E501
                f"QPushButton { background-color: #2563eb; color: {Colors.TEXT_BRIGHT}; font-weight: bold; border-radius: 4px; } "
                "QPushButton:hover { background-color: #1d4ed8; }"
            )
            filters_layout = QHBoxLayout(filters_frame)
            filters_layout.setContentsMargins(12, 8, 12, 8)
            filters_layout.setSpacing(12)

            search_label = QLabel("بحث:")
            search_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
            filters_layout.addWidget(search_label)

            self.inventory_search_input = QLineEdit()
            self.inventory_search_input.setPlaceholderText("ابحث باسم المنتج أو الباركود...")
            # تحسين السلاسة - Debouncing للبحث (تأخير 500ms بعد توقف الكتابة)
            self.inventory_search_input.textChanged.connect(self._on_inventory_search_changed)
            # البحث الفوري عند الضغط على Enter
            self.inventory_search_input.returnPressed.connect(self.on_inventory_filters_changed)
            filters_layout.addWidget(self.inventory_search_input, 2)

            category_label = QLabel("الفئة:")
            category_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
            filters_layout.addWidget(category_label)

            self.inventory_category_combo = QComboBox()
            self.inventory_category_combo.setMinimumWidth(200)
            self.inventory_category_combo.currentIndexChanged.connect(self.on_inventory_filters_changed)
            filters_layout.addWidget(self.inventory_category_combo, 1)

            # فلتر المستودع (Multi-Warehouse)
            warehouse_label = QLabel("المستودع:")
            warehouse_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
            filters_layout.addWidget(warehouse_label)

            self.inventory_warehouse_combo = QComboBox()
            self.inventory_warehouse_combo.setMinimumWidth(200)
            self.inventory_warehouse_combo.addItem("الكل", None)
            self.inventory_warehouse_combo.currentIndexChanged.connect(self.on_inventory_filters_changed)
            filters_layout.addWidget(self.inventory_warehouse_combo, 1)

            # تحميل المستودعات
            self.load_warehouses_for_inventory_filter()

            # أزرار مع تحسينات
            small_button_style = """
                QPushButton {
                    background-color: rgb(236, 240, 241);
                    color: #cbd5e1;
                    border: 1px solid rgb(189, 195, 199);
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 500;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background-color: rgb(189, 195, 199);
                    border-color: rgb(149, 165, 166);
                }
                QPushButton:pressed {
                    background-color: rgb(149, 165, 166);
                }
                QPushButton:disabled {
                    background-color: rgb(236, 240, 241);
                    color: rgb(189, 195, 199);
                    border-color: rgb(236, 240, 241);
                }
            """

            self.inventory_refresh_btn = QPushButton("🔄 تحديث")
            self.inventory_refresh_btn.setStyleSheet(small_button_style)
            self.inventory_refresh_btn.clicked.connect(self.refresh_inventory_data)
            filters_layout.addWidget(self.inventory_refresh_btn)

            # زر تحميل المزيد
            self.inventory_load_more_btn = QPushButton("📥 تحميل المزيد")
            self.inventory_load_more_btn.setStyleSheet(small_button_style)
            self.inventory_load_more_btn.setEnabled(False)
            self.inventory_load_more_btn.clicked.connect(self.load_more_inventory)
            filters_layout.addWidget(self.inventory_load_more_btn)

            layout.addWidget(filters_frame)

            # Phase 2: QTableView with High-Performance Model (بدلاً من QTableWidget)
            self.inventory_table = QTableView()

            # إنشاء Model عالي الأداء
            self.inventory_model = InventoryTableModel(parent=self.inventory_table)
            self.inventory_table.setModel(self.inventory_model)

            # إعدادات الأداء المحسّنة
            self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.inventory_table.setSelectionMode(QAbstractItemView.SingleSelection)
            self.inventory_table.setAlternatingRowColors(True)
            self.inventory_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

            # تحسينات السلاسة - Virtual Scrolling
            # 🔥 ANTI-FREEZE: استخدام ScrollPerItem بدلاً من ScrollPerPixel
            self.inventory_table.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
            self.inventory_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
            self.inventory_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.inventory_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

            # إعدادات Header
            header = self.inventory_table.horizontalHeader()
            # ⚠️ CRITICAL: استخدام Interactive بدلاً من Stretch لتجنب التجميد مع البيانات الكبيرة
            # Stretch يحسب العرض لكل صف، مما يسبب تجميد مع 50K منتج
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setDefaultSectionSize(120)  # عرض افتراضي سريع
            header.setSortIndicatorShown(True)  # إظهار مؤشر الفرز
            header.setSectionsClickable(True)  # السماح بالضغط على الرؤوس للفرز

            # 🔥 استراتيجية التحكم في حجم العرض الاحترافية (Hybrid Sizing)
            # العمود الرئيسي (اسم المنتج) يتمدد، والباقي بحجم معقول وتفاعلي
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Barcode
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Name (The Star)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Category
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Unit
            header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Actions

            # ربط sorting مع Model
            header.sectionClicked.connect(self._on_inventory_header_clicked)

            # 👇👇👇 ANTI-FREEZE FIX: منع التجميد عند فتح التبويب 👇👇👇
            # 1. منع الجدول من حساب ارتفاع 50,000 صف (هذا هو السبب الرئيسي للتعليق)
            v_header = self.inventory_table.verticalHeader()
            v_header.setSectionResizeMode(QHeaderView.Fixed)  # وضع ثابت - لا يحسب الارتفاع
            v_header.setDefaultSectionSize(40)  # ارتفاع 40 بكسل لكل صف (ثابت)
            v_header.setVisible(True)

            # 2. تحسين الأداء عند التمرير الأفقي (تم تطبيقه سابقاً)
            # h_header.setSectionResizeMode(QHeaderView.Interactive) - موجود أعلاه
            # 👆👆👆 انتهى الإصلاح 👆👆👆

            # تحسينات الأداء الإضافية
            self.inventory_table.verticalScrollBar().setSingleStep(20)  # تمرير أسرع
            self.inventory_table.setShowGrid(True)  # إظهار الشبكة

            # 🔥 Modern Action Delegate - أيقونات حديثة مع كشف دقيق للنقرات
            self.inventory_action_delegate = ModernActionDelegate(self.inventory_table)
            # ربط الإشارات (ترسل product_id مباشرة)
            self.inventory_action_delegate.edit_clicked.connect(self._on_inventory_edit_clicked_by_id)
            self.inventory_action_delegate.delete_clicked.connect(self._on_inventory_delete_clicked_by_id)
            # تطبيق Delegate على العمود الأخير (إجراءات - العمود 9)
            self.inventory_table.setItemDelegateForColumn(9, self.inventory_action_delegate)

            # Phase 3: Context Menu (Right-Click Menu)
            self.inventory_table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.inventory_table.customContextMenuRequested.connect(self._show_inventory_context_menu)

            self.inventory_table.setStyleSheet(
                "QTableView, QTableWidget {"
                "background-color: #000000;"
                f"color: {Colors.TEXT_BRIGHT};"
                "gridline-color: #333333;"
                "border: 1px solid #333333;"
                "border-radius: 4px;"
                "}"
                "QTableView::item, QTableWidget::item {"
                "padding: 4px;"
                "border: none;"
                "}"
                "QTableView::item:selected, QTableWidget::item:selected {"
                "background-color: #1e3a8a;"
                f"color: {Colors.TEXT_BRIGHT};"
                "}"
                "QTableView::item:hover, QTableWidget::item:hover {"
                "background-color: #1f2937;"
                "}"
                "QHeaderView::section {"
                "background-color: #111111;"
                f"color: {Colors.TEXT_BRIGHT};"
                "font-weight: bold;"
                "padding: 8px;"
                "border: 1px solid #333333;"
                "}"
                "QScrollBar:vertical {"
                "border: none;"
                "background: #111111;"
                "width: 12px;"
                "border-radius: 6px;"
                "}"
                "QScrollBar::handle:vertical {"
                "background: #333333;"
                "min-height: 30px;"
                "border-radius: 6px;"
                "}"
                "QScrollBar::handle:vertical:hover {"
                "background: #555555;"
                "}"
            )
            layout.addWidget(self.inventory_table)

            # تحميل البيانات الأولية (مع معالجة أخطاء محسّنة)
            try:
                self.load_inventory_filters()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"فشل تحميل مرشحات المخزون: {e}")

            # وضع المحتوى في QScrollArea
            scroll_area.setWidget(tab)

            # تحميل البيانات بعد وضع المحتوى (لتجنب مشاكل التوقيت)
            # استخدام QTimer لتأخير التحميل قليلاً
            # إضافة timeout handling لتجنب التعليق
            def safe_refresh():
                try:
                    self.refresh_inventory_data()
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل تحميل بيانات المخزون: {e}")

            QTimer.singleShot(100, safe_refresh)

            if self.logger:
                self.logger.debug("✅ تم إنشاء تبويب المخزون بنجاح")

            return scroll_area

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            if self.logger:
                self.logger.error(f"❌ خطأ في create_inventory_tab(): {e}\nتفاصيل الخطأ:\n{error_details}",
                    exc_info=True,
                )
            else:

                logging.error(
                    f"❌ خطأ في create_inventory_tab(): {e}\nتفاصيل الخطأ:\n{error_details}",
                    exc_info=True,
                )
            # إرجاع صفحة فارغة مع رسالة خطأ بدلاً من None
            try:
                error_widget = QWidget()
                error_label = QLabel(f"❌ خطأ في تحميل صفحة المخزون:\n{str(e)}\n\nيرجى التحقق من السجلات.")
                error_label.setWordWrap(True)
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
                error_layout = QVBoxLayout(error_widget)
                error_layout.addWidget(error_label)
                return error_widget
            except (RuntimeError, ImportError) as e:
                # إذا فشل حتى إنشاء صفحة الخطأ، أرجع None
                self.logger.error(f"Failed to create inventory error widget: {e}")
                return None

    def _on_inventory_edit_clicked(self, index: QModelIndex):
        """معالجة النقر على زر التعديل في جدول المخزون"""
        try:
            # الحصول على product_id من العمود الأول (id)
            product_id_index = self.inventory_model.index(index.row(), 0)
            product_id = self.inventory_model.data(product_id_index, Qt.UserRole)
            if not product_id:
                # Fallback: الحصول من DisplayRole
                product_id = self.inventory_model.data(product_id_index, Qt.DisplayRole)

            if product_id:
                self._edit_product_by_id(int(product_id))
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تعديل المنتج: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في تعديل المنتج:\n{str(e)}")

    def _on_inventory_delete_clicked(self, index: QModelIndex):
        """معالجة النقر على زر الحذف في جدول المخزون"""
        try:
            # الحصول على product_id من العمود الأول (id)
            product_id_index = self.inventory_model.index(index.row(), 0)
            product_id = self.inventory_model.data(product_id_index, Qt.UserRole)
            if not product_id:
                # Fallback: الحصول من DisplayRole
                product_id = self.inventory_model.data(product_id_index, Qt.DisplayRole)

            if product_id:
                self._delete_product_by_id(int(product_id))
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المنتج: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في حذف المنتج:\n{str(e)}")

    def _on_inventory_edit_clicked_by_id(self, product_id: int):
        """
        🔥 معالجة النقر على أيقونة التعديل (Modern Delegate)
        يستقبل product_id مباشرة من Delegate
        """
        try:
            if product_id and product_id > 0:
                self._edit_product_by_id(int(product_id))
            else:
                if self.logger:
                    self.logger.warning(f"قيمة product_id غير صحيحة: {product_id}")
                QMessageBox.warning(self, "تحذير", "معرف المنتج غير صحيح")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تعديل المنتج: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في تعديل المنتج:\n{str(e)}")

    def _on_inventory_delete_clicked_by_id(self, product_id: int):
        """
        🔥 معالجة النقر على أيقونة الحذف (Modern Delegate)
        يستقبل product_id مباشرة من Delegate
        """
        try:
            if product_id and product_id > 0:
                self._delete_product_by_id(int(product_id))
            else:
                if self.logger:
                    self.logger.warning(f"قيمة product_id غير صحيحة: {product_id}")
                QMessageBox.warning(self, "تحذير", "معرف المنتج غير صحيح")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المنتج: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في حذف المنتج:\n{str(e)}")

    def _edit_product_by_id(self, product_id: int):
        """تعديل منتج حسب المعرف"""
        try:
            # 🔥 CRITICAL FIX: الحصول على كائن Product أولاً
            from src.models.product import ProductManager
            from src.ui.dialogs.product_dialog import ProductDialog

            # الحصول على المنتج من قاعدة البيانات
            product_manager = ProductManager(self.db_manager)
            product = product_manager.get_product_by_id(product_id)

            if not product:
                QMessageBox.warning(self, "تحذير", f"لم يتم العثور على المنتج برقم: {product_id}")
                return

            # إنشاء Dialog مع كائن Product (وليس product_id)
            dialog = ProductDialog(self.db_manager, product=product, parent=self)
            dialog.product_saved.connect(self.on_product_saved)

            if dialog.exec() == QDialog.Accepted:
                if self.logger:
                    self.logger.info(f"تم تعديل المنتج {product_id} بنجاح")
                self.show_success_message("تم تعديل المنتج بنجاح")
                self.refresh_inventory_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تعديل المنتج {product_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في تعديل المنتج:\n{str(e)}")

    def _delete_product_by_id(self, product_id: int):
        """حذف منتج حسب المعرف"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل تريد حذف المنتج (ID: {product_id})؟\nهذا الإجراء لا يمكن التراجع عنه.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if hasattr(self, "inventory_service") and self.inventory_service:
                    self.inventory_service.delete_product(product_id)

                    # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                    try:
                        from src.core.signals import signals

                        signals.inventory_updated.emit()
                        signals.inventory_item_deleted.emit(product_id)
                        if self.logger:
                            self.logger.debug("✅ تم إطلاق إشارات: inventory_updated, inventory_item_deleted")
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")

                    if self.logger:
                        self.logger.info(f"تم حذف المنتج {product_id} بنجاح")
                    self.show_success_message("تم حذف المنتج بنجاح")
                    self.refresh_inventory_data()
                else:
                    QMessageBox.warning(self, "تحذير", "خدمة المخزون غير متاحة.")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"خطأ في حذف المنتج {product_id}: {e}")
                QMessageBox.critical(self, "خطأ", f"فشل في حذف المنتج:\n{str(e)}")

    def _show_inventory_context_menu(self, position):
        """عرض قائمة السياق (Right-Click Menu) لجدول المخزون"""
        try:
            index = self.inventory_table.indexAt(position)
            if not index.isValid():
                return

            # الحصول على product_id
            product_id_index = self.inventory_model.index(index.row(), 0)
            product_id = self.inventory_model.data(product_id_index, Qt.UserRole)
            if not product_id:
                product_id = self.inventory_model.data(product_id_index, Qt.DisplayRole)

            if not product_id:
                return

            # إنشاء القائمة
            menu = QMenu(self)

            edit_action = menu.addAction("✏️ تعديل المنتج")
            edit_action.triggered.connect(lambda: self._edit_product_by_id(int(product_id)))

            delete_action = menu.addAction("🗑️ حذف المنتج")
            delete_action.triggered.connect(lambda: self._delete_product_by_id(int(product_id)))

            menu.addSeparator()

            copy_action = menu.addAction("📋 نسخ معرف المنتج")
            copy_action.triggered.connect(lambda: self._copy_product_id_to_clipboard(int(product_id)))

            menu.exec(self.inventory_table.viewport().mapToGlobal(position))
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في عرض قائمة السياق: {e}")

    def _copy_product_id_to_clipboard(self, product_id: int):
        """نسخ معرف المنتج إلى الحافظة"""
        try:
            from PySide6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setText(str(product_id))
            self.show_success_message(f"تم نسخ معرف المنتج: {product_id}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في نسخ معرف المنتج: {e}")

    def _on_inventory_header_clicked(self, logical_index: int):
        """معالجة الضغط على رأس العمود للفرز"""
        try:
            if not hasattr(self, "inventory_model") or self.inventory_model is None:
                return

            # الحصول على الترتيب الحالي
            header = self.inventory_table.horizontalHeader()
            current_order = header.sortIndicatorOrder()

            # تبديل الترتيب
            new_order = Qt.DescendingOrder if current_order == Qt.AscendingOrder else Qt.AscendingOrder

            # تطبيق الفرز
            self.inventory_model.sort(logical_index, new_order)

            # تحديث مؤشر الفرز
            header.setSortIndicator(logical_index, new_order)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فرز الجدول: {e}")

    def create_sales_tab(self) -> QWidget:
        """إنشاء تبويب المبيعات"""
        # 🔥 الربط العصبي: ربط الإشارات لتحديث تلقائي (مع منع الاتصالات المكررة)
        try:
            import warnings

            from src.core.signals import signals

            # فك الاتصال أولاً لتجنب الاتصالات المكررة (إذا كانت موجودة)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    signals.sales_updated.disconnect(self.refresh_sales_data)
                except (TypeError, RuntimeError):
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")

            # إنشاء مراجع للـ lambda functions لتجنب الاتصالات المكررة
            if not hasattr(self, "_sale_created_slot"):
                self._sale_created_slot = lambda sale_id: self.refresh_sales_data()
            if not hasattr(self, "_sale_updated_slot"):
                self._sale_updated_slot = lambda sale_id: self.refresh_sales_data()
            if not hasattr(self, "_sale_deleted_slot"):
                self._sale_deleted_slot = lambda sale_id: self.refresh_sales_data()

            # فك الاتصال من الـ slots المخصصة
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    signals.sale_created.disconnect(self._sale_created_slot)
                except (TypeError, RuntimeError):
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")
                try:
                    signals.sale_updated.disconnect(self._sale_updated_slot)
                except (TypeError, RuntimeError):
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")
                try:
                    signals.sale_deleted.disconnect(self._sale_deleted_slot)
                except (TypeError, RuntimeError):
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")

            # ربط الإشارات
            signals.sales_updated.connect(self.refresh_sales_data)
            signals.sale_created.connect(self._sale_created_slot)
            signals.sale_updated.connect(self._sale_updated_slot)
            signals.sale_deleted.connect(self._sale_deleted_slot)

            if self.logger:
                self.logger.debug("✅ تم ربط إشارات المبيعات بنجاح")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ فشل ربط إشارات المبيعات: {e}")

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("إدارة المبيعات والفواتير")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: rgb(231, 76, 60); margin-bottom: 4px;")
        layout.addWidget(title)

        # أزرار الإجراءات
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        new_sale_btn = QPushButton("فاتورة جديدة")
        new_sale_btn.setMinimumHeight(36)
        new_sale_btn.clicked.connect(self.new_sale)
        buttons_layout.addWidget(new_sale_btn)

        pos_btn = QPushButton("نقطة البيع")
        pos_btn.setMinimumHeight(36)
        pos_btn.clicked.connect(self.open_pos)
        buttons_layout.addWidget(pos_btn)

        print_receipt_btn = QPushButton("طباعة إيصال")
        print_receipt_btn.setMinimumHeight(36)
        print_receipt_btn.clicked.connect(self.print_selected_sale_receipt)
        print_receipt_btn.setToolTip("طباعة إيصال حراري (للطابعات الحرارية)")
        buttons_layout.addWidget(print_receipt_btn)

        # زر طباعة فاتورة HTML احترافية
        print_invoice_btn = QPushButton("📄 طباعة فاتورة")
        print_invoice_btn.setMinimumHeight(36)
        print_invoice_btn.setToolTip("طباعة فاتورة HTML احترافية في المتصفح")
        print_invoice_btn.clicked.connect(self.print_invoice_html)
        buttons_layout.addWidget(print_invoice_btn)

        export_sales_btn = QPushButton("📥 تصدير الفواتير")
        export_sales_btn.setMinimumHeight(36)
        export_sales_btn.clicked.connect(self.export_sales_data)
        buttons_layout.addWidget(export_sales_btn)

        sales_report_btn = QPushButton("📈 تقرير المبيعات")
        sales_report_btn.setMinimumHeight(36)
        sales_report_btn.clicked.connect(self.sales_report)
        buttons_layout.addWidget(sales_report_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # مرشحات البحث
        filters_frame = QFrame()
        filters_frame.setObjectName("salesFiltersFrame")
        filters_frame.setStyleSheet(
            "QFrame { "
            "background-color: #000000; "
            "border: 1px solid #333333; "
            "border-radius: 6px; "
            "} "
            f"QLabel { color: {Colors.TEXT_BRIGHT}; font-weight: 600; } "
            f"QLineEdit, QComboBox { background-color: #111111; color: {Colors.TEXT_BRIGHT}; border: 1px solid #444444; border-radius: 4px; padding: 4px; } "  # noqa: E501
            f"QPushButton { background-color: #2563eb; color: {Colors.TEXT_BRIGHT}; font-weight: bold; border-radius: 4px; } "
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(12)

        search_label = QLabel("بحث:")
        search_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(search_label)

        self.sales_search_input = QLineEdit()
        self.sales_search_input.setPlaceholderText("ابحث برقم الفاتورة أو اسم العميل...")
        self.sales_search_input.textChanged.connect(self.on_sales_filters_changed)
        filters_layout.addWidget(self.sales_search_input, 2)

        # 🔥 Debouncing للبحث في المبيعات
        self._sales_search_debounce_timer = QTimer(self)
        self._sales_search_debounce_timer.setSingleShot(True)
        self._sales_search_debounce_timer.timeout.connect(self.refresh_sales_data)
        self.sales_search_input.textChanged.connect(lambda text: self._sales_search_debounce_timer.start(500))

        status_label = QLabel("الحالة:")
        status_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(status_label)

        self.sales_status_combo = QComboBox()
        self.sales_status_combo.setMinimumWidth(150)
        self.sales_status_combo.addItems(["الكل", "مسودة", "مؤكدة", "مدفوعة", "مدفوعة جزئياً", "ملغية"])
        self.sales_status_combo.currentIndexChanged.connect(self.on_sales_filters_changed)
        filters_layout.addWidget(self.sales_status_combo, 1)

        payment_label = QLabel("طريقة الدفع:")
        payment_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(payment_label)

        self.sales_payment_combo = QComboBox()
        self.sales_payment_combo.setMinimumWidth(150)
        self.sales_payment_combo.addItems(["الكل", "نقدي", "بطاقة", "تحويل بنكي", "آجل"])
        self.sales_payment_combo.currentIndexChanged.connect(self.on_sales_filters_changed)
        filters_layout.addWidget(self.sales_payment_combo, 1)

        self.sales_refresh_btn = QPushButton("🔄 تحديث")
        self.sales_refresh_btn.setMinimumHeight(32)
        self.sales_refresh_btn.clicked.connect(self.refresh_sales_data)
        filters_layout.addWidget(self.sales_refresh_btn)

        layout.addWidget(filters_frame)

        # ملخص المبيعات
        summary_group = QGroupBox("ملخص المبيعات")
        summary_layout = QHBoxLayout(summary_group)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(18)

        summary_items = [
            ("total_invoices", "إجمالي الفواتير"),
            ("total_revenue", "إجمالي الإيرادات"),
            ("total_paid", "المبلغ المدفوع"),
            ("total_remaining", "المبلغ المتبقي"),
            ("avg_invoice_value", "متوسط قيمة الفاتورة"),
        ]

        self.sales_summary_labels = {}
        for key, title_text in summary_items:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)

            title_label = QLabel(title_text)
            title_label.setStyleSheet("color: rgb(127, 140, 141); font-size: 12px;")
            value_label = QLabel("-")
            value_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")

            container_layout.addWidget(title_label)
            container_layout.addWidget(value_label)
            container_layout.addStretch()

            summary_layout.addWidget(container)
            self.sales_summary_labels[key] = value_label

        summary_layout.addStretch()
        layout.addWidget(summary_group)

        # 🔥 جدول المبيعات عالي الأداء (QTableView + Model)
        self.sales_table = QTableView()
        self.sales_model = SalesTableModel(parent=self.sales_table)
        self.sales_table.setModel(self.sales_model)

        # إعدادات الأداء
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # تمت إزالة الـ setStyleSheet المحلي للسماح للثيم الموحد (modern_glass.qss) بالعمل
        self.sales_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # إعدادات Header
        header = self.sales_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(120)
        header.setDefaultSectionSize(150)
        header.setStretchLastSection(True)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # عمود الإجراءات
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(lambda index: self.sales_model.sort(index, header.sortIndicatorOrder()))

        # 🔥 Modern Action Delegate
        self.sales_action_delegate = ModernActionDelegate(self.sales_table)
        self.sales_action_delegate.edit_clicked.connect(self._on_sale_edit_clicked)
        self.sales_action_delegate.delete_clicked.connect(self._on_sale_delete_clicked)
        self.sales_table.setItemDelegateForColumn(9, self.sales_action_delegate)

        # ربط النقر المزدوج لعرض التفاصيل
        # QTableView يستخدم doubleClicked (ليس itemDoubleClicked)
        self.sales_table.doubleClicked.connect(self.on_sale_double_clicked)
        layout.addWidget(self.sales_table)

        # تحميل البيانات الأولية
        self.refresh_sales_data()

        return tab

    def _on_sale_edit_clicked(self, sale_id: int):
        """معالجة النقر على أيقونة التعديل في جدول المبيعات"""
        try:
            if sale_id > 0:
                self.edit_sale(sale_id)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تعديل الفاتورة {sale_id}: {e}", exc_info=True)

    def _on_sale_delete_clicked(self, sale_id: int):
        """معالجة النقر على أيقونة الحذف في جدول المبيعات"""
        try:
            if sale_id > 0:
                reply = QMessageBox.question(
                    self,
                    "تأكيد الحذف",
                    f"هل تريد حذف الفاتورة رقم {sale_id}؟",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    if self.logger:
                        self.logger.info(f"طلب حذف/إلغاء الفاتورة {sale_id}")
                    if hasattr(self, "sales_service") and self.sales_service:
                        success = self.sales_service.cancel_sale(sale_id)
                        if success:
                            QMessageBox.information(self, "نجاح", f"تم إلغاء الفاتورة رقم {sale_id} بنجاح")
                        else:
                            QMessageBox.warning(self, "فشل", f"لم يتم إلغاء الفاتورة رقم {sale_id}")
                    self.refresh_sales_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف الفاتورة {sale_id}: {e}", exc_info=True)

    def print_selected_sale_receipt(self):
        """Prints a receipt for the currently selected sale."""
        if not hasattr(self, "printing_service") or not self.printing_service:
            QMessageBox.critical(self, "خطأ", "خدمة الطباعة غير متوفرة.")
            return

        selected_rows = self.sales_table.selectionModel().selectedRows()
        if not selected_rows or not hasattr(self, "sales_model"):
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد فاتورة لطباعتها.")
            return

        selected_row = selected_rows[0].row()
        index = self.sales_model.index(selected_row, 0)
        sale_id = self.sales_model.data(index, Qt.UserRole) if index.isValid() else None
        if not sale_id:
            QMessageBox.warning(self, "خطأ", "لا يمكن العثور على معرّف الفاتورة.")
            return

        try:
            # Use sales_service for fetching sale details (db_manager.get_sale doesn't exist)
            if hasattr(self, "sales_service") and self.sales_service:
                sale_details = self.sales_service.get_sale_details(sale_id)
            else:
                sale_details = None
            if not sale_details:
                QMessageBox.warning(self, "خطأ", "لم يتم العثور على تفاصيل الفاتورة.")
                return

            from PySide6.QtCore import QSettings

            s = QSettings("StandardElJoumla", "ERP")
            printer_config = {
                "vendor_id": s.value("printer/vendor_id", type=int),
                "product_id": s.value("printer/product_id", type=int),
            }

            if not printer_config.get("vendor_id") or not printer_config.get("product_id"):
                QMessageBox.critical(self, "خطأ", "لم يتم تكوين طابعة. يرجى تحديد طابعة في الإعدادات.")
                return

            success, message = self.printing_service.print_receipt(printer_config, sale_details)

            if success:
                QMessageBox.information(self, "نجاح", "تم إرسال الإيصال إلى الطابعة.")
                if sale_details.get("payment_method") == "نقدي":
                    self.printing_service.open_cash_drawer(printer_config)
            else:
                QMessageBox.critical(self, "فشل الطباعة", f"حدث خطأ أثناء الطباعة: {message}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تجهيز الطباعة: {e}")

    def print_invoice_html(self):
        """
        🖨️ طباعة فاتورة HTML احترافية (باستخدام PrintService)
        """
        if not hasattr(self, "print_service") or not self.print_service:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "خطأ", "خدمة الطباعة المتقدمة غير متوفرة.")
            return

        # الحصول على الفاتورة المحددة
        if not hasattr(self, "sales_table"):
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "تنبيه", "جدول المبيعات غير متاح.")
            return

        selected_rows = self.sales_table.selectionModel().selectedRows()
        if not selected_rows or not hasattr(self, "sales_model"):
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "تنبيه", "يرجى تحديد فاتورة لطباعتها.")
            return

        model_index = selected_rows[0]
        from PySide6.QtCore import Qt

        sale_id = self.sales_model.data(self.sales_model.index(model_index.row(), 0), Qt.UserRole)

        if not sale_id:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "خطأ", "لا يمكن العثور على معرّف الفاتورة.")
            return

        try:
            result = self.print_service.print_invoice(sale_id=sale_id)
            if result.get("success"):
                import os
                import tempfile
                import webbrowser

                html_content = result.get("html")
                with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as f:
                    f.write(html_content)
                    temp_path = f.name

                # فتح المتصفح
                webbrowser.open(f"file:///{temp_path.replace(os.sep, '/')}")
                self.statusBar().showMessage("✅ تم فتح الفاتورة المتقدمة في المتصفح", 5000)
            else:
                from PySide6.QtWidgets import QMessageBox

                message = result.get("error", "خطأ غير معروف")
                QMessageBox.critical(self, "فشل الطباعة", f"حدث خطأ أثناء طباعة الفاتورة:\n{message}")
        except Exception as e:
            error_msg = f"خطأ في طباعة الفاتورة: {str(e)}"
            if self.logger:
                self.logger.error(error_msg, exc_info=True)
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "خطأ", error_msg)

    def refresh_sales_data(self):
        """تحديث بيانات جدول المبيعات (محسّنة - في الخلفية)"""
        if not hasattr(self, "sales_table"):
            return

        if not getattr(self, "sales_service", None):
            self.sales_table.setRowCount(0)
            return

        # Throttling - منع التحديثات المتكررة
        if self._is_updating:
            return

        self._is_updating = True
        start_time = time.perf_counter()
        self._sales_load_started = start_time

        try:
            # تعطيل الأزرار أثناء التحديث
            if hasattr(self, "sales_refresh_btn"):
                self.sales_refresh_btn.setEnabled(False)
                self.sales_refresh_btn.setText("⏳ جاري التحديث...")

            # جمع معاملات البحث
            status_text = self.sales_status_combo.currentText() if hasattr(self, "sales_status_combo") else "الكل"
            payment_text = self.sales_payment_combo.currentText() if hasattr(self, "sales_payment_combo") else "الكل"
            search_term = self.sales_search_input.text().strip() if hasattr(self, "sales_search_input") else ""

            # تحويل الحالة
            status = None
            if status_text != "الكل":
                status_map = {
                    "مسودة": "draft",
                    "مؤكدة": "confirmed",
                    "مدفوعة": "paid",
                    "مدفوعة جزئياً": "partially_paid",
                    "ملغية": "cancelled",
                }
                status = status_map.get(status_text)

            # تحويل طريقة الدفع
            payment_method = None
            if payment_text != "الكل":
                payment_map = {
                    "نقدي": "cash",
                    "بطاقة": "card",
                    "تحويل بنكي": "bank_transfer",
                    "آجل": "credit",
                }
                payment_method = payment_map.get(payment_text)

            # تحميل البيانات في الخلفية باستخدام Worker
            def load_sales():
                """تحميل بيانات المبيعات في الخلفية"""
                try:
                    sales_list = self.sales_service.list_sales(
                        search_term=search_term if search_term else None,
                        status=status,
                        payment_method=payment_method,
                        limit=500,
                    )
                    # حساب الملخص من جميع الفواتير (بدون فلترة التاريخ) أو من الفواتير المحملة
                    # إذا كانت هناك فلاتر، نحسب من sales_list مباشرة
                    if sales_list:
                        # حساب الملخص من البيانات المحملة
                        total_invoices = len(sales_list)
                        total_revenue = sum(float(s.get("total_amount", 0) or 0) for s in sales_list)
                        total_paid = sum(float(s.get("paid_amount", 0) or 0) for s in sales_list)
                        total_remaining = sum(float(s.get("remaining_amount", 0) or 0) for s in sales_list)
                        avg_invoice_value = total_revenue / total_invoices if total_invoices > 0 else 0.0

                        summary = {
                            "total_invoices": total_invoices,
                            "total_revenue": total_revenue,
                            "total_amount": total_revenue,  # للتوافق
                            "total_paid": total_paid,
                            "total_remaining": total_remaining,
                            "avg_invoice_value": avg_invoice_value,
                        }
                    else:
                        # إذا لم تكن هناك بيانات، جلب الملخص من قاعدة البيانات
                        summary = self.sales_service.get_sales_summary()
                    return {"sales": sales_list, "summary": summary}
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"خطأ في تحميل بيانات المبيعات: {e}")
                    return None

            # إنشاء Worker وتشغيله
            sales_worker = DataLoaderWorker(load_sales)
            # 🔥 استخدام SalesDataLoaderThread الجديد
            db_path = (  # noqa: F841
                self.db_manager.db_path if hasattr(self.db_manager, "db_path") else "data/standard_eljoumla.db"
            )  # noqa: F841
            sales_worker = SalesDataLoaderThread(
                db_manager=self.db_manager,
                search_term=search_term,
                status=status,
                payment_method=payment_method,
            )
            sales_worker.data_loaded.connect(self._on_sales_data_loaded)

            # معالج الأخطاء مع Safety Net لإعادة تشغيل المؤقت
            def handle_sales_error(err):
                QMessageBox.critical(self, "خطأ", f"فشل تحميل بيانات المبيعات:\n{err}")
                self._is_updating = False
                self._log_section_duration("refresh_sales_data", start_time, threshold_ms=1000.0)
                # إعادة تفعيل زر التحديث
                if hasattr(self, "sales_refresh_btn"):
                    try:
                        self.sales_refresh_btn.setEnabled(True)
                        self.sales_refresh_btn.setText("🔄 تحديث")
                    except RuntimeError:
                        # الزر تم حذفه (libshiboken) - نتجاهله بأمان
                        del self.sales_refresh_btn
                # ✅ Safety Net: إعادة تشغيل مراقب الجلسة في حالة فشل Worker
                if hasattr(self, "session_monitor_timer") and self.session_monitor_timer:
                    if not self.session_monitor_timer.isActive():
                        if self.logger:
                            self.logger.debug(
                                "▶️ إعادة تشغيل session_monitor_timer (بعد خطأ Worker في refresh_sales_data)"
                            )
                        self.session_monitor_timer.start(60000)

            sales_worker.error_occurred.connect(handle_sales_error)
            self._start_worker(sales_worker)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في refresh_sales_data: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات المبيعات:\n{str(e)}")
            self._is_updating = False
            self._log_section_duration("refresh_sales_data", start_time, threshold_ms=1000.0)
        finally:
            # ✅ Safety Net: إعادة تشغيل مراقب الجلسة مضمونة 100% حتى لو حدث خطأ
            # (سيتم إعادة التشغيل مرة أخرى في _on_sales_data_loaded() لكن هذا يضمن عدم الموت)
            if hasattr(self, "session_monitor_timer") and self.session_monitor_timer:
                if not self.session_monitor_timer.isActive():
                    if self.logger:
                        self.logger.debug("▶️ إعادة تشغيل session_monitor_timer (Safety Net في refresh_sales_data)")
                    self.session_monitor_timer.start(60000)  # كل 60 ثانية

    def _on_sales_data_loaded(self, data):
        """معالجة بيانات المبيعات المحمّلة"""
        import pandas as pd

        try:
            # 🔥 التحقق من نوع البيانات: DataFrame أو dict
            if isinstance(data, pd.DataFrame):
                # البيانات من SalesDataLoaderThread (DataFrame مباشرة)
                df = data
            elif isinstance(data, dict) and "sales" in data:
                # البيانات من DataLoaderWorker القديم (dict)
                sales_list = data["sales"]
                summary = data.get("summary")
                df = pd.DataFrame(sales_list) if sales_list else pd.DataFrame()
            else:
                # بيانات غير صالحة
                if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                    if self.logger:
                        self.logger.warning("⚠️ لا توجد بيانات مبيعات للعرض")
                self._is_updating = False
                return

            # التحقق من أن DataFrame غير فارغ
            if df.empty:
                if self.logger:
                    self.logger.warning("⚠️ DataFrame فارغ - لا توجد بيانات للعرض")
                self._is_updating = False
                return

            # 🔥 استخدام SalesTableModel بدلاً من ملء الجدول يدوياً
            if not hasattr(self, "sales_model") or self.sales_model is None:
                if self.logger:
                    self.logger.error("❌ sales_model غير موجود - لا يمكن تحديث البيانات")
                self._is_updating = False
                return

            # تعطيل التحديثات أثناء التعبئة
            self.sales_table.setUpdatesEnabled(False)

            # تحديث النموذج بالبيانات الجديدة
            self.sales_model.setData(df)

            # حساب الملخص من DataFrame
            try:
                total_invoices = len(df)
                total_revenue = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0).sum()
                total_paid = pd.to_numeric(df["paid_amount"], errors="coerce").fillna(0).sum()
                total_remaining = total_revenue - total_paid
                avg_invoice_value = total_revenue / total_invoices if total_invoices > 0 else 0

                summary = {
                    "total_invoices": total_invoices,
                    "total_revenue": total_revenue,
                    "total_paid": total_paid,
                    "total_remaining": total_remaining,
                    "avg_invoice_value": avg_invoice_value,
                }

                # تحديث الملخص
                self.update_sales_summary(summary)

                if self.logger:
                    self.logger.debug(f"✅ تم تحديث بيانات المبيعات: {total_invoices} فاتورة")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"فشل حساب إحصائيات المبيعات: {e}")

            # الكود القديم (ملء QTableWidget يدوياً) - تم إزالته
            # لأننا نستخدم SalesTableModel الآن

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في _on_sales_data_loaded: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في معالجة بيانات المبيعات:\n{str(e)}")
        finally:
            # إعادة تفعيل التحديثات
            self.sales_table.setUpdatesEnabled(True)

            # إعادة تفعيل الأزرار
            if hasattr(self, "sales_refresh_btn"):
                self.sales_refresh_btn.setEnabled(True)
                self.sales_refresh_btn.setText("🔄 تحديث")

            self._is_updating = False

            # ✅ إعادة تشغيل مراقب الجلسة بعد أن هدأ الوضع
            if hasattr(self, "session_monitor_timer") and self.session_monitor_timer:
                if not self.session_monitor_timer.isActive():
                    if self.logger:
                        self.logger.debug("▶️ إعادة تشغيل session_monitor_timer بعد انتهاء تحميل المبيعات")
                    self.session_monitor_timer.start(60000)  # كل 60 ثانية

            # تسجيل المدة
            start_value = getattr(self, "_sales_load_started", None)
            if start_value:
                self._log_section_duration("refresh_sales_data", start_value, threshold_ms=1000.0)
                self._sales_load_started = None

    def update_sales_summary(self, summary):
        """تحديث ملخص المبيعات"""
        if not hasattr(self, "sales_summary_labels"):
            return

        def set_label(key, value):
            label = self.sales_summary_labels.get(key)
            if not label:
                return
            if isinstance(value, (int, float)):
                if key in (
                    "total_revenue",
                    "total_paid",
                    "total_remaining",
                    "avg_invoice_value",
                ):
                    label.setText(f"{value:,.2f} د.ج")
                else:
                    label.setText(f"{value:,}")
            else:
                label.setText(str(value))

        set_label("total_invoices", summary.get("total_invoices", 0))
        set_label("total_revenue", summary.get("total_revenue", 0))
        set_label("total_paid", summary.get("total_paid", 0))
        set_label("total_remaining", summary.get("total_remaining", 0))
        set_label("avg_invoice_value", summary.get("avg_invoice_value", 0))

    def on_sales_filters_changed(self):
        """التعامل مع تغيير مرشحات المبيعات"""
        self.refresh_sales_data()

    def on_sale_double_clicked(self, index: QModelIndex):
        """فتح تفاصيل الفاتورة عند النقر المزدوج"""
        try:
            if not index.isValid():
                return

            if not hasattr(self, "sales_model") or not self.sales_model:
                return

            # الحصول على sale_id من النموذج (من العمود الأول باستخدام UserRole)
            sale_id = self.sales_model.data(self.sales_model.index(index.row(), 0), Qt.UserRole)

            if sale_id and sale_id > 0:
                self.edit_sale(sale_id)
            else:
                if self.logger:
                    self.logger.warning(f"⚠️ لم يتم العثور على sale_id للصف {index.row()}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في on_sale_double_clicked: {e}")
            import traceback

            if self.logger:
                self.logger.error(traceback.format_exc())

    def edit_sale(self, sale_id):
        """تعديل فاتورة موجودة"""
        if not sale_id:
            return

        try:
            # الحصول على بيانات الفاتورة
            sale = self.sales_service.sale_manager.get_sale_by_id(sale_id)
            if not sale:
                QMessageBox.warning(self, "تحذير", f"لم يتم العثور على الفاتورة رقم {sale_id}")
                return

            # فتح نافذة الفاتورة في وضع التعديل
            from ..dialogs.sales_dialog import SalesDialog

            dialog = SalesDialog(self.db_manager, sale=sale, parent=self)

            # ربط إشارة إتمام البيع
            dialog.sale_completed.connect(self.on_sale_completed)

            if dialog.exec() == QDialog.Accepted:
                # تحديث جدول المبيعات بعد التعديل
                self.refresh_sales_data()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تعديل الفاتورة:\n{str(e)}")

    def view_sale_details(self, sale_id):
        """عرض تفاصيل الفاتورة (النقر المزدوج)"""
        # استخدام نفس دالة التعديل
        self.edit_sale(sale_id)

    # ===== إدارة المشتريات =====
    def load_purchase_suppliers(self):
        """تحميل قائمة الموردين في مرشح المشتريات"""
        if not hasattr(self, "purchase_supplier_combo"):
            return

        try:

            if getattr(self, "supplier_manager", None):
                suppliers = self.supplier_manager.get_all_suppliers(active_only=True)
                for supplier in suppliers:
                    self.purchase_supplier_combo.addItem(supplier.name, supplier.id)
            else:
                self.purchase_supplier_combo.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الموردين:\n{str(e)}")
        finally:
            self.purchase_supplier_combo.blockSignals(False)

    def refresh_purchases_data(self):
        """تحديث بيانات جدول المشتريات"""
        if not hasattr(self, "purchases_table"):
            return

        if not getattr(self, "purchase_service", None):
            self.purchases_table.setRowCount(0)
            return

        start_time = time.perf_counter()
        try:
            supplier_id = (
                self.purchase_supplier_combo.currentData() if hasattr(self, "purchase_supplier_combo") else None
            )
            search_term = self.purchase_search_input.text().strip() if hasattr(self, "purchase_search_input") else ""
            status = self.purchase_status_combo.currentText() if hasattr(self, "purchase_status_combo") else "الكل"
            payment_status = (
                self.purchase_payment_status_combo.currentText()
                if hasattr(self, "purchase_payment_status_combo")
                else "الكل"
            )

            purchases = self.purchase_service.list_purchases(
                search_term=search_term if search_term else None,
                supplier_id=supplier_id,
                status=None if status == "الكل" else status,
                payment_status=None if payment_status == "الكل" else payment_status,
                limit=500,
            )

            # Quick Win: Disable updates during batch operations
            self.purchases_table.setUpdatesEnabled(False)

            self.purchases_table.setRowCount(len(purchases))

            # Quick Win: Set uniform row height ONCE before loop
            self.purchases_table.verticalHeader().setDefaultSectionSize(40)

            for row_index, purchase in enumerate(purchases):
                row_data = [
                    purchase.get("invoice_number", "-"),
                    purchase.get("supplier_name", "-"),
                    purchase.get("purchase_date", "-"),
                    f"{purchase.get('total_amount', 0):,.2f}",
                    f"{purchase.get('paid_amount', 0):,.2f}",
                    f"{purchase.get('remaining_amount', 0):,.2f}",
                    purchase.get("status", "-"),
                    purchase.get("payment_status", "-"),
                ]

                for col_index, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    if col_index in (3, 4, 5):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)

                    if col_index == 0:
                        item.setData(Qt.UserRole, purchase.get("id"))

                    if col_index == 6:
                        status_val = str(purchase.get("status", "")).lower()
                        if "مستلمة" in status_val or "received" in status_val:
                            item.setForeground(QColor("#27ae60"))
                        elif "جزئية" in status_val or "partial" in status_val:
                            item.setForeground(QColor("#f39c12"))
                        elif "ملغية" in status_val or "cancelled" in status_val:
                            item.setForeground(QColor("#e74c3c"))
                        else:
                            item.setForeground(QColor("#2980b9"))

                    if col_index == 7:
                        payment_val = str(purchase.get("payment_status", "")).lower()
                        if "مدفوعة" in payment_val or "paid" in payment_val:
                            item.setForeground(QColor("#27ae60"))
                        elif "جزئياً" in payment_val or "partial" in payment_val:
                            item.setForeground(QColor("#f39c12"))
                        elif "متأخرة" in payment_val or "overdue" in payment_val:
                            item.setForeground(QColor("#e74c3c"))

                    self.purchases_table.setItem(row_index, col_index, item)

                # REMOVED: setRowHeight() from inside loop - using setDefaultSectionSize() above

            # ---------------------------------------------------------
            # 🛠️ الإصلاح: حساب الإحصائيات مباشرة من purchases list
            # ---------------------------------------------------------
            if purchases and hasattr(self, "purchase_summary_labels"):
                try:
                    import pandas as pd

                    purchases_df = pd.DataFrame(purchases)

                    if not purchases_df.empty:
                        total_purchases = len(purchases_df)

                        # البحث عن أعمدة المبالغ
                        total_col = None
                        paid_col = None

                        for col in purchases_df.columns:
                            col_lower = str(col).lower()
                            if "total" in col_lower and ("amount" in col_lower or "value" in col_lower):
                                total_col = col
                            if "paid" in col_lower and "amount" in col_lower:
                                paid_col = col

                        total_amount = 0.0
                        total_paid = 0.0

                        if total_col:
                            total_amount = pd.to_numeric(purchases_df[total_col], errors="coerce").fillna(0).sum()
                        if paid_col:
                            total_paid = pd.to_numeric(purchases_df[paid_col], errors="coerce").fillna(0).sum()

                        total_debt = total_amount - total_paid
                        avg_purchase_value = total_amount / total_purchases if total_purchases > 0 else 0

                        # تحديث الـ Labels مباشرة
                        def set_label(key, value):
                            if hasattr(self, "purchase_summary_labels") and key in self.purchase_summary_labels:
                                label = self.purchase_summary_labels[key]
                                if isinstance(value, (int, float)):
                                    if key in (
                                        "total_amount",
                                        "total_paid",
                                        "total_debt",
                                        "avg_purchase_value",
                                    ):
                                        label.setText(f"{value:,.2f} دج")
                                    else:
                                        label.setText(f"{value:,}")
                                else:
                                    label.setText(str(value))

                        set_label("total_purchases", total_purchases)
                        set_label("total_amount", total_amount)
                        set_label("total_paid", total_paid)
                        set_label("total_debt", total_debt)
                        set_label("avg_purchase_value", avg_purchase_value)

                        if self.logger:
                            self.logger.debug(
                                f"✅ تم تحديث إحصائيات المشتريات مباشرة من البيانات: {total_purchases} عملية"
                            )
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل حساب إحصائيات المشتريات من البيانات: {e}")

            # تحديث الملخص من الخدمة (كـ backup)
            try:
                summary = self.purchase_service.get_purchases_summary()
                if summary:
                    self.update_purchases_summary(summary)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"فشل جلب ملخص المشتريات من الخدمة: {e}")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات المشتريات:\n{str(e)}")
        finally:
            # Quick Win: Re-enable updates after batch operations
            self.purchases_table.setUpdatesEnabled(True)
            self._log_section_duration("refresh_purchases_data", start_time)

            # ✅ إعادة تشغيل مراقب الجلسة بعد أن هدأ الوضع
            if hasattr(self, "session_monitor_timer") and self.session_monitor_timer:
                if not self.session_monitor_timer.isActive():
                    if self.logger:
                        self.logger.debug("▶️ إعادة تشغيل session_monitor_timer بعد انتهاء تحميل المشتريات")
                    self.session_monitor_timer.start(60000)  # كل 60 ثانية

    def update_purchases_summary(self, summary):
        """تحديث ملخص المشتريات"""
        if not hasattr(self, "purchase_summary_labels"):
            return

        def set_label(key, value):
            label = self.purchase_summary_labels.get(key)
            if label is None:
                return
            if isinstance(value, (int, float)):
                if key in (
                    "total_amount",
                    "total_paid",
                    "total_remaining",
                    "avg_purchase_value",
                ):
                    label.setText(f"{value:,.2f} د.ج")
                else:
                    label.setText(f"{value:,}")
            else:
                label.setText(str(value))

        set_label("total_purchases", summary.get("total_purchases", 0))
        set_label("total_amount", summary.get("total_amount", 0))
        set_label("total_paid", summary.get("total_paid", 0))
        set_label("total_remaining", summary.get("total_remaining", 0))
        set_label("avg_purchase_value", summary.get("avg_purchase_value", 0))

    def on_purchases_filters_changed(self):
        """التعامل مع تغير مرشحات المشتريات"""
        self.refresh_purchases_data()

    def on_purchase_double_clicked(self, item):
        """فتح تفاصيل المشتريات عند النقر المزدوج"""
        purchase_id = item.data(Qt.UserRole)
        if purchase_id:
            self.view_purchase_details(purchase_id)

    def view_purchase_details(self, purchase_id):
        """عرض تفاصيل فاتورة الشراء"""
        if not purchase_id:
            return

        try:

            purchase = self.purchase_service.get_purchase_by_id(purchase_id)
            if not purchase:
                QMessageBox.warning(self, "تحذير", f"لم يتم العثور على فاتورة الشراء رقم {purchase_id}")
                return

            details = (
                f"<h3>فاتورة شراء {purchase.invoice_number}</h3>"
                f"<p>المورد: <b>{getattr(purchase, 'supplier_name', '') or 'غير محدد'}</b></p>"
                f"<p>التاريخ: {purchase.purchase_date}</p>"
                f"<p>القيمة الإجمالية: {float(purchase.total_amount):,.2f} د.ج</p>"
                f"<p>المدفوع: {float(purchase.paid_amount):,.2f} د.ج</p>"
                f"<p>المتبقي: {float(purchase.remaining_amount):,.2f} د.ج</p>"
                f"<p>حالة الاستلام: {purchase.status}</p>"
                f"<p>حالة الدفع: {purchase.payment_status}</p>"
            )

            QMessageBox.information(self, "تفاصيل فاتورة الشراء", details)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في عرض تفاصيل فاتورة الشراء:\n{str(e)}")

    def receive_purchase_shipment(self):
        """استلام شحنة مشتريات (واجهة مبسطة حالياً)"""
        if not getattr(self, "db_manager", None):
            QMessageBox.warning(self, "تحذير", "قاعدة البيانات غير متصلة")
            return

        window = self.window_manager.open_window("purchase_orders", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة أوامر الشراء")

    # ===== لوحة التقارير =====
    def set_report_quick_range(self, days: int):
        """تعيين نطاق زمني سريع للتقارير"""
        if not hasattr(self, "report_start_date") or not hasattr(self, "report_end_date"):
            return
        try:
            end_date = QDate.currentDate()
            start_date = end_date.addDays(-days)
            self.report_start_date.setDate(start_date)
            self.report_end_date.setDate(end_date)
            self.refresh_reports_data()
        except (AttributeError, ValueError, TypeError) as e:
            self.logger.warning(f"Quick date range failed: {e}")

    def refresh_reports_data(self):
        """تحديث بيانات تبويب التقارير"""
        if not hasattr(self, "reports_summary_labels"):
            return
        if not getattr(self, "dashboard_service", None):
            QMessageBox.warning(self, "تحذير", "خدمة لوحات المعلومات غير متوفرة")
            return

        # إظهار مؤشر التحميل
        self._show_reports_loading(True)

        start_time = time.perf_counter()
        try:
            # الحصول على التواريخ من الواجهة
            start_date = (
                self._qdate_to_date(self.report_start_date.date())
                if hasattr(self, "report_start_date")
                else date.today() - timedelta(days=30)
            )
            end_date = (
                self._qdate_to_date(self.report_end_date.date()) if hasattr(self, "report_end_date") else date.today()
            )

            # التحقق من صحة النطاق الزمني
            if start_date > end_date:
                QMessageBox.warning(self, "تحذير", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
                return

            # حساب عدد الأيام للتحقق من الأداء
            days_diff = (end_date - start_date).days
            if days_diff > 365:
                reply = QMessageBox.question(
                    self,
                    "تحذير",
                    f"النطاق الزمني المحدد كبير ({days_diff} يوم). قد يستغرق التحميل وقتاً طويلاً.\nهل تريد المتابعة؟",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

            # الحصول على بيانات لوحة المعلومات
            dashboard_data = self.dashboard_service.load_dashboard(start_date, end_date)

            purchase_summary = {}
            if getattr(self, "purchase_service", None):
                purchase_summary = self.purchase_service.get_purchases_summary(start_date, end_date)

            # جلب بيانات الإيرادات مقابل المشتريات
            revenue_data = self._get_revenue_vs_expense_data(start_date, end_date)

            receivables_total = 0.0
            payables_total = 0.0
            if getattr(self, "payment_service", None):
                try:
                    receivables = self.payment_service.get_accounts_receivable()
                    receivables_total = sum(float(r.get("balance", 0)) for r in receivables)
                    payables = self.payment_service.get_accounts_payable()
                    payables_total = sum(float(p.get("balance", 0)) for p in payables)
                except (AttributeError, ValueError, TypeError) as e:
                    self.logger.warning(f"Payment accounts fetch failed: {e}")

            # تحديث الواجهة
            self.update_reports_summary(dashboard_data, purchase_summary, receivables_total, payables_total)
            self.update_top_products_table(dashboard_data.top_products)
            self.update_payment_distribution_table(dashboard_data.distribution)
            self.update_revenue_vs_expense_table(revenue_data)

            # إظهار رسالة نجاح للفترات الكبيرة
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > 1.0 and self.logger:
                self.logger.info(f"تم تحميل بيانات التقارير في {elapsed_time:.2f} ثانية")

        except Exception as e:
            error_msg = str(e)
            if self.logger:
                self.logger.error(f"فشل في تحميل بيانات التقارير: {error_msg}")
            QMessageBox.critical(
                self,
                "خطأ",
                f"فشل في تحميل بيانات التقارير:\n{error_msg}\n\nيرجى التحقق من الاتصال بقاعدة البيانات والمحاولة مرة أخرى.",  # noqa: E501
            )
        finally:
            # إخفاء مؤشر التحميل
            self._show_reports_loading(False)
            self._log_section_duration("refresh_reports_data", start_time, threshold_ms=500.0)

    def update_reports_summary(
        self,
        dashboard_data,
        purchase_summary,
        receivables_total=0.0,
        payables_total=0.0,
    ):
        """تحديث بطاقات المؤشرات"""
        if not hasattr(self, "reports_summary_labels"):
            return

        try:

            def set_label(key, value):
                label = self.reports_summary_labels.get(key)
                if not label:
                    return
                if key == "profit_margin":
                    label.setText(f"{value:.2f}%")
                elif key in (
                    "total_sales",
                    "total_purchases",
                    "gross_profit",
                    "receivables",
                    "payables",
                ):
                    label.setText(f"{value:,.2f} د.ج")
                else:
                    label.setText(f"{value:,.2f}")

            total_sales = self._get_kpi_value(dashboard_data.kpis, "total_sales")
            gross_profit = self._get_kpi_value(dashboard_data.kpis, "gross_profit")
            profit_margin = self._get_kpi_value(dashboard_data.kpis, "profit_margin")

            # استخدام القيم من payment_service إذا كانت متوفرة، وإلا من dashboard
            receivables = (
                receivables_total if receivables_total > 0 else self._get_kpi_value(dashboard_data.kpis, "receivables")
            )
            payables = payables_total if payables_total > 0 else self._get_kpi_value(dashboard_data.kpis, "payables")

            total_purchases = purchase_summary.get("total_amount", 0) if purchase_summary else 0

            set_label("total_sales", total_sales)
            set_label("total_purchases", total_purchases)
            set_label("gross_profit", gross_profit)
            set_label("profit_margin", profit_margin)
            set_label("receivables", receivables)
            set_label("payables", payables)
        except (KeyError, ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Reports summary update failed: {e}")

    def update_top_products_table(self, products: List[Dict[str, Any]]):
        if not hasattr(self, "top_products_table") or not products:
            return

        try:
            self.top_products_table.setRowCount(len(products))
            for row, product in enumerate(products):
                name = product.get("name") or product.get("product_name") or "-"
                qty = product.get("qty") or product.get("total_quantity") or product.get("total_quantityOdered") or 0
                total = product.get("total") or product.get("total_revenue") or 0

                self.top_products_table.setItem(row, 0, QTableWidgetItem(str(name)))
                qty_item = QTableWidgetItem(f"{float(qty):,.0f}")
                qty_item.setTextAlignment(Qt.AlignCenter)
                self.top_products_table.setItem(row, 1, qty_item)

                total_item = QTableWidgetItem(f"{float(total):,.2f}")
                total_item.setTextAlignment(Qt.AlignCenter)
                self.top_products_table.setItem(row, 2, total_item)
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Top products table update failed: {e}")

    def update_payment_distribution_table(self, distribution: List[Dict[str, Any]]):
        try:
            if not hasattr(self, "payment_distribution_table"):
                return
            self.payment_distribution_table.setRowCount(len(distribution))
            for row, entry in enumerate(distribution):
                label = entry.get("label", "")
                value = entry.get("value", 0)
                self.payment_distribution_table.setItem(row, 0, QTableWidgetItem(str(label)))
                value_item = QTableWidgetItem(f"{float(value):,.2f}")
                value_item.setTextAlignment(Qt.AlignCenter)
                self.payment_distribution_table.setItem(row, 1, value_item)
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Payment distribution table update failed: {e}")

    def update_revenue_vs_expense_table(self, revenue_data: Dict[str, List[Dict[str, Any]]]):
        try:
            if not hasattr(self, "revenue_vs_expense_table"):
                return
            revenue = revenue_data.get("revenue", [])
            expenses = revenue_data.get("expenses", [])
            combined = {}
            for row in revenue:
                day = str(row.get("day") or row.get("sale_date") or row.get("d"))
                combined.setdefault(day, {"revenue": 0.0, "expenses": 0.0})
                combined[day]["revenue"] = float(row.get("amount", row.get("total", 0)))

            for row in expenses:
                day = str(row.get("day") or row.get("purchase_date") or row.get("d"))
                combined.setdefault(day, {"revenue": 0.0, "expenses": 0.0})
                combined[day]["expenses"] = float(row.get("amount", row.get("total", 0)))

            sorted_days = sorted(combined.keys())
            self.revenue_vs_expense_table.setRowCount(len(sorted_days))
            for idx, day in enumerate(sorted_days):
                self.revenue_vs_expense_table.setItem(idx, 0, QTableWidgetItem(day))

                rev_item = QTableWidgetItem(f"{combined[day]['revenue']:,.2f}")
                rev_item.setTextAlignment(Qt.AlignCenter)
                self.revenue_vs_expense_table.setItem(idx, 1, rev_item)

                exp_item = QTableWidgetItem(f"{combined[day]['expenses']:,.2f}")
                exp_item.setTextAlignment(Qt.AlignCenter)
                self.revenue_vs_expense_table.setItem(idx, 2, exp_item)

            self.update_revenue_chart(combined)
        except (KeyError, ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Revenue vs expense table update failed: {e}")

    def update_revenue_chart(self, combined_points: Dict[str, Dict[str, float]]):
        """تحديث الرسم البياني للإيرادات مقابل المشتريات"""
        try:
            sorted_days = sorted(combined_points.keys())
            revenue_series = QLineSeries()
            revenue_series.setName("الإيرادات")
            expense_series = QLineSeries()
            expense_series.setName("المشتريات")

            axis_x = QCategoryAxis()
            axis_x.setLabelsAngle(-60)
            axis_x.setTitleText("التاريخ")

            max_value = 0.0
            for idx, day in enumerate(sorted_days):
                rev = combined_points[day]["revenue"]
                exp = combined_points[day]["expenses"]
                revenue_series.append(idx, rev)
                expense_series.append(idx, exp)
                axis_x.append(day, idx)
                max_value = max(max_value, rev, exp)

            self.revenue_chart.addSeries(revenue_series)
            self.revenue_chart.addSeries(expense_series)

            axis_y = QValueAxis()
            axis_y.setTitleText("القيمة (د.ج)")
            axis_y.setLabelFormat("%.0f")
            axis_y.setRange(0, max_value * 1.2 if max_value else 1)

            self.revenue_chart.setAxisX(axis_x, revenue_series)
            self.revenue_chart.setAxisY(axis_y, revenue_series)
            self.revenue_chart.setAxisX(axis_x, expense_series)
            self.revenue_chart.setAxisY(axis_y, expense_series)
            self.revenue_chart.setTitle("مقارنة الإيرادات بالمشتريات")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def export_reports_summary(self, format_type: ExportFormat):
        """تصدير تقرير الملخص المالي"""
        if not getattr(self, "reports_service", None):
            QMessageBox.warning(self, "تحذير", "خدمة التقارير غير متوفرة")
            return
        try:
            filepath = self.reports_service.export_summary(format_type)
            if filepath:
                QMessageBox.information(self, "تم التصدير", f"تم حفظ التقرير في:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير التقرير:\n{str(e)}")

    def print_reports_summary(self):
        """تصدير التقرير PDF وفتحه للطباعة"""
        if not getattr(self, "reports_service", None):
            QMessageBox.warning(self, "تحذير", "خدمة التقارير غير متوفرة")
            return
        try:
            filepath = self.reports_service.export_summary(ExportFormat.PDF)
            if filepath:
                QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
                QMessageBox.information(self, "جاهز للطباعة", "تم إنشاء ملف PDF وفتحه للطباعة.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في طباعة التقرير:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تجهيز التقرير للطباعة:\n{str(e)}")

    def _build_report_filter(self) -> ReportFilter:
        """بناء كائن فلاتر للتقارير من واجهة المستخدم"""
        start_date = (
            self._qdate_to_date(self.report_start_date.date()) if hasattr(self, "report_start_date") else date.today()
        )
        end_date = (
            self._qdate_to_date(self.report_end_date.date()) if hasattr(self, "report_end_date") else date.today()
        )
        return ReportFilter(
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time()),
        )

    def _get_kpi_value(self, kpis, key: str) -> float:
        for kpi in kpis:
            if getattr(kpi, "key", "") == key:
                return float(getattr(kpi, "value", 0))
        return 0.0

    def _qdate_to_date(self, qdate: QDate) -> date:
        """تحويل QDate إلى date"""
        return date(qdate.year(), qdate.month(), qdate.day())

    def _get_revenue_vs_expense_data(self, start_date: date, end_date: date) -> Dict[str, List[Dict[str, Any]]]:
        """جلب بيانات الإيرادات مقابل المشتريات"""
        revenue_data = {"revenue": [], "expenses": []}

        try:
            # جلب بيانات المبيعات اليومية
            if self.db_manager:
                sales_query = """
                    SELECT DATE(sale_date) as day, SUM(final_amount) as total
                    FROM sales
                    WHERE DATE(sale_date) BETWEEN ? AND ?
                    AND status != 'cancelled'
                    GROUP BY DATE(sale_date)
                    ORDER BY DATE(sale_date)
                """
                sales_rows = self.db_manager.execute_query(sales_query, [start_date, end_date])
                revenue_data["revenue"] = [
                    {
                        "day": str(row.get("day", "")),
                        "total": float(row.get("total", 0)),
                    }
                    for row in sales_rows
                ]

            # جلب بيانات المشتريات اليومية
            if self.db_manager:
                purchases_query = """
                    SELECT DATE(purchase_date) as day, SUM(total_amount) as total
                    FROM purchases
                    WHERE DATE(purchase_date) BETWEEN ? AND ?
                    AND status != 'cancelled'
                    GROUP BY DATE(purchase_date)
                    ORDER BY DATE(purchase_date)
                """
                purchases_rows = self.db_manager.execute_query(purchases_query, [start_date, end_date])
                revenue_data["expenses"] = [
                    {
                        "day": str(row.get("day", "")),
                        "total": float(row.get("total", 0)),
                    }
                    for row in purchases_rows
                ]
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في جلب بيانات الإيرادات مقابل المشتريات: {e}")

        return revenue_data

    def open_detailed_report(self):
        """فتح نافذة التقارير التفصيلية مع الفلاتر المحددة"""
        try:
            from src.services.report_exporter import ReportType

            # تحديد نوع التقرير بناءً على الاختيار
            report_type_map = {
                "ملخص المبيعات": ReportType.SALES_SUMMARY,
                "ملخص المشتريات": ReportType.FINANCIAL_SUMMARY,  # يمكن إضافة نوع خاص بالمشتريات لاحقاً
                "الملخص المالي": ReportType.FINANCIAL_SUMMARY,
                "تحليل المنتجات": ReportType.PRODUCT_PERFORMANCE,
                "تحليل العملاء": ReportType.CUSTOMER_ANALYSIS,
                "تحليل الموردين": ReportType.SUPPLIER_ANALYSIS,
            }

            selected_type = self.report_type_combo.currentText()
            report_type = report_type_map.get(selected_type, ReportType.SALES_SUMMARY)

            # فتح نافذة التقارير باستخدام Window Manager
            reports_window = self.window_manager.open_window("reports", parent=self)
            if not reports_window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة التقارير")
                return

            # تعيين الفلاتر والبدء في توليد التقرير
            try:
                start_date = (
                    self._qdate_to_date(self.report_start_date.date())
                    if hasattr(self, "report_start_date")
                    else date.today() - timedelta(days=30)
                )
                end_date = (
                    self._qdate_to_date(self.report_end_date.date())
                    if hasattr(self, "report_end_date")
                    else date.today()
                )

                # استخدام QTimer لتأخير توليد التقرير قليلاً لضمان تحميل الواجهة
                from datetime import datetime

                from src.services.report_exporter import ReportFilter

                filter_data = ReportFilter(
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    end_date=datetime.combine(end_date, datetime.max.time()),
                )

                # تعيين نوع التقرير والفلاتر
                if hasattr(reports_window, "set_report_type"):
                    reports_window.set_report_type(report_type)
                if hasattr(reports_window, "set_filters"):
                    reports_window.set_filters(filter_data)

                QTimer.singleShot(
                    300,
                    lambda: (reports_window.generate_report() if hasattr(reports_window, "generate_report") else None),
                )
            except Exception as e:
                if self.logger:
                    import traceback

                    self.logger.error(f"خطأ في إعداد التقارير: {e}")
                    self.logger.error(traceback.format_exc())
                QMessageBox.critical(self, "خطأ", f"فشل في إعداد التقارير:\n{str(e)}")
        except Exception as e:
            if self.logger:
                import traceback

                self.logger.error(f"خطأ في open_detailed_report: {e}")
                self.logger.error(traceback.format_exc())
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة التقارير:\n{str(e)}")

    def _format_currency(self, value) -> str:
        """تنسيق الأرقام كعملة موحدة"""
        try:
            if value is None:
                return "0.00"
            # If already a number
            if isinstance(value, (int, float)):
                amount = float(value)
            else:
                amount = float(str(value).replace(",", "").replace(" ", ""))
            return "{:,.2f}".format(amount)
        except Exception:
            return "0.00"

    def _get_value(self, obj, attr: str):
        """الحصول على خاصية سواء كان الكائن dataclass أو dict"""
        try:
            # يدعم dict و dataclass
            if hasattr(obj, attr):
                return getattr(obj, attr)
            elif isinstance(obj, dict):
                return obj.get(attr)
            return None
        except Exception:
            if isinstance(obj, dict):
                return obj.get(attr)
            return None

    def _safe_float(self, value, default=0.0):
        """تحويل قيمة إلى float بشكل آمن"""
        try:
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return float(value)
            # محاولة تحويل من string
            value_str = str(value).strip().replace(",", "").replace(" ", "")
            if not value_str:
                return default
            return float(value_str)
        except (ValueError, TypeError, AttributeError):
            return default

    def _register_worker(self, worker: QThread):
        """تسجيل خيط خلفي لتتبعه"""
        if not hasattr(self, "_background_threads"):
            self._background_threads = []
        if worker not in self._background_threads:
            self._background_threads.append(worker)
            worker.finished.connect(
                lambda w=worker: (self._background_threads.remove(w) if w in self._background_threads else None)
            )
        return worker

    def _start_worker(self, worker: QThread):
        """تشغيل خيط وتتبعه تلقائياً"""
        self._register_worker(worker)
        worker.start()
        return worker

    def _stop_background_threads(self):
        """
        🔥 إيقاف جميع الخيوط الخلفية والموقتات النشطة قبل الإغلاق
        يضمن إنهاء نظيفاً للتطبيق بدون تسريبات ذاكرة
        """
        # إيقاف مؤقت الاستقرار
        if hasattr(self, "stability_timer"):
            self.stability_timer.stop()

        if self.logger:
            self.logger.info("بدء تنظيف الموارد وإيقاف الخيوط الخلفية...")

        # جمع جميع الخيوط المعروفة (من _background_threads + المتغيرات المباشرة)
        all_threads = []

        # إضافة الخيوط المسجلة
        if hasattr(self, "_background_threads") and self._background_threads:
            all_threads.extend(self._background_threads)

        # إضافة الخيوط المعروفة الأخرى (جميع الخيوط المحتملة)
        thread_attributes = [
            "_inventory_loader",
            "_customers_loader",
            "_suppliers_loader",
            "_dashboard_loader",
            "_dashboard_analytics_loader",
            "_sales_loader",
            "_load_more_worker",
            "_backup_thread",
            "_restore_thread",
            "_backup_worker",
            "_restore_worker",
        ]

        for attr_name in dir(self):
            if not attr_name.startswith("_"):
                continue
            try:
                attr_value = getattr(self, attr_name, None)
                if isinstance(attr_value, QThread) and attr_value not in all_threads:
                    all_threads.append(attr_value)
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in main_window.py")

        for attr_name in thread_attributes:
            if hasattr(self, attr_name):
                thread = getattr(self, attr_name)
                if thread and isinstance(thread, QThread) and thread not in all_threads:
                    all_threads.append(thread)

        # إيقاف جميع الخيوط
        for thread in all_threads:
            try:
                if not thread:
                    continue
                if thread.isRunning():
                    if self.logger:
                        self.logger.debug(f"إيقاف خيط: {type(thread).__name__}")
                    if hasattr(thread, "stop"):
                        thread.stop()
                    elif hasattr(thread, "requestInterruption"):
                        thread.requestInterruption()
                    if not thread.wait(500):
                        if self.logger:
                            self.logger.warning(f"إنهاء قسري للخيط: {type(thread).__name__}")
                        thread.terminate()
                        thread.wait(1000)
                if not thread.isRunning():
                    thread.deleteLater()
                else:
                    QTimer.singleShot(
                        100,
                        lambda t=thread: (t.deleteLater() if t and not t.isRunning() else None),
                    )
            except Exception as e:
                if self.logger:
                    self.logger.error(f"خطأ في إيقاف خيط: {e}")

        if hasattr(self, "_background_threads"):
            self._background_threads.clear()

        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        # إيقاف جميع الموقتات
        timers_to_stop = [
            "_search_debounce_timer",
            "_update_throttle_timer",
            "_status_timer",
            "dashboard_refresh_timer",
            "perf_timer",
        ]
        for timer_name in timers_to_stop:
            if hasattr(self, timer_name):
                timer = getattr(self, timer_name)
                if timer and isinstance(timer, QTimer):
                    try:
                        timer.stop()
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in main_window.py")

        # إغلاق Window Manager
        if hasattr(self, "window_manager"):
            try:
                self.window_manager.close_all()
                self.window_manager.cleanup()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"خطأ في تنظيف Window Manager: {e}")

        # حفظ بيانات Telemetry
        if hasattr(self, "telemetry") and self.telemetry:
            try:
                self.telemetry.save_and_reset()
                if self.logger:
                    self.logger.info("✅ تم حفظ بيانات Telemetry")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️  فشل حفظ بيانات Telemetry: {e}")

        if self.logger:
            self.logger.info("✓ تم تنظيف الموارد")

    def _run_stability_check(self):
        """دورة فحص الاستقرار والإصلاح الذاتي (Stability & Self-Healing Cycle)"""
        if not hasattr(self, "system_doctor"):
            return

        # 1. التشخيص (Diagnosis)
        issues = self.system_doctor.diagnose()

        # 2. الإصلاح التلقائي (Auto-Healing) إذا وجدت مشاكل بيانات أو اتصال
        if issues:
            if self.logger:
                self.logger.warning(f"🩺 طبيب النظام اكتشف مشاكل: {issues}")

            reports = self.system_doctor.heal()
            if reports and self.logger:
                self.logger.info(f"💊 تقرير الإصلاح الذاتي: {reports}")
                self.notify.info(
                    "طبيب النظام",
                    "تم اكتشاف وإصلاح بعض المشاكل التقنية تلقائياً لضمان استقرار بياناتك.",
                )

        # 3. تحسين الموارد (Resource Optimization)
        if hasattr(self.system_doctor, "check_resource_usage"):
            stats = self.system_doctor.check_resource_usage()
            memory_mb = stats.get("memory_mb", 0)
        else:
            # Fallback if service is not updated
            memory_mb = 0

        # إذا تجاوز استهلاك الذاكرة 600 ميجابايت، قم بالتنظيف
        if memory_mb > 600:
            if hasattr(self.system_doctor, "optimize_memory"):
                success, report = self.system_doctor.optimize_memory()
                if success and self.logger:
                    self.logger.info(f"🚀 تم تحسين الذاكرة تلقائياً: {report}")

            # إرسال إشعار للمستخدم إذا كان الاستهلاك حرجاً
            if memory_mb > 800:
                self.notify.warning(
                    "تحسين الأداء",
                    "تم اكتشاف ضغط عالٍ على الذاكرة، قام النظام بتنظيف نفسه لزيادة السرعة.",
                )

        if self.logger:
            self.logger.debug("✓ تمت دورة فحص الاستقرار بنجاح")

    def _register_all_windows(self):
        """تسجيل جميع النوافذ في Window Manager باستخدام Auto-Registration System"""
        try:
            # استخدام Auto-Registration System
            from src.core.window_registry import (
                WindowRegistry,
                create_init_kwargs_provider,
            )

            # إنشاء Window Registry
            registry = WindowRegistry()

            # إنشاء provider لـ init_kwargs
            cycle_count_service = None
            if hasattr(self, "_get_cycle_count_service"):
                try:
                    cycle_count_service = self._get_cycle_count_service()
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")

            init_kwargs_provider = create_init_kwargs_provider(
                db_manager=self.db_manager,
                payment_service=self.payment_service,
                cycle_count_service=cycle_count_service,
            )

            # تسجيل جميع النوافذ تلقائياً
            registration_results = registry.register_all(
                window_manager=self.window_manager,
                init_kwargs_provider=init_kwargs_provider,
            )

            # عرض النتائج
            successful = sum(1 for success in registration_results.values() if success)
            total = len(registration_results)

            if self.logger:
                self.logger.info(f"✅ تم تسجيل {successful}/{total} نافذة تلقائياً")
                if successful < total:
                    failed = [key for key, success in registration_results.items() if not success]
                    self.logger.warning(f"⚠️ فشل تسجيل النوافذ التالية: {', '.join(failed)}")

            # تسجيل النوافذ الخاصة التي تحتاج معاملات خاصة (إن وجدت)
            # مثال: PaymentDashboard إذا لم تكن مسجلة تلقائياً
            if "payment_dashboard" not in registration_results and self.payment_service:
                try:
                    from src.ui.windows.payment_dashboard import PaymentDashboard

                    self.window_manager.register_window(
                        window_key="payment_dashboard",
                        window_class=PaymentDashboard,
                        title="لوحة تحكم المدفوعات",
                        singleton=True,
                        init_kwargs={
                            "db_manager": self.db_manager,
                            "payment_service": self.payment_service,
                        },
                    )
                    if self.logger:
                        self.logger.info("✅ تم تسجيل PaymentDashboard يدوياً")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ فشل تسجيل PaymentDashboard: {e}")

            if self.logger:
                self.logger.info("✅ تم تسجيل جميع النوافذ في Window Manager")

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ فشل تسجيل النوافذ: {e}", exc_info=True)

    def _register_external_window(self, window: QWidget):
        """تتبع أي نافذة مستقلة لإغلاقها عند إنهاء التطبيق"""
        if window in self._managed_windows:
            return
        self._managed_windows.append(window)
        try:
            pass  # (If you need to track window-specific logic, add here)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def _log_section_duration(self, label: str, start_time: float, threshold_ms: float = 100.0):
        """تسجيل مدة تنفيذ قسم معين"""
        try:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            if self.logger:
                if elapsed_ms >= threshold_ms:
                    self.logger.warning(f"{label} استغرق {elapsed_ms:.2f}ms")
                else:
                    self.logger.debug(f"{label} استغرق {elapsed_ms:.2f}ms")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    # ===== إدارة المخزون =====
    def load_inventory_filters(self):
        """تحميل قائمة الفئات في مرشحات المخزون"""
        if not hasattr(self, "inventory_category_combo"):
            return

        try:
            # منع إشارات التغيير أثناء التحميل
            self.inventory_category_combo.blockSignals(True)

            # مسح القائمة الحالية
            self.inventory_category_combo.clear()
            self.inventory_category_combo.addItem("جميع الفئات", None)

            # تحميل الفئات من قاعدة البيانات
            if self.db_manager:
                try:
                    from src.models.category import CategoryManager

                    category_manager = CategoryManager(self.db_manager)
                    categories = category_manager.get_all_categories()

                    for category in categories:
                        self.inventory_category_combo.addItem(category.name, category.id)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل تحميل الفئات من CategoryManager: {e}")
                    # Fallback: تحميل مباشر من قاعدة البيانات
                    try:
                        conn = self.db_manager.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name")
                        for row in cursor.fetchall():
                            self.inventory_category_combo.addItem(row[1], row[0])
                    except Exception as e2:
                        if self.logger:
                            self.logger.error(f"فشل تحميل الفئات من قاعدة البيانات: {e2}")
            elif getattr(self, "inventory_service", None):
                # Fallback: استخدام inventory_service
                pass

            self.inventory_category_combo.blockSignals(False)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل فلاتر المخزون: {e}")

    def load_warehouses_for_inventory_filter(self):
        """تحميل قائمة المستودعات في فلتر المخزون"""
        if not hasattr(self, "inventory_warehouse_combo"):
            return

        try:
            self.inventory_warehouse_combo.blockSignals(True)

            self.inventory_warehouse_combo.clear()
            self.inventory_warehouse_combo.addItem("الكل", None)

            # تحميل المستودعات
            try:
                from src.services.warehouse_service import WarehouseService

                warehouse_service = WarehouseService(self.db_manager)
                warehouses = warehouse_service.get_all_warehouses(include_inactive=False)

                for warehouse in warehouses:
                    display_text = f"{warehouse.name} ({warehouse.code})"
                    self.inventory_warehouse_combo.addItem(display_text, warehouse.id)

            except Exception as e:
                if self.logger:
                    self.logger.warning(f"فشل تحميل المستودعات: {e}")

            self.inventory_warehouse_combo.blockSignals(False)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل المستودعات للفلتر: {e}")

    def _on_inventory_search_changed(self, text: str):
        """معالجة تغيير نص البحث مع Debouncing"""
        # إلغاء المؤقت السابق
        self._search_debounce_timer.stop()

        # حفظ النص الحالي
        self._last_search_term = text.strip()

        # بدء مؤقت جديد (500ms) - البحث بعد توقف المستخدم عن الكتابة
        self._search_debounce_timer.setInterval(500)
        self._search_debounce_timer.start()

    def _on_search_debounced(self):
        """تنفيذ البحث بعد انتهاء Debounce"""
        if self._last_search_term != getattr(self, "_last_executed_search", ""):
            self._last_executed_search = self._last_search_term
            self.on_inventory_filters_changed()

    def on_inventory_filters_changed(self):
        """التعامل مع تغيير مرشحات المخزون"""
        # إيقاف debounce timer إذا كان يعمل
        if hasattr(self, "_search_debounce_timer"):
            self._search_debounce_timer.stop()

        # Throttling - منع التحديثات المتكررة
        if self._is_updating:
            return

        self.refresh_inventory_data()

    def refresh_inventory_data(self):
        """تحديث بيانات جدول المخزون (محسّنة - في الخلفية)"""
        if not hasattr(self, "inventory_table"):
            return

        # التحقق من وجود inventory_model
        if not hasattr(self, "inventory_model") or self.inventory_model is None:
            if self.logger:
                self.logger.warning("inventory_model غير موجود - تخطي refresh_inventory_data")
            return

        if not getattr(self, "inventory_service", None):
            # عرض جدول فارغ بدلاً من crash
            if PANDAS_AVAILABLE:
                empty_df = pd.DataFrame(
                    columns=[
                        "id",
                        "barcode",
                        "name",
                        "category",
                        "unit",
                        "current_stock",
                        "min_stock",
                        "selling_price",
                        "status",
                    ]
                )
                self.inventory_model.setData(empty_df)
            return

        # Throttling - منع التحديثات المتكررة
        if self._is_updating:
            return

        self._is_updating = True

        # 🔥 إعادة تعيين offset عند التحديث الكامل (refresh)
        self._inventory_offset = 0

        # تعطيل الأزرار أثناء التحديث
        if hasattr(self, "inventory_refresh_btn"):
            self.inventory_refresh_btn.setEnabled(False)
            self.inventory_refresh_btn.setText("⏳ جاري التحديث...")

        # إعادة تعيين عداد التحميل
        self._inventory_offset = 0
        self._inventory_has_more = True

        # Phase 2: عرض مؤشر التحميل باستخدام Model
        if PANDAS_AVAILABLE:
            # إنشاء DataFrame فارغ مع رسالة تحميل
            loading_df = pd.DataFrame(
                [["⏳ جاري تحميل البيانات...", "", "", "", "", "", "", "", ""]],
                columns=[
                    "id",
                    "barcode",
                    "name",
                    "category",
                    "unit",
                    "current_stock",
                    "min_stock",
                    "selling_price",
                    "status",
                ],
            )
            self.inventory_model.setData(loading_df)
        else:
            # Fallback: إذا لم يكن Pandas متاحاً
            if hasattr(self, "inventory_model"):
                self.inventory_model.setData(pd.DataFrame() if PANDAS_AVAILABLE else None)

        # تحميل البيانات في الخلفية باستخدام InventoryDataLoaderThread المحسّن
        search_term = self.inventory_search_input.text().strip() if hasattr(self, "inventory_search_input") else ""
        category_id = self.inventory_category_combo.currentData() if hasattr(self, "inventory_category_combo") else None

        # الحصول على مسار قاعدة البيانات
        db_path = None
        if self.db_manager and hasattr(self.db_manager, "db_path"):
            db_path = self.db_manager.db_path
        elif self.config_manager:
            db_path = self.config_manager.get_database_path()
        else:
            # Fallback: مسار افتراضي
            from pathlib import Path

            db_path = str(Path("data/standard_eljoumla.db").absolute())

        if not db_path:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على مسار قاعدة البيانات")
            self._is_updating = False
            return

        # إظهار رسالة التحميل في شريط الحالة
        self.statusBar().showMessage("⏳ جاري تحميل المنتجات من قاعدة البيانات... يرجى الانتظار")

        # الحصول على warehouse_id من الفلتر (Multi-Warehouse)
        warehouse_id = None
        if hasattr(self, "inventory_warehouse_combo"):
            warehouse_id = self.inventory_warehouse_combo.currentData()

        # Worker محسّن للتحميل المباشر من SQLite
        self._inventory_load_started = time.perf_counter()
        # 🔥 تقليل LIMIT إلى 100 فقط للحد الأدنى من تجميد الواجهة
        inventory_page_size = 100
        self._inventory_loader = InventoryDataLoaderThread(
            db_manager=self.db_manager,
            search_term=search_term,
            category_id=category_id,
            warehouse_id=warehouse_id,  # Multi-Warehouse Support
            limit=inventory_page_size,  # تحميل 100 منتج في المرة
            offset=self._inventory_offset,
        )

        # ربط الإشارات
        self._inventory_loader.data_loaded.connect(self._on_inventory_data_loaded)
        self._inventory_loader.progress_updated.connect(lambda msg: self.statusBar().showMessage(msg))
        self._inventory_loader.error_occurred.connect(
            lambda err: (
                QMessageBox.critical(self, "خطأ", f"فشل تحميل البيانات:\n{err}"),
                setattr(self, "_is_updating", False),
            )
        )
        self._inventory_loader.finished.connect(
            lambda: self.statusBar().showMessage("✅ تم تحميل البيانات بنجاح", 3000)
        )

        # بدء التحميل في الخلفية
        self._start_worker(self._inventory_loader)

    def _on_inventory_data_loaded(self, df):
        """معالجة البيانات المحملة من الخلفية"""
        try:
            if df is None or (PANDAS_AVAILABLE and df.empty):
                # جدول فارغ
                if PANDAS_AVAILABLE:
                    empty_df = pd.DataFrame(
                        columns=[
                            "id",
                            "barcode",
                            "name",
                            "category",
                            "unit",
                            "current_stock",
                            "min_stock",
                            "selling_price",
                            "status",
                            "actions",
                        ]
                    )
                    self.inventory_model.setData(empty_df)
                self.statusBar().showMessage("لا توجد منتجات للعرض", 3000)
                # 🔥 تحديث حالة الزر عند عدم وجود منتجات
                self._inventory_has_more = False
                self._inventory_offset = 0
                self._update_load_more_button_state()
                self._is_updating = False
                return

            # تحديث Model بالبيانات الجديدة (هذا سريع جداً - <50ms)
            if PANDAS_AVAILABLE:
                self.inventory_model.setData(df)

                # ⚠️ CRITICAL FIX: لا تستخدم resizeColumnsToContents() - يسبب تجميد مع 50K صف!
                # بدلاً من ذلك، استخدم Interactive mode مع عرض افتراضي
                header = self.inventory_table.horizontalHeader()

                # جعل الأعمدة تفاعلية (يمكن للمستخدم تغيير الحجم) بدلاً من Stretch
                # هذا أسرع بكثير من resizeColumnsToContents()
                header.setSectionResizeMode(QHeaderView.Interactive)

                # تعيين عرض افتراضي سريع (بدون حسابات على 50K صف)
                header.setDefaultSectionSize(120)

                # جعل بعض الأعمدة ثابتة العرض (ID, Actions)
                if df is not None and not df.empty:
                    # العمود الأول (ID) - عرض ثابت صغير
                    header.resizeSection(0, 80)
                    # العمود الأخير (Actions) - عرض ثابت
                    if len(df.columns) > 0:
                        header.resizeSection(len(df.columns) - 1, 120)

                # ---------------------------------------------------------
                # 🛠️ الإصلاح: حساب الإحصائيات مباشرة من DataFrame (سريع وفوري)
                # ---------------------------------------------------------
                if not df.empty and hasattr(self, "inventory_summary_labels"):
                    try:
                        # حساب الأرقام باستخدام Pandas (سريع جداً)
                        total_products = len(df)

                        # حساب قيمة المخزون (price * quantity)
                        # البحث عن أعمدة السعر والكمية (قد تكون بأسماء مختلفة)
                        price_col = None
                        quantity_col = None

                        for col in df.columns:
                            col_lower = str(col).lower()
                            if "price" in col_lower or "selling_price" in col_lower:
                                price_col = col
                            if "quantity" in col_lower or "stock" in col_lower or "current_stock" in col_lower:
                                quantity_col = col

                        total_stock_value = 0.0
                        if quantity_col:
                            try:
                                # Use cost_price for valuation if available, otherwise fallback to selling_price
                                val_col = None
                                for col in df.columns:
                                    if "cost_price" in str(col).lower():
                                        val_col = col
                                        break

                                if not val_col:
                                    val_col = price_col

                                if val_col:
                                    prices = pd.to_numeric(df[val_col], errors="coerce").fillna(0)
                                    quantities = pd.to_numeric(df[quantity_col], errors="coerce").fillna(0)
                                    total_stock_value = (prices * quantities).sum()
                            except Exception:
                                logging.getLogger(__name__).warning("Ignored exception in main_window.py")

                        # حساب المخزون المنخفض والنافد
                        if quantity_col:
                            try:
                                quantities = pd.to_numeric(df[quantity_col], errors="coerce").fillna(0)
                                low_stock_count = len(df[quantities < 10])
                                out_of_stock_count = len(df[quantities <= 0])
                            except Exception:
                                low_stock_count = 0
                                out_of_stock_count = 0
                        else:
                            low_stock_count = 0
                            out_of_stock_count = 0

                        # حساب عدد الفئات
                        category_col = None
                        for col in df.columns:
                            if "category" in str(col).lower():
                                category_col = col
                                break
                        total_categories = df[category_col].nunique() if category_col else 0

                        # تحديث الـ Labels مباشرة
                        def set_label(key, value):
                            if hasattr(self, "inventory_summary_labels") and key in self.inventory_summary_labels:
                                self.inventory_summary_labels[key].setText(str(value))

                        set_label("total_products", f"{total_products:,}")
                        set_label("total_categories", f"{total_categories:,}")
                        set_label("total_stock_value", f"{total_stock_value:,.2f} دج")
                        set_label("low_stock_items", f"{low_stock_count:,}")
                        set_label("out_of_stock_items", f"{out_of_stock_count:,}")

                        if self.logger:
                            self.logger.debug(
                                f"✅ تم تحديث إحصائيات المخزون مباشرة من DataFrame: {total_products} منتج"
                            )
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"فشل حساب إحصائيات المخزون من DataFrame: {e}")

                # تحديث ملخص المخزون (في الخلفية أيضاً) - كـ backup
                QTimer.singleShot(100, lambda: self._load_inventory_summary_async())

                # قياس الأداء
                if self._inventory_load_started:
                    elapsed_ms = (time.perf_counter() - self._inventory_load_started) * 1000
                    if self.logger:
                        self.logger.info(f"تم تحميل {len(df):,} منتج في {elapsed_ms:.2f}ms")
                    self.statusBar().showMessage(f"✅ تم تحميل {len(df):,} منتج بنجاح ({elapsed_ms:.0f}ms)", 5000)

                # 🔥 CRITICAL FIX: تحديث حالة التحميل وزر "تحميل المزيد"
                # هذه الدالة (_on_inventory_data_loaded) تستدعى فقط من refresh_inventory_data
                # لذلك نحن في التحميل الأولي - offset = 0
                self._inventory_offset = len(df)  # عدد المنتجات المحملة في التحميل الأولي

                # إذا كانت النتائج = 500، فهناك المزيد من المنتجات
                self._inventory_has_more = len(df) == 500

                # 🔥 تحديث حالة زر "تحميل المزيد" بشكل موحد وموثوق
                self._update_load_more_button_state()

                if self.logger:
                    self.logger.debug(
                        f"✅ التحميل الأولي: {len(df)} منتج، offset={self._inventory_offset}, has_more={self._inventory_has_more}"  # noqa: E501
                    )

            else:
                QMessageBox.warning(self, "تحذير", "Pandas غير متاح. يرجى تثبيته: pip install pandas")
                # تحديث حالة الزر عند عدم توفر Pandas
                self._inventory_has_more = False
                self._update_load_more_button_state()

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في معالجة البيانات المحملة: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في معالجة البيانات:\n{str(e)}")
            # تحديث حالة الزر عند حدوث خطأ
            self._inventory_has_more = False
            self._update_load_more_button_state()
        finally:
            # إعادة تفعيل الأزرار
            self._is_updating = False
            if hasattr(self, "inventory_refresh_btn"):
                self.inventory_refresh_btn.setEnabled(True)
                self.inventory_refresh_btn.setText("🔄 تحديث")
            # 🔥 التأكد من تحديث حالة زر "تحميل المزيد" في النهاية
            self._update_load_more_button_state()

            # ✅ إعادة تشغيل مراقب الجلسة بعد أن هدأ الوضع
            if hasattr(self, "session_monitor_timer") and self.session_monitor_timer:
                if not self.session_monitor_timer.isActive():
                    if self.logger:
                        self.logger.debug("▶️ إعادة تشغيل session_monitor_timer بعد انتهاء تحميل المخزون")
                    self.session_monitor_timer.start(60000)  # كل 60 ثانية

    def _load_inventory_summary_async(self):
        """تحميل ملخص المخزون في الخلفية"""
        try:
            if not getattr(self, "inventory_service", None):
                return

            # تحميل التقرير في Worker منفصل
            def load_report():
                search_term = (
                    self.inventory_search_input.text().strip() if hasattr(self, "inventory_search_input") else ""
                )
                category_id = (
                    self.inventory_category_combo.currentData() if hasattr(self, "inventory_category_combo") else None
                )
                report_filters = {
                    "search": search_term or "",
                    "category_id": category_id,
                }

                if getattr(self, "cache", None):
                    cached_report = self.cache.get_cached_report("inventory_summary", report_filters)
                    if cached_report is not None:
                        return cached_report

                report = self.inventory_service.generate_inventory_report()
                if getattr(self, "cache", None):
                    self.cache.cache_report("inventory_summary", report_filters, report, ttl=60)
                return report

            report_worker = DataLoaderWorker(load_report)
            report_worker.data_loaded.connect(
                lambda report: (self.update_inventory_summary(report) if report else None)
            )
            self._start_worker(report_worker)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل ملخص المخزون: {e}")

    def load_more_inventory(self):
        """تحميل المزيد من المنتجات"""
        if not hasattr(self, "inventory_table") or not getattr(self, "inventory_service", None):
            return

        if not getattr(self, "_inventory_has_more", True):
            return

        # تعطيل الزر أثناء التحميل
        if hasattr(self, "inventory_load_more_btn"):
            self.inventory_load_more_btn.setEnabled(False)
            self.inventory_load_more_btn.setText("⏳ جاري التحميل...")

        # 🔥 CRITICAL FIX: تحميل البيانات في الخلفية مع offset صحيح
        # الحصول على offset الحالي (عدد المنتجات المحملة حالياً)
        current_offset = getattr(self, "_inventory_offset", 0)

        # التحقق من وجود offset صحيح
        if current_offset == 0:
            # إذا كان offset = 0، فهذا يعني أننا في التحميل الأولي
            # يجب أن نبدأ من 500 (لأن التحميل الأولي كان 500)
            current_offset = 500

        search_term = self.inventory_search_input.text().strip() if hasattr(self, "inventory_search_input") else ""
        category_id = self.inventory_category_combo.currentData() if hasattr(self, "inventory_category_combo") else None

        # 🔥 CRITICAL: استخدام offset الحالي (وليس offset + limit)
        # لأن offset في SQL يعني "تخطي X صفوف"
        limit = 500
        offset = current_offset  # تخطي المنتجات المحملة بالفعل

        if self.logger:
            self.logger.debug(f"🔥 تحميل المزيد: offset={offset}, limit={limit}")

        # 🔥 استخدام InventoryDataLoaderThread المحسّن للتحميل التدريجي
        db_path = (  # noqa: F841
            self.db_manager.db_path if hasattr(self.db_manager, "db_path") else "data/standard_eljoumla.db"
        )  # noqa: F841

        self._load_more_worker = InventoryDataLoaderThread(
            db_manager=self.db_manager,
            search_term=search_term,
            category_id=category_id,
            limit=limit,
            offset=offset,  # 🔥 تمرير offset الصحيح
        )
        self._load_more_worker.data_loaded.connect(self._append_inventory_products)
        self._load_more_worker.error_occurred.connect(
            lambda err: (
                QMessageBox.critical(self, "خطأ", f"فشل تحميل المزيد: {err}"),
                self._update_load_more_button_state(),  # تحديث حالة الزر عند الخطأ
            )
        )
        self._start_worker(self._load_more_worker)

    def _populate_inventory_table(self, data):
        """
        Phase 2: ملء جدول المخزون باستخدام Model عالي الأداء
        التحول من QTableWidget loops إلى QTableView + Pandas DataFrame
        """
        try:
            products = data.get("products", [])
            report = data.get("report")
            movements = data.get("movements", [])
            has_more = data.get("has_more", False)
            offset = data.get("offset", 0)
            df = data.get("dataframe")  # Pandas DataFrame

            # تحديث حالة التحميل
            self._inventory_offset = offset
            self._inventory_has_more = has_more
            if df is not None:
                # افترض أن هناك المزيد إذا كانت النتائج تساوي الحد الأقصى
                self._inventory_has_more = len(df) == 500
                self._inventory_offset = 0  # إعادة التعيين عند التحديث الكامل

            # 🔥 تحديث حالة زر "تحميل المزيد" بشكل موحد وموثوق
            self._update_load_more_button_state()

            # Phase 2: استخدام Model بدلاً من loops
            if PANDAS_AVAILABLE and df is not None and not df.empty:
                # الطريقة الجديدة: تحديث Model مباشرة - أسرع بـ 10-20x
                self.inventory_model.setData(df)

                # قياس الأداء
                if self.logger:
                    self.logger.debug(f"تم تحديث جدول المخزون: {len(df)} منتج في <50ms")
            else:
                # Fallback: إذا لم يكن Pandas متاحاً، استخدم الطريقة القديمة
                if self.logger:
                    self.logger.warning("Pandas غير متاح - استخدام الطريقة التقليدية")

                # إنشاء DataFrame يدوياً من products
                if PANDAS_AVAILABLE and products:
                    df_data = []
                    for product in products:
                        product_id = self._get_value(product, "id") or 0
                        barcode = self._get_value(product, "barcode") or "-"
                        name = self._get_value(product, "name") or "-"
                        category_name = self._get_value(product, "category_name") or "-"
                        unit = self._get_value(product, "unit") or "-"
                        current_stock = self._get_value(product, "current_stock") or 0
                        min_stock = (
                            self._get_value(product, "min_stock") or self._get_value(product, "min_stock_level") or 0
                        )
                        selling_price = self._safe_float(self._get_value(product, "selling_price"), 0.0)

                        # تحديد حالة المخزون
                        current_stock_value = self._safe_float(current_stock, 0)
                        min_stock_value = self._safe_float(min_stock, 0)

                        if current_stock_value == 0:
                            status_text = "نفد من المخزون"
                        elif current_stock_value <= min_stock_value:
                            status_text = "مخزون منخفض"
                        else:
                            status_text = "جيد"

                        df_data.append(
                            [
                                product_id,
                                barcode,
                                name,
                                category_name,
                                unit,
                                current_stock,
                                min_stock,
                                selling_price,
                                status_text,
                                "",  # عمود إجراءات فارغ
                            ]
                        )

                    df = pd.DataFrame(
                        df_data,
                        columns=[
                            "id",
                            "barcode",
                            "name",
                            "category",
                            "unit",
                            "current_stock",
                            "min_stock",
                            "selling_price",
                            "status",
                            "actions",
                        ],
                    )
                    self.inventory_model.setData(df)
                else:
                    # Fallback نهائي: جدول فارغ
                    if PANDAS_AVAILABLE:
                        self.inventory_model.setData(pd.DataFrame())
                    else:
                        QMessageBox.warning(
                            self,
                            "تحذير",
                            "Pandas غير متاح. يرجى تثبيته: pip install pandas",
                        )

            # تحديث ملخص المخزون إذا كان متوفراً
            if report:
                self.update_inventory_summary(report)

            # تحديث تنبيهات المخزون
            if movements:
                self.update_inventory_alerts_table(movements)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في ملء جدول المخزون: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في ملء جدول المخزون:\n{str(e)}")
        finally:
            # إعادة تفعيل الأزرار
            self._is_updating = False
            if hasattr(self, "inventory_refresh_btn"):
                self.inventory_refresh_btn.setEnabled(True)
                self.inventory_refresh_btn.setText("🔄 تحديث")

            start_value = getattr(self, "_inventory_load_started", None)
            if start_value:
                self._log_section_duration("refresh_inventory_data", start_value, threshold_ms=400.0)
                self._inventory_load_started = None

    def _append_inventory_products(self, df):
        """
        🔥 CRITICAL FIX: إضافة منتجات جديدة إلى الجدول (للتحميل التدريجي)
        هذه الدالة تستدعى من load_more_inventory عند تحميل المزيد
        """
        # تحسين الأداء - تعطيل التحديثات أثناء التعبئة
        self.inventory_table.setUpdatesEnabled(False)
        try:
            if df is None or (PANDAS_AVAILABLE and df.empty):
                # لا توجد بيانات جديدة
                self._inventory_has_more = False
                if self.logger:
                    self.logger.debug("لا توجد منتجات إضافية للتحميل")
            else:
                # 🔥 CRITICAL: استخدام appendData لإضافة البيانات (بدلاً من استبدالها)
                if hasattr(self.inventory_model, "appendData"):
                    self.inventory_model.appendData(df)
                else:
                    # Fallback: إذا لم تكن الدالة موجودة، استخدم concat يدوياً
                    if PANDAS_AVAILABLE:
                        if self.inventory_model._data.empty:
                            self.inventory_model.setData(df)
                        else:
                            # دمج البيانات يدوياً
                            combined_df = pd.concat([self.inventory_model._data, df], ignore_index=True)
                            self.inventory_model.setData(combined_df)

                # تحديث offset و has_more
                self._inventory_offset += len(df)
                self._inventory_has_more = len(df) == 500  # إذا كانت النتائج = 500، فهناك المزيد

                if self.logger:
                    self.logger.debug(f"تم إضافة {len(df)} منتج جديد. الإجمالي الآن: {self._inventory_offset}")

            # 🔥 تحديث حالة زر "تحميل المزيد" بشكل موحد وموثوق
            self._update_load_more_button_state()

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة المنتجات: {e}", exc_info=True)
            QMessageBox.warning(self, "تحذير", f"فشل تحميل المزيد من المنتجات:\n{str(e)}")
            # تحديث حالة الزر عند حدوث خطأ
            self._inventory_has_more = False
            self._update_load_more_button_state()
        finally:
            # Quick Win: Re-enable updates after batch operations
            self.inventory_table.setUpdatesEnabled(True)

            # 🔥 تحديث حالة زر "تحميل المزيد" بشكل موحد وموثوق
            self._update_load_more_button_state()

    def update_inventory_summary(self, report):
        """تحديث ملخص المخزون"""
        if not hasattr(self, "inventory_summary_labels"):
            return

        try:

            def set_label(key, value):
                if key in self.inventory_summary_labels:
                    self.inventory_summary_labels[key].setText(value)

            set_label("total_products", f"{getattr(report, 'total_products', 0):,}")
            set_label("total_categories", f"{getattr(report, 'total_categories', 0):,}")
            set_label(
                "total_stock_value",
                f"{getattr(report, 'total_stock_value', 0):,.2f} دج",
            )
            set_label("low_stock_items", f"{getattr(report, 'low_stock_items', 0):,}")
            set_label("out_of_stock_items", f"{getattr(report, 'out_of_stock_items', 0):,}")
            set_label("expired_items", f"{getattr(report, 'expired_items', 0):,}")

        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def open_adjust_stock_dialog(self):
        """فتح حوار تعديل المخزون"""
        if not getattr(self, "inventory_service", None):
            QMessageBox.warning(self, "تحذير", "خدمة المخزون غير متوفرة")
            return
        dialog = AdjustStockDialog(self.inventory_service, parent=self)
        dialog.stock_adjusted.connect(self._on_inventory_operation_completed)
        dialog.exec()

    def open_transfer_stock_dialog(self):
        """فتح حوار نقل المخزون"""
        if not getattr(self, "inventory_service", None):
            QMessageBox.warning(self, "تحذير", "خدمة المخزون غير متوفرة")
            return
        dialog = TransferStockDialog(self.inventory_service, parent=self)
        dialog.transfer_completed.connect(self._on_inventory_operation_completed)
        dialog.exec()

    def _update_load_more_button_state(self):
        """
        🔥 دالة موحدة لتحديث حالة زر "تحميل المزيد"
        تضمن الاتساق في جميع السيناريوهات (نجاح/فشل/لا نتائج)
        """
        if not hasattr(self, "inventory_load_more_btn"):
            return

        has_more = getattr(self, "_inventory_has_more", False)
        self.inventory_load_more_btn.setEnabled(has_more)

        if has_more:
            self.inventory_load_more_btn.setText("📥 تحميل المزيد")
        else:
            self.inventory_load_more_btn.setText("✅ تم تحميل كل المنتجات")

    def _on_inventory_operation_completed(self):
        """تحديث بيانات المخزون بعد أي عملية"""
        self.refresh_inventory_data()

    def update_inventory_alerts_table(self, alerts):
        """عرض تنبيهات المخزون"""
        if not hasattr(self, "inventory_alerts_table"):
            return
        table = self.inventory_alerts_table
        alerts = alerts or []
        if not alerts:
            table.setRowCount(1)
            info_item = QTableWidgetItem("لا توجد تنبيهات حالياً")
            info_item.setTextAlignment(Qt.AlignCenter)
            table.setSpan(0, 0, 1, table.columnCount())
            table.setItem(0, 0, info_item)
            return
        table.setRowCount(len(alerts))
        severity_colors = {
            "low": "#2ecc71",
            "medium": "#f1c40f",
            "high": "#e67e22",
            "critical": "#e74c3c",
        }
        for row, alert in enumerate(alerts):
            if isinstance(alert, dict):
                product_name = alert.get("product_name", "-")
                alert_type = alert.get("alert_type", "")
                current_stock = alert.get("current_stock", "-")
                message = alert.get("message", "-")
                severity = alert.get("severity", "")
            else:
                product_name = getattr(alert, "product_name", "-")
                alert_type = getattr(alert, "alert_type", "")
                current_stock = getattr(alert, "current_stock", "-")
                message = getattr(alert, "message", "-")
                severity = getattr(alert, "severity", "")
            status_text = {
                "low_stock": "مخزون منخفض",
                "out_of_stock": "نفاد المخزون",
                "expired": "منتهي الصلاحية",
            }.get(alert_type, alert_type or "-")
            color = severity_colors.get(severity, "#94a3b8")

            items = [
                QTableWidgetItem(str(product_name)),
                QTableWidgetItem(status_text),
                QTableWidgetItem(str(current_stock)),
                QTableWidgetItem(str(message)),
            ]
            for idx, item in enumerate(items):
                if idx == 2:
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter)
                item.setForeground(QColor(color))
                table.setItem(row, idx, item)

    def update_stock_movements_table(self, movements):
        """عرض آخر حركات المخزون"""
        if not hasattr(self, "stock_movements_table"):
            return
        table = self.stock_movements_table
        movements = movements or []
        if not movements:
            table.setRowCount(1)
            info_item = QTableWidgetItem("لا توجد حركات حديثة")
            info_item.setTextAlignment(Qt.AlignCenter)
            table.setSpan(0, 0, 1, table.columnCount())
            table.setItem(0, 0, info_item)
            return
        table.setRowCount(len(movements))
        for row, movement in enumerate(movements):
            if hasattr(movement, "__dict__"):
                movement_date = getattr(movement, "created_at", None)
                if movement_date:
                    date_text = movement_date.strftime("%Y-%m-%d %H:%M")
                else:
                    date_text = "-"
                product_id = getattr(movement, "product_id", "-")
                product_name = getattr(movement, "product_name", None) if hasattr(movement, "product_name") else "-"
                movement_type = getattr(movement, "movement_type", "-")
                quantity = getattr(movement, "quantity", 0)
                notes = getattr(movement, "notes", "") or "-"
            else:
                data = movement
                date_text = data.get("created_at", "-")
                product_name = data.get("product_name", "-")
                product_id = data.get("product_id", "-")
                movement_type = data.get("movement_type", "-")
                quantity = data.get("quantity", 0)
                notes = data.get("notes", "-")
            type_display = {
                "in": "إدخال",
                "out": "إخراج",
                "adjustment": "تعديل",
                "transfer": "نقل",
            }.get(str(movement_type), str(movement_type))
            quantity_value = self._safe_float(quantity)
            row_items = [
                QTableWidgetItem(date_text),
                QTableWidgetItem(f"{product_name or product_id}"),
                QTableWidgetItem(type_display),
                QTableWidgetItem(f"{quantity_value:,.2f}"),
                QTableWidgetItem(notes),
            ]
            for idx, item in enumerate(row_items):
                if idx == 3:
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter)
                table.setItem(row, idx, item)

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
        """تحديث جدول العملاء (محسّنة - في الخلفية)"""
        if not hasattr(self, "customers_table"):
            return

        if not getattr(self, "customer_manager", None):
            self.customers_table.setRowCount(0)
            self.customers_summary_label.setText("تعذر تحميل بيانات العملاء (قاعدة البيانات غير متصلة).")
            return

        # عرض مؤشر التحميل
        self.customers_table.setRowCount(1)
        loading_item = QTableWidgetItem("⏳ جاري تحميل العملاع...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.customers_table.setItem(0, 0, loading_item)
        self.customers_table.setSpan(0, 0, 1, 10)

        # تحميل البيانات في الخلفية
        def load_customers():
            search_term = self.contacts_search_input.text().strip() if hasattr(self, "contacts_search_input") else ""
            cache_key = None
            if getattr(self, "cache", None):
                cache_key = f"ui:customers:search:{search_term}"
                customers = self.cache.get(cache_key)
            else:
                customers = None
            if customers is None:
                customers = self.customer_manager.search_customers(search_term=search_term, active_only=True)
                if getattr(self, "cache", None) and cache_key:
                    self.cache.set(cache_key, customers, ttl=45)
            return customers

        self._customers_loader = DataLoaderWorker(load_customers)
        self._customers_loader.data_loaded.connect(self._populate_customers_table)
        self._customers_loader.error_occurred.connect(
            lambda err: QMessageBox.critical(self, "خطأ", f"فشل تحميل بيانات العملاء: {err}")
        )
        self._start_worker(self._customers_loader)

    def _populate_customers_table(self, customers):
        """ملء جدول العملاء (في UI thread)"""
        # Guard: widget may have been deleted if the tab was recreated (libshiboken)
        if not hasattr(self, "customers_table"):
            return
        try:
            self.customers_table.isVisible()  # lightweight C++ liveness check
        except RuntimeError:
            del self.customers_table
            return

        # Quick Win: Disable updates during batch operations
        self.customers_table.setUpdatesEnabled(False)
        try:
            if customers is None:
                customers = []

            self.customers_table.setRowCount(len(customers))

            # Quick Win: Set uniform row height ONCE before loop
            self.customers_table.verticalHeader().setDefaultSectionSize(36)

            for row_index, customer in enumerate(customers):
                row_data = [
                    str(customer.id or ""),
                    customer.name or "-",
                    customer.phone or (customer.phone2 if hasattr(customer, "phone2") else None) or "-",
                    customer.email or "-",
                    customer.city or "-",
                    f"{float(customer.current_balance):,.2f}",
                    f"{float(customer.credit_limit):,.2f}",
                    (customer.last_purchase_date.isoformat() if customer.last_purchase_date else "-"),
                    str(customer.purchases_count or 0),
                ]

                for col_index, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    if col_index in (0, 5, 6, 8):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.customers_table.setItem(row_index, col_index, item)

                # Quick Win: setCellWidget is expensive, but keeping it for now
                # TODO: Replace with QTableView + custom delegate in Phase 2
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
                delete_btn.setStyleSheet("background-color: rgb(231, 76, 60); color: white;")
                delete_btn.clicked.connect(lambda checked, cid=customer.id: self.delete_customer(cid))
                actions_layout.addWidget(delete_btn)

                actions_layout.addStretch()
                self.customers_table.setCellWidget(row_index, 9, actions_widget)
                # REMOVED: setRowHeight() from inside loop - using setDefaultSectionSize() above

            self.update_customers_summary()

            # عرض رسالة واضحة إذا كانت القائمة فارغة
            if len(customers) == 0:
                self.customers_table.setRowCount(1)
                empty_item = QTableWidgetItem(
                    "لا توجد عملاء في قاعدة البيانات. اضغط على 'إضافة عميل' لإضافة عميل جديد."
                )
                empty_item.setTextAlignment(Qt.AlignCenter)
                self.customers_table.setItem(0, 0, empty_item)
                self.customers_table.setSpan(0, 0, 1, 10)
                if self.logger:
                    self.logger.info("ℹ️ لا توجد عملاء للعرض")
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في _populate_customers_table: {e}")
                import traceback

                self.logger.error(traceback.format_exc())
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات العملاء:\n{str(e)}")
        finally:
            # Quick Win: Re-enable updates after batch operations
            self.customers_table.setUpdatesEnabled(True)

    def update_customers_summary(self):
        """تحديث ملخص العملاء"""
        if not getattr(self, "customer_manager", None):
            return

        try:
            report = self.customer_manager.get_customers_summary()
            summary_text = (
                f"العملاء النشطون: {report.get('active_customers', 0):,} | "
                f"عملاء لديهم رصيد مستحق: {report.get('customers_with_balance', 0):,} | "
                f"إجمالي الأرصدة المستحقة: {report.get('total_outstanding_balance', 0):,.2f} دج"
            )
            if hasattr(self, "customers_summary_label"):
                self.customers_summary_label.setText(summary_text)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def refresh_suppliers_data(self):
        """تحديث جدول الموردين (محسّنة - في الخلفية)"""
        if not hasattr(self, "suppliers_table"):
            return

        if not getattr(self, "supplier_manager", None):
            self.suppliers_table.setRowCount(0)
            self.suppliers_summary_label.setText("تعذر تحميل بيانات الموردين (قاعدة البيانات غير متصلة).")
            return

        # عرض مؤشر التحميل
        self.suppliers_table.setRowCount(1)
        loading_item = QTableWidgetItem("⏳ جاري تحميل الموردين...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.suppliers_table.setItem(0, 0, loading_item)
        self.suppliers_table.setSpan(0, 0, 1, 10)

        # تحميل البيانات في الخلفية
        def load_suppliers():
            search_term = self.contacts_search_input.text().strip() if hasattr(self, "contacts_search_input") else ""
            cache_key = None
            if getattr(self, "cache", None):
                cache_key = f"ui:suppliers:search:{search_term}"
                suppliers = self.cache.get(cache_key)
            else:
                suppliers = None
            if suppliers is None:
                suppliers = self.supplier_manager.search_suppliers(search_term=search_term, active_only=True)
                if getattr(self, "cache", None) and cache_key:
                    self.cache.set(cache_key, suppliers, ttl=45)
            return suppliers

        self._suppliers_loader = DataLoaderWorker(load_suppliers)
        self._suppliers_loader.data_loaded.connect(self._populate_suppliers_table)
        self._suppliers_loader.error_occurred.connect(
            lambda err: QMessageBox.critical(self, "خطأ", f"فشل تحميل بيانات الموردين: {err}")
        )
        self._start_worker(self._suppliers_loader)

    def _populate_suppliers_table(self, suppliers):
        """ملء جدول الموردين (في UI thread)"""
        # Quick Win: Disable updates during batch operations
        self.suppliers_table.setUpdatesEnabled(False)
        try:
            if suppliers is None:
                suppliers = []

            self.suppliers_table.setRowCount(len(suppliers))

            # Quick Win: Set uniform row height ONCE before loop
            self.suppliers_table.verticalHeader().setDefaultSectionSize(36)

            for row_index, supplier in enumerate(suppliers):
                row_data = [
                    str(supplier.id or ""),
                    supplier.name or "-",
                    supplier.contact_person or "-",
                    supplier.phone or (supplier.phone2 if hasattr(supplier, "phone2") else None) or "-",
                    supplier.city or "-",
                    f"{float(supplier.current_balance):,.2f}",
                    f"{float(supplier.credit_limit):,.2f}",
                    (supplier.last_purchase_date.isoformat() if supplier.last_purchase_date else "-"),
                    str(supplier.purchases_count or 0),
                ]

                for col_index, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    if col_index in (0, 5, 6, 8):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.suppliers_table.setItem(row_index, col_index, item)

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
                delete_btn.setStyleSheet("background-color: rgb(231, 76, 60); color: white;")
                delete_btn.clicked.connect(lambda checked, sid=supplier.id: self.delete_supplier(sid))
                actions_layout.addWidget(delete_btn)

                actions_layout.addStretch()
                self.suppliers_table.setCellWidget(row_index, 9, actions_widget)
                # REMOVED: setRowHeight() from inside loop - using setDefaultSectionSize() above

            self.update_suppliers_summary()

            # عرض رسالة واضحة إذا كانت القائمة فارغة
            if len(suppliers) == 0:
                self.suppliers_table.setRowCount(1)
                empty_item = QTableWidgetItem(
                    "لا توجد موردين في قاعدة البيانات. اضغط على 'إضافة مورد' لإضافة مورد جديد."
                )
                empty_item.setTextAlignment(Qt.AlignCenter)
                self.suppliers_table.setItem(0, 0, empty_item)
                self.suppliers_table.setSpan(0, 0, 1, 10)
                if self.logger:
                    self.logger.info("ℹ️ لا توجد موردين للعرض")
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطأ في _populate_suppliers_table: {e}")
                import traceback

                self.logger.error(traceback.format_exc())
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات الموردين:\n{str(e)}")
        finally:
            # Quick Win: Re-enable updates after batch operations
            self.suppliers_table.setUpdatesEnabled(True)

    def update_suppliers_summary(self):
        """تحديث ملخص الموردين"""
        if not getattr(self, "supplier_manager", None):
            return

        try:
            report = self.supplier_manager.get_suppliers_summary()
            summary_text = (
                f"الموردون النشطون: {report.get('active_suppliers', 0):,} | "
                f"موردون لديهم رصيد مستحق: {report.get('suppliers_with_balance', 0):,} | "
                f"إجمالي الأرصدة المستحقة: {report.get('total_outstanding_balancef', 0):,.2f} دج"
            )
            if hasattr(self, "suppliers_summary_label"):
                self.suppliers_summary_label.setText(summary_text)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    # ===== عمليات إدارة العملاء والموردين =====
    def add_customer(self):
        """إضافة عميل جديد"""
        try:
            from src.ui.dialogs.customer_form_dialog import CustomerFormDialog

            dialog = CustomerFormDialog(self.db_manager, logger=self.logger, parent=self)
            if dialog.exec():
                self.refresh_contacts_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إضافة عميل:\n{str(e)}")

    def add_supplier(self):
        """إضافة مورد جديد"""
        try:
            from src.ui.dialogs.supplier_form_dialog import SupplierFormDialog

            dialog = SupplierFormDialog(self.db_manager, logger=self.logger, parent=self)
            if dialog.exec():
                self.refresh_contacts_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إضافة مورد:\n{str(e)}")

    def edit_customer(self, customer_id):
        """تعديل عميل"""
        try:
            from src.ui.dialogs.customer_form_dialog import CustomerFormDialog

            dialog = CustomerFormDialog(
                self.db_manager,
                customer_id=customer_id,
                logger=self.logger,
                parent=self,
            )
            if dialog.exec():
                self.refresh_contacts_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تعديل عميل:\n{str(e)}")

    def delete_customer(self, customer_id):
        """حذف عميل"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل تريد حذف هذا العميل؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if hasattr(self, "customer_manager") and self.customer_manager:
                    self.customer_manager.delete_customer(customer_id)
                    self.refresh_contacts_data()
                    QMessageBox.information(self, "نجح", "تم حذف العميل بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في حذف العميل: {str(e)}")

    def edit_supplier(self, supplier_id):
        """تعديل مورد"""
        try:
            from src.ui.dialogs.supplier_form_dialog import SupplierFormDialog

            dialog = SupplierFormDialog(
                self.db_manager,
                supplier_id=supplier_id,
                logger=self.logger,
                parent=self,
            )
            if dialog.exec():
                self.refresh_contacts_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تعديل مورد:\n{str(e)}")

    def delete_supplier(self, supplier_id):
        """حذف مورد"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل تريد حذف هذا المورد؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if hasattr(self, "supplier_manager") and self.supplier_manager:
                    self.supplier_manager.delete_supplier(supplier_id)
                    self.refresh_contacts_data()
                    QMessageBox.information(self, "نجح", "تم حذف المورد بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في حذف المورد: {str(e)}")

    def contacts_report(self):
        """عرض تقارير العملاء والموردين"""
        try:
            from src.ui.dialogs.contacts_report_dialog import ContactsReportDialog

            dialog = ContactsReportDialog(self, self.db_manager)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة التقارير:\n{str(e)}")
        self.refresh_inventory_data()
        self.refresh_contacts_data()

    def create_purchases_tab(self) -> QWidget:
        """إنشاء تبويب المشتريات"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("إدارة المشتريات وأوامر التوريد")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: {Colors.ACCENT_GOLD}; margin-bottom: 4px;")
        layout.addWidget(title)

        # أزرار الإجراءات
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        new_purchase_btn = QPushButton("📥 فاتورة شراء جديدة")
        new_purchase_btn.setMinimumHeight(36)
        new_purchase_btn.clicked.connect(self.new_purchase)
        buttons_layout.addWidget(new_purchase_btn)

        receive_btn = QPushButton("📦 استلام شحنة")
        receive_btn.setMinimumHeight(36)
        receive_btn.clicked.connect(self.receive_purchase_shipment)
        buttons_layout.addWidget(receive_btn)

        manage_suppliers_btn = QPushButton("🏢 إدارة الموردين")
        manage_suppliers_btn.setMinimumHeight(36)
        manage_suppliers_btn.clicked.connect(self.manage_suppliers)
        buttons_layout.addWidget(manage_suppliers_btn)

        purchases_report_btn = QPushButton("📊 تقرير المشتريات")
        purchases_report_btn.setMinimumHeight(36)
        purchases_report_btn.clicked.connect(self.purchases_report)
        buttons_layout.addWidget(purchases_report_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # مرشحات البحث
        filters_frame = QFrame()
        filters_frame.setObjectName("purchasesFiltersFrame")
        filters_frame.setStyleSheet(
            "QFrame { "
            "background-color: #000000; "
            "border: 1px solid #333333; "
            "border-radius: 6px; "
            "} "
            "QLabel { color: {Colors.TEXT_BRIGHT}; font-weight: 600; } "
            "QLineEdit, QComboBox { background-color: #111111; color: {Colors.TEXT_BRIGHT}; border: 1px solid #444444; border-radius: 4px; padding: 4px; } "  # noqa: E501
            "QPushButton { background-color: #2563eb; color: {Colors.TEXT_BRIGHT}; font-weight: bold; border-radius: 4px; } "
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(12)

        search_label = QLabel("بحث:")
        search_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(search_label)

        self.purchase_search_input = QLineEdit()
        self.purchase_search_input.setPlaceholderText("ابحث برقم الفاتورة أو اسم المورد...")
        self.purchase_search_input.textChanged.connect(self.on_purchases_filters_changed)
        filters_layout.addWidget(self.purchase_search_input, 2)

        status_label = QLabel("حالة الاستلام:")
        status_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(status_label)

        self.purchase_status_combo = QComboBox()
        self.purchase_status_combo.setMinimumWidth(150)
        self.purchase_status_combo.addItems(["الكل", "معلقة", "مستلمة", "جزئية", "ملغية", "مرتجعة"])
        self.purchase_status_combo.currentIndexChanged.connect(self.on_purchases_filters_changed)
        filters_layout.addWidget(self.purchase_status_combo, 1)

        payment_status_label = QLabel("حالة الدفع:")
        payment_status_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(payment_status_label)

        self.purchase_payment_combo = QComboBox()
        self.purchase_payment_combo.setMinimumWidth(150)
        self.purchase_payment_combo.addItems(["الكل", "غير مدفوعة", "مدفوعة جزئياً", "مدفوعة", "متأخرة"])
        self.purchase_payment_combo.currentIndexChanged.connect(self.on_purchases_filters_changed)
        filters_layout.addWidget(self.purchase_payment_combo, 1)

        supplier_label = QLabel("المورد:")
        supplier_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(supplier_label)

        self.purchase_supplier_combo = QComboBox()
        self.purchase_supplier_combo.setMinimumWidth(180)
        self.purchase_supplier_combo.addItem("كل الموردين", None)
        self.purchase_supplier_combo.currentIndexChanged.connect(self.on_purchases_filters_changed)
        filters_layout.addWidget(self.purchase_supplier_combo, 1)

        self.purchase_refresh_btn = QPushButton("🔄 تحديث")
        self.purchase_refresh_btn.setMinimumHeight(32)
        self.purchase_refresh_btn.clicked.connect(self.refresh_purchases_data)
        filters_layout.addWidget(self.purchase_refresh_btn)

        layout.addWidget(filters_frame)

        # ملخص المشتريات
        purchase_summary_group = QGroupBox("ملخص المشتريات")
        purchase_summary_layout = QHBoxLayout(purchase_summary_group)
        purchase_summary_layout.setContentsMargins(12, 12, 12, 12)
        purchase_summary_layout.setSpacing(18)

        purchase_summary_items = [
            ("total_purchases", "إجمالي الفواتير"),
            ("total_amount", "إجمالي قيمة الفواتير"),
            ("total_paid", "المبالغ المدفوعة"),
            ("total_remaining", "المبالغ المتبقية"),
            ("avg_purchase_value", "متوسط قيمة الفاتورة"),
        ]

        self.purchase_summary_labels = {}
        for key, title_text in purchase_summary_items:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)

            title_label = QLabel(title_text)
            title_label.setStyleSheet("color: rgb(127, 140, 141); font-size: 12px;")
            value_label = QLabel("-")
            value_label.setStyleSheet("font-size: 20px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")

            container_layout.addWidget(title_label)
            container_layout.addWidget(value_label)
            container_layout.addStretch()

            purchase_summary_layout.addWidget(container)
            self.purchase_summary_labels[key] = value_label

        purchase_summary_layout.addStretch()
        layout.addWidget(purchase_summary_group)

        # جدول المشتريات
        self.purchases_table = QTableWidget()
        self.purchases_table.setColumnCount(8)
        self.purchases_table.setHorizontalHeaderLabels(
            [
                "رقم الفاتورة",
                "المورد",
                "تاريخ الشراء",
                "إجمالي الفاتورة",
                "المبلغ المدفوع",
                "المبلغ المتبقي",
                "حالة الاستلام",
                "حالة الدفع",
            ]
        )
        header = self.purchases_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(120)
        header.setDefaultSectionSize(150)
        header.setStretchLastSection(True)
        self.purchases_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.purchases_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.purchases_table.setAlternatingRowColors(True)
        self.purchases_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.purchases_table.itemDoubleClicked.connect(self.on_purchase_double_clicked)
        self.purchases_table.setStyleSheet(
            "QTableView, QTableWidget { "
            "background-color: #000000; "
            "color: {Colors.TEXT_BRIGHT}; "
            "gridline-color: #333333; "
            "border: 1px solid #333333; "
            "border-radius: 4px; "
            "} "
            "QTableView::item, QTableWidget::item { "
            "padding: 4px; "
            "border: none; "
            "} "
            "QTableView::item:selected, QTableWidget::item:selected { "
            "background-color: #1e3a8a; "
            "color: {Colors.TEXT_BRIGHT}; "
            "} "
            "QTableView::item:hover, QTableWidget::item:hover { "
            "background-color: #1f2937; "
            "} "
            "QHeaderView::section { "
            "background-color: #111111; "
            "color: {Colors.TEXT_BRIGHT}; "
            "font-weight: bold; "
            "padding: 8px; "
            "border: 1px solid #333333; "
            "} "
            "QScrollBar:vertical { "
            "border: none; "
            "background: #111111; "
            "width: 12px; "
            "border-radius: 6px; "
            "} "
            "QScrollBar::handle:vertical { "
            "background: #333333; "
            "min-height: 30px; "
            "border-radius: 6px; "
            "} "
            "QScrollBar::handle:vertical:hover { "
            "background: #555555; "
            "}"
        )
        layout.addWidget(self.purchases_table)

        self.load_purchase_suppliers()
        self.refresh_purchases_data()

        return tab

    def create_payments_tab(self) -> QWidget:
        """إنشاء تبويب المدفوعات والذمم"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("لوحة المدفوعات والذمم المدينة/الدائنة")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: rgb(22, 160, 133); margin-bottom: 4px;")
        layout.addWidget(title)

        # تأكد من توفر خدمة المدفوعات
        if not getattr(self, "payment_service", None) and self.db_manager:
            # هنا يمكن معالجة الخطأ أو تهيئة الخدمة حسب الحاجة
            pass
        filters_frame = QFrame()
        filters_frame.setObjectName("paymentsFiltersFrame")
        filters_frame.setStyleSheet("")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(12)

        date_label = QLabel("الفترة:")
        date_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(date_label)

        self.payments_start_date = QDateEdit()
        self.payments_start_date.setCalendarPopup(True)
        self.payments_start_date.setDate(QDate.currentDate().addDays(-30))
        self.payments_start_date.dateChanged.connect(lambda *_: self.refresh_payments_data())
        filters_layout.addWidget(self.payments_start_date)

        to_label = QLabel("إلى")
        filters_layout.addWidget(to_label)

        self.payments_end_date = QDateEdit()
        self.payments_end_date.setCalendarPopup(True)
        self.payments_end_date.setDate(QDate.currentDate())
        self.payments_end_date.dateChanged.connect(lambda *_: self.refresh_payments_data())
        filters_layout.addWidget(self.payments_end_date)

        self.payments_refresh_btn = QPushButton("🔄 تحديث")
        self.payments_refresh_btn.setMinimumHeight(32)
        self.payments_refresh_btn.clicked.connect(self.refresh_payments_data)
        filters_layout.addWidget(self.payments_refresh_btn)

        self.payments_new_btn = QPushButton("➕ دفعة جديدة")
        self.payments_new_btn.setMinimumHeight(32)
        self.payments_new_btn.clicked.connect(self.show_payment_dialog)
        filters_layout.addWidget(self.payments_new_btn)

        filters_layout.addStretch()
        layout.addWidget(filters_frame)

        # ملخص المدفوعات
        summary_group = QGroupBox("المؤشرات السريعة")
        summary_layout = QHBoxLayout(summary_group)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(18)

        summary_items = [
            ("customer_payments", "مقبوضات العملاء"),
            ("supplier_payments", "مدفوعات الموردين"),
            ("total_payments", "إجمالي العمليات"),
            ("net_cash_flow", "صافي التدفق النقدي"),
        ]
        self.payment_summary_labels = {}
        for key, title_text in summary_items:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)

            title_label = QLabel(title_text)
            title_label.setStyleSheet("color: rgb(127, 140, 141); font-size: 12px;")
            value_label = QLabel("-")
            value_label.setStyleSheet("font-size: 20px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")

            container_layout.addWidget(title_label)
            container_layout.addWidget(value_label)
            container_layout.addStretch()

            summary_layout.addWidget(container)
            self.payment_summary_labels[key] = value_label

        summary_layout.addStretch()
        layout.addWidget(summary_group)

        # جدول المدفوعات
        payments_group = QGroupBox("آخر المدفوعات")
        payments_layout = QVBoxLayout(payments_group)
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(7)
        self.payments_table.setHorizontalHeaderLabels(
            [
                "رقم الدفعة",
                "النوع",
                "الجهة",
                "تاريخ الدفع",
                "طريقة الدفع",
                "الحالة",
                "المبلغ",
            ]
        )
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.payments_table.horizontalHeader().setMinimumSectionSize(120)
        self.payments_table.horizontalHeader().setDefaultSectionSize(150)
        self.payments_table.horizontalHeader().setStretchLastSection(True)
        self.payments_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.payments_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.payments_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        payments_layout.addWidget(self.payments_table)
        layout.addWidget(payments_group)

        # جداول تفصيلية
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(12)

        breakdown_group = QGroupBox("توزيع حسب النوع وطريقة الدفع")
        breakdown_layout = QVBoxLayout(breakdown_group)
        self.payment_breakdown_table = QTableWidget()
        self.payment_breakdown_table.setColumnCount(4)
        self.payment_breakdown_table.setHorizontalHeaderLabels(["النوع", "الطريقة", "عدد العمليات", "الإجمالي"])
        self.payment_breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.payment_breakdown_table.horizontalHeader().setMinimumSectionSize(120)
        self.payment_breakdown_table.horizontalHeader().setDefaultSectionSize(150)
        self.payment_breakdown_table.horizontalHeader().setStretchLastSection(True)
        self.payment_breakdown_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.payment_breakdown_table.setSelectionMode(QAbstractItemView.NoSelection)
        breakdown_layout.addWidget(self.payment_breakdown_table)
        tables_layout.addWidget(breakdown_group, 1)

        schedules_group = QGroupBox("الاستحقاقات القادمة")
        schedules_layout = QVBoxLayout(schedules_group)
        self.payment_schedules_table = QTableWidget()
        self.payment_schedules_table.setColumnCount(6)
        self.payment_schedules_table.setHorizontalHeaderLabels(
            [
                "رقم القسط",
                "رقم الدفعة",
                "تاريخ الاستحقاق",
                "المبلغ",
                "المتبقي",
                "الحالة",
            ]
        )
        self.payment_schedules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.payment_schedules_table.horizontalHeader().setMinimumSectionSize(120)
        self.payment_schedules_table.horizontalHeader().setDefaultSectionSize(150)
        self.payment_schedules_table.horizontalHeader().setStretchLastSection(True)
        self.payment_schedules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.payment_schedules_table.setSelectionMode(QAbstractItemView.NoSelection)
        schedules_layout.addWidget(self.payment_schedules_table)
        tables_layout.addWidget(schedules_group, 1)

        layout.addLayout(tables_layout)

        # حالة الخدمة
        self.payments_status_label = QLabel("")
        self.payments_status_label.setStyleSheet("color: rgb(192, 57, 43);")
        layout.addWidget(self.payments_status_label)

        self.refresh_payments_data()
        return tab

    def refresh_payments_data(self):
        """تحديث بيانات تبويب المدفوعات"""
        if not hasattr(self, "payments_table"):
            return

        if not getattr(self, "payment_service", None):
            self.payments_table.setRowCount(0)
            self.payment_breakdown_table.setRowCount(0)
            self.payment_schedules_table.setRowCount(0)
            self.payments_status_label.setText("خدمة المدفوعات غير متوفرة حالياً.")
            return

        start_time = time.perf_counter()
        try:
            # الحصول على التواريخ من التقارير أو استخدام القيم الافتراضية
            if hasattr(self, "reports_start_date") and hasattr(self, "reports_end_date"):
                start_date = (
                    self.reports_start_date.date()
                    if hasattr(self.reports_start_date, "date")
                    else date.today() - timedelta(days=30)
                )
                end_date = self.reports_end_date.date() if hasattr(self.reports_end_date, "date") else date.today()
            else:
                end_date = date.today()
                start_date = end_date - timedelta(days=30)

            summary = self.payment_service.get_payment_summary(start_date, end_date)
            self.update_payments_summary(summary or {})

            payments = self.payment_service.get_payments_by_date_range(start_date, end_date)
            self._populate_payments_table(payments)

            breakdown = summary.get("by_type_and_method", []) if summary else []
            self._populate_payment_breakdown_table(breakdown)

            schedules = self.payment_service.get_payment_schedules(limit=50)
            self._populate_payment_schedules_table(schedules)

            self.payments_status_label.setText("")
        except Exception as exc:
            self.payments_status_label.setText(f"فشل تحديث بيانات المدفوعات: {exc}")
        finally:
            self._log_section_duration("refresh_payments_data", start_time)

            # ✅ إعادة تشغيل مراقب الجلسة بعد أن هدأ الوضع
            if hasattr(self, "session_monitor_timer") and self.session_monitor_timer:
                if not self.session_monitor_timer.isActive():
                    if self.logger:
                        self.logger.debug("▶️ إعادة تشغيل session_monitor_timer بعد انتهاء تحميل المدفوعات")
                    self.session_monitor_timer.start(60000)  # كل 60 ثانية

    def update_payments_summary(self, summary: Dict[str, Any]):
        """تحديث مؤشرات المدفوعات"""
        totals = summary.get("totals", {}) if summary else {}

        for key in (
            "customer_payments",
            "supplier_payments",
            "total_payments",
            "net_cash_flow",
        ):
            label = self.payment_summary_labels.get(key)
            if label:
                label.setText(self._format_currency(totals.get(key, 0)))

    def _populate_payments_table(self, payments):
        """عرض قائمة المدفوعات"""
        table = self.payments_table
        payments = payments or []
        if not payments:
            table.setRowCount(1)
            empty_item = QTableWidgetItem("لا توجد عمليات دفع في الفترة المحددة")
            empty_item.setTextAlignment(Qt.AlignCenter)
            table.setSpan(0, 0, 1, table.columnCount())
            table.setItem(0, 0, empty_item)
            return
        table.setRowCount(len(payments))

        for row, payment in enumerate(payments):
            entity = self._get_payment_entity_name(payment)
            payment_date = payment.payment_date.strftime("%Y-%m-%d") if getattr(payment, "payment_date", None) else "-"

            row_values = [
                getattr(payment, "payment_number", None) or f"PAY-{getattr(payment, 'id', 'f')}",
                getattr(payment, "payment_type", "-"),
                entity,
                payment_date,
                getattr(payment, "payment_method", "-"),
                getattr(payment, "status", "-"),
                self._format_currency(
                    getattr(payment, "amount_in_base_currency", None) or getattr(payment, "amount", 0)
                ),
            ]

            for col, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                if col in (6,):
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                table.setItem(row, col, item)

    def _populate_payment_breakdown_table(self, breakdown):
        """عرض توزيع المدفوعات"""
        table = self.payment_breakdown_table
        breakdown = breakdown or []
        if not breakdown:
            table.setRowCount(1)
            msg = QTableWidgetItem("لا يوجد توزيع متاح للفترة الحالية")
            msg.setTextAlignment(Qt.AlignCenter)
            table.setSpan(0, 0, 1, table.columnCount())
            table.setItem(0, 0, msg)
            return
        table.setRowCount(len(breakdown))

        for row, entry in enumerate(breakdown):
            row_values = [
                entry.get("payment_type", "-"),
                entry.get("payment_method", "-"),
                entry.get("count", 0),
                self._format_currency(entry.get("amount", 0)),
            ]
            for col, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                if col == 2:
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter)
                table.setItem(row, col, item)

    def _populate_payment_schedules_table(self, schedules):
        """عرض الجدولة القادمة للمدفوعات"""
        table = self.payment_schedules_table
        schedules = schedules or []
        if not schedules:
            table.setRowCount(1)
            msg = QTableWidgetItem("لا توجد استحقاقات حالياً")
            msg.setTextAlignment(Qt.AlignCenter)
            table.setSpan(0, 0, 1, table.columnCount())
            table.setItem(0, 0, msg)
            return
        table.setRowCount(len(schedules))

        for row, schedule in enumerate(schedules):
            due_date = schedule.get("due_date")
            due_text = due_date.strftime("%Y-%m-%d") if isinstance(due_date, date) else str(due_date or "-")

            row_values = [
                schedule.get("installment_number", "-"),
                schedule.get("payment_id", "-"),
                due_text,
                self._format_currency(schedule.get("amount", 0)),
                self._format_currency(schedule.get("remaining_amount", 0)),
                schedule.get("status", "-"),
            ]

            for col, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                if col in (3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter)
                if schedule.get("is_overdue"):
                    item.setForeground(QColor("#c0392b"))
                table.setItem(row, col, item)

    def _get_payment_entity_name(self, payment) -> str:
        """محاولة استخراج اسم الجهة المرتبطة بالدفعة"""
        try:
            if payment.payment_type == PaymentType.CUSTOMER_PAYMENT.value and payment.customer_id:
                if getattr(self, "customer_manager", None):
                    customer = self.customer_manager.get_customer_by_id(payment.customer_id)
                    if customer and getattr(customer, "name", None):
                        return customer.name
                return f"عميل #{payment.customer_id}"
            if payment.payment_type == PaymentType.SUPPLIER_PAYMENT.value and payment.supplier_id:
                if getattr(self, "supplier_manager", None):
                    supplier = self.supplier_manager.get_supplier_by_id(payment.supplier_id)
                    if supplier and getattr(supplier, "name", None):
                        return supplier.name
                return f"مورد #{payment.supplier_id}"
        except Exception:
            return "-"

    def create_reports_tab(self) -> QWidget:
        """إنشاء تبويب التقارير"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("لوحة التقارير والمؤشرات")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: rgb(155, 89, 182); margin-bottom: 4px;")
        layout.addWidget(title)

        # منطقة الفلاتر
        filters_frame = QFrame()
        filters_frame.setObjectName("reportsFiltersFrame")
        filters_frame.setStyleSheet("")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(12)

        date_label = QLabel("النطاق الزمني:")
        date_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(date_label)

        self.report_start_date = QDateEdit()
        self.report_start_date.setCalendarPopup(True)
        self.report_start_date.setDate(QDate.currentDate().addDays(-30))
        filters_layout.addWidget(self.report_start_date)

        to_label = QLabel("إلى")
        filters_layout.addWidget(to_label)

        self.report_end_date = QDateEdit()
        self.report_end_date.setCalendarPopup(True)
        self.report_end_date.setDate(QDate.currentDate())
        filters_layout.addWidget(self.report_end_date)

        quick_buttons_layout = QHBoxLayout()
        self.report_last_7_btn = QPushButton("آخر 7 أيام")
        self.report_last_7_btn.setMinimumHeight(30)
        self.report_last_7_btn.clicked.connect(lambda: self.set_report_quick_range(7))
        quick_buttons_layout.addWidget(self.report_last_7_btn)

        self.report_last_30_btn = QPushButton("آخر 30 يوم")
        self.report_last_30_btn.setMinimumHeight(30)
        self.report_last_30_btn.clicked.connect(lambda: self.set_report_quick_range(30))
        quick_buttons_layout.addWidget(self.report_last_30_btn)

        filters_layout.addLayout(quick_buttons_layout)

        self.report_refresh_btn = QPushButton("🔄 تحديث التقارير")
        self.report_refresh_btn.setMinimumHeight(32)
        self.report_refresh_btn.clicked.connect(self.refresh_reports_data)
        filters_layout.addWidget(self.report_refresh_btn)

        # محدد نوع التقرير
        report_type_label = QLabel("نوع التقرير:")
        report_type_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        filters_layout.addWidget(report_type_label)

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(
            [
                "ملخص المبيعات",
                "ملخص المشتريات",
                "الملخص المالي",
                "تحليل المنتجات",
                "تحليل العملاء",
                "تحليل الموردين",
            ]
        )
        self.report_type_combo.setMinimumWidth(150)
        filters_layout.addWidget(self.report_type_combo)

        # أزرار التنقل السريع إلى التقارير التفصيلية
        self.report_open_detailed_btn = QPushButton("📊 فتح تقرير تفصيلي")
        self.report_open_detailed_btn.setMinimumHeight(32)
        self.report_open_detailed_btn.clicked.connect(self.open_detailed_report)
        filters_layout.addWidget(self.report_open_detailed_btn)

        layout.addWidget(filters_frame)

        # ملخص المؤشرات
        summary_group = QGroupBox("الملخص المالي")
        summary_layout = QHBoxLayout(summary_group)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(18)

        summary_items = [
            ("total_sales", "إجمالي المبيعات"),
            ("total_purchases", "إجمالي المشتريات"),
            ("gross_profit", "إجمالي الربح"),
            ("profit_margin", "هامش الربح"),
            ("receivables", "الذمم المدينة"),
            ("payables", "الذمم الدائنة"),
        ]

        self.reports_summary_labels = {}
        for key, title_text in summary_items:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)

            title_label = QLabel(title_text)
            title_label.setStyleSheet("color: rgb(127, 140, 141); font-size: 12px;")
            value_label = QLabel("-")
            value_label.setStyleSheet("font-size: 20px; font-weight: bold; color: {Colors.TEXT_BRIGHT};")

            container_layout.addWidget(title_label)
            container_layout.addWidget(value_label)
            container_layout.addStretch()

            summary_layout.addWidget(container)
            self.reports_summary_labels[key] = value_label

        summary_layout.addStretch()
        layout.addWidget(summary_group)

        # جداول المؤشرات
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(12)

        # جدول أفضل المنتجات
        top_products_group = QGroupBox("أفضل المنتجات مبيعاً")
        top_products_layout = QVBoxLayout(top_products_group)
        self.top_products_table = QTableWidget()
        self.top_products_table.setColumnCount(3)
        self.top_products_table.setHorizontalHeaderLabels(["المنتج", "الكمية", "القيمة"])
        self.top_products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.top_products_table.horizontalHeader().setMinimumSectionSize(120)
        self.top_products_table.horizontalHeader().setDefaultSectionSize(150)
        self.top_products_table.horizontalHeader().setStretchLastSection(True)
        self.top_products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.top_products_table.setSelectionMode(QAbstractItemView.NoSelection)
        top_products_layout.addWidget(self.top_products_table)
        tables_layout.addWidget(top_products_group, 2)

        # توزيع طرق الدفع
        distribution_group = QGroupBox("توزيع المبيعات حسب طريقة الدفع")
        distribution_layout = QVBoxLayout(distribution_group)
        self.payment_distribution_table = QTableWidget()
        self.payment_distribution_table.setColumnCount(2)
        self.payment_distribution_table.setHorizontalHeaderLabels(["الطريقة", "القيمة"])
        self.payment_distribution_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.payment_distribution_table.horizontalHeader().setMinimumSectionSize(120)
        self.payment_distribution_table.horizontalHeader().setDefaultSectionSize(150)
        self.payment_distribution_table.horizontalHeader().setStretchLastSection(True)
        self.payment_distribution_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.payment_distribution_table.setSelectionMode(QAbstractItemView.NoSelection)
        distribution_layout.addWidget(self.payment_distribution_table)
        tables_layout.addWidget(distribution_group, 1)

        layout.addLayout(tables_layout)

        # جدول الإيرادات مقابل المصروفات
        revenue_group = QGroupBox("الإيرادات مقابل المشتريات")
        revenue_layout = QVBoxLayout(revenue_group)
        self.revenue_vs_expense_table = QTableWidget()
        self.revenue_vs_expense_table.setColumnCount(3)
        self.revenue_vs_expense_table.setHorizontalHeaderLabels(["التاريخ", "الإيرادات", "المشتريات"])
        self.revenue_vs_expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.revenue_vs_expense_table.horizontalHeader().setMinimumSectionSize(120)
        self.revenue_vs_expense_table.horizontalHeader().setDefaultSectionSize(150)
        self.revenue_vs_expense_table.horizontalHeader().setStretchLastSection(True)
        self.revenue_vs_expense_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.revenue_vs_expense_table.setSelectionMode(QAbstractItemView.NoSelection)
        revenue_layout.addWidget(self.revenue_vs_expense_table)
        layout.addWidget(revenue_group)

        # الرسوم البيانية
        chart_group = QGroupBox("رسم بياني: الإيرادات مقابل المشتريات")
        chart_layout = QVBoxLayout(chart_group)
        self.revenue_chart = QChart()
        self.revenue_chart.legend().setVisible(True)
        self.revenue_chart_view = QChartView(self.revenue_chart)
        self.revenue_chart_view.setRenderHint(QPainter.Antialiasing)
        chart_layout.addWidget(self.revenue_chart_view)
        layout.addWidget(chart_group)

        # أزرار التصدير والطباعة
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        self.report_export_pdf_btn = QPushButton("⬇️ تصدير PDF")
        self.report_export_pdf_btn.clicked.connect(lambda: self.export_reports_summary(ExportFormat.PDF))
        actions_layout.addWidget(self.report_export_pdf_btn)

        self.report_export_excel_btn = QPushButton("⬇️ تصدير Excel")
        self.report_export_excel_btn.clicked.connect(lambda: self.export_reports_summary(ExportFormat.EXCEL))
        actions_layout.addWidget(self.report_export_excel_btn)

        self.report_print_btn = QPushButton("🖨️ طباعة ملخص")
        self.report_print_btn.clicked.connect(self.print_reports_summary)
        actions_layout.addWidget(self.report_print_btn)

        layout.addLayout(actions_layout)

        # مؤشر التحميل (يُضاف ديناميكياً عند الحاجة)
        self.reports_loading_label = None

        self.refresh_reports_data()
        return tab

    def _show_reports_loading(self, show: bool):
        """إظهار/إخفاء مؤشر التحميل في تبويب التقارير"""
        if not hasattr(self, "reports_tab") or self.reports_tab is None:
            return

        try:
            if show:
                # إنشاء مؤشر التحميل إذا لم يكن موجوداً
                if self.reports_loading_label is None:
                    from PySide6.QtWidgets import QLabel

                    self.reports_loading_label = QLabel("⏳ جاري تحميل البيانات...")
                    self.reports_loading_label.setStyleSheet("""
                        QLabel {
                            background-color: rgba(255, 255, 255, 230);
                            border: 2px solid #3b82f6;
                            border-radius: 8px;
                            padding: 20px;
                            font-size: 14px;
                            font-weight: bold;
                            color: #1e40af;
                        }
                    """)
                    self.reports_loading_label.setAlignment(Qt.AlignCenter)
                    self.reports_loading_label.setMinimumHeight(60)

                # إضافة المؤشر إلى التبويب
                layout = self.reports_tab.layout()
                if layout and self.reports_loading_label.parent() is None:
                    layout.insertWidget(1, self.reports_loading_label)

                # تعطيل الأزرار أثناء التحميل
                if hasattr(self, "report_refresh_btn"):
                    self.report_refresh_btn.setEnabled(False)
                    self.reports_loading_label.show()
            else:
                # إخفاء المؤشر
                if self.reports_loading_label:
                    self.reports_loading_label.hide()

                # تفعيل الأزرار بعد التحميل
                if hasattr(self, "report_refresh_btn"):
                    self.report_refresh_btn.setEnabled(True)
        except Exception:
            # تجاهل الأخطاء في مؤشر التحميل
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def create_contacts_tab(self) -> QWidget:
        """إنشاء تبويب العملاء والموردين"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("إدارة العملاء والموردين")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: rgb(243, 156, 18); margin-bottom: 4px;")
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
        contacts_filters_frame.setStyleSheet("")
        contacts_filters_layout = QHBoxLayout(contacts_filters_frame)
        contacts_filters_layout.setContentsMargins(12, 8, 12, 8)
        contacts_filters_layout.setSpacing(12)

        search_label = QLabel("بحث:")
        search_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
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
        self.customers_summary_label.setStyleSheet("font-size: 14px; color: {Colors.TEXT_BRIGHT};")
        customers_summary_layout.addWidget(self.customers_summary_label)
        customers_layout.addWidget(customers_summary_group)

        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(10)
        self.customers_table.setHorizontalHeaderLabels(
            [
                "المعرف",
                "الاسم",
                "الهاتف",
                "البريد الإلكتروني",
                "المدينة",
                "الرصيد الحالي",
                "الحد الائتماني",
                "آخر شراء",
                "عدد الفواتير",
                "الإجراءات",
            ]
        )
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.customers_table.horizontalHeader().setMinimumSectionSize(120)
        self.customers_table.horizontalHeader().setDefaultSectionSize(150)
        self.customers_table.horizontalHeader().setStretchLastSection(True)
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
        self.suppliers_summary_label.setStyleSheet("font-size: 14px; color: {Colors.TEXT_BRIGHT};")
        suppliers_summary_layout.addWidget(self.suppliers_summary_label)
        suppliers_layout.addWidget(suppliers_summary_group)

        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(10)
        self.suppliers_table.setHorizontalHeaderLabels(
            [
                "المعرف",
                "الاسم",
                "مسؤول الاتصال",
                "الهاتف",
                "المدينة",
                "الرصيد الحالي",
                "الحد الائتماني",
                "آخر شراء",
                "عدد فواتير الشراء",
                "الإجراءات",
            ]
        )
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.suppliers_table.horizontalHeader().setMinimumSectionSize(120)
        self.suppliers_table.horizontalHeader().setDefaultSectionSize(150)
        self.suppliers_table.horizontalHeader().setStretchLastSection(True)
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
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #cbd5e1; margin: 10px;")
        layout.addWidget(title)

        buttons_layout = QHBoxLayout()

        general_settings_btn = QPushButton("⚙️ الإعدادات العامة")
        general_settings_btn.setMinimumHeight(40)
        buttons_layout.addWidget(general_settings_btn)

        template_editor_btn = QPushButton("🎨 محرر القوالب")
        template_editor_btn.setMinimumHeight(40)
        template_editor_btn.clicked.connect(self.show_template_editor)
        buttons_layout.addWidget(template_editor_btn)

        backup_btn = QPushButton("💾 النسخ الاحتياطي")
        backup_btn.setMinimumHeight(40)
        backup_btn.clicked.connect(self.backup_database)
        buttons_layout.addWidget(backup_btn)

        users_btn = QPushButton("👥 إدارة المستخدمين")
        users_btn.setMinimumHeight(40)
        users_btn.clicked.connect(self.show_user_management)
        buttons_layout.addWidget(users_btn)

        permissions_btn = QPushButton("🔐 إدارة الصلاحيات")
        permissions_btn.setMinimumHeight(40)
        permissions_btn.clicked.connect(self.show_permission_management)
        buttons_layout.addWidget(permissions_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Automated Backup Settings
        backup_group = QGroupBox("النسخ الاحتياطي التلقائي")
        backup_layout = QVBoxLayout(backup_group)

        backup_form_layout = QFormLayout()
        self.backup_enabled_check = QCheckBox("تفعيل النسخ الاحتياطي اليومي")
        self.backup_time_edit = QTimeEdit()
        self.backup_keep_spin = QSpinBox()
        self.backup_keep_spin.setRange(1, 100)
        self.backup_keep_spin.setSuffix(" نسخة")

        backup_form_layout.addRow(self.backup_enabled_check)
        backup_form_layout.addRow("وقت النسخ الاحتياطي:", self.backup_time_edit)
        backup_form_layout.addRow("الاحتفاظ بآخر:", self.backup_keep_spin)

        save_backup_btn = QPushButton("حفظ إعدادات النسخ الاحتياطي")
        save_backup_btn.clicked.connect(self.save_backup_settings)

        backup_layout.addLayout(backup_form_layout)
        backup_layout.addWidget(save_backup_btn)
        layout.addWidget(backup_group)

        # Printer Settings
        printer_group = QGroupBox("إعدادات طابعة الإيصالات")
        printer_layout = QVBoxLayout(printer_group)

        printer_form_layout = QHBoxLayout()
        self.printer_combo = QComboBox()
        self.printer_combo.setMinimumWidth(300)
        printer_form_layout.addWidget(QLabel("الطابعة المحددة:"))
        printer_form_layout.addWidget(self.printer_combo)

        refresh_printers_btn = QPushButton("تحديث قائمة الطابعات")
        refresh_printers_btn.clicked.connect(self.populate_printers_list)
        printer_form_layout.addWidget(refresh_printers_btn)

        save_printer_btn = QPushButton("حفظ الطابعة")
        save_printer_btn.clicked.connect(self.save_printer_selection)
        printer_form_layout.addWidget(save_printer_btn)

        printer_layout.addLayout(printer_form_layout)
        self.printer_status_label = QLabel("")
        self.printer_status_label.setStyleSheet("color: rgb(127, 140, 141); font-size: 12px;")
        printer_layout.addWidget(self.printer_status_label)
        layout.addWidget(printer_group)

        # مجموعة إعدادات الإشعارات
        notifications_group = QGroupBox("إعدادات الإشعارات")
        notif_layout = QHBoxLayout(notifications_group)
        notif_layout.setContentsMargins(12, 12, 12, 12)
        notif_layout.setSpacing(12)

        notif_label = QLabel("فترة الفحص:")
        notif_layout.addWidget(notif_label)

        self.notifications_interval_combo = QComboBox()
        self.notifications_interval_combo.setMinimumWidth(200)
        minutes_options = [1, 2, 5, 10, 15, 30]
        for m in minutes_options:
            self.notifications_interval_combo.addItem(f"كل {m} دقيقة", m)
        notif_layout.addWidget(self.notifications_interval_combo)

        try:
            from PySide6.QtCore import QSettings

            s = QSettings("StandardElJoumla", "ERP")
            val = s.value("notifications/interval_seconds", type=int)
            current_m = 5
            if val is not None:
                current_m = max(1, int(int(val) / 60))
            idx = self.notifications_interval_combo.findData(current_m)
            if idx >= 0:
                self.notifications_interval_combo.setCurrentIndex(idx)
        except Exception:
            self.notifications_interval_combo.currentIndexChanged.connect(self.on_notifications_interval_changed)
        layout.addWidget(notifications_group)

        # مجموعة إعدادات الأمان
        security_group = QGroupBox("إعدادات الأمان")
        security_layout = QVBoxLayout(security_group)
        security_layout.setContentsMargins(12, 12, 12, 12)
        security_layout.setSpacing(8)

        encryption_info = QLabel("🔒 التشفير: النسخ الاحتياطية المشفرة متاحة من قائمة 'ملف'")
        encryption_info.setStyleSheet("color: rgb(127, 140, 141); font-size: 11px;")
        security_layout.addWidget(encryption_info)

        security_actions_layout = QHBoxLayout()
        security_actions_layout.setSpacing(8)

        encryption_settings_btn = QPushButton("⚙️ إعدادات التشفير")
        encryption_settings_btn.clicked.connect(self.show_encryption_dialog)
        security_actions_layout.addWidget(encryption_settings_btn)

        security_actions_layout.addStretch()
        security_layout.addLayout(security_actions_layout)

        layout.addWidget(security_group)

        layout.addStretch()

        self.load_backup_settings()
        self.populate_printers_list()

        # تحديث تسمية السمة الحالية
        try:
            current_theme = self.config_manager.get("theme", "light")
            if hasattr(self, "current_theme_label"):
                self.current_theme_label.setText("داكن" if current_theme == "dark" else "فاتح")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")
        return tab

    def load_backup_settings(self):
        """Loads backup settings from QSettings."""
        from PySide6.QtCore import QSettings, QTime

        s = QSettings("StandardElJoumla", "ERP")
        is_enabled = s.value("backup/auto_enabled", False, type=bool)
        backup_time_str = s.value("backup/time", "02:00")
        backups_to_keep = s.value("backup/keep", 7, type=int)

        self.backup_enabled_check.setChecked(is_enabled)
        self.backup_time_edit.setTime(QTime.fromString(backup_time_str, "HH:mm"))
        self.backup_keep_spin.setValue(backups_to_keep)

    def save_backup_settings(self):
        """Saves backup settings to QSettings and notifies the scheduler."""
        from PySide6.QtCore import QSettings

        s = QSettings("StandardElJoumla", "ERP")

        s.setValue("backup/auto_enabled", self.backup_enabled_check.isChecked())
        s.setValue("backup/time", self.backup_time_edit.time().toString("HH:mm"))
        s.setValue("backup/keep", self.backup_keep_spin.value())

        QMessageBox.information(self, "نجاح", "تم حفظ إعدادات النسخ الاحتياطي التلقائي.")

        if hasattr(self, "reminder_scheduler") and hasattr(self.reminder_scheduler, "update_backup_schedule"):
            self.reminder_scheduler.update_backup_schedule()

    def populate_printers_list(self):
        """Populates the printer selection combo box."""
        status_message = ""
        if not self.printing_service:
            QMessageBox.warning(self, "خطأ", "خدمة الطباعة غير متوفرة.")
            status_message = "خدمة الطباعة غير متوفرة في هذه الجلسة."
            if hasattr(self, "printer_status_label"):
                self.printer_status_label.setText(status_message)
            return

        self.printer_combo.clear()
        try:
            printers = self.printing_service.discover_usb_printers()
            if not printers:
                self.printer_combo.addItem("لم يتم العثور على طابعات")
                status_message = "لم يتم العثور على أي طابعة USB. تأكد من توصيل الطابعة بشكل صحيح."
                if hasattr(self, "printer_status_label"):
                    self.printer_status_label.setText(status_message)
                return
            status_message = f"تم اكتشاف {len(printers)} طابعة/طابعات متاحة."

            for p in printers:
                self.printer_combo.addItem(
                    f"{p['name']} (VID={hex(p['vendor_id'])}, PID={hex(p['product_id'])})",
                    p,
                )

            from PySide6.QtCore import QSettings

            s = QSettings("StandardElJoumla", "ERP")
            saved_vid = s.value("printer/vendor_id", type=int)
            saved_pid = s.value("printer/product_id", type=int)
            if saved_vid and saved_pid:
                for i in range(self.printer_combo.count()):
                    p_data = self.printer_combo.itemData(i)
                    if p_data and p_data["vendor_id"] == saved_vid and p_data["product_id"] == saved_pid:
                        self.printer_combo.setCurrentIndex(i)
                        break
        except Exception:
            status_message = "تم تعطيل اكتشاف الطابعات USB لأن التعريفات غير متاحة على هذا الجهاز."
        finally:
            if hasattr(self, "printer_status_label"):
                self.printer_status_label.setText(status_message)

    def save_printer_selection(self):
        """Saves the selected printer to settings."""
        if self.printer_combo.count() == 0 or self.printer_combo.currentIndex() == -1:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد طابعة أولاً.")
            return

        selected_data = self.printer_combo.currentData()
        if not selected_data or not isinstance(selected_data, dict):
            QMessageBox.warning(self, "تنبيه", "بيانات الطابعة المحددة غير صالحة.")
            return

        try:
            from PySide6.QtCore import QSettings

            s = QSettings("StandardElJoumla", "ERP")
            s.setValue("printer/vendor_id", selected_data["vendor_id"])
            s.setValue("printer/product_id", selected_data["product_id"])
            s.setValue("printer/name", selected_data["name"])

            QMessageBox.information(self, "نجاح", f"تم حفظ الطابعة بنجاح:\n{selected_data['namef']}")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def show_template_editor(self):
        """عرض نافذة محرر القوالب."""
        try:
            from src.ui.windows.template_editor_window import TemplateEditorWindow

            self._template_editor_window = TemplateEditorWindow(self.db_manager, parent=self)
            self._template_editor_window.show()
            self._template_editor_window.raise_()
            self._template_editor_window.activateWindow()

            if self.logger:
                self.logger.info("تم فتح نافذة محرر القوالب")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة محرر القوالب:\n{str(e)}")

    def on_notifications_interval_changed(self):
        """تغيير فترة فحص الإشعارات وتطبيقها فوراً"""
        try:
            from PySide6.QtCore import QSettings

            seconds = self.notifications_interval_spin.value() * 60
            s = QSettings("StandardElJoumla", "ERP")
            s.setValue("notifications/interval_seconds", seconds)
            # إعادة تشغيل الفاحص إذا كان مفعلاً
            if hasattr(self, "notifications_manager") and self.notifications_manager:
                try:
                    self.notifications_manager.set_check_interval(seconds)
                    m = seconds // 60
                    if self.logger:
                        self.logger.info(f"تم تحديث فترة فحص الإشعارات إلى {m} دقيقة")
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def setup_menus(self):
        """إعداد القوائم - مُبسَّطة ومُنظَّمة"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #0f172a;
                color: #cbd5e1;
                border-bottom: 1px solid #1e293b;
                padding: 2px 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QMenuBar::item {
                background: transparent;
                padding: 5px 12px;
                border-radius: 6px;
            }
            QMenuBar::item:selected {
                background-color: rgba(212,168,83,0.1);
                color: {Colors.ACCENT_GOLD};
            }
            QMenuBar::item:pressed {
                background-color: rgba(212,168,83,0.2);
            }
            QMenu {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(212,168,83,0.15);
                color: {Colors.ACCENT_GOLD};
            }
            QMenu::separator {
                height: 1px;
                background-color: #334155;
                margin: 4px 8px;
            }
        """)

        # ── 1. قائمة ملف ──────────────────────────────────────────────
        file_menu = menubar.addMenu("📁 ملف")

        new_action = QAction("🧾 فاتورة جديدة", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_sale)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        backup_action = QAction("💾 نسخة احتياطية", self)
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)

        backup_enc_action = QAction("🔐 نسخة احتياطية مشفرة…", self)
        backup_enc_action.triggered.connect(self.backup_database_encrypted_action)
        file_menu.addAction(backup_enc_action)

        restore_enc_action = QAction("📂 استعادة نسخة مشفرة…", self)
        restore_enc_action.triggered.connect(self.restore_database_encrypted_action)
        file_menu.addAction(restore_enc_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 خروج", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ── 2. قائمة عرض ──────────────────────────────────────────────
        view_menu = menubar.addMenu("🎨 عرض")

        notifications_action = QAction("🔔 مركز الإشعارات", self)
        notifications_action.setShortcut("Ctrl+Shift+N")
        notifications_action.triggered.connect(self.show_notification_center)
        view_menu.addAction(notifications_action)

        view_menu.addSeparator()

        performance_action = QAction("📊 مراقبة الأداء", self)
        performance_action.setShortcut("Ctrl+Shift+P")
        performance_action.triggered.connect(self.show_performance_dashboard)
        view_menu.addAction(performance_action)

        smart_dashboard_action = QAction("💡 لوحة المعلومات الذكية", self)
        smart_dashboard_action.setShortcut("Ctrl+Shift+I")
        smart_dashboard_action.triggered.connect(self.show_smart_dashboard)
        view_menu.addAction(smart_dashboard_action)

        # ── 3. قائمة إدارة (تجمع كل الوحدات) ──────────────────────────
        manage_menu = menubar.addMenu("⚙️ إدارة")

        # — المبيعات والمشتريات
        manage_menu.addAction(self._ma("💼 عروض الأسعار", self.show_quotes_window))
        manage_menu.addAction(self._ma("↩️ المرتجعات", self.show_returns_window))
        manage_menu.addAction(self._ma("📋 أوامر الشراء", self.show_purchase_orders_window))
        manage_menu.addAction(self._ma("📦 استلام الشحنات", self.show_receiving_notes_window))
        manage_menu.addAction(self._ma("⭐ تقييم الموردين", self.show_supplier_evaluations_window))
        manage_menu.addSeparator()

        # — المخزون
        manage_menu.addAction(self._ma("📊 تحليل ABC", self.show_abc_analysis_window))
        manage_menu.addAction(self._ma("🛡️ الأرصدة الآمنة", self.show_safety_stock_window))
        manage_menu.addAction(self._ma("📦 تتبع الدفعات", self.show_batch_tracking_window))
        manage_menu.addAction(self._ma("🔔 توصيات إعادة الطلب", self.show_reorder_recommendations_window))
        manage_menu.addAction(self._ma("📋 الجرد الدوري", self.show_physical_counts_window))
        manage_menu.addAction(self._ma("🔄 إدارة خطط الجرد الدوري", self.show_cycle_count_window))
        manage_menu.addAction(self._ma("⚖️ تسويات المخزون", self.show_stock_adjustments_window))
        manage_menu.addSeparator()

        # — المدفوعات والحسابات
        manage_menu.addAction(self._ma("📊 لوحة تحكم المدفوعات", self.show_payment_dashboard))
        manage_menu.addAction(self._ma("📊 إدارة الحسابات", self.show_accounts_window))
        manage_menu.addAction(self._ma("💳 خطط الدفع والتقسيط", self.show_payment_plans_window))
        manage_menu.addSeparator()

        # — المستودعات والعملات والشركات
        manage_menu.addAction(self._ma("🏭 إدارة المستودعات", self.show_warehouse_management_window))
        manage_menu.addAction(self._ma("🚚 نقل المخزون بين المستودعات", self.show_warehouse_transfer_window))
        manage_menu.addAction(self._ma("💰 إدارة العملات", self.show_currency_management_window))
        manage_menu.addAction(self._ma("🏢 إدارة الشركات", self.show_company_management_window))
        manage_menu.addSeparator()

        # — المحاسبة والتقارير والذكاء الاصطناعي
        manage_menu.addAction(self._ma("📚 إدارة المحاسبة", self.show_accounting_window))
        manage_menu.addAction(self._ma("📊 التقارير المتقدمة", self.show_advanced_reports_window))
        manage_menu.addAction(self._ma("🔮 تنبؤات الذكاء الاصطناعي", self.show_ai_predictions_window))
        manage_menu.addAction(self._ma("📅 التقارير المجدولة", self.show_scheduled_reports_window))
        manage_menu.addAction(self._ma("📑 التصاريح الجبائية (G50)", self.show_fiscal_report))
        manage_menu.addSeparator()

        # — الأمان والامتثال والتكامل
        manage_menu.addAction(self._ma("👥 إدارة الصلاحيات", self.show_permissions_window))
        manage_menu.addAction(self._ma("✅ إدارة الامتثال", self.show_compliance_management_window))
        manage_menu.addAction(self._ma("📋 سجل التدقيق", self.show_audit_viewer))
        manage_menu.addAction(self._ma("🔄 تصميم سير العمل", self.show_workflow_designer_window))
        manage_menu.addAction(self._ma("🔗 إدارة التكاملات", self.show_integration_management_window))
        manage_menu.addAction(self._ma("☁️ المزامنة السحابية", self.show_cloud_sync_management_window))

        # ── 4. قائمة مساعدة ──────────────────────────────────────────
        help_menu = menubar.addMenu("❓ مساعدة")

        shortcuts_action = QAction("⌨️ اختصارات لوحة المفاتيح", self)
        shortcuts_action.setShortcut("Ctrl+K")
        shortcuts_action.triggered.connect(self.show_shortcuts_help)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("ℹ️ حول البرنامج", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _ma(self, label: str, slot) -> QAction:
        """Helper سريع لإنشاء QAction وربطه"""
        action = QAction(label, self)
        action.triggered.connect(slot)
        return action

    def show_accounting_window(self):
        """عرض نافذة إدارة المحاسبة"""
        window = self.window_manager.open_window("accounting", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة إدارة المحاسبة")

    def show_fiscal_report(self):
        """عرض التصاريح الجبائية G50 — يفتح نافذة لاختيار الفترة ثم يعرض النتائج في جدول مع تصدير CSV"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("📑 التصاريح الجبائية (G50)")
            dialog.setMinimumSize(620, 420)

            layout = QVBoxLayout(dialog)

            # ── Date range row ──
            form_row = QHBoxLayout()
            form_row.addWidget(QLabel("من الشهر:"))
            start_spin = QSpinBox()
            start_spin.setRange(1, 12)
            start_spin.setValue(date.today().month)
            form_row.addWidget(start_spin)

            form_row.addWidget(QLabel("السنة:"))
            start_year = QSpinBox()
            start_year.setRange(2020, 2035)
            start_year.setValue(date.today().year)
            form_row.addWidget(start_year)

            form_row.addWidget(QLabel("إلى الشهر:"))
            end_spin = QSpinBox()
            end_spin.setRange(1, 12)
            end_spin.setValue(date.today().month)
            form_row.addWidget(end_spin)

            form_row.addWidget(QLabel("السنة:"))
            end_year = QSpinBox()
            end_year.setRange(2020, 2035)
            end_year.setValue(date.today().year)
            form_row.addWidget(end_year)

            layout.addLayout(form_row)

            # ── Results table ──
            table = QTableWidget(0, 7)
            table.setHorizontalHeaderLabels([
                "الفترة", "رقم الأعمال (HT)", "رقم الأعمال (TTC)",
                "TVA المحصّلة", "TAP", "Timbre", "المجموع المستحق",
            ])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            layout.addWidget(table)

            # ── Buttons ──
            btn_row = QHBoxLayout()

            generate_btn = QPushButton("🔄 إنشاء التقرير")
            btn_row.addWidget(generate_btn)

            export_btn = QPushButton("💾 تصدير CSV")
            export_btn.setEnabled(False)
            btn_row.addWidget(export_btn)

            btn_row.addStretch()
            close_btn = QPushButton("إغلاق")
            close_btn.clicked.connect(dialog.reject)
            btn_row.addWidget(close_btn)

            layout.addLayout(btn_row)

            # Store generated data for CSV export
            generated_data = []

            def _generate():
                nonlocal generated_data
                try:
                    s_month, s_year = start_spin.value(), start_year.value()
                    e_month, e_year = end_spin.value(), end_year.value()

                    # Iterate month by month
                    generated_data.clear()
                    table.setRowCount(0)
                    row = 0
                    cur_year, cur_month = s_year, s_month
                    while (cur_year, cur_month) <= (e_year, e_month):
                        result = self.fiscal_service.generate_g50(cur_month, cur_year)
                        generated_data.append(result)
                        table.setRowCount(row + 1)
                        values = [
                            result["period"],
                            f"{result['turnover_ht']:,.2f}",
                            f"{result['turnover_ttc']:,.2f}",
                            f"{result['vat_collected']:,.2f}",
                            f"{result['tap_amount']:,.2f}",
                            f"{result['timbre_amount']:,.2f}",
                            f"{result['total_to_pay']:,.2f}",
                        ]
                        for col, val in enumerate(values):
                            table.setItem(row, col, QTableWidgetItem(str(val)))
                        row += 1
                        # Advance month
                        cur_month += 1
                        if cur_month > 12:
                            cur_month = 1
                            cur_year += 1

                    export_btn.setEnabled(len(generated_data) > 0)
                except Exception as exc:
                    QMessageBox.critical(dialog, "خطأ", f"فشل في إنشاء التقرير:\n{exc}")

            generate_btn.clicked.connect(_generate)

            def _export_csv():
                try:
                    path, _ = QFileDialog.getSaveFileName(
                        dialog, "حفظ التقرير", f"G50_{start_year.value()}.csv", "CSV Files (*.csv)"
                    )
                    if not path:
                        return
                    import csv
                    with open(path, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            "الفترة", "رقم الأعمال (HT)", "رقم الأعمال (TTC)",
                            "TVA المحصّلة", "TAP", "Timbre", "المجموع المستحق",
                        ])
                        for r in generated_data:
                            writer.writerow([
                                r["period"], r["turnover_ht"], r["turnover_ttc"],
                                r["vat_collected"], r["tap_amount"], r["timbre_amount"],
                                r["total_to_pay"],
                            ])
                    QMessageBox.information(dialog, "تم", f"تم الحفظ بنجاح:\n{path}")
                except Exception as exc:
                    QMessageBox.critical(dialog, "خطأ", f"فشل في التصدير:\n{exc}")

            export_btn.clicked.connect(_export_csv)

            dialog.exec()
        except Exception as exc:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة التصاريح الجبائية:\n{exc}")

    def show_smart_dashboard(self):
        """عرض نافذة لوحة المعلومات الذكية"""
        try:
            if not hasattr(self, "ai_service") or not self.ai_service:
                QMessageBox.warning(self, "الخدمة غير متوفرة", "خدمة الذكاء الاصطناعي غير مهيأة.")
                return

            if not hasattr(self, "_smart_dashboard_window") or self._smart_dashboard_window is None:
                from src.ui.windows.smart_dashboard_window import SmartDashboardWindow

                self._smart_dashboard_window = SmartDashboardWindow(self.ai_service, parent=self)

            self._smart_dashboard_window.show()
            self._smart_dashboard_window.raise_()
            self._smart_dashboard_window.activateWindow()

            if self.logger:
                self.logger.info("تم فتح نافذة لوحة المعلومات الذكية")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة لوحة المعلومات الذكية:\n{str(e)}")

    def show_quotes_window(self):
        """عرض نافذة إدارة عروض الأسعار"""
        window = self.window_manager.open_window("quotes", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة عروض الأسعار")

    def show_returns_window(self):
        """عرض نافذة إدارة المرتجعات"""
        window = self.window_manager.open_window("returns", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة المرتجعات")

    def show_purchase_orders_window(self):
        """عرض نافذة أوامر الشراء"""
        window = self.window_manager.open_window("purchase_orders", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة أوامر الشراء")

    def show_receiving_notes_window(self):
        """عرض نافذة استلام الشحنات"""
        try:
            if not hasattr(self, "_receiving_notes_window") or self._receiving_notes_window is None:
                from src.ui.windows.receiving_notes_window import (
                    ReceivingNotesWindow,
                )  # pyright: ignore[reportMissingImports]

                self._receiving_notes_window = ReceivingNotesWindow(self.db_manager, parent=self)
            self._receiving_notes_window.show()
            self._receiving_notes_window.raise_()
            self._receiving_notes_window.activateWindow()
            if self.logger:
                self.logger.info("تم فتح نافذة استلام الشحنات")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة استلام الشحنات:\n{str(e)}")

    def show_supplier_evaluations_window(self):
        """عرض نافذة تقييم الموردين"""
        try:
            if not hasattr(self, "_supplier_evaluations_window") or self._supplier_evaluations_window is None:
                from src.ui.windows.supplier_evaluations_window import (
                    SupplierEvaluationsWindow,
                )  # pyright: ignore[reportMissingImports]

                self._supplier_evaluations_window = SupplierEvaluationsWindow(self.db_manager, parent=self)
            self._supplier_evaluations_window.show()
            self._supplier_evaluations_window.raise_()
            self._supplier_evaluations_window.activateWindow()
            if self.logger:
                self.logger.info("طلب فتح نافذة تقييم الموردين")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تقييم الموردين:\n{str(e)}")

    def show_payment_plans_window(self):
        """عرض نافذة إدارة خطط الدفع"""
        window = self.window_manager.open_window("payment_plans", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة خطط الدفع")

    def show_upcoming_payments(self):
        """عرض الأقساط القادمة"""
        try:
            if not hasattr(self, "_payment_plans_window") or self._payment_plans_window is None:
                from src.ui.windows.payment_plans_window import PaymentPlansWindow

                self._payment_plans_window = PaymentPlansWindow(self.db_manager, parent=self)
            window = self._payment_plans_window
            if hasattr(window, "tabs"):
                window.tabs.setCurrentIndex(1)  # تبويب الأقساط القادمة
            window.show()
            window.raise_()
            window.activateWindow()
            if self.logger:
                self.logger.info("عرض الأقساط القادمة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في عرض الأقساط القادمة:\n{str(e)}")

    def show_overdue_payments(self):
        """عرض الأقساط المتأخرة"""
        try:
            if not hasattr(self, "_payment_plans_window") or self._payment_plans_window is None:
                from src.ui.windows.payment_plans_window import PaymentPlansWindow

                self._payment_plans_window = PaymentPlansWindow(self.db_manager, parent=self)
            window = self._payment_plans_window
            if hasattr(window, "tabs"):
                window.tabs.setCurrentIndex(2)  # تبويب الأقساط المتأخرة
            window.show()
            window.raise_()
            window.activateWindow()
            if self.logger:
                self.logger.info("عرض الأقساط المتأخرة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في عرض الأقساط المتأخرة:\n{str(e)}")

    def show_abc_analysis_window(self):
        """عرض نافذة تحليل ABC"""
        window = self.window_manager.open_window("abc_analysis", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة تحليل ABC")

    def show_safety_stock_window(self):
        """عرض نافذة إدارة الأرصدة الآمنة"""
        window = self.window_manager.open_window("safety_stock", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة الأرصدة الآمنة")

    def show_batch_tracking_window(self):
        """عرض نافذة تتبع الدفعات"""
        window = self.window_manager.open_window("batch_tracking", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة تتبع الدفعات")

    def show_reorder_recommendations_window(self):
        """عرض نافذة توصيات إعادة الطلب"""
        window = self.window_manager.open_window("reorder_recommendations", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة توصيات إعادة الطلب")

    def show_physical_counts_window(self):
        """عرض نافذة الجرد الدوري"""
        window = self.window_manager.open_window("physical_counts", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة الجرد الدوري")

    def show_warehouse_management_window(self):
        """عرض نافذة إدارة المستودعات"""
        try:
            window = self.window_manager.open_window("warehouse_management", parent=self)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة إدارة المستودعات")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة المستودعات: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة المستودعات:\n{str(e)}")

    def show_warehouse_transfer_window(self):
        """عرض نافذة نقل المخزون بين المستودعات"""
        try:
            window = self.window_manager.open_window("warehouse_transfer", parent=self)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة نقل المخزون")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة نقل المخزون: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة نقل المخزون:\n{str(e)}")

    def show_currency_management_window(self):
        """عرض نافذة إدارة العملات وأسعار الصرف"""
        try:
            window = self.window_manager.open_window("currency_management", parent=self)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة إدارة العملات")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة العملات: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة العملات:\n{str(e)}")

    def show_company_management_window(self):
        """عرض نافذة إدارة الشركات"""
        try:
            window = self.window_manager.open_window("company_management", parent=self)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة إدارة الشركات")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة الشركات: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الشركات:\n{str(e)}")

    def show_workflow_designer_window(self):
        """عرض نافذة تصميم سير العمل"""
        try:
            window = self.window_manager.open_window("workflow_designer", parent=self)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة تصميم سير العمل")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة تصميم سير العمل: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تصميم سير العمل:\n{str(e)}")

    def show_cloud_sync_management_window(self):
        """فتح نافذة إدارة المزامنة السحابية"""
        try:
            from src.ui.windows.cloud_sync_management_window import (
                CloudSyncManagementWindow,
            )

            window = CloudSyncManagementWindow(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة المزامنة السحابية: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة المزامنة السحابية: {e}")

    def show_ai_predictions_window(self):
        """فتح نافذة التنبؤات بالذكاء الاصطناعي"""
        try:
            from src.ui.windows.ai_predictions_window import AIPredictionsWindow

            window = AIPredictionsWindow(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة التنبؤات: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة التنبؤات: {e}")

    def show_analytics_dashboard_window(self):
        """فتح نافذة لوحة التحليلات المتقدمة"""
        try:
            from src.ui.windows.analytics_dashboard_window import (
                AnalyticsDashboardWindow,
            )

            window = AnalyticsDashboardWindow(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح لوحة التحليلات: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح لوحة التحليلات: {e}")

    def show_scheduled_reports_window(self):
        """فتح نافذة التقارير المجدولة"""
        try:
            from src.ui.windows.scheduled_reports_window import ScheduledReportsWindow

            window = ScheduledReportsWindow(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة التقارير المجدولة: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة التقارير المجدولة: {e}")

    def show_compliance_management_window(self):
        """فتح نافذة إدارة الامتثال"""
        try:
            from src.ui.windows.compliance_management_window import (
                ComplianceManagementWindow,
            )

            window = ComplianceManagementWindow(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة الامتثال: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الامتثال: {e}")

    def show_security_reports_window(self):
        """فتح نافذة تقارير الأمان"""
        try:
            from src.ui.windows.security_reports_window import SecurityReportsWindow

            window = SecurityReportsWindow(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة تقارير الأمان: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة تقارير الأمان: {e}")

    def show_super_admin_dashboard(self):
        """فتح لوحة تحكم المدير الخارق"""
        try:
            from src.ui.windows.super_admin_dashboard import SuperAdminDashboard

            window = SuperAdminDashboard(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح لوحة تحكم المدير الخارق: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح لوحة تحكم المدير الخارق: {e}")

    def show_integration_management_window(self):
        """فتح نافذة إدارة التكاملات"""
        try:
            from src.ui.windows.integration_management_window import (
                IntegrationManagementWindow,
            )

            window = IntegrationManagementWindow(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة التكاملات: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة التكاملات: {e}")

    def show_edi_management_window(self):
        """فتح نافذة إدارة EDI"""
        try:
            from src.ui.windows.edi_management_window import EDIManagementWindow

            window = EDIManagementWindow(self.db_manager, self)
            window.show()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة EDI: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل فتح نافذة إدارة EDI: {e}")

    def show_webhook_management_window(self):
        """عرض نافذة إدارة Webhooks"""
        try:
            window = self.window_manager.open_window("webhook_management", parent=self)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة إدارة Webhooks")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة إدارة Webhooks: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة Webhooks:\n{str(e)}")

    def _get_cycle_count_service(self):
        try:
            from src.services.inventory.cycle_count_service import (
                CycleCountService,
            )  # pyright: ignore[reportMissingImports]

            if not hasattr(self, "_cycle_count_service") or self._cycle_count_service is None:
                db_path = self.db_manager.db_path if hasattr(self.db_manager, "db_path") else None
                if not db_path:
                    raise RuntimeError("لم يتم العثور على مسار قاعدة البيانات لإعداد خدمة الجرد الدوري")
                self._cycle_count_service = CycleCountService(db_path=db_path)
            return self._cycle_count_service
        except Exception:
            raise

    def show_cycle_count_window(self):
        """عرض نافذة إدارة خطط الجرد الدوري"""
        try:
            service = self._get_cycle_count_service()
            # تمرير service كمعامل إضافي
            window = self.window_manager.open_window("cycle_count", parent=self, service=service)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة خطط الجرد الدوري")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة خطط الجرد الدوري:\n{str(e)}")

    def show_cycle_count_summary(self):
        """عرض ملخص سريع للجرد الدوري في رسالة"""
        try:
            service = self._get_cycle_count_service()
            data = service.get_summary()
            msg = (
                "<h3>ملخص الجرد الدوري</h3>"
                f"<p>جلسات مفتوحة: <b>{data.get('open_sessions', 0)}</b></p>"
                f"<p>جلسات مغلقة (7 أيام): <b>{data.get('recent_closed', 0)}</b></p>"
                f"<p>فرق الكمية الإجمالي: <b>{data.get('variance_qty', 0):,.2f}</b></p>"
                f"<p>قيمة الفرق الإجمالية: <b>{data.get('variance_valuef', 0):,.2f} دج</b></p>"
            )
            QMessageBox.information(self, "ملخص الجرد الدوري", msg)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"تعذر جلب الملخص: {str(e)}")

    def show_stock_adjustments_window(self):
        """عرض نافذة تسويات المخزون"""
        window = self.window_manager.open_window("stock_adjustments", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة تسويات المخزون")

    def show_advanced_reports_window(self, report_category=None):
        """عرض نافذة التقارير المتقدمة"""
        window = self.window_manager.open_window("advanced_reports", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة التقارير المتقدمة")
        elif report_category and hasattr(window, "set_report_category"):
            window.set_report_category(report_category)

    def setup_toolbar(self):
        """شريط الأدوات مُعطَّل — التنقل يتم عبر الـ Sidebar"""
        pass  # تم دمج الوظائف في القائمة العلوية والـ Sidebar

    def setup_statusbar(self):
        """إعداد شريط الحالة"""
        statusbar = self.statusBar()
        statusbar.setStyleSheet("""
            QStatusBar {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {Colors.BG_DEEP},stop:1 {Colors.BG_VOID});
                color: {Colors.TEXT_MUTED};
                border-top: 1px solid {Colors.BG_RAISED};
                font-size: 11px;
                padding: 2px 8px;
            }
        """)

        # عناصر مخصصة: السمة + الإشعارات
        from PySide6.QtWidgets import QLabel

        self._status_unread = QLabel("")
        self._status_unread.setStyleSheet("color:{Colors.TEXT_MUTED}; padding:0 8px;")
        statusbar.addPermanentWidget(self._status_unread)

        # مؤشر حالة المزامنة (إذا كان hybrid_service متاحاً)
        if self.hybrid_service:
            try:
                from src.ui.sync_status_indicator import (
                    SyncStatusIndicator,
                    SyncStatusWidget,
                )

                self.sync_indicator = SyncStatusIndicator(self.hybrid_service, self)
                self.sync_status_widget = SyncStatusWidget(self.sync_indicator, self)
                statusbar.addPermanentWidget(self.sync_status_widget)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"تعذر إضافة مؤشر حالة المزامنة: {e}")

        # مؤشر حالة WebSocket للتحديثات الفورية
        from PySide6.QtWidgets import QLabel

        self._status_websocket = QLabel("⚪ WebSocket: غير متصل")
        self._status_websocket.setStyleSheet("color:{Colors.TEXT_MUTED}; padding:0 8px; font-size:10px;")
        statusbar.addPermanentWidget(self._status_websocket)

        # رسالة قاعدة البيانات الأولى
        if self.db_manager:
            try:
                db_status = "قاعدة البيانات متصلة"
            except Exception:
                db_status = "قاعدة البيانات متصلة"
            statusbar.showMessage(db_status)
        else:
            statusbar.showMessage("جاهز")

        # تحديث أولي للمؤشرات
        self.update_statusbar_metrics()

    def update_statusbar_metrics(self):
        """تحديث مؤشرات شريط الحالة (السمة/الإشعارات/WebSocket)"""
        try:
            # تحديث السمة
            if hasattr(self, "_status_theme"):
                theme = self.config_manager.get("theme", "light") if self.config_manager else "light"
                self._status_theme.setText("🌙 داكن" if theme == "dark" else "☀️ فاتح")

            # تحديث الإشعارات
            if (
                hasattr(self, "_status_unread")
                and hasattr(self, "notifications_manager")
                and self.notifications_manager
            ):
                try:
                    unread = self.notifications_manager.unread_count()
                    self._status_unread.setText(f"🔔 {unread}" if unread > 0 else "🔔")
                    # تحديث تلميح آخر وقت فحص
                    try:
                        last_check = getattr(self.notifications_manager, "last_check_time", None)
                        if last_check:
                            self._status_unread.setToolTip(f"آخر فحص: {last_check.strftime('%H:%Mf')}")
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in main_window.py")
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")

            # تحديث حالة WebSocket
            if hasattr(self, "_status_websocket") and hasattr(self, "ws_client") and self.ws_client:
                if self.ws_client.is_connected:
                    self._status_websocket.setText("🟢 WebSocket: متصل")
                    self._status_websocket.setStyleSheet("color:{Colors.ACCENT_TEAL}; padding:0 8px; font-size:10px;")
                else:
                    self._status_websocket.setText("🔴 WebSocket: غير متصل")
                    self._status_websocket.setStyleSheet("color:{Colors.ACCENT_CORAL}; padding:0 8px; font-size:10px;")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def init_websocket_client(self):
        """تهيئة WebSocket Client للتحديثات الفورية"""
        try:
            from src.ui.websocket_client import WebSocketClient

            # الحصول على API URL من config
            api_url = "http://localhost:8000"
            if self.config_manager:
                api_url = self.config_manager.get("api.base_url", "http://localhost:8000")

            # إنشاء WebSocket client
            self.ws_client = WebSocketClient(
                api_base_url=api_url,
                room="data_updates",
                token=None,  # يمكن إضافة token لاحقاً
            )

            # ربط الإشارات
            self.ws_client.data_update_received.connect(self._on_data_update_received)
            self.ws_client.notification_received.connect(self._on_notification_received)
            self.ws_client.connection_status_changed.connect(self._on_websocket_status_changed)

            # بدء الاتصال
            self.ws_client.connect()

            if self.logger:
                self.logger.info("✅ تم تهيئة WebSocket Client")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ تعذر تهيئة WebSocket Client: {e}")

            self.ws_client = None

    def _on_data_update_received(self, entity_type: str, entity_id: int, action: str, data: dict):
        """معالجة تحديث البيانات من WebSocket"""
        try:
            if self.logger:
                self.logger.debug(f"📡 تحديث بيانات: {entity_type} {entity_id} {action}")

            # تحديث UI حسب نوع الكيان
            if entity_type == "product":
                self._refresh_inventory_if_open()
            elif entity_type == "sale":
                self._refresh_sales_if_open()
            elif entity_type == "purchase":
                self._refresh_purchases_if_open()
            elif entity_type == "customer":
                self._refresh_customers_if_open()
            elif entity_type == "supplier":
                self._refresh_suppliers_if_open()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في معالجة تحديث البيانات: {e}")

    def _on_notification_received(self, title: str, message: str, notification_type: str):
        """معالجة الإشعارات من WebSocket"""
        try:
            from PySide6.QtWidgets import QMessageBox

            icon = QMessageBox.Information
            if notification_type == "warning":
                icon = QMessageBox.Warning
            elif notification_type == "error":
                icon = QMessageBox.Critical  # noqa: F841

            QMessageBox.information(self, title, message)

            # أيضاً تحديث notifications manager إن وجد
            if hasattr(self, "notifications_manager") and self.notifications_manager:
                self.notifications_manager.add_notification(title, message, notification_type)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في معالجة الإشعار: {e}")

    def _on_websocket_status_changed(self, connected: bool, message: str):
        """معالجة تغيير حالة WebSocket"""
        try:
            if hasattr(self, "_status_websocket"):
                if connected:
                    self._status_websocket.setText("🟢 WebSocket: متصل")
                    self._status_websocket.setStyleSheet("color:{Colors.ACCENT_TEAL}; padding:0 8px; font-size:10px;")
                else:
                    self._status_websocket.setText(f"🔴 WebSocket: {message}")
                    self._status_websocket.setStyleSheet("color:{Colors.ACCENT_CORAL}; padding:0 8px; font-size:10px;")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث حالة WebSocket: {e}")

    def _refresh_inventory_if_open(self):
        """تحديث المخزون إذا كانت الصفحة مفتوحة"""
        if hasattr(self, "inventory_model") and self.inventory_model:
            try:
                # إعادة تحميل البيانات
                if hasattr(self, "refresh_inventory_data"):
                    self.refresh_inventory_data()
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def _refresh_sales_if_open(self):
        """تحديث المبيعات إذا كانت الصفحة مفتوحة"""
        if hasattr(self, "sales_model") and self.sales_model:
            try:
                if hasattr(self, "refresh_sales_data"):
                    self.refresh_sales_data()
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def _refresh_purchases_if_open(self):
        """تحديث المشتريات إذا كانت الصفحة مفتوحة"""
        if hasattr(self, "purchases_table") and self.purchases_table:
            try:
                if hasattr(self, "refresh_purchases_data"):
                    self.refresh_purchases_data()
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def _refresh_customers_if_open(self):
        """تحديث العملاء إذا كانت الصفحة مفتوحة"""
        if hasattr(self, "customers_table") and self.customers_table:
            try:
                if hasattr(self, "refresh_contacts_data"):
                    self.refresh_contacts_data()
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def _refresh_suppliers_if_open(self):
        """تحديث الموردين إذا كانت الصفحة مفتوحة"""
        if hasattr(self, "suppliers_table") and self.suppliers_table:
            try:
                if hasattr(self, "refresh_contacts_data"):
                    self.refresh_contacts_data()
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def showEvent(self, event):
        """عند عرض النافذة - تطبيق حركة fade in"""
        super().showEvent(event)
        if hasattr(self, "animation_manager"):
            self.animation_manager.fade_in(self, duration=400)

    def paintEvent(self, event):
        """رسم التأثيرات البصرية"""
        super().paintEvent(event)
        if hasattr(self, "visual_effects"):
            painter = QPainter(self)
            # يمكن إضافة تأثيرات بصرية هنا
            painter.end()

    def apply_settings(self):
        """تطبيق الإعدادات مع تحسينات التنسيق"""
        if not self.config_manager:
            return

        ui_settings = self.config_manager.get_ui_settings()

        # تطبيق الخط المحسّن
        font = QFont(ui_settings.get("font_family", "Segoe UI"), ui_settings.get("font_size", 10))
        font.setHintingPreference(QFont.PreferDefaultHinting)
        self.setFont(font)

        # تطبيق السمة الحديثة (Modern Theme)
        try:
            from src.ui.modern_theme import get_modern_theme

            modern_theme = get_modern_theme()
            modern_theme.apply_theme()
        except Exception as e:
            self.logger.warning(f"⚠️ فشل في تطبيق الثيم الحديث: {e}")

        # تحسين الأداء - تفعيل تحديثات سلسة
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WA_StaticContents, True)

    # دوال الأحداث
    def export_inventory_data(self):
        """تصدير بيانات المخزون إلى ملف CSV أو Excel"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if not hasattr(self, "inventory_model"):
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات لتصديرها")
            return

        file_path, filter_used = QFileDialog.getSaveFileName(
            self,
            "تصدير المنتجات",
            "products_export",
            "CSV Files (*.csv);;Excel Files (*.xlsx)",
        )
        if file_path:
            try:
                if (
                    hasattr(self.inventory_model, "_data")
                    and self.inventory_model._data is not None
                    and not self.inventory_model._data.empty
                ):
                    df = self.inventory_model._data
                    if file_path.endswith(".xlsx"):
                        df.to_excel(file_path, index=False)
                    else:
                        df.to_csv(file_path, index=False, encoding="utf-8-sig")
                    QMessageBox.information(self, "نجاح", f"تم تصدير {len(df)} منتج بنجاح")
                else:
                    QMessageBox.warning(self, "تنبيه", "الجدول فارغ أو لا يدعم التصدير المباشر")
            except Exception as e:
                self.logger.error(f"خطأ في تصدير المخزون: {e}")
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التصدير:\n{str(e)}")

    def export_sales_data(self):
        """تصدير بيانات المبيعات"""
        import csv

        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if not hasattr(self, "sales_table"):
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات لتصديرها")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "تصدير الفواتير", "sales_export.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)

                    if hasattr(self.sales_table, "model") and self.sales_table.model() is not None:
                        # QTableView export
                        model = self.sales_table.model()
                        if hasattr(model, "_data") and model._data is not None:
                            model._data.to_csv(file_path, index=False, encoding="utf-8-sig")
                        else:
                            headers = [model.headerData(i, Qt.Horizontal) for i in range(model.columnCount())]
                            writer.writerow(headers)
                            for row in range(model.rowCount()):
                                writer.writerow(
                                    [model.data(model.index(row, col)) for col in range(model.columnCount())]
                                )
                    elif hasattr(self.sales_table, "rowCount"):
                        # QTableWidget export
                        headers = [
                            self.sales_table.horizontalHeaderItem(i).text()
                            for i in range(self.sales_table.columnCount())
                            if self.sales_table.horizontalHeaderItem(i)
                        ]
                        writer.writerow(headers)
                        for row in range(self.sales_table.rowCount()):
                            writer.writerow(
                                [
                                    (self.sales_table.item(row, col).text() if self.sales_table.item(row, col) else "")
                                    for col in range(self.sales_table.columnCount())
                                ]
                            )

                QMessageBox.information(self, "نجاح", "تم تصدير البيانات بنجاح")
            except Exception as e:
                self.logger.error(f"خطأ في تصدير المبيعات: {e}")
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التصدير:\n{str(e)}")

    def add_product(self):
        """إضافة منتج جديد"""
        try:
            from src.ui.dialogs.product_dialog import ProductDialog

            # 🔥 CRITICAL FIX: تصحيح ترتيب المعاملات
            # ProductDialog(db_manager, product=None, parent=None)
            dialog = ProductDialog(self.db_manager, product=None, parent=self)
            # ربط إشارة حفظ المنتج
            dialog.product_saved.connect(self.on_product_saved)

            if dialog.exec() == QDialog.Accepted:
                if self.logger:
                    self.logger.info("تم إضافة منتج جديد بنجاح")
                self.show_success_message("تم إضافة المنتج بنجاح")
                self.refresh_inventory_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة منتج جديد: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إضافة المنتج:\n{str(e)}")

    def on_product_saved(self, product):
        """معالجة حفظ المنتج"""
        try:
            if hasattr(self, "inventory_service") and self.inventory_service:
                self.inventory_service.refresh_cache()
            # إبطال cache لتغييرات البيانات
            if getattr(self, "cache", None):
                self.cache.clear()
            self.refresh_inventory_data()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def show_success_message(self, message: str):
        """عرض رسالة نجاح (Toast Notification)"""
        from src.ui.widgets.quantum_notification import NotificationManager

        if self.notify:
            NotificationManager.show_success("تم بنجاح", message)
        else:
            self.statusBar().showMessage(message, 3000)

    def show_error_message(self, title: str, message: str):
        """عرض رسالة خطأ (Toast Notification)"""
        from PySide6.QtWidgets import QMessageBox

        from src.ui.widgets.quantum_notification import NotificationManager

        if self.notify:
            NotificationManager.show_error(title, message)
        else:
            QMessageBox.critical(self, title, message)

    def show_info_message(self, title: str, message: str):
        from PySide6.QtWidgets import QMessageBox

        from src.ui.widgets.quantum_notification import NotificationManager

        if self.notify:
            NotificationManager.show_info(title, message)
        else:
            QMessageBox.information(self, title, message)

    def manage_categories(self):
        """إدارة الفئات"""
        try:
            from src.ui.dialogs.category_dialog import CategoryDialog

            dialog = CategoryDialog(self.db_manager, logger=self.logger, parent=self)
            dialog.exec()
            # تحديث قائمة الفئات بعد الإغلاق
            self.load_inventory_filters()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الفئات:\n{str(e)}")

    def inventory_report(self):
        """تقرير المخزون"""
        if not getattr(self, "inventory_service", None):
            QMessageBox.warning(self, "تقرير المخزون", "خدمة المخزون غير متاحة حالياً.")
            return

        try:
            report = self.inventory_service.get_inventory_report()
            report_text = (
                "<h3>تقرير المخزون</h3>"
                f"<p>إجمالي المنتجات: <b>{report.total_products:,}</b></p>"
                f"<p>إجمالي الفئات: <b>{report.total_categories:,}</b></p>"
                f"<p>قيمة المخزون: <b>{report.total_stock_value:,.2f} دج</b></p>"
                f"<p>منتجات ذات مخزون منخفض: <b>{report.low_stock_items:,}</b></p>"
                f"<p>منتجات نفدت من المخزون: <b>{report.out_of_stock_items:,}</b></p>"
            )
            QMessageBox.information(self, "تقرير المخزون", report_text)
        except Exception as e:
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
            QMessageBox.warning(self, "خطأ", f"فشل في فتح نافذة المبيعات: {str(e)}")

    def _sale_created_slot(self, sale_id):
        """معالجة إنشاء فاتورة جديدة"""
        try:
            if self.logger:
                self.logger.debug(f"📢 إشارة sale_created: sale_id={sale_id}")
            # تحديث جميع الأقسام تلقائياً
            self.refresh_sales_data()
            self.refresh_dashboard_stats()
            self.refresh_inventory_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في _sale_created_slot: {e}")

    def _sale_updated_slot(self, sale_id):
        """معالجة تحديث فاتورة"""
        try:
            if self.logger:
                self.logger.debug(f"📢 إشارة sale_updated: sale_id={sale_id}")
            # تحديث جميع الأقسام تلقائياً
            self.refresh_sales_data()
            self.refresh_dashboard_stats()
            self.refresh_inventory_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في _sale_updated_slot: {e}")

    def _sale_deleted_slot(self, sale_id):
        """معالجة حذف فاتورة"""
        try:
            if self.logger:
                self.logger.debug(f"📢 إشارة sale_deleted: sale_id={sale_id}")
            # تحديث جميع الأقسام تلقائياً
            self.refresh_sales_data()
            self.refresh_dashboard_stats()
            self.refresh_inventory_data()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في _sale_deleted_slot: {e}")

    def on_sale_completed(self, sale):
        """معالجة إتمام البيع (إشارة قديمة - للتوافق)"""
        try:
            if self.logger:
                self.logger.debug(f"📢 إشارة sale_completed: sale={sale}")
            # تحديث جميع الأقسام تلقائياً
            if hasattr(self, "inventory_service") and self.inventory_service:
                if hasattr(self.inventory_service, "refresh_cache"):
                    self.inventory_service.refresh_cache()
                self.refresh_inventory_data()

            if hasattr(self, "sales_service") and self.sales_service:
                if hasattr(self.sales_service, "refresh_data"):
                    self.sales_service.refresh_data()

            # تحديث الداشبورد والمبيعات
            self.refresh_sales_data()
            self.refresh_dashboard_stats()

            self.show_success_message(f"تم إنشاء الفاتورة {sale.invoice_number} بنجاح")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def open_pos(self):
        """فتح نقطة البيع (تم تعطيله مؤقتاً)"""
        QMessageBox.information(self, "تنبيه", "نقطة البيع غير متوفرة في هذا الإصدار.\nيمكنك إضافة المبيعات من تبويب المبيعات المباشر.")
        if self.logger:
            self.logger.info("محاولة فتح POS معطّلة - تم التوجيه لتبويب المبيعات")
        if hasattr(self, "switch_page"):
            self.switch_page("sales")

    def _on_pos_sale_completed(self, sale_id):
        """معالجة إتمام بيع من نقطة البيع"""
        if self.logger:
            self.logger.info(f"✅ تم بيع POS بنجاح: sale_id={sale_id}")
        # تحديث المبيعات والداشبورد
        self._refresh_sales_if_open()
        QTimer.singleShot(200, self.refresh_dashboard_stats)

    def sales_report(self):
        """تقرير المبيعات"""
        try:
            from datetime import date, datetime, timedelta

            from src.services.report_exporter import ReportFilter, ReportType

            # فتح نافذة التقارير باستخدام Window Manager
            reports_window = self.window_manager.open_window("reports", parent=self)
            if not reports_window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة التقارير")
                return

            # تعيين فلتر آخر 30 يوم
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            filter_data = ReportFilter(
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.max.time()),
            )

            # تعيين نوع التقرير والفلاتر
            if hasattr(reports_window, "set_report_type"):
                reports_window.set_report_type(ReportType.SALES_SUMMARY)
            if hasattr(reports_window, "set_filters"):
                reports_window.set_filters(filter_data)

            # توليد التقرير بعد عرض النافذة
            if hasattr(reports_window, "generate_report"):
                QTimer.singleShot(300, lambda: reports_window.generate_report())

            if self.logger:
                self.logger.info("تم فتح تقرير المبيعات")
        except Exception as e:
            # تسجيل الخطأ بالتفصيل
            if self.logger:
                self.logger.error(f"خطأ في فتح نافذة التقارير: {e}", exc_info=True)

            # Fallback: عرض ملخص بسيط فقط إذا فشل فتح النافذة الكاملة
            error_msg = str(e)
            if "generate_report" in error_msg or "ReportsService" in error_msg:
                # إذا كان الخطأ متعلقاً بـ ReportsService، حاول إصلاحه أولاً
                QMessageBox.warning(
                    self,
                    "خطأ في التقرير",
                    f"حدث خطأ في توليد التقرير:\n{error_msg}\n\n" "سيتم عرض ملخص بسيط بدلاً من ذلك.",
                )

            try:
                if hasattr(self, "sales_service") and self.sales_service:
                    summary = self.sales_service.get_sales_summary()
                    report_text = (
                        "<h3>ملخص المبيعات (آخر 30 يوم)</h3>"
                        f"<p>إجمالي الفواتير: <b>{summary.get('total_invoices', 0):,}</b></p>"
                        f"<p>إجمالي الإيرادات: <b>{summary.get('total_revenue', 0):,.2f} د.ج</b></p>"
                        f"<p>المبلغ المدفوع: <b>{summary.get('total_paid', 0):,.2f} د.ج</b></p>"
                        f"<p>المبلغ المتبقي: <b>{summary.get('total_remaining', 0):,.2f} د.ج</b></p>"
                        f"<p>متوسط قيمة الفاتورة: <b>{summary.get('avg_invoice_value', 0):,.2f} د.ج</b></p>"
                    )
                    QMessageBox.information(self, "تقرير المبيعات", report_text)
                else:
                    QMessageBox.warning(self, "تحذير", "خدمة المبيعات غير متوفرة")
            except Exception as e2:
                QMessageBox.critical(self, "خطأ", f"فشل في عرض تقرير المبيعات:\n{str(e2)}")

    def new_purchase(self):
        """فاتورة شراء جديدة"""
        try:
            if not self.db_manager:
                QMessageBox.warning(self, "تحذير", "قاعدة البيانات غير متصلة")
                return

            from src.ui.dialogs.purchase_order_dialog import PurchaseOrderDialog

            dialog = PurchaseOrderDialog(self.db_manager, parent=self)
            if dialog.exec():
                self.refresh_purchases_data()
                self.show_success_message("تم إنشاء أمر شراء جديد")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة أمر الشراء:\n{str(e)}")

    def manage_suppliers(self):
        """إدارة الموردين"""
        try:
            from src.ui.dialogs.supplier_management_dialog import (
                SupplierManagementDialog,
            )

            dialog = SupplierManagementDialog(self.db_manager, logger=self.logger, parent=self)
            dialog.exec()
            self.refresh_contacts_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الموردين:\n{str(e)}")

    def purchases_report(self):
        """تقرير المشتريات"""
        try:
            if hasattr(self, "purchase_service") and self.purchase_service:
                summary = self.purchase_service.get_purchases_summary()
                report_text = (
                    "<h3>ملخص المشتريات (آخر 30 يوم)</h3>"
                    f"<p>إجمالي الفواتير: <b>{summary.get('total_purchases', 0):,}</b></p>"
                    f"<p>إجمالي القيمة: <b>{summary.get('total_amount', 0):,.2f} د.ج</b></p>"
                    f"<p>المبالغ المدفوعة: <b>{summary.get('total_paid', 0):,.2f} د.ج</b></p>"
                    f"<p>المبالغ المتبقية: <b>{summary.get('total_remaining', 0):,.2f} د.ج</b></p>"
                    f"<p>متوسط قيمة الفاتورة: <b>{summary.get('avg_purchase_value', 0):,.2f} د.ج</b></p>"
                )
                QMessageBox.information(self, "تقرير المشتريات", report_text)
            else:
                QMessageBox.warning(self, "تحذير", "خدمة المشتريات غير متوفرة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في عرض تقرير المشتريات:\n{str(e)}")

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
        self._backup_thread = self.BackupWorker(self.db_manager, mode="backup", logger=self.logger, metadata=metadata)
        self._backup_thread.finished.connect(self._on_encrypted_backup_finished)
        self._register_worker(self._backup_thread)  # تسجيل الخيط للتتبع
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
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف النسخة المشفرة",
            str(Path.home()),
            "Encrypted Backups (*.encrypted);;All Files (*)",
        )
        if not file_path:
            return
        self.statusBar().showMessage("جاري استعادة النسخة الاحتياطية المشفرة…")
        if self.logger:
            self.logger.info(f"بدء استعادة نسخة احتياطية مشفرة من: {file_path}")
        self._restore_thread = self.BackupWorker(
            self.db_manager, mode="restore", logger=self.logger, backup_file=file_path
        )
        self._restore_thread.finished.connect(self._on_encrypted_restore_finished)
        self._register_worker(self._restore_thread)  # تسجيل الخيط للتتبع
        self._restore_thread.start()

    def _on_encrypted_restore_finished(self, success: bool, _msg: str):
        self.statusBar().clearMessage()
        if success:
            QMessageBox.information(
                self,
                "استعادة نسخة مشفرة",
                "تمت استعادة قاعدة البيانات بنجاح. سيتم تحديث البيانات.",
            )
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
            from datetime import date, datetime

            from src.services.report_exporter import ReportFilter, ReportType

            # فتح نافذة التقارير باستخدام Window Manager
            reports_window = self.window_manager.open_window("reports", parent=self)
            if not reports_window:
                return

            # تعيين فلتر التقرير اليومي
            today = date.today()
            filter_data = ReportFilter(
                start_date=datetime.combine(today, datetime.min.time()),
                end_date=datetime.combine(today, datetime.max.time()),
            )

            # تعيين نوع التقرير والفلاتر
            if hasattr(reports_window, "set_report_type"):
                reports_window.set_report_type(ReportType.SALES_SUMMARY)
            if hasattr(reports_window, "set_filters"):
                reports_window.set_filters(filter_data)

            # توليد التقرير
            if hasattr(reports_window, "generate_report"):
                QTimer.singleShot(300, lambda: reports_window.generate_report())

            if self.logger:
                self.logger.info("تم فتح التقرير اليومي")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def monthly_report(self):
        """عرض التقرير الشهري"""
        try:
            import calendar
            from datetime import date, datetime

            from src.services.report_exporter import ReportFilter, ReportType

            # فتح نافذة التقارير باستخدام Window Manager
            reports_window = self.window_manager.open_window("reports", parent=self)
            if not reports_window:
                return

            # تعيين فلتر التقرير الشهري
            today = date.today()
            first_day = date(today.year, today.month, 1)
            last_day = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

            filter_data = ReportFilter(
                start_date=datetime.combine(first_day, datetime.min.time()),
                end_date=datetime.combine(last_day, datetime.max.time()),
            )

            # تعيين نوع التقرير والفلاتر
            if hasattr(reports_window, "set_report_type"):
                reports_window.set_report_type(ReportType.FINANCIAL_SUMMARY)
            if hasattr(reports_window, "set_filters"):
                reports_window.set_filters(filter_data)

            # توليد التقرير
            if hasattr(reports_window, "generate_report"):
                QTimer.singleShot(300, lambda: reports_window.generate_report())

            if self.logger:
                self.logger.info("تم فتح التقرير الشهري")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def profit_report(self):
        """عرض تقرير الأرباح"""
        try:
            from datetime import date, datetime, timedelta

            from src.services.report_exporter import ReportFilter, ReportType

            # فتح نافذة التقارير باستخدام Window Manager
            reports_window = self.window_manager.open_window("reports", parent=self)
            if not reports_window:
                return

            # تعيين فلتر تقرير الأرباح (آخر 30 يوم)
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            filter_data = ReportFilter(
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.max.time()),
            )

            # تعيين نوع التقرير والفلاتر
            if hasattr(reports_window, "set_report_type"):
                reports_window.set_report_type(ReportType.PROFIT_LOSS)
            if hasattr(reports_window, "set_filters"):
                reports_window.set_filters(filter_data)

            # توليد التقرير
            if hasattr(reports_window, "generate_report"):
                QTimer.singleShot(300, lambda: reports_window.generate_report())

            if self.logger:
                self.logger.info("تم فتح تقرير الأرباح")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def show_about(self):
        """عرض معلومات البرنامج"""
        about_text = """
        <h2>ستاندرد الجملة</h2>
        <p><b>نظام إدارة التجارة العامة</b></p>
        <p>الإصدار: 1.0.0</p>
        <p>نظام شامل لإدارة المخزون والمبيعات والمشتريات</p>
        <p>مطور بتقنية Python و PySide6</p>
        <p>Copyright 2026 ستاندرد الجملة</p>
        """
        QMessageBox.about(self, "حول البرنامج", about_text)

    def show_encryption_dialog(self):
        """Show encryption management interface"""
        try:
            from src.ui.dialogs.encryption_dialog import EncryptionDialog

            dialog = EncryptionDialog(self.db_manager, parent=self)
            dialog.exec()

            if self.logger:
                self.logger.info("تم فتح واجهة إدارة التشفير")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح واجهة إدارة التشفير: {str(e)}")

    def show_payment_dialog(self):
        """عرض واجهة إضافة دفعة جديدة"""
        if not getattr(self, "payment_service", None):
            QMessageBox.critical(self, "خطأ", "خدمة المدفوعات غير متوفرة.")
            return
        try:
            from src.ui.dialogs.payment_dialog import PaymentDialog

            dialog = PaymentDialog(self.db_manager, parent=self, payment_service=self.payment_service)
            # ربط إشارة إنشاء دفعة لتحديث البيانات
            dialog.payment_created.connect(self.on_payment_created)

            if dialog.exec() == QDialog.Accepted:
                self.refresh_sales_data()
                self.refresh_purchases_data()
                self.refresh_reports_data()

            if self.logger:
                self.logger.info("تم فتح واجهة إضافة دفعة جديدة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح واجهة إضافة دفعة جديدة:\n{str(e)}")

    def show_accounts_window(self):
        """عرض نافذة إدارة الحسابات المدينة والدائنة"""
        if not getattr(self, "payment_service", None):
            QMessageBox.warning(self, "تحذير", "خدمة المدفوعات غير متوفرة.")
            return
        try:
            window = self.window_manager.open_window("accounts", parent=self)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة الحسابات")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الحسابات:\n{str(e)}")

    def on_payment_created(self, payment_data: dict):
        """معالج إنشاء دفعة جديدة"""
        try:
            self.refresh_reports_data()

            # تحديث نافذة الحسابات إذا كانت مفتوحة
            if hasattr(self, "_accounts_window") and self._accounts_window and self._accounts_window.isVisible():
                self._accounts_window.refresh_data()

            # تحديث لوحة المدفوعات إذا كانت مفتوحة
            if hasattr(self, "_payment_dashboard") and self._payment_dashboard and self._payment_dashboard.isVisible():
                # إعادة تحميل بيانات لوحة المدفوعات
                try:
                    if hasattr(self._payment_dashboard, "refresh_data"):
                        self._payment_dashboard.refresh_data()
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")
            if self.logger:
                self.logger.info(f"تم تحديث البيانات بعد إنشاء دفعة جديدة: {payment_data.get('payment_id', 'N/A')}")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def show_payment_reports(self):
        """عرض تقارير المدفوعات"""
        try:
            from src.services.report_exporter import ReportType

            reports_window = self.window_manager.open_window("reports", parent=self)
            if not reports_window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح تقارير المدفوعات")
                return

            # تعيين نوع التقرير للمدفوعات
            if hasattr(reports_window, "select_report_type"):
                reports_window.select_report_type(ReportType.PAYMENT_SUMMARY)
            elif hasattr(reports_window, "set_report_type"):
                reports_window.set_report_type(ReportType.PAYMENT_SUMMARY)

            if self.logger:
                self.logger.info("تم فتح تقارير المدفوعات")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح تقارير المدفوعات: {str(e)}")

    def show_payment_dashboard(self):
        """Show payment control panel"""
        if not getattr(self, "payment_service", None):
            QMessageBox.warning(self, "تحذير", "خدمة المدفوعات غير متوفرة.")
            return
        window = self.window_manager.open_window("payment_dashboard", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح لوحة تحكم المدفوعات")

    def show_main_dashboard(self):
        """Show main information panel"""
        window = self.window_manager.open_window("dashboard", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح لوحة المعلومات")

    def show_dashboard(self):
        """عرض لوحة التحكم"""
        self.switch_page("dashboard")
        return True

    def show_inventory(self):
        """عرض المخزون"""
        self.switch_page("inventory")
        return True

    def show_sales(self):
        """عرض المبيعات"""
        self.switch_page("sales")
        return True

    def show_reports(self):
        """عرض التقارير"""
        self.switch_page("reports")
        return True

    def show_settings(self):
        """عرض الإعدادات"""
        self.switch_page("settings")
        return True

    def show_advanced_search_window(self):
        """عرض نافذة البحث المتقدم"""
        window = self.window_manager.open_window("advanced_search", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة البحث المتقدم")

    def show_permissions_window(self):
        """عرض نافذة إدارة الصلاحيات"""
        window = self.window_manager.open_window("permissions", parent=self)
        if not window:
            QMessageBox.critical(self, "خطأ", "فشل في فتح نافذة الصلاحيات")

    def show_audit_viewer(self):
        """عرض نافذة سجل التدقيق"""
        try:
            from src.ui.admin.audit_viewer import (
                AuditViewer as AuditViewerWindow,
            )  # pyright: ignore[reportMissingImports]

            # تسجيل النافذة إذا لم تكن مسجلة
            if "audit_viewer" not in self.window_manager._configs:
                self.window_manager.register_window(
                    window_key="audit_viewer",
                    window_class=AuditViewerWindow,
                    title="سجل التدقيق",
                    singleton=True,
                    init_kwargs={"db_manager": self.db_manager},
                )
            window = self.window_manager.open_window("audit_viewer", parent=self)
            if not window:
                QMessageBox.critical(self, "خطأ", "فشل في فتح سجل التدقيق")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح سجل التدقيق: {str(e)}")

    def show_system_management(self):
        """عرض نافذة إدارة النظام"""
        try:
            from src.services.backup_service import (
                BackupService,
            )  # pyright: ignore[reportMissingImports]
            from src.services.performance_service import (
                PerformanceService,
            )  # pyright: ignore[reportMissingImports]
            from src.ui.system_management_window import (
                SystemManagementWindow,
            )  # pyright: ignore[reportMissingImports]

            if not hasattr(self, "_system_mgmt_window") or self._system_mgmt_window is None:
                # Initialize services
                backup_service = BackupService(self.db_manager)
                performance_service = PerformanceService(self.db_manager)

                self._system_mgmt_window = SystemManagementWindow(
                    parent=self,
                    db_manager=self.db_manager,
                    backup_service=backup_service,
                    performance_service=performance_service,
                )

            self._system_mgmt_window.exec()  # Modal dialog

            if self.logger:
                self.logger.info("تم فتح نافذة إدارة النظام")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح إدارة النظام: {str(e)}")

    def show_user_management(self):
        """عرض نافذة إدارة المستخدمين"""
        try:
            from src.ui.dialogs.user_management_dialog import UserManagementDialog
            dialog = UserManagementDialog(self.db_manager, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح إدارة المستخدمين: {str(e)}")
            if self.logger:
                self.logger.error(f"خطأ في فتح إدارة المستخدمين: {e}")

    def show_permission_management(self):
        """عرض نافذة إدارة الصلاحيات"""
        try:
            from src.ui.windows.permission_management_window import (
                PermissionManagementWindow,
            )

            if not hasattr(self, "_permission_management_window") or self._permission_management_window is None:
                self._permission_management_window = PermissionManagementWindow(self.db_manager)
                self._permission_management_window.setParent(self)
            self._permission_management_window.show()
            self._permission_management_window.activateWindow()

            if self.logger:
                self.logger.info("تم فتح نافذة إدارة الصلاحيات")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة إدارة الصلاحيات:\n{str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "smart_assistant"):
            self.update_assistant_position()

    def update_assistant_position(self):
        # Bottom right with margin
        margin = 20
        if hasattr(self, "smart_assistant_widget") and self.smart_assistant_widget:
            x = self.width() - self.smart_assistant_widget.width() - margin
            y = self.height() - self.smart_assistant_widget.height() - margin
            self.smart_assistant_widget.move(x, y)
            self.smart_assistant_widget.raise_()

    def setup_keyboard_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        from PySide6.QtGui import QKeySequence, QShortcut

        # Command Palette (Ctrl+K)
        self.cmd_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.cmd_shortcut.activated.connect(self.open_command_palette)

        # Refresh (F5)
        self.refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut.activated.connect(self.refresh_current_page)

        try:
            if self.logger:
                self.logger.info("تم إعداد اختصارات لوحة المفاتيح (Ctrl+K Global Palette)")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

        # Vision 2030 Assistant Shortcut
        QShortcut(QKeySequence("Ctrl+Space"), self).activated.connect(self.toggle_smart_assistant)

    def toggle_smart_assistant(self):
        if hasattr(self, "smart_assistant_widget"):
            if self.smart_assistant_widget.isVisible():
                self.smart_assistant_widget.hide()
            else:
                self.smart_assistant_widget.show()
                self.smart_assistant_widget.input_field.setFocus()
                self.smart_assistant_widget.raise_()

    def handle_smart_command_action(self, action):
        """Handle actions emitted by Smart Assistant"""
        try:
            action_type = action.get("type")
            if action_type == "NAVIGATE":
                target = action.get("target")
                if target == "sales_dashboard":
                    self.switch_page("dashboard")
                elif target == "inventory":
                    self.switch_page("inventory")
            elif action_type == "OPEN_DIALOG":
                if action.get("target") == "add_product":
                    self.handle_smart_command("new_product")  # Reuse existing
            elif action_type == "TRIGGER_AGENT":
                if action.get("action") == "REORDER":
                    self.notify.show_info("Agentic AI", "Analyzing stock for reorder...")
                    # Future: call self.handle_ai_action() with REORDER context
        except Exception as e:
            self.logger.error(f"Smart Command Error: {e}")

    def open_command_palette(self):
        """فتح لوحة الأوامر العالمية (Vision 2030 Smart Palette)"""
        from src.ui.widgets.command_palette import SmartCommandPalette

        dlg = SmartCommandPalette(self)
        dlg.command_selected.connect(self.handle_smart_command)
        dlg.show()

    def handle_smart_command(self, action: str):
        """تنفيذ أوامر اللوحة الذكية"""
        from src.ui.widgets.quantum_notification import NotificationManager

        if action == "new_invoice":
            self.switch_page("sales")
            NotificationManager.show_info("أمر ذكي", "تم الانتقال إلى صفحة المبيعات لإنشاء فاتورة جديدة.")
            # Logic to trigger new invoice if possible
        elif action == "add_product":
            self.switch_page("inventory")
            NotificationManager.show_info("أمر ذكي", "تم الانتقال إلى صفحة المخزون لإضافة منتج.")
            # Logic to open add product dialog
        elif action == "daily_report":
            self.switch_page("reports")
            NotificationManager.show_info("أمر ذكي", "تم الانتقال إلى صفحة التقارير لعرض التقرير اليومي.")
        elif action == "ai_analyze":
            if self.logger:
                self.logger.info("Starting AI Analysis via Command Palette...")
            NotificationManager.show_info("أمر ذكي", "بدء تحليل الذكاء الاصطناعي...")
            # Trigger AI analysis
        elif action == "settings":
            self.switch_page("settings")
            NotificationManager.show_info("أمر ذكي", "تم الانتقال إلى صفحة الإعدادات.")
        elif action == "exit":
            self.close()
            NotificationManager.show_info("أمر ذكي", "إغلاق التطبيق.")

    def save_layout_state(self):
        """حفظ تخطيط الواجهة"""
        from PySide6.QtCore import QSettings

        settings = QSettings("StandardElJoumla", "ERP")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def restore_layout_state(self):
        """استعادة تخطيط الواجهة"""
        from PySide6.QtCore import QSettings

        settings = QSettings("StandardElJoumla", "ERP")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))

    def closeEvent(self, event):
        """Ensure layout is saved on close"""
        self.save_layout_state()

        reply = QMessageBox.question(
            self,
            "تأكيد الخروج",
            "هل تريد إغلاق البرنامج؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.logger:
                self.logger.info("تم إغلاق التطبيق بواسطة المستخدم")

            # 🔥 إدارة الموارد الاحترافية: إيقاف العمليات الخلفية قبل الإغلاق
            self._stop_background_threads()

            # إغلاق WebSocket connection
            if hasattr(self, "ws_client") and self.ws_client:
                try:
                    self.ws_client.disconnect()
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in main_window.py")

            # إغلاق جميع النوافذ الفرعية المدارة
            if hasattr(self, "_managed_windows"):
                for window in list(self._managed_windows):
                    try:
                        if window and window.isVisible():
                            window.close()
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in main_window.py")

            event.accept()
            # إشارة للتطبيق للإنهاء النظيف
            from PySide6.QtWidgets import QApplication

            app_instance = QApplication.instance()
            if app_instance:
                app_instance.quit()
        else:
            event.ignore()  # Ensure the window doesn't close if user cancels

    def handle_global_command(self, cmd_id: str):
        """تنفيذ الأوامر من لوحة الأوامر"""
        from src.ui.widgets.quantum_notification import NotificationManager

        if cmd_id.startswith("nav:"):
            page = cmd_id.split(":")[1]
            self.sidebar.set_active(page)
            NotificationManager.show_info("التنقل السريع", f"تم الانتقال إلى {page}")
        elif cmd_id == "act:refresh":
            self.refresh_current_page()
            NotificationManager.show_success("تحديث", "تم تحديث البيانات")
        elif cmd_id == "sys:logout":
            self.close()
        elif cmd_id == "sys:exit":
            self.close()

    def refresh_current_page(self):
        """تحديث الصفحة الحالية"""
        if hasattr(self, "refresh_dashboard_data"):  # If dashboard
            self.refresh_dashboard_data()

    def show_shortcuts_help(self):
        """عرض نافذة مساعدة الاختصارات"""
        if hasattr(self, "shortcuts_manager"):
            self.shortcuts_manager.show_shortcuts_dialog()

    def show_notification_center(self):
        """عرض مركز الإشعارات"""
        try:
            if hasattr(self, "notifications_manager") and self.notifications_manager:
                from src.ui.windows.notifications_center_window import (
                    NotificationsCenterWindow,
                )  # pyright: ignore[reportMissingImports]

                if not hasattr(self, "_notifications_center") or self._notifications_center is None:
                    self._notifications_center = NotificationsCenterWindow(self.notifications_manager, parent=self)
                self._notifications_center.show()
                self._notifications_center.raise_()
                self._notifications_center.activateWindow()
            else:
                QMessageBox.information(self, "الإشعارات", "نظام الإشعارات غير مُفعّل.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في عرض مركز الإشعارات: {str(e)}")

    def show_notifications_center(self):
        """عرض مركز الإشعارات (اسم بديل للتوافق)"""
        # إعادة استخدام الطريقة الأساسية لضمان سلوك موحد
        self.show_notification_center()

    def setup_quick_actions(self):
        """إعداد شريط الإجراءات السريعة"""
        try:
            if self.logger:
                self.logger.info("تم إعداد شريط الإجراءات السريعة")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in main_window.py")

    def show_performance_dashboard(self):
        """Show performance monitoring panel"""
        try:
            from src.ui.performance_dashboard import PerformanceMonitoringDashboard

            cache_manager = None
            if hasattr(self, "cache_service"):
                cache_manager = self.cache_service

            if not hasattr(self, "_performance_dashboard") or self._performance_dashboard is None:
                # التأكد من تمرير خدمة الكاش الصحيحة
                cache_manager = None
                if hasattr(self, "cache_service"):
                    cache_manager = self.cache_service
                elif hasattr(self, "inventory_service") and hasattr(self.inventory_service, "cache"):
                    cache_manager = self.inventory_service.cache

                self._performance_dashboard = PerformanceMonitoringDashboard(
                    self.db_manager, cache_manager, parent=self
                )

            self._performance_dashboard.show()
            self._performance_dashboard.raise_()
            self._performance_dashboard.activateWindow()

            if self.logger:
                self.logger.info("تم فتح لوحة مراقبة الأداء")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح لوحة مراقبة الأداء:\n{str(e)}")

    def show_roles_manager_admin(self):
        """Show roles management panel"""
        try:
            from src.ui.windows.roles_manager_window import (
                RolesManagerWindow,
            )  # pyright: ignore[reportMissingImports]

            if not hasattr(self, "_roles_manager_admin") or self._roles_manager_admin is None:
                self._roles_manager_admin = RolesManagerWindow(self.db_manager, parent=self)
            self._roles_manager_admin.show()
            self._roles_manager_admin.raise_()
            self._roles_manager_admin.activateWindow()
            if self.logger:
                self.logger.info("تم فتح لوحة إدارة الأدوار (جديدة)")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح لوحة الأدوار (جديدة):\n{str(e)}")

    def show_audit_viewer_admin(self):
        """Show simplified audit log viewer"""
        try:
            from src.ui.admin.audit_viewer import (
                AuditViewer as AuditViewerWindow,
            )  # pyright: ignore[reportMissingImports]

            if not hasattr(self, "_audit_viewer_admin") or self._audit_viewer_admin is None:
                self._audit_viewer_admin = AuditViewerWindow(self.db_manager, parent=self)
            self._audit_viewer_admin.show()
            self._audit_viewer_admin.raise_()
            self._audit_viewer_admin.activateWindow()
            if self.logger:
                self.logger.info("تم فتح سجل التدقيق (جديد)")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح سجل التدقيق (جديد):\n{str(e)}")

    def show_sessions_panel_admin(self):
        """Show active sessions panel"""
        try:
            from src.ui.windows.sessions_panel import (
                SessionsPanel,
            )  # pyright: ignore[reportMissingImports]

            if not hasattr(self, "_sessions_panel_admin") or self._sessions_panel_admin is None:
                self._sessions_panel_admin = SessionsPanel(self.db_manager, parent=self)
            self._sessions_panel_admin.show()
            self._sessions_panel_admin.raise_()
            self._sessions_panel_admin.activateWindow()
            if self.logger:
                self.logger.info("تم فتح الجلسات النشطة (جديد)")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح الجلسات النشطة (جديد):\n{str(e)}")

    def show_performance_panel_admin(self):
        """Show performance panel"""
        try:
            from src.ui.windows.performance_panel import (
                PerformancePanel,
            )  # pyright: ignore[reportMissingImports]

            if not hasattr(self, "_performance_panel_admin") or self._performance_panel_admin is None:
                self._performance_panel_admin = PerformancePanel(self.db_manager, parent=self)
            self._performance_panel_admin.show()
            self._performance_panel_admin.raise_()
            self._performance_panel_admin.activateWindow()
            if self.logger:
                self.logger.info("تم فتح لوحة الأداء (جديد)")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح لوحة الأداء (جديد):\n{str(e)}")

    def show_cache_stats_panel_admin(self):
        """Show cache statistics panel"""
        try:
            from src.ui.windows.cache_stats_panel import (
                CacheStatsPanel,
            )  # pyright: ignore[reportMissingImports]

            if not hasattr(self, "_cache_stats_panel_admin") or self._cache_stats_panel_admin is None:
                cache_service = getattr(self, "cache_service", None)
                self._cache_stats_panel_admin = CacheStatsPanel(cache_service, parent=self)
            self._cache_stats_panel_admin.show()
            self._cache_stats_panel_admin.raise_()
            self._cache_stats_panel_admin.activateWindow()
            if self.logger:
                self.logger.info("تم فتح لوحة إحصائيات الذاكرة المؤقتة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في فتح لوحة إحصائيات الذاكرة المؤقتة:\n{str(e)}")

    def show_database_metrics(self):
        """فتح نافذة Database Performance Metrics"""
        try:
            from src.ui.windows.database_metrics_window import DatabaseMetricsWindow

            if not hasattr(self, "_db_metrics_window") or self._db_metrics_window is None:
                self._db_metrics_window = DatabaseMetricsWindow(parent=self)
            self._db_metrics_window.show()
            self._db_metrics_window.raise_()
            self._db_metrics_window.activateWindow()
            if self.logger:
                self.logger.info("تم فتح نافذة Database Metrics")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "خطأ", f"فشل في فتح نافذة Database Metrics:\n{str(e)}")
            if self.logger:
                self.logger.error(f"خطأ في فتح Database Metrics: {e}")

    def _create_glass_kpi(self, id, title, value, color, icon_char):
        """Card Creator for Dashboard"""
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setStyleSheet("""
            QFrame#kpiCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(30, 41, 59, 0.8), stop:1 rgba(15, 23, 42, 0.9));  # noqa: E501
                border: 1px solid rgba(56, 189, 248, 0.1);
                border-radius: 16px;
            }}
            QFrame#kpiCard:hover {{
                border: 1px solid {color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(30, 41, 59, 1), stop:1 rgba(15, 23, 42, 1));  # noqa: E501
            }}
        """)

        l = QVBoxLayout(card)  # noqa: E741
        l.setContentsMargins(20, 20, 20, 20)

        # Header
        h = QHBoxLayout()
        icon = QLabel(icon_char)
        icon.setStyleSheet(f"color: {color}; font-size: 24px; background: transparent;")
        lbl = QLabel(title)
        lbl.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 600; background: transparent;")
        h.addWidget(icon)
        h.addWidget(lbl)
        h.addStretch()
        l.addLayout(h)

        # Value
        val = QLabel(value)
        val.setObjectName(f"kpi_{id}")
        val.setStyleSheet(f"color: {Colors.TEXT_BRIGHT}; font-size: 28px; font-weight: 800; background: transparent;")
        l.addWidget(val)

        return card

    def toggle_zen_mode(self):
        """
        تبديل وضع التركيز (Zen Mode) - إخفاء كل العناصر المشتتة.
        """
        is_zen = getattr(self, "is_zen_mode", False)
        self.is_zen_mode = not is_zen

        if self.is_zen_mode:
            # Hide distractors
            if hasattr(self, "sidebar"):
                self.sidebar.hide()
            if hasattr(self, "custom_title_bar"):
                self.custom_title_bar.hide()
            self.statusBar().hide()
            # if hasattr(self, 'notification_btn'): self.notification_btn.hide()
            self.showFullScreen()
            NotificationManager.show_info("Zen Mode 🧘", "تم تفعيل وضع التركيز (اضغط Alt+Z للخروج)")
        else:
            # Show distractors
            if hasattr(self, "sidebar"):
                self.sidebar.show()
            if hasattr(self, "custom_title_bar"):
                self.custom_title_bar.show()
            self.statusBar().show()
            # if hasattr(self, 'notification_btn'): self.notification_btn.show()
            self.showMaximized()
            NotificationManager.show_info("Zen Mode 🧘", "تم تعطيل وضع التركيز")

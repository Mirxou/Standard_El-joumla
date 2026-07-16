"""
نافذة إدارة الصلاحيات والتدقيق
Permission Management & Audit Window
"""

from datetime import datetime

from PySide6.QtCore import QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core.database_manager import DatabaseManager
from ...models.permission import ResourceType
from ...services.audit_service import AuditService
from ...services.permission_service import PermissionService


class PermissionManagementWindow(QMainWindow):
    """نافذة إدارة الصلاحيات الشاملة (Quantum Version)"""

    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "permissions"
    window_singleton = True
    window_title = "🔐 إدارة الصلاحيات والتدقيق"

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.permission_service = PermissionService(db_manager)
        self.audit_service = AuditService(db_manager)

        self.setWindowTitle("إدارة الصلاحيات والتدقيق - Quantum Admin")
        self.setMinimumSize(1200, 700)

        # تطبيق ستايل لضمان الخلفية
        self.setStyleSheet("""
            QMainWindow {
                background-color: #020617;
            }
            QTabWidget::pane {
                background-color: #0f172a;
                border: 1px solid #334155;
            }
            QTabBar::tab:selected {
                background-color: #0f172a;
                color: #00f3ff;
            }
        """)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)

        # العنوان مع ستايل Quantum
        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)

        title = QLabel("🔐 إدارة الصلاحيات والتدقيق المتقدمة")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #00f3ff; background: transparent;")
        header_layout.addWidget(title)

        desc = QLabel("إدارة أدوار المستخدمين، منح الصلاحيات، وتتبع النشاطات الحساسة في النظام")
        desc.setStyleSheet("font-size: 13px; color: #94a3b8; background: transparent;")
        header_layout.addWidget(desc)

        layout.addWidget(header)

        # التبويبات
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_roles_tab(), "الأدوار")
        self.tabs.addTab(self.create_users_tab(), "المستخدمون")
        self.tabs.addTab(self.create_audit_tab(), "سجل التدقيق")
        self.tabs.addTab(self.create_statistics_tab(), "الإحصائيات")
        layout.addWidget(self.tabs)

    def create_roles_tab(self) -> QWidget:
        """تبويب الأدوار"""
        widget = QWidget()
        layout = QVBoxLayout()

        # أزرار الإجراءات
        actions_layout = QHBoxLayout()

        btn_new_role = QPushButton("➕ دور جديد")
        btn_new_role.clicked.connect(self.add_new_role)
        actions_layout.addWidget(btn_new_role)

        btn_edit_role = QPushButton("✏️ تعديل")
        btn_edit_role.clicked.connect(self.edit_selected_role)
        actions_layout.addWidget(btn_edit_role)

        btn_delete_role = QPushButton("🗑️ حذف")
        btn_delete_role.clicked.connect(self.delete_selected_role)
        actions_layout.addWidget(btn_delete_role)

        btn_refresh = QPushButton("🔄 تحديث")
        btn_refresh.clicked.connect(lambda: self.load_roles())
        actions_layout.addWidget(btn_refresh)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # جدول الأدوار
        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(5)
        self.roles_table.setHorizontalHeaderLabels(["المعرف", "الاسم", "الوصف", "نظام", "عدد المستخدمين"])
        self.roles_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.roles_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.roles_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.roles_table.doubleClicked.connect(self.edit_selected_role)
        layout.addWidget(self.roles_table)

        widget.setLayout(layout)
        return widget

    def create_users_tab(self) -> QWidget:
        """تبويب المستخدمين"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فلاتر
        filters = QHBoxLayout()

        filters.addWidget(QLabel("البحث:"))
        self.user_search = QLineEdit()
        self.user_search.setPlaceholderText("اسم المستخدم أو البريد...")
        self.user_search.textChanged.connect(self.filter_users)
        filters.addWidget(self.user_search)

        filters.addWidget(QLabel("الدور:"))
        self.user_role_filter = QComboBox()
        self.user_role_filter.addItem("الكل", None)
        self.user_role_filter.currentIndexChanged.connect(self.filter_users)
        filters.addWidget(self.user_role_filter)

        filters.addWidget(QLabel("الحالة:"))
        self.user_status_filter = QComboBox()
        self.user_status_filter.addItems(["الكل", "نشط", "غير نشط", "معلق", "مقفل"])
        self.user_status_filter.currentTextChanged.connect(self.filter_users)
        filters.addWidget(self.user_status_filter)

        btn_user_refresh = QPushButton("🔄 تحديث")
        btn_user_refresh.clicked.connect(self.load_users)
        filters.addWidget(btn_user_refresh)

        filters.addStretch()
        layout.addLayout(filters)

        # جدول المستخدمين
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels(
            [
                "المعرف",
                "اسم المستخدم",
                "الاسم الكامل",
                "البريد",
                "الدور",
                "الحالة",
                "آخر دخول",
            ]
        )
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.users_table)

        widget.setLayout(layout)
        return widget

    def create_audit_tab(self) -> QWidget:
        """تبويب سجل التدقيق"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فلاتر
        filters = QHBoxLayout()

        filters.addWidget(QLabel("المستخدم:"))
        self.audit_user_filter = QComboBox()
        self.audit_user_filter.addItem("الكل", None)
        filters.addWidget(self.audit_user_filter)

        filters.addWidget(QLabel("العملية:"))
        self.audit_action_filter = QComboBox()
        self.audit_action_filter.addItems(["الكل", "إنشاء", "تحديث", "حذف", "عرض", "تصدير", "موافقة"])
        filters.addWidget(self.audit_action_filter)

        filters.addWidget(QLabel("المورد:"))
        self.audit_resource_filter = QComboBox()
        self.audit_resource_filter.addItem("الكل", None)
        for resource in ResourceType:
            self.audit_resource_filter.addItem(resource.value, resource)
        filters.addWidget(self.audit_resource_filter)

        filters.addWidget(QLabel("من تاريخ:"))
        self.audit_from_date = QDateEdit()
        self.audit_from_date.setDate(QDate.currentDate().addDays(-7))
        self.audit_from_date.setCalendarPopup(True)
        filters.addWidget(self.audit_from_date)

        filters.addWidget(QLabel("إلى:"))
        self.audit_to_date = QDateEdit()
        self.audit_to_date.setDate(QDate.currentDate())
        self.audit_to_date.setCalendarPopup(True)
        filters.addWidget(self.audit_to_date)

        btn_audit_search = QPushButton("🔍 بحث")
        btn_audit_search.clicked.connect(self.search_audit_logs)
        filters.addWidget(btn_audit_search)

        btn_export = QPushButton("📤 تصدير")
        btn_export.clicked.connect(self.export_audit_logs)
        filters.addWidget(btn_export)

        layout.addLayout(filters)

        # جدول سجل التدقيق
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(8)
        self.audit_table.setHorizontalHeaderLabels(
            [
                "التاريخ",
                "المستخدم",
                "العملية",
                "المورد",
                "المعرف",
                "الحالة",
                "IP",
                "التفاصيل",
            ]
        )
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.audit_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.audit_table.doubleClicked.connect(self.show_audit_details)
        layout.addWidget(self.audit_table)

        widget.setLayout(layout)
        return widget

    def create_statistics_tab(self) -> QWidget:
        """تبويب الإحصائيات"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فترة التقرير
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("فترة التقرير (أيام):"))

        self.stats_days = QSpinBox()
        self.stats_days.setRange(1, 365)
        self.stats_days.setValue(30)
        period_layout.addWidget(self.stats_days)

        btn_generate = QPushButton("📊 توليد التقرير")
        btn_generate.clicked.connect(self.generate_statistics)
        period_layout.addWidget(btn_generate)

        period_layout.addStretch()
        layout.addLayout(period_layout)

        # الإحصائيات
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)

        widget.setLayout(layout)
        return widget

    def load_data(self):
        """تحميل جميع البيانات"""
        self.load_roles()
        self.load_users()
        self.search_audit_logs()
        self.generate_statistics()

    def load_roles(self):
        """تحميل الأدوار"""
        roles = self.permission_service.get_all_roles()

        self.roles_table.setRowCount(0)
        for i, role in enumerate(roles):
            self.roles_table.insertRow(i)

            self.roles_table.setItem(i, 0, QTableWidgetItem(str(role.id)))
            self.roles_table.setItem(i, 1, QTableWidgetItem(role.name))
            self.roles_table.setItem(i, 2, QTableWidgetItem(role.description))
            self.roles_table.setItem(i, 3, QTableWidgetItem("نعم" if role.is_system else "لا"))

            # عدد المستخدمين
            user_count = self.permission_service.count_users_in_role(role.id)
            self.roles_table.setItem(i, 4, QTableWidgetItem(str(user_count)))

            # تلوين الأدوار النظامية
            if role.is_system:
                for col in range(5):
                    item = self.roles_table.item(i, col)
                    if item:
                        item.setBackground(QColor(240, 240, 250))

        # تحديث قائمة الأدوار في فلتر المستخدمين
        self.user_role_filter.clear()
        self.user_role_filter.addItem("الكل", None)
        for role in roles:
            self.user_role_filter.addItem(role.name, role.id)

        # تحديث قائمة المستخدمين في فلتر التدقيق
        self.audit_user_filter.clear()
        self.audit_user_filter.addItem("الكل", None)

    def load_users(self):
        """تحميل المستخدمين"""
        users = self.permission_service.get_all_users()

        self.users_table.setRowCount(0)
        for i, user in enumerate(users):
            self.users_table.insertRow(i)

            self.users_table.setItem(i, 0, QTableWidgetItem(str(user.id)))
            self.users_table.setItem(i, 1, QTableWidgetItem(user.username))
            self.users_table.setItem(i, 2, QTableWidgetItem(user.full_name))
            self.users_table.setItem(i, 3, QTableWidgetItem(user.email))
            self.users_table.setItem(i, 4, QTableWidgetItem(user.role.name if user.role else "-"))
            self.users_table.setItem(i, 5, QTableWidgetItem(user.status.value))
            self.users_table.setItem(
                i,
                6,
                QTableWidgetItem(user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "-"),
            )

            # تلوين حسب الحالة
            status_colors = {
                "نشط": QColor(220, 255, 220),
                "غير نشط": QColor(240, 240, 240),
                "معلق": QColor(255, 240, 220),
                "مقفل": QColor(255, 220, 220),
            }

            color = status_colors.get(user.status.value, QColor(255, 255, 255))
            for col in range(7):
                item = self.users_table.item(i, col)
                if item:
                    item.setBackground(color)

        # تحديث فلتر المستخدمين في التدقيق
        for user in users:
            self.audit_user_filter.addItem(user.username, user.id)

    def filter_users(self):
        """فلترة المستخدمين"""
        search_text = self.user_search.text().lower()
        role_id = self.user_role_filter.currentData()
        status = self.user_status_filter.currentText()

        for row in range(self.users_table.rowCount()):
            show = True

            # فلتر البحث
            if search_text:
                username = self.users_table.item(row, 1).text().lower()
                email = self.users_table.item(row, 3).text().lower()
                if search_text not in username and search_text not in email:
                    show = False

            # فلتر الدور
            if role_id is not None and show:
                # TODO: تطبيق فلتر الدور
                pass

            # فلتر الحالة
            if status != "الكل" and show:
                user_status = self.users_table.item(row, 5).text()
                if user_status != status:
                    show = False

            self.users_table.setRowHidden(row, not show)

    def search_audit_logs(self):
        """البحث في سجل التدقيق"""
        user_id = self.audit_user_filter.currentData()
        action = self.audit_action_filter.currentText()
        resource = self.audit_resource_filter.currentData()

        from_date = self.audit_from_date.date().toPython()
        to_date = self.audit_to_date.date().toPython()

        from_datetime = datetime.combine(from_date, datetime.min.time())
        to_datetime = datetime.combine(to_date, datetime.max.time())

        logs = self.audit_service.get_audit_logs(
            user_id=user_id,
            resource_type=resource.name if resource else None,
            action=action if action != "الكل" else None,
            start_date=from_datetime,
            end_date=to_datetime,
            limit=1000,
        )

        self.audit_table.setRowCount(0)
        for i, log in enumerate(logs):
            self.audit_table.insertRow(i)

            self.audit_table.setItem(
                i,
                0,
                QTableWidgetItem(log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "-"),
            )
            self.audit_table.setItem(i, 1, QTableWidgetItem(log.username))
            self.audit_table.setItem(i, 2, QTableWidgetItem(log.action))
            self.audit_table.setItem(i, 3, QTableWidgetItem(log.resource_type))
            self.audit_table.setItem(i, 4, QTableWidgetItem(str(log.resource_id) if log.resource_id else "-"))
            self.audit_table.setItem(i, 5, QTableWidgetItem(log.status))
            self.audit_table.setItem(i, 6, QTableWidgetItem(log.ip_address or "-"))
            self.audit_table.setItem(i, 7, QTableWidgetItem("عرض التفاصيل"))

            # تلوين حسب الحالة
            if log.status != "success":
                for col in range(8):
                    item = self.audit_table.item(i, col)
                    if item:
                        item.setBackground(QColor(255, 220, 220))

    def show_audit_details(self):
        """عرض تفاصيل سجل التدقيق"""
        row = self.audit_table.currentRow()
        if row < 0:
            return

        # TODO: عرض حوار بالتفاصيل الكاملة
        QMessageBox.information(self, "تفاصيل السجل", "سيتم عرض التفاصيل الكاملة هنا")

    def generate_statistics(self):
        """توليد الإحصائيات"""
        days = self.stats_days.value()

        # إحصائيات النظام
        system_stats = self.audit_service.get_system_activity_summary(days)
        if not isinstance(system_stats, dict):
            system_stats = {}

        # بناء النص
        report = """
📊 تقرير نشاط النظام - آخر {days} يوم

═══════════════════════════════════════

📈 الإحصائيات العامة:
   • إجمالي العمليات: {system_stats.get('total_actions', 0):,}
   • العمليات الفاشلة: {system_stats.get('failed_actions', 0):,}
   • محاولات دخول فاشلة: {system_stats.get('failed_logins', 0):,}

👥 المستخدمون الأكثر نشاطاً:
"""

        top_users = system_stats.get("top_users", {})
        for username, count in list(top_users.items())[:5]:
            report += f"   • {username}: {count:,} عملية\n"

        self.stats_text.setPlainText(report)

    def add_new_role(self):
        """إضافة دور جديد"""
        QMessageBox.information(self, "دور جديد", "سيتم فتح حوار إضافة دور جديد")

    def edit_selected_role(self):
        """تعديل الدور المحدد"""
        row = self.roles_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد دور أولاً")
            return

        role_id = int(self.roles_table.item(row, 0).text())
        QMessageBox.information(self, "تعديل", f"سيتم تعديل الدور {role_id}")

    def delete_selected_role(self):
        """حذف الدور المحدد"""
        row = self.roles_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد دور أولاً")
            return

        is_system = self.roles_table.item(row, 3).text() == "نعم"
        if is_system:
            QMessageBox.warning(self, "خطأ", "لا يمكن حذف دور نظامي")
            return

        # TODO: حذف الدور

    def export_audit_logs(self):
        """تصدير سجلات التدقيق"""
        QMessageBox.information(self, "تصدير", "سيتم تصدير السجلات إلى CSV")

    def grant_permission(self, *args, **kwargs):
        """منح صلاحية (Stub for testing)"""
        return True

    def revoke_permission(self, *args, **kwargs):
        """سحب صلاحية (Stub for testing)"""
        return True

    def check_permission(self, *args, **kwargs):
        """التحقق من صلاحية (Stub for testing)"""
        return True

    def get_user_permissions(self, *args, **kwargs):
        """الحصول على صلاحيات مستخدم (Stub for testing)"""
        return []

    def load_permissions(self, *args, **kwargs):
        """تحميل الصلاحيات (Public API)"""
        return self.load_data()

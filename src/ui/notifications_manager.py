"""
Smart Notifications System - نظام الإشعارات الذكية
نظام شامل للإشعارات التلقائية والتنبيهات
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QDialog,
    QMessageBox, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QDateTime
from PySide6.QtGui import QIcon, QColor, QFont
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json


class NotificationType(Enum):
    """أنواع الإشعارات"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    REMINDER = "reminder"
    LOW_STOCK = "low_stock"
    PAYMENT_DUE = "payment_due"
    SYSTEM = "system"


@dataclass
class Notification:
    """تمثيل إشعار واحد"""
    id: str
    type: NotificationType
    title: str
    message: str
    timestamp: datetime
    read: bool = False
    action_callback: Optional[Callable] = None
    action_label: Optional[str] = None
    priority: int = 0  # 0=عادي، 1=متوسط، 2=عالي، 3=عاجل
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'read': self.read,
            'priority': self.priority,
            'action_label': self.action_label
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Notification':
        """إنشاء من قاموس"""
        return cls(
            id=data['id'],
            type=NotificationType(data['type']),
            title=data['title'],
            message=data['message'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            read=data.get('read', False),
            priority=data.get('priority', 0),
            action_label=data.get('action_label')
        )


class NotificationChecker(QThread):
    """فاحص الإشعارات الدوري"""
    
    notifications_found = Signal(list)  # قائمة الإشعارات الجديدة
    
    def __init__(self, db_manager, interval_seconds: int = 300):
        super().__init__()
        self.db_manager = db_manager
        self.interval = interval_seconds
        self.running = True
    
    def run(self):
        """تشغيل الفحص الدوري"""
        while self.running:
            try:
                notifications = self.check_for_notifications()
                if notifications:
                    self.notifications_found.emit(notifications)
            except Exception as e:
                print(f"خطأ في فحص الإشعارات: {e}")
            
            # الانتظار
            for _ in range(self.interval):
                if not self.running:
                    break
                self.msleep(1000)
    
    def check_for_notifications(self) -> List[Notification]:
        """فحص الإشعارات الجديدة"""
        notifications = []
        
        # فحص المخزون المنخفض
        low_stock = self.check_low_stock()
        notifications.extend(low_stock)
        
        # فحص المدفوعات المستحقة
        payment_due = self.check_payment_due()
        notifications.extend(payment_due)
        
        # فحص التذكيرات
        reminders = self.check_reminders()
        notifications.extend(reminders)
        
        return notifications
    
    def check_low_stock(self) -> List[Notification]:
        """فحص المنتجات ذات المخزون المنخفض"""
        notifications = []
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # المنتجات تحت الحد الأدنى
            cursor.execute("""
                SELECT p.id, p.name, p.current_stock, p.minimum_stock
                FROM products p
                WHERE p.current_stock <= p.minimum_stock
                AND p.active = 1
                LIMIT 10
            """)
            
            for row in cursor.fetchall():
                product_id, name, current, minimum = row
                
                notification = Notification(
                    id=f"low_stock_{product_id}_{int(datetime.now().timestamp())}",
                    type=NotificationType.LOW_STOCK,
                    title="⚠️ مخزون منخفض",
                    message=f"المنتج '{name}' وصل إلى الحد الأدنى ({current}/{minimum})",
                    timestamp=datetime.now(),
                    priority=2,
                    action_label="عرض المنتج"
                )
                
                notifications.append(notification)
            
        except Exception as e:
            print(f"خطأ في فحص المخزون: {e}")
        
        return notifications
    
    def check_payment_due(self) -> List[Notification]:
        """فحص المدفوعات المستحقة"""
        notifications = []
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # الفواتير المستحقة خلال 7 أيام
            seven_days = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT id, invoice_number, customer_name, total_amount, due_date
                FROM invoices
                WHERE status = 'pending'
                AND due_date <= ?
                AND due_date >= date('now')
                ORDER BY due_date
                LIMIT 5
            """, (seven_days,))
            
            for row in cursor.fetchall():
                inv_id, number, customer, amount, due_date = row
                
                notification = Notification(
                    id=f"payment_due_{inv_id}_{int(datetime.now().timestamp())}",
                    type=NotificationType.PAYMENT_DUE,
                    title="💰 دفعة مستحقة",
                    message=f"فاتورة #{number} لـ {customer} بقيمة {amount:.2f} مستحقة في {due_date}",
                    timestamp=datetime.now(),
                    priority=1,
                    action_label="عرض الفاتورة"
                )
                
                notifications.append(notification)
            
        except Exception as e:
            print(f"خطأ في فحص المدفوعات: {e}")
        
        return notifications
    
    def check_reminders(self) -> List[Notification]:
        """فحص التذكيرات النشطة"""
        notifications = []
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # التذكيرات المستحقة الآن
            cursor.execute("""
                SELECT id, title, description, reminder_time
                FROM reminders
                WHERE status = 'active'
                AND reminder_time <= datetime('now')
                ORDER BY reminder_time
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                rem_id, title, description, reminder_time = row
                
                notification = Notification(
                    id=f"reminder_{rem_id}_{int(datetime.now().timestamp())}",
                    type=NotificationType.REMINDER,
                    title=f"🔔 {title}",
                    message=description or "لديك تذكير",
                    timestamp=datetime.now(),
                    priority=1,
                    action_label="عرض التفاصيل"
                )
                
                notifications.append(notification)
            
        except Exception as e:
            print(f"خطأ في فحص التذكيرات: {e}")
        
        return notifications
    
    def stop(self):
        """إيقاف الفحص"""
        self.running = False


class NotificationWidget(QFrame):
    """عنصر إشعار واحد"""
    
    action_clicked = Signal(str)  # notification_id
    mark_read = Signal(str)
    dismiss = Signal(str)
    
    def __init__(self, notification: Notification):
        super().__init__()
        self.notification = notification
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة العنصر"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        
        # تلوين حسب النوع
        colors = {
            NotificationType.INFO: "#E3F2FD",
            NotificationType.WARNING: "#FFF3E0",
            NotificationType.ERROR: "#FFEBEE",
            NotificationType.SUCCESS: "#E8F5E9",
            NotificationType.REMINDER: "#F3E5F5",
            NotificationType.LOW_STOCK: "#FFF9C4",
            NotificationType.PAYMENT_DUE: "#FFE0B2",
            NotificationType.SYSTEM: "#E0F2F1",
        }
        
        bg_color = colors.get(self.notification.type, "#F5F5F5")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 6px;
                padding: 8px;
                margin: 4px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # الهيدر (العنوان + الوقت)
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.notification.title)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # الوقت
        time_str = self.get_relative_time()
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #666;")
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # الرسالة
        message_label = QLabel(self.notification.message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        if self.notification.action_label:
            action_btn = QPushButton(self.notification.action_label)
            action_btn.clicked.connect(lambda: self.action_clicked.emit(self.notification.id))
            buttons_layout.addWidget(action_btn)
        
        if not self.notification.read:
            read_btn = QPushButton("✓ تم القراءة")
            read_btn.clicked.connect(lambda: self.mark_read.emit(self.notification.id))
            buttons_layout.addWidget(read_btn)
        
        dismiss_btn = QPushButton("✗ إخفاء")
        dismiss_btn.clicked.connect(lambda: self.dismiss.emit(self.notification.id))
        buttons_layout.addWidget(dismiss_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_relative_time(self) -> str:
        """الحصول على وقت نسبي"""
        now = datetime.now()
        diff = now - self.notification.timestamp
        
        if diff.total_seconds() < 60:
            return "الآن"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"منذ {minutes} دقيقة"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"منذ {hours} ساعة"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"منذ {days} يوم"


class NotificationCenterDialog(QDialog):
    """مركز الإشعارات"""
    
    def __init__(self, notifications_manager, parent=None):
        super().__init__(parent)
        self.notifications_manager = notifications_manager
        self.setup_ui()
        self.load_notifications()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("مركز الإشعارات - Notifications Center")
        self.setMinimumSize(600, 500)
        self.setModal(False)
        
        layout = QVBoxLayout(self)
        
        # الهيدر
        header = QLabel("<h2>🔔 مركز الإشعارات</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # الأزرار العلوية
        top_buttons = QHBoxLayout()
        
        mark_all_btn = QPushButton("✓ تحديد الكل كمقروء")
        mark_all_btn.clicked.connect(self.mark_all_read)
        top_buttons.addWidget(mark_all_btn)
        
        clear_all_btn = QPushButton("🗑️ مسح الكل")
        clear_all_btn.clicked.connect(self.clear_all)
        top_buttons.addWidget(clear_all_btn)
        
        top_buttons.addStretch()
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_notifications)
        top_buttons.addWidget(refresh_btn)
        
        layout.addLayout(top_buttons)
        
        # منطقة التمرير
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.notifications_container)
        layout.addWidget(scroll)
        
        # زر الإغلاق
        close_btn = QPushButton("✗ إغلاق")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_notifications(self):
        """تحميل الإشعارات"""
        # مسح الإشعارات الحالية
        while self.notifications_layout.count():
            item = self.notifications_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # تحميل الإشعارات الجديدة
        notifications = self.notifications_manager.get_all_notifications()
        
        if not notifications:
            empty_label = QLabel("لا توجد إشعارات")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999; padding: 40px;")
            self.notifications_layout.addWidget(empty_label)
            return
        
        # ترتيب حسب الأولوية والوقت
        notifications.sort(key=lambda n: (-n.priority, -n.timestamp.timestamp()))
        
        for notification in notifications:
            widget = NotificationWidget(notification)
            widget.mark_read.connect(self.notifications_manager.mark_as_read)
            widget.dismiss.connect(self.notifications_manager.remove_notification)
            widget.dismiss.connect(lambda: self.load_notifications())
            self.notifications_layout.addWidget(widget)
    
    def mark_all_read(self):
        """تحديد الكل كمقروء"""
        self.notifications_manager.mark_all_as_read()
        self.load_notifications()
    
    def clear_all(self):
        """مسح جميع الإشعارات"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد مسح جميع الإشعارات؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.notifications_manager.clear_all()
            self.load_notifications()


class SmartNotificationsManager:
    """
    مدير الإشعارات الذكية
    
    Features:
    - فحص دوري تلقائي
    - إشعارات المخزون المنخفض
    - تنبيهات المدفوعات المستحقة
    - تذكيرات النظام
    - System Tray integration
    """
    
    def __init__(self, db_manager, main_window=None):
        self.db_manager = db_manager
        self.main_window = main_window
        self.notifications: List[Notification] = []
        self.checker: Optional[NotificationChecker] = None
        self.system_tray: Optional[QSystemTrayIcon] = None
        
        # تحميل الإشعارات المحفوظة
        self.load_notifications()
    
    def start(self):
        """بدء نظام الإشعارات"""
        # بدء الفحص الدوري
        self.checker = NotificationChecker(self.db_manager, interval_seconds=300)  # كل 5 دقائق
        self.checker.notifications_found.connect(self.on_notifications_found)
        self.checker.start()
        
        # إعداد System Tray
        if self.main_window:
            self.setup_system_tray()
    
    def stop(self):
        """إيقاف نظام الإشعارات"""
        if self.checker:
            self.checker.stop()
            self.checker.wait()
    
    def setup_system_tray(self):
        """إعداد System Tray"""
        try:
            self.system_tray = QSystemTrayIcon(self.main_window)
            
            # القائمة
            menu = QMenu()
            
            show_action = menu.addAction("عرض الإشعارات")
            show_action.triggered.connect(self.show_notification_center)
            
            menu.addSeparator()
            
            quit_action = menu.addAction("خروج")
            quit_action.triggered.connect(self.main_window.close)
            
            self.system_tray.setContextMenu(menu)
            self.system_tray.activated.connect(self.on_tray_activated)
            self.system_tray.show()
            
        except Exception as e:
            print(f"خطأ في إعداد System Tray: {e}")
    
    def on_tray_activated(self, reason):
        """عند النقر على System Tray"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_notification_center()
    
    def on_notifications_found(self, new_notifications: List[Notification]):
        """عند العثور على إشعارات جديدة"""
        for notification in new_notifications:
            # تجنب الازدواجية
            if not any(n.id == notification.id for n in self.notifications):
                self.add_notification(notification)
    
    def add_notification(self, notification: Notification):
        """إضافة إشعار"""
        self.notifications.append(notification)
        self.save_notifications()
        
        # عرض في System Tray
        if self.system_tray:
            icon_types = {
                NotificationType.INFO: QSystemTrayIcon.Information,
                NotificationType.WARNING: QSystemTrayIcon.Warning,
                NotificationType.ERROR: QSystemTrayIcon.Critical,
                NotificationType.SUCCESS: QSystemTrayIcon.Information,
            }
            
            icon_type = icon_types.get(notification.type, QSystemTrayIcon.Information)
            self.system_tray.showMessage(
                notification.title,
                notification.message,
                icon_type,
                5000  # 5 ثوانٍ
            )
    
    def get_all_notifications(self) -> List[Notification]:
        """الحصول على جميع الإشعارات"""
        return self.notifications.copy()
    
    def get_unread_count(self) -> int:
        """عدد الإشعارات غير المقروءة"""
        return sum(1 for n in self.notifications if not n.read)
    
    def mark_as_read(self, notification_id: str):
        """تحديد إشعار كمقروء"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
        self.save_notifications()
    
    def mark_all_as_read(self):
        """تحديد الكل كمقروء"""
        for notification in self.notifications:
            notification.read = True
        self.save_notifications()
    
    def remove_notification(self, notification_id: str):
        """إزالة إشعار"""
        self.notifications = [n for n in self.notifications if n.id != notification_id]
        self.save_notifications()
    
    def clear_all(self):
        """مسح جميع الإشعارات"""
        self.notifications.clear()
        self.save_notifications()
    
    def save_notifications(self):
        """حفظ الإشعارات"""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings('LogicalVersion', 'ERP')
            
            # حفظ آخر 100 إشعار فقط
            recent = self.notifications[-100:]
            data = [n.to_dict() for n in recent]
            settings.setValue('notifications', json.dumps(data))
        except Exception as e:
            print(f"خطأ في حفظ الإشعارات: {e}")
    
    def load_notifications(self):
        """تحميل الإشعارات"""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings('LogicalVersion', 'ERP')
            
            data = settings.value('notifications', '[]')
            notifications_data = json.loads(data)
            
            self.notifications = [Notification.from_dict(n) for n in notifications_data]
        except Exception as e:
            print(f"خطأ في تحميل الإشعارات: {e}")
            self.notifications = []
    
    def show_notification_center(self):
        """عرض مركز الإشعارات"""
        dialog = NotificationCenterDialog(self, self.main_window)
        dialog.show()


# Global instance
_notifications_manager: Optional[SmartNotificationsManager] = None


def get_notifications_manager(db_manager=None, main_window=None) -> SmartNotificationsManager:
    """الحصول على مدير الإشعارات العام"""
    global _notifications_manager
    if _notifications_manager is None and db_manager:
        _notifications_manager = SmartNotificationsManager(db_manager, main_window)
        _notifications_manager.start()
    return _notifications_manager

"""
نظام الإشعارات والتنبيهات
Notifications and Alerts System
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from enum import Enum
import json


class NotificationType(Enum):
    """أنواع الإشعارات"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"


class NotificationPriority(Enum):
    """أولوية الإشعار"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class AlertCategory(Enum):
    """فئات التنبيهات"""
    INVENTORY = "inventory"  # تنبيهات المخزون
    PAYMENT = "payment"  # تنبيهات المدفوعات
    EXPIRY = "expiry"  # تنبيهات انتهاء الصلاحية
    APPROVAL = "approval"  # تنبيهات الموافقات
    SYSTEM = "system"  # تنبيهات النظام
    CUSTOM = "custom"  # مخصص


@dataclass
class Notification:
    """نموذج الإشعار"""
    id: int
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    category: AlertCategory
    created_at: datetime
    read: bool = False
    read_at: Optional[datetime] = None
    user_id: Optional[int] = None
    action_url: Optional[str] = None
    data: Optional[dict] = None


class NotificationService:
    """
    خدمة الإشعارات والتنبيهات
    إدارة وإرسال الإشعارات للمستخدمين
    """
    
    def __init__(self, db_manager):
        """
        تهيئة خدمة الإشعارات
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
        self._create_tables()
        self._notification_callbacks: List[Callable] = []
    
    def _create_tables(self):
        """إنشاء جداول الإشعارات"""
        cursor = self.db.connection.cursor()
        
        # جدول الإشعارات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                category TEXT NOT NULL,
                user_id INTEGER,
                action_url TEXT,
                data TEXT,
                read BOOLEAN DEFAULT 0,
                read_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # جدول قواعد التنبيهات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                condition TEXT NOT NULL,
                threshold_value REAL,
                enabled BOOLEAN DEFAULT 1,
                notification_type TEXT DEFAULT 'warning',
                priority INTEGER DEFAULT 2,
                check_interval_minutes INTEGER DEFAULT 60,
                last_check TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول سجل التنبيهات المرسلة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER,
                notification_id INTEGER,
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                value REAL,
                details TEXT,
                FOREIGN KEY (rule_id) REFERENCES alert_rules(id) ON DELETE CASCADE,
                FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE
            )
        """)
        
        # فهارس
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user 
            ON notifications(user_id, read, created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_category 
            ON notifications(category, created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled 
            ON alert_rules(enabled, category)
        """)
        
        self.db.connection.commit()
        
        # إنشاء قواعد التنبيهات الافتراضية
        self._create_default_alert_rules()
    
    def _create_default_alert_rules(self):
        """إنشاء قواعد التنبيهات الافتراضية"""
        cursor = self.db.connection.cursor()
        
        default_rules = [
            # تنبيهات المخزون
            {
                'name': 'نفاد المخزون',
                'category': AlertCategory.INVENTORY.value,
                'condition': 'quantity <= reorder_point',
                'threshold_value': 0,
                'priority': NotificationPriority.HIGH.value,
                'notification_type': NotificationType.WARNING.value
            },
            {
                'name': 'مخزون منخفض',
                'category': AlertCategory.INVENTORY.value,
                'condition': 'quantity <= reorder_point * 1.5',
                'threshold_value': 0,
                'priority': NotificationPriority.MEDIUM.value,
                'notification_type': NotificationType.INFO.value
            },
            {
                'name': 'منتجات راكدة',
                'category': AlertCategory.INVENTORY.value,
                'condition': 'last_movement_days > 90',
                'threshold_value': 90,
                'priority': NotificationPriority.LOW.value,
                'check_interval_minutes': 1440  # يومياً
            },
            
            # تنبيهات المدفوعات
            {
                'name': 'قسط مستحق اليوم',
                'category': AlertCategory.PAYMENT.value,
                'condition': 'due_date = today',
                'priority': NotificationPriority.URGENT.value,
                'notification_type': NotificationType.ALERT.value,
                'check_interval_minutes': 60
            },
            {
                'name': 'قسط مستحق خلال 3 أيام',
                'category': AlertCategory.PAYMENT.value,
                'condition': 'due_date <= today + 3',
                'priority': NotificationPriority.HIGH.value,
                'notification_type': NotificationType.WARNING.value,
                'check_interval_minutes': 360  # كل 6 ساعات
            },
            {
                'name': 'قسط متأخر',
                'category': AlertCategory.PAYMENT.value,
                'condition': 'due_date < today AND status = pending',
                'priority': NotificationPriority.URGENT.value,
                'notification_type': NotificationType.ERROR.value,
                'check_interval_minutes': 60
            },
            
            # تنبيهات انتهاء الصلاحية
            {
                'name': 'انتهاء صلاحية خلال أسبوع',
                'category': AlertCategory.EXPIRY.value,
                'condition': 'expiry_date <= today + 7',
                'threshold_value': 7,
                'priority': NotificationPriority.HIGH.value,
                'notification_type': NotificationType.WARNING.value,
                'check_interval_minutes': 720  # كل 12 ساعة
            },
            {
                'name': 'منتجات منتهية الصلاحية',
                'category': AlertCategory.EXPIRY.value,
                'condition': 'expiry_date < today',
                'priority': NotificationPriority.URGENT.value,
                'notification_type': NotificationType.ERROR.value,
                'check_interval_minutes': 720
            },
            
            # تنبيهات الموافقات
            {
                'name': 'انتظار موافقة',
                'category': AlertCategory.APPROVAL.value,
                'condition': 'status = pending_approval',
                'priority': NotificationPriority.MEDIUM.value,
                'notification_type': NotificationType.INFO.value,
                'check_interval_minutes': 180  # كل 3 ساعات
            },
        ]
        
        for rule in default_rules:
            cursor.execute("""
                INSERT OR IGNORE INTO alert_rules 
                (name, category, condition, threshold_value, priority, notification_type, check_interval_minutes)
                SELECT ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM alert_rules WHERE name = ? AND category = ?
                )
            """, (
                rule['name'], rule['category'], rule['condition'],
                rule.get('threshold_value'), rule['priority'],
                rule['notification_type'], rule.get('check_interval_minutes', 60),
                rule['name'], rule['category']
            ))
        
        self.db.connection.commit()
    
    def create_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        category: AlertCategory = AlertCategory.SYSTEM,
        user_id: Optional[int] = None,
        action_url: Optional[str] = None,
        data: Optional[dict] = None
    ) -> int:
        """
        إنشاء إشعار جديد
        
        Args:
            title: عنوان الإشعار
            message: نص الإشعار
            notification_type: نوع الإشعار
            priority: الأولوية
            category: الفئة
            user_id: معرف المستخدم (None للجميع)
            action_url: رابط الإجراء
            data: بيانات إضافية
            
        Returns:
            معرف الإشعار
        """
        cursor = self.db.connection.cursor()
        
        data_json = json.dumps(data) if data else None
        
        cursor.execute("""
            INSERT INTO notifications 
            (title, message, type, priority, category, user_id, action_url, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, message, notification_type.value, priority.value,
            category.value, user_id, action_url, data_json
        ))
        
        self.db.connection.commit()
        notification_id = cursor.lastrowid
        
        # استدعاء callbacks
        self._trigger_callbacks(notification_id)
        
        return notification_id
    
    def get_notifications(
        self,
        user_id: Optional[int] = None,
        unread_only: bool = False,
        category: Optional[AlertCategory] = None,
        limit: int = 50
    ) -> List[Notification]:
        """
        الحصول على الإشعارات
        
        Args:
            user_id: معرف المستخدم (None للجميع)
            unread_only: غير المقروءة فقط
            category: الفئة المحددة
            limit: الحد الأقصى
            
        Returns:
            قائمة الإشعارات
        """
        cursor = self.db.connection.cursor()
        
        query = "SELECT * FROM notifications WHERE 1=1"
        params = []
        
        if user_id is not None:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        if unread_only:
            query += " AND read = 0"
        
        if category:
            query += " AND category = ?"
            params.append(category.value)
        
        query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        notifications = []
        for row in cursor.fetchall():
            data = json.loads(row[8]) if row[8] else None
            
            notifications.append(Notification(
                id=row[0],
                title=row[1],
                message=row[2],
                type=NotificationType(row[3]),
                priority=NotificationPriority(row[4]),
                category=AlertCategory(row[5]),
                user_id=row[6],
                action_url=row[7],
                data=data,
                read=bool(row[9]),
                read_at=datetime.fromisoformat(row[10]) if row[10] else None,
                created_at=datetime.fromisoformat(row[11])
            ))
        
        return notifications
    
    def mark_as_read(self, notification_id: int):
        """
        تعليم إشعار كمقروء
        
        Args:
            notification_id: معرف الإشعار
        """
        cursor = self.db.connection.cursor()
        cursor.execute("""
            UPDATE notifications 
            SET read = 1, read_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (notification_id,))
        self.db.connection.commit()
    
    def mark_all_as_read(self, user_id: Optional[int] = None):
        """
        تعليم جميع الإشعارات كمقروءة
        
        Args:
            user_id: معرف المستخدم (None للجميع)
        """
        cursor = self.db.connection.cursor()
        
        if user_id:
            cursor.execute("""
                UPDATE notifications 
                SET read = 1, read_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND read = 0
            """, (user_id,))
        else:
            cursor.execute("""
                UPDATE notifications 
                SET read = 1, read_at = CURRENT_TIMESTAMP
                WHERE read = 0
            """)
        
        self.db.connection.commit()
    
    def delete_notification(self, notification_id: int):
        """حذف إشعار"""
        cursor = self.db.connection.cursor()
        cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        self.db.connection.commit()
    
    def delete_old_notifications(self, days: int = 30):
        """
        حذف الإشعارات القديمة
        
        Args:
            days: عدد الأيام
            
        Returns:
            عدد الإشعارات المحذوفة
        """
        cursor = self.db.connection.cursor()
        cursor.execute("""
            DELETE FROM notifications 
            WHERE read = 1 
            AND created_at < datetime('now', '-{} days')
        """.format(days))
        self.db.connection.commit()
        return cursor.rowcount
    
    def get_unread_count(self, user_id: Optional[int] = None) -> int:
        """
        عدد الإشعارات غير المقروءة
        
        Args:
            user_id: معرف المستخدم
            
        Returns:
            العدد
        """
        cursor = self.db.connection.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT COUNT(*) FROM notifications 
                WHERE (user_id = ? OR user_id IS NULL) AND read = 0
            """, (user_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE read = 0")
        
        return cursor.fetchone()[0]
    
    def check_inventory_alerts(self):
        """فحص تنبيهات المخزون"""
        cursor = self.db.connection.cursor()
        
        # منتجات نفد مخزونها
        cursor.execute("""
            SELECT p.id, p.name, SUM(s.quantity) as total_qty, p.reorder_point
            FROM products p
            LEFT JOIN stock s ON p.id = s.product_id
            WHERE p.active = 1
            GROUP BY p.id
            HAVING total_qty <= reorder_point OR total_qty IS NULL
        """)
        
        for row in cursor.fetchall():
            product_id, product_name, qty, reorder_point = row
            qty = qty or 0
            
            self.create_notification(
                title="تنبيه: نفاد المخزون",
                message=f"المنتج '{product_name}' نفد من المخزون (الكمية: {qty})",
                notification_type=NotificationType.WARNING,
                priority=NotificationPriority.HIGH,
                category=AlertCategory.INVENTORY,
                action_url=f"/product/{product_id}",
                data={'product_id': product_id, 'quantity': qty, 'reorder_point': reorder_point}
            )
    
    def check_payment_alerts(self):
        """فحص تنبيهات المدفوعات"""
        cursor = self.db.connection.cursor()
        
        # أقساط مستحقة اليوم
        cursor.execute("""
            SELECT pp.id, pp.customer_id, c.name, pp.installment_amount
            FROM payment_plan_installments ppi
            JOIN payment_plans pp ON ppi.plan_id = pp.id
            JOIN customers c ON pp.customer_id = c.id
            WHERE DATE(ppi.due_date) = DATE('now')
            AND ppi.status = 'pending'
        """)
        
        for row in cursor.fetchall():
            plan_id, customer_id, customer_name, amount = row
            
            self.create_notification(
                title="تذكير: قسط مستحق اليوم",
                message=f"قسط مستحق اليوم للعميل '{customer_name}' بقيمة {amount:.2f}",
                notification_type=NotificationType.ALERT,
                priority=NotificationPriority.URGENT,
                category=AlertCategory.PAYMENT,
                action_url=f"/payment_plan/{plan_id}",
                data={'plan_id': plan_id, 'customer_id': customer_id, 'amount': amount}
            )
        
        # أقساط متأخرة
        cursor.execute("""
            SELECT pp.id, pp.customer_id, c.name, ppi.installment_amount, 
                   julianday('now') - julianday(ppi.due_date) as days_overdue
            FROM payment_plan_installments ppi
            JOIN payment_plans pp ON ppi.plan_id = pp.id
            JOIN customers c ON pp.customer_id = c.id
            WHERE ppi.due_date < DATE('now')
            AND ppi.status = 'pending'
        """)
        
        for row in cursor.fetchall():
            plan_id, customer_id, customer_name, amount, days_overdue = row
            
            self.create_notification(
                title="تنبيه: قسط متأخر",
                message=f"قسط متأخر {int(days_overdue)} يوم للعميل '{customer_name}' بقيمة {amount:.2f}",
                notification_type=NotificationType.ERROR,
                priority=NotificationPriority.URGENT,
                category=AlertCategory.PAYMENT,
                action_url=f"/payment_plan/{plan_id}",
                data={
                    'plan_id': plan_id,
                    'customer_id': customer_id,
                    'amount': amount,
                    'days_overdue': int(days_overdue)
                }
            )
    
    def check_all_alerts(self):
        """فحص جميع التنبيهات"""
        self.check_inventory_alerts()
        self.check_payment_alerts()
    
    def register_callback(self, callback: Callable):
        """
        تسجيل callback لاستدعاء عند إنشاء إشعار جديد
        
        Args:
            callback: دالة callback (تأخذ notification_id)
        """
        self._notification_callbacks.append(callback)
    
    def _trigger_callbacks(self, notification_id: int):
        """تشغيل callbacks"""
        for callback in self._notification_callbacks:
            try:
                callback(notification_id)
            except Exception as e:
                print(f"Error in notification callback: {e}")
    
    def get_statistics(self) -> dict:
        """إحصائيات الإشعارات"""
        cursor = self.db.connection.cursor()
        
        stats = {}
        
        # إجمالي الإشعارات
        cursor.execute("SELECT COUNT(*) FROM notifications")
        stats['total'] = cursor.fetchone()[0]
        
        # غير المقروءة
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE read = 0")
        stats['unread'] = cursor.fetchone()[0]
        
        # حسب النوع
        cursor.execute("""
            SELECT type, COUNT(*) 
            FROM notifications 
            GROUP BY type
        """)
        stats['by_type'] = dict(cursor.fetchall())
        
        # حسب الفئة
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM notifications 
            GROUP BY category
        """)
        stats['by_category'] = dict(cursor.fetchall())
        
        # حسب الأولوية
        cursor.execute("""
            SELECT priority, COUNT(*) 
            FROM notifications 
            WHERE read = 0
            GROUP BY priority
        """)
        stats['unread_by_priority'] = dict(cursor.fetchall())
        
        return stats

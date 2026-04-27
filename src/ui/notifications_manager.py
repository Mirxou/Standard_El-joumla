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
from pathlib import Path
import json
import sys
from src.utils.logger import setup_logger


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
    # Multi-Warehouse Notifications
    WAREHOUSE_LOW_STOCK = "warehouse_low_stock"
    WAREHOUSE_OUT_OF_STOCK = "warehouse_out_of_stock"
    WAREHOUSE_TRANSFER_COMPLETED = "warehouse_transfer_completed"
    WAREHOUSE_TRANSFER_PENDING = "warehouse_transfer_pending"
    # Workflow Notifications
    WORKFLOW_PENDING_APPROVAL = "workflow_pending_approval"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"
    WORKFLOW_EXPIRED = "workflow_expired"
    WORKFLOW_COMPLETED = "workflow_completed"


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
    check_performed = Signal()          # إشارة عند اكتمال كل فحص
    
    def __init__(self, db_manager, interval_seconds: int = 300, main_window=None):
        super().__init__()
        self.db_manager = db_manager
        self.interval = interval_seconds
        self.running = True
        self.main_window = main_window  # للحصول على main_window في callbacks
        self.logger = setup_logger(__name__)
    
    def run(self):
        """تشغيل الفحص الدوري"""
        while self.running:
            try:
                notifications = self.check_for_notifications()
                if notifications:
                    self.notifications_found.emit(notifications)
                # دائماً أعلن عن اكتمال الفحص حتى لو لم توجد إشعارات جديدة
                self.check_performed.emit()
            except Exception as e:
                self.logger.error(f"خطأ في فحص الإشعارات: {e}", exc_info=True)
            
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
        
        # فحص إشعارات المستودعات (Multi-Warehouse)
        warehouse_notifications = self.check_warehouse_notifications()
        notifications.extend(warehouse_notifications)
        
        # فحص إشعارات سير العمل (Workflow)
        workflow_notifications = self.check_workflow_notifications()
        notifications.extend(workflow_notifications)
        
        return notifications

    # ----------------- Helpers للجداول -----------------
    def _table_exists(self, table_name: str) -> bool:
        """يتحقق هل الجدول موجود في قاعدة البيانات"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return cur.fetchone() is not None
        except Exception:
            return False

    def _table_has_columns(self, table_name: str, columns: List[str]) -> bool:
        """يتحقق من وجود الأعمدة المطلوبة داخل الجدول"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table_name})")
            existing = {row[1] for row in cur.fetchall()}
            return all(col in existing for col in columns)
        except Exception:
            return False
    
    def check_low_stock(self) -> List[Notification]:
        """فحص المنتجات ذات المخزون المنخفض"""
        notifications = []
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # المنتجات تحت الحد الأدنى
            cursor.execute("""
                SELECT p.id, p.name, p.current_stock, COALESCE(p.min_stock, 0) as min_stock
                FROM products p
                WHERE p.current_stock <= COALESCE(p.min_stock, 0)
                AND p.is_active = 1
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
            self.logger.error(f"خطأ في فحص المخزون: {e}", exc_info=True)
        
        return notifications
    
    def check_payment_due(self) -> List[Notification]:
        """فحص المدفوعات المستحقة"""
        notifications = []
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            # نتأكد أن جدول المبيعات موجود و الأعمدة الضرورية متوفرة
            if not (self._table_exists('sales') and self._table_has_columns('sales', ['id','invoice_number','customer_name','total_amount','due_date','paid_amount'])):
                return notifications  # لا يوجد ما يمكن فحصه حالياً

            seven_days = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

            # الفواتير (المبيعات الآجلة) غير المسددة كلياً و المستحقة خلال 7 أيام
            cursor.execute("""
                SELECT id, invoice_number, customer_name, total_amount, due_date, paid_amount
                FROM sales
                WHERE due_date IS NOT NULL
                AND due_date <= ?
                AND due_date >= date('now')
                AND (paid_amount < total_amount)
                AND status NOT IN ('ملغية','مرتجعة')
                ORDER BY due_date
                LIMIT 5
            """, (seven_days,))

            for row in cursor.fetchall():
                inv_id, number, customer, amount, due_date, paid_amount = row
                remaining = (amount - paid_amount) if (amount is not None and paid_amount is not None) else amount

                notification = Notification(
                    id=f"payment_due_{inv_id}_{int(datetime.now().timestamp())}",
                    type=NotificationType.PAYMENT_DUE,
                    title="💰 دفعة مستحقة",
                    message=f"فاتورة #{number} لـ {customer} المتبقي {remaining:.2f} مستحق في {due_date}",
                    timestamp=datetime.now(),
                    priority=1,
                    action_label="عرض الفاتورة"
                )
                notifications.append(notification)
            
        except Exception as e:
            self.logger.error(f"خطأ في فحص المدفوعات: {e}", exc_info=True)
        
        return notifications
    
    def check_reminders(self) -> List[Notification]:
        """فحص التذكيرات النشطة"""
        notifications = []
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            # التأكد من وجود جدول التذكيرات و الأعمدة
            if not (self._table_exists('reminders') and self._table_has_columns('reminders', ['id','title','description','reminder_time','status'])):
                return notifications

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
            self.logger.error(f"خطأ في فحص التذكيرات: {e}", exc_info=True)
        
        return notifications
    
    def check_warehouse_notifications(self) -> List[Notification]:
        """فحص إشعارات المستودعات (Multi-Warehouse)"""
        notifications = []
        
        try:
            # التحقق من وجود جدول warehouses
            if not self._table_exists('warehouses'):
                return notifications
            
            from src.services.warehouse_service import WarehouseService
            warehouse_service = WarehouseService(self.db_manager)
            
            # فحص جميع المستودعات النشطة
            warehouses = warehouse_service.get_all_warehouses(include_inactive=False)
            
            for warehouse in warehouses:
                # فحص المخزون المنخفض والنافذ في المستودع
                inventory = warehouse_service.get_warehouse_inventory(warehouse.id)
                
                low_stock_count = 0
                out_of_stock_count = 0
                low_stock_items = []
                out_of_stock_items = []
                
                for inv in inventory:
                    if inv.available_quantity <= 0:
                        out_of_stock_count += 1
                        if len(out_of_stock_items) < 5:  # أول 5 منتجات فقط
                            out_of_stock_items.append(inv.product_name or f"منتج #{inv.product_id}")
                    elif inv.available_quantity <= inv.min_stock:
                        low_stock_count += 1
                        if len(low_stock_items) < 5:  # أول 5 منتجات فقط
                            low_stock_items.append(inv.product_name or f"منتج #{inv.product_id}")
                
                # إشعار نفاد المخزون
                if out_of_stock_count > 0:
                    items_text = ", ".join(out_of_stock_items)
                    if out_of_stock_count > 5:
                        items_text += f" و{out_of_stock_count - 5} منتج آخر"
                    
                    # إنشاء callback لفتح نافذة إدارة المستودعات
                    def open_warehouse_management():
                        try:
                            mw = getattr(self, 'main_window', None)
                            if mw and hasattr(mw, 'show_warehouse_management_window'):
                                mw.show_warehouse_management_window()
                        except Exception as e:
                            self.logger.error(f"خطأ في فتح نافذة إدارة المستودعات: {e}", exc_info=True)
                    
                    notification = Notification(
                        id=f"warehouse_out_{warehouse.id}_{datetime.now().strftime('%Y%m%d')}",
                        type=NotificationType.WAREHOUSE_OUT_OF_STOCK,
                        title=f"⚠️ نفاد المخزون في {warehouse.name}",
                        message=f"نفد المخزون من {out_of_stock_count} منتج في مستودع {warehouse.name}:\n{items_text}",
                        timestamp=datetime.now(),
                        priority=3,  # عاجل
                        action_label="عرض المستودع",
                        action_callback=open_warehouse_management
                    )
                    notifications.append(notification)
                
                # إشعار المخزون المنخفض
                elif low_stock_count > 0:
                    items_text = ", ".join(low_stock_items)
                    if low_stock_count > 5:
                        items_text += f" و{low_stock_count - 5} منتج آخر"
                    
                    # إنشاء callback لفتح نافذة إدارة المستودعات
                    def open_warehouse_management():
                        try:
                            mw = getattr(self, 'main_window', None)
                            if mw and hasattr(mw, 'show_warehouse_management_window'):
                                mw.show_warehouse_management_window()
                        except Exception as e:
                            self.logger.error(f"خطأ في فتح نافذة إدارة المستودعات: {e}", exc_info=True)
                    
                    # 🔔 إطلاق Webhook: إرسال Webhook عند اكتشاف مخزون منخفض
                    try:
                        from src.services.webhook_service import WebhookService
                        webhook_service = WebhookService(self.db_manager)
                        
                        # بناء Payload للـ Webhook
                        webhook_payload = {
                            "event": "inventory_low_stock",
                            "warehouse_id": warehouse.id,
                            "warehouse_name": warehouse.name,
                            "low_stock_count": low_stock_count,
                            "low_stock_items": low_stock_items[:10],  # أول 10 منتجات فقط
                            "detected_at": datetime.now().isoformat()
                        }
                        
                        webhook_service.trigger_webhook(
                            event_type="inventory_low_stock",
                            payload=webhook_payload,
                            entity_id=warehouse.id,
                            company_id=warehouse.company_id if hasattr(warehouse, 'company_id') else None
                        )
                    except Exception as e:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.warning(f"⚠️ فشل إطلاق Webhook: {e}")
                    
                    notification = Notification(
                        id=f"warehouse_low_{warehouse.id}_{datetime.now().strftime('%Y%m%d')}",
                        type=NotificationType.WAREHOUSE_LOW_STOCK,
                        title=f"📉 مخزون منخفض في {warehouse.name}",
                        message=f"المخزون منخفض لـ {low_stock_count} منتج في مستودع {warehouse.name}:\n{items_text}",
                        timestamp=datetime.now(),
                        priority=2,  # عالي
                        action_label="عرض المستودع",
                        action_callback=open_warehouse_management
                    )
                    notifications.append(notification)
                
                # فحص التحويلات المعلقة
                transfers = warehouse_service.get_transfers(warehouse_id=warehouse.id, status='pending')
                if transfers:
                    pending_count = len(transfers)
                    # إنشاء callback لفتح نافذة نقل المخزون
                    def open_warehouse_transfers():
                        try:
                            mw = getattr(self, 'main_window', None)
                            if mw and hasattr(mw, 'show_warehouse_transfer_window'):
                                mw.show_warehouse_transfer_window()
                        except Exception as e:
                            self.logger.error(f"خطأ في فتح نافذة نقل المخزون: {e}", exc_info=True)
                    
                    notification = Notification(
                        id=f"warehouse_transfer_pending_{warehouse.id}_{datetime.now().strftime('%Y%m%d')}",
                        type=NotificationType.WAREHOUSE_TRANSFER_PENDING,
                        title=f"⏳ تحويلات معلقة في {warehouse.name}",
                        message=f"يوجد {pending_count} تحويل معلق في مستودع {warehouse.name} يحتاج إلى إكمال",
                        timestamp=datetime.now(),
                        priority=1,  # متوسط
                        action_label="عرض التحويلات",
                        action_callback=open_warehouse_transfers
                    )
                    notifications.append(notification)
            
        except Exception as e:
            self.logger.error(f"خطأ في فحص إشعارات المستودعات: {e}", exc_info=True)
        
        return notifications
    
    def check_workflow_notifications(self) -> List[Notification]:
        """فحص إشعارات سير العمل (Workflow)"""
        notifications = []
        
        try:
            # التحقق من وجود جداول Workflow
            if not (self._table_exists('workflow_instances') and 
                    self._table_exists('workflow_approvals') and
                    self._table_exists('workflow_steps')):
                return notifications
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 1. الموافقات المعلقة للمستخدم الحالي
            # (سنحتاج معرف المستخدم الحالي - سنستخدم None للجميع حالياً)
            cursor.execute("""
                SELECT 
                    wa.id,
                    wa.instance_id,
                    wa.step_id,
                    wa.approver_id,
                    wa.deadline,
                    wa.status,
                    wi.entity_type,
                    wi.entity_id,
                    ws.name as step_name,
                    w.name as workflow_name,
                    u.username as approver_name
                FROM workflow_approvals wa
                JOIN workflow_instances wi ON wa.instance_id = wi.id
                JOIN workflow_steps ws ON wa.step_id = ws.id
                JOIN workflows w ON ws.workflow_id = w.id
                LEFT JOIN users u ON wa.approver_id = u.id
                WHERE wa.status = 'pending'
                AND (wa.deadline IS NULL OR wa.deadline > datetime('now'))
                ORDER BY wa.deadline ASC, wa.created_at ASC
                LIMIT 10
            """)
            
            for row in cursor.fetchall():
                approval_id, instance_id, step_id, approver_id, deadline, status, \
                entity_type, entity_id, step_name, workflow_name, approver_name = row
                
                # تحديد نوع الكيان واسمه
                entity_name = f"{entity_type} #{entity_id}"
                if entity_type == "purchase_order":
                    po_query = "SELECT po_number FROM purchase_orders WHERE id = ?"
                    po_result = cursor.execute(po_query, (entity_id,)).fetchone()
                    if po_result:
                        entity_name = f"أمر شراء {po_result[0]}"
                elif entity_type == "sale":
                    sale_query = "SELECT invoice_number FROM sales WHERE id = ?"
                    sale_result = cursor.execute(sale_query, (entity_id,)).fetchone()
                    if sale_result:
                        entity_name = f"فاتورة {sale_result[0]}"
                
                deadline_text = ""
                if deadline:
                    deadline_dt = datetime.fromisoformat(deadline)
                    now = datetime.now()
                    if deadline_dt < now:
                        deadline_text = " (منتهية الصلاحية!)"
                    else:
                        hours_left = (deadline_dt - now).total_seconds() / 3600
                        if hours_left < 24:
                            deadline_text = f" (متبقي {int(hours_left)} ساعة)"
                        else:
                            days_left = int(hours_left / 24)
                            deadline_text = f" (متبقي {days_left} يوم)"
                
                # إنشاء callback لفتح نافذة سير العمل
                def open_workflow_designer(inst_id=instance_id):
                    try:
                        mw = getattr(self, 'main_window', None)
                        if mw and hasattr(mw, 'show_workflow_designer_window'):
                            mw.show_workflow_designer_window()
                    except Exception as e:
                        self.logger.error(f"خطأ في فتح نافذة سير العمل: {e}", exc_info=True)
                
                notification = Notification(
                    id=f"workflow_pending_{approval_id}_{int(datetime.now().timestamp())}",
                    type=NotificationType.WORKFLOW_PENDING_APPROVAL,
                    title=f"⏳ موافقة مطلوبة: {step_name}",
                    message=f"يحتاج {entity_name} إلى موافقتك في سير العمل '{workflow_name}'{deadline_text}",
                    timestamp=datetime.now(),
                    priority=2 if deadline and datetime.fromisoformat(deadline) < datetime.now() + timedelta(hours=24) else 1,
                    action_label="عرض الموافقات",
                    action_callback=open_workflow_designer
                )
                notifications.append(notification)
            
            # 2. الموافقات المنتهية الصلاحية
            cursor.execute("""
                SELECT 
                    wa.id,
                    wa.instance_id,
                    wa.step_id,
                    wa.approver_id,
                    wa.deadline,
                    wi.entity_type,
                    wi.entity_id,
                    ws.name as step_name,
                    w.name as workflow_name
                FROM workflow_approvals wa
                JOIN workflow_instances wi ON wa.instance_id = wi.id
                JOIN workflow_steps ws ON wa.step_id = ws.id
                JOIN workflows w ON ws.workflow_id = w.id
                WHERE wa.status = 'pending'
                AND wa.deadline IS NOT NULL
                AND wa.deadline < datetime('now')
                AND wa.reminder_sent = 0
                ORDER BY wa.deadline ASC
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                approval_id, instance_id, step_id, approver_id, deadline, \
                entity_type, entity_id, step_name, workflow_name = row
                
                entity_name = f"{entity_type} #{entity_id}"
                if entity_type == "purchase_order":
                    po_query = "SELECT po_number FROM purchase_orders WHERE id = ?"
                    po_result = cursor.execute(po_query, (entity_id,)).fetchone()
                    if po_result:
                        entity_name = f"أمر شراء {po_result[0]}"
                elif entity_type == "sale":
                    sale_query = "SELECT invoice_number FROM sales WHERE id = ?"
                    sale_result = cursor.execute(sale_query, (entity_id,)).fetchone()
                    if sale_result:
                        entity_name = f"فاتورة {sale_result[0]}"
                
                def open_workflow_designer(inst_id=instance_id):
                    try:
                        mw = getattr(self, 'main_window', None)
                        if mw and hasattr(mw, 'show_workflow_designer_window'):
                            mw.show_workflow_designer_window()
                    except Exception as e:
                        self.logger.error(f"خطأ في فتح نافذة سير العمل: {e}", exc_info=True)
                
                notification = Notification(
                    id=f"workflow_expired_{approval_id}_{int(datetime.now().timestamp())}",
                    type=NotificationType.WORKFLOW_EXPIRED,
                    title=f"⚠️ موافقة منتهية الصلاحية: {step_name}",
                    message=f"انتهت صلاحية الموافقة المطلوبة لـ {entity_name} في سير العمل '{workflow_name}'",
                    timestamp=datetime.now(),
                    priority=3,  # عاجل
                    action_label="عرض الموافقات",
                    action_callback=open_workflow_designer
                )
                notifications.append(notification)
                
                # تحديث reminder_sent لتجنب تكرار الإشعار
                cursor.execute("""
                    UPDATE workflow_approvals 
                    SET reminder_sent = 1 
                    WHERE id = ?
                """, (approval_id,))
                conn.commit()
            
        except Exception as e:
            self.logger.error(f"خطأ في فحص إشعارات سير العمل: {e}", exc_info=True)
        
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
            # Multi-Warehouse Notifications
            NotificationType.WAREHOUSE_LOW_STOCK: "#FFF9C4",
            NotificationType.WAREHOUSE_OUT_OF_STOCK: "#FFCDD2",
            NotificationType.WAREHOUSE_TRANSFER_COMPLETED: "#C8E6C9",
            NotificationType.WAREHOUSE_TRANSFER_PENDING: "#FFE0B2",
            # Workflow Notifications
            NotificationType.WORKFLOW_PENDING_APPROVAL: "#E1F5FE",
            NotificationType.WORKFLOW_APPROVED: "#C8E6C9",
            NotificationType.WORKFLOW_REJECTED: "#FFCDD2",
            NotificationType.WORKFLOW_EXPIRED: "#FFE0B2",
            NotificationType.WORKFLOW_COMPLETED: "#C8E6C9",
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
        
        settings_btn = QPushButton("⚙️ إعدادات الإشعارات")
        settings_btn.setToolTip("فتح إعدادات الإشعارات لتغيير فترة الفحص")
        settings_btn.clicked.connect(self.open_notifications_settings)
        top_buttons.addWidget(settings_btn)

        top_buttons.addStretch()
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_notifications)
        top_buttons.addWidget(refresh_btn)

        # فحص فوري
        check_now_btn = QPushButton("⟳ افحص الآن")
        check_now_btn.setToolTip("تنفيذ فحص الإشعارات فوراً")
        check_now_btn.clicked.connect(self.run_check_now)
        top_buttons.addWidget(check_now_btn)
        
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
            # ربط إجراء الإشعار
            if notification.action_callback:
                widget.action_clicked.connect(lambda nid=notification.id: self._handle_notification_action(nid))
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

    def run_check_now(self):
        """تنفيذ فحص إشعارات فوري"""
        try:
            self.notifications_manager.force_check()
            self.load_notifications()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"تعذر تنفيذ الفحص الآن: {e}")

    def _handle_notification_action(self, notification_id: str):
        """معالجة إجراء الإشعار"""
        try:
            # البحث عن الإشعار
            notification = None
            for n in self.notifications_manager.get_all_notifications():
                if n.id == notification_id:
                    notification = n
                    break
            
            if notification and notification.action_callback:
                # استدعاء callback الإجراء
                notification.action_callback()
                # تحديد الإشعار كمقروء
                self.notifications_manager.mark_as_read(notification_id)
        except Exception as e:
            self.logger.error(f"خطأ في معالجة إجراء الإشعار: {e}", exc_info=True)
    
    def open_notifications_settings(self):
        """فتح تبويب الإعدادات والتركيز على إعدادات الإشعارات"""
        try:
            mw = getattr(self.notifications_manager, 'main_window', None)
            if mw and hasattr(mw, 'tab_widget') and hasattr(mw, 'settings_tab'):
                mw.tab_widget.setCurrentWidget(mw.settings_tab)
                # إذا كانت هناك قائمة منسدلة لفترة الإشعارات، يمكن لفت الانتباه إليها بتغيير التركيز
                if hasattr(mw, 'notifications_interval_combo'):
                    mw.notifications_interval_combo.setFocus()
                self.accept()
        except Exception as e:
            self.logger.error(f"خطأ في فتح إعدادات الإشعارات: {e}", exc_info=True)


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
        self.last_check_time: Optional[datetime] = None
        self.logger = setup_logger(__name__)
        
        # تحميل الإشعارات المحفوظة
        self.load_notifications()
    
    def start(self):
        """بدء نظام الإشعارات"""
        # تحديد فترة الفحص من الإعدادات أو التهيئة (افتراضي 300 ثانية)
        interval_seconds = 300
        try:
            # تفضيل QSettings إن وُجد
            from PySide6.QtCore import QSettings
            s = QSettings('LogicalVersion', 'ERP')
            val = s.value('notifications/interval_seconds', None)
            if val is not None:
                interval_seconds = int(val)
        except Exception:
            pass

        # محاولة القراءة من config_manager للنافذة الرئيسية إن توفر
        try:
            if self.main_window and hasattr(self.main_window, 'config_manager') and self.main_window.config_manager:
                cfg_val = self.main_window.config_manager.get('notifications.interval_seconds', None)
                if cfg_val is not None:
                    interval_seconds = int(cfg_val)
        except Exception:
            pass

        # بدء الفحص الدوري
        self.checker = NotificationChecker(self.db_manager, interval_seconds=interval_seconds, main_window=self.main_window)
        self.checker.notifications_found.connect(self.on_notifications_found)
        self.checker.check_performed.connect(self._on_check_performed)
        self.checker.start()
        
        # إعداد System Tray
        if self.main_window:
            self.setup_system_tray()
    
    def stop(self):
        """إيقاف نظام الإشعارات"""
        if self.checker and self.checker.isRunning():
            self.checker.stop()
            # إعطاء الـ thread وقت كافي للإغلاق النظيف
            if not self.checker.wait(3000):  # 3 ثواني
                self.checker.terminate()
                self.checker.wait(1000)
    
    def setup_system_tray(self):
        """إعداد System Tray"""
        try:
            self.system_tray = QSystemTrayIcon(self.main_window)
            
            # إنشاء أيقونة افتراضية إذا لم تكن موجودة
            from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
            from PySide6.QtCore import QSize
            
            # محاولة تحميل أيقونة من الملفات
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
            if icon_path.exists():
                icon = QIcon(str(icon_path))
            else:
                # إنشاء أيقونة بسيطة برمجياً
                pixmap = QPixmap(64, 64)
                pixmap.fill(QColor(0, 120, 215))  # لون أزرق
                painter = QPainter(pixmap)
                painter.setPen(QColor(255, 255, 255))
                from PySide6.QtGui import QFont
                font = QFont()
                font.setPixelSize(40)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(pixmap.rect(), Qt.AlignCenter, "🔔")
                painter.end()
                icon = QIcon(pixmap)
            
            self.system_tray.setIcon(icon)
            self.system_tray.setToolTip("نظام الإشعارات - Standard El-Joumla")
            
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
            self.logger.error(f"خطأ في إعداد System Tray: {e}", exc_info=True)
    
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

    def _on_check_performed(self):
        """تحديث وقت آخر فحص"""
        try:
            self.last_check_time = datetime.now()
        except Exception:
            pass
    
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
            self.logger.error(f"خطأ في حفظ الإشعارات: {e}", exc_info=True)
    
    def load_notifications(self):
        """تحميل الإشعارات"""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings('LogicalVersion', 'ERP')
            
            data = settings.value('notifications', '[]')
            notifications_data = json.loads(data)
            
            self.notifications = [Notification.from_dict(n) for n in notifications_data]
        except Exception as e:
            self.logger.error(f"خطأ في تحميل الإشعارات: {e}", exc_info=True)
            self.notifications = []
    
    def show_notification_center(self):
        """عرض مركز الإشعارات"""
        dialog = NotificationCenterDialog(self, self.main_window)
        dialog.show()

    def get_last_check_time_str(self) -> str:
        """إرجاع آخر وقت فحص كسلسلة قابلة للعرض"""
        try:
            if not self.last_check_time:
                return "—"
            return self.last_check_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return "—"

    def force_check(self):
        """تنفيذ فحص فوري للإشعارات وتحديث الحالة"""
        try:
            # استخدام نفس منطق الفاحص بدون تشغيل خيط منفصل
            temp_checker = NotificationChecker(self.db_manager, interval_seconds=0, main_window=self.main_window)
            new_list = temp_checker.check_for_notifications()
            if new_list:
                self.on_notifications_found(new_list)
            # تحديث وقت آخر فحص
            self._on_check_performed()
        except Exception as e:
            self.logger.error(f"خطأ في الفحص الفوري للإشعارات: {e}", exc_info=True)


# Global instance
_notifications_manager: Optional[SmartNotificationsManager] = None


def get_notifications_manager(db_manager=None, main_window=None) -> SmartNotificationsManager:
    """الحصول على مدير الإشعارات العام"""
    global _notifications_manager
    if _notifications_manager is None and db_manager:
        _notifications_manager = SmartNotificationsManager(db_manager, main_window)
        _notifications_manager.start()
    return _notifications_manager

"""
نظام سجل التدقيق الشامل
Comprehensive Audit Trail System

يتتبع جميع التغييرات في النظام مع تفاصيل كاملة
Tracks all system changes with complete details
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """أنواع العمليات المسجلة"""
    
    # عمليات البيانات
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    
    # عمليات الموافقات
    APPROVE = "approve"
    REJECT = "reject"
    VOID = "void"
    
    # عمليات تسجيل الدخول
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # عمليات النظام
    BACKUP = "backup"
    RESTORE = "restore"
    EXPORT = "export"
    IMPORT = "import"
    
    # عمليات الصلاحيات
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"


class AuditEntity(Enum):
    """الكيانات القابلة للتدقيق"""
    
    # الكيانات الأساسية
    SALE = "sale"
    PRODUCT = "product"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PURCHASE = "purchase"
    
    # المحاسبة
    JOURNAL_ENTRY = "journal_entry"
    ACCOUNT = "account"
    PERIOD = "period"
    
    # العمليات الخاصة
    QUOTE = "quote"
    RETURN = "return"
    PAYMENT_PLAN = "payment_plan"
    INSTALLMENT = "installment"
    CYCLE_COUNT = "cycle_count"
    
    # النظام
    USER = "user"
    ROLE = "role"
    SETTINGS = "settings"
    BACKUP = "backup"


class AuditEntry:
    """سجل تدقيق واحد"""
    
    def __init__(
        self,
        audit_id: Optional[int] = None,
        user_id: Optional[int] = None,
        username: str = "",
        action: str = "",
        entity_type: str = "",
        entity_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, tuple]] = None,
        ip_address: str = "",
        user_agent: str = "",
        timestamp: Optional[datetime] = None,
        success: bool = True,
        error_message: str = ""
    ):
        self.audit_id = audit_id
        self.user_id = user_id
        self.username = username
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.old_values = old_values or {}
        self.new_values = new_values or {}
        self.changes = changes or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.timestamp = timestamp or datetime.now()
        self.success = success
        self.error_message = error_message
        
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'audit_id': self.audit_id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'changes': self.changes,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success,
            'error_message': self.error_message
        }


class AuditTrailManager:
    """
    مدير سجل التدقيق
    
    يوفر:
    - تسجيل جميع العمليات
    - تتبع التغييرات (من غيّر، متى، ماذا)
    - استعلامات متقدمة
    - تقارير تدقيق
    - حذف آلي للسجلات القديمة
    """
    
    def __init__(self, db_manager):
        """
        تهيئة مدير التدقيق
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
        self._create_tables()
        
    def _create_tables(self):
        """إنشاء جداول التدقيق"""
        
        # جدول سجل التدقيق الرئيسي
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                old_values TEXT,  -- JSON
                new_values TEXT,  -- JSON
                changes TEXT,     -- JSON: {field: [old, new]}
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # جدول ملخص نشاط المستخدمين
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_summary (
                user_id INTEGER,
                date DATE,
                total_actions INTEGER DEFAULT 0,
                creates INTEGER DEFAULT 0,
                updates INTEGER DEFAULT 0,
                deletes INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                last_activity TIMESTAMP,
                PRIMARY KEY (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # فهارس للأداء
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_trail(user_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_trail(action)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_trail(entity_type, entity_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail(timestamp DESC)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_success ON audit_trail(success)")
        
    def log(
        self,
        user_id: Optional[int],
        username: str,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: str = "",
        user_agent: str = "",
        success: bool = True,
        error_message: str = ""
    ) -> Optional[int]:
        """
        تسجيل عملية في سجل التدقيق
        
        Args:
            user_id: معرف المستخدم
            username: اسم المستخدم
            action: نوع العملية
            entity_type: نوع الكيان
            entity_id: معرف الكيان
            old_values: القيم القديمة (للتحديث/الحذف)
            new_values: القيم الجديدة (للإنشاء/التحديث)
            ip_address: عنوان IP
            user_agent: متصفح المستخدم
            success: نجاح العملية
            error_message: رسالة الخطأ (إن وجدت)
            
        Returns:
            معرف السجل أو None
        """
        try:
            # حساب التغييرات
            changes = self._calculate_changes(old_values, new_values)
            
            # تحويل إلى JSON
            old_values_json = json.dumps(old_values) if old_values else None
            new_values_json = json.dumps(new_values) if new_values else None
            changes_json = json.dumps(changes) if changes else None
            
            # إدراج السجل
            cursor = self.db.execute(
                """INSERT INTO audit_trail (
                    user_id, username, action, entity_type, entity_id,
                    old_values, new_values, changes,
                    ip_address, user_agent, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id, username, action, entity_type, entity_id,
                    old_values_json, new_values_json, changes_json,
                    ip_address, user_agent, success, error_message
                )
            )
            
            # تحديث ملخص النشاط
            if user_id:
                self._update_activity_summary(user_id, action, success)
                
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Failed to log audit entry: {str(e)}")
            return None
            
    def _calculate_changes(
        self,
        old_values: Optional[Dict[str, Any]],
        new_values: Optional[Dict[str, Any]]
    ) -> Dict[str, tuple]:
        """
        حساب الفروقات بين القيم القديمة والجديدة
        
        Args:
            old_values: القيم القديمة
            new_values: القيم الجديدة
            
        Returns:
            قاموس {field: (old_value, new_value)}
        """
        if not old_values or not new_values:
            return {}
            
        changes = {}
        
        # المفاتيح المشتركة
        all_keys = set(old_values.keys()) | set(new_values.keys())
        
        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)
            
            if old_val != new_val:
                changes[key] = (old_val, new_val)
                
        return changes
        
    def _update_activity_summary(self, user_id: int, action: str, success: bool):
        """تحديث ملخص نشاط المستخدم"""
        try:
            today = datetime.now().date()
            
            # التحقق من وجود سجل اليوم
            existing = self.db.fetch_one(
                "SELECT total_actions FROM user_activity_summary WHERE user_id = ? AND date = ?",
                (user_id, today)
            )
            
            if existing:
                # تحديث السجل
                updates = ["total_actions = total_actions + 1", "last_activity = CURRENT_TIMESTAMP"]
                
                if success:
                    if action == AuditAction.CREATE.value:
                        updates.append("creates = creates + 1")
                    elif action == AuditAction.UPDATE.value:
                        updates.append("updates = updates + 1")
                    elif action == AuditAction.DELETE.value:
                        updates.append("deletes = deletes + 1")
                    elif action == AuditAction.VIEW.value:
                        updates.append("views = views + 1")
                else:
                    updates.append("failed_attempts = failed_attempts + 1")
                    
                self.db.execute(
                    f"""UPDATE user_activity_summary 
                        SET {', '.join(updates)}
                        WHERE user_id = ? AND date = ?""",
                    (user_id, today)
                )
            else:
                # إنشاء سجل جديد
                creates = 1 if action == AuditAction.CREATE.value and success else 0
                updates_count = 1 if action == AuditAction.UPDATE.value and success else 0
                deletes = 1 if action == AuditAction.DELETE.value and success else 0
                views = 1 if action == AuditAction.VIEW.value and success else 0
                failed = 0 if success else 1
                
                self.db.execute(
                    """INSERT INTO user_activity_summary (
                        user_id, date, total_actions, creates, updates, deletes, views,
                        failed_attempts, last_activity
                    ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, today, creates, updates_count, deletes, views, failed)
                )
                
        except Exception as e:
            logger.error(f"Failed to update activity summary: {str(e)}")
            
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        الحصول على تاريخ كيان معين
        
        Args:
            entity_type: نوع الكيان
            entity_id: معرف الكيان
            limit: الحد الأقصى للسجلات
            
        Returns:
            قائمة سجلات التدقيق
        """
        rows = self.db.fetch_all(
            """SELECT * FROM audit_trail
               WHERE entity_type = ? AND entity_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (entity_type, entity_id, limit)
        )
        
        return self._rows_to_entries(rows)
        
    def get_user_activity(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        الحصول على نشاط مستخدم
        
        Args:
            user_id: معرف المستخدم
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            limit: الحد الأقصى
            
        Returns:
            قائمة السجلات
        """
        query = "SELECT * FROM audit_trail WHERE user_id = ?"
        params = [user_id]
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self.db.fetch_all(query, tuple(params))
        return self._rows_to_entries(rows)
        
    def search(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: bool = False,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        بحث متقدم في سجل التدقيق
        
        Args:
            action: نوع العملية
            entity_type: نوع الكيان
            user_id: معرف المستخدم
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            success_only: فقط العمليات الناجحة
            limit: الحد الأقصى
            
        Returns:
            قائمة السجلات
        """
        query = "SELECT * FROM audit_trail WHERE 1=1"
        params = []
        
        if action:
            query += " AND action = ?"
            params.append(action)
            
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
            
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
            
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
            
        if success_only:
            query += " AND success = 1"
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self.db.fetch_all(query, tuple(params))
        return self._rows_to_entries(rows)
        
    def get_activity_summary(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        الحصول على ملخص النشاط
        
        Args:
            user_id: معرف المستخدم (اختياري)
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            
        Returns:
            قائمة الملخصات
        """
        query = "SELECT * FROM user_activity_summary WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
            
        if start_date:
            query += " AND date >= ?"
            params.append(start_date.date())
            
        if end_date:
            query += " AND date <= ?"
            params.append(end_date.date())
            
        query += " ORDER BY date DESC"
        
        rows = self.db.fetch_all(query, tuple(params))
        
        summaries = []
        for row in rows:
            summaries.append({
                'user_id': row[0],
                'date': row[1],
                'total_actions': row[2],
                'creates': row[3],
                'updates': row[4],
                'deletes': row[5],
                'views': row[6],
                'failed_attempts': row[7],
                'last_activity': row[8]
            })
            
        return summaries
        
    def cleanup_old_records(self, days: int = 365) -> int:
        """
        حذف السجلات القديمة
        
        Args:
            days: عدد الأيام للاحتفاظ
            
        Returns:
            عدد السجلات المحذوفة
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor = self.db.execute(
                "DELETE FROM audit_trail WHERE timestamp < ?",
                (cutoff_date,)
            )
            
            deleted = cursor.rowcount
            logger.info(f"Deleted {deleted} old audit records")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {str(e)}")
            return 0
            
    def _rows_to_entries(self, rows: List[tuple]) -> List[AuditEntry]:
        """تحويل صفوف قاعدة البيانات إلى كائنات AuditEntry"""
        entries = []
        
        for row in rows:
            old_values = json.loads(row[6]) if row[6] else {}
            new_values = json.loads(row[7]) if row[7] else {}
            changes = json.loads(row[8]) if row[8] else {}
            
            entries.append(AuditEntry(
                audit_id=row[0],
                user_id=row[1],
                username=row[2],
                action=row[3],
                entity_type=row[4],
                entity_id=row[5],
                old_values=old_values,
                new_values=new_values,
                changes=changes,
                ip_address=row[9],
                user_agent=row[10],
                timestamp=datetime.fromisoformat(row[11]) if row[11] else None,
                success=bool(row[12]),
                error_message=row[13] or ""
            ))
            
        return entries


# مثيل عام
global_audit_manager: Optional[AuditTrailManager] = None


def initialize_audit_manager(db_manager) -> AuditTrailManager:
    """تهيئة مدير التدقيق العام"""
    global global_audit_manager
    global_audit_manager = AuditTrailManager(db_manager)
    return global_audit_manager


def get_audit_manager() -> Optional[AuditTrailManager]:
    """الحصول على مدير التدقيق العام"""
    return global_audit_manager


# Decorator للتدقيق التلقائي
def audited(entity_type: str):
    """
    Decorator لتسجيل العمليات تلقائياً
    
    الاستخدام:
    @audited(entity_type="sale")
    def create_sale(self, data):
        ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # تنفيذ الدالة
            result = func(*args, **kwargs)
            
            # تسجيل في التدقيق
            if global_audit_manager:
                action = AuditAction.CREATE.value
                if 'update' in func.__name__:
                    action = AuditAction.UPDATE.value
                elif 'delete' in func.__name__:
                    action = AuditAction.DELETE.value
                    
                global_audit_manager.log(
                    user_id=kwargs.get('user_id'),
                    username=kwargs.get('username', 'system'),
                    action=action,
                    entity_type=entity_type,
                    entity_id=result if isinstance(result, int) else None,
                    new_values=kwargs.get('data', {})
                )
                
            return result
        return wrapper
    return decorator

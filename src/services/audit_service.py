"""
خدمة سجل التدقيق
Audit Log Service
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta

from ..core.database_manager import DatabaseManager
from ..models.permission import AuditLog, LoginHistory


class AuditService:
    """خدمة سجل التدقيق"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    # ==================== Audit Logs ====================
    
    def log_action(self, user_id: Optional[int], username: str, action: str,
                   resource_type: str, resource_id: Optional[int] = None,
                   old_value: Any = None, new_value: Any = None,
                   ip_address: str = "", user_agent: str = "",
                   status: str = "success", error_message: str = "") -> int:
        """تسجيل عملية في سجل التدقيق"""
        
        # تحويل القيم إلى JSON
        old_json = json.dumps(old_value, ensure_ascii=False) if old_value else ""
        new_json = json.dumps(new_value, ensure_ascii=False) if new_value else ""
        
        return self.db.execute_update(
            """INSERT INTO audit_logs 
               (user_id, username, action, resource_type, resource_id,
                old_value, new_value, ip_address, user_agent, status, error_message, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [user_id, username, action, resource_type, resource_id,
             old_json, new_json, ip_address, user_agent, status, error_message,
             datetime.now().isoformat()]
        )
    
    def get_audit_log(self, log_id: int) -> Optional[AuditLog]:
        """الحصول على سجل تدقيق معين"""
        result = self.db.execute_query(
            "SELECT * FROM audit_logs WHERE id = ?",
            [log_id]
        )
        if not result:
            return None
        
        return self._audit_log_from_row(result[0])
    
    def list_audit_logs(self, user_id: Optional[int] = None,
                       resource_type: Optional[str] = None,
                       action: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       status: Optional[str] = None,
                       limit: int = 100,
                       offset: int = 0) -> List[AuditLog]:
        """قائمة سجلات التدقيق مع فلاتر"""
        
        sql = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        if resource_type:
            sql += " AND resource_type = ?"
            params.append(resource_type)
        
        if action:
            sql += " AND action = ?"
            params.append(action)
        
        if status:
            sql += " AND status = ?"
            params.append(status)
        
        if start_date:
            sql += " AND created_at >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            sql += " AND created_at <= ?"
            params.append(end_date.isoformat())
        
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        result = self.db.execute_query(sql, params)
        return [self._audit_log_from_row(row) for row in result]
    
    def count_audit_logs(self, user_id: Optional[int] = None,
                        resource_type: Optional[str] = None,
                        action: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        status: Optional[str] = None) -> int:
        """عد سجلات التدقيق"""
        
        sql = "SELECT COUNT(*) as total FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        if resource_type:
            sql += " AND resource_type = ?"
            params.append(resource_type)
        
        if action:
            sql += " AND action = ?"
            params.append(action)
        
        if status:
            sql += " AND status = ?"
            params.append(status)
        
        if start_date:
            sql += " AND created_at >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            sql += " AND created_at <= ?"
            params.append(end_date.isoformat())
        
        result = self.db.execute_query(sql, params)
        return result[0]['total'] if result else 0
    
    def get_user_activity(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """الحصول على نشاط مستخدم معين"""
        start_date = datetime.now() - timedelta(days=days)
        
        # إجمالي العمليات
        total = self.count_audit_logs(user_id=user_id, start_date=start_date)
        
        # العمليات حسب النوع
        actions_result = self.db.execute_query(
            """SELECT action, COUNT(*) as count
               FROM audit_logs
               WHERE user_id = ? AND created_at >= ?
               GROUP BY action
               ORDER BY count DESC""",
            [user_id, start_date.isoformat()]
        )
        
        actions_by_type = {row['action']: row['count'] for row in actions_result}
        
        # الموارد المعدلة
        resources_result = self.db.execute_query(
            """SELECT resource_type, COUNT(*) as count
               FROM audit_logs
               WHERE user_id = ? AND created_at >= ?
               GROUP BY resource_type
               ORDER BY count DESC""",
            [user_id, start_date.isoformat()]
        )
        
        resources_modified = {row['resource_type']: row['count'] for row in resources_result}
        
        # نسبة النجاح
        success_count = self.count_audit_logs(user_id=user_id, start_date=start_date, status='success')
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        return {
            'total_actions': total,
            'actions_by_type': actions_by_type,
            'resources_modified': resources_modified,
            'success_rate': success_rate,
            'period_days': days
        }
    
    def get_resource_history(self, resource_type: str, resource_id: int,
                            limit: int = 50) -> List[AuditLog]:
        """سجل تاريخ مورد معين"""
        result = self.db.execute_query(
            """SELECT * FROM audit_logs
               WHERE resource_type = ? AND resource_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            [resource_type, resource_id, limit]
        )
        
        return [self._audit_log_from_row(row) for row in result]
    
    def _audit_log_from_row(self, row: Dict[str, Any]) -> AuditLog:
        """تحويل صف إلى كائن AuditLog"""
        return AuditLog(
            id=row['id'],
            user_id=row.get('user_id'),
            username=row['username'],
            action=row['action'],
            resource_type=row['resource_type'],
            resource_id=row.get('resource_id'),
            old_value=row.get('old_value', ''),
            new_value=row.get('new_value', ''),
            ip_address=row.get('ip_address', ''),
            user_agent=row.get('user_agent', ''),
            status=row.get('status', 'success'),
            error_message=row.get('error_message', ''),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None
        )
    
    # ==================== Login History ====================
    
    def log_login(self, user_id: Optional[int], username: str, status: str,
                  ip_address: str = "", user_agent: str = "",
                  failure_reason: str = "") -> int:
        """تسجيل محاولة تسجيل دخول"""
        
        return self.db.execute_update(
            """INSERT INTO login_history
               (user_id, username, status, ip_address, user_agent, failure_reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [user_id, username, status, ip_address, user_agent, failure_reason,
             datetime.now().isoformat()]
        )
    
    def get_login_history(self, user_id: Optional[int] = None,
                         status: Optional[str] = None,
                         days: int = 30,
                         limit: int = 100) -> List[LoginHistory]:
        """سجل تسجيل الدخول"""
        
        start_date = datetime.now() - timedelta(days=days)
        sql = "SELECT * FROM login_history WHERE created_at >= ?"
        params = [start_date.isoformat()]
        
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        if status:
            sql += " AND status = ?"
            params.append(status)
        
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        result = self.db.execute_query(sql, params)
        return [self._login_history_from_row(row) for row in result]
    
    def get_failed_login_attempts(self, username: str, hours: int = 24) -> int:
        """عدد محاولات الدخول الفاشلة"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        result = self.db.execute_query(
            """SELECT COUNT(*) as count FROM login_history
               WHERE username = ? AND status = 'failed' AND created_at >= ?""",
            [username, start_time.isoformat()]
        )
        
        return result[0]['count'] if result else 0
    
    def get_login_statistics(self, days: int = 30) -> Dict[str, Any]:
        """إحصائيات تسجيل الدخول"""
        start_date = datetime.now() - timedelta(days=days)
        
        # إجمالي المحاولات
        total_result = self.db.execute_query(
            "SELECT COUNT(*) as total FROM login_history WHERE created_at >= ?",
            [start_date.isoformat()]
        )
        total = total_result[0]['total'] if total_result else 0
        
        # المحاولات الناجحة والفاشلة
        status_result = self.db.execute_query(
            """SELECT status, COUNT(*) as count
               FROM login_history
               WHERE created_at >= ?
               GROUP BY status""",
            [start_date.isoformat()]
        )
        
        status_counts = {row['status']: row['count'] for row in status_result}
        
        # أكثر المستخدمين نشاطاً
        top_users_result = self.db.execute_query(
            """SELECT username, COUNT(*) as count
               FROM login_history
               WHERE created_at >= ? AND status = 'success'
               GROUP BY username
               ORDER BY count DESC
               LIMIT 10""",
            [start_date.isoformat()]
        )
        
        top_users = [(row['username'], row['count']) for row in top_users_result]
        
        # أكثر عناوين IP نشاطاً
        top_ips_result = self.db.execute_query(
            """SELECT ip_address, COUNT(*) as count
               FROM login_history
               WHERE created_at >= ? AND ip_address != ''
               GROUP BY ip_address
               ORDER BY count DESC
               LIMIT 10""",
            [start_date.isoformat()]
        )
        
        top_ips = [(row['ip_address'], row['count']) for row in top_ips_result]
        
        return {
            'total_attempts': total,
            'successful_logins': status_counts.get('success', 0),
            'failed_logins': status_counts.get('failed', 0),
            'success_rate': (status_counts.get('success', 0) / total * 100) if total > 0 else 0,
            'top_users': top_users,
            'top_ip_addresses': top_ips,
            'period_days': days
        }
    
    def _login_history_from_row(self, row: Dict[str, Any]) -> LoginHistory:
        """تحويل صف إلى كائن LoginHistory"""
        return LoginHistory(
            id=row['id'],
            user_id=row.get('user_id'),
            username=row['username'],
            status=row['status'],
            ip_address=row.get('ip_address', ''),
            user_agent=row.get('user_agent', ''),
            failure_reason=row.get('failure_reason', ''),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None
        )
    
    # ==================== Cleanup ====================
    
    def cleanup_old_logs(self, days: int = 90) -> int:
        """حذف السجلات القديمة"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # حذف سجلات التدقيق القديمة
        audit_deleted = self.db.execute_update(
            "DELETE FROM audit_logs WHERE created_at < ?",
            [cutoff_date.isoformat()]
        )
        
        # حذف سجلات تسجيل الدخول القديمة
        login_deleted = self.db.execute_update(
            "DELETE FROM login_history WHERE created_at < ?",
            [cutoff_date.isoformat()]
        )
        
        return audit_deleted + login_deleted

"""
Audit Log Service - Comprehensive Activity Tracking
خدمة سجل التدقيق - تتبع شامل للنشاطات
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

class AuditLogService:
    """خدمة سجل التدقيق الشامل"""
    
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or logging.getLogger(__name__)
    
    # ========================================================================
    # AUDIT LOGGING
    # ========================================================================
    
    def log_action(self, user_id: int, username: str, action: str, module: str,
                   entity_type: str = None, entity_id: int = None,
                   old_values: Dict = None, new_values: Dict = None,
                   ip_address: str = None, user_agent: str = None,
                   session_id: str = None, status: str = 'success',
                   error_message: str = None) -> int:
        """تسجيل نشاط في سجل التدقيق"""
        try:
            # Calculate changes summary
            changes_summary = self._compute_changes(old_values, new_values)
            
            # Convert dicts to JSON
            old_json = json.dumps(old_values, ensure_ascii=False) if old_values else None
            new_json = json.dumps(new_values, ensure_ascii=False) if new_values else None
            
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO audit_log (
                    user_id, username, action, module, entity_type, entity_id,
                    old_values, new_values, changes_summary,
                    ip_address, user_agent, session_id, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, username, action, module, entity_type, entity_id,
                old_json, new_json, changes_summary,
                ip_address, user_agent, session_id, status, error_message
            ))
            
            audit_id = cursor.lastrowid
            self.db.conn.commit()
            
            return audit_id
            
        except Exception as e:
            self.logger.error(f"Error logging audit: {e}")
            # Don't raise - audit logging should not break the main flow
            return 0
    
    def log_create(self, user_id: int, username: str, module: str,
                   entity_type: str, entity_id: int, values: Dict, **kwargs) -> int:
        """تسجيل عملية إنشاء"""
        return self.log_action(
            user_id=user_id,
            username=username,
            action='create',
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values=values,
            **kwargs
        )
    
    def log_update(self, user_id: int, username: str, module: str,
                   entity_type: str, entity_id: int, 
                   old_values: Dict, new_values: Dict, **kwargs) -> int:
        """تسجيل عملية تحديث"""
        return self.log_action(
            user_id=user_id,
            username=username,
            action='update',
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            **kwargs
        )
    
    def log_delete(self, user_id: int, username: str, module: str,
                   entity_type: str, entity_id: int, values: Dict, **kwargs) -> int:
        """تسجيل عملية حذف"""
        return self.log_action(
            user_id=user_id,
            username=username,
            action='delete',
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=values,
            **kwargs
        )
    
    def log_view(self, user_id: int, username: str, module: str,
                 entity_type: str = None, entity_id: int = None, **kwargs) -> int:
        """تسجيل عملية عرض"""
        return self.log_action(
            user_id=user_id,
            username=username,
            action='view',
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs
        )
    
    def log_export(self, user_id: int, username: str, module: str,
                   export_type: str, record_count: int, **kwargs) -> int:
        """تسجيل عملية تصدير"""
        return self.log_action(
            user_id=user_id,
            username=username,
            action='export',
            module=module,
            new_values={
                'export_type': export_type,
                'record_count': record_count
            },
            **kwargs
        )
    
    def log_login(self, user_id: int, username: str,
                  ip_address: str, user_agent: str,
                  session_id: str, status: str = 'success',
                  error_message: str = None) -> int:
        """تسجيل عملية تسجيل دخول"""
        return self.log_action(
            user_id=user_id,
            username=username,
            action='login',
            module='authentication',
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            status=status,
            error_message=error_message
        )
    
    def log_logout(self, user_id: int, username: str,
                   session_id: str, **kwargs) -> int:
        """تسجيل عملية تسجيل خروج"""
        return self.log_action(
            user_id=user_id,
            username=username,
            action='logout',
            module='authentication',
            session_id=session_id,
            **kwargs
        )
    
    # ========================================================================
    # QUERY AND SEARCH
    # ========================================================================
    
    def get_audit_log(self, audit_id: int) -> Optional[Dict]:
        """الحصول على سجل تدقيق محدد"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT audit_id, user_id, username, action, module,
                   entity_type, entity_id, old_values, new_values, changes_summary,
                   ip_address, user_agent, session_id, status, error_message, timestamp
            FROM audit_log
            WHERE audit_id = ?
        ''', (audit_id,))
        
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None
    
    def search_audit_logs(self, user_id: int = None, username: str = None,
                         action: str = None, module: str = None,
                         entity_type: str = None, entity_id: int = None,
                         status: str = None, start_date: datetime = None,
                         end_date: datetime = None, limit: int = 100,
                         offset: int = 0) -> Tuple[List[Dict], int]:
        """البحث في سجلات التدقيق"""
        conditions = []
        params = []
        
        if user_id:
            conditions.append('user_id = ?')
            params.append(user_id)
        
        if username:
            conditions.append('username LIKE ?')
            params.append(f'%{username}%')
        
        if action:
            conditions.append('action = ?')
            params.append(action)
        
        if module:
            conditions.append('module = ?')
            params.append(module)
        
        if entity_type:
            conditions.append('entity_type = ?')
            params.append(entity_type)
        
        if entity_id:
            conditions.append('entity_id = ?')
            params.append(entity_id)
        
        if status:
            conditions.append('status = ?')
            params.append(status)
        
        if start_date:
            conditions.append('timestamp >= ?')
            params.append(start_date.isoformat())
        
        if end_date:
            conditions.append('timestamp <= ?')
            params.append(end_date.isoformat())
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        # Get total count
        cursor = self.db.conn.cursor()
        cursor.execute(f'''
            SELECT COUNT(*)
            FROM audit_log
            WHERE {where_clause}
        ''', params)
        total = cursor.fetchone()[0]
        
        # Get records
        cursor.execute(f'''
            SELECT audit_id, user_id, username, action, module,
                   entity_type, entity_id, old_values, new_values, changes_summary,
                   ip_address, user_agent, session_id, status, error_message, timestamp
            FROM audit_log
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', params + [limit, offset])
        
        logs = [self._row_to_dict(row) for row in cursor.fetchall()]
        
        return logs, total
    
    def get_user_activity(self, user_id: int, days: int = 30) -> List[Dict]:
        """الحصول على نشاط مستخدم"""
        start_date = datetime.now() - timedelta(days=days)
        logs, _ = self.search_audit_logs(
            user_id=user_id,
            start_date=start_date,
            limit=1000
        )
        return logs
    
    def get_entity_history(self, entity_type: str, entity_id: int) -> List[Dict]:
        """الحصول على تاريخ كيان"""
        logs, _ = self.search_audit_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=1000
        )
        return logs
    
    def get_recent_activity(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """الحصول على النشاط الأخير"""
        start_date = datetime.now() - timedelta(hours=hours)
        logs, _ = self.search_audit_logs(
            start_date=start_date,
            limit=limit
        )
        return logs
    
    # ========================================================================
    # STATISTICS AND ANALYTICS
    # ========================================================================
    
    def get_user_statistics(self, user_id: int, days: int = 30) -> Dict:
        """إحصائيات نشاط مستخدم"""
        cursor = self.db.conn.cursor()
        start_date = datetime.now() - timedelta(days=days)
        
        stats = {}
        
        # Total actions
        cursor.execute('''
            SELECT COUNT(*) FROM audit_log
            WHERE user_id = ? AND timestamp >= ?
        ''', (user_id, start_date))
        stats['total_actions'] = cursor.fetchone()[0]
        
        # Actions by type
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM audit_log
            WHERE user_id = ? AND timestamp >= ?
            GROUP BY action
            ORDER BY count DESC
        ''', (user_id, start_date))
        stats['actions_by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Actions by module
        cursor.execute('''
            SELECT module, COUNT(*) as count
            FROM audit_log
            WHERE user_id = ? AND timestamp >= ?
            GROUP BY module
            ORDER BY count DESC
        ''', (user_id, start_date))
        stats['actions_by_module'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Success rate
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) * 100
            FROM audit_log
            WHERE user_id = ? AND timestamp >= ?
        ''', (user_id, start_date))
        stats['success_rate'] = round(cursor.fetchone()[0] or 0, 2)
        
        # Most active day
        cursor.execute('''
            SELECT date(timestamp) as day, COUNT(*) as count
            FROM audit_log
            WHERE user_id = ? AND timestamp >= ?
            GROUP BY day
            ORDER BY count DESC
            LIMIT 1
        ''', (user_id, start_date))
        row = cursor.fetchone()
        stats['most_active_day'] = {
            'date': row[0] if row else None,
            'count': row[1] if row else 0
        }
        
        return stats
    
    def get_module_statistics(self, module: str, days: int = 30) -> Dict:
        """إحصائيات وحدة"""
        cursor = self.db.conn.cursor()
        start_date = datetime.now() - timedelta(days=days)
        
        stats = {}
        
        # Total actions
        cursor.execute('''
            SELECT COUNT(*) FROM audit_log
            WHERE module = ? AND timestamp >= ?
        ''', (module, start_date))
        stats['total_actions'] = cursor.fetchone()[0]
        
        # Top users
        cursor.execute('''
            SELECT username, COUNT(*) as count
            FROM audit_log
            WHERE module = ? AND timestamp >= ?
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 5
        ''', (module, start_date))
        stats['top_users'] = [
            {'username': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]
        
        # Actions breakdown
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM audit_log
            WHERE module = ? AND timestamp >= ?
            GROUP BY action
        ''', (module, start_date))
        stats['actions'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        return stats
    
    def get_daily_summary(self, days: int = 7) -> List[Dict]:
        """ملخص يومي"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT 
                date(timestamp) as date,
                COUNT(*) as total,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM audit_log
            WHERE timestamp >= date('now', ? || ' days')
            GROUP BY date(timestamp)
            ORDER BY date DESC
        ''', (f'-{days}',))
        
        summary = []
        for row in cursor.fetchall():
            summary.append({
                'date': row[0],
                'total_actions': row[1],
                'unique_users': row[2],
                'successful': row[3],
                'failed': row[4],
                'success_rate': round(row[3] * 100.0 / row[1], 2) if row[1] > 0 else 0
            })
        
        return summary
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    def create_session(self, user_id: int, session_id: str,
                      ip_address: str = None, user_agent: str = None) -> bool:
        """إنشاء جلسة مستخدم"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO user_sessions (session_id, user_id, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (session_id, user_id, ip_address, user_agent))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            return False
    
    def end_session(self, session_id: str) -> bool:
        """إنهاء جلسة"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                UPDATE user_sessions
                SET logout_time = CURRENT_TIMESTAMP, is_active = 0
                WHERE session_id = ?
            ''', (session_id,))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error ending session: {e}")
            return False
    
    def get_active_sessions(self, user_id: int = None) -> List[Dict]:
        """الحصول على الجلسات النشطة"""
        cursor = self.db.conn.cursor()
        
        if user_id:
            cursor.execute('SELECT * FROM v_active_sessions WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('SELECT * FROM v_active_sessions')
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row[0],
                'user_id': row[1],
                'username': row[2],
                'full_name': row[3],
                'login_time': row[4],
                'last_activity': row[5],
                'ip_address': row[6],
                'user_agent': row[7],
                'idle_minutes': row[8]
            })
        
        return sessions
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _compute_changes(self, old_values: Dict, new_values: Dict) -> str:
        """حساب ملخص التغييرات"""
        if not old_values or not new_values:
            return None
        
        changes = []
        all_keys = set(old_values.keys()) | set(new_values.keys())
        
        for key in sorted(all_keys):
            old_val = old_values.get(key)
            new_val = new_values.get(key)
            
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")
        
        return '; '.join(changes) if changes else None
    
    def _row_to_dict(self, row) -> Dict:
        """تحويل صف إلى قاموس"""
        return {
            'audit_id': row[0],
            'user_id': row[1],
            'username': row[2],
            'action': row[3],
            'module': row[4],
            'entity_type': row[5],
            'entity_id': row[6],
            'old_values': json.loads(row[7]) if row[7] else None,
            'new_values': json.loads(row[8]) if row[8] else None,
            'changes_summary': row[9],
            'ip_address': row[10],
            'user_agent': row[11],
            'session_id': row[12],
            'status': row[13],
            'error_message': row[14],
            'timestamp': row[15]
        }
    
    def cleanup_old_logs(self, days: int = 365) -> int:
        """تنظيف السجلات القديمة"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor = self.db.conn.cursor()
            cursor.execute('''
                DELETE FROM audit_log
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            deleted = cursor.rowcount
            self.db.conn.commit()
            
            self.logger.info(f"Cleaned up {deleted} old audit logs")
            return deleted
            
        except Exception as e:
            self.logger.error(f"Error cleaning up logs: {e}")
            return 0

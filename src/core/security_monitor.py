#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Monitor - مراقب الأمان
مراقبة الأحداث الأمنية والتنبيهات
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """أنواع الأحداث الأمنية"""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    BRUTE_FORCE_ATTEMPT = "BRUTE_FORCE_ATTEMPT"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    DATA_EXPORT = "DATA_EXPORT"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"


class SecurityEventSeverity(Enum):
    """خطورة الحدث الأمني"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityEvent:
    """حدث أمني"""
    id: Optional[int] = None
    event_type: str = ""
    severity: str = SecurityEventSeverity.MEDIUM.value
    user_id: Optional[int] = None
    username: str = ""
    description: str = ""
    ip_address: str = ""
    user_agent: str = ""
    metadata: str = ""  # JSON
    timestamp: Optional[datetime] = None
    company_id: Optional[int] = None


class SecurityMonitor:
    """مراقب الأمان"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة مراقب الأمان
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
        
        self._create_tables()
    
    def _create_tables(self):
        """إنشاء جداول مراقبة الأمان"""
        try:
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'MEDIUM',
                    user_id INTEGER,
                    username TEXT,
                    description TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    company_id INTEGER,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            """)
            
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_security_events_type 
                ON security_events(event_type)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_security_events_severity 
                ON security_events(severity)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_security_events_timestamp 
                ON security_events(timestamp)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_security_events_user 
                ON security_events(user_id)
            """)
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء جداول مراقبة الأمان: {e}", exc_info=True)
    
    def log_event(
        self,
        event_type: str,
        description: str,
        severity: str = SecurityEventSeverity.MEDIUM.value,
        user_id: Optional[int] = None,
        username: str = "",
        ip_address: str = "",
        user_agent: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        تسجيل حدث أمني
        
        Args:
            event_type: نوع الحدث
            description: وصف الحدث
            severity: خطورة الحدث
            user_id: معرف المستخدم
            username: اسم المستخدم
            ip_address: عنوان IP
            user_agent: User Agent
            metadata: بيانات إضافية (Dict)
            
        Returns:
            معرف الحدث أو None
        """
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                INSERT INTO security_events (
                    event_type, severity, user_id, username,
                    description, ip_address, user_agent, metadata,
                    company_id, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            metadata_json = json.dumps(metadata, ensure_ascii=False, default=str) if metadata else ""
            
            values = (
                event_type, severity, user_id, username,
                description, ip_address, user_agent, metadata_json,
                company_id, datetime.now().isoformat()
            )
            
            result = self.db_manager.execute_query(query, values)
            if result:
                event_id = result.lastrowid
                self.logger.info(f"✅ تم تسجيل حدث أمني: {event_type} (ID: {event_id})")
                
                # إرسال تنبيه للحدث عالي الخطورة
                if severity in [SecurityEventSeverity.HIGH.value, SecurityEventSeverity.CRITICAL.value]:
                    self._send_alert(event_id, event_type, severity, description)
                
                return event_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تسجيل حدث أمني: {e}", exc_info=True)
            return None
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """
        الحصول على الأحداث الأمنية
        
        Args:
            event_type: نوع الحدث (فلتر)
            severity: خطورة الحدث (فلتر)
            user_id: معرف المستخدم (فلتر)
            start_date: تاريخ البداية (فلتر)
            end_date: تاريخ النهاية (فلتر)
            limit: الحد الأقصى للنتائج
            
        Returns:
            List من SecurityEvent
        """
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "SELECT * FROM security_events WHERE 1=1"
            params = []
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_event(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على الأحداث الأمنية: {e}", exc_info=True)
            return []
    
    def get_security_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        الحصول على ملخص الأمان
        
        Args:
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            
        Returns:
            Dict مع الملخص
        """
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()
            
            events = self.get_events(start_date=start_date, end_date=end_date, limit=1000)
            
            summary = {
                "total_events": len(events),
                "by_type": {},
                "by_severity": {
                    "CRITICAL": 0,
                    "HIGH": 0,
                    "MEDIUM": 0,
                    "LOW": 0
                },
                "failed_logins": 0,
                "suspicious_activities": 0,
                "unauthorized_access": 0
            }
            
            for event in events:
                # حسب النوع
                event_type = event.event_type
                summary["by_type"][event_type] = summary["by_type"].get(event_type, 0) + 1
                
                # حسب الخطورة
                severity = event.severity
                if severity in summary["by_severity"]:
                    summary["by_severity"][severity] += 1
                
                # إحصائيات خاصة
                if event_type == SecurityEventType.LOGIN_FAILED.value:
                    summary["failed_logins"] += 1
                elif event_type == SecurityEventType.SUSPICIOUS_ACTIVITY.value:
                    summary["suspicious_activities"] += 1
                elif event_type == SecurityEventType.UNAUTHORIZED_ACCESS.value:
                    summary["unauthorized_access"] += 1
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على ملخص الأمان: {e}", exc_info=True)
            return {}
    
    def _send_alert(self, event_id: int, event_type: str, severity: str, description: str):
        """إرسال تنبيه للحدث عالي الخطورة"""
        try:
            # TODO: إرسال تنبيه عبر البريد الإلكتروني أو نظام الإشعارات
            self.logger.warning(f"🚨 تنبيه أمني [{severity}]: {event_type} - {description}")
        except Exception as e:
            self.logger.error(f"❌ خطأ في إرسال التنبيه: {e}", exc_info=True)
    
    def _row_to_event(self, row: Dict[str, Any]) -> SecurityEvent:
        """تحويل صف قاعدة البيانات إلى SecurityEvent"""
        return SecurityEvent(
            id=row.get("id"),
            event_type=row.get("event_type", ""),
            severity=row.get("severity", SecurityEventSeverity.MEDIUM.value),
            user_id=row.get("user_id"),
            username=row.get("username", ""),
            description=row.get("description", ""),
            ip_address=row.get("ip_address", ""),
            user_agent=row.get("user_agent", ""),
            metadata=row.get("metadata", ""),
            timestamp=self._parse_datetime(row.get("timestamp")),
            company_id=row.get("company_id")
        )
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """تحليل datetime من قاعدة البيانات"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except:
                    return None
        return None


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intrusion Detection System - نظام كشف التسلل
كشف محاولات التسلل والهجمات الأمنية
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


class ThreatType(Enum):
    """أنواع التهديدات"""
    BRUTE_FORCE = "BRUTE_FORCE"
    SQL_INJECTION = "SQL_INJECTION"
    XSS_ATTACK = "XSS_ATTACK"
    CSRF_ATTACK = "CSRF_ATTACK"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    SUSPICIOUS_PATTERN = "SUSPICIOUS_PATTERN"


class ThreatLevel(Enum):
    """مستوى التهديد"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Threat:
    """تهديد أمني"""
    id: Optional[int] = None
    threat_type: str = ""
    threat_level: str = ThreatLevel.MEDIUM.value
    source_ip: str = ""
    user_id: Optional[int] = None
    description: str = ""
    detected_at: Optional[datetime] = None
    blocked: bool = False
    metadata: str = ""  # JSON
    company_id: Optional[int] = None


class IntrusionDetectionSystem:
    """نظام كشف التسلل"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة نظام كشف التسلل
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
        
        self._create_tables()
        
        # قائمة IPs المحظورة
        self._blocked_ips: Dict[str, datetime] = {}
        
        # عتبات الكشف
        self.brute_force_threshold = 5  # عدد محاولات تسجيل الدخول الفاشلة
        self.brute_force_window = 300  # نافذة الوقت بالثواني (5 دقائق)
    
    def _create_tables(self):
        """إنشاء جداول كشف التسلل"""
        try:
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS security_threats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    threat_type TEXT NOT NULL,
                    threat_level TEXT NOT NULL DEFAULT 'MEDIUM',
                    source_ip TEXT NOT NULL,
                    user_id INTEGER,
                    description TEXT NOT NULL,
                    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    blocked INTEGER DEFAULT 0,
                    metadata TEXT,
                    company_id INTEGER,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            """)
            
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL UNIQUE,
                    reason TEXT,
                    blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    company_id INTEGER,
                    
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            """)
            
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_threats_ip 
                ON security_threats(source_ip)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_threats_type 
                ON security_threats(threat_type)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip 
                ON blocked_ips(ip_address)
            """)
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء جداول كشف التسلل: {e}", exc_info=True)
    
    def detect_brute_force(self, ip_address: str, username: str = "") -> Optional[Threat]:
        """
        كشف هجمات Brute Force
        
        Args:
            ip_address: عنوان IP
            username: اسم المستخدم (اختياري)
            
        Returns:
            Threat إذا تم اكتشاف هجوم، None خلاف ذلك
        """
        try:
            # حساب عدد محاولات تسجيل الدخول الفاشلة في النافذة الزمنية
            window_start = datetime.now() - timedelta(seconds=self.brute_force_window)
            
            query = """
                SELECT COUNT(*) as count
                FROM security_events
                WHERE event_type = 'LOGIN_FAILED'
                    AND ip_address = ?
                    AND timestamp >= ?
            """
            
            row = self.db_manager.fetch_one(query, (ip_address, window_start.isoformat()))
            failed_attempts = row['count'] if row else 0
            
            if failed_attempts >= self.brute_force_threshold:
                # تم اكتشاف هجوم Brute Force
                threat = Threat(
                    threat_type=ThreatType.BRUTE_FORCE.value,
                    threat_level=ThreatLevel.HIGH.value,
                    source_ip=ip_address,
                    description=f"تم اكتشاف {failed_attempts} محاولة تسجيل دخول فاشلة من {ip_address}",
                    detected_at=datetime.now(),
                    blocked=True
                )
                
                threat_id = self._save_threat(threat)
                if threat_id:
                    threat.id = threat_id
                    
                    # حظر IP تلقائياً
                    self.block_ip(ip_address, f"Brute Force Attack ({failed_attempts} attempts)")
                    
                    self.logger.warning(f"🚨 تم اكتشاف هجوم Brute Force من {ip_address}")
                    return threat
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في كشف Brute Force: {e}", exc_info=True)
            return None
    
    def detect_sql_injection(self, query_string: str, ip_address: str) -> Optional[Threat]:
        """
        كشف محاولات SQL Injection
        
        Args:
            query_string: سلسلة الاستعلام
            ip_address: عنوان IP
            
        Returns:
            Threat إذا تم اكتشاف هجوم، None خلاف ذلك
        """
        try:
            # قائمة بأنماط SQL Injection الشائعة
            sql_patterns = [
                "'; DROP",
                "'; DELETE",
                "'; UPDATE",
                "'; INSERT",
                "'; SELECT",
                "UNION SELECT",
                "OR 1=1",
                "OR '1'='1",
                "' OR '1'='1",
                "'; --",
                "'; /*",
                "xp_cmdshell",
                "exec(",
                "eval("
            ]
            
            query_lower = query_string.lower()
            
            for pattern in sql_patterns:
                if pattern.lower() in query_lower:
                    threat = Threat(
                        threat_type=ThreatType.SQL_INJECTION.value,
                        threat_level=ThreatLevel.CRITICAL.value,
                        source_ip=ip_address,
                        description=f"تم اكتشاف محاولة SQL Injection: {pattern}",
                        detected_at=datetime.now(),
                        blocked=True,
                        metadata=json.dumps({"query": query_string[:200]}, ensure_ascii=False)
                    )
                    
                    threat_id = self._save_threat(threat)
                    if threat_id:
                        threat.id = threat_id
                        self.block_ip(ip_address, "SQL Injection Attempt")
                        self.logger.critical(f"🚨 تم اكتشاف محاولة SQL Injection من {ip_address}")
                        return threat
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في كشف SQL Injection: {e}", exc_info=True)
            return None
    
    def detect_xss_attack(self, input_string: str, ip_address: str) -> Optional[Threat]:
        """
        كشف محاولات XSS
        
        Args:
            input_string: السلسلة المدخلة
            ip_address: عنوان IP
            
        Returns:
            Threat إذا تم اكتشاف هجوم، None خلاف ذلك
        """
        try:
            # قائمة بأنماط XSS الشائعة
            xss_patterns = [
                "<script",
                "javascript:",
                "onerror=",
                "onload=",
                "onclick=",
                "onmouseover=",
                "eval(",
                "alert(",
                "document.cookie",
                "<iframe",
                "<img src="
            ]
            
            input_lower = input_string.lower()
            
            for pattern in xss_patterns:
                if pattern.lower() in input_lower:
                    threat = Threat(
                        threat_type=ThreatType.XSS_ATTACK.value,
                        threat_level=ThreatLevel.HIGH.value,
                        source_ip=ip_address,
                        description=f"تم اكتشاف محاولة XSS: {pattern}",
                        detected_at=datetime.now(),
                        blocked=False,  # قد لا نحتاج لحظر IP فوراً
                        metadata=json.dumps({"input": input_string[:200]}, ensure_ascii=False)
                    )
                    
                    threat_id = self._save_threat(threat)
                    if threat_id:
                        threat.id = threat_id
                        self.logger.warning(f"🚨 تم اكتشاف محاولة XSS من {ip_address}")
                        return threat
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في كشف XSS: {e}", exc_info=True)
            return None
    
    def block_ip(self, ip_address: str, reason: str = "", duration_hours: int = 24) -> bool:
        """
        حظر عنوان IP
        
        Args:
            ip_address: عنوان IP
            reason: سبب الحظر
            duration_hours: مدة الحظر بالساعات
            
        Returns:
            True إذا نجح الحظر
        """
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            expires_at = datetime.now() + timedelta(hours=duration_hours)
            
            query = """
                INSERT OR REPLACE INTO blocked_ips (
                    ip_address, reason, blocked_at, expires_at, company_id
                ) VALUES (?, ?, ?, ?, ?)
            """
            
            result = self.db_manager.execute_query(query, (
                ip_address, reason, datetime.now().isoformat(),
                expires_at.isoformat(), company_id
            ))
            
            if result:
                self._blocked_ips[ip_address] = expires_at
                self.logger.info(f"✅ تم حظر IP: {ip_address} ({reason})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حظر IP: {e}", exc_info=True)
            return False
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """
        التحقق من حظر IP
        
        Args:
            ip_address: عنوان IP
            
        Returns:
            True إذا كان محظوراً
        """
        try:
            # التحقق من الذاكرة أولاً
            if ip_address in self._blocked_ips:
                expires_at = self._blocked_ips[ip_address]
                if datetime.now() < expires_at:
                    return True
                else:
                    # انتهت مدة الحظر
                    del self._blocked_ips[ip_address]
            
            # التحقق من قاعدة البيانات
            query = """
                SELECT expires_at FROM blocked_ips
                WHERE ip_address = ? AND (expires_at IS NULL OR expires_at > ?)
            """
            
            row = self.db_manager.fetch_one(query, (ip_address, datetime.now().isoformat()))
            if row:
                expires_at = self._parse_datetime(row.get("expires_at"))
                if expires_at:
                    self._blocked_ips[ip_address] = expires_at
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في التحقق من حظر IP: {e}", exc_info=True)
            return False
    
    def get_threats(
        self,
        threat_type: Optional[str] = None,
        threat_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Threat]:
        """الحصول على التهديدات المكتشفة"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "SELECT * FROM security_threats WHERE 1=1"
            params = []
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            if threat_type:
                query += " AND threat_type = ?"
                params.append(threat_type)
            
            if threat_level:
                query += " AND threat_level = ?"
                params.append(threat_level)
            
            if start_date:
                query += " AND detected_at >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND detected_at <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY detected_at DESC LIMIT ?"
            params.append(limit)
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_threat(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على التهديدات: {e}", exc_info=True)
            return []
    
    def _save_threat(self, threat: Threat) -> Optional[int]:
        """حفظ تهديد"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                INSERT INTO security_threats (
                    threat_type, threat_level, source_ip, user_id,
                    description, detected_at, blocked, metadata, company_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                threat.threat_type, threat.threat_level, threat.source_ip,
                threat.user_id, threat.description,
                threat.detected_at.isoformat() if threat.detected_at else None,
                1 if threat.blocked else 0,
                threat.metadata, company_id
            )
            
            result = self.db_manager.execute_query(query, values)
            if result:
                return result.lastrowid
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حفظ تهديد: {e}", exc_info=True)
            return None
    
    def _row_to_threat(self, row: Dict[str, Any]) -> Threat:
        """تحويل صف قاعدة البيانات إلى Threat"""
        return Threat(
            id=row.get("id"),
            threat_type=row.get("threat_type", ""),
            threat_level=row.get("threat_level", ThreatLevel.MEDIUM.value),
            source_ip=row.get("source_ip", ""),
            user_id=row.get("user_id"),
            description=row.get("description", ""),
            detected_at=self._parse_datetime(row.get("detected_at")),
            blocked=bool(row.get("blocked", 0)),
            metadata=row.get("metadata", ""),
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


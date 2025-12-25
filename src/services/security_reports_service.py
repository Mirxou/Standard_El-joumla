#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Reports Service - خدمة تقارير الأمان
توليد تقارير الأمان المتقدمة
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.security_monitor import SecurityMonitor, SecurityEventType, SecurityEventSeverity
from src.core.intrusion_detection import IntrusionDetectionSystem, ThreatType, ThreatLevel
from src.services.sso_service import SSOService

logger = logging.getLogger(__name__)


class SecurityReportsService:
    """خدمة تقارير الأمان"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة تقارير الأمان
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.security_monitor = SecurityMonitor(db_manager, logger_instance)
        self.intrusion_detection = IntrusionDetectionSystem(db_manager, logger_instance)
        self.sso_service = SSOService(db_manager, logger_instance)
    
    def generate_security_summary_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        توليد تقرير ملخص الأمان
        
        Args:
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            
        Returns:
            Dict مع بيانات التقرير
        """
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # جمع البيانات
            security_summary = self.security_monitor.get_security_summary(start_date, end_date)
            threats = self.intrusion_detection.get_threats(start_date=start_date, end_date=end_date, limit=100)
            
            report_data = {
                "report_type": "SECURITY_SUMMARY",
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "security_events": security_summary,
                "threats": {
                    "total": len(threats),
                    "by_type": self._group_threats_by_type(threats),
                    "by_level": self._group_threats_by_level(threats),
                    "blocked_ips": len([t for t in threats if t.blocked])
                },
                "sso_providers": {
                    "total": len(self.sso_service.get_all_providers()),
                    "enabled": len([p for p in self.sso_service.get_all_providers() if p.enabled])
                },
                "recommendations": self._generate_recommendations(security_summary, threats)
            }
            
            return {
                "success": True,
                "data": report_data
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في توليد تقرير ملخص الأمان: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def generate_security_events_report(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 500
    ) -> Dict[str, Any]:
        """توليد تقرير الأحداث الأمنية"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            events = self.security_monitor.get_events(
                event_type=event_type,
                severity=severity,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            report_data = {
                "report_type": "SECURITY_EVENTS",
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_events": len(events),
                "events": [
                    {
                        "id": event.id,
                        "event_type": event.event_type,
                        "severity": event.severity,
                        "username": event.username,
                        "description": event.description,
                        "ip_address": event.ip_address,
                        "timestamp": event.timestamp.isoformat() if event.timestamp else None
                    }
                    for event in events
                ],
                "by_type": self._group_events_by_type(events),
                "by_severity": self._group_events_by_severity(events),
                "by_user": self._group_events_by_user(events)
            }
            
            return {
                "success": True,
                "data": report_data
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في توليد تقرير الأحداث الأمنية: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def generate_threats_report(
        self,
        threat_type: Optional[str] = None,
        threat_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 500
    ) -> Dict[str, Any]:
        """توليد تقرير التهديدات"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            threats = self.intrusion_detection.get_threats(
                threat_type=threat_type,
                threat_level=threat_level,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            report_data = {
                "report_type": "SECURITY_THREATS",
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_threats": len(threats),
                "threats": [
                    {
                        "id": threat.id,
                        "threat_type": threat.threat_type,
                        "threat_level": threat.threat_level,
                        "source_ip": threat.source_ip,
                        "description": threat.description,
                        "blocked": threat.blocked,
                        "detected_at": threat.detected_at.isoformat() if threat.detected_at else None
                    }
                    for threat in threats
                ],
                "by_type": self._group_threats_by_type(threats),
                "by_level": self._group_threats_by_level(threats),
                "blocked_ips": len([t for t in threats if t.blocked])
            }
            
            return {
                "success": True,
                "data": report_data
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في توليد تقرير التهديدات: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def generate_login_activity_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """توليد تقرير نشاط تسجيل الدخول"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # الأحداث المتعلقة بتسجيل الدخول
            login_events = self.security_monitor.get_events(
                event_type=SecurityEventType.LOGIN_SUCCESS.value,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            failed_login_events = self.security_monitor.get_events(
                event_type=SecurityEventType.LOGIN_FAILED.value,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            report_data = {
                "report_type": "LOGIN_ACTIVITY",
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "successful_logins": {
                    "total": len(login_events),
                    "by_user": self._group_events_by_user(login_events),
                    "by_ip": self._group_events_by_ip(login_events),
                    "events": [
                        {
                            "username": e.username,
                            "ip_address": e.ip_address,
                            "timestamp": e.timestamp.isoformat() if e.timestamp else None
                        }
                        for e in login_events
                    ]
                },
                "failed_logins": {
                    "total": len(failed_login_events),
                    "by_user": self._group_events_by_user(failed_login_events),
                    "by_ip": self._group_events_by_ip(failed_login_events),
                    "events": [
                        {
                            "username": e.username,
                            "ip_address": e.ip_address,
                            "timestamp": e.timestamp.isoformat() if e.timestamp else None
                        }
                        for e in failed_login_events
                    ]
                },
                "login_success_rate": (len(login_events) / (len(login_events) + len(failed_login_events)) * 100) if (login_events or failed_login_events) else 0
            }
            
            return {
                "success": True,
                "data": report_data
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في توليد تقرير نشاط تسجيل الدخول: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def generate_ip_blocking_report(self) -> Dict[str, Any]:
        """توليد تقرير حظر IP"""
        try:
            query = """
                SELECT * FROM blocked_ips
                WHERE expires_at IS NULL OR expires_at > ?
                ORDER BY blocked_at DESC
            """
            
            rows = self.db_manager.fetch_all(query, (datetime.now().isoformat(),))
            
            report_data = {
                "report_type": "IP_BLOCKING",
                "generated_at": datetime.now().isoformat(),
                "total_blocked_ips": len(rows),
                "blocked_ips": [
                    {
                        "ip_address": row.get("ip_address"),
                        "reason": row.get("reason"),
                        "blocked_at": row.get("blocked_at"),
                        "expires_at": row.get("expires_at")
                    }
                    for row in rows
                ]
            }
            
            return {
                "success": True,
                "data": report_data
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في توليد تقرير حظر IP: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def _group_threats_by_type(self, threats: List) -> Dict[str, int]:
        """تجميع التهديدات حسب النوع"""
        by_type = {}
        for threat in threats:
            threat_type = threat.threat_type
            by_type[threat_type] = by_type.get(threat_type, 0) + 1
        return by_type
    
    def _group_threats_by_level(self, threats: List) -> Dict[str, int]:
        """تجميع التهديدات حسب المستوى"""
        by_level = {}
        for threat in threats:
            threat_level = threat.threat_level
            by_level[threat_level] = by_level.get(threat_level, 0) + 1
        return by_level
    
    def _group_events_by_type(self, events: List) -> Dict[str, int]:
        """تجميع الأحداث حسب النوع"""
        by_type = {}
        for event in events:
            event_type = event.event_type
            by_type[event_type] = by_type.get(event_type, 0) + 1
        return by_type
    
    def _group_events_by_severity(self, events: List) -> Dict[str, int]:
        """تجميع الأحداث حسب الخطورة"""
        by_severity = {}
        for event in events:
            severity = event.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1
        return by_severity
    
    def _group_events_by_user(self, events: List) -> Dict[str, int]:
        """تجميع الأحداث حسب المستخدم"""
        by_user = {}
        for event in events:
            username = event.username or "Unknown"
            by_user[username] = by_user.get(username, 0) + 1
        return by_user
    
    def _group_events_by_ip(self, events: List) -> Dict[str, int]:
        """تجميع الأحداث حسب IP"""
        by_ip = {}
        for event in events:
            ip_address = event.ip_address or "Unknown"
            by_ip[ip_address] = by_ip.get(ip_address, 0) + 1
        return by_ip
    
    def _generate_recommendations(self, security_summary: Dict[str, Any], threats: List) -> List[str]:
        """توليد توصيات أمنية"""
        recommendations = []
        
        # تحليل البيانات وتوليد التوصيات
        if security_summary.get("failed_logins", 0) > 50:
            recommendations.append("عدد كبير من محاولات تسجيل الدخول الفاشلة. يُنصح بمراجعة سياسات كلمات المرور.")
        
        if security_summary.get("suspicious_activities", 0) > 10:
            recommendations.append("تم اكتشاف أنشطة مشبوهة. يُنصح بمراجعة سجلات الأمان.")
        
        if security_summary.get("unauthorized_access", 0) > 0:
            recommendations.append("تم اكتشاف محاولات وصول غير مصرح بها. يُنصح بمراجعة الصلاحيات.")
        
        critical_threats = [t for t in threats if t.threat_level == ThreatLevel.CRITICAL.value]
        if len(critical_threats) > 0:
            recommendations.append(f"تم اكتشاف {len(critical_threats)} تهديد حرج. يُنصح باتخاذ إجراءات فورية.")
        
        if not recommendations:
            recommendations.append("لا توجد توصيات أمنية حالياً. الوضع الأمني جيد.")
        
        return recommendations


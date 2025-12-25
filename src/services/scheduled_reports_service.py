#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduled Reports Service - خدمة التقارير المجدولة
جدولة التقارير التلقائية وإرسالها
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
from src.services.analytics_service import AnalyticsService
from src.services.report_exporter import ReportExporter, ReportType, ExportFormat

logger = logging.getLogger(__name__)


class ScheduleFrequency(Enum):
    """تكرار الجدولة"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


@dataclass
class ScheduledReport:
    """تقرير مجدول"""
    id: Optional[int] = None
    name: str = ""
    report_type: str = ""  # SALES, INVENTORY, FINANCIAL, CUSTOM
    frequency: str = ScheduleFrequency.DAILY.value
    schedule_time: str = "09:00"  # HH:MM
    schedule_day: Optional[int] = None  # 1-7 for weekly, 1-31 for monthly
    recipients: str = ""  # JSON list of emails
    export_format: str = ExportFormat.PDF.value
    filters: str = ""  # JSON filters
    is_active: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    company_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ScheduledReportsService:
    """خدمة التقارير المجدولة"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة التقارير المجدولة
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
        self.analytics_service = AnalyticsService(db_manager, logger_instance)
        self.report_exporter = ReportExporter(db_manager)
        
        # إنشاء الجدول إذا لم يكن موجوداً
        self._create_table()
    
    def _create_table(self):
        """إنشاء جدول التقارير المجدولة"""
        try:
            query = """
                CREATE TABLE IF NOT EXISTS scheduled_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    schedule_time TEXT NOT NULL,
                    schedule_day INTEGER,
                    recipients TEXT,
                    export_format TEXT NOT NULL DEFAULT 'PDF',
                    filters TEXT,
                    is_active INTEGER DEFAULT 1,
                    last_run_at DATETIME,
                    next_run_at DATETIME,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """
            self.db_manager.execute_query(query)
            
            # إنشاء Indexes
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_scheduled_reports_company 
                ON scheduled_reports(company_id)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_scheduled_reports_active 
                ON scheduled_reports(is_active)
            """)
            self.db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_scheduled_reports_next_run 
                ON scheduled_reports(next_run_at)
            """)
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء جدول التقارير المجدولة: {e}", exc_info=True)
    
    # ============================================================================
    # CRUD Operations
    # ============================================================================
    
    def create_scheduled_report(self, report: ScheduledReport) -> Optional[int]:
        """إنشاء تقرير مجدول"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            # حساب next_run_at
            next_run = self._calculate_next_run(
                report.frequency,
                report.schedule_time,
                report.schedule_day
            )
            
            query = """
                INSERT INTO scheduled_reports (
                    name, report_type, frequency, schedule_time, schedule_day,
                    recipients, export_format, filters, is_active,
                    next_run_at, company_id, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                report.name, report.report_type, report.frequency,
                report.schedule_time, report.schedule_day,
                report.recipients, report.export_format, report.filters,
                1 if report.is_active else 0,
                next_run.isoformat() if next_run else None,
                company_id, report.created_by
            )
            
            result = self.db_manager.execute_query(query, values)
            if result:
                report_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء تقرير مجدول: {report.name} (ID: {report_id})")
                return report_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء تقرير مجدول: {e}", exc_info=True)
            return None
    
    def get_scheduled_report(self, report_id: int) -> Optional[ScheduledReport]:
        """الحصول على تقرير مجدول"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "SELECT * FROM scheduled_reports WHERE id = ?"
            params = [report_id]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            row = self.db_manager.fetch_one(query, tuple(params))
            if row:
                return self._row_to_report(row)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على تقرير مجدول: {e}", exc_info=True)
            return None
    
    def get_all_scheduled_reports(self) -> List[ScheduledReport]:
        """الحصول على جميع التقارير المجدولة"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "SELECT * FROM scheduled_reports WHERE 1=1"
            params = []
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            query += " ORDER BY name"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_report(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على التقارير المجدولة: {e}", exc_info=True)
            return []
    
    def update_scheduled_report(self, report: ScheduledReport) -> bool:
        """تحديث تقرير مجدول"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            # إعادة حساب next_run_at
            next_run = self._calculate_next_run(
                report.frequency,
                report.schedule_time,
                report.schedule_day
            )
            
            query = """
                UPDATE scheduled_reports SET
                    name = ?, report_type = ?, frequency = ?,
                    schedule_time = ?, schedule_day = ?,
                    recipients = ?, export_format = ?, filters = ?,
                    is_active = ?, next_run_at = ?
                WHERE id = ?
            """
            
            params = [
                report.name, report.report_type, report.frequency,
                report.schedule_time, report.schedule_day,
                report.recipients, report.export_format, report.filters,
                1 if report.is_active else 0,
                next_run.isoformat() if next_run else None,
                report.id
            ]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            result = self.db_manager.execute_query(query, tuple(params))
            if result and (hasattr(result, 'rowcount') and result.rowcount > 0 or not hasattr(result, 'rowcount')):
                self.logger.info(f"✅ تم تحديث تقرير مجدول: {report.name} (ID: {report.id})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث تقرير مجدول: {e}", exc_info=True)
            return False
    
    def delete_scheduled_report(self, report_id: int) -> bool:
        """حذف تقرير مجدول"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "DELETE FROM scheduled_reports WHERE id = ?"
            params = [report_id]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            result = self.db_manager.execute_query(query, tuple(params))
            if result and (hasattr(result, 'rowcount') and result.rowcount > 0 or not hasattr(result, 'rowcount')):
                self.logger.info(f"✅ تم حذف تقرير مجدول: ID={report_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حذف تقرير مجدول: {e}", exc_info=True)
            return False
    
    # ============================================================================
    # Report Execution
    # ============================================================================
    
    def run_scheduled_report(self, report_id: int) -> Dict[str, Any]:
        """
        تشغيل تقرير مجدول
        
        Args:
            report_id: معرف التقرير
            
        Returns:
            Dict مع نتيجة التنفيذ
        """
        try:
            report = self.get_scheduled_report(report_id)
            if not report:
                return {"error": "التقرير غير موجود"}
            
            if not report.is_active:
                return {"error": "التقرير غير مفعّل"}
            
            # توليد التقرير
            report_data = self._generate_report(report)
            
            if report_data.get("error"):
                return report_data
            
            # تصدير التقرير
            export_result = self._export_report(report, report_data)
            
            if export_result.get("error"):
                return export_result
            
            # تحديث last_run_at و next_run_at
            self._update_run_times(report_id)
            
            return {
                "success": True,
                "report_id": report_id,
                "export_path": export_result.get("file_path"),
                "message": "تم توليد التقرير بنجاح"
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تشغيل تقرير مجدول: {e}", exc_info=True)
            return {"error": str(e)}
    
    def check_and_run_due_reports(self) -> List[Dict[str, Any]]:
        """
        فحص وتشغيل التقارير المستحقة
        
        Returns:
            List من نتائج التنفيذ
        """
        try:
            now = datetime.now()
            
            query = """
                SELECT id FROM scheduled_reports
                WHERE is_active = 1
                    AND next_run_at <= ?
            """
            params = [now.isoformat()]
            
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            
            results = []
            for row in rows:
                report_id = row['id']
                result = self.run_scheduled_report(report_id)
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في فحص التقارير المستحقة: {e}", exc_info=True)
            return []
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def _calculate_next_run(self, frequency: str, schedule_time: str, schedule_day: Optional[int]) -> Optional[datetime]:
        """حساب وقت التشغيل القادم"""
        try:
            now = datetime.now()
            hour, minute = map(int, schedule_time.split(':'))
            
            if frequency == ScheduleFrequency.DAILY.value:
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run
            
            elif frequency == ScheduleFrequency.WEEKLY.value:
                if schedule_day is None:
                    schedule_day = 1  # الاثنين
                
                days_until = (schedule_day - now.weekday()) % 7
                if days_until == 0:
                    days_until = 7
                
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                next_run += timedelta(days=days_until)
                return next_run
            
            elif frequency == ScheduleFrequency.MONTHLY.value:
                if schedule_day is None:
                    schedule_day = 1
                
                next_run = now.replace(day=schedule_day, hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    # الانتقال للشهر القادم
                    if next_run.month == 12:
                        next_run = next_run.replace(year=next_run.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=next_run.month + 1)
                
                return next_run
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حساب وقت التشغيل القادم: {e}", exc_info=True)
            return None
    
    def _generate_report(self, report: ScheduledReport) -> Dict[str, Any]:
        """توليد التقرير"""
        try:
            filters = json.loads(report.filters) if report.filters else {}
            
            start_date = filters.get('start_date')
            end_date = filters.get('end_date')
            
            if start_date:
                start_date = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            if end_date:
                end_date = datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
            else:
                end_date = datetime.now()
            
            # توليد البيانات حسب نوع التقرير
            if report.report_type == "SALES":
                return {
                    "success": True,
                    "data": self.analytics_service.get_sales_trends(start_date, end_date),
                    "report_type": "SALES"
                }
            elif report.report_type == "INVENTORY":
                return {
                    "success": True,
                    "data": self.analytics_service.get_inventory_turnover(),
                    "report_type": "INVENTORY"
                }
            elif report.report_type == "FINANCIAL":
                return {
                    "success": True,
                    "data": self.analytics_service.get_profit_margin_analysis(start_date, end_date),
                    "report_type": "FINANCIAL"
                }
            else:
                return {"error": f"نوع تقرير غير مدعوم: {report.report_type}"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في توليد التقرير: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _export_report(self, report: ScheduledReport, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """تصدير التقرير"""
        try:
            # تحديد مسار التصدير
            reports_dir = Path("data/scheduled_reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{report.name}_{timestamp}"
            
            # التصدير حسب الصيغة
            if report.export_format == ExportFormat.PDF.value:
                file_path = reports_dir / f"{file_name}.pdf"
                # TODO: استخدام ReportExporter لتصدير PDF
                return {"error": "تصدير PDF غير متاح حالياً"}
            elif report.export_format == ExportFormat.EXCEL.value:
                file_path = reports_dir / f"{file_name}.xlsx"
                success = self.analytics_service.export_to_excel(
                    {"Report": report_data.get("data", {}).get("data", [])},
                    str(file_path)
                )
            elif report.export_format == ExportFormat.CSV.value:
                file_path = reports_dir / f"{file_name}.csv"
                data = report_data.get("data", {}).get("data", [])
                if isinstance(data, list):
                    success = self.analytics_service.export_to_csv(data, str(file_path))
                else:
                    success = False
            elif report.export_format == ExportFormat.JSON.value:
                file_path = reports_dir / f"{file_name}.json"
                success = self.analytics_service.export_to_json(report_data, str(file_path))
            else:
                return {"error": f"صيغة تصدير غير مدعومة: {report.export_format}"}
            
            if success:
                # TODO: إرسال البريد الإلكتروني إذا كان هناك مستلمون
                return {
                    "success": True,
                    "file_path": str(file_path)
                }
            else:
                return {"error": "فشل تصدير التقرير"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في تصدير التقرير: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _update_run_times(self, report_id: int):
        """تحديث أوقات التشغيل"""
        try:
            report = self.get_scheduled_report(report_id)
            if not report:
                return
            
            now = datetime.now()
            next_run = self._calculate_next_run(
                report.frequency,
                report.schedule_time,
                report.schedule_day
            )
            
            query = """
                UPDATE scheduled_reports SET
                    last_run_at = ?,
                    next_run_at = ?
                WHERE id = ?
            """
            
            self.db_manager.execute_query(
                query,
                (now.isoformat(), next_run.isoformat() if next_run else None, report_id)
            )
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث أوقات التشغيل: {e}", exc_info=True)
    
    def _row_to_report(self, row: Dict[str, Any]) -> ScheduledReport:
        """تحويل صف قاعدة البيانات إلى ScheduledReport"""
        return ScheduledReport(
            id=row.get("id"),
            name=row.get("name", ""),
            report_type=row.get("report_type", ""),
            frequency=row.get("frequency", ScheduleFrequency.DAILY.value),
            schedule_time=row.get("schedule_time", "09:00"),
            schedule_day=row.get("schedule_day"),
            recipients=row.get("recipients", ""),
            export_format=row.get("export_format", ExportFormat.PDF.value),
            filters=row.get("filters", ""),
            is_active=bool(row.get("is_active", 1)),
            last_run_at=self._parse_datetime(row.get("last_run_at")),
            next_run_at=self._parse_datetime(row.get("next_run_at")),
            company_id=row.get("company_id"),
            created_by=row.get("created_by"),
            created_at=self._parse_datetime(row.get("created_at")),
            updated_at=self._parse_datetime(row.get("updated_at"))
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


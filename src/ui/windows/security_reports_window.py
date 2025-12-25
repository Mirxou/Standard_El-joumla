#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة تقارير الأمان - Security Reports Window
واجهة لتوليد تقارير الأمان
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QToolBar, QStatusBar,
    QAbstractItemView, QDialog, QDialogButtonBox, QDateEdit, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QAction, QColor, QBrush

# إضافة مسار src
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager
from src.services.security_reports_service import SecurityReportsService
from src.services.analytics_service import AnalyticsService
from src.utils.logger import setup_logger


class SecurityReportsWindow(QMainWindow):
    """نافذة تقارير الأمان"""
    
    # Window Manager attributes
    window_key = "security_reports"
    window_singleton = True
    window_title = "📊 تقارير الأمان"
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.security_reports_service = SecurityReportsService(db_manager, self.logger)
        self.analytics_service = AnalyticsService(db_manager, self.logger)
        
        self.setWindowTitle("تقارير الأمان")
        self.setMinimumSize(1200, 800)
        
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد الواجهة"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        generate_report_action = QAction("📄 توليد تقرير", self)
        generate_report_action.triggered.connect(self.generate_report)
        toolbar.addAction(generate_report_action)
        
        # Filters
        filters_group = QGroupBox("المرشحات")
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("نوع التقرير:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "ملخص الأمان",
            "الأحداث الأمنية",
            "التهديدات",
            "نشاط تسجيل الدخول",
            "حظر IP"
        ])
        filters_layout.addWidget(self.report_type_combo)
        
        filters_layout.addWidget(QLabel("من:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        filters_layout.addWidget(self.start_date)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filters_layout.addWidget(self.end_date)
        
        apply_btn = QPushButton("تطبيق")
        apply_btn.clicked.connect(self.load_report)
        filters_layout.addWidget(apply_btn)
        
        filters_layout.addStretch()
        filters_group.setLayout(filters_layout)
        main_layout.addWidget(filters_group)
        
        # جدول النتائج
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "النوع", "الخطورة/المستوى", "المستخدم/IP", "الوصف", "التاريخ", "الحالة"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        main_layout.addWidget(self.results_table)
        
        # Status Bar
        self.statusBar().showMessage("جاهز")
    
    def load_report(self):
        """تحميل التقرير"""
        report_type = self.report_type_combo.currentText()
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        
        self.statusBar().showMessage("جاري تحميل التقرير...")
        
        try:
            if report_type == "ملخص الأمان":
                result = self.security_reports_service.generate_security_summary_report(start_date, end_date)
                self.display_summary_report(result)
            elif report_type == "الأحداث الأمنية":
                result = self.security_reports_service.generate_security_events_report(
                    start_date=start_date, end_date=end_date
                )
                self.display_events_report(result)
            elif report_type == "التهديدات":
                result = self.security_reports_service.generate_threats_report(
                    start_date=start_date, end_date=end_date
                )
                self.display_threats_report(result)
            elif report_type == "نشاط تسجيل الدخول":
                result = self.security_reports_service.generate_login_activity_report(
                    start_date=start_date, end_date=end_date
                )
                self.display_login_activity_report(result)
            elif report_type == "حظر IP":
                result = self.security_reports_service.generate_ip_blocking_report()
                self.display_ip_blocking_report(result)
            else:
                QMessageBox.warning(self, "خطأ", "نوع تقرير غير معروف")
                return
            
            self.statusBar().showMessage("تم تحميل التقرير")
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل التقرير: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل تحميل التقرير: {e}")
            self.statusBar().showMessage("جاهز")
    
    def display_summary_report(self, result: dict):
        """عرض تقرير الملخص"""
        if not result.get("success"):
            QMessageBox.critical(self, "خطأ", result.get("error", "خطأ غير معروف"))
            return
        
        data = result.get("data", {})
        events_summary = data.get("security_events", {})
        
        # عرض البيانات في الجدول
        rows = []
        
        # إضافة إحصائيات الأحداث
        for event_type, count in events_summary.get("by_type", {}).items():
            rows.append({
                "type": event_type,
                "severity": "",
                "user": "",
                "description": f"إجمالي: {count}",
                "date": "",
                "status": ""
            })
        
        self._populate_table(rows)
    
    def display_events_report(self, result: dict):
        """عرض تقرير الأحداث"""
        if not result.get("success"):
            QMessageBox.critical(self, "خطأ", result.get("error", "خطأ غير معروف"))
            return
        
        data = result.get("data", {})
        events = data.get("events", [])
        
        rows = []
        for event in events:
            rows.append({
                "type": event.get("event_type", ""),
                "severity": event.get("severity", ""),
                "user": event.get("username", ""),
                "description": event.get("description", ""),
                "date": event.get("timestamp", ""),
                "status": ""
            })
        
        self._populate_table(rows)
    
    def display_threats_report(self, result: dict):
        """عرض تقرير التهديدات"""
        if not result.get("success"):
            QMessageBox.critical(self, "خطأ", result.get("error", "خطأ غير معروف"))
            return
        
        data = result.get("data", {})
        threats = data.get("threats", [])
        
        rows = []
        for threat in threats:
            rows.append({
                "type": threat.get("threat_type", ""),
                "severity": threat.get("threat_level", ""),
                "user": threat.get("source_ip", ""),
                "description": threat.get("description", ""),
                "date": threat.get("detected_at", ""),
                "status": "محظور" if threat.get("blocked") else "غير محظور"
            })
        
        self._populate_table(rows)
    
    def display_login_activity_report(self, result: dict):
        """عرض تقرير نشاط تسجيل الدخول"""
        if not result.get("success"):
            QMessageBox.critical(self, "خطأ", result.get("error", "خطأ غير معروف"))
            return
        
        data = result.get("data", {})
        successful = data.get("successful_logins", {}).get("events", [])
        failed = data.get("failed_logins", {}).get("events", [])
        
        rows = []
        for event in successful:
            rows.append({
                "type": "تسجيل دخول ناجح",
                "severity": "",
                "user": event.get("username", ""),
                "description": "",
                "date": event.get("timestamp", ""),
                "status": "نجح"
            })
        
        for event in failed:
            rows.append({
                "type": "تسجيل دخول فاشل",
                "severity": "HIGH",
                "user": event.get("username", ""),
                "description": "",
                "date": event.get("timestamp", ""),
                "status": "فشل"
            })
        
        self._populate_table(rows)
    
    def display_ip_blocking_report(self, result: dict):
        """عرض تقرير حظر IP"""
        if not result.get("success"):
            QMessageBox.critical(self, "خطأ", result.get("error", "خطأ غير معروف"))
            return
        
        data = result.get("data", {})
        blocked_ips = data.get("blocked_ips", [])
        
        rows = []
        for ip_info in blocked_ips:
            rows.append({
                "type": "حظر IP",
                "severity": "",
                "user": ip_info.get("ip_address", ""),
                "description": ip_info.get("reason", ""),
                "date": ip_info.get("blocked_at", ""),
                "status": "محظور"
            })
        
        self._populate_table(rows)
    
    def _populate_table(self, rows: list):
        """ملء الجدول بالبيانات"""
        self.results_table.setRowCount(len(rows))
        
        for row_idx, row_data in enumerate(rows):
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(row_data.get("type", "")))
            
            severity_item = QTableWidgetItem(row_data.get("severity", ""))
            severity = row_data.get("severity", "")
            if severity == "CRITICAL":
                severity_item.setForeground(QBrush(QColor("red")))
            elif severity == "HIGH":
                severity_item.setForeground(QBrush(QColor("orange")))
            elif severity == "MEDIUM":
                severity_item.setForeground(QBrush(QColor("blue")))
            self.results_table.setItem(row_idx, 1, severity_item)
            
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(row_data.get("user", "")))
            self.results_table.setItem(row_idx, 3, QTableWidgetItem(row_data.get("description", "")))
            self.results_table.setItem(row_idx, 4, QTableWidgetItem(row_data.get("date", "")))
            self.results_table.setItem(row_idx, 5, QTableWidgetItem(row_data.get("status", "")))
    
    def generate_report(self):
        """توليد وتصدير التقرير"""
        report_type = self.report_type_combo.currentText()
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        
        self.statusBar().showMessage("جاري توليد التقرير...")
        
        try:
            if report_type == "ملخص الأمان":
                result = self.security_reports_service.generate_security_summary_report(start_date, end_date)
            elif report_type == "الأحداث الأمنية":
                result = self.security_reports_service.generate_security_events_report(
                    start_date=start_date, end_date=end_date
                )
            elif report_type == "التهديدات":
                result = self.security_reports_service.generate_threats_report(
                    start_date=start_date, end_date=end_date
                )
            elif report_type == "نشاط تسجيل الدخول":
                result = self.security_reports_service.generate_login_activity_report(
                    start_date=start_date, end_date=end_date
                )
            elif report_type == "حظر IP":
                result = self.security_reports_service.generate_ip_blocking_report()
            else:
                QMessageBox.warning(self, "خطأ", "نوع تقرير غير معروف")
                return
            
            if not result.get("success"):
                QMessageBox.critical(self, "خطأ", result.get("error", "خطأ غير معروف"))
                return
            
            # تصدير التقرير
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "حفظ التقرير",
                f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx)"
            )
            
            if file_path:
                if file_path.endswith('.json'):
                    success = self.analytics_service.export_to_json(result.get("data", {}), file_path)
                elif file_path.endswith('.csv'):
                    data_list = result.get("data", {}).get("events", []) or result.get("data", {}).get("threats", []) or result.get("data", {}).get("blocked_ips", [])
                    if data_list:
                        success = self.analytics_service.export_to_csv(data_list, file_path)
                    else:
                        success = False
                elif file_path.endswith('.xlsx'):
                    excel_data = {}
                    report_data = result.get("data", {})
                    if "events" in report_data:
                        excel_data["Events"] = report_data["events"]
                    if "threats" in report_data:
                        excel_data["Threats"] = report_data["threats"]
                    if "blocked_ips" in report_data:
                        excel_data["Blocked IPs"] = report_data["blocked_ips"]
                    
                    if excel_data:
                        success = self.analytics_service.export_to_excel(excel_data, file_path)
                    else:
                        success = False
                else:
                    success = False
                
                if success:
                    QMessageBox.information(
                        self, "نجاح",
                        f"تم توليد التقرير بنجاح!\n\nتم حفظ الملف في:\n{file_path}"
                    )
                else:
                    QMessageBox.critical(self, "خطأ", "فشل تصدير التقرير")
            
            self.statusBar().showMessage("جاهز")
            
        except Exception as e:
            self.logger.error(f"خطأ في توليد التقرير: {e}", exc_info=True)
            QMessageBox.critical(self, "خطأ", f"فشل توليد التقرير: {e}")
            self.statusBar().showMessage("جاهز")


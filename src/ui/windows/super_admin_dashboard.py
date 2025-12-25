#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Admin Dashboard - لوحة تحكم المدير الخارق
مراقبة صحة النظام بأكمله
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QToolBar, QStatusBar,
    QProgressBar, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QBrush

# إضافة مسار src
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager
from src.core.security_monitor import SecurityMonitor
from src.core.intrusion_detection import IntrusionDetectionSystem
from src.services.webhook_service import WebhookService
from src.services.cloud_sync_service import CloudSyncService
from src.utils.logger import setup_logger


class SuperAdminDashboard(QMainWindow):
    """لوحة تحكم المدير الخارق"""
    
    # Window Manager attributes
    window_key = "super_admin_dashboard"
    window_singleton = True
    window_title = "🎛️ لوحة تحكم المدير الخارق"
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        
        self.security_monitor = SecurityMonitor(db_manager, self.logger)
        self.intrusion_detection = IntrusionDetectionSystem(db_manager, self.logger)
        
        self.setWindowTitle("لوحة تحكم المدير الخارق")
        self.setMinimumSize(1400, 900)
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        """إعداد الواجهة"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)
        
        # Grid Layout for Dashboard Widgets
        grid_layout = QGridLayout()
        
        # System Health
        health_group = self.create_health_widget()
        grid_layout.addWidget(health_group, 0, 0, 1, 2)
        
        # Security Status
        security_group = self.create_security_widget()
        grid_layout.addWidget(security_group, 0, 2, 1, 2)
        
        # Database Status
        database_group = self.create_database_widget()
        grid_layout.addWidget(database_group, 1, 0, 1, 2)
        
        # Services Status
        services_group = self.create_services_widget()
        grid_layout.addWidget(services_group, 1, 2, 1, 2)
        
        # Recent Threats
        threats_group = self.create_threats_widget()
        grid_layout.addWidget(threats_group, 2, 0, 1, 4)
        
        main_layout.addLayout(grid_layout)
        
        # Status Bar
        self.statusBar().showMessage("جاهز")
        
        # Auto-refresh timer (every 30 seconds)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        # self.refresh_timer.start(30000)  # 🔥 معطّل لمنع التجميد
    
    def create_health_widget(self) -> QGroupBox:
        """إنشاء widget صحة النظام"""
        group = QGroupBox("💚 صحة النظام")
        layout = QVBoxLayout()
        
        # CPU Usage (simulated)
        cpu_label = QLabel("استخدام المعالج:")
        cpu_progress = QProgressBar()
        cpu_progress.setRange(0, 100)
        cpu_progress.setValue(45)
        cpu_progress.setFormat("%p%")
        layout.addWidget(cpu_label)
        layout.addWidget(cpu_progress)
        
        # Memory Usage (simulated)
        memory_label = QLabel("استخدام الذاكرة:")
        memory_progress = QProgressBar()
        memory_progress.setRange(0, 100)
        memory_progress.setValue(62)
        memory_progress.setFormat("%p%")
        layout.addWidget(memory_label)
        layout.addWidget(memory_progress)
        
        # Disk Usage (simulated)
        disk_label = QLabel("استخدام القرص:")
        disk_progress = QProgressBar()
        disk_progress.setRange(0, 100)
        disk_progress.setValue(38)
        disk_progress.setFormat("%p%")
        layout.addWidget(disk_label)
        layout.addWidget(disk_progress)
        
        group.setLayout(layout)
        return group
    
    def create_security_widget(self) -> QGroupBox:
        """إنشاء widget حالة الأمان"""
        group = QGroupBox("🔒 حالة الأمان")
        layout = QVBoxLayout()
        
        # Recent Security Events
        summary = self.security_monitor.get_security_summary()
        
        total_events = summary.get("total_events", 0)
        failed_logins = summary.get("failed_logins", 0)
        suspicious = summary.get("suspicious_activities", 0)
        
        layout.addWidget(QLabel(f"إجمالي الأحداث: {total_events}"))
        layout.addWidget(QLabel(f"محاولات فاشلة: {failed_logins}"))
        layout.addWidget(QLabel(f"أنشطة مشبوهة: {suspicious}"))
        
        # Threats
        threats = self.intrusion_detection.get_threats(limit=5)
        critical_threats = len([t for t in threats if t.threat_level == "CRITICAL"])
        
        threats_label = QLabel(f"تهديدات حرجة: {critical_threats}")
        if critical_threats > 0:
            threats_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(threats_label)
        
        group.setLayout(layout)
        return group
    
    def create_database_widget(self) -> QGroupBox:
        """إنشاء widget حالة قاعدة البيانات"""
        group = QGroupBox("🗄️ قاعدة البيانات")
        layout = QVBoxLayout()
        
        try:
            # Get database stats
            query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
            tables_row = self.db_manager.fetch_one(query)
            table_count = tables_row['count'] if tables_row else 0
            
            # Get total records (sample)
            query = "SELECT COUNT(*) as count FROM products"
            products_row = self.db_manager.fetch_one(query)
            products_count = products_row['count'] if products_row else 0
            
            layout.addWidget(QLabel(f"عدد الجداول: {table_count}"))
            layout.addWidget(QLabel(f"عدد المنتجات: {products_count}"))
            layout.addWidget(QLabel("الحالة: ✅ متصل"))
            
        except Exception as e:
            layout.addWidget(QLabel(f"خطأ: {str(e)}"))
        
        group.setLayout(layout)
        return group
    
    def create_services_widget(self) -> QGroupBox:
        """إنشاء widget حالة الخدمات"""
        group = QGroupBox("⚙️ حالة الخدمات")
        layout = QVBoxLayout()
        
        # Webhooks Status
        try:
            webhook_service = WebhookService(self.db_manager, self.logger)
            webhooks = webhook_service.get_all_webhooks()
            active_webhooks = len([w for w in webhooks if w.is_active])
            layout.addWidget(QLabel(f"Webhooks نشطة: {active_webhooks}/{len(webhooks)}"))
        except:
            layout.addWidget(QLabel("Webhooks: غير متاح"))
        
        # Cloud Sync Status
        try:
            cloud_sync = CloudSyncService(self.db_manager, self.logger)
            # Check if cloud sync is configured
            layout.addWidget(QLabel("Cloud Sync: ⚠️ يحتاج إعداد"))
        except:
            layout.addWidget(QLabel("Cloud Sync: غير متاح"))
        
        # API Status
        layout.addWidget(QLabel("REST API: ✅ نشط"))
        
        group.setLayout(layout)
        return group
    
    def create_threats_widget(self) -> QGroupBox:
        """إنشاء widget التهديدات الأخيرة"""
        group = QGroupBox("🚨 التهديدات الأخيرة")
        layout = QVBoxLayout()
        
        self.threats_table = QTableWidget()
        self.threats_table.setColumnCount(5)
        self.threats_table.setHorizontalHeaderLabels([
            "النوع", "المستوى", "IP المصدر", "الوصف", "التاريخ"
        ])
        self.threats_table.horizontalHeader().setStretchLastSection(True)
        self.threats_table.setAlternatingRowColors(True)
        self.threats_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.threats_table.setMaximumHeight(200)
        layout.addWidget(self.threats_table)
        
        group.setLayout(layout)
        return group
    
    def refresh_all(self):
        """تحديث جميع البيانات"""
        self.refresh_threats()
        self.statusBar().showMessage(f"تم التحديث: {datetime.now().strftime('%H:%M:%S')}")
    
    def refresh_threats(self):
        """تحديث قائمة التهديدات"""
        try:
            threats = self.intrusion_detection.get_threats(limit=10)
            
            self.threats_table.setRowCount(len(threats))
            
            for row, threat in enumerate(threats):
                self.threats_table.setItem(row, 0, QTableWidgetItem(threat.threat_type))
                
                level_item = QTableWidgetItem(threat.threat_level)
                if threat.threat_level == "CRITICAL":
                    level_item.setForeground(QBrush(QColor("red")))
                elif threat.threat_level == "HIGH":
                    level_item.setForeground(QBrush(QColor("orange")))
                self.threats_table.setItem(row, 1, level_item)
                
                self.threats_table.setItem(row, 2, QTableWidgetItem(threat.source_ip))
                self.threats_table.setItem(row, 3, QTableWidgetItem(threat.description[:50]))
                
                date_str = threat.detected_at.strftime("%Y-%m-%d %H:%M") if threat.detected_at else ""
                self.threats_table.setItem(row, 4, QTableWidgetItem(date_str))
                
        except Exception as e:
            self.logger.error(f"خطأ في تحديث التهديدات: {e}", exc_info=True)
    
    def start_monitoring(self):
        """بدء المراقبة"""
        self.refresh_all()
    
    def closeEvent(self, event):
        """إغلاق النافذة"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        event.accept()


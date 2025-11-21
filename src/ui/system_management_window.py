"""
نافذة إدارة النظام
System Management Window - Backup, Performance, and Maintenance
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QTextEdit, QGroupBox, QGridLayout,
    QComboBox, QSpinBox, QCheckBox, QFileDialog, QMessageBox,
    QLineEdit, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from datetime import datetime, timedelta
import json
import os


class BackupThread(QThread):
    """Thread for backup operations"""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, backup_service, operation, **kwargs):
        super().__init__()
        self.backup_service = backup_service
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == 'create':
                result = self.backup_service.create_backup(**self.kwargs)
                self.finished.emit(True, f"تم إنشاء النسخة الاحتياطية: {result}")
            elif self.operation == 'restore':
                self.backup_service.restore_backup(**self.kwargs)
                self.finished.emit(True, "تم استعادة النسخة الاحتياطية بنجاح")
            elif self.operation == 'cleanup':
                self.backup_service.cleanup_old_backups(**self.kwargs)
                self.finished.emit(True, "تم تنظيف النسخ القديمة بنجاح")
        except Exception as e:
            self.finished.emit(False, str(e))


class PerformanceThread(QThread):
    """Thread for performance operations"""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, performance_service, operation, **kwargs):
        super().__init__()
        self.performance_service = performance_service
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == 'optimize':
                self.performance_service.optimize_database()
                self.finished.emit(True, "تم تحسين قاعدة البيانات بنجاح")
            elif self.operation == 'check':
                result = self.performance_service.check_integrity()
                status = "سليمة" if result else "يوجد أخطاء"
                self.finished.emit(result, f"حالة قاعدة البيانات: {status}")
            elif self.operation == 'repair':
                self.performance_service.repair_database()
                self.finished.emit(True, "تم إصلاح قاعدة البيانات")
            elif self.operation == 'cleanup':
                deleted = self.performance_service.cleanup_data(**self.kwargs)
                self.finished.emit(True, f"تم حذف {deleted} سجل قديم")
        except Exception as e:
            self.finished.emit(False, str(e))


class SystemManagementWindow(QDialog):
    """نافذة إدارة النظام الشاملة"""
    
    def __init__(self, parent, db_manager, backup_service, performance_service, permission_service=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.backup_service = backup_service
        self.performance_service = performance_service
        self.permission_service = permission_service
        
        self.setWindowTitle("إدارة النظام")
        self.setMinimumSize(1000, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("إدارة النظام والصيانة")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_backup_tab(), "النسخ الاحتياطي")
        self.tabs.addTab(self.create_performance_tab(), "الأداء والتحسين")
        self.tabs.addTab(self.create_maintenance_tab(), "الصيانة")
        self.tabs.addTab(self.create_settings_tab(), "الإعدادات")
        layout.addWidget(self.tabs)
        
        # Close Button
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    # ==================== Backup Tab ====================
    
    def create_backup_tab(self):
        """تبويب النسخ الاحتياطي"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Backup Controls
        controls_group = QGroupBox("عمليات النسخ الاحتياطي")
        controls_layout = QGridLayout(controls_group)
        
        # Create Backup
        controls_layout.addWidget(QLabel("وصف النسخة:"), 0, 0)
        self.backup_description = QLineEdit()
        self.backup_description.setPlaceholderText("نسخة احتياطية يدوية")
        controls_layout.addWidget(self.backup_description, 0, 1)
        
        self.include_attachments_cb = QCheckBox("تضمين المرفقات")
        self.include_attachments_cb.setChecked(True)
        controls_layout.addWidget(self.include_attachments_cb, 0, 2)
        
        create_backup_btn = QPushButton("إنشاء نسخة احتياطية")
        create_backup_btn.clicked.connect(self.create_backup)
        controls_layout.addWidget(create_backup_btn, 0, 3)
        
        # Auto Backup
        controls_layout.addWidget(QLabel("نسخ تلقائي كل:"), 1, 0)
        self.auto_backup_interval = QSpinBox()
        self.auto_backup_interval.setRange(1, 168)
        self.auto_backup_interval.setValue(24)
        self.auto_backup_interval.setSuffix(" ساعة")
        controls_layout.addWidget(self.auto_backup_interval, 1, 1)
        
        self.auto_backup_btn = QPushButton("تفعيل النسخ التلقائي")
        self.auto_backup_btn.setCheckable(True)
        self.auto_backup_btn.clicked.connect(self.toggle_auto_backup)
        controls_layout.addWidget(self.auto_backup_btn, 1, 2)
        
        # Cleanup
        controls_layout.addWidget(QLabel("حذف القديم:"), 2, 0)
        self.keep_count_spin = QSpinBox()
        self.keep_count_spin.setRange(1, 100)
        self.keep_count_spin.setValue(10)
        self.keep_count_spin.setPrefix("آخر ")
        self.keep_count_spin.setSuffix(" نسخة")
        controls_layout.addWidget(self.keep_count_spin, 2, 1)
        
        cleanup_btn = QPushButton("تنظيف النسخ القديمة")
        cleanup_btn.clicked.connect(self.cleanup_backups)
        controls_layout.addWidget(cleanup_btn, 2, 2)
        
        layout.addWidget(controls_group)
        
        # Backup List
        list_group = QGroupBox("النسخ الاحتياطية المتاحة")
        list_layout = QVBoxLayout(list_group)
        
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(6)
        self.backups_table.setHorizontalHeaderLabels([
            "اسم النسخة", "التاريخ", "الحجم", "النوع", "الملفات", "الإجراءات"
        ])
        self.backups_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_layout.addWidget(self.backups_table)
        
        layout.addWidget(list_group)
        
        # Backup Statistics
        stats_group = QGroupBox("إحصائيات النسخ الاحتياطي")
        stats_layout = QGridLayout(stats_group)
        
        self.backup_stats_labels = {}
        stats = [
            ("total", "إجمالي النسخ"),
            ("size", "الحجم الكلي"),
            ("last", "آخر نسخة"),
            ("oldest", "أقدم نسخة")
        ]
        
        for i, (key, label) in enumerate(stats):
            stats_layout.addWidget(QLabel(f"{label}:"), i // 2, (i % 2) * 2)
            value_label = QLabel("-")
            value_label.setStyleSheet("font-weight: bold;")
            self.backup_stats_labels[key] = value_label
            stats_layout.addWidget(value_label, i // 2, (i % 2) * 2 + 1)
        
        layout.addWidget(stats_group)
        
        return widget
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        description = self.backup_description.text() or "نسخة احتياطية يدوية"
        include_attachments = self.include_attachments_cb.isChecked()
        
        self.progress_dialog = QMessageBox(self)
        self.progress_dialog.setWindowTitle("جاري الإنشاء...")
        self.progress_dialog.setText("جاري إنشاء النسخة الاحتياطية...")
        self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
        self.progress_dialog.show()
        
        self.backup_thread = BackupThread(
            self.backup_service,
            'create',
            description=description,
            include_attachments=include_attachments,
            compress=True
        )
        self.backup_thread.finished.connect(self.on_backup_finished)
        self.backup_thread.start()
    
    def toggle_auto_backup(self, checked):
        """تبديل النسخ التلقائي"""
        try:
            if checked:
                interval = self.auto_backup_interval.value()
                self.backup_service.enable_auto_backup(interval_hours=interval)
                self.auto_backup_btn.setText("إيقاف النسخ التلقائي")
                QMessageBox.information(self, "نجح", f"تم تفعيل النسخ التلقائي كل {interval} ساعة")
            else:
                self.backup_service.disable_auto_backup()
                self.auto_backup_btn.setText("تفعيل النسخ التلقائي")
                QMessageBox.information(self, "نجح", "تم إيقاف النسخ التلقائي")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تبديل النسخ التلقائي: {str(e)}")
            self.auto_backup_btn.setChecked(not checked)
    
    def cleanup_backups(self):
        """تنظيف النسخ القديمة"""
        keep_count = self.keep_count_spin.value()
        
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد حذف جميع النسخ ما عدا آخر {keep_count} نسخة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.backup_thread = BackupThread(
                self.backup_service,
                'cleanup',
                keep_count=keep_count
            )
            self.backup_thread.finished.connect(self.on_backup_finished)
            self.backup_thread.start()
    
    def restore_backup(self, backup_name):
        """استعادة نسخة احتياطية"""
        reply = QMessageBox.warning(
            self,
            "تحذير",
            f"سيتم استبدال قاعدة البيانات الحالية بالنسخة: {backup_name}\n"
            "هذا الإجراء لا يمكن التراجع عنه!\n"
            "هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.progress_dialog = QMessageBox(self)
            self.progress_dialog.setWindowTitle("جاري الاستعادة...")
            self.progress_dialog.setText("جاري استعادة النسخة الاحتياطية...")
            self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
            self.progress_dialog.show()
            
            self.backup_thread = BackupThread(
                self.backup_service,
                'restore',
                backup_name=backup_name,
                restore_attachments=True
            )
            self.backup_thread.finished.connect(self.on_restore_finished)
            self.backup_thread.start()
    
    def delete_backup(self, backup_name):
        """حذف نسخة احتياطية"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد حذف النسخة: {backup_name}؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.backup_service.delete_backup(backup_name)
                QMessageBox.information(self, "نجح", "تم حذف النسخة بنجاح")
                self.load_backups()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل حذف النسخة: {str(e)}")
    
    def on_backup_finished(self, success, message):
        """معالج انتهاء عملية النسخ"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        if success:
            QMessageBox.information(self, "نجح", message)
            self.load_backups()
            self.backup_description.clear()
        else:
            QMessageBox.critical(self, "خطأ", f"فشلت العملية: {message}")
    
    def on_restore_finished(self, success, message):
        """معالج انتهاء عملية الاستعادة"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        if success:
            QMessageBox.information(
                self,
                "نجح",
                f"{message}\n\nيُنصح بإعادة تشغيل التطبيق."
            )
            self.load_backups()
        else:
            QMessageBox.critical(self, "خطأ", f"فشلت الاستعادة: {message}")
    
    def load_backups(self):
        """تحميل قائمة النسخ الاحتياطية"""
        try:
            backups = self.backup_service.list_backups(limit=100)
            
            self.backups_table.setRowCount(len(backups))
            
            for row, backup in enumerate(backups):
                # Name
                self.backups_table.setItem(row, 0, QTableWidgetItem(backup['name']))
                
                # Date
                date_str = backup.get('date', '-')
                if isinstance(date_str, str) and date_str != '-':
                    try:
                        date_obj = datetime.fromisoformat(date_str)
                        date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                self.backups_table.setItem(row, 1, QTableWidgetItem(date_str))
                
                # Size
                size_mb = backup.get('size', 0) / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb > 0 else "-"
                self.backups_table.setItem(row, 2, QTableWidgetItem(size_str))
                
                # Type
                backup_type = backup.get('type', 'manual')
                type_ar = "تلقائي" if backup_type == 'automatic' else "يدوي"
                self.backups_table.setItem(row, 3, QTableWidgetItem(type_ar))
                
                # Files
                files_count = backup.get('files_count', '-')
                self.backups_table.setItem(row, 4, QTableWidgetItem(str(files_count)))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                
                restore_btn = QPushButton("استعادة")
                restore_btn.clicked.connect(lambda checked, n=backup['name']: self.restore_backup(n))
                actions_layout.addWidget(restore_btn)
                
                delete_btn = QPushButton("حذف")
                delete_btn.clicked.connect(lambda checked, n=backup['name']: self.delete_backup(n))
                actions_layout.addWidget(delete_btn)
                
                self.backups_table.setCellWidget(row, 5, actions_widget)
            
            # Update statistics
            stats = self.backup_service.get_backup_statistics()
            self.backup_stats_labels['total'].setText(str(stats['total_backups']))
            
            size_mb = stats['total_size'] / (1024 * 1024) if stats['total_size'] else 0
            self.backup_stats_labels['size'].setText(f"{size_mb:.2f} MB")
            
            if stats['newest_backup']:
                try:
                    newest = datetime.fromisoformat(stats['newest_backup'])
                    self.backup_stats_labels['last'].setText(newest.strftime("%Y-%m-%d %H:%M"))
                except:
                    self.backup_stats_labels['last'].setText(stats['newest_backup'])
            else:
                self.backup_stats_labels['last'].setText("-")
            
            if stats['oldest_backup']:
                try:
                    oldest = datetime.fromisoformat(stats['oldest_backup'])
                    self.backup_stats_labels['oldest'].setText(oldest.strftime("%Y-%m-%d %H:%M"))
                except:
                    self.backup_stats_labels['oldest'].setText(stats['oldest_backup'])
            else:
                self.backup_stats_labels['oldest'].setText("-")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل النسخ: {str(e)}")
    
    # ==================== Performance Tab ====================
    
    def create_performance_tab(self):
        """تبويب الأداء والتحسين"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Performance Actions
        actions_group = QGroupBox("عمليات التحسين")
        actions_layout = QGridLayout(actions_group)
        
        optimize_btn = QPushButton("تحسين قاعدة البيانات")
        optimize_btn.clicked.connect(self.optimize_database)
        actions_layout.addWidget(optimize_btn, 0, 0)
        
        check_btn = QPushButton("فحص السلامة")
        check_btn.clicked.connect(self.check_integrity)
        actions_layout.addWidget(check_btn, 0, 1)
        
        repair_btn = QPushButton("إصلاح قاعدة البيانات")
        repair_btn.clicked.connect(self.repair_database)
        actions_layout.addWidget(repair_btn, 0, 2)
        
        analyze_btn = QPushButton("تحليل الأداء")
        analyze_btn.clicked.connect(self.analyze_performance)
        actions_layout.addWidget(analyze_btn, 1, 0)
        
        cleanup_btn = QPushButton("حذف السجلات القديمة")
        cleanup_btn.clicked.connect(self.cleanup_data)
        actions_layout.addWidget(cleanup_btn, 1, 1)
        
        refresh_btn = QPushButton("تحديث المعلومات")
        refresh_btn.clicked.connect(self.load_performance_info)
        actions_layout.addWidget(refresh_btn, 1, 2)
        
        layout.addWidget(actions_group)
        
        # Performance Metrics
        metrics_group = QGroupBox("مقاييس الأداء")
        metrics_layout = QGridLayout(metrics_group)
        
        self.perf_labels = {}
        metrics = [
            ("db_size", "حجم قاعدة البيانات"),
            ("table_count", "عدد الجداول"),
            ("index_count", "عدد الفهارس"),
            ("free_pages", "صفحات فارغة"),
            ("ram_usage", "استخدام الذاكرة"),
            ("disk_free", "مساحة القرص الحرة")
        ]
        
        for i, (key, label) in enumerate(metrics):
            metrics_layout.addWidget(QLabel(f"{label}:"), i // 2, (i % 2) * 2)
            value_label = QLabel("-")
            value_label.setStyleSheet("font-weight: bold;")
            self.perf_labels[key] = value_label
            metrics_layout.addWidget(value_label, i // 2, (i % 2) * 2 + 1)
        
        layout.addWidget(metrics_group)
        
        # Analysis Results
        results_group = QGroupBox("نتائج التحليل")
        results_layout = QVBoxLayout(results_group)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(200)
        results_layout.addWidget(self.analysis_text)
        
        layout.addWidget(results_group)
        
        return widget
    
    def optimize_database(self):
        """تحسين قاعدة البيانات"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "سيتم تحسين قاعدة البيانات (ANALYZE, REINDEX, VACUUM)\n"
            "قد تستغرق هذه العملية عدة دقائق.\n"
            "هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.progress_dialog = QMessageBox(self)
            self.progress_dialog.setWindowTitle("جاري التحسين...")
            self.progress_dialog.setText("جاري تحسين قاعدة البيانات...")
            self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
            self.progress_dialog.show()
            
            self.perf_thread = PerformanceThread(self.performance_service, 'optimize')
            self.perf_thread.finished.connect(self.on_performance_finished)
            self.perf_thread.start()
    
    def check_integrity(self):
        """فحص سلامة قاعدة البيانات"""
        self.progress_dialog = QMessageBox(self)
        self.progress_dialog.setWindowTitle("جاري الفحص...")
        self.progress_dialog.setText("جاري فحص سلامة قاعدة البيانات...")
        self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
        self.progress_dialog.show()
        
        self.perf_thread = PerformanceThread(self.performance_service, 'check')
        self.perf_thread.finished.connect(self.on_performance_finished)
        self.perf_thread.start()
    
    def repair_database(self):
        """إصلاح قاعدة البيانات"""
        reply = QMessageBox.warning(
            self,
            "تحذير",
            "سيتم محاولة إصلاح قاعدة البيانات.\n"
            "يُنصح بإنشاء نسخة احتياطية أولاً.\n"
            "هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.perf_thread = PerformanceThread(self.performance_service, 'repair')
            self.perf_thread.finished.connect(self.on_performance_finished)
            self.perf_thread.start()
    
    def cleanup_data(self):
        """حذف البيانات القديمة"""
        days, ok = QMessageBox.getText(
            self,
            "حذف البيانات القديمة",
            "حذف السجلات الأقدم من (أيام):",
            QLineEdit.Normal,
            "90"
        )
        
        if ok:
            try:
                days_int = int(days)
                self.perf_thread = PerformanceThread(
                    self.performance_service,
                    'cleanup',
                    days=days_int
                )
                self.perf_thread.finished.connect(self.on_performance_finished)
                self.perf_thread.start()
            except ValueError:
                QMessageBox.warning(self, "خطأ", "يرجى إدخال رقم صحيح")
    
    def analyze_performance(self):
        """تحليل الأداء"""
        try:
            analysis = self.performance_service.analyze_performance()
            
            result_text = "=== تحليل الأداء ===\n\n"
            
            result_text += f"حجم قاعدة البيانات: {analysis['database_size_mb']:.2f} MB\n"
            result_text += f"عدد الجداول: {analysis['table_count']}\n"
            result_text += f"عدد الفهارس: {analysis['index_count']}\n"
            result_text += f"صفحات فارغة: {analysis['freelist_count']}\n"
            
            if analysis['fragmentation_percent'] > 0:
                result_text += f"نسبة التجزئة: {analysis['fragmentation_percent']:.2f}%\n"
            
            result_text += "\n=== أكبر الجداول ===\n"
            for table in analysis['largest_tables'][:10]:
                result_text += f"{table['name']}: {table['rows']:,} صف, {table['size_kb']:.2f} KB\n"
            
            result_text += "\n=== التوصيات ===\n"
            if analysis['fragmentation_percent'] > 10:
                result_text += "• يُنصح بتشغيل VACUUM لتقليل التجزئة\n"
            if analysis['freelist_count'] > 100:
                result_text += "• يوجد صفحات فارغة كثيرة - قم بتشغيل التحسين\n"
            if analysis['database_size_mb'] > 100:
                result_text += "• قاعدة البيانات كبيرة - فكر في أرشفة البيانات القديمة\n"
            
            if not any([
                analysis['fragmentation_percent'] > 10,
                analysis['freelist_count'] > 100,
                analysis['database_size_mb'] > 100
            ]):
                result_text += "• قاعدة البيانات في حالة جيدة\n"
            
            self.analysis_text.setPlainText(result_text)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحليل الأداء: {str(e)}")
    
    def load_performance_info(self):
        """تحميل معلومات الأداء"""
        try:
            # Database metrics
            analysis = self.performance_service.analyze_performance()
            
            self.perf_labels['db_size'].setText(f"{analysis['database_size_mb']:.2f} MB")
            self.perf_labels['table_count'].setText(str(analysis['table_count']))
            self.perf_labels['index_count'].setText(str(analysis['index_count']))
            self.perf_labels['free_pages'].setText(str(analysis['freelist_count']))
            
            # System info
            system_info = self.performance_service.get_system_info()
            
            ram_percent = system_info.get('memory_percent', 0)
            self.perf_labels['ram_usage'].setText(f"{ram_percent:.1f}%")
            
            disk_free_gb = system_info.get('disk_free_gb', 0)
            self.perf_labels['disk_free'].setText(f"{disk_free_gb:.2f} GB")
            
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"فشل تحميل بعض المعلومات: {str(e)}")
    
    def on_performance_finished(self, success, message):
        """معالج انتهاء عملية الأداء"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        if success:
            QMessageBox.information(self, "نجح", message)
            self.load_performance_info()
        else:
            QMessageBox.critical(self, "خطأ", f"فشلت العملية: {message}")
    
    # ==================== Maintenance Tab ====================
    
    def create_maintenance_tab(self):
        """تبويب الصيانة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Maintenance Log
        log_group = QGroupBox("سجل الصيانة")
        log_layout = QVBoxLayout(log_group)
        
        self.maintenance_table = QTableWidget()
        self.maintenance_table.setColumnCount(5)
        self.maintenance_table.setHorizontalHeaderLabels([
            "نوع العملية", "الحالة", "وقت التنفيذ", "التاريخ", "المستخدم"
        ])
        self.maintenance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        log_layout.addWidget(self.maintenance_table)
        
        layout.addWidget(log_group)
        
        return widget
    
    def load_maintenance_log(self):
        """تحميل سجل الصيانة"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT 
                    ml.operation_type,
                    ml.status,
                    ml.execution_time_seconds,
                    ml.performed_at,
                    COALESCE(u.username, 'نظام') as username
                FROM maintenance_log ml
                LEFT JOIN users u ON ml.performed_by = u.id
                ORDER BY ml.performed_at DESC
                LIMIT 100
            """)
            
            logs = cursor.fetchall()
            self.maintenance_table.setRowCount(len(logs))
            
            operation_names = {
                'optimize': 'تحسين',
                'vacuum': 'ضغط',
                'analyze': 'تحليل',
                'repair': 'إصلاح',
                'cleanup': 'تنظيف'
            }
            
            status_names = {
                'completed': 'مكتمل',
                'failed': 'فشل',
                'in_progress': 'جاري'
            }
            
            for row, log in enumerate(logs):
                # Operation Type
                op_type = operation_names.get(log[0], log[0])
                self.maintenance_table.setItem(row, 0, QTableWidgetItem(op_type))
                
                # Status
                status = status_names.get(log[1], log[1])
                status_item = QTableWidgetItem(status)
                if log[1] == 'completed':
                    status_item.setForeground(Qt.darkGreen)
                elif log[1] == 'failed':
                    status_item.setForeground(Qt.red)
                self.maintenance_table.setItem(row, 1, status_item)
                
                # Execution Time
                exec_time = f"{log[2]:.2f} ثانية" if log[2] else "-"
                self.maintenance_table.setItem(row, 2, QTableWidgetItem(exec_time))
                
                # Date
                date_str = log[3]
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str)
                        date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                self.maintenance_table.setItem(row, 3, QTableWidgetItem(date_str))
                
                # User
                self.maintenance_table.setItem(row, 4, QTableWidgetItem(log[4]))
                
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"فشل تحميل سجل الصيانة: {str(e)}")
    
    # ==================== Settings Tab ====================
    
    def create_settings_tab(self):
        """تبويب الإعدادات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # System Settings
        settings_group = QGroupBox("إعدادات النظام")
        settings_layout = QGridLayout(settings_group)
        
        row = 0
        
        # Company Info
        settings_layout.addWidget(QLabel("اسم الشركة:"), row, 0)
        self.company_name_edit = QLineEdit()
        settings_layout.addWidget(self.company_name_edit, row, 1)
        row += 1
        
        settings_layout.addWidget(QLabel("عنوان الشركة:"), row, 0)
        self.company_address_edit = QLineEdit()
        settings_layout.addWidget(self.company_address_edit, row, 1)
        row += 1
        
        settings_layout.addWidget(QLabel("هاتف الشركة:"), row, 0)
        self.company_phone_edit = QLineEdit()
        settings_layout.addWidget(self.company_phone_edit, row, 1)
        row += 1
        
        settings_layout.addWidget(QLabel("الرقم الضريبي:"), row, 0)
        self.tax_number_edit = QLineEdit()
        settings_layout.addWidget(self.tax_number_edit, row, 1)
        row += 1
        
        # Save button
        save_btn = QPushButton("حفظ الإعدادات")
        save_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_btn, row, 0, 1, 2)
        
        layout.addWidget(settings_group)
        
        # App Info
        info_group = QGroupBox("معلومات التطبيق")
        info_layout = QGridLayout(info_group)
        
        self.app_info_labels = {}
        info_items = [
            ("version", "إصدار التطبيق"),
            ("db_version", "إصدار قاعدة البيانات"),
            ("db_path", "مسار قاعدة البيانات")
        ]
        
        for i, (key, label) in enumerate(info_items):
            info_layout.addWidget(QLabel(f"{label}:"), i, 0)
            value_label = QLabel("-")
            value_label.setStyleSheet("font-weight: bold;")
            self.app_info_labels[key] = value_label
            info_layout.addWidget(value_label, i, 1)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def load_settings(self):
        """تحميل الإعدادات"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT key, value FROM system_settings WHERE category = 'general'")
            
            settings = dict(cursor.fetchall())
            
            self.company_name_edit.setText(settings.get('company_name', ''))
            self.company_address_edit.setText(settings.get('company_address', ''))
            self.company_phone_edit.setText(settings.get('company_phone', ''))
            self.tax_number_edit.setText(settings.get('tax_number', ''))
            
            self.app_info_labels['version'].setText(settings.get('app_version', '1.0.0'))
            self.app_info_labels['db_version'].setText(settings.get('db_version', '1.0'))
            self.app_info_labels['db_path'].setText(self.db_manager.db_path)
            
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"فشل تحميل الإعدادات: {str(e)}")
    
    def save_settings(self):
        """حفظ الإعدادات"""
        try:
            cursor = self.db_manager.connection.cursor()
            
            settings = {
                'company_name': self.company_name_edit.text(),
                'company_address': self.company_address_edit.text(),
                'company_phone': self.company_phone_edit.text(),
                'tax_number': self.tax_number_edit.text()
            }
            
            for key, value in settings.items():
                cursor.execute("""
                    UPDATE system_settings 
                    SET value = ?
                    WHERE key = ?
                """, (value, key))
            
            self.db_manager.connection.commit()
            QMessageBox.information(self, "نجح", "تم حفظ الإعدادات بنجاح")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حفظ الإعدادات: {str(e)}")
            self.db_manager.connection.rollback()
    
    # ==================== Data Loading ====================
    
    def load_data(self):
        """تحميل جميع البيانات"""
        self.load_backups()
        self.load_performance_info()
        self.load_maintenance_log()
        self.load_settings()

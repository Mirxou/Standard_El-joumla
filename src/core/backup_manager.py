"""
نظام النسخ الاحتياطي التلقائي
Automatic Backup System

يوفر نظام نسخ احتياطي تلقائي مع ضغط ودوران وجدولة
Provides automatic backup with compression, rotation, and scheduling
"""

import os
import shutil
import sqlite3
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import time
import logging

# إعداد المسجل
logger = logging.getLogger(__name__)


class BackupConfig:
    """إعدادات النسخ الاحتياطي"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        تهيئة الإعدادات
        
        Args:
            config_dict: قاموس الإعدادات
        """
        config = config_dict or {}
        
        # المسارات
        self.db_path: str = config.get('db_path', 'database.db')
        self.backup_dir: str = config.get('backup_dir', 'backups')
        
        # الجدولة
        self.auto_backup: bool = config.get('auto_backup', True)
        self.backup_interval_hours: int = config.get('backup_interval_hours', 24)
        self.backup_time: Optional[str] = config.get('backup_time')  # "03:00" صيغة 24 ساعة
        
        # الدوران
        self.max_backups: int = config.get('max_backups', 7)
        self.keep_daily: int = config.get('keep_daily', 7)
        self.keep_weekly: int = config.get('keep_weekly', 4)
        self.keep_monthly: int = config.get('keep_monthly', 6)
        
        # الضغط
        self.compress: bool = config.get('compress', True)
        self.compression_level: int = config.get('compression_level', 6)
        
        # الأمان
        self.verify_backup: bool = config.get('verify_backup', True)
        self.backup_wal: bool = config.get('backup_wal', True)


class BackupInfo:
    """معلومات النسخة الاحتياطية"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        self.created_at = datetime.fromtimestamp(os.path.getctime(filepath)) if os.path.exists(filepath) else None
        self.is_compressed = filepath.endswith('.gz')
        
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'filepath': self.filepath,
            'filename': self.filename,
            'size': self.size,
            'size_mb': round(self.size / (1024 * 1024), 2),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_compressed': self.is_compressed
        }


class BackupManager:
    """
    مدير النسخ الاحتياطي التلقائي
    
    يوفر:
    - نسخ احتياطي يدوي وتلقائي
    - ضغط الملفات
    - دوران النسخ (يومي، أسبوعي، شهري)
    - جدولة النسخ الاحتياطي
    - استعادة من النسخ الاحتياطية
    - التحقق من سلامة النسخ
    """
    
    def __init__(self, config: Optional[BackupConfig] = None):
        """
        تهيئة مدير النسخ الاحتياطي
        
        Args:
            config: إعدادات النسخ الاحتياطي
        """
        self.config = config or BackupConfig()
        
        # إنشاء مجلد النسخ الاحتياطي
        os.makedirs(self.config.backup_dir, exist_ok=True)
        
        # حالة الجدولة
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_stop = threading.Event()
        self._last_backup: Optional[datetime] = None
        
        # تحميل آخر نسخة احتياطية
        self._load_last_backup_time()
        
    def create_backup(self, description: str = "") -> Dict[str, Any]:
        """
        إنشاء نسخة احتياطية
        
        Args:
            description: وصف النسخة الاحتياطية
            
        Returns:
            معلومات النسخة الاحتياطية
        """
        try:
            # اسم الملف
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.db"
            
            if self.config.compress:
                backup_filename += ".gz"
                
            backup_path = os.path.join(self.config.backup_dir, backup_filename)
            
            # نسخ قاعدة البيانات
            logger.info(f"Creating backup: {backup_filename}")
            
            if self.config.compress:
                self._backup_compressed(backup_path)
            else:
                self._backup_simple(backup_path)
                
            # التحقق من النسخة الاحتياطية
            if self.config.verify_backup:
                if not self._verify_backup(backup_path):
                    raise Exception("Backup verification failed")
                    
            # حفظ المعلومات
            backup_info = BackupInfo(backup_path)
            self._save_backup_metadata(backup_info, description)
            
            # تحديث آخر نسخة احتياطية
            self._last_backup = datetime.now()
            self._save_last_backup_time()
            
            # تطبيق سياسة الدوران
            self._apply_rotation_policy()
            
            logger.info(f"Backup created successfully: {backup_filename} ({backup_info.size_mb} MB)")
            
            return {
                'success': True,
                'backup_info': backup_info.to_dict(),
                'description': description
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def _backup_simple(self, backup_path: str):
        """نسخ بسيط بدون ضغط"""
        # استخدام API النسخ الاحتياطي من SQLite
        source_conn = sqlite3.connect(self.config.db_path)
        backup_conn = sqlite3.connect(backup_path)
        
        with backup_conn:
            source_conn.backup(backup_conn)
            
        source_conn.close()
        backup_conn.close()
        
    def _backup_compressed(self, backup_path: str):
        """نسخ مع ضغط"""
        # نسخ إلى ملف مؤقت
        temp_path = backup_path.replace('.gz', '')
        self._backup_simple(temp_path)
        
        # ضغط الملف
        with open(temp_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb', compresslevel=self.config.compression_level) as f_out:
                shutil.copyfileobj(f_in, f_out)
                
        # حذف الملف المؤقت
        os.remove(temp_path)
        
    def _verify_backup(self, backup_path: str) -> bool:
        """
        التحقق من سلامة النسخة الاحتياطية
        
        Args:
            backup_path: مسار النسخة الاحتياطية
            
        Returns:
            True إذا كانت سليمة
        """
        try:
            if backup_path.endswith('.gz'):
                # فك الضغط للتحقق
                temp_path = backup_path.replace('.gz', '.temp')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                        
                # التحقق من قاعدة البيانات
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                conn.close()
                
                # حذف الملف المؤقت
                os.remove(temp_path)
                
                return result == 'ok'
            else:
                # التحقق مباشرة
                conn = sqlite3.connect(backup_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                conn.close()
                
                return result == 'ok'
                
        except Exception as e:
            logger.error(f"Backup verification error: {str(e)}")
            return False
            
    def restore_backup(self, backup_path: str, target_path: Optional[str] = None) -> Dict[str, Any]:
        """
        استعادة من نسخة احتياطية
        
        Args:
            backup_path: مسار النسخة الاحتياطية
            target_path: مسار الاستعادة (افتراضياً قاعدة البيانات الحالية)
            
        Returns:
            نتيجة الاستعادة
        """
        try:
            target = target_path or self.config.db_path
            
            # نسخ احتياطي للقاعدة الحالية
            if os.path.exists(target):
                backup_current = f"{target}.before_restore"
                shutil.copy2(target, backup_current)
                logger.info(f"Current database backed up to: {backup_current}")
                
            # استعادة
            if backup_path.endswith('.gz'):
                # فك الضغط واستعادة
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # نسخ مباشر
                shutil.copy2(backup_path, target)
                
            # التحقق من النسخة المستعادة
            conn = sqlite3.connect(target)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            
            if result != 'ok':
                # استعادة النسخة السابقة
                if os.path.exists(backup_current):
                    shutil.copy2(backup_current, target)
                raise Exception("Restored database integrity check failed")
                
            logger.info(f"Database restored successfully from: {backup_path}")
            
            return {
                'success': True,
                'backup_path': backup_path,
                'target_path': target
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def list_backups(self) -> List[BackupInfo]:
        """
        قائمة النسخ الاحتياطية
        
        Returns:
            قائمة معلومات النسخ الاحتياطية
        """
        backups = []
        
        for filename in os.listdir(self.config.backup_dir):
            if filename.startswith('backup_') and (filename.endswith('.db') or filename.endswith('.db.gz')):
                filepath = os.path.join(self.config.backup_dir, filename)
                backups.append(BackupInfo(filepath))
                
        # ترتيب حسب التاريخ (الأحدث أولاً)
        backups.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        
        return backups
        
    def _apply_rotation_policy(self):
        """تطبيق سياسة دوران النسخ الاحتياطية"""
        backups = self.list_backups()
        
        # تصنيف النسخ
        daily = []
        weekly = []
        monthly = []
        
        now = datetime.now()
        
        for backup in backups:
            if not backup.created_at:
                continue
                
            age_days = (now - backup.created_at).days
            
            # يومي (آخر 7 أيام)
            if age_days < self.config.keep_daily:
                daily.append(backup)
            # أسبوعي (آخر 4 أسابيع)
            elif age_days < self.config.keep_daily + (self.config.keep_weekly * 7):
                # الاحتفاظ بنسخة واحدة في الأسبوع
                week_num = backup.created_at.isocalendar()[1]
                if not any(b.created_at.isocalendar()[1] == week_num for b in weekly):
                    weekly.append(backup)
            # شهري (آخر 6 أشهر)
            elif age_days < self.config.keep_daily + (self.config.keep_weekly * 7) + (self.config.keep_monthly * 30):
                # الاحتفاظ بنسخة واحدة في الشهر
                month = backup.created_at.month
                if not any(b.created_at.month == month for b in monthly):
                    monthly.append(backup)
                    
        # النسخ المحفوظة
        keep_backups = set(daily + weekly + monthly)
        
        # حذف النسخ القديمة
        for backup in backups:
            if backup not in keep_backups:
                try:
                    os.remove(backup.filepath)
                    logger.info(f"Deleted old backup: {backup.filename}")
                except Exception as e:
                    logger.error(f"Failed to delete backup {backup.filename}: {str(e)}")
                    
    def _save_backup_metadata(self, backup_info: BackupInfo, description: str):
        """حفظ معلومات النسخة الاحتياطية"""
        metadata_file = backup_info.filepath + '.json'
        
        metadata = {
            'filename': backup_info.filename,
            'size': backup_info.size,
            'created_at': backup_info.created_at.isoformat() if backup_info.created_at else None,
            'description': description,
            'compressed': backup_info.is_compressed
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
    def start_scheduler(self):
        """بدء جدولة النسخ الاحتياطي التلقائي"""
        if not self.config.auto_backup:
            logger.info("Auto backup is disabled")
            return
            
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            logger.warning("Scheduler already running")
            return
            
        self._scheduler_stop.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info("Backup scheduler started")
        
    def stop_scheduler(self):
        """إيقاف جدولة النسخ الاحتياطي"""
        if self._scheduler_thread:
            self._scheduler_stop.set()
            self._scheduler_thread.join(timeout=5)
            logger.info("Backup scheduler stopped")
            
    def _scheduler_loop(self):
        """حلقة الجدولة"""
        while not self._scheduler_stop.is_set():
            try:
                # التحقق من وقت النسخ الاحتياطي
                if self._should_backup():
                    logger.info("Scheduled backup starting...")
                    result = self.create_backup(description="Automatic scheduled backup")
                    
                    if result['success']:
                        logger.info("Scheduled backup completed successfully")
                    else:
                        logger.error(f"Scheduled backup failed: {result.get('error')}")
                        
                # الانتظار دقيقة قبل التحقق مجدداً
                self._scheduler_stop.wait(60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                self._scheduler_stop.wait(60)
                
    def _should_backup(self) -> bool:
        """
        التحقق من ضرورة إنشاء نسخة احتياطية
        
        Returns:
            True إذا كان يجب إنشاء نسخة احتياطية
        """
        now = datetime.now()
        
        # إذا كان هناك وقت محدد
        if self.config.backup_time:
            target_hour, target_minute = map(int, self.config.backup_time.split(':'))
            
            # التحقق من الوقت الحالي
            if now.hour == target_hour and now.minute == target_minute:
                # التحقق من عدم وجود نسخة اليوم
                if self._last_backup:
                    if self._last_backup.date() == now.date():
                        return False
                return True
        else:
            # استخدام الفاصل الزمني
            if self._last_backup:
                elapsed = (now - self._last_backup).total_seconds() / 3600  # ساعات
                return elapsed >= self.config.backup_interval_hours
            else:
                return True  # أول نسخة احتياطية
                
        return False
        
    def _load_last_backup_time(self):
        """تحميل وقت آخر نسخة احتياطية"""
        metadata_file = os.path.join(self.config.backup_dir, '.last_backup')
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    timestamp = f.read().strip()
                    self._last_backup = datetime.fromisoformat(timestamp)
            except Exception as e:
                logger.error(f"Failed to load last backup time: {str(e)}")
                
    def _save_last_backup_time(self):
        """حفظ وقت آخر نسخة احتياطية"""
        metadata_file = os.path.join(self.config.backup_dir, '.last_backup')
        
        try:
            with open(metadata_file, 'w') as f:
                f.write(self._last_backup.isoformat())
        except Exception as e:
            logger.error(f"Failed to save last backup time: {str(e)}")
            
    def get_status(self) -> Dict[str, Any]:
        """
        الحصول على حالة النسخ الاحتياطي
        
        Returns:
            معلومات حالة النسخ الاحتياطي
        """
        backups = self.list_backups()
        
        total_size = sum(b.size for b in backups)
        
        return {
            'auto_backup_enabled': self.config.auto_backup,
            'scheduler_running': self._scheduler_thread and self._scheduler_thread.is_alive(),
            'last_backup': self._last_backup.isoformat() if self._last_backup else None,
            'total_backups': len(backups),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'backup_dir': self.config.backup_dir,
            'latest_backup': backups[0].to_dict() if backups else None
        }


# مثيل عام
global_backup_manager: Optional[BackupManager] = None


def initialize_backup_manager(config: Optional[BackupConfig] = None) -> BackupManager:
    """
    تهيئة مدير النسخ الاحتياطي العام
    
    Args:
        config: إعدادات النسخ الاحتياطي
        
    Returns:
        مدير النسخ الاحتياطي
    """
    global global_backup_manager
    global_backup_manager = BackupManager(config)
    return global_backup_manager


def get_backup_manager() -> Optional[BackupManager]:
    """
    الحصول على مدير النسخ الاحتياطي العام
    
    Returns:
        مدير النسخ الاحتياطي أو None
    """
    return global_backup_manager

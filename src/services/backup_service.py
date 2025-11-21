"""
خدمة النسخ الاحتياطي والاستعادة
Backup & Restore Service
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable
import os
import shutil
import zipfile
import json
from datetime import datetime, timedelta
from pathlib import Path
import threading
import schedule

from ..core.database_manager import DatabaseManager


class BackupService:
    """خدمة إدارة النسخ الاحتياطي والاستعادة"""
    
    def __init__(self, db: DatabaseManager, backup_dir: Optional[str] = None):
        self.db = db
        self.backup_dir = Path(backup_dir) if backup_dir else Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self._auto_backup_enabled = False
        self._auto_backup_thread = None
        self._backup_schedule = None
        
    # ==================== Manual Backup ====================
    
    def create_backup(self, description: str = "", include_attachments: bool = True,
                     compress: bool = True) -> Dict[str, Any]:
        """إنشاء نسخة احتياطية"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # نسخ قاعدة البيانات
            db_backup_path = backup_path / "database.db"
            shutil.copy2(self.db.db_path, db_backup_path)
            
            files_backed_up = [str(db_backup_path)]
            total_size = os.path.getsize(db_backup_path)
            
            # نسخ المرفقات إن وجدت
            if include_attachments:
                attachments_dir = Path("data/attachments")
                if attachments_dir.exists():
                    backup_attachments = backup_path / "attachments"
                    shutil.copytree(attachments_dir, backup_attachments)
                    for file in backup_attachments.rglob("*"):
                        if file.is_file():
                            files_backed_up.append(str(file))
                            total_size += os.path.getsize(file)
            
            # حفظ metadata
            metadata = {
                'backup_name': backup_name,
                'timestamp': datetime.now().isoformat(),
                'description': description,
                'database_file': 'database.db',
                'include_attachments': include_attachments,
                'files_count': len(files_backed_up),
                'total_size_bytes': total_size,
                'db_version': self._get_db_version(),
                'app_version': '1.0'
            }
            
            metadata_path = backup_path / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # ضغط النسخة الاحتياطية
            if compress:
                zip_path = self.backup_dir / f"{backup_name}.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in backup_path.rglob("*"):
                        if file.is_file():
                            zipf.write(file, file.relative_to(backup_path))
                
                # حذف المجلد غير المضغوط
                shutil.rmtree(backup_path)
                
                metadata['compressed'] = True
                metadata['compressed_file'] = str(zip_path)
                metadata['compressed_size'] = os.path.getsize(zip_path)
            
            # تسجيل النسخة الاحتياطية في قاعدة البيانات
            self._log_backup(metadata)
            
            return {
                'success': True,
                'backup_name': backup_name,
                'path': str(zip_path if compress else backup_path),
                'size': metadata.get('compressed_size', total_size),
                'files_count': len(files_backed_up),
                'timestamp': metadata['timestamp']
            }
            
        except Exception as e:
            # تنظيف في حالة الفشل
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def restore_backup(self, backup_name: str, restore_attachments: bool = True) -> Dict[str, Any]:
        """استعادة نسخة احتياطية"""
        try:
            # البحث عن النسخة الاحتياطية
            zip_path = self.backup_dir / f"{backup_name}.zip"
            folder_path = self.backup_dir / backup_name
            
            backup_path = None
            is_compressed = False
            
            if zip_path.exists():
                backup_path = zip_path
                is_compressed = True
            elif folder_path.exists():
                backup_path = folder_path
            else:
                return {'success': False, 'error': 'النسخة الاحتياطية غير موجودة'}
            
            # إنشاء مجلد مؤقت للاستخراج
            temp_dir = self.backup_dir / "temp_restore"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # استخراج النسخة الاحتياطية إن كانت مضغوطة
                if is_compressed:
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        zipf.extractall(temp_dir)
                else:
                    shutil.copytree(folder_path, temp_dir, dirs_exist_ok=True)
                
                # قراءة metadata
                metadata_path = temp_dir / "metadata.json"
                if not metadata_path.exists():
                    return {'success': False, 'error': 'ملف metadata غير موجود'}
                
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # إنشاء نسخة احتياطية من الوضع الحالي قبل الاستعادة
                current_backup = self.create_backup(
                    description="نسخة احتياطية تلقائية قبل الاستعادة",
                    compress=True
                )
                
                # استعادة قاعدة البيانات
                db_backup = temp_dir / metadata['database_file']
                if db_backup.exists():
                    # إغلاق الاتصال الحالي
                    if hasattr(self.db, 'connection') and self.db.connection:
                        self.db.connection.close()
                    
                    # استبدال قاعدة البيانات
                    shutil.copy2(db_backup, self.db.db_path)
                    
                    # إعادة الاتصال
                    self.db.initialize()
                
                # استعادة المرفقات
                if restore_attachments and metadata.get('include_attachments'):
                    attachments_backup = temp_dir / "attachments"
                    if attachments_backup.exists():
                        attachments_dir = Path("data/attachments")
                        if attachments_dir.exists():
                            shutil.rmtree(attachments_dir)
                        shutil.copytree(attachments_backup, attachments_dir)
                
                # تسجيل الاستعادة
                self._log_restore(backup_name, metadata)
                
                return {
                    'success': True,
                    'backup_name': backup_name,
                    'timestamp': metadata['timestamp'],
                    'current_backup': current_backup.get('backup_name')
                }
                
            finally:
                # تنظيف المجلد المؤقت
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self, limit: int = 50) -> List[Dict[str, Any]]:
        """قائمة النسخ الاحتياطية المتوفرة"""
        backups = []
        
        # البحث عن النسخ المضغوطة
        for zip_file in self.backup_dir.glob("backup_*.zip"):
            try:
                with zipfile.ZipFile(zip_file, 'r') as zipf:
                    if 'metadata.json' in zipf.namelist():
                        metadata_content = zipf.read('metadata.json')
                        metadata = json.loads(metadata_content)
                        metadata['file_path'] = str(zip_file)
                        metadata['file_size'] = os.path.getsize(zip_file)
                        backups.append(metadata)
            except:
                continue
        
        # البحث عن النسخ غير المضغوطة
        for backup_dir in self.backup_dir.glob("backup_*"):
            if backup_dir.is_dir():
                metadata_file = backup_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            metadata['file_path'] = str(backup_dir)
                            metadata['file_size'] = sum(
                                f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
                            )
                            backups.append(metadata)
                    except:
                        continue
        
        # الترتيب حسب التاريخ (الأحدث أولاً)
        backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return backups[:limit]
    
    def delete_backup(self, backup_name: str) -> bool:
        """حذف نسخة احتياطية"""
        try:
            zip_path = self.backup_dir / f"{backup_name}.zip"
            folder_path = self.backup_dir / backup_name
            
            if zip_path.exists():
                os.remove(zip_path)
                return True
            elif folder_path.exists():
                shutil.rmtree(folder_path)
                return True
            
            return False
        except:
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10, keep_days: int = 30) -> int:
        """تنظيف النسخ الاحتياطية القديمة"""
        backups = self.list_backups(limit=1000)
        deleted_count = 0
        
        # الاحتفاظ بأحدث keep_count نسخة
        backups_to_delete = backups[keep_count:]
        
        # حذف النسخ الأقدم من keep_days يوم
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for backup in backups_to_delete:
            try:
                backup_date = datetime.fromisoformat(backup['timestamp'])
                if backup_date < cutoff_date:
                    if self.delete_backup(backup['backup_name']):
                        deleted_count += 1
            except:
                continue
        
        return deleted_count
    
    # ==================== Auto Backup ====================
    
    def enable_auto_backup(self, interval_hours: int = 24, 
                          keep_count: int = 10) -> bool:
        """تفعيل النسخ الاحتياطي التلقائي"""
        if self._auto_backup_enabled:
            return False
        
        def auto_backup_job():
            """مهمة النسخ الاحتياطي التلقائي"""
            result = self.create_backup(
                description=f"نسخة احتياطية تلقائية - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                compress=True
            )
            
            if result.get('success'):
                # تنظيف النسخ القديمة
                self.cleanup_old_backups(keep_count=keep_count)
        
        # جدولة المهمة
        schedule.every(interval_hours).hours.do(auto_backup_job)
        
        # بدء خيط الجدولة
        def run_scheduler():
            while self._auto_backup_enabled:
                schedule.run_pending()
                threading.Event().wait(60)  # التحقق كل دقيقة
        
        self._auto_backup_enabled = True
        self._auto_backup_thread = threading.Thread(target=run_scheduler, daemon=True)
        self._auto_backup_thread.start()
        
        # تنفيذ نسخة احتياطية فورية
        auto_backup_job()
        
        return True
    
    def disable_auto_backup(self) -> bool:
        """تعطيل النسخ الاحتياطي التلقائي"""
        if not self._auto_backup_enabled:
            return False
        
        self._auto_backup_enabled = False
        schedule.clear()
        
        return True
    
    # ==================== Export/Import ====================
    
    def export_data(self, tables: List[str], output_path: str,
                   format: str = 'json') -> Dict[str, Any]:
        """تصدير بيانات جداول محددة"""
        try:
            data = {}
            total_records = 0
            
            for table in tables:
                result = self.db.execute_query(f"SELECT * FROM {table}")
                data[table] = result
                total_records += len(result)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            return {
                'success': True,
                'file': str(output_file),
                'tables_count': len(tables),
                'records_count': total_records,
                'file_size': os.path.getsize(output_file)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== Helper Methods ====================
    
    def _get_db_version(self) -> str:
        """الحصول على إصدار قاعدة البيانات"""
        try:
            result = self.db.execute_query(
                "SELECT value FROM system_settings WHERE key = 'db_version'"
            )
            return result[0]['value'] if result else '1.0'
        except:
            return '1.0'
    
    def _log_backup(self, metadata: Dict[str, Any]):
        """تسجيل عملية النسخ الاحتياطي"""
        try:
            self.db.execute_update(
                """INSERT INTO backup_history 
                   (backup_name, description, size_bytes, files_count, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                [metadata['backup_name'], metadata.get('description', ''),
                 metadata.get('compressed_size', metadata['total_size_bytes']),
                 metadata['files_count'], metadata['timestamp']]
            )
        except:
            pass
    
    def _log_restore(self, backup_name: str, metadata: Dict[str, Any]):
        """تسجيل عملية الاستعادة"""
        try:
            self.db.execute_update(
                """INSERT INTO restore_history 
                   (backup_name, restored_at)
                   VALUES (?, ?)""",
                [backup_name, datetime.now().isoformat()]
            )
        except:
            pass
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """إحصائيات النسخ الاحتياطي"""
        backups = self.list_backups(limit=1000)
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'auto_backup_enabled': self._auto_backup_enabled
            }
        
        total_size = sum(b.get('file_size', 0) for b in backups)
        
        return {
            'total_backups': len(backups),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_backup': backups[-1]['timestamp'],
            'newest_backup': backups[0]['timestamp'],
            'auto_backup_enabled': self._auto_backup_enabled,
            'average_size': total_size // len(backups) if backups else 0
        }

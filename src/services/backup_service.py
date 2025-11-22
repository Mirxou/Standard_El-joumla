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
import hashlib

# Optional cryptography imports (present in requirements.txt)
try:
    import base64
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    _CRYPTO_AVAILABLE = True
except Exception:
    _CRYPTO_AVAILABLE = False
import hashlib
from base64 import urlsafe_b64encode, urlsafe_b64decode

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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
        
        # Encryption state/config
        self._encryption_password: Optional[str] = None
        self._fernet_key: Optional[bytes] = None
        self._config_path = self.backup_dir / "backup_config.json"
        self._config = self._load_config()

    # ==================== Config & Encryption ====================
    # ملاحظة: تم نقل التنفيذ إلى قسم "Encryption Support" أدناه لتوحيد الأساليب.
        
    # ==================== Manual Backup ====================
    
    def create_backup(self, description: str = "", include_attachments: bool = True,
                     compress: bool = True, encrypt: Optional[bool] = None) -> Dict[str, Any]:
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

            # حساب بصمة قاعدة البيانات (سلامة)
            try:
                with open(db_backup_path, 'rb') as _fdb:
                    metadata['database_checksum_sha256'] = hashlib.sha256(_fdb.read()).hexdigest()
            except Exception:
                metadata['database_checksum_sha256'] = None
            
            metadata_path = backup_path / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # تحديد سياسة الضغط والتشفير
            encrypt = self._resolve_encrypt(encrypt)
            # إذا كان هناك تشفير، نُفضّل الضغط أولاً لملف واحد ثم تشفيره
            zip_path = None
            final_path: Path = backup_path
            
            if compress or encrypt:
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
                final_path = zip_path
            
            # تشفير الملف النهائي عند الحاجة
            if encrypt:
                if not self._fernet:
                    raise ValueError("لم يتم ضبط كلمة مرور التشفير. نادِ set_encryption_password أولاً.")
                enc_path = Path(str(final_path) + ".enc")
                self._encrypt_file(final_path, enc_path)
                if final_path.exists() and final_path.is_file():
                    final_path.unlink()
                final_path = enc_path
                metadata['encrypted'] = True
                metadata['encrypted_file'] = str(enc_path)
                # حساب بصمة الملف المضغوط قبل التشفير إن أمكن
                try:
                    with open(enc_path, 'rb') as _fenc:
                        metadata['encrypted_payload_checksum_sha256'] = hashlib.sha256(_fenc.read()).hexdigest()
                except Exception:
                    metadata['encrypted_payload_checksum_sha256'] = None
            
            # تسجيل النسخة الاحتياطية في قاعدة البيانات
            self._log_backup(metadata)
            
            return {
                'success': True,
                'backup_name': backup_name,
                'path': str(final_path if (compress or encrypt) else backup_path),
                'size': os.path.getsize(final_path) if final_path.exists() else metadata.get('compressed_size', total_size),
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
    
    def restore_backup(self, backup_name: str, restore_attachments: bool = True, password: Optional[str] = None) -> Dict[str, Any]:
        """استعادة نسخة احتياطية"""
        try:
            # البحث عن النسخة الاحتياطية
            enc_zip_path = self.backup_dir / f"{backup_name}.zip.enc"
            enc_path = self.backup_dir / f"{backup_name}.enc"
            zip_path = self.backup_dir / f"{backup_name}.zip"
            folder_path = self.backup_dir / backup_name
            
            backup_path = None
            is_compressed = False
            is_encrypted = False
            
            if enc_zip_path.exists():
                backup_path = enc_zip_path
                is_compressed = True
                is_encrypted = True
            elif enc_path.exists():
                backup_path = enc_path
                is_encrypted = True
            elif zip_path.exists():
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
                current_file: Optional[Path] = None
                
                # فك التشفير إذا لزم
                if is_encrypted:
                    # إعداد كلمة المرور إن تم تمريرها
                    if password is not None:
                        self.set_encryption_password(password)
                    if not self._fernet:
                        return {'success': False, 'error': 'لم يتم ضبط كلمة مرور التشفير'}
                    dec_file = temp_dir / "decrypted_payload"
                    self._decrypt_file(backup_path, dec_file)
                    current_file = dec_file
                else:
                    current_file = backup_path
                
                # استخراج النسخة الاحتياطية إن كانت مضغوطة
                if is_compressed:
                    with zipfile.ZipFile(current_file, 'r') as zipf:
                        zipf.extractall(temp_dir)
                    current_dir = temp_dir
                else:
                    if current_file.is_dir():
                        shutil.copytree(current_file, temp_dir, dirs_exist_ok=True)
                        current_dir = temp_dir
                    else:
                        # نتوقع أن يكون current_file مجلد نسخ غير مضغوط
                        return {'success': False, 'error': 'صيغة النسخة غير مدعومة'}
                
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
                    # تحقق من سلامة قاعدة البيانات المنسوخة
                    try:
                        with open(db_backup, 'rb') as _chk:
                            current_checksum = hashlib.sha256(_chk.read()).hexdigest()
                        expected_checksum = metadata.get('database_checksum_sha256')
                        if expected_checksum and current_checksum != expected_checksum:
                            return {'success': False, 'error': 'فشل التحقق من سلامة قاعدة البيانات (بصمة غير مطابقة)'}
                    except Exception:
                        pass

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
                    'current_backup': current_backup.get('backup_name'),
                    'checksum_verified': bool(metadata.get('database_checksum_sha256'))
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
        for enc_zip_file in self.backup_dir.glob("backup_*.zip.enc"):
            try:
                # لا يمكن قراءة metadata مباشرة؛ نضع معلومات أساسية
                stat = enc_zip_file.stat()
                backups.append({
                    'backup_name': enc_zip_file.stem.replace('.zip', ''),
                    'timestamp': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'file_path': str(enc_zip_file),
                    'file_size': stat.st_size,
                    'compressed': True,
                    'encrypted': True
                })
            except:
                continue
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
        for enc_file in self.backup_dir.glob("backup_*.enc"):
            try:
                stat = enc_file.stat()
                backups.append({
                    'backup_name': enc_file.stem,
                    'timestamp': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'file_path': str(enc_file),
                    'file_size': stat.st_size,
                    'compressed': False,
                    'encrypted': True
                })
            except:
                continue
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

    # ==================== Encryption Support ====================
    def set_encryption_password(self, password: str, iterations: int = 200_000) -> None:
        """تهيئة مفتاح التشفير من كلمة مرور آمنة (لا تُخزّن الكلمة)."""
        # إنشاء salt أو استخدام الموجود
        enc_cfg = self._config.get('encryption', {})
        salt = enc_cfg.get('salt')
        if salt is None:
            salt_bytes = os.urandom(16)
            enc_cfg['salt'] = urlsafe_b64encode(salt_bytes).decode('utf-8')
        else:
            salt_bytes = urlsafe_b64decode(enc_cfg['salt'].encode('utf-8')) if isinstance(salt, str) else salt
        enc_cfg['enabled'] = True
        enc_cfg['kdf'] = 'PBKDF2HMAC'
        enc_cfg['iterations'] = iterations
        self._config['encryption'] = enc_cfg
        self._save_config()
        
        # اشتقاق مفتاح Fernet (base64 urlsafe 32-byte)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=iterations,
        )
        key = urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        self._fernet = Fernet(key)

    def disable_encryption(self) -> None:
        enc_cfg = self._config.get('encryption', {})
        enc_cfg['enabled'] = False
        self._config['encryption'] = enc_cfg
        self._save_config()
        self._fernet = None

    def is_encryption_enabled(self) -> bool:
        return bool(self._config.get('encryption', {}).get('enabled'))

    def _encrypt_file(self, src: Path, dst: Path) -> None:
        if not self._fernet:
            raise ValueError("encryption key not initialized")
        data = src.read_bytes()
        encrypted = self._fernet.encrypt(data)
        dst.write_bytes(encrypted)

    def _decrypt_file(self, src: Path, dst: Path) -> None:
        if not self._fernet:
            raise ValueError("encryption key not initialized")
        data = src.read_bytes()
        decrypted = self._fernet.decrypt(data)
        dst.write_bytes(decrypted)

    def _resolve_encrypt(self, encrypt: Optional[bool]) -> bool:
        if encrypt is not None:
            return encrypt
        return bool(self._config.get('encryption', {}).get('enabled'))

    # ==================== Config Persistence ====================
    def _load_config(self) -> Dict[str, Any]:
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        # Default config
        return {
            'encryption': {
                'enabled': False
            }
        }

    def _save_config(self) -> None:
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
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

    # ==================== Verification ====================
    def verify_backup(self, backup_name: str, password: Optional[str] = None) -> Dict[str, Any]:
        """التحقق من سلامة نسخة احتياطية عبر مقارنة البصمة"""
        try:
            # استخدم مسار الاستعادة لكن بدون استبدال قاعدة البيانات الحالية
            enc_zip_path = self.backup_dir / f"{backup_name}.zip.enc"
            enc_path = self.backup_dir / f"{backup_name}.enc"
            zip_path = self.backup_dir / f"{backup_name}.zip"
            folder_path = self.backup_dir / backup_name
            source = None
            is_encrypted = False
            is_compressed = False
            if enc_zip_path.exists():
                source = enc_zip_path; is_encrypted = True; is_compressed = True
            elif enc_path.exists():
                source = enc_path; is_encrypted = True
            elif zip_path.exists():
                source = zip_path; is_compressed = True
            elif folder_path.exists():
                source = folder_path
            else:
                return {'success': False, 'error': 'النسخة غير موجودة'}

            temp_dir = self.backup_dir / "temp_verify"
            temp_dir.mkdir(parents=True, exist_ok=True)
            try:
                working_file = source
                if is_encrypted:
                    if password is not None:
                        self.set_encryption_password(password)
                    if not self._fernet:
                        return {'success': False, 'error': 'لم يتم ضبط كلمة مرور التشفير'}
                    decrypted = temp_dir / "payload.dec"
                    self._decrypt_file(source, decrypted)
                    working_file = decrypted
                if is_compressed:
                    with zipfile.ZipFile(working_file, 'r') as zipf:
                        zipf.extractall(temp_dir)
                    working_dir = temp_dir
                else:
                    if working_file.is_dir():
                        working_dir = working_file
                    else:
                        return {'success': False, 'error': 'صيغة غير مدعومة'}
                meta_path = working_dir / 'metadata.json'
                if not meta_path.exists():
                    return {'success': False, 'error': 'metadata مفقود'}
                metadata = json.load(open(meta_path, 'r', encoding='utf-8'))
                db_file = working_dir / metadata.get('database_file', 'database.db')
                if not db_file.exists():
                    return {'success': False, 'error': 'ملف قاعدة البيانات داخل النسخة مفقود'}
                with open(db_file, 'rb') as fdb:
                    checksum = hashlib.sha256(fdb.read()).hexdigest()
                expected = metadata.get('database_checksum_sha256')
                return {
                    'success': True,
                    'backup_name': backup_name,
                    'expected': expected,
                    'calculated': checksum,
                    'match': bool(expected and checksum == expected)
                }
            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
        except Exception as e:
            return {'success': False, 'error': str(e)}

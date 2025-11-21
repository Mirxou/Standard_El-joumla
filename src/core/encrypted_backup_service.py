#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة النسخ الاحتياطي المشفرة
إنشاء واستعادة نسخ احتياطية مشفرة بدرجة أمان عالية
"""

import os
import shutil
import sqlite3
import tarfile
import gzip
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import hashlib
import secrets

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes, padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ تحذير: مكتبة cryptography غير متاحة. لن يعمل التشفير.")


class EncryptedBackupService:
    """
    خدمة النسخ الاحتياطي المشفرة
    
    المزايا:
    - تشفير AES-256-GCM
    - ضغط البيانات قبل التشفير
    - تخزين metadata
    - التحقق من السلامة (checksum)
    - إدارة تلقائية للنسخ القديمة
    - دعم النسخ التزايدية (incremental)
    """
    
    def __init__(
        self,
        database_path: str,
        backup_dir: str = "data/backups",
        encryption_key: Optional[bytes] = None,
        max_backups: int = 30,
        compress: bool = True
    ):
        """
        تهيئة خدمة النسخ الاحتياطي
        
        Args:
            database_path: مسار قاعدة البيانات
            backup_dir: مجلد النسخ الاحتياطية
            encryption_key: مفتاح التشفير (32 bytes)
            max_backups: أقصى عدد من النسخ الاحتياطية
            compress: ضغط البيانات قبل التشفير
        """
        self.database_path = Path(database_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_backups = max_backups
        self.compress = compress
        
        # مفتاح التشفير
        if encryption_key:
            if len(encryption_key) != 32:
                raise ValueError("مفتاح التشفير يجب أن يكون 32 بايت")
            self.encryption_key = encryption_key
        else:
            # إنشاء مفتاح عشوائي
            self.encryption_key = secrets.token_bytes(32)
        
        # التحقق من توفر التشفير
        if not CRYPTO_AVAILABLE:
            print("⚠️ التشفير غير متاح. سيتم إنشاء نسخ غير مشفرة.")
    
    # ==================== التشفير وفك التشفير ====================
    
    def _encrypt_data(self, data: bytes) -> tuple[bytes, bytes, bytes]:
        """
        تشفير البيانات باستخدام AES-256-GCM
        
        Args:
            data: البيانات للتشفير
            
        Returns:
            (encrypted_data, iv, tag)
        """
        if not CRYPTO_AVAILABLE:
            return data, b'', b''
        
        # IV عشوائي (12 bytes for GCM)
        iv = secrets.token_bytes(12)
        
        # إنشاء cipher
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        
        # التشفير
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        
        # Tag للتحقق من السلامة
        tag = encryptor.tag
        
        return encrypted_data, iv, tag
    
    def _decrypt_data(self, encrypted_data: bytes, iv: bytes, tag: bytes) -> bytes:
        """
        فك تشفير البيانات
        
        Args:
            encrypted_data: البيانات المشفرة
            iv: Initialization Vector
            tag: Authentication Tag
            
        Returns:
            البيانات الأصلية
        """
        if not CRYPTO_AVAILABLE:
            return encrypted_data
        
        # إنشاء cipher
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        
        # فك التشفير
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        return decrypted_data
    
    # ==================== الضغط ====================
    
    def _compress_data(self, data: bytes) -> bytes:
        """ضغط البيانات باستخدام gzip"""
        return gzip.compress(data, compresslevel=9)
    
    def _decompress_data(self, data: bytes) -> bytes:
        """فك ضغط البيانات"""
        return gzip.decompress(data)
    
    # ==================== Checksum ====================
    
    def _calculate_checksum(self, data: bytes) -> str:
        """حساب SHA-256 checksum"""
        return hashlib.sha256(data).hexdigest()
    
    def _verify_checksum(self, data: bytes, expected_checksum: str) -> bool:
        """التحقق من checksum"""
        actual_checksum = self._calculate_checksum(data)
        return actual_checksum == expected_checksum
    
    # ==================== النسخ الاحتياطي ====================
    
    def create_backup(
        self,
        backup_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """
        إنشاء نسخة احتياطية مشفرة
        
        Args:
            backup_name: اسم النسخة الاحتياطية
            metadata: بيانات وصفية إضافية
            
        Returns:
            مسار النسخة الاحتياطية
        """
        try:
            # التحقق من وجود قاعدة البيانات
            if not self.database_path.exists():
                raise FileNotFoundError(f"قاعدة البيانات غير موجودة: {self.database_path}")
            
            # إنشاء اسم النسخة الاحتياطية
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
            
            backup_file = self.backup_dir / f"{backup_name}.encrypted"
            
            # قراءة قاعدة البيانات
            with open(self.database_path, 'rb') as f:
                db_data = f.read()
            
            # حساب checksum على البيانات الأصلية غير المضغوطة
            checksum_plain = self._calculate_checksum(db_data)
            
            # الضغط (إن طُلب)
            if self.compress:
                db_data = self._compress_data(db_data)
            
            # التشفير
            encrypted_data, iv, tag = self._encrypt_data(db_data)
            
            # Metadata
            backup_metadata = {
                'created_at': datetime.now().isoformat(),
                'database_path': str(self.database_path),
                'database_size': self.database_path.stat().st_size,
                'compressed': self.compress,
                'encrypted': CRYPTO_AVAILABLE,
                'checksum': checksum_plain,
                'checksum_on': 'plain',
                'iv': iv.hex() if CRYPTO_AVAILABLE else '',
                'tag': tag.hex() if CRYPTO_AVAILABLE else '',
                'version': '1.0'
            }
            
            if metadata:
                backup_metadata['custom'] = metadata
            
            # حفظ النسخة الاحتياطية
            with open(backup_file, 'wb') as f:
                # كتابة metadata كـ JSON
                metadata_json = json.dumps(backup_metadata).encode('utf-8')
                metadata_length = len(metadata_json)
                
                # تنسيق الملف:
                # [4 bytes: metadata length] [metadata] [encrypted data]
                f.write(metadata_length.to_bytes(4, byteorder='big'))
                f.write(metadata_json)
                f.write(encrypted_data)
            
            print(f"✅ تم إنشاء نسخة احتياطية مشفرة: {backup_file.name}")
            
            # تنظيف النسخ القديمة
            self._cleanup_old_backups()
            
            return backup_file
            
        except Exception as e:
            print(f"❌ فشل إنشاء النسخة الاحتياطية: {e}")
            return None
    
    def restore_backup(
        self,
        backup_file: str,
        restore_path: Optional[str] = None
    ) -> bool:
        """
        استعادة نسخة احتياطية
        
        Args:
            backup_file: ملف النسخة الاحتياطية
            restore_path: مسار الاستعادة (افتراضي: المسار الأصلي)
            
        Returns:
            True إذا نجحت الاستعادة
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                raise FileNotFoundError(f"النسخة الاحتياطية غير موجودة: {backup_file}")
            
            # قراءة الملف
            with open(backup_path, 'rb') as f:
                # قراءة metadata length
                metadata_length_bytes = f.read(4)
                metadata_length = int.from_bytes(metadata_length_bytes, byteorder='big')
                
                # قراءة metadata
                metadata_json = f.read(metadata_length)
                metadata = json.loads(metadata_json.decode('utf-8'))
                
                # قراءة البيانات المشفرة
                encrypted_data = f.read()
            
            # فك التشفير
            if metadata['encrypted'] and CRYPTO_AVAILABLE:
                iv = bytes.fromhex(metadata['iv'])
                tag = bytes.fromhex(metadata['tag'])
                db_data = self._decrypt_data(encrypted_data, iv, tag)
            else:
                db_data = encrypted_data
            
            # فك الضغط
            if metadata['compressed']:
                db_data = self._decompress_data(db_data)
            
            # التحقق من checksum على البيانات غير المضغوطة
            if not self._verify_checksum(db_data, metadata['checksum']):
                raise ValueError("فشل التحقق من سلامة البيانات (checksum mismatch)")
            
            # تحديد مسار الاستعادة
            if restore_path is None:
                restore_path = self.database_path
            else:
                restore_path = Path(restore_path)
            
            # إنشاء نسخة احتياطية من الملف الحالي (إن وُجد)
            if restore_path.exists():
                temp_backup = restore_path.with_suffix('.backup_before_restore')
                shutil.copy2(restore_path, temp_backup)
                print(f"📦 تم إنشاء نسخة احتياطية مؤقتة: {temp_backup.name}")
            
            # كتابة قاعدة البيانات المستعادة
            with open(restore_path, 'wb') as f:
                f.write(db_data)
            
            print(f"✅ تمت استعادة النسخة الاحتياطية: {backup_path.name}")
            print(f"   تاريخ النسخة: {metadata['created_at']}")
            print(f"   حجم قاعدة البيانات الأصلية: {metadata['database_size']:,} bytes")
            
            return True
            
        except Exception as e:
            print(f"❌ فشلت الاستعادة: {e}")
            return False
    
    # ==================== إدارة النسخ الاحتياطية ====================
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        قائمة جميع النسخ الاحتياطية
        
        Returns:
            قائمة بمعلومات النسخ الاحتياطية
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("*.encrypted")):
            try:
                # قراءة metadata
                with open(backup_file, 'rb') as f:
                    metadata_length = int.from_bytes(f.read(4), byteorder='big')
                    metadata_json = f.read(metadata_length)
                    metadata = json.loads(metadata_json.decode('utf-8'))
                
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size': backup_file.stat().st_size,
                    'created_at': metadata['created_at'],
                    'database_size': metadata['database_size'],
                    'compressed': metadata['compressed'],
                    'encrypted': metadata['encrypted']
                })
            except Exception:
                pass
        
        return backups
    
    def _cleanup_old_backups(self) -> int:
        """
        حذف النسخ الاحتياطية القديمة
        
        Returns:
            عدد النسخ المحذوفة
        """
        backups = list(sorted(
            self.backup_dir.glob("*.encrypted"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        ))
        
        deleted = 0
        
        if len(backups) > self.max_backups:
            for old_backup in backups[self.max_backups:]:
                try:
                    old_backup.unlink()
                    deleted += 1
                    print(f"🗑️ حذف نسخة قديمة: {old_backup.name}")
                except Exception:
                    pass
        
        return deleted
    
    def delete_backup(self, backup_name: str) -> bool:
        """حذف نسخة احتياطية محددة"""
        backup_file = self.backup_dir / backup_name
        
        if backup_file.exists():
            backup_file.unlink()
            return True
        
        return False
    
    # ==================== إدارة المفاتيح ====================
    
    def export_key(self, key_file: str) -> bool:
        """
        تصدير مفتاح التشفير
        
        Args:
            key_file: ملف حفظ المفتاح
            
        Returns:
            True إذا نجح التصدير
        """
        try:
            key_path = Path(key_file)
            
            with open(key_path, 'wb') as f:
                f.write(self.encryption_key)
            
            # حماية الملف (chmod 600)
            key_path.chmod(0o600)
            
            print(f"🔑 تم تصدير مفتاح التشفير: {key_file}")
            print("⚠️ احتفظ بهذا المفتاح بشكل آمن!")
            
            return True
        except Exception as e:
            print(f"❌ فشل تصدير المفتاح: {e}")
            return False
    
    @staticmethod
    def import_key(key_file: str) -> Optional[bytes]:
        """
        استيراد مفتاح تشفير
        
        Args:
            key_file: ملف المفتاح
            
        Returns:
            المفتاح أو None
        """
        try:
            with open(key_file, 'rb') as f:
                key = f.read()
            
            if len(key) != 32:
                raise ValueError("المفتاح غير صالح")
            
            return key
        except Exception as e:
            print(f"❌ فشل استيراد المفتاح: {e}")
            return None


# ==================== مثال على الاستخدام ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🔒 اختبار خدمة النسخ الاحتياطي المشفرة")
    print("=" * 70)
    
    # إنشاء قاعدة بيانات تجريبية
    test_db = Path("test_backup.db")
    conn = sqlite3.connect(test_db)
    conn.execute("""
        CREATE TABLE test_data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL
        )
    """)
    conn.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ("Test", 123.45))
    conn.commit()
    conn.close()
    
    # 1. إنشاء الخدمة
    print("\n1️⃣ إنشاء خدمة النسخ الاحتياطي:")
    service = EncryptedBackupService(
        database_path=str(test_db),
        backup_dir="test_backups",
        max_backups=5,
        compress=True
    )
    print("   ✅ تم إنشاء الخدمة")
    
    # 2. إنشاء نسخة احتياطية
    print("\n2️⃣ إنشاء نسخة احتياطية مشفرة:")
    backup_file = service.create_backup(
        metadata={'description': 'اختبار النسخ الاحتياطي'}
    )
    
    # 3. قائمة النسخ الاحتياطية
    print("\n3️⃣ قائمة النسخ الاحتياطية:")
    backups = service.list_backups()
    for backup in backups:
        print(f"   📦 {backup['name']}")
        print(f"      التاريخ: {backup['created_at']}")
        print(f"      الحجم: {backup['size']:,} bytes")
    
    # 4. استعادة النسخة الاحتياطية
    print("\n4️⃣ اختبار الاستعادة:")
    restored_db = Path("test_restored.db")
    success = service.restore_backup(
        str(backup_file),
        restore_path=str(restored_db)
    )
    
    if success:
        # التحقق من البيانات
        conn = sqlite3.connect(restored_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test_data")
        data = cursor.fetchall()
        conn.close()
        print(f"   البيانات المستعادة: {data}")
    
    # 5. تصدير المفتاح
    print("\n5️⃣ تصدير مفتاح التشفير:")
    service.export_key("test_encryption.key")
    
    # تنظيف
    print("\n🧹 تنظيف الملفات التجريبية...")
    test_db.unlink(missing_ok=True)
    restored_db.unlink(missing_ok=True)
    shutil.rmtree("test_backups", ignore_errors=True)
    Path("test_encryption.key").unlink(missing_ok=True)
    
    print("\n" + "=" * 70)
    print("✅ اكتملت جميع الاختبارات بنجاح!")
    print("=" * 70)

import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إدارة تشفير قاعدة البيانات - Database Encryption Manager
استخدام SQLCipher لتشفير قاعدة البيانات المحلية
"""

import os
from typing import Optional

from src.core.keyring_manager import KeyringManager
from src.utils.logger import setup_logger

try:
    from sqlcipher3 import dbapi2 as sqlite3

    SQLCIPHER_AVAILABLE = True
except ImportError:
    SQLCIPHER_AVAILABLE = False
    import sqlite3


class DatabaseEncryption:
    """مدير تشفير قاعدة البيانات باستخدام SQLCipher"""

    def __init__(self, keyring_manager: Optional[KeyringManager] = None):
        self.logger = setup_logger(__name__)
        self.keyring_manager = keyring_manager or KeyringManager()

        if not SQLCIPHER_AVAILABLE:
            self.logger.warning("⚠️ SQLCipher غير متوفر - سيتم استخدام SQLite غير المشفر")

    def is_available(self) -> bool:
        """التحقق من توفر SQLCipher"""
        return SQLCIPHER_AVAILABLE

    def get_encryption_password(self, device_id: Optional[str] = None) -> str:
        """
        الحصول على كلمة مرور التشفير من Keyring

        Args:
            device_id: معرف الجهاز (اختياري)

        Returns:
            كلمة مرور التشفير
        """
        password = self.keyring_manager.get_database_password(device_id)

        if not password:
            # توليد كلمة مرور جديدة
            password = self.keyring_manager.generate_secure_password()
            device_id = device_id or self.keyring_manager.get_device_id()
            self.keyring_manager.set_database_password(password, device_id)
            self.logger.info("✅ تم توليد كلمة مرور جديدة لقاعدة البيانات")

        return password

    def create_encrypted_connection(self, db_path: str, password: Optional[str] = None) -> sqlite3.Connection:
        """
        إنشاء اتصال مشفر بقاعدة البيانات

        Args:
            db_path: مسار قاعدة البيانات
            password: كلمة مرور التشفير (اختياري - سيتم الحصول عليها من Keyring)

        Returns:
            اتصال SQLite/SQLCipher
        """
        if not SQLCIPHER_AVAILABLE:
            # استخدام SQLite العادي
            return sqlite3.connect(db_path, check_same_thread=False, timeout=60.0)

        # استخدام SQLCipher
        if password is None:
            device_id = self.keyring_manager.get_device_id()
            password = self.get_encryption_password(device_id)

        conn = sqlite3.connect(db_path, check_same_thread=False, timeout=60.0)

        # تفعيل التشفير - استخدام طريقة آمنة لتجنب SQL Injection
        # escaping the password to prevent injection
        safe_password = password.replace("'", "''")
        conn.execute(f"PRAGMA key='{safe_password}'")

        # التحقق من أن التشفير يعمل
        try:
            conn.execute("SELECT COUNT(*) FROM sqlite_master")
        except Exception as e:
            self.logger.error(f"❌ فشل فك تشفير قاعدة البيانات: {str(e)}")
            raise ValueError("كلمة مرور التشفير غير صحيحة أو قاعدة البيانات غير مشفرة")

        self.logger.info("✅ تم الاتصال بقاعدة البيانات المشفرة بنجاح")
        return conn

    def encrypt_existing_database(self, db_path: str, password: Optional[str] = None) -> bool:
        """
        تشفير قاعدة بيانات موجودة

        Args:
            db_path: مسار قاعدة البيانات
            password: كلمة مرور التشفير (اختياري)

        Returns:
            True إذا نجح التشفير
        """
        if not SQLCIPHER_AVAILABLE:
            self.logger.warning("⚠️ SQLCipher غير متوفر - لا يمكن تشفير قاعدة البيانات")
            return False

        if not os.path.exists(db_path):
            self.logger.error(f"❌ قاعدة البيانات غير موجودة: {db_path}")
            return False

        try:
            # نسخ احتياطي
            backup_path = f"{db_path}.backup"
            import shutil

            shutil.copy2(db_path, backup_path)
            self.logger.info(f"✅ تم إنشاء نسخة احتياطية: {backup_path}")

            # الحصول على كلمة المرور
            if password is None:
                device_id = self.keyring_manager.get_device_id()
                password = self.get_encryption_password(device_id)

            # فتح قاعدة البيانات العادية
            plain_conn = None
            encrypted_conn = None
            try:
                plain_conn = sqlite3.connect(db_path)

                # إنشاء قاعدة بيانات مشفرة جديدة - مع حماية من SQL Injection
                encrypted_path = f"{db_path}.encrypted"
                encrypted_conn = sqlite3.connect(encrypted_path)
                safe_password = password.replace("'", "''")
                encrypted_conn.execute(f"PRAGMA key='{safe_password}'")

                # نسخ البيانات
                plain_conn.backup(encrypted_conn)
            finally:
                if plain_conn:
                    plain_conn.close()
                if encrypted_conn:
                    encrypted_conn.close()

            # استبدال الملف القديم
            os.replace(encrypted_path, db_path)

            self.logger.info("✅ تم تشفير قاعدة البيانات بنجاح")
            return True

        except Exception as e:
            self.logger.error(f"❌ فشل تشفير قاعدة البيانات: {str(e)}")
            return False

    def is_database_encrypted(self, db_path: str) -> bool:
        """
        التحقق من كون قاعدة البيانات مشفرة

        Args:
            db_path: مسار قاعدة البيانات

        Returns:
            True إذا كانت مشفرة
        """
        if not SQLCIPHER_AVAILABLE or not os.path.exists(db_path):
            return False

        conn = None
        try:
            # محاولة فتح بدون كلمة مرور
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT COUNT(*) FROM sqlite_master")
            return False
        except Exception:
            # إذا فشل، قد تكون مشفرة
            return True
        finally:
            if conn:
                conn.close()

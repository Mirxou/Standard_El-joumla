#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير التشفير - Encryption Manager
إدارة تشفير قاعدة البيانات والملفات الحساسة
"""

import base64
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
from datetime import datetime
from typing import Union

# Setup logger
logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None
    logger.warning("cryptography library not available. EncryptionManager will not work.")


class EncryptionManager:
    """مدير التشفير"""

    # الحد الأدنى لمتطلبات كلمة المرور ( حسب OWASP )
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True

    def __init__(self, password: str = None):
        self.password = password
        self.salt = None
        self.key = None
        self.fernet = None

        if password:
            self._generate_key(password)

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        التحقق من قوة كلمة المرور

        Returns:
            tuple: (is_valid, error_message)
        """
        if not password:
            return False, "كلمة المرور مطلوبة"

        if len(password) < EncryptionManager.MIN_PASSWORD_LENGTH:
            return (
                False,
                f"كلمة المرور يجب أن تكون {EncryptionManager.MIN_PASSWORD_LENGTH} أحرف على الأقل",
            )

        errors = []

        if EncryptionManager.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("حرف كبير uppercase")

        if EncryptionManager.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("حرف صغير lowercase")

        if EncryptionManager.REQUIRE_DIGITS and not re.search(r"\d", password):
            errors.append("رقم")

        if EncryptionManager.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("رمز خاص")

        if errors:
            return False, f"كلمة المرور يجب أن تتضمن: {', '.join(errors)}"

        return True, ""

    @staticmethod
    def is_password_compliant(password: str) -> bool:
        """تحقق سريع من الامتثال"""
        is_valid, _ = EncryptionManager.validate_password_strength(password)
        return is_valid

    def _generate_key(self, password: str, salt: bytes = None) -> bytes:
        """توليد مفتاح التشفير من كلمة المرور"""
        if salt is None:
            salt = os.urandom(16)

        self.salt = salt

        # استخدام PBKDF2 لتوليد مفتاح قوي (480,000 iterations للامتثال لـ OWASP)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.key = key
        self.fernet = Fernet(key)

        return key

    def encrypt_data(self, data: Union[str, bytes]) -> bytes:
        """تشفير البيانات"""
        if not self.fernet:
            raise ValueError("لم يتم تهيئة مفتاح التشفير")

        if isinstance(data, str):
            data = data.encode("utf-8")

        return self.fernet.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """فك تشفير البيانات"""
        if not self.fernet:
            raise ValueError("لم يتم تهيئة مفتاح التشفير")

        return self.fernet.decrypt(encrypted_data)

    # Backward-compatible aliases used by older code/tests.
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        return self.encrypt_data(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        return self.decrypt_data(encrypted_data)

    def encrypt_file(self, file_path: str, output_path: str = None) -> str:
        """تشفير ملف"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")

        if output_path is None:
            output_path = file_path + ".encrypted"

        with open(file_path, "rb") as file:
            file_data = file.read()

        encrypted_data = self.encrypt_data(file_data)

        # حفظ البيانات المشفرة مع معلومات التشفير
        encryption_info = {
            "salt": base64.b64encode(self.salt).decode("utf-8"),
            "encrypted_at": datetime.now().isoformat(),
            "original_size": len(file_data),
        }

        with open(output_path, "wb") as encrypted_file:
            # كتابة معلومات التشفير أولاً
            info_json = json.dumps(encryption_info).encode("utf-8")
            info_length = len(info_json)
            encrypted_file.write(info_length.to_bytes(4, byteorder="big"))
            encrypted_file.write(info_json)
            # ثم كتابة البيانات المشفرة
            encrypted_file.write(encrypted_data)

        return output_path

    def decrypt_file(self, encrypted_file_path: str, output_path: str = None) -> str:
        """فك تشفير ملف"""
        if not os.path.exists(encrypted_file_path):
            raise FileNotFoundError(f"الملف المشفر غير موجود: {encrypted_file_path}")

        with open(encrypted_file_path, "rb") as encrypted_file:
            # قراءة معلومات التشفير
            info_length = int.from_bytes(encrypted_file.read(4), byteorder="big")
            info_json = encrypted_file.read(info_length).decode("utf-8")
            encryption_info = json.loads(info_json)

            # استخراج salt
            salt = base64.b64decode(encryption_info["salt"])

            # إعادة توليد المفتاح باستخدام salt المحفوظ
            if self.password:
                self._generate_key(self.password, salt)

            # قراءة البيانات المشفرة
            encrypted_data = encrypted_file.read()

        # فك التشفير
        decrypted_data = self.decrypt_data(encrypted_data)

        if output_path is None:
            output_path = encrypted_file_path.replace(".encrypted", "")

        with open(output_path, "wb") as decrypted_file:
            decrypted_file.write(decrypted_data)

        return output_path

    def encrypt_database(self, db_path: str, password: str, backup_original: bool = True) -> str:
        """تشفير قاعدة البيانات"""
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"قاعدة البيانات غير موجودة: {db_path}")

        # إنشاء نسخة احتياطية إذا طُلب ذلك
        if backup_original:
            backup_path = db_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            logger.info(f"تم إنشاء نسخة احتياطية: {backup_path}")

        # تشفير قاعدة البيانات
        self.password = password
        encrypted_path = self.encrypt_file(db_path, db_path + ".encrypted")

        # حذف قاعدة البيانات الأصلية واستبدالها بالمشفرة
        os.remove(db_path)
        os.rename(encrypted_path, db_path)

        logger.info(f"تم تشفير قاعدة البيانات: {db_path}")
        return db_path

    def decrypt_database(self, encrypted_db_path: str, password: str, output_path: str = None) -> str:
        """فك تشفير قاعدة البيانات"""
        self.password = password

        if output_path is None:
            output_path = encrypted_db_path.replace(".encrypted", "")

        decrypted_path = self.decrypt_file(encrypted_db_path, output_path)
        logger.info(f"تم فك تشفير قاعدة البيانات: {decrypted_path}")
        return decrypted_path

    def verify_database_integrity(self, db_path: str) -> bool:
        """التحقق من سلامة قاعدة البيانات"""
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            return result[0] == "ok"
        except Exception as e:
            logger.log(logging.ERROR, f"خطأ في التحقق من سلامة قاعدة البيانات: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def is_database_encrypted(self, db_path: str) -> bool:
        """التحقق من كون قاعدة البيانات مشفرة"""
        try:
            with open(db_path, "rb") as file:
                # قراءة أول 4 بايت للتحقق من وجود معلومات التشفير
                info_length_bytes = file.read(4)
                if len(info_length_bytes) == 4:
                    info_length = int.from_bytes(info_length_bytes, byteorder="big")
                    if 0 < info_length < 1000:  # حجم معقول لمعلومات التشفير
                        info_json = file.read(info_length).decode("utf-8")
                        encryption_info = json.loads(info_json)
                        return "salt" in encryption_info and "encrypted_at" in encryption_info
            return False
        except Exception:
            return False

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        توليد كلمة مرور آمنة

        Args:
            length: طول كلمة المرور (افتراضي 16)

        Returns:
            str: كلمة مرور آمنة
        """
        import secrets
        import string

        # تحديد الأحرف المسموحة
        characters = string.ascii_letters + string.digits + "!@#$%^&*"

        # توليد كلمة مرور آمنة
        password = "".join(secrets.choice(characters) for _ in range(length))

        # التأكد من وجود أحرف من كل نوع
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*" for c in password)

        # إعادة التوليد إذا لم تحتوي على جميع الأنواع
        if not all([has_upper, has_lower, has_digit, has_special]):
            return EncryptionManager.generate_secure_password(length)

        return password

    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> tuple:
        """تشفير كلمة المرور للتخزين الآمن"""
        if salt is None:
            salt = os.urandom(32)

        # استخدام 480,000 iterations للامتثال لـ OWASP
        pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 480000)
        return pwdhash, salt

    @staticmethod
    def verify_password(stored_password: bytes, stored_salt: bytes, provided_password: str) -> bool:
        """التحقق من كلمة المرور"""
        pwdhash, _ = EncryptionManager.hash_password(provided_password, stored_salt)
        return pwdhash == stored_password

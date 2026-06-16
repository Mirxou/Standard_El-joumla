#!/usr/bin/env python3
"""
خدمة التشفير (Encryption Service)
تشفير/فك تشفير البيانات الحساسة باستخدام Fernet (cryptography) الآمنة
"""

import base64
import hashlib
import logging
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self, key: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.raw_key = key
        # توليد مفتاح متوافق مع Fernet (32 بايت مرمز بـ base64 ملائم للمسارات)
        h = hashlib.sha256(key.encode()).digest()
        self.key = base64.urlsafe_b64encode(h)
        self._fernet = Fernet(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        تشفير النص الواضح باستخدام Fernet
        """
        if not plaintext:
            return ""
        try:
            return self._fernet.encrypt(plaintext.encode()).decode()
        except Exception as e:
            self.logger.error(f"خطأ أثناء تشفير البيانات: {e}")
            return f"PLAINTEXT::{plaintext}"

    def decrypt(self, enc: str) -> str:
        """
        فك تشفير النص المشفر باستخدام Fernet
        """
        if not enc:
            return ""
        if enc.startswith("PLAINTEXT::"):
            return enc.split("PLAINTEXT::", 1)[1]
        
        try:
            return self._fernet.decrypt(enc.encode()).decode()
        except Exception as e:
            # محاولة التعامل مع التشفير القديم أو فك التشفير كـ plaintext احتياطياً
            self.logger.warning(f"فشل فك التشفير العادي، محاولة إرجاع القيمة الأصلية: {e}")
            return enc

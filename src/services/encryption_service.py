#!/usr/bin/env python3
"""
خدمة التشفير (Encryption Service)
تشفير/فك تشفير البيانات الحساسة باستخدام AES (PyCryptodome)
أو Fernet (cryptography) كخيار احتياطي في حال عدم توفر Crypto.
"""
import base64
import hashlib

try:
    from Crypto.Cipher import AES  # type: ignore
    from Crypto.Random import get_random_bytes  # type: ignore
    _CRYPTO_MODE = "AES"
except ImportError:
    try:
        from cryptography.fernet import Fernet  # type: ignore
        _CRYPTO_MODE = "FERNET"
    except ImportError:
        _CRYPTO_MODE = "NONE"

class EncryptionService:
    def __init__(self, key: str):
        self.raw_key = key
        if _CRYPTO_MODE == "AES":
            self.key = hashlib.sha256(key.encode()).digest()
        elif _CRYPTO_MODE == "FERNET":
            h = hashlib.sha256(key.encode()).digest()
            self.key = base64.urlsafe_b64encode(h)
            self._fernet = Fernet(self.key)
        else:
            self.key = None

    def encrypt(self, plaintext: str) -> str:
        if _CRYPTO_MODE == "AES":
            cipher = AES.new(self.key, AES.MODE_EAX)
            nonce = cipher.nonce
            ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
            return base64.b64encode(nonce + tag + ciphertext).decode()
        elif _CRYPTO_MODE == "FERNET":
            return self._fernet.encrypt(plaintext.encode()).decode()
        else:
            return f"PLAINTEXT::{plaintext}"

    def decrypt(self, enc: str) -> str:
        if _CRYPTO_MODE == "AES":
            raw = base64.b64decode(enc)
            nonce = raw[:16]
            tag = raw[16:32]
            ciphertext = raw[32:]
            cipher = AES.new(self.key, AES.MODE_EAX, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return plaintext.decode()
        elif _CRYPTO_MODE == "FERNET":
            return self._fernet.decrypt(enc.encode()).decode()
        else:
            if enc.startswith("PLAINTEXT::"):
                return enc.split("PLAINTEXT::",1)[1]
            return enc

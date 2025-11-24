#!/usr/bin/env python3
"""
خدمة التشفير (Encryption Service)
تشفير/فك تشفير البيانات الحساسة باستخدام AES
"""
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import hashlib

class EncryptionService:
    def __init__(self, key: str):
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, plaintext: str) -> str:
        cipher = AES.new(self.key, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
        return base64.b64encode(nonce + tag + ciphertext).decode()

    def decrypt(self, enc: str) -> str:
        raw = base64.b64decode(enc)
        nonce = raw[:16]
        tag = raw[16:32]
        ciphertext = raw[32:]
        cipher = AES.new(self.key, AES.MODE_EAX, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode()

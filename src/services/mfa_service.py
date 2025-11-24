#!/usr/bin/env python3
"""
خدمة المصادقة متعددة العوامل (MFA/OTP Service)
تدعم توليد والتحقق من رموز OTP لمرة واحدة (TOTP)
"""
import base64
import hmac
import hashlib
import time
from typing import Optional

class MFAService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self._init_table()

    def _init_table(self):
        q = '''
        ALTER TABLE users ADD COLUMN otp_secret TEXT;
        '''
        try:
            self.db.execute_query(q)
        except Exception:
            pass  # العمود موجود مسبقاً

    def set_otp_secret(self, user_id: int, secret: str):
        q = 'UPDATE users SET otp_secret=? WHERE user_id=?'
        self.db.execute_query(q, (secret, user_id))

    def get_otp_secret(self, user_id: int) -> Optional[str]:
        q = 'SELECT otp_secret FROM users WHERE user_id=?'
        row = self.db.fetch_one(q, (user_id,))
        return row[0] if row and row[0] else None

    def generate_otp(self, secret: str, interval: int = 30, digits: int = 6) -> str:
        key = base64.b32decode(secret, True)
        msg = int(time.time() // interval)
        msg_bytes = msg.to_bytes(8, 'big')
        h = hmac.new(key, msg_bytes, hashlib.sha1).digest()
        o = h[19] & 15
        code = (int.from_bytes(h[o:o+4], 'big') & 0x7fffffff) % (10 ** digits)
        return str(code).zfill(digits)

    def verify_otp(self, user_id: int, otp: str, window: int = 1) -> bool:
        secret = self.get_otp_secret(user_id)
        if not secret:
            return False
        for offset in range(-window, window+1):
            key = base64.b32decode(secret, True)
            t = int(time.time() // 30) + offset
            msg_bytes = t.to_bytes(8, 'big')
            h = hmac.new(key, msg_bytes, hashlib.sha1).digest()
            o = h[19] & 15
            code = (int.from_bytes(h[o:o+4], 'big') & 0x7fffffff) % (10 ** 6)
            if str(code).zfill(6) == otp:
                return True
        return False

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الأمان المتقدمة
توفر تشفير قوي، مصادقة ثنائية، وحماية متقدمة
"""

import os
import secrets
import hashlib
import base64
import json
import time
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Setup logger
logger = logging.getLogger(__name__)

# إضافة المسار للوصول للوحدات

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash

    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    logging.warning(
        "⚠️ تحذير: مكتبة argon2-cffi غير مثبتة. سيتم استخدام PBKDF2 بدلاً منها."
    )

try:
    import pyotp

    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    logging.warning("⚠️ تحذير: مكتبة pyotp غير مثبتة. المصادقة الثنائية غير متاحة.")


class AdvancedSecurityService:
    """
    خدمة الأمان المتقدمة

    المزايا:
    - تشفير كلمات المرور بـ Argon2 (أقوى من bcrypt/PBKDF2)
    - مصادقة ثنائية (2FA) باستخدام TOTP
    - إدارة الجلسات بشكل آمن
    - حماية من SQL Injection
    - Audit logging متقدم
    """

    def __init__(self, db_manager=None):
        """
        تهيئة خدمة الأمان

        Args:
            db_manager: مدير قاعدة البيانات (اختياري)
        """
        self.db = db_manager
        # Multi-Company Support
        self._tenant_manager = None

        # تهيئة Password Hasher (Argon2 أو PBKDF2)
        if ARGON2_AVAILABLE:
            # Argon2id - أقوى وأحدث خوارزمية تشفير
            self.ph = PasswordHasher(
                time_cost=3,  # عدد التكرارات (أعلى = أبطأ وأكثر أماناً)
                memory_cost=65536,  # الذاكرة المستخدمة (64 MB)
                parallelism=4,  # عدد الخيوط المتوازية
                hash_len=32,  # طول Hash النهائي
                salt_len=16,  # طول الملح
            )
            self.hash_method = "argon2"
        else:
            # PBKDF2 كبديل (أقل أماناً لكن مقبول)
            self.ph = None
            self.hash_method = "pbkdf2"
            self.pbkdf2_iterations = 1000000  # OWASP recommended for higher security

        # معلومات الجلسات النشطة (في الذاكرة)
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

        # مدة صلاحية الجلسة (بالثواني)
        self.session_timeout = 3600  # ساعة واحدة

        # عدد محاولات تسجيل الدخول الفاشلة المسموحة
        self.max_login_attempts = 5

        # مدة الحظر بعد تجاوز المحاولات (بالثواني)
        self.lockout_duration = 900  # 15 دقيقة

        # تتبع محاولات تسجيل الدخول الفاشلة
        self._failed_attempts: Dict[str, list] = {}

    # ==================== تشفير كلمات المرور ====================

    def hash_password(self, password: str) -> str:
        """
        تشفير كلمة المرور باستخدام Argon2 أو PBKDF2

        Args:
            password: كلمة المرور النصية

        Returns:
            str: كلمة المرور المشفرة مع البادئة للتعرف على نوع التشفير

        Example:
            >>> security = AdvancedSecurityService()
            >>> hashed = security.hash_password("MySecureP@ss123")
            >>> print(hashed[:10])
            $argon2id$
        """
        if not password:
            raise ValueError("كلمة المرور لا يمكن أن تكون فارغة")

        if self.hash_method == "argon2" and self.ph:
            # استخدام Argon2
            return self.ph.hash(password)
        else:
            # استخدام PBKDF2 كبديل
            salt = os.urandom(32)  # 256 بت
            pwdhash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, self.pbkdf2_iterations
            )
            # تخزين الملح مع الـ hash
            storage = salt + pwdhash
            return f"$pbkdf2${base64.b64encode(storage).decode('ascii')}"

    def verify_password(self, stored_hash: str, provided_password: str) -> bool:
        """
        التحقق من كلمة المرور

        Args:
            stored_hash: كلمة المرور المشفرة المخزنة
            provided_password: كلمة المرور المُدخلة للتحقق

        Returns:
            bool: True إذا كانت صحيحة، False خلاف ذلك

        Example:
            >>> security = AdvancedSecurityService()
            >>> hashed = security.hash_password("MyPassword")
            >>> security.verify_password(hashed, "MyPassword")
            True
            >>> security.verify_password(hashed, "WrongPassword")
            False
        """
        if not stored_hash or not provided_password:
            return False

        try:
            if stored_hash.startswith("$argon2"):
                # Argon2 verification
                if not self.ph:
                    return False
                self.ph.verify(stored_hash, provided_password)

                # التحقق من الحاجة لإعادة التشفير (إذا تغيرت المعايير)
                if self.ph.check_needs_rehash(stored_hash):
                    # يمكن هنا تحديث كلمة المرور في قاعدة البيانات
                    pass

                return True

            elif stored_hash.startswith("$pbkdf2$"):
                # PBKDF2 verification
                storage = base64.b64decode(stored_hash.split("$")[2])
                salt = storage[:32]
                stored_pwdhash = storage[32:]

                pwdhash = hashlib.pbkdf2_hmac(
                    "sha256",
                    provided_password.encode("utf-8"),
                    salt,
                    self.pbkdf2_iterations,
                )

                return secrets.compare_digest(pwdhash, stored_pwdhash)
            else:
                # نوع تشفير غير معروف
                return False

        except (VerifyMismatchError, VerificationError, InvalidHash):
            return False
        except Exception:
            return False

    # ==================== المصادقة الثنائية (2FA) ====================

    def generate_totp_secret(self) -> str:
        """
        إنشاء سر TOTP للمصادقة الثنائية

        Returns:
            str: السر بصيغة Base32

        Example:
            >>> security = AdvancedSecurityService()
            >>> secret = security.generate_totp_secret()
            >>> len(secret)
            32
        """
        if not PYOTP_AVAILABLE:
            raise RuntimeError("مكتبة pyotp غير مثبتة. المصادقة الثنائية غير متاحة.")

        return pyotp.random_base32()

    def get_totp_uri(
        self, secret: str, account_name: str, issuer: str = "الإصدار المنطقي"
    ) -> str:
        """
        إنشاء URI للمصادقة الثنائية (لعرضه كـ QR Code)

        Args:
            secret: سر TOTP
            account_name: اسم الحساب (عادة البريد الإلكتروني أو اسم المستخدم)
            issuer: اسم التطبيق

        Returns:
            str: URI يمكن تحويله لـ QR Code

        Example:
            >>> security = AdvancedSecurityService()
            >>> secret = security.generate_totp_secret()
            >>> uri = security.get_totp_uri(secret, "user@example.com")
            >>> uri.startswith("otpauth://totp/")
            True
        """
        if not PYOTP_AVAILABLE:
            raise RuntimeError("مكتبة pyotp غير مثبتة")

        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=account_name, issuer_name=issuer)

    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """
        التحقق من رمز TOTP

        Args:
            secret: سر TOTP المخزن
            token: الرمز المُدخل (6 أرقام عادةً)
            window: نافذة التسامح (عدد الفترات الزمنية المقبولة قبل/بعد)

        Returns:
            bool: True إذا كان الرمز صحيحاً

        Example:
            >>> security = AdvancedSecurityService()
            >>> secret = security.generate_totp_secret()
            >>> totp = pyotp.TOTP(secret)
            >>> token = totp.now()
            >>> security.verify_totp(secret, token)
            True
        """
        if not PYOTP_AVAILABLE:
            return False

        if not secret or not token:
            return False

        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception:
            return False

    # ==================== إدارة الجلسات ====================

    def create_session(
        self,
        user_id: int,
        username: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> str:
        """
        إنشاء جلسة جديدة

        Args:
            user_id: معرف المستخدم
            username: اسم المستخدم
            ip_address: عنوان IP (اختياري)
            user_agent: User Agent (اختياري)

        Returns:
            str: رمز الجلسة (Session Token)

        Example:
            >>> security = AdvancedSecurityService()
            >>> token = security.create_session(1, "admin", "192.168.1.1")
            >>> len(token)
            43
        """
        # إنشاء رمز عشوائي آمن
        session_token = secrets.token_urlsafe(32)

        # بيانات الجلسة
        session_data = {
            "user_id": user_id,
            "username": username,
            "created_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.now() + timedelta(seconds=self.session_timeout)
            ).isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "last_activity": datetime.now().isoformat(),
        }

        # حفظ في الذاكرة
        self._active_sessions[session_token] = session_data

        # حفظ في قاعدة البيانات (إذا كانت متاحة)
        if self.db:
            try:
                self.db.execute_query(
                    """
                    INSERT INTO user_sessions 
                    (session_token, user_id, username, created_at, expires_at, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_token,
                        user_id,
                        username,
                        session_data["created_at"],
                        session_data["expires_at"],
                        ip_address,
                        user_agent,
                    ),
                )
            except Exception:
                pass  # الجلسة موجودة في الذاكرة على الأقل

        return session_token

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        التحقق من صلاحية الجلسة

        Args:
            session_token: رمز الجلسة

        Returns:
            Optional[Dict]: بيانات الجلسة إذا كانت صالحة، None خلاف ذلك

        Example:
            >>> security = AdvancedSecurityService()
            >>> token = security.create_session(1, "admin")
            >>> session = security.validate_session(token)
            >>> session['user_id']
            1
        """
        if not session_token:
            return None

        # البحث في الذاكرة أولاً
        session_data = self._active_sessions.get(session_token)

        # إذا لم تُوجد، البحث في قاعدة البيانات
        if not session_data and self.db:
            try:
                row = self.db.fetch_one(
                    "SELECT * FROM user_sessions WHERE session_token = ? AND is_active = 1",
                    (session_token,),
                )
                if row:
                    session_data = dict(row)
                    # حفظ في الذاكرة للوصول السريع
                    self._active_sessions[session_token] = session_data
            except Exception:
                pass

        if not session_data:
            return None

        # التحقق من انتهاء الصلاحية
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.now() > expires_at:
            # انتهت صلاحية الجلسة
            self.invalidate_session(session_token)
            return None

        # تحديث آخر نشاط
        session_data["last_activity"] = datetime.now().isoformat()

        return session_data

    def invalidate_session(self, session_token: str) -> bool:
        """
        إلغاء جلسة (تسجيل خروج)

        Args:
            session_token: رمز الجلسة

        Returns:
            bool: True إذا تم الإلغاء بنجاح
        """
        # حذف من الذاكرة
        if session_token in self._active_sessions:
            del self._active_sessions[session_token]

        # تحديث في قاعدة البيانات
        if self.db:
            try:
                self.db.execute_query(
                    "UPDATE user_sessions SET is_active = 0, ended_at = ? WHERE session_token = ?",
                    (datetime.now().isoformat(), session_token),
                )
                return True
            except Exception:
                pass

        return True

    def invalidate_all_user_sessions(self, user_id: int) -> int:
        """
        إلغاء جميع جلسات مستخدم معين

        Args:
            user_id: معرف المستخدم

        Returns:
            int: عدد الجلسات الملغاة
        """
        count = 0

        # حذف من الذاكرة
        tokens_to_remove = [
            token
            for token, data in self._active_sessions.items()
            if data.get("user_id") == user_id
        ]
        for token in tokens_to_remove:
            del self._active_sessions[token]
            count += 1

        # تحديث في قاعدة البيانات
        if self.db:
            try:
                cursor = self.db.execute_query(
                    "UPDATE user_sessions SET is_active = 0, ended_at = ? WHERE user_id = ? AND is_active = 1",
                    (datetime.now().isoformat(), user_id),
                )
                if cursor and hasattr(cursor, "rowcount"):
                    count = max(count, cursor.rowcount)
            except Exception:
                pass

        return count

    # ==================== حماية من Brute Force ====================

    def record_failed_login(self, username: str) -> bool:
        """
        تسجيل محاولة تسجيل دخول فاشلة

        Args:
            username: اسم المستخدم

        Returns:
            bool: True إذا وصل لحد المحاولات المسموحة (يجب حظر الحساب)
        """
        if username not in self._failed_attempts:
            self._failed_attempts[username] = []

        # إضافة المحاولة الحالية
        self._failed_attempts[username].append(time.time())

        # تنظيف المحاولات القديمة (أقدم من مدة الحظر)
        cutoff_time = time.time() - self.lockout_duration
        self._failed_attempts[username] = [
            t for t in self._failed_attempts[username] if t > cutoff_time
        ]

        # التحقق من تجاوز الحد
        return len(self._failed_attempts[username]) >= self.max_login_attempts

    def is_account_locked(self, username: str) -> Tuple[bool, Optional[int]]:
        """
        التحقق من حظر الحساب

        Args:
            username: اسم المستخدم

        Returns:
            Tuple[bool, Optional[int]]: (محظور أم لا، الوقت المتبقي بالثواني)
        """
        if username not in self._failed_attempts:
            return False, None

        # تنظيف المحاولات القديمة
        cutoff_time = time.time() - self.lockout_duration
        self._failed_attempts[username] = [
            t for t in self._failed_attempts[username] if t > cutoff_time
        ]

        attempts = self._failed_attempts[username]

        if len(attempts) >= self.max_login_attempts:
            # محسوب الوقت المتبقي
            oldest_attempt = min(attempts)
            unlock_time = oldest_attempt + self.lockout_duration
            remaining = int(unlock_time - time.time())

            return True, max(0, remaining)

        return False, None

    def clear_failed_attempts(self, username: str) -> None:
        """مسح محاولات تسجيل الدخول الفاشلة (بعد تسجيل دخول ناجح)"""
        if username in self._failed_attempts:
            del self._failed_attempts[username]

    # ==================== Audit Logging ====================

    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[int],
        username: Optional[str],
        description: str,
        ip_address: Optional[str] = None,
        severity: str = "INFO",
    ) -> None:
        """
        تسجيل حدث أمني

        Args:
            event_type: نوع الحدث (LOGIN, LOGOUT, PASSWORD_CHANGE, etc.)
            user_id: معرف المستخدم (اختياري)
            username: اسم المستخدم (اختياري)
            description: وصف الحدث
            ip_address: عنوان IP (اختياري)
            severity: درجة الخطورة (INFO, WARNING, ERROR, CRITICAL)
        """
        if not self.db:
            return

        try:
            self.db.execute_query(
                """
                INSERT INTO security_audit_log 
                (event_type, user_id, username, description, ip_address, severity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event_type,
                    user_id,
                    username,
                    description,
                    ip_address,
                    severity,
                    datetime.now().isoformat(),
                ),
            )
        except Exception:
            pass  # فشل تسجيل الحدث - لا نريد إيقاف التطبيق


# ==================== وظائف مساعدة ====================


def generate_secure_token(length: int = 32) -> str:
    """
    إنشاء رمز عشوائي آمن

    Args:
        length: طول الرمز بالبايتات

    Returns:
        str: رمز عشوائي آمن
    """
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """
    إنشاء مفتاح API

    Returns:
        str: مفتاح API بصيغة معينة
    """
    prefix = "lv_"  # Logical Version prefix
    random_part = secrets.token_hex(24)  # 48 حرف hex
    return f"{prefix}{random_part}"


# ==================== مثال على الاستخدام ====================

if __name__ == "__main__":
    # إنشاء خدمة الأمان
    security = AdvancedSecurityService()

    print("=" * 70)
    print("🔐 اختبار خدمة الأمان المتقدمة")
    print("=" * 70)

    # 1. اختبار تشفير كلمة المرور
    print("\n1️⃣ اختبار تشفير كلمة المرور:")
    password = "MySecureP@ssw0rd123"
    hashed = security.hash_password(password)
    print(f"   كلمة المرور: {password}")
    print(f"   المشفرة: {hashed[:60]}...")
    print(f"   طريقة التشفير: {security.hash_method}")

    # التحقق
    is_valid = security.verify_password(hashed, password)
    print(f"   ✅ التحقق ناجح: {is_valid}")

    is_invalid = security.verify_password(hashed, "WrongPassword")
    print(f"   ❌ كلمة مرور خاطئة: {is_invalid}")

    # 2. اختبار المصادقة الثنائية (إذا كانت متاحة)
    if PYOTP_AVAILABLE:
        print("\n2️⃣ اختبار المصادقة الثنائية (2FA):")
        secret = security.generate_totp_secret()
        print(f"   السر: {secret}")

        uri = security.get_totp_uri(secret, "user@example.com")
        print(f"   URI: {uri[:50]}...")

        # إنشاء رمز
        import pyotp

        totp = pyotp.TOTP(secret)
        token = totp.now()
        print(f"   الرمز الحالي: {token}")

        # التحقق
        is_valid = security.verify_totp(secret, token)
        print(f"   ✅ التحقق من الرمز: {is_valid}")
    else:
        print("\n2️⃣ المصادقة الثنائية غير متاحة (pyotp غير مثبت)")

    # 3. اختبار الجلسات
    print("\n3️⃣ اختبار إدارة الجلسات:")
    session_token = security.create_session(1, "admin", "192.168.1.1")
    print(f"   رمز الجلسة: {session_token}")

    session_data = security.validate_session(session_token)
    print(f"   ✅ الجلسة صالحة: {session_data is not None}")
    if session_data:
        print(f"   المستخدم: {session_data['username']}")

    # 4. اختبار حماية Brute Force
    print("\n4️⃣ اختبار حماية Brute Force:")
    username = "test_user"
    for i in range(6):
        is_locked = security.record_failed_login(username)
        print(f"   المحاولة {i + 1}: {'🔒 محظور' if is_locked else '✅ مسموح'}")

    locked, remaining = security.is_account_locked(username)
    if locked:
        print(f"   ⏳ الحساب محظور لمدة {remaining} ثانية")

    print("\n" + "=" * 70)
    print("✅ اكتملت جميع الاختبارات بنجاح!")
    print("=" * 70)

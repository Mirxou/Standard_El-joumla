"""
نظام المصادقة متعددة العوامل - Multi-Factor Authentication (MFA)
Enhanced security with multiple authentication methods

Features:
- SMS OTP
- Email OTP
- Authenticator Apps (TOTP)
- Backup Codes
- Biometric placeholder
"""

import secrets
import hashlib
import base64
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class MFAMethod(Enum):
    """طرق المصادقة"""
    SMS = "sms"
    EMAIL = "email"
    TOTP = "totp"  # Time-based One-Time Password
    BACKUP_CODE = "backup_code"


@dataclass
class MFAConfig:
    """إعدادات MFA للمستخدم"""
    user_id: int
    methods_enabled: List[MFAMethod]
    phone_number: Optional[str]
    email: Optional[str]
    totp_secret: Optional[str]
    backup_codes: List[str]


class MFAService:
    """خدمة المصادقة متعددة العوامل"""
    
    # إعدادات OTP
    OTP_LENGTH = 6
    OTP_VALIDITY_MINUTES = 5
    MAX_ATTEMPTS = 3
    
    # إعدادات TOTP
    TOTP_PERIOD = 30  # ثانية
    TOTP_DIGITS = 6
    
    def __init__(self, db_manager):
        """
        تهيئة خدمة MFA
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
        self._create_tables()
    
    def _create_tables(self):
        """إنشاء جداول MFA"""
        cursor = self.db.get_cursor()
        
        # جدول إعدادات MFA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mfa_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                mfa_enabled BOOLEAN DEFAULT 0,
                methods_enabled TEXT,
                phone_number TEXT,
                email TEXT,
                totp_secret TEXT,
                backup_codes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # جدول OTP المؤقت
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mfa_otp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                method TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # جدول سجل التحقق
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mfa_verification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                method TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                verified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        self.db.connection.commit()
    
    def enable_mfa(
        self,
        user_id: int,
        methods: List[MFAMethod],
        phone_number: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict:
        """
        تفعيل MFA للمستخدم
        
        Args:
            user_id: معرف المستخدم
            methods: طرق المصادقة المطلوبة
            phone_number: رقم الهاتف (للـ SMS)
            email: البريد الإلكتروني (للـ Email OTP)
            
        Returns:
            معلومات التفعيل
        """
        cursor = self.db.get_cursor()
        
        # إنشاء TOTP secret إذا كان TOTP مفعل
        totp_secret = None
        if MFAMethod.TOTP in methods:
            totp_secret = self._generate_totp_secret()
        
        # إنشاء Backup Codes
        backup_codes = [self._generate_backup_code() for _ in range(10)]
        backup_codes_hashed = [self._hash_code(code) for code in backup_codes]
        
        import json
        
        cursor.execute('''
            INSERT INTO mfa_settings 
            (user_id, mfa_enabled, methods_enabled, phone_number, email, totp_secret, backup_codes)
            VALUES (?, 1, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                mfa_enabled = 1,
                methods_enabled = ?,
                phone_number = ?,
                email = ?,
                totp_secret = ?,
                backup_codes = ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (
            user_id,
            json.dumps([m.value for m in methods]),
            phone_number,
            email,
            totp_secret,
            json.dumps(backup_codes_hashed),
            json.dumps([m.value for m in methods]),
            phone_number,
            email,
            totp_secret,
            json.dumps(backup_codes_hashed)
        ))
        
        self.db.connection.commit()
        
        response = {
            "mfa_enabled": True,
            "methods": [m.value for m in methods],
            "backup_codes": backup_codes  # يُعرض مرة واحدة فقط
        }
        
        if totp_secret:
            # إنشاء QR Code URL للـ Authenticator App
            response["totp_secret"] = totp_secret
            response["totp_qr_url"] = self._generate_totp_qr_url(user_id, totp_secret)
        
        return response
    
    def disable_mfa(self, user_id: int):
        """تعطيل MFA"""
        cursor = self.db.get_cursor()
        
        cursor.execute('''
            UPDATE mfa_settings
            SET mfa_enabled = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        
        self.db.connection.commit()
    
    def send_otp(
        self,
        user_id: int,
        method: MFAMethod
    ) -> Dict:
        """
        إرسال OTP
        
        Args:
            user_id: معرف المستخدم
            method: طريقة الإرسال
            
        Returns:
            نتيجة الإرسال
        """
        # إنشاء OTP
        otp_code = self._generate_otp()
        code_hash = self._hash_code(otp_code)
        
        # حساب وقت انتهاء الصلاحية
        expires_at = (datetime.now() + timedelta(minutes=self.OTP_VALIDITY_MINUTES)).isoformat()
        
        cursor = self.db.get_cursor()
        
        # حذف OTP القديم غير المستخدم
        cursor.execute('''
            DELETE FROM mfa_otp
            WHERE user_id = ? AND method = ? AND verified = 0
        ''', (user_id, method.value))
        
        # حفظ OTP الجديد
        cursor.execute('''
            INSERT INTO mfa_otp (user_id, method, code_hash, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, method.value, code_hash, expires_at))
        
        self.db.connection.commit()
        
        # الحصول على معلومات الاتصال
        cursor.execute('''
            SELECT phone_number, email FROM mfa_settings WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return {"success": False, "message": "MFA not configured"}
        
        phone_number, email = row
        
        # إرسال OTP (محاكاة - يجب استبداله بخدمة حقيقية)
        if method == MFAMethod.SMS:
            # هنا يمكن استخدام خدمة مثل Twilio
            # send_sms(phone_number, f"Your code is: {otp_code}")
            return {
                "success": True,
                "message": f"OTP sent to {phone_number[-4:].rjust(len(phone_number), '*')}",
                "expires_in_minutes": self.OTP_VALIDITY_MINUTES,
                # للاختبار فقط - احذف في الإنتاج!
                "test_code": otp_code
            }
        
        elif method == MFAMethod.EMAIL:
            # هنا يمكن استخدام SMTP
            # send_email(email, "Your OTP Code", f"Your code is: {otp_code}")
            return {
                "success": True,
                "message": f"OTP sent to {email}",
                "expires_in_minutes": self.OTP_VALIDITY_MINUTES,
                # للاختبار فقط
                "test_code": otp_code
            }
        
        return {"success": False, "message": "Invalid method"}
    
    def verify_otp(
        self,
        user_id: int,
        method: MFAMethod,
        code: str,
        ip_address: Optional[str] = None
    ) -> Dict:
        """
        التحقق من OTP
        
        Args:
            user_id: معرف المستخدم
            method: طريقة المصادقة
            code: الكود المُدخل
            ip_address: عنوان IP
            
        Returns:
            نتيجة التحقق
        """
        cursor = self.db.get_cursor()
        
        # الحصول على OTP
        cursor.execute('''
            SELECT id, code_hash, expires_at, attempts
            FROM mfa_otp
            WHERE user_id = ? AND method = ? AND verified = 0
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id, method.value))
        
        row = cursor.fetchone()
        if not row:
            self._log_verification(user_id, method, False, ip_address)
            return {"success": False, "message": "لا يوجد OTP صالح"}
        
        otp_id, code_hash, expires_at, attempts = row
        
        # التحقق من انتهاء الصلاحية
        if datetime.fromisoformat(expires_at) < datetime.now():
            self._log_verification(user_id, method, False, ip_address)
            return {"success": False, "message": "انتهت صلاحية الكود"}
        
        # التحقق من المحاولات
        if attempts >= self.MAX_ATTEMPTS:
            self._log_verification(user_id, method, False, ip_address)
            return {"success": False, "message": "تم تجاوز الحد الأقصى للمحاولات"}
        
        # التحقق من الكود
        if self._hash_code(code) == code_hash:
            # نجح التحقق
            cursor.execute('''
                UPDATE mfa_otp
                SET verified = 1
                WHERE id = ?
            ''', (otp_id,))
            
            self.db.connection.commit()
            self._log_verification(user_id, method, True, ip_address)
            
            return {"success": True, "message": "تم التحقق بنجاح"}
        else:
            # فشل التحقق
            cursor.execute('''
                UPDATE mfa_otp
                SET attempts = attempts + 1
                WHERE id = ?
            ''', (otp_id,))
            
            self.db.connection.commit()
            self._log_verification(user_id, method, False, ip_address)
            
            remaining = self.MAX_ATTEMPTS - attempts - 1
            return {
                "success": False,
                "message": f"كود خاطئ. المحاولات المتبقية: {remaining}"
            }
    
    def verify_totp(
        self,
        user_id: int,
        code: str,
        ip_address: Optional[str] = None
    ) -> Dict:
        """
        التحقق من TOTP (Authenticator App)
        
        Args:
            user_id: معرف المستخدم
            code: الكود من التطبيق
            ip_address: عنوان IP
            
        Returns:
            نتيجة التحقق
        """
        cursor = self.db.get_cursor()
        
        # الحصول على TOTP secret
        cursor.execute('''
            SELECT totp_secret FROM mfa_settings WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if not row or not row[0]:
            return {"success": False, "message": "TOTP غير مفعل"}
        
        totp_secret = row[0]
        
        # التحقق من TOTP
        expected_code = self._generate_totp_code(totp_secret)
        
        if code == expected_code:
            self._log_verification(user_id, MFAMethod.TOTP, True, ip_address)
            return {"success": True, "message": "تم التحقق بنجاح"}
        else:
            self._log_verification(user_id, MFAMethod.TOTP, False, ip_address)
            return {"success": False, "message": "كود خاطئ"}
    
    def verify_backup_code(
        self,
        user_id: int,
        code: str,
        ip_address: Optional[str] = None
    ) -> Dict:
        """التحقق من Backup Code"""
        import json
        
        cursor = self.db.get_cursor()
        
        cursor.execute('''
            SELECT backup_codes FROM mfa_settings WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if not row or not row[0]:
            return {"success": False, "message": "لا توجد أكواد احتياطية"}
        
        backup_codes = json.loads(row[0])
        code_hash = self._hash_code(code)
        
        if code_hash in backup_codes:
            # إزالة الكود المستخدم
            backup_codes.remove(code_hash)
            
            cursor.execute('''
                UPDATE mfa_settings
                SET backup_codes = ?
                WHERE user_id = ?
            ''', (json.dumps(backup_codes), user_id))
            
            self.db.connection.commit()
            self._log_verification(user_id, MFAMethod.BACKUP_CODE, True, ip_address)
            
            return {
                "success": True,
                "message": "تم التحقق بنجاح",
                "remaining_codes": len(backup_codes)
            }
        else:
            self._log_verification(user_id, MFAMethod.BACKUP_CODE, False, ip_address)
            return {"success": False, "message": "كود احتياطي خاطئ"}
    
    def _generate_otp(self) -> str:
        """إنشاء OTP عشوائي"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.OTP_LENGTH)])
    
    def _generate_backup_code(self) -> str:
        """إنشاء كود احتياطي"""
        return secrets.token_hex(8).upper()
    
    def _generate_totp_secret(self) -> str:
        """إنشاء TOTP secret"""
        return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')
    
    def _generate_totp_code(self, secret: str) -> str:
        """إنشاء TOTP code من secret"""
        import hmac
        
        # الحصول على الوقت الحالي
        time_step = int(time.time() // self.TOTP_PERIOD)
        
        # تحويل إلى bytes
        time_bytes = time_step.to_bytes(8, byteorder='big')
        secret_bytes = base64.b32decode(secret)
        
        # HMAC-SHA1
        hmac_hash = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        code_int = int.from_bytes(hmac_hash[offset:offset+4], byteorder='big') & 0x7FFFFFFF
        
        # تحويل إلى 6 أرقام
        code = str(code_int % (10 ** self.TOTP_DIGITS)).zfill(self.TOTP_DIGITS)
        
        return code
    
    def _generate_totp_qr_url(self, user_id: int, secret: str) -> str:
        """إنشاء QR code URL للـ Authenticator App"""
        # تنسيق otpauth://
        issuer = "LogicalVersion"
        label = f"{issuer}:User{user_id}"
        
        return f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&digits={self.TOTP_DIGITS}&period={self.TOTP_PERIOD}"
    
    def _hash_code(self, code: str) -> str:
        """تشفير الكود"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def _log_verification(
        self,
        user_id: int,
        method: MFAMethod,
        success: bool,
        ip_address: Optional[str] = None
    ):
        """تسجيل محاولة التحقق"""
        cursor = self.db.get_cursor()
        
        cursor.execute('''
            INSERT INTO mfa_verification_log (user_id, method, success, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, method.value, success, ip_address))
        
        self.db.connection.commit()


if __name__ == "__main__":
    print("🔐 Multi-Factor Authentication (MFA) Service")
    print("=" * 50)
    print("✅ Module loaded successfully!")
    print("\nSupported Methods:")
    print("  - SMS OTP")
    print("  - Email OTP")
    print("  - TOTP (Authenticator Apps)")
    print("  - Backup Codes")

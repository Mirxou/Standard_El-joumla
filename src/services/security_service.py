#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الأمان والصلاحيات (Security Service)
توفر إدارة الأدوار، التحقق من الأذونات، وسجل التدقيق البسيط
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path
import re

try:
    import pyotp
except Exception:
    pyotp = None

sys.path.insert(0, str(Path(__file__).parent.parent))

class SecurityService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self._ensure_tables()

    def _ensure_tables(self):
        try:
            # 2FA table
            self.db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS user_2fa (
                    user_id INTEGER PRIMARY KEY,
                    secret TEXT NOT NULL,
                    enabled_at TEXT NOT NULL
                )
                """
            )
            # login attempts for brute force protection
            self.db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    ip TEXT,
                    user_agent TEXT,
                    success INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f'فشل تهيئة جداول الأمان: {e}')

    def create_role(self, name: str, permissions: List[str]) -> Optional[int]:
        try:
            now = datetime.now()
            q = 'INSERT INTO roles (name, permissions, created_at, updated_at) VALUES (?, ?, ?, ?)'
            res = self.db.execute_query(q, (name, ','.join(permissions), now, now))
            if res and hasattr(res, 'lastrowid'):
                return res.lastrowid
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء الدور: {e}')
        return None

    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        try:
            q = 'INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES (?, ?, ?)'
            self.db.execute_query(q, (user_id, role_id, datetime.now()))
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في تعيين الدور للمستخدم: {e}')
            return False

    def user_has_permission(self, user_id: int, permission: str) -> bool:
        try:
            q = ('SELECT r.permissions FROM roles r '
                 'JOIN user_roles ur ON ur.role_id = r.id '
                 'WHERE ur.user_id = ?')
            rows = self.db.fetch_all(q, (user_id,))
            perms = set()
            for r in rows:
                if r[0]:
                    perms.update([p.strip() for p in r[0].split(',') if p.strip()])
            return permission in perms
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في فحص صلاحية المستخدم {user_id}: {e}')
            return False

    def audit_log(self, actor: str, action: str, details: str = '') -> None:
        try:
            q = 'INSERT INTO audit_logs (actor, action, details, created_at) VALUES (?, ?, ?, ?)'
            self.db.execute_query(q, (actor, action, details, datetime.now()))
        except Exception as e:
            if self.logger:
                self.logger.error(f'فشل تسجيل السجل التدقيقي: {e}')

    # ================== 2FA (TOTP) ==================
    def enable_2fa(self, user_id: int) -> Dict[str, Any]:
        if pyotp is None:
            return {"success": False, "error": "pyotp غير متوفر"}
        secret = pyotp.random_base32()
        now = datetime.now().isoformat()
        try:
            self.db.execute_query(
                'REPLACE INTO user_2fa (user_id, secret, enabled_at) VALUES (?, ?, ?)',
                (user_id, secret, now)
            )
            return {"success": True, "secret": secret, "enabled_at": now}
        except Exception as e:
            if self.logger:
                self.logger.error(f'فشل تفعيل 2FA: {e}')
            return {"success": False, "error": str(e)}

    def get_2fa_uri(self, user_id: int, account: str, issuer: str = 'ElJoumla') -> Optional[str]:
        try:
            rows = self.db.execute_query('SELECT secret FROM user_2fa WHERE user_id = ?', (user_id,))
            if not rows:
                return None
            secret = rows[0]['secret'] if isinstance(rows[0], dict) else rows[0][0]
            if pyotp is None:
                return None
            return pyotp.totp.TOTP(secret).provisioning_uri(name=account, issuer_name=issuer)
        except Exception:
            return None

    def verify_2fa(self, user_id: int, code: str, valid_window: int = 1) -> bool:
        try:
            rows = self.db.execute_query('SELECT secret FROM user_2fa WHERE user_id = ?', (user_id,))
            if not rows or pyotp is None:
                return False
            secret = rows[0]['secret'] if isinstance(rows[0], dict) else rows[0][0]
            return bool(pyotp.TOTP(secret).verify(code, valid_window=valid_window))
        except Exception:
            return False

    # ============ Password Strength (heuristic) ============
    def password_strength(self, password: str) -> Dict[str, Any]:
        length = len(password)
        classes = sum([
            bool(re.search(r'[a-z]', password)),
            bool(re.search(r'[A-Z]', password)),
            bool(re.search(r'\d', password)),
            bool(re.search(r'[^\w]', password)),
        ])
        score = 0
        feedback: List[str] = []  # type: ignore
        if length >= 12:
            score += 2
        elif length >= 8:
            score += 1
        else:
            feedback.append('زِد طول كلمة المرور إلى 12+')
        if classes >= 3:
            score += 2
        elif classes == 2:
            score += 1
        else:
            feedback.append('استخدم أحرف كبيرة وصغيرة وأرقام ورموز')
        if re.search(r'(.)\1{2,}', password):
            feedback.append('تجنب تكرار الأحرف')
            score -= 1
        for word in ('password', '123456', 'qwerty', 'admin'):
            if word in password.lower():
                feedback.append('تجنب الكلمات الشائعة')
                score -= 1
        rating = 'weak'
        if score >= 3:
            rating = 'strong'
        elif score == 2:
            rating = 'medium'
        return {"score": max(score, 0), "rating": rating, "feedback": feedback}

    # ============ Brute-force protection ============
    def record_login_attempt(self, username: str, success: bool, ip: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        try:
            self.db.execute_query(
                'INSERT INTO login_attempts (username, ip, user_agent, success, created_at) VALUES (?, ?, ?, ?, ?)',
                (username, ip, user_agent, 1 if success else 0, datetime.now().isoformat())
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f'فشل تسجيل محاولة الدخول: {e}')

    def is_blocked(self, username: str, ip: Optional[str] = None, window_minutes: int = 15, max_failures: int = 5) -> bool:
        try:
            cutoff = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
            params: List[Any] = [cutoff, username]  # type: ignore
            where = 'created_at >= ? AND username = ? AND success = 0'
            if ip:
                where += ' AND ip = ?'
                params.append(ip)
            rows = self.db.execute_query(
                f'SELECT COUNT(*) as cnt FROM login_attempts WHERE {where}',
                tuple(params)
            )
            cnt = rows[0]['cnt'] if rows and isinstance(rows[0], dict) else (rows[0][0] if rows else 0)
            return cnt >= max_failures
        except Exception:
            return False

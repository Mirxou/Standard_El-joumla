#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إعادة تعيين كلمة سر admin باستخدام الطريقة الصحيحة (PBKDF2)"""
import sys
import io
import hashlib
import secrets
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager

def hash_password_pbkdf2(password: str, salt: str) -> str:
    """تشفير كلمة المرور باستخدام PBKDF2 (نفس الطريقة المستخدمة في user.py)"""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

config = ConfigManager()
db = DatabaseManager(config.get_database_path())
db.initialize()

print("=== إعادة تعيين كلمة سر admin (الطريقة الصحيحة) ===\n")

# الحصول على المستخدم
admin = db.fetch_one('SELECT id, username, salt FROM users WHERE username = ?', ('admin',))

if not admin:
    print("❌ المستخدم admin غير موجود!")
    sys.exit(1)

user_id = admin['id']
salt = admin['salt'] if admin['salt'] else secrets.token_hex(16)

if not admin['salt']:
    print(f"⚠️ لم يكن هناك salt، تم إنشاء واحد جديد")

new_password = "admin123"

# تشفير كلمة المرور
password_hash = hash_password_pbkdf2(new_password, salt)

# تحديث قاعدة البيانات
try:
    db.execute_non_query(
        'UPDATE users SET password_hash = ?, salt = ?, failed_login_attempts = 0, is_locked = 0 WHERE id = ?',
        (password_hash, salt, user_id)
    )
    print(f"✅ تم تحديث كلمة مرور 'admin' بنجاح")
    print(f"\n🔑 بيانات الدخول:")
    print(f"   Username: admin")
    print(f"   Password: admin123")
    print(f"\n💡 جرب الآن: python main.py")
except Exception as e:
    print(f"❌ خطأ في التحديث: {e}")
    sys.exit(1)

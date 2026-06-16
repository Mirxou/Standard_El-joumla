#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعادة تعيين كلمة سر admin باستخدام الطريقة الصحيحة (PBKDF2)

الاستخدام: python fix_admin_password.py [new_password]
           أو استخدم متغير البيئة: ADMIN_PASSWORD=your_password python fix_admin_password.py
"""
import sys
import os
import io
import hashlib
import secrets
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# الحصول على كلمة المرور من متغير البيئة أو المعاملات
new_password = os.getenv('ADMIN_PASSWORD')
if not new_password:
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
    else:
        print("❌ خطأ: يجب تحديد كلمة المرور الجديدة")
        print("   الاستخدام:")
        print("   - ADMIN_PASSWORD=كلمة_مرور python fix_admin_password.py")
        print("   - python fix_admin_password.py كلمة_المرور")
        sys.exit(1)

# التحقق من قوة كلمة المرور
if len(new_password) < 8:
    print("❌ خطأ: كلمة المرور يجب أن تكون 8 أحرف على الأقل")
    sys.exit(1)

sys.path.insert(0, str(Path.cwd()))
from src.core.local_database_manager import LocalDatabaseManager
from src.core.config_manager import ConfigManager

def hash_password_pbkdf2(password: str, salt: str) -> str:
    """تشفير كلمة المرور باستخدام PBKDF2"""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

config = ConfigManager()
db = LocalDatabaseManager(config.get_database_path())
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

# تشفير كلمة المرور
password_hash = hash_password_pbkdf2(new_password, salt)

# تحديث قاعدة البيانات
try:
    db.execute_non_query(
        'UPDATE users SET password_hash = ?, salt = ?, failed_login_attempts = 0, is_locked = 0 WHERE id = ?',
        (password_hash, salt, user_id)
    )
    print(f"✅ تم تحديث كلمة مرور 'admin' بنجاح")
    print(f"\n💡 جرب الآن: python main.py")
except Exception as e:
    print(f"❌ خطأ في التحديث: {e}")
    sys.exit(1)
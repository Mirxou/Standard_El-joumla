#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إدارة كلمات المرور - Password Management Utility
وحدة مركزية لجميع عمليات إدارة كلمات المرور

الاستخدام:
    python password_manager.py reset-admin [new_password]
    python password_manager.py create-user [username] [email] [password]
    python password_manager.py check-strength [password]

أو استخدم متغيرات البيئة:
    ADMIN_PASSWORD=your_password python password_manager.py reset-admin
"""

import sys
import os
import hashlib
import secrets
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager
from src.models.user import UserManager, User, UserRole
from src.core.security_service import AdvancedSecurityService
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def hash_password_pbkdf2(password: str, salt: str) -> str:
    """تشفير كلمة المرور باستخدام PBKDF2"""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()


def validate_password(password: str) -> bool:
    """التحقق من قوة كلمة المرور"""
    if len(password) < 8:
        print("❌ خطأ: كلمة المرور يجب أن تكون 8 أحرف على الأقل")
        return False
    return True


def reset_admin_password(new_password: str = None):
    """إعادة تعيين كلمة مرور المدير"""
    if not new_password:
        new_password = os.getenv('ADMIN_PASSWORD')
    
    if not new_password:
        print("❌ خطأ: يجب تحديد كلمة المرور الجديدة")
        print("   الاستخدام: ADMIN_PASSWORD=كلمة_مرور python password_manager.py reset-admin")
        return False
    
    if not validate_password(new_password):
        return False
    
    config = ConfigManager()
    db = DatabaseManager(config.get_database_path())
    
    if not db.initialize():
        print("❌ فشل تهيئة قاعدة البيانات")
        return False
    
    admin = db.fetch_one('SELECT id, username, salt FROM users WHERE username = ?', ('admin',))
    
    if not admin:
        print("❌ المستخدم admin غير موجود!")
        return False
    
    user_id = admin['id']
    salt = admin['salt'] if admin['salt'] else secrets.token_hex(16)
    
    if not admin['salt']:
        print("⚠️ لم يكن هناك salt، تم إنشاء واحد جديد")
    
    password_hash = hash_password_pbkdf2(new_password, salt)
    
    try:
        db.execute_non_query(
            'UPDATE users SET password_hash = ?, salt = ?, failed_login_attempts = 0, is_locked = 0 WHERE id = ?',
            (password_hash, salt, user_id)
        )
        print("✅ تم تحديث كلمة مرور 'admin' بنجاح")
        return True
    except Exception as e:
        print(f"❌ خطأ في التحديث: {e}")
        return False


def create_user(username: str, email: str, password: str):
    """إنشاء مستخدم جديد"""
    if not validate_password(password):
        return False
    
    config = ConfigManager()
    db = DatabaseManager(config.get_database_path())
    
    if not db.initialize():
        print("❌ فشل تهيئة قاعدة البيانات")
        return False
    
    user_manager = UserManager(db, logger)
    
    try:
        user = User(
            username=username,
            email=email,
            password_hash="",
            salt=secrets.token_hex(16),
            full_name=username,
            role=UserRole.USER,
            company_id=1,
            is_active=True
        )
        user_manager.create_user(user, password)
        print(f"✅ تم إنشاء المستخدم '{username}' بنجاح")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء المستخدم: {e}")
        return False


def check_password_strength(password: str):
    """فحص قوة كلمة المرور"""
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("❌ يجب أن تكون 8 أحرف على الأقل")
    
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("❌ يجب أن تحتوي على أحرف كبيرة")
    
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("❌ يجب أن تحتوي على أحرف صغيرة")
    
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("❌ يجب أن تحتوي على أرقام")
    
    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        score += 1
    else:
        feedback.append("❌ يجب أن تحتوي على رموز خاصة")
    
    strength = ["ضعيفة جداً", "ضعيفة", "متوسطة", "قوية", "قوية جداً"]
    
    print(f"قوة كلمة المرور: {strength[score-1] if score > 0 else strength[0]} ({score}/5)")
    
    if feedback:
        print("\nالتوصيات:")
        for f in feedback:
            print(f"  {f}")
    
    return score >= 3


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "reset-admin":
        password = sys.argv[2] if len(sys.argv) > 2 else None
        reset_admin_password(password)
    
    elif command == "create-user":
        if len(sys.argv) < 5:
            print("❌ الاستخدام: python password_manager.py create-user [username] [email] [password]")
            return
        create_user(sys.argv[2], sys.argv[3], sys.argv[4])
    
    elif command == "check-strength":
        if len(sys.argv) < 3:
            print("❌ الاستخدام: python password_manager.py check-strength [password]")
            return
        check_password_strength(sys.argv[2])
    
    else:
        print(f"❌ أمر غير معروف: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
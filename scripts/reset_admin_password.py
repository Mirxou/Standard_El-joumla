#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعادة تعيين كلمة مرور المستخدم admin
Reset admin user password
"""

import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.security_service import AdvancedSecurityService

def reset_admin_password(new_password: str = "admin123"):
    """إعادة تعيين كلمة مرور admin"""
    print("🔧 إعادة تعيين كلمة مرور admin...")
    
    db_manager = DatabaseManager()
    if not db_manager.initialize():
        print("❌ فشل تهيئة قاعدة البيانات")
        return False
    
    # التحقق من وجود المستخدم أولاً
    user = db_manager.fetch_one(
        "SELECT id, username FROM users WHERE username = ?",
        ("admin",)
    )
    
    if not user:
        print("❌ المستخدم 'admin' غير موجود")
        print("💡 استخدم: python scripts/test_login.py --create-user")
        return False
    
    # التعامل مع sqlite3.Row أو tuple
    if hasattr(user, 'keys') and 'id' in user.keys():
        user_id = user['id']
    elif isinstance(user, (tuple, list)):
        user_id = user[0]
    else:
        user_id = user.get('id') if isinstance(user, dict) else user[0]
    
    # إنشاء security service بعد التحقق من المستخدم
    security_service = AdvancedSecurityService(db_manager)
    
    # إنشاء hash جديد لكلمة المرور
    password_hash = security_service.hash_password(new_password)
    
    # تحديث كلمة المرور
    try:
        db_manager.execute_query(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )
        print(f"✅ تم تحديث كلمة مرور 'admin' بنجاح")
        print(f"   Username: admin")
        print(f"   Password: {new_password}")
        print(f"   Hash Method: {security_service.hash_method}")
        return True
    except Exception as e:
        print(f"❌ خطأ في تحديث كلمة المرور: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="إعادة تعيين كلمة مرور admin")
    parser.add_argument(
        "--password",
        default="admin123",
        help="كلمة المرور الجديدة (default: admin123)"
    )
    
    args = parser.parse_args()
    
    reset_admin_password(args.password)


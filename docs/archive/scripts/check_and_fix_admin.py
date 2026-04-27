#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من مستخدم admin وإعادة تعيين كلمة المرور إذا لزم الأمر
"""

import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent))

# تجنب استيراد PySide6
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from src.core.database_manager import DatabaseManager
from src.models.user import UserManager, User, UserRole
from src.utils.logger import setup_logger
import secrets

logger = setup_logger(__name__)

def check_and_fix_admin(username: str = "admin", password: str = "admin123"):
    """التحقق من مستخدم admin وإعادة تعيين كلمة المرور"""
    try:
        print("🔧 تهيئة قاعدة البيانات...")
        db_manager = DatabaseManager()
        if not db_manager.initialize():
            print("❌ فشل تهيئة قاعدة البيانات")
            return False
        
        print("👤 البحث عن المستخدم...")
        user_manager = UserManager(db_manager, logger)
        
        # البحث عن المستخدم
        user = user_manager.get_user_by_username(username)
        
        if not user:
            print(f"❌ المستخدم '{username}' غير موجود")
            print(f"➕ إنشاء مستخدم جديد...")
            
            # إنشاء مستخدم جديد
            admin_user = User(
                username=username,
                email="admin@system.local",
                full_name="مدير النظام",
                role=UserRole.ADMIN.value if hasattr(UserRole, 'ADMIN') else 'admin',
                is_active=True
            )
            
            user_id = user_manager.create_user(admin_user, password)
            
            if user_id:
                print(f"✅ تم إنشاء المستخدم بنجاح! (ID: {user_id})")
            else:
                print("❌ فشل إنشاء المستخدم")
                return False
        else:
            print(f"✅ تم العثور على المستخدم: {user.username} (ID: {user.id})")
            print(f"🔄 التحقق من كلمة المرور...")
            
            # محاولة تسجيل الدخول للتحقق من كلمة المرور
            test_user = user_manager.authenticate_user(username, password)
            
            if not test_user:
                print(f"⚠️  كلمة المرور غير صحيحة. إعادة تعيين...")
                
                # إعادة تعيين كلمة المرور
                new_salt = secrets.token_hex(32)
                password_hash = user_manager._hash_password(password, new_salt)
                
                from datetime import datetime
                db_manager.execute_non_query(
                    """
                    UPDATE users 
                    SET password_hash = ?, 
                        salt = ?,
                        last_password_change = ?,
                        password_expires_at = NULL,
                        failed_login_attempts = 0,
                        is_locked = 0
                    WHERE id = ?
                    """,
                    (password_hash, new_salt, datetime.now(), user.id)
                )
                
                print("✅ تم إعادة تعيين كلمة المرور بنجاح!")
            else:
                print("✅ كلمة المرور صحيحة!")
        
        print(f"\n📋 معلومات تسجيل الدخول:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"\n⚠️  يرجى تغيير كلمة المرور بعد تسجيل الدخول الأول!")
        return True
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_and_fix_admin("admin", "admin123")
    sys.exit(0 if success else 1)

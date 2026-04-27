#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعادة تعيين كلمة مرور المدير
Reset admin password

الاستخدام: python reset_admin_password.py [username] [new_password]
           أو استخدم متغيرات البيئة: ADMIN_PASSWORD=your_password python reset_admin_password.py
"""

import sys
import os
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.models.user import UserManager
from src.utils.logger import setup_logger
import secrets

logger = setup_logger(__name__)

def reset_admin_password(
    username: str = "admin",
    new_password: str = None
):
    """إعادة تعيين كلمة مرور المدير"""
    # الحصول على كلمة المرور من متغير البيئة أو معامل
    if new_password is None:
        new_password = os.getenv('ADMIN_PASSWORD')
    if new_password is None:
        print("❌ خطأ: يجب تحديد كلمة المرور الجديدة")
        print("   استخدم: ADMIN_PASSWORD=كلمة_مرور python reset_admin_password.py")
        print("   أو: python reset_admin_password.py admin كلمة_المرور")
        return False
    
    # التحقق من قوة كلمة المرور
    if len(new_password) < 8:
        print("❌ خطأ: كلمة المرور يجب أن تكون 8 أحرف على الأقل")
        return False
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
            # محاولة البحث بالبريد الإلكتروني
            user_data = db_manager.fetch_one(
                "SELECT id, username FROM users WHERE email = ?",
                (username,)
            )
            if user_data:
                user = user_manager.get_user_by_id(user_data['id'])
        
        if not user:
            print(f"❌ المستخدم '{username}' غير موجود")
            return False
        
        print(f"✅ تم العثور على المستخدم: {user.username} (ID: {user.id})")
        print(f"🔄 إعادة تعيين كلمة المرور...")
        
        # إعادة تعيين كلمة المرور
        success = user_manager.change_password(user.id, user.password_hash, new_password)
        
        if not success:
            # إذا فشل change_password (لأنه يتطلب كلمة المرور القديمة)،
            # نستخدم طريقة مباشرة
            print("⚠️  استخدام طريقة مباشرة لإعادة تعيين كلمة المرور...")
            
            # إنشاء salt جديد
            new_salt = secrets.token_hex(32)
            
            # تشفير كلمة المرور الجديدة
            password_hash = user_manager._hash_password(new_password, new_salt)
            
            # تحديث في قاعدة البيانات
            from datetime import datetime
            db_manager.execute_non_query(
                """
                UPDATE users 
                SET password_hash = ?, 
                    salt = ?,
                    last_password_change = ?,
                    password_expires_at = NULL
                WHERE id = ?
                """,
                (password_hash, new_salt, datetime.now(), user.id)
            )
            
            print("✅ تم إعادة تعيين كلمة المرور بنجاح!")
        else:
            print("✅ تم إعادة تعيين كلمة المرور بنجاح!")
        
        print(f"\n📋 معلومات تسجيل الدخول:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email if hasattr(user, 'email') else 'N/A'}")
        print(f"   Password: {new_password}")
        print(f"\n⚠️  يرجى تغيير كلمة المرور بعد تسجيل الدخول الأول!")
        return True
    
    except Exception as e:
        print(f"❌ خطأ في إعادة تعيين كلمة المرور: {e}")
        logger.error(f"خطأ في إعادة تعيين كلمة المرور: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="إعادة تعيين كلمة مرور المدير")
    parser.add_argument("--username", default="admin", help="اسم المستخدم")
    parser.add_argument("--password", default="admin123", help="كلمة المرور الجديدة")
    
    args = parser.parse_args()
    
    success = reset_admin_password(
        username=args.username,
        new_password=args.password
    )
    
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إنشاء مستخدم المدير الافتراضي
Create default admin user

الاستخدام: python create_admin_user.py [username] [email] [password]
           أو استخدم متغيرات البيئة: ADMIN_PASSWORD=your_password python create_admin_user.py
"""

import sys
import os
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.models.user import UserManager, User, UserRole
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def create_admin_user(
    username: str = "admin",
    email: str = "admin@standard.com",
    password: str = None,
    full_name: str = "مدير النظام"
):
    """إنشاء مستخدم المدير الافتراضي"""
    # الحصول على كلمة المرور من متغير البيئة أو معامل
    if password is None:
        password = os.getenv('ADMIN_PASSWORD')
    if password is None:
        print("❌ خطأ: يجب تحديد كلمة المرور")
        print("   استخدم: ADMIN_PASSWORD=كلمة_مرور python create_admin_user.py")
        print("   أو: python create_admin_user.py admin admin@example.com كلمة_المرور")
        return False
    
    # التحقق من قوة كلمة المرور
    if len(password) < 8:
        print("❌ خطأ: كلمة المرور يجب أن تكون 8 أحرف على الأقل")
        return False
    try:
        print("🔧 تهيئة قاعدة البيانات...")
        db_manager = DatabaseManager()
        if not db_manager.initialize():
            print("❌ فشل تهيئة قاعدة البيانات")
            return False
        
        print("👤 التحقق من وجود المستخدم...")
        user_manager = UserManager(db_manager, logger)
        
        # التحقق من وجود المستخدم بالبريد الإلكتروني أو اسم المستخدم
        existing_user = db_manager.fetch_one(
            "SELECT id, username, email FROM users WHERE username = ? OR email = ?",
            (username, email)
        )
        
        if existing_user:
            print(f"⚠️  المستخدم موجود بالفعل:")
            print(f"   - ID: {existing_user['id']}")
            print(f"   - Username: {existing_user['username']}")
            email = existing_user.get('email') if hasattr(existing_user, 'get') else (existing_user['email'] if 'email' in existing_user.keys() else 'N/A')
            print(f"   - Email: {email}")
            print(f"\n💡 يمكنك تسجيل الدخول باستخدام:")
            print(f"   Username: {existing_user['username']}")
            print(f"   Email: {email}")
            return True
        
        print("➕ إنشاء مستخدم المدير...")
        
        # إنشاء مستخدم جديد
        admin_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=UserRole.ADMIN.value if hasattr(UserRole, 'ADMIN') else 'admin',
            is_active=True
        )
        
        user_id = user_manager.create_user(admin_user, password)
        
        if user_id and user_id > 0:
            print(f"✅ تم إنشاء مستخدم المدير بنجاح!")
            print(f"\n📋 معلومات تسجيل الدخول:")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"   User ID: {user_id}")
            print(f"\n⚠️  يرجى تغيير كلمة المرور بعد تسجيل الدخول الأول!")
            return True
        else:
            # محاولة الحصول على المستخدم مباشرة
            user = db_manager.fetch_one(
                "SELECT id, username, email FROM users WHERE username = ? OR email = ?",
                (username, email)
            )
            if user and user['id']:
                print(f"✅ المستخدم موجود بالفعل (ID: {user['id']})")
                print(f"\n📋 معلومات تسجيل الدخول:")
                print(f"   Username: {user['username']}")
                user_email = user.get('email') if hasattr(user, 'get') else (user['email'] if 'email' in user.keys() else email)
                print(f"   Email: {user_email}")
                print(f"   Password: {password}")
                return True
            else:
                print("❌ فشل إنشاء مستخدم المدير")
                return False
    
    except Exception as e:
        print(f"❌ خطأ في إنشاء مستخدم المدير: {e}")
        logger.error(f"خطأ في إنشاء مستخدم المدير: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="إنشاء مستخدم المدير الافتراضي")
    parser.add_argument("--username", default="admin", help="اسم المستخدم")
    parser.add_argument("--email", default="admin@standard.com", help="البريد الإلكتروني")
    parser.add_argument("--password", default="admin123", help="كلمة المرور")
    parser.add_argument("--full-name", default="مدير النظام", help="الاسم الكامل")
    
    args = parser.parse_args()
    
    success = create_admin_user(
        username=args.username,
        email=args.email,
        password=args.password,
        full_name=args.full_name
    )
    
    sys.exit(0 if success else 1)


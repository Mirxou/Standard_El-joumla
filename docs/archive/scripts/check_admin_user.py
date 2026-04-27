#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من مستخدم admin وإعادة تعيين كلمة المرور
"""

import sys
import io
import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

from src.core.database_manager import DatabaseManager

# إصلاح encoding في Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# الحصول على مسار قاعدة البيانات
project_root = Path(__file__).parent
db_path = project_root / "data" / "logical_release.db"

def hash_password(password: str, salt: str) -> str:
    """تشفير كلمة المرور"""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def check_and_fix_admin(username: str = "admin", password: str = "admin123"):
    """التحقق من مستخدم admin وإعادة تعيين كلمة المرور"""
    try:
        print("🔧 فتح قاعدة البيانات...")
        
        if not db_path.exists():
            print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
            return False
        
        db_manager = DatabaseManager(str(db_path))
        db_manager.initialize()
        db_manager.connection.row_factory = sqlite3.Row
        cursor = db_manager.connection.cursor()
        
        print("👤 البحث عن المستخدم...")
        
        # البحث عن المستخدم
        cursor.execute("SELECT id, username, email, password_hash, salt, is_active, is_locked FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        
        if not user_row:
            print(f"❌ المستخدم '{username}' غير موجود")
            print(f"➕ إنشاء مستخدم جديد...")
            
            # إنشاء salt جديد
            new_salt = secrets.token_hex(32)
            password_hash = hash_password(password, new_salt)
            
            # إدراج المستخدم
            cursor.execute("""
                INSERT INTO users (
                    username, email, full_name, role, password_hash, salt,
                    is_active, is_locked, failed_login_attempts,
                    last_password_change, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                "admin@system.local",
                "مدير النظام",
                "admin",
                password_hash,
                new_salt,
                1,  # is_active
                0,  # is_locked
                0,  # failed_login_attempts
                datetime.now(),
                datetime.now(),
                datetime.now()
            ))
            
            db_manager.connection.commit()
            user_id = cursor.lastrowid
            print(f"✅ تم إنشاء المستخدم بنجاح! (ID: {user_id})")
        else:
            user_id = user_row['id']
            print(f"✅ تم العثور على المستخدم: {user_row['username']} (ID: {user_id})")
            
            # التحقق من كلمة المرور
            stored_hash = user_row['password_hash']
            stored_salt = user_row['salt']
            test_hash = hash_password(password, stored_salt)
            
            if test_hash != stored_hash:
                print(f"⚠️  كلمة المرور غير صحيحة. إعادة تعيين...")
                
                # إعادة تعيين كلمة المرور
                new_salt = secrets.token_hex(32)
                password_hash = hash_password(password, new_salt)
                
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = ?, 
                        salt = ?,
                        last_password_change = ?,
                        password_expires_at = NULL,
                        failed_login_attempts = 0,
                        is_locked = 0
                    WHERE id = ?
                """, (password_hash, new_salt, datetime.now(), user_id))
                
                db_manager.connection.commit()
                print("✅ تم إعادة تعيين كلمة المرور بنجاح!")
            else:
                print("✅ كلمة المرور صحيحة!")
            
            # التحقق من حالة المستخدم
            if user_row['is_locked']:
                print("⚠️  المستخدم مقفل. إلغاء القفل...")
                cursor.execute("UPDATE users SET is_locked = 0, failed_login_attempts = 0 WHERE id = ?", (user_id,))
                db_manager.connection.commit()
                print("✅ تم إلغاء قفل المستخدم!")
            
            if not user_row['is_active']:
                print("⚠️  المستخدم غير نشط. تفعيل...")
                cursor.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))
                db_manager.connection.commit()
                print("✅ تم تفعيل المستخدم!")
        
        db_manager.connection.close()
        
        print(f"\n📋 معلومات تسجيل الدخول:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"\n✅ جاهز لتسجيل الدخول!")
        return True
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_and_fix_admin("admin", "admin123")
    sys.exit(0 if success else 1)

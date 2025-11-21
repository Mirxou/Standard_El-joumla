#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعادة تعيين كلمة مرور المدير
Reset admin password utility
"""

import sys
import getpass
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.security_service import AdvancedSecurityService

def reset_admin_password():
    """إعادة تعيين كلمة مرور المدير"""
    print("=" * 70)
    print("🔐 إعادة تعيين كلمة مرور المدير")
    print("=" * 70)
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        # Initialize security service
        security = AdvancedSecurityService()
        
        # Get admin user
        admin = db_manager.fetch_one(
            "SELECT * FROM users WHERE username = ? OR role = ?",
            ('admin', 'admin')
        )
        
        if not admin:
            print("❌ لم يتم العثور على حساب المدير")
            return False
        
        admin_id = admin[0]
        admin_username = admin[1]
        
        print(f"\n✅ تم العثور على حساب المدير: {admin_username}")
        print("\nأدخل كلمة المرور الجديدة:")
        
        # Get new password with confirmation
        while True:
            password = getpass.getpass("كلمة المرور: ")
            
            if len(password) < 8:
                print("❌ كلمة المرور يجب أن تكون 8 أحرف على الأقل")
                continue
            
            password_confirm = getpass.getpass("تأكيد كلمة المرور: ")
            
            if password != password_confirm:
                print("❌ كلمات المرور غير متطابقة")
                continue
            
            break
        
        # Hash the new password
        password_hash, salt = security.hash_password(password)
        
        # Update password in database
        db_manager.execute_query(
            """
            UPDATE users 
            SET password_hash = ?, 
                salt = ?,
                last_password_change = CURRENT_TIMESTAMP,
                failed_login_attempts = 0,
                is_locked = 0
            WHERE id = ?
            """,
            (password_hash, salt, admin_id)
        )
        
        print("\n" + "=" * 70)
        print("✅ تم إعادة تعيين كلمة المرور بنجاح!")
        print("=" * 70)
        print(f"\nاسم المستخدم: {admin_username}")
        print("يمكنك الآن تسجيل الدخول بكلمة المرور الجديدة")
        
        # Log security event
        db_manager.execute_query(
            """
            INSERT INTO audit_log (user_id, action, table_name, new_values)
            VALUES (?, ?, ?, ?)
            """,
            (admin_id, 'password_reset', 'users', 'Password reset via script')
        )
        
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    success = reset_admin_password()
    sys.exit(0 if success else 1)

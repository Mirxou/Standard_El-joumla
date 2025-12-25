#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار Login API وإنشاء مستخدم تجريبي
Test Login API and create test user
"""

import requests
import json
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.security_service import AdvancedSecurityService

def create_test_user():
    """إنشاء مستخدم تجريبي"""
    print("🔧 إنشاء مستخدم تجريبي...")
    
    db_manager = DatabaseManager()
    if not db_manager.initialize():
        print("❌ فشل تهيئة قاعدة البيانات")
        return False
    
    security_service = AdvancedSecurityService(db_manager)
    
    # بيانات المستخدم
    username = "admin"
    password = "admin123"
    full_name = "مدير النظام"
    email = "admin@example.com"
    
    # التحقق من وجود المستخدم
    existing_user = db_manager.fetch_one(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    
    if existing_user:
        print(f"⚠️ المستخدم '{username}' موجود بالفعل")
        return True
    
    # إنشاء hash لكلمة المرور
    # استخدام Argon2 إذا كان متاحاً، وإلا PBKDF2
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        password_hash = ph.hash(password)
    except ImportError:
        # استخدام PBKDF2 كبديل
        password_hash = security_service.hash_password(password)
    
    # إدراج المستخدم
    try:
        db_manager.execute_query(
            """
            INSERT INTO users (username, password_hash, full_name, email, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, password_hash, full_name, email, "admin", True)
        )
        print(f"✅ تم إنشاء المستخدم '{username}' بنجاح")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء المستخدم: {e}")
        return False


def test_login(base_url: str = "http://localhost:8000"):
    """اختبار Login API"""
    print(f"\n🧪 اختبار Login API على: {base_url}")
    print("=" * 50)
    
    # بيانات Login
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # طلب Login
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📤 Request:")
        print(f"   URL: {response.url}")
        print(f"   Method: POST")
        print(f"   Body: {json.dumps(login_data, ensure_ascii=False, indent=2)}")
        
        print(f"\n📥 Response:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login نجح!")
            print(f"\n📋 بيانات الاستجابة:")
            print(f"   Access Token: {data.get('access_token', '')[:50]}...")
            print(f"   Token Type: {data.get('token_type', '')}")
            print(f"   User ID: {data.get('user_id', '')}")
            print(f"   Username: {data.get('username', '')}")
            
            # حفظ Token للاستخدام لاحقاً
            token = data.get('access_token')
            if token:
                print(f"\n💾 Token محفوظ للاستخدام في الاختبارات التالية")
                return token
        else:
            print(f"   ❌ Login فشل")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ لا يمكن الاتصال بالـ API على {base_url}")
        print(f"   تأكد من أن الـ API يعمل: uvicorn src.api.app:app --host 0.0.0.0 --port 8000")
        return None
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None


def test_protected_endpoint(base_url: str = "http://localhost:8000", token: str = None):
    """اختبار endpoint محمي"""
    if not token:
        print("\n⚠️ لا يوجد Token - تخطي اختبار الـ endpoints المحمية")
        return
    
    print(f"\n🔒 اختبار Protected Endpoint: /api/v1/auth/me")
    print("=" * 50)
    
    try:
        response = requests.get(
            f"{base_url}/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"\n📥 Response:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ نجح!")
            print(f"\n📋 بيانات المستخدم:")
            for key, value in data.items():
                print(f"   {key}: {value}")
        else:
            print(f"   ❌ فشل")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"❌ خطأ: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="اختبار Login API")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL للـ API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--create-user",
        action="store_true",
        help="إنشاء مستخدم تجريبي قبل الاختبار"
    )
    
    args = parser.parse_args()
    
    # إنشاء مستخدم تجريبي إذا طُلب
    if args.create_user:
        create_test_user()
        print()
    
    # اختبار Login
    token = test_login(args.url)
    
    # اختبار Protected Endpoint
    if token:
        test_protected_endpoint(args.url, token)
    
    print("\n" + "=" * 50)
    print("✅ انتهى الاختبار")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار تسجيل الدخول
Test login functionality
"""

import sys
import io
import requests
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
def test_login():
    """اختبار تسجيل الدخول"""
    base_url = "http://localhost:8000"
    
    print("Test login...")
    print(f"Connecting to: {base_url}")
    
    # محاولة تسجيل الدخول
    login_data = {
        "username": "admin@standard.com",
        "password": "admin123"
    }
    
    try:
        print(f"\nSending login request...")
        print(f"   Username: {login_data['username']}")
        print(f"   Password: {'*' * len(login_data['password'])}")
        
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nResponse:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Login successful!")
            print(f"   Access Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"   User ID: {data.get('user', {}).get('id', 'N/A')}")
            print(f"   Username: {data.get('user', {}).get('username', 'N/A')}")
            
            # اختبار استخدام الـ token
            token = data.get('access_token')
            if token:
                print(f"\nTesting token usage...")
                headers = {"Authorization": f"Bearer {token}"}
                notif_response = requests.get(
                    f"{base_url}/api/v1/notifications",
                    headers=headers,
                    timeout=10
                )
                print(f"   Notifications Status: {notif_response.status_code}")
                if notif_response.status_code == 200:
                    notif_data = notif_response.json()
                    print(f"   [OK] Access to notifications successful!")
                    print(f"   Number of notifications: {notif_data.get('total', 0)}")
                else:
                    print(f"   [ERROR] Failed to access notifications: {notif_response.text}")
            
            return True
        else:
            print(f"   ❌ فشل تسجيل الدخول")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"   [ERROR] Cannot connect to server. Make sure server is running on {base_url}")
        return False
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    sys.exit(0 if success else 1)





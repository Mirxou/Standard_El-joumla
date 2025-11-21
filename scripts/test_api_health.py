#!/usr/bin/env python3
"""
Quick API Health Check
Tests all critical endpoints to ensure API is working correctly.
"""
import requests
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_health() -> bool:
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        print(f"❌ Health check failed: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_login() -> Dict[str, Any]:
    """Test login endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful - Token expires in {data['expires_in_hours']}h")
            return {"success": True, "token": data["access_token"]}
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return {"success": False, "token": None}
    except Exception as e:
        print(f"❌ Login error: {e}")
        return {"success": False, "token": None}

def test_protected_endpoint(token: str, endpoint: str) -> bool:
    """Test protected endpoint with JWT"""
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {endpoint} - Total: {data.get('total', 'N/A')}, Items: {len(data.get('items', []))}")
            return True
        print(f"❌ {endpoint} failed: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ {endpoint} error: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 Logical Version API Health Check")
    print("=" * 60)
    print()
    
    # Test 1: Health
    if not test_health():
        print("\n❌ API server is not running or not responding")
        print("Run: python scripts/run_api_server.py")
        sys.exit(1)
    
    print()
    
    # Test 2: Login
    login_result = test_login()
    if not login_result["success"]:
        print("\n❌ Login failed - check admin credentials")
        sys.exit(1)
    
    print()
    
    # Test 3: Protected endpoints
    token = login_result["token"]
    endpoints = [
        "/customers?page=1&page_size=10",
        "/products?page=1&page_size=10",
        "/invoices?page=1&page_size=10"
    ]
    
    failed = 0
    for endpoint in endpoints:
        if not test_protected_endpoint(token, endpoint):
            failed += 1
    
    print()
    print("=" * 60)
    if failed == 0:
        print("🎉 All API tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"⚠️  {failed} test(s) failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()

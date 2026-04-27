#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Test Script
اختبار شامل لـ REST API
"""

import sys
import urllib.request
import urllib.error
import json

def test_endpoint(url, expected_status=200, description=""):
    """اختبار endpoint"""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            data = response.read().decode()
            
            if status == expected_status:
                print(f"   ✅ {description}")
                return True, data
            else:
                print(f"   ❌ {description} (HTTP {status})")
                return False, data
    except urllib.error.HTTPError as e:
        if e.code == expected_status:
            print(f"   ✅ {description} (HTTP {e.code})")
            return True, ""
        else:
            print(f"   ❌ {description} (HTTP {e.code})")
            return False, ""
    except Exception as e:
        print(f"   ❌ {description}: {e}")
        return False, ""


def test_health_check(base_url):
    """اختبار Health Check"""
    print("1️⃣ اختبار Health Check...")
    
    success, data = test_endpoint(
        f"{base_url}/health",
        description="Health Check"
    )
    
    if success and data:
        try:
            response = json.loads(data)
            print(f"      Response: {response}")
        except:
            pass
    
    return 1 if success else 0, 0 if success else 1


def test_api_health_check(base_url):
    """اختبار API Health Check"""
    print("\n2️⃣ اختبار API Health Check...")
    
    success, data = test_endpoint(
        f"{base_url}/api/v1/health",
        description="API Health Check"
    )
    
    if success and data:
        try:
            response = json.loads(data)
            print(f"      Response: {response}")
        except:
            pass
    
    return 1 if success else 0, 0 if success else 1


def test_openapi_docs(base_url):
    """اختبار OpenAPI Documentation"""
    print("\n3️⃣ اختبار OpenAPI Documentation...")
    
    success, _ = test_endpoint(
        f"{base_url}/docs",
        description="Swagger UI"
    )
    
    return 1 if success else 0, 0 if success else 1


def test_openapi_json(base_url):
    """اختبار OpenAPI JSON"""
    print("\n4️⃣ اختبار OpenAPI JSON...")
    
    success, _ = test_endpoint(
        f"{base_url}/openapi.json",
        description="OpenAPI JSON"
    )
    
    return 1 if success else 0, 0 if success else 1


def test_login_endpoint(base_url):
    """اختبار Login Endpoint"""
    print("\n5️⃣ اختبار Login Endpoint...")
    
    try:
        data = json.dumps({
            "username": "test",
            "password": "test"
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{base_url}/api/v1/auth/login",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                # Login should fail with invalid credentials
                print("   ⚠️ Login نجح (غير متوقع)")
                return 0, 1
        except urllib.error.HTTPError as e:
            if e.code in [401, 422]:
                print("   ✅ Login Endpoint يستجيب (فشل متوقع)")
                return 1, 0
            else:
                print(f"   ❌ Login Endpoint (HTTP {e.code})")
                return 0, 1
    except Exception as e:
        print(f"   ❌ Login Endpoint: {e}")
        return 0, 1


def main():
    """الدالة الرئيسية"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"🧪 اختبار REST API على: {base_url}")
    print("=" * 50)
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Health Check
    passed, failed = test_health_check(base_url)
    total_passed += passed
    total_failed += failed
    
    # Test 2: API Health Check
    passed, failed = test_api_health_check(base_url)
    total_passed += passed
    total_failed += failed
    
    # Test 3: OpenAPI Docs
    passed, failed = test_openapi_docs(base_url)
    total_passed += passed
    total_failed += failed
    
    # Test 4: OpenAPI JSON
    passed, failed = test_openapi_json(base_url)
    total_passed += passed
    total_failed += failed
    
    # Test 5: Login
    passed, failed = test_login_endpoint(base_url)
    total_passed += passed
    total_failed += failed
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ملخص اختبارات API:")
    print(f"   ✅ نجحت: {total_passed}")
    print(f"   ❌ فشلت: {total_failed}")
    print("=" * 50)
    
    if total_failed == 0:
        print("\n🎉 جميع اختبارات API نجحت!")
        return 0
    else:
        print("\n⚠️ بعض الاختبارات فشلت.")
        return 1


if __name__ == "__main__":
    sys.exit(main())





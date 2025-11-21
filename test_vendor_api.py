"""
Vendor Management API Test Suite - v1.5.0
Tests for vendor CRUD, ratings, evaluations, and performance tracking
"""
import pytest
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Global variables
access_token = None
vendor_id = None


def get_auth_token(username: str = ADMIN_USERNAME, password: str = ADMIN_PASSWORD):
    """Get JWT access token"""
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200, f"Authentication failed: {response.text}"
    return response.json()["access_token"]


def get_headers():
    """Get authorization headers"""
    global access_token
    if not access_token:
        access_token = get_auth_token()
    return {"Authorization": f"Bearer {access_token}"}


def setup_module():
    """Setup test environment"""
    global access_token
    access_token = get_auth_token()
    print(f"\n✓ Authentication successful")


def test_01_create_vendor():
    """Test 1: Create a new vendor"""
    global vendor_id
    headers = get_headers()
    
    vendor_data = {
        "name": "شركة التوريدات المتقدمة",
        "contact_person": "أحمد محمد",
        "phone": "+966501234567",
        "email": "info@advanced-supplies.com",
        "address": "الجزائر العاصمة، الجزائر",
        "payment_terms": "آجل 30 يوم",
        "credit_limit": 100000.0
    }
    
    response = requests.post(
        f"{BASE_URL}/vendors",
        json=vendor_data,
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 1: Create Vendor")
    print(f"{'='*60}")
    print(f"Request: POST /vendors")
    print(f"Data: {json.dumps(vendor_data, indent=2, ensure_ascii=False)}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 201, f"Failed to create vendor: {response.text}"
    data = response.json()
    assert "id" in data
    vendor_id = data["id"]
    print(f"✓ Vendor created with ID: {vendor_id}")


def test_02_get_vendor():
    """Test 2: Get vendor details"""
    headers = get_headers()
    
    response = requests.get(
        f"{BASE_URL}/vendors/{vendor_id}",
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 2: Get Vendor Details")
    print(f"{'='*60}")
    print(f"Request: GET /vendors/{vendor_id}")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200, f"Failed to get vendor: {response.text}"
    data = response.json()
    
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    assert data["id"] == vendor_id
    assert data["name"] == "شركة التوريدات المتقدمة"
    print(f"✓ Vendor details retrieved successfully")


def test_03_search_vendors():
    """Test 3: Search vendors"""
    headers = get_headers()
    
    response = requests.get(
        f"{BASE_URL}/vendors?term=التوريدات",
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 3: Search Vendors")
    print(f"{'='*60}")
    print(f"Request: GET /vendors?term=التوريدات")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200, f"Failed to search vendors: {response.text}"
    data = response.json()
    
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1, "Should find at least 1 vendor"
    print(f"✓ Found {data['total']} vendor(s)")


def test_04_create_vendor_evaluation():
    """Test 4: Create vendor evaluation/rating"""
    headers = get_headers()
    
    evaluation_data = {
        "supplier_id": vendor_id,
        "evaluation_period_start": "2025-10-01",
        "evaluation_period_end": "2025-11-01",
        "quality_score": 4.5,
        "delivery_score": 4.8,
        "pricing_score": 4.2,
        "communication_score": 4.6,
        "reliability_score": 4.7,
        "total_orders": 10,
        "completed_orders": 10,
        "on_time_deliveries": 9,
        "late_deliveries": 1,
        "rejected_shipments": 0,
        "total_value": 500000.0,
        "notes": "أداء ممتاز خلال الشهر الماضي",
        "recommendations": "يُنصح بزيادة حجم الطلبات",
        "is_approved": True,
        "is_preferred": True
    }
    
    response = requests.post(
        f"{BASE_URL}/vendors/{vendor_id}/evaluations",
        json=evaluation_data,
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 4: Create Vendor Evaluation")
    print(f"{'='*60}")
    print(f"Request: POST /vendors/{vendor_id}/evaluations")
    print(f"Data: {json.dumps(evaluation_data, indent=2, ensure_ascii=False)}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 201, f"Failed to create evaluation: {response.text}"
    assert "id" in response.json()
    print(f"✓ Vendor evaluation created successfully")


def test_05_get_vendor_evaluation():
    """Test 5: Get vendor latest evaluation"""
    headers = get_headers()
    
    response = requests.get(
        f"{BASE_URL}/vendors/{vendor_id}/evaluation",
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 5: Get Vendor Evaluation")
    print(f"{'='*60}")
    print(f"Request: GET /vendors/{vendor_id}/evaluation")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200, f"Failed to get evaluation: {response.text}"
    data = response.json()
    
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    assert data["supplier_id"] == vendor_id
    assert "overall_score" in data
    assert "grade" in data
    print(f"✓ Overall Score: {data['overall_score']}, Grade: {data['grade']}")


def test_06_get_vendor_score():
    """Test 6: Get vendor score/grade"""
    headers = get_headers()
    
    response = requests.get(
        f"{BASE_URL}/vendors/{vendor_id}/score",
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 6: Get Vendor Score")
    print(f"{'='*60}")
    print(f"Request: GET /vendors/{vendor_id}/score")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200, f"Failed to get score: {response.text}"
    data = response.json()
    
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    assert "overall_score" in data
    assert "grade" in data
    assert data["supplier_id"] == vendor_id
    print(f"✓ Score: {data['overall_score']}, Grade: {data['grade']}")


def test_07_get_vendor_performance():
    """Test 7: Get vendor performance metrics"""
    headers = get_headers()
    
    response = requests.get(
        f"{BASE_URL}/vendors/{vendor_id}/performance",
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 7: Get Vendor Performance")
    print(f"{'='*60}")
    print(f"Request: GET /vendors/{vendor_id}/performance")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200, f"Failed to get performance: {response.text}"
    data = response.json()
    
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    assert "vendor_id" in data
    assert data["vendor_id"] == vendor_id
    print(f"✓ Performance metrics retrieved")


def test_08_unauthorized_create_vendor():
    """Test 8: Test unauthorized vendor creation"""
    # No token
    vendor_data = {
        "name": "Test Vendor",
        "contact_person": "Test",
        "phone": "123456"
    }
    
    response = requests.post(
        f"{BASE_URL}/vendors",
        json=vendor_data
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 8: Unauthorized Vendor Creation")
    print(f"{'='*60}")
    print(f"Request: POST /vendors (no token)")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 401, "Should reject unauthorized access"
    print("✓ Unauthorized access properly rejected")


def test_09_invalid_vendor_id():
    """Test 9: Test with invalid vendor ID"""
    headers = get_headers()
    
    response = requests.get(
        f"{BASE_URL}/vendors/999999",
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 9: Invalid Vendor ID")
    print(f"{'='*60}")
    print(f"Request: GET /vendors/999999")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 404, "Should return 404 for invalid vendor"
    print("✓ Invalid vendor ID handled correctly")


def test_10_validation_errors():
    """Test 10: Test validation (negative credit limit)"""
    headers = get_headers()
    
    invalid_data = {
        "name": "Test",
        "credit_limit": -1000
    }
    
    response = requests.post(
        f"{BASE_URL}/vendors",
        json=invalid_data,
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 10: Validation - Negative Credit Limit")
    print(f"{'='*60}")
    print(f"Request: POST /vendors (credit_limit=-1000)")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 422, "Should reject negative credit limit"
    print("✓ Validation working correctly")


def test_11_invalid_evaluation_scores():
    """Test 11: Test evaluation with invalid scores"""
    headers = get_headers()
    
    invalid_evaluation = {
        "supplier_id": vendor_id,
        "quality_score": 6.0,  # Max is 5
        "delivery_score": 4.0,
        "pricing_score": 4.0,
        "communication_score": 4.0,
        "reliability_score": 4.0,
        "total_orders": 5,
        "completed_orders": 5,
        "on_time_deliveries": 5,
        "late_deliveries": 0,
        "rejected_shipments": 0,
        "total_value": 1000.0
    }
    
    response = requests.post(
        f"{BASE_URL}/vendors/{vendor_id}/evaluations",
        json=invalid_evaluation,
        headers=headers
    )
    
    print(f"\n{'='*60}")
    print(f"TEST 11: Invalid Evaluation Scores")
    print(f"{'='*60}")
    print(f"Request: POST /vendors/{vendor_id}/evaluations (quality_score=6.0)")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 422, "Should reject score > 5"
    print("✓ Score validation working correctly")


def print_summary():
    """Print test summary"""
    print(f"\n{'='*60}")
    print("VENDOR MANAGEMENT API TEST SUITE - SUMMARY")
    print(f"{'='*60}")
    print("All tests completed successfully!")
    print("\nTested Features:")
    print("  ✓ Vendor CRUD (Create, Read)")
    print("  ✓ Vendor Search")
    print("  ✓ Vendor Evaluations/Ratings")
    print("  ✓ Vendor Score/Grade Calculation")
    print("  ✓ Vendor Performance Metrics")
    print("  ✓ Authorization checks")
    print("  ✓ Input validation")
    print("  ✓ Error handling")
    print(f"\n{'='*60}")


if __name__ == "__main__":
    # Run tests
    try:
        setup_module()
        test_01_create_vendor()
        test_02_get_vendor()
        test_03_search_vendors()
        test_04_create_vendor_evaluation()
        test_05_get_vendor_evaluation()
        test_06_get_vendor_score()
        test_07_get_vendor_performance()
        test_08_unauthorized_create_vendor()
        test_09_invalid_vendor_id()
        test_10_validation_errors()
        test_11_invalid_evaluation_scores()
        print_summary()
        print("\n✅ ALL TESTS PASSED!")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise

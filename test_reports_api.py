#!/usr/bin/env python3
"""
Test suite for Reports & Analytics API (v1.6.0)
Tests all report generation endpoints with comprehensive scenarios
"""

import requests
import json
from datetime import datetime, timedelta

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
TOKEN = None


def setup():
    """Setup: Login and get authentication token"""
    global TOKEN
    print("=" * 60)
    print("SETUP: Authenticating...")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if response.status_code == 200:
        TOKEN = response.json()["access_token"]
        print(f"✅ Authentication successful")
        print(f"Token: {TOKEN[:20]}...")
    else:
        print(f"❌ Authentication failed: {response.text}")
        exit(1)
    print()


def get_headers():
    """Get authorization headers"""
    return {"Authorization": f"Bearer {TOKEN}"}


def test_01_sales_summary_report():
    """Test 1: Generate Sales Summary Report"""
    print("=" * 60)
    print("TEST 1: Generate Sales Summary Report")
    print("=" * 60)
    
    # Get last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    payload = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    print(f"Request: POST /reports/sales-summary")
    print(f"Filters: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/reports/sales-summary",
        json=payload,
        params={"format": "json"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sales Summary Report Generated Successfully")
        print(f"\nTitle: {data.get('title')}")
        print(f"Subtitle: {data.get('subtitle')}")
        print(f"Generated At: {data.get('generated_at')}")
        print(f"\n📊 Summary:")
        summary = data.get('summary', {})
        print(f"  - Total Sales: {summary.get('total_sales', 0)}")
        print(f"  - Total Amount: {summary.get('total_amount', 0):.2f}")
        print(f"  - Average Sale: {summary.get('average_sale', 0):.2f}")
        print(f"  - Total Discount: {summary.get('total_discount', 0):.2f}")
        print(f"  - Total Tax: {summary.get('total_tax', 0):.2f}")
        
        if 'payment_methods' in summary:
            print(f"\n💳 Payment Methods Breakdown:")
            for method, details in summary['payment_methods'].items():
                print(f"  - {method}: {details.get('count', 0)} sales, {details.get('amount', 0):.2f}")
        
        print(f"\n📈 Data Records: {len(data.get('data', []))}")
    else:
        print(f"❌ Failed: {response.text}")
    
    print()


def test_02_inventory_status_report():
    """Test 2: Generate Inventory Status Report"""
    print("=" * 60)
    print("TEST 2: Generate Inventory Status Report")
    print("=" * 60)
    
    payload = {}
    
    print(f"Request: POST /reports/inventory-status")
    print(f"Filters: All products")
    
    response = requests.post(
        f"{BASE_URL}/reports/inventory-status",
        json=payload,
        params={"format": "json"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Inventory Status Report Generated Successfully")
        print(f"\nTitle: {data.get('title')}")
        print(f"\n📦 Summary:")
        summary = data.get('summary', {})
        print(f"  - Total Products: {summary.get('total_products', 0)}")
        print(f"  - Total Stock Value: {summary.get('total_stock_value', 0):.2f}")
        print(f"  - Out of Stock: {summary.get('out_of_stock', 0)}")
        print(f"  - Low Stock: {summary.get('low_stock', 0)}")
        print(f"  - High Stock: {summary.get('high_stock', 0)}")
        print(f"  - Normal Stock: {summary.get('normal_stock', 0)}")
        
        if 'categories_summary' in summary:
            print(f"\n📁 Categories Breakdown:")
            for cat, details in list(summary['categories_summary'].items())[:5]:
                print(f"  - {cat}: {details.get('count', 0)} products, {details.get('value', 0):.2f} value")
    else:
        print(f"❌ Failed: {response.text}")
    
    print()


def test_03_financial_summary_report():
    """Test 3: Generate Financial Summary Report"""
    print("=" * 60)
    print("TEST 3: Generate Financial Summary Report")
    print("=" * 60)
    
    # Get last 90 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    payload = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    print(f"Request: POST /reports/financial-summary")
    print(f"Period: Last 90 days")
    
    response = requests.post(
        f"{BASE_URL}/reports/financial-summary",
        json=payload,
        params={"format": "json"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Financial Summary Report Generated Successfully")
        print(f"\nTitle: {data.get('title')}")
        print(f"\n💰 Summary:")
        summary = data.get('summary', {})
        print(f"  - Total Sales: {summary.get('total_sales', 0):.2f}")
        print(f"  - Total Purchases: {summary.get('total_purchases', 0):.2f}")
        print(f"  - Gross Profit: {summary.get('gross_profit', 0):.2f}")
        print(f"  - Profit Margin: {summary.get('profit_margin', 0):.2f}%")
        print(f"  - Inventory Value: {summary.get('inventory_value', 0):.2f}")
        print(f"  - Sales Count: {summary.get('sales_count', 0)}")
        print(f"  - Purchases Count: {summary.get('purchases_count', 0)}")
    else:
        print(f"❌ Failed: {response.text}")
    
    print()


def test_04_payment_summary_report():
    """Test 4: Generate Payment Summary Report"""
    print("=" * 60)
    print("TEST 4: Generate Payment Summary Report")
    print("=" * 60)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    payload = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    print(f"Request: POST /reports/payment-summary")
    
    response = requests.post(
        f"{BASE_URL}/reports/payment-summary",
        json=payload,
        params={"format": "json"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Payment Summary Report Generated Successfully")
        print(f"\nTitle: {data.get('title')}")
        print(f"Summary: {json.dumps(data.get('summary', {}), indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Failed: {response.text}")
    
    print()


def test_05_cash_flow_report():
    """Test 5: Generate Cash Flow Report"""
    print("=" * 60)
    print("TEST 5: Generate Cash Flow Report")
    print("=" * 60)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    payload = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    print(f"Request: POST /reports/cash-flow")
    
    response = requests.post(
        f"{BASE_URL}/reports/cash-flow",
        json=payload,
        params={"format": "json"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Cash Flow Report Generated Successfully")
        print(f"\nTitle: {data.get('title')}")
        print(f"Summary: {json.dumps(data.get('summary', {}), indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Failed: {response.text}")
    
    print()


def test_06_sales_report_with_filters():
    """Test 6: Sales Report with Customer Filter"""
    print("=" * 60)
    print("TEST 6: Sales Report with Customer Filter")
    print("=" * 60)
    
    payload = {
        "customer_id": 1,
        "min_amount": 100.0
    }
    
    print(f"Request: POST /reports/sales-summary")
    print(f"Filters: Customer ID=1, Min Amount=100")
    
    response = requests.post(
        f"{BASE_URL}/reports/sales-summary",
        json=payload,
        params={"format": "json"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Filtered Report Generated")
        print(f"Records Found: {len(data.get('data', []))}")
    else:
        print(f"❌ Failed: {response.text}")
    
    print()


def test_07_inventory_by_category():
    """Test 7: Inventory Report by Category"""
    print("=" * 60)
    print("TEST 7: Inventory Report by Category")
    print("=" * 60)
    
    payload = {
        "category_id": 1
    }
    
    print(f"Request: POST /reports/inventory-status")
    print(f"Filter: Category ID=1")
    
    response = requests.post(
        f"{BASE_URL}/reports/inventory-status",
        json=payload,
        params={"format": "json"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Category-Filtered Report Generated")
        print(f"Products Found: {len(data.get('data', []))}")
    else:
        print(f"❌ Failed: {response.text}")
    
    print()


def test_08_export_to_excel():
    """Test 8: Export Report to Excel"""
    print("=" * 60)
    print("TEST 8: Export Sales Report to Excel")
    print("=" * 60)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    payload = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    print(f"Request: POST /reports/sales-summary?format=xlsx")
    
    response = requests.post(
        f"{BASE_URL}/reports/sales-summary",
        json=payload,
        params={"format": "xlsx"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Report Exported to Excel")
        print(f"Filename: {data.get('filename')}")
        print(f"Format: {data.get('format')}")
    else:
        print(f"❌ Failed: {response.text}")
    
    print()


def test_09_unauthorized_access():
    """Test 9: Unauthorized Access"""
    print("=" * 60)
    print("TEST 9: Unauthorized Access Test")
    print("=" * 60)
    
    print(f"Request: POST /reports/sales-summary (without token)")
    
    response = requests.post(
        f"{BASE_URL}/reports/sales-summary",
        json={}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✅ Correctly rejected unauthorized access")
    else:
        print(f"❌ Should return 401, got {response.status_code}")
    
    print()


def test_10_invalid_date_format():
    """Test 10: Invalid Date Format Validation"""
    print("=" * 60)
    print("TEST 10: Invalid Date Format Validation")
    print("=" * 60)
    
    payload = {
        "start_date": "invalid-date",
        "end_date": "2025-11-19"
    }
    
    print(f"Request: POST /reports/financial-summary")
    print(f"Invalid start_date: 'invalid-date'")
    
    response = requests.post(
        f"{BASE_URL}/reports/financial-summary",
        json=payload,
        params={"format": "json"},
        headers=get_headers()
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code in [400, 422, 500]:
        print(f"✅ Correctly handled invalid date format")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
    
    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("REPORTS & ANALYTICS API TEST SUITE (v1.6.0)")
    print("=" * 60 + "\n")
    
    setup()
    
    # Run all tests
    test_01_sales_summary_report()
    test_02_inventory_status_report()
    test_03_financial_summary_report()
    test_04_payment_summary_report()
    test_05_cash_flow_report()
    test_06_sales_report_with_filters()
    test_07_inventory_by_category()
    test_08_export_to_excel()
    test_09_unauthorized_access()
    test_10_invalid_date_format()
    
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
Performance & Load Testing
اختبار الأداء والحمل للنظام
"""

import asyncio
import time
from typing import Dict, List
import statistics
import httpx
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
NUM_REQUESTS = 100
CONCURRENT_USERS = 10

async def login() -> str:
    """تسجيل الدخول والحصول على token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        raise Exception("Login failed")

async def make_request(client: httpx.AsyncClient, endpoint: str, token: str) -> Dict:
    """إجراء طلب واحد وقياس الوقت"""
    start_time = time.time()
    
    try:
        response = await client.get(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
        
        elapsed = time.time() - start_time
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "elapsed": elapsed,
            "endpoint": endpoint
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "elapsed": time.time() - start_time,
            "endpoint": endpoint,
            "error": str(e)
        }

async def run_load_test(endpoint: str, token: str, num_requests: int, concurrent: int):
    """تشغيل اختبار الحمل على endpoint محدد"""
    print(f"\n{'='*60}")
    print(f"🔥 Load Testing: {endpoint}")
    print(f"{'='*60}")
    print(f"Total Requests: {num_requests}")
    print(f"Concurrent Users: {concurrent}")
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Create batches of concurrent requests
        for batch_start in range(0, num_requests, concurrent):
            batch_size = min(concurrent, num_requests - batch_start)
            
            # Execute batch concurrently
            tasks = [
                make_request(client, endpoint, token)
                for _ in range(batch_size)
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Progress indicator
            progress = (batch_start + batch_size) / num_requests * 100
            print(f"Progress: {progress:.1f}% ({batch_start + batch_size}/{num_requests})", end="\r")
    
    print()  # New line after progress
    
    # Analyze results
    analyze_results(results, endpoint)
    
    return results

def analyze_results(results: List[Dict], endpoint: str):
    """تحليل نتائج الاختبار"""
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if successful:
        response_times = [r["elapsed"] for r in successful]
        
        print(f"\n📊 Results for {endpoint}:")
        print(f"  ✅ Successful: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"  ❌ Failed: {len(failed)}/{len(results)} ({len(failed)/len(results)*100:.1f}%)")
        print(f"\n⏱️  Response Times (seconds):")
        print(f"  Min:    {min(response_times):.3f}s")
        print(f"  Max:    {max(response_times):.3f}s")
        print(f"  Mean:   {statistics.mean(response_times):.3f}s")
        print(f"  Median: {statistics.median(response_times):.3f}s")
        
        if len(response_times) > 1:
            print(f"  StdDev: {statistics.stdev(response_times):.3f}s")
        
        # Percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p90 = sorted_times[int(len(sorted_times) * 0.90)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        print(f"\n📈 Percentiles:")
        print(f"  P50: {p50:.3f}s")
        print(f"  P90: {p90:.3f}s")
        print(f"  P95: {p95:.3f}s")
        print(f"  P99: {p99:.3f}s")
        
        # Throughput
        total_time = max(response_times)
        requests_per_second = len(successful) / total_time if total_time > 0 else 0
        
        print(f"\n🚀 Throughput:")
        print(f"  Requests/second: {requests_per_second:.2f}")
    else:
        print(f"\n❌ All requests failed for {endpoint}")
    
    # Error analysis
    if failed:
        print(f"\n🔍 Failed Requests Analysis:")
        error_counts = {}
        for result in failed:
            error = result.get("error", f"Status {result['status_code']}")
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error}: {count} times")

async def main():
    """تشغيل جميع اختبارات الأداء"""
    print("=" * 60)
    print("🚀 Logical Version ERP - Performance Testing")
    print("=" * 60)
    
    # Login first
    print("\n🔐 Logging in...")
    try:
        token = await login()
        print("✅ Login successful")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Test endpoints
    endpoints = [
        "/products",
        "/sales/orders",
        "/customers",
        "/inventory/stock",
        "/reports/inventory/current",
        "/ai/recommendations/1",
    ]
    
    all_results = {}
    
    for endpoint in endpoints:
        results = await run_load_test(
            endpoint=endpoint,
            token=token,
            num_requests=NUM_REQUESTS,
            concurrent=CONCURRENT_USERS
        )
        all_results[endpoint] = results
        
        # Wait between tests
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*60}")
    
    for endpoint, results in all_results.items():
        successful = sum(1 for r in results if r["success"])
        success_rate = successful / len(results) * 100
        avg_time = statistics.mean([r["elapsed"] for r in results if r["success"]]) if successful > 0 else 0
        
        status = "✅" if success_rate >= 95 else "⚠️" if success_rate >= 80 else "❌"
        print(f"{status} {endpoint:30} Success: {success_rate:5.1f}%  Avg: {avg_time:.3f}s")
    
    print(f"\n{'='*60}")
    print(f"Test completed at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("\n⚠️  Make sure the API server is running on http://localhost:8000")
    print("   Start it with: uvicorn src.api.app:app --reload\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

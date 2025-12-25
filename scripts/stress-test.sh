#!/bin/bash
# Stress Test Script for ERP API
# Usage: ./scripts/stress-test.sh [endpoint] [users] [duration]

set -e

ENDPOINT=${1:-"http://localhost:8000/api/v1/health"}
USERS=${2:-100}
DURATION=${3:-60}

echo "🔥 Starting Stress Test..."
echo "  Endpoint: $ENDPOINT"
echo "  Users: $USERS"
echo "  Duration: ${DURATION}s"
echo ""

# Check if Locust is installed
if ! command -v locust &> /dev/null; then
    echo "📦 Installing Locust..."
    pip install locust
fi

# Create Locust test file if it doesn't exist
if [ ! -f tests/locustfile.py ]; then
    echo "📝 Creating Locust test file..."
    mkdir -p tests
    cat > tests/locustfile.py << 'EOF'
from locust import HttpUser, task, between
import random

class ERPUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(3)
    def get_products(self):
        self.client.get("/api/v1/products")
    
    @task(2)
    def get_sales(self):
        self.client.get("/api/v1/sales")
    
    @task(1)
    def create_sale(self):
        self.client.post("/api/v1/sales", json={
            "customer_id": random.randint(1, 10),
            "items": [{
                "product_id": random.randint(1, 100),
                "quantity": random.randint(1, 5),
                "price": random.uniform(10, 1000)
            }]
        })
    
    @task(1)
    def get_analytics(self):
        self.client.get("/api/v1/analytics/sales-trends")
EOF
fi

# Run Locust
echo "🚀 Running Locust..."
locust -f tests/locustfile.py \
    --host="$ENDPOINT" \
    --users="$USERS" \
    --spawn-rate=10 \
    --run-time="${DURATION}s" \
    --headless \
    --html=reports/stress-test-report.html

echo ""
echo "✅ Stress test complete!"
echo "📊 Report saved to: reports/stress-test-report.html"


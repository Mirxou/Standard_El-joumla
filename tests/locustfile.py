"""
Locust Stress Test File for ERP API
Usage: locust -f tests/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random
import json


class ERPUser(HttpUser):
    """Simulated ERP user for stress testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login and get authentication token"""
        try:
            response = self.client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "admin"
            })
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.client.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
        except Exception as e:
            print(f"Login failed: {e}")
    
    @task(5)
    def get_products(self):
        """Get products list"""
        self.client.get("/api/v1/products")
    
    @task(3)
    def get_sales(self):
        """Get sales list"""
        self.client.get("/api/v1/sales")
    
    @task(2)
    def get_customers(self):
        """Get customers list"""
        self.client.get("/api/v1/customers")
    
    @task(1)
    def create_sale(self):
        """Create a new sale"""
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
        """Get analytics data"""
        self.client.get("/api/v1/analytics/sales-trends")
    
    @task(1)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/health")


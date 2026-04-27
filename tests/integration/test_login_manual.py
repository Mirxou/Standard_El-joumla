import requests
import json

BASE_URL = "http://127.0.0.1:8001/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"

def test_login():
    print(f"Testing Login URL: {LOGIN_URL}")
    
    # Default admin credentials (usually)
    payload = {
        "username": "admin",
        "password": "password",  # Try common default or 'admin' or '123456' which user typed
        "company_id": "1"        # Often required
    }
    
    try:
        # Try the reset password '123'
        payload['password'] = "123"
        print(f"Attempt 1 (123): Sending POST...")
        response = requests.post(LOGIN_URL, json=payload, headers={"Content-Type": "application/json"})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        # If that fails, try 'admin'
        if response.status_code != 200:
            payload['password'] = "admin"
            print(f"Attempt 2 (admin): Sending POST...")
            response = requests.post(LOGIN_URL, json=payload, headers={"Content-Type": "application/json"})
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_login()




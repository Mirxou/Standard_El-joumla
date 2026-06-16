import requests

BASE_URL = "http://127.0.0.1:8001/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"


def test_login():
    # print(f"Testing Login URL: {LOGIN_URL}")
    pass

    # Default admin credentials (usually)
    payload = {
        "username": "admin",
        "password": "password",  # Try common default or 'admin' or '123456' which user typed
        "company_id": "1",  # Often required
    }

    try:
        # Try the reset password '123'
        payload["password"] = "123"
        # print("Attempt 1 (123): Sending POST...")
        response = requests.post(LOGIN_URL, json=payload, headers={"Content-Type": "application/json"})
        # print(f"Status: {response.status_code}")
        # print(f"Response: {response.text}")

        # If that fails, try 'admin'
        if response.status_code != 200:
            payload["password"] = "admin"
            # print("Attempt 2 (admin): Sending POST...")
            response = requests.post(LOGIN_URL, json=payload, headers={"Content-Type": "application/json"})
            # print(f"Status: {response.status_code}")
            # print(f"Response: {response.text}")

    except Exception as e:  # noqa: F841
        # print(f"Connection Error: {e}")
        pass


if __name__ == "__main__":
    test_login()

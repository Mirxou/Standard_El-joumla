from fastapi.testclient import TestClient
from src.api.app import app, get_services
import uuid


def ensure_admin(db, us):
    try:
        us.user_manager.create_default_admin()
    except Exception:
        pass
    user = us.user_manager.get_user_by_username("admin")
    if not user:
        from src.models.user import User, UserRole
        admin = User(username="admin", email="admin@test.local", role=UserRole.ADMIN.value, full_name="Admin User")
        us.user_manager.create_user(admin, "admin123")
    return us.user_manager.get_user_by_username("admin")


def get_admin_token(client: TestClient):
    r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_pricing_invalid_price_type_and_missing_group():
    db, us, *_ = get_services()
    ensure_admin(db, us)
    client = TestClient(app)
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    unique = uuid.uuid4().hex[:8]

    # Create product
    prod_payload = {
        "name": f"Price Product {unique}",
        "unit": "قطعة",
        "cost_price": 10.0,
        "selling_price": 15.0,
        "barcode": f"PRD-NEG-{unique}"
    }
    r = client.post("/products", json=prod_payload, headers=headers)
    assert r.status_code == 201
    product_id = r.json()["id"]

    # invalid price_type
    bad = {"product_id": product_id, "price_type": "vip", "min_qty": 1, "price": 14.0}
    r1 = client.post("/prices", json=bad, headers=headers)
    assert r1.status_code == 422

    # missing customer_group for customer_group type
    bad2 = {"product_id": product_id, "price_type": "customer_group", "min_qty": 1, "price": 14.0}
    r2 = client.post("/prices", json=bad2, headers=headers)
    assert r2.status_code == 400

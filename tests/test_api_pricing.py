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


def test_create_and_list_price_tiers_for_product_and_variant():
    db, us, *_ = get_services()
    ensure_admin(db, us)

    client = TestClient(app)
    token = get_admin_token(client)

    unique = uuid.uuid4().hex[:8]

    # Create product
    prod_payload = {
        "name": f"Price Product {unique}",
        "unit": "قطعة",
        "cost_price": 20.0,
        "selling_price": 30.0,
        "barcode": f"PRD-PRICE-{unique}"
    }
    r = client.post("/products", json=prod_payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    product_id = r.json()["id"]

    # Create price tiers for product
    p1 = {
        "product_id": product_id,
        "price_type": "retail",
        "min_qty": 1,
        "price": 30.0
    }
    p2 = {
        "product_id": product_id,
        "price_type": "retail",
        "min_qty": 10,
        "price": 27.5
    }
    r1 = client.post("/prices", json=p1, headers={"Authorization": f"Bearer {token}"})
    r2 = client.post("/prices", json=p2, headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 201 and r2.status_code == 201

    # Create a variant
    var_payload = {
        "sku": f"SKU-{unique}",
        "attributes": {"size": "S"},
        "selling_price": 28.0
    }
    r3 = client.post(f"/products/{product_id}/variants", json=var_payload, headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 201, r3.text
    variant_id = r3.json()["id"]

    # Variant price
    pv = {
        "variant_id": variant_id,
        "price_type": "retail",
        "min_qty": 5,
        "price": 26.0
    }
    r4 = client.post("/prices", json=pv, headers={"Authorization": f"Bearer {token}"})
    assert r4.status_code == 201, r4.text

    # List product prices
    rp = client.get(f"/products/{product_id}/prices", headers={"Authorization": f"Bearer {token}"})
    assert rp.status_code == 200
    prices = rp.json()
    assert len(prices) >= 2
    assert prices[0]["min_qty"] <= prices[-1]["min_qty"]

    # List variant prices
    rv = client.get(f"/variants/{variant_id}/prices", headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200
    vprices = rv.json()
    assert any(p["min_qty"] == 5 and p["price"] == 26.0 for p in vprices)

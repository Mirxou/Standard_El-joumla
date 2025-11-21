from fastapi.testclient import TestClient
import uuid
from src.api.app import app, get_services

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


def test_create_product_and_variant_and_fetch_detail():
    db, us, *_ = get_services()
    ensure_admin(db, us)

    client = TestClient(app)
    token = get_admin_token(client)

    # Create product
    unique = uuid.uuid4().hex[:8]
    prod_payload = {
        "name": "قميص قطن",
        "name_en": "Cotton Shirt",
        "unit": "قطعة",
        "cost_price": 50.0,
        "selling_price": 80.0,
        "min_stock": 5,
        "current_stock": 10,
        "barcode": f"PRD-001-BASE-{unique}"
    }
    r = client.post("/products", json=prod_payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    product_id = r.json()["id"]
    assert product_id > 0

    # Create variant
    var_payload = {
        "sku": f"PRD-001-L-RED-{unique}",
        "attributes": {"size": "L", "color": "Red"},
        "barcode": f"PRD-001-L-RED-BC-{unique}",
        "cost_price": 55.0,
        "selling_price": 85.0,
        "current_stock": 3
    }
    r2 = client.post(f"/products/{product_id}/variants", json=var_payload, headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 201, r2.text
    variant_id = r2.json()["id"]
    assert variant_id > 0

    # Fetch detail
    r3 = client.get(f"/products/{product_id}", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200, r3.text
    data = r3.json()
    assert data["id"] == product_id
    assert isinstance(data.get("variants"), list)
    assert any(v["id"] == variant_id for v in data["variants"])
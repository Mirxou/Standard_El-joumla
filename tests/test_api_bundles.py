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


def test_create_bundle_add_items_and_fetch_detail():
    db, us, *_ = get_services()
    ensure_admin(db, us)

    client = TestClient(app)
    token = get_admin_token(client)

    unique = uuid.uuid4().hex[:8]

    # Create parent product for bundle
    prod_bundle = {
        "name": f"Bundle Parent {unique}",
        "unit": "قطعة",
        "cost_price": 0.0,
        "selling_price": 0.0,
        "min_stock": 0,
        "current_stock": 0,
        "barcode": f"PRD-BUNDLE-{unique}"
    }
    r = client.post("/products", json=prod_bundle, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    bundle_product_id = r.json()["id"]

    # Create another product to act as bundle item
    prod_item = {
        "name": f"Item Product {unique}",
        "unit": "قطعة",
        "cost_price": 5.0,
        "selling_price": 10.0,
        "barcode": f"PRD-ITEM-{unique}"
    }
    r2 = client.post("/products", json=prod_item, headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 201, r2.text
    item_product_id = r2.json()["id"]

    # Create a variant for the item product
    var_payload = {
        "sku": f"SKU-{unique}",
        "attributes": {"size": "M", "color": "Blue"},
        "barcode": f"VAR-{unique}",
        "selling_price": 11.0,
        "current_stock": 2
    }
    r3 = client.post(f"/products/{item_product_id}/variants", json=var_payload, headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 201, r3.text
    variant_id = r3.json()["id"]

    # Create bundle
    b_payload = {"name": f"Bundle {unique}", "description": "Test bundle", "is_active": True}
    r4 = client.post(f"/products/{bundle_product_id}/bundles", json=b_payload, headers={"Authorization": f"Bearer {token}"})
    assert r4.status_code == 201, r4.text
    bundle_id = r4.json()["id"]

    # Add product item
    r5 = client.post(f"/bundles/{bundle_id}/items", json={
        "item_type": "product",
        "item_product_id": item_product_id,
        "quantity": 2
    }, headers={"Authorization": f"Bearer {token}"})
    assert r5.status_code == 201, r5.text

    # Add variant item
    r6 = client.post(f"/bundles/{bundle_id}/items", json={
        "item_type": "variant",
        "item_variant_id": variant_id,
        "quantity": 3
    }, headers={"Authorization": f"Bearer {token}"})
    assert r6.status_code == 201, r6.text

    # Get bundle detail
    r7 = client.get(f"/bundles/{bundle_id}", headers={"Authorization": f"Bearer {token}"})
    assert r7.status_code == 200, r7.text
    data = r7.json()
    assert data["id"] == bundle_id
    assert len(data["items"]) == 2
    assert any(i["item_product_id"] == item_product_id and i["quantity"] == 2 for i in data["items"])
    assert any(i["item_variant_id"] == variant_id and i["quantity"] == 3 for i in data["items"])

    # List bundles
    r8 = client.get("/bundles?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert r8.status_code == 200, r8.text
    items = r8.json()["items"]
    assert any(b["id"] == bundle_id for b in items)

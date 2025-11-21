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


def test_add_list_delete_tags_and_filter_products():
    db, us, *_ = get_services()
    ensure_admin(db, us)

    client = TestClient(app)
    token = get_admin_token(client)

    unique = uuid.uuid4().hex[:8]
    prod_payload = {
        "name": f"Product {unique}",
        "name_en": f"Product {unique}",
        "unit": "قطعة",
        "cost_price": 10.0,
        "selling_price": 20.0,
        "min_stock": 0,
        "current_stock": 0,
        "barcode": f"PRD-TAG-{unique}"
    }
    r = client.post("/products", json=prod_payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    product_id = r.json()["id"]

    # add tag
    tag_value = f"tag-{unique}"
    r2 = client.post(f"/products/{product_id}/tags", json={"tag": tag_value}, headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 201, r2.text

    # list tags
    r3 = client.get(f"/products/{product_id}/tags", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200, r3.text
    tags = r3.json()["tags"]
    assert tag_value in tags

    # filter products by tag
    r4 = client.get(f"/products?tag={tag_value}", headers={"Authorization": f"Bearer {token}"})
    assert r4.status_code == 200, r4.text
    items = r4.json()["items"]
    assert any(p["id"] == product_id for p in items)

    # delete tag
    r5 = client.delete(f"/products/{product_id}/tags/{tag_value}", headers={"Authorization": f"Bearer {token}"})
    assert r5.status_code == 204, r5.text

    # confirm removed
    r6 = client.get(f"/products/{product_id}/tags", headers={"Authorization": f"Bearer {token}"})
    assert tag_value not in r6.json()["tags"]

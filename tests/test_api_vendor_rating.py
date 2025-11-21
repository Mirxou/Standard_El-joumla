from fastapi.testclient import TestClient
from src.api.app import app, get_services

# We rely on default admin creation if exists; otherwise create manually.

def ensure_admin(db, us):
    # Attempt to create default admin if not present
    try:
        created = us.user_manager.create_default_admin()
    except Exception:
        created = False
    user = us.user_manager.get_user_by_username("admin")
    if not user:
        # Fallback: create minimal admin user
        from src.models.user import User, UserRole
        admin = User(username="admin", email="admin@test.local", role=UserRole.ADMIN.value, full_name="Admin User")
        us.user_manager.create_user(admin, "admin123")
    return us.user_manager.get_user_by_username("admin")


def get_admin_token(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_create_and_fetch_supplier_rating():
    db, us, vs, *rest = get_services()
    admin_user = ensure_admin(db, us)

    # Seed a supplier if not exists
    with db.get_cursor() as cur:
        cur.execute("SELECT id FROM suppliers LIMIT 1")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO suppliers (name) VALUES ('API Supplier')")
            cur.connection.commit()
            supplier_id = cur.lastrowid
        else:
            supplier_id = row[0]

    client = TestClient(app)
    token = get_admin_token(client)

    # Create evaluation
    payload = {
        "quality_score": 4.8,
        "delivery_score": 4.6,
        "pricing_score": 4.1,
        "communication_score": 4.7,
        "reliability_score": 4.9
    }
    r = client.post(f"/suppliers/{supplier_id}/evaluations", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    eval_id = r.json()["id"]
    assert eval_id > 0

    # Fetch rating
    r2 = client.get(f"/suppliers/{supplier_id}/rating", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["supplier_id"] == supplier_id
    assert 0 <= data["overall_score"] <= 5
    assert data["grade"] in {"A+","A","B+","B","C","D","F"}


def test_rbac_blocks_non_admin():
    # Create a non-admin user and attempt evaluation creation
    db, us, vs, *rest = get_services()
    from src.models.user import User, UserRole
    normal = us.user_manager.get_user_by_username("regular1")
    if not normal:
        u = User(username="regular1", email="regular1@test.local", role=UserRole.CASHIER.value, full_name="Regular User")
        us.user_manager.create_user(u, "userpass1")

    client = TestClient(app)
    # Login as regular user
    resp = client.post("/auth/login", json={"username": "regular1", "password": "userpass1"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]

    with db.get_cursor() as cur:
        cur.execute("SELECT id FROM suppliers LIMIT 1")
        row = cur.fetchone()
        supplier_id = row[0] if row else 1

    payload = {
        "quality_score": 4.0,
        "delivery_score": 4.0,
        "pricing_score": 4.0,
        "communication_score": 4.0,
        "reliability_score": 4.0
    }
    r = client.post(f"/suppliers/{supplier_id}/evaluations", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403

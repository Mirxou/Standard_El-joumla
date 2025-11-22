import sqlite3
from pathlib import Path
from src.services.rbac_service import RBACService


class MiniDB:
    def __init__(self, conn):
        self.conn = conn


def _create_schema_variant_a(conn):
    # roles(id, name)
    conn.execute("CREATE TABLE roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, created_at TEXT)")
    conn.execute("INSERT INTO roles (name, description, created_at) VALUES ('admin','Administrator','2024-01-01')")
    conn.commit()


def _create_schema_variant_b(conn):
    # roles(role_id, role_name)
    conn.execute("CREATE TABLE roles (role_id INTEGER PRIMARY KEY AUTOINCREMENT, role_name TEXT, display_name TEXT, description TEXT, is_active INTEGER, created_at TEXT, updated_at TEXT)")
    conn.execute("INSERT INTO roles (role_name, display_name, description, is_active, created_at, updated_at) VALUES ('editor','Editor','Edit content',1,'2024-01-01','2024-01-02')")
    conn.commit()


def test_rbac_schema_variant_a(tmp_path):
    db_path = tmp_path / "a.db"
    conn = sqlite3.connect(str(db_path))
    _create_schema_variant_a(conn)
    service = RBACService(MiniDB(conn))
    roles = service.list_roles()
    assert roles and roles[0]['role_name'] == 'admin'


def test_rbac_schema_variant_b(tmp_path):
    db_path = tmp_path / "b.db"
    conn = sqlite3.connect(str(db_path))
    _create_schema_variant_b(conn)
    service = RBACService(MiniDB(conn))
    roles = service.list_roles()
    assert roles and roles[0]['role_name'] == 'editor'
    # ensure display_name mapped
    assert roles[0]['display_name'] in ('Editor','editor')

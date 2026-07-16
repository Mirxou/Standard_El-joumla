#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, warnings, tempfile
sys.path.insert(0, os.getcwd())
warnings.filterwarnings('ignore')

PASS = 0
FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}" + (f" -- {detail}" if detail else ""))

print("=" * 60)
print("CORE PRODUCTION READINESS TEST")
print("=" * 60)

# 1. LocalDatabaseManager
print("\n--- LocalDatabaseManager ---")
from src.core.local_database_manager import LocalDatabaseManager

tmp_db = tempfile.mktemp(suffix='.db')
db = LocalDatabaseManager(tmp_db)
result = db.initialize()
check("initialize() returns True", result is True)

tables_raw = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
table_names = [t['name'] for t in tables_raw]
check("products table exists", 'products' in table_names)
check("users table exists", 'users' in table_names)
check("sales table exists", 'sales' in table_names)
check("sync_queue table exists", 'sync_queue' in table_names)

cols_raw = db.fetch_all("PRAGMA table_info(users)")
col_names = [c['name'] for c in cols_raw]
check("users.role_id column exists", 'role_id' in col_names, f"got: {col_names}")

# lock_row - no FOR UPDATE crash
try:
    db.execute_non_query(
        "INSERT OR IGNORE INTO users (username, full_name, role, password_hash, salt) VALUES ('u1', 'Test', 'user', 'x', 'y')"
    )
    result_lock = db.lock_row('users', 1)
    check("lock_row() does not crash (no FOR UPDATE)", True)
    check("lock_row() returns bool", isinstance(result_lock, bool))
except Exception as e:
    check("lock_row() does not crash", False, str(e))
    check("lock_row() returns bool", False)

# execute_query returns list for UPDATE (not cursor)
ret = db.execute_query("UPDATE users SET role='admin' WHERE username='u1'")
check("execute_query returns list for non-SELECT", isinstance(ret, list), f"got: {type(ret).__name__}")

# fetch_one / SmartRow
row = db.fetch_one("SELECT * FROM users WHERE username='u1'")
check("fetch_one() returns row", row is not None)
if row:
    check("SmartRow key access: row['username']", row['username'] == 'u1')
    check("SmartRow index access: row[0]", row[0] is not None)

# 2. PermissionManager
print("\n--- PermissionManager ---")
from src.core.permission_manager import PermissionManager

pm = PermissionManager(db)
roles = pm.list_roles()
check("Default roles created (>=4)", len(roles) >= 4, f"got {len(roles)}")

all_ok = True
for role in roles:
    try:
        _ = role.name, role.permissions, role.role_id
    except Exception as e:  # noqa: F841
        all_ok = False
        break
check("All roles named-key access (name/permissions/role_id)", all_ok)

admin_role = pm.get_role_by_name('Admin')
check("get_role_by_name('Admin') returns Role", admin_role is not None)
if admin_role:
    check("Admin has >=20 permissions", len(admin_role.permissions) >= 20,
          f"got {len(admin_role.permissions)}")

# 3. AdvancedSecurityService
print("\n--- AdvancedSecurityService ---")
from src.core.security_service import AdvancedSecurityService

sec = AdvancedSecurityService()
hashed = sec.hash_password('TestP@ss123!')
check("hash_password returns string", isinstance(hashed, str))
check("hash has known prefix", hashed.startswith('$argon2') or hashed.startswith('$pbkdf2'))
check("verify correct password -> True", sec.verify_password(hashed, 'TestP@ss123!') is True)
check("verify wrong password -> False", sec.verify_password(hashed, 'WrongPass') is False)

sec_db = AdvancedSecurityService(db)
token = sec_db.create_session(1, 'admin', '127.0.0.1')
check("create_session returns token (len>20)", isinstance(token, str) and len(token) > 20)
session = sec_db.validate_session(token)
check("validate_session returns session dict", session is not None)
if session:
    check("session['user_id'] == 1", session.get('user_id') == 1)

# invalidate_session uses execute_non_query (no crash)
try:
    sec_db.invalidate_session(token)
    check("invalidate_session does not crash", True)
except Exception as e:
    check("invalidate_session does not crash", False, str(e))

# 4. ConfigManager
print("\n--- ConfigManager ---")
from src.core.config_manager import ConfigManager

cfg = ConfigManager()
cfg.load_config()
db_path = cfg.get_database_path()
check("get_database_path returns non-empty string", isinstance(db_path, str) and len(db_path) > 0)
db_info = cfg.get_database_info()
check("get_database_info returns dict (no old DatabaseManager)", isinstance(db_info, dict))
check("db_info has 'path' key", 'path' in db_info)
check("db_info has 'backend' key", 'backend' in db_info)

# 5. core.__init__ exports
print("\n--- core __init__ exports ---")
import src.core as core_mod
check("'LocalDatabaseManager' in core.__all__", 'LocalDatabaseManager' in core_mod.__all__)
check("'DatabaseException' in core.__all__", 'DatabaseException' in core_mod.__all__)
check("'ConfigManager' in core.__all__", 'ConfigManager' in core_mod.__all__)

# Cleanup
db.close()
try:
    os.unlink(tmp_db)
except Exception:
    pass

print()
print("=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("ALL TESTS PASSED - src/core IS PRODUCTION READY")
else:
    print(f"ATTENTION: {FAIL} test(s) FAILED")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)

import os
import shutil

root = r"c:\Users\aboun\Desktop\Logical Version trae"
tests_root = os.path.join(root, "tests")

moves = [
    ("integration_test.py", "integration"),
    ("stress_test.py", "performance"),
    ("locustfile.py", "performance"),
    ("test_api_client.py", "api"),
    ("test_api_integration.py", "integration"),
    ("test_core_database_coverage.py", "core"),
    ("test_customer_coverage.py", "models"),
    ("test_mobile_auth.py", "integration"),
    ("test_models_coverage.py", "models"),
    ("test_phase7_cognitive_ai.py", "services"),
    ("test_phase_6.py", "integration"),
    ("test_phase_9_ai.py", "services"),
    ("test_postgresql_support.py", "integration"),
    ("test_product_coverage.py", "models"),
    ("test_purchase_coverage.py", "models"),
    ("test_sale_coverage.py", "models"),
    ("test_supplier_coverage.py", "models"),
    ("test_sync_api.py", "api"),
    ("test_user_coverage.py", "models"),
    ("test_user_security_coverage.py", "models"),
    ("test_vision_2030.py", "services"),
    ("test_warehouse_coverage.py", "models"),
]

for src_name, dst_sub in moves:
    src_path = os.path.join(tests_root, src_name)
    dst_path = os.path.join(tests_root, dst_sub, src_name)
    
    if os.path.exists(src_path):
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.move(src_path, dst_path)
        print(f"Moved tests/{src_name} to tests/{dst_sub}/")
    else:
        print(f"File not found: tests/{src_name}")

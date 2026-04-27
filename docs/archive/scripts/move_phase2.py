import os
import shutil

root = r"c:\Users\aboun\Desktop\Logical Version trae"
tests_root = os.path.join(root, "tests")

moves = [
    ("test_ai_analytics_services.py", os.path.join("tests", "services")),
    ("test_inventory_supply_chain.py", os.path.join("tests", "integration")),
    ("test_login_manual.py", os.path.join("tests", "integration")),
    ("test_multi_agent_system.py", os.path.join("tests", "services")),
    ("test_phase6_integration.py", os.path.join("tests", "integration")),
    ("test_sale.py", os.path.join("tests", "integration", "test_sale_alternative.py")),
    ("test_save.py", os.path.join("tests", "unit")),
    ("test_unified_commerce_2030.py", os.path.join("tests", "integration")),
    ("test_warehouse_logistics.py", os.path.join("tests", "integration")),
    ("phase_9_validation.py", os.path.join("tests", "integration", "test_phase9_validation.py")),
    ("check_db.py", os.path.join("tests", "utils", "diagnostics")),
    ("check_logical.py", os.path.join("tests", "utils", "diagnostics")),
    ("check_model.py", os.path.join("tests", "utils", "diagnostics")),
    ("check_schema.py", os.path.join("tests", "utils", "diagnostics")),
    ("check_tables.py", os.path.join("tests", "utils", "diagnostics")),
    ("check_phase7_tables.py", os.path.join("tests", "utils", "diagnostics")),
]

for src_name, dst_rel in moves:
    src_path = os.path.join(root, src_name)
    dst_path = os.path.join(root, dst_rel)
    
    if os.path.exists(src_path):
        # Create dst directory if it doesn't exist
        if dst_rel.endswith('.py'):
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.move(src_path, dst_path)
            print(f"Moved {src_name} to {dst_rel}")
        else:
            os.makedirs(dst_path, exist_ok=True)
            shutil.move(src_path, os.path.join(dst_path, src_name))
            print(f"Moved {src_name} to {dst_rel}/")
    else:
        print(f"File not found: {src_name}")

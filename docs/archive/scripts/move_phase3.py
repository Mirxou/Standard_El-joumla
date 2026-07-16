import os
import shutil

root = r"c:\Users\aboun\Desktop\Logical Version trae"
scripts_dir = os.path.join(root, "scripts")

moves = [
    ("test_api.py", os.path.join("tests", "api")),
    ("test_dashboard_chart.py", os.path.join("tests", "ui")),
    ("test_docker.py", os.path.join("tests", "integration")),
    ("test_login.py", os.path.join("tests", "integration")),
    ("test_services.py", os.path.join("tests", "services")),
    ("test_sqlite_wal_performance.py", os.path.join("tests", "performance")),
    ("test_warehouse_migration.py", os.path.join("tests", "integration")),
    ("benchmark_app.py", os.path.join("tests", "performance")),
    ("validate_migrations.py", os.path.join("tests", "utils")),
    ("verify_safety_nets.py", os.path.join("tests", "utils")),
    ("monitor_test.py", os.path.join("tests", "utils")),
    ("run_all_tests.py", os.path.join("tests", "run_tests.py")),
    ("cleanup_test_logs.py", os.path.join("tests", "utils")),
    ("run-all-tests.sh", os.path.join("tests", "scripts")),
    ("test-api.sh", os.path.join("tests", "scripts")),
    ("test-docker.sh", os.path.join("tests", "scripts")),
    ("test-services.sh", os.path.join("tests", "scripts")),
    ("test-api-login.ps1", os.path.join("tests", "scripts")),
    ("stress-test.sh", os.path.join("tests", "scripts")),
]

for src_name, dst_rel in moves:
    src_path = os.path.join(scripts_dir, src_name)
    dst_path = os.path.join(root, dst_rel)
    
    if os.path.exists(src_path):
        if dst_rel.endswith('.py') or dst_rel.endswith('.sh') or dst_rel.endswith('.ps1'):
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.move(src_path, dst_path)
            print(f"Moved scripts/{src_name} to {dst_rel}")
        else:
            os.makedirs(dst_path, exist_ok=True)
            shutil.move(src_path, os.path.join(dst_path, src_name))
            print(f"Moved scripts/{src_name} to {dst_rel}/")
    else:
        print(f"File not found: scripts/{src_name}")

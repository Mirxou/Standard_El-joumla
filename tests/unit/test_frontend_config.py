import json
from pathlib import Path


def test_frontend_package_json_contains_next_and_build_scripts():
    root = Path(__file__).resolve().parents[2]
    package_path = root / "web" / "package.json"
    assert package_path.exists(), f"Missing {package_path}"
    with open(package_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    dependencies = data.get("dependencies", {})
    assert "next" in dependencies, "Dependency 'next' not found in frontend package.json"
    scripts = data.get("scripts", {})
    assert "dev" in scripts or "build" in scripts, "Frontend scripts do not include 'dev' or 'build'"

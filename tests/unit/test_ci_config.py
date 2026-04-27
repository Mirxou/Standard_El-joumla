def test_ci_yaml_exists_and_contains_ci_header():
    import os
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ci_path = os.path.join(root, ".github", "workflows", "ci.yml")
    assert os.path.exists(ci_path), f"CI config not found at {ci_path}"
    with open(ci_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert "name: CI - Continuous Integration" in content, "CI header not found in ci.yml"
    assert "jobs:" in content, "ci.yml missing 'jobs' section"




#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]  # repo root (tools/.. -> root)


def find_db_candidates():
    candidates = [
        ROOT / "data" / "logical_release.db",
        ROOT / "data" / "database.db",
        ROOT / "erp_system.db",
    ]
    return [str(p) for p in candidates if p.exists()]


def main():
    status = {
        "repositories": {
            "web": str(ROOT / "web"),
            "backend": str(ROOT),
        },
        "db_candidates": find_db_candidates(),
        "files_present": {
            "package_json": os.path.exists(str(ROOT / "web" / "package.json")),
            "requirements_txt": os.path.exists(str(ROOT / "requirements.txt")),
            "dockerfile": os.path.exists(str(ROOT / "Dockerfile")),
            ".github": os.path.isdir(str(ROOT / ".github")),
        },
        "ci_dirs": [str(ROOT / ".github" / "workflows")],
        "python_version": sys.version.split()[0],
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

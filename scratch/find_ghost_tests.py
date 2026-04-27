import os
import re
from pathlib import Path

def find_ghost_tests():
    tests_dir = Path("tests/unit")
    ghost_tests = []
    
    for test_file in tests_dir.glob("test_*.py"):
        content = test_file.read_text(encoding="utf-8")
        # Match "from src... import" OR "import src..."
        from_imports = re.findall(r"from (src\.[a-zA-Z0-9_\.]+) import", content)
        direct_imports = re.findall(r"import (src\.[a-zA-Z0-9_\.]+)", content)
        
        all_modules = set(from_imports + direct_imports)
        
        for module in all_modules:
            module_path = module.replace(".", "/") + ".py"
            if not os.path.exists(module_path):
                pkg_path = module.replace(".", "/") + "/__init__.py"
                if not os.path.exists(pkg_path):
                    ghost_tests.append((test_file, module))
                    break
    
    return ghost_tests

if __name__ == "__main__":
    ghosts = find_ghost_tests()
    print(f"Found {len(ghosts)} ghost tests:")
    for test_file, module in ghosts:
        print(f"- {test_file}: Missing {module}")

import os
import re
from pathlib import Path

tests_root = r"c:\Users\aboun\Desktop\Logical Version trae\tests"

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Standard replacement block
    # We find how many levels up to reach the root (which contains 'src' and 'requirements.txt')
    rel_depth = len(Path(file_path).relative_to(Path(tests_root).parent).parts) - 1
    parents_num = rel_depth
    
    replacement = f"""import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[{parents_num}])
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if str(Path(project_root) / "src") not in sys.path:
    sys.path.insert(0, str(Path(project_root) / "src"))"""

    # Look for common sys.path hacks
    # Pattern matches lines with sys.path.insert(0, ...) and potentially surrounding imports of sys, os, Path
    pattern = re.compile(r'(?:import sys\s+|import os\s+|from pathlib import Path\s+)*sys\.path\.insert\(0,.*?\)', re.DOTALL)
    
    new_content = pattern.sub(replacement, content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

count = 0
for root, dirs, files in os.walk(tests_root):
    for file in files:
        if file.endswith('.py') and file != 'conftest.py':
            if fix_file(os.path.join(root, file)):
                count += 1
                print(f"Fixed paths in {os.path.relpath(os.path.join(root, file), tests_root)}")

print(f"Total files fixed: {count}")

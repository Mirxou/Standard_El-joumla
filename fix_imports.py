import os
import re

workspace_dir = r"c:\Users\aboun\Desktop\Logical Version trae"
src_dir = os.path.join(workspace_dir, "src")
test_dir = os.path.join(workspace_dir, "tests")

modules = [
    'models', 'core', 'services', 'utils', 'ui', 
    'database', 'api', 'ai', 'security', 'repositories', 
    'experimental', 'config'
]

def fix_file(filepath):
    print(f"Processing {filepath}", flush=True)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    new_content = content

    # 1. Remove sys.path blocks (more robustly)
    # Remove single lines
    new_content = re.sub(r'^[ \t]*sys\.path\.(?:insert|append)\(.*$\n?', '', new_content, flags=re.MULTILINE)
    
    # Remove if blocks that are now empty or contain only other if blocks
    # Pattern: if ... not in sys.path:\s* (and nothing else for a while or just another if)
    # This is tricky with regex, so we'll do it line by line or with a multi-line regex
    new_content = re.sub(r'^[ \t]*if .*sys\.path:.*$\n(?:[ \t]*sys\.path\..*$\n?|[ \t]*\n)*', '', new_content, flags=re.MULTILINE)
    
    # Specific fix for the "double if" created in the previous run
    new_content = re.sub(r'^[ \t]*if .*sys\.path:.*$\n[ \t]*if .*sys\.path:.*$\n?', '', new_content, flags=re.MULTILINE)

    # 2. Standardize from X import ... to from src.X import ...
    for mod in modules:
        # Avoid double src.
        if mod.startswith('src.'): continue
        
        # from models import ... -> from src.models import ...
        new_content = re.sub(rf'^([ \t]*)from {mod}(\.|\s+import)', rf'\1from src.{mod}\2', new_content, flags=re.MULTILINE)
        # import models.product -> import src.models.product
        new_content = re.sub(rf'^([ \t]*)import {mod}(\.|\s+)', rf'\1import src.{mod}\2', new_content, flags=re.MULTILINE)

    if new_content != content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {filepath}")
        except Exception as e:
            print(f"Error writing {filepath}: {e}")

count = 0
for root_dir in [src_dir, test_dir, os.path.join(workspace_dir, "api")]:
    if not os.path.exists(root_dir):
        continue
    for root, _, files in os.walk(root_dir):
        # Don't process virtual envs or cache
        if '.venv' in root or '__pycache__' in root or '.git' in root or 'node_modules' in root:
            continue
        for f in files:
            if f.endswith('.py') and f != 'fix_imports.py':
                fix_file(os.path.join(root, f))
                count += 1

print(f"Processed {count} files.")

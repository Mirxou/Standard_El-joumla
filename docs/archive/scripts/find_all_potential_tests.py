import os
import re

root_dir = r"c:\Users\aboun\Desktop\Logical Version trae"
exclude_dirs = {'.venv', '.venv-1', '.git', 'node_modules', '.pytest_cache', 'htmlcov', '__pycache__', 'tests'}

test_patterns = [
    re.compile(r'import\s+unittest'),
    re.compile(r'import\s+pytest'),
    re.compile(r'from\s+unittest'),
    re.compile(r'from\s+pytest'),
    re.compile(r'class\s+Test'),
    re.compile(r'def\s+test_'),
]

found_files = []

for dirpath, dirnames, filenames in os.walk(root_dir):
    dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
    
    for f in filenames:
        if f.endswith('.py'):
            filepath = os.path.join(dirpath, f)
            
            # If name has 'test', it's already a candidate
            if 'test' in f.lower():
                found_files.append((filepath, "Name contains 'test'"))
                continue
            
            # Check content
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    for pattern in test_patterns:
                        if pattern.search(content):
                            found_files.append((filepath, f"Content matches pattern: {pattern.pattern}"))
                            break
            except Exception as e:
                pass

for path, reason in found_files:
    print(f"{path} | {reason}")

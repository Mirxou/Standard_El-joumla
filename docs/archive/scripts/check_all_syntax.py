"""Check ALL test files for syntax errors"""
import os
import ast
import glob

project_dir = r"C:\Users\aboun\Desktop\Logical Version trae"

# Check all test directories
test_dirs = [
    "tests/api",
    "tests/core",
    "tests/integration", 
    "tests/services",
    "tests/unit",
    "tests/models",
    "tests/performance",
    "tests/utils",
]

errors = []
ok_count = 0

for test_dir in test_dirs:
    full_dir = os.path.join(project_dir, test_dir)
    if not os.path.exists(full_dir):
        continue
    test_files = glob.glob(os.path.join(full_dir, "test_*.py"))
    for filepath in sorted(test_files):
        filename = os.path.relpath(filepath, project_dir)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
            ast.parse(source, filename=filepath)
            ok_count += 1
        except SyntaxError as e:
            print(f"SYNTAX ERROR: {filename}: line {e.lineno}: {e.msg}")
            errors.append((filename, e.lineno, e.msg, str(e.text).strip()))

print(f"\nOK: {ok_count}, Errors: {len(errors)}")
if errors:
    print("\nAll errors:")
    for fname, lineno, msg, text in errors:
        print(f"  {fname}:{lineno}: {msg} - {text!r}")

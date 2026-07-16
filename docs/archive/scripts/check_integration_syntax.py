"""Check which integration test files fail to import"""
import sys
import os
import ast
import glob

sys.path.insert(0, r"C:\Users\aboun\Desktop\Logical Version trae")
sys.path.insert(0, r"C:\Users\aboun\Desktop\Logical Version trae\src")

test_dir = r"C:\Users\aboun\Desktop\Logical Version trae\tests\integration"
test_files = glob.glob(os.path.join(test_dir, "test_*.py"))

print(f"Found {len(test_files)} test files")
print()

errors = []
for filepath in sorted(test_files):
    filename = os.path.basename(filepath)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        # Try to parse as AST (syntax check)
        ast.parse(source, filename=filepath)
        print(f"OK (syntax): {filename}")
    except SyntaxError as e:
        print(f"SYNTAX ERROR: {filename}: {e}")
        errors.append((filename, str(e)))

print(f"\nTotal syntax errors: {len(errors)}")
for f, e in errors:
    print(f"  {f}: {e}")

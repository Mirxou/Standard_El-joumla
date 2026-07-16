import os

root_dir = r"c:\Users\aboun\Desktop\Logical Version trae"
exclude_dirs = {'.venv', '.venv-1', '.git', 'node_modules', '.pytest_cache', 'htmlcov', '__pycache__', 'tests', 'test_data', 'tests_backup'}

found_tests = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    # modify dirnames in place to skip excluded directories
    dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
    
    for f in filenames:
        if ('test' in f.lower() and f.endswith('.py')):
            found_tests.append(os.path.join(dirpath, f))

for t in found_tests:
    print(t)

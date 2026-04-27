import os
from pathlib import Path

root = r"c:\Users\aboun\Desktop\Logical Version trae"
src_dir = os.path.join(root, "src")
tests_dir = os.path.join(root, "tests")

modules = [
    "AI", "API", "Core", "Database", "Experimental", "Models", 
    "Repositories", "Security", "Services", "UI", "Utils"
]

mapping = {
    "AI": "ai",
    "API": "api",
    "Core": "core",
    "Database": "database",
    "Experimental": "experimental",
    "Models": "models",
    "Repositories": "repositories",
    "Security": "security",
    "Services": "services",
    "UI": "ui",
    "Utils": "utils"
}

def count_files(directory):
    count = 0
    if not os.path.exists(directory): return 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                count += 1
    return count

print("## MODULE ANALYSIS")
total_src = 0
total_tests = 0

for mod in modules:
    src_subdir = os.path.join(src_dir, mapping[mod])
    
    # Heuristic for tests: check both tests/<mod> and tests/unit/<mod>, tests/integration/<mod> etc.
    test_count = 0
    test_subdirs = [
        os.path.join(tests_dir, mapping[mod]),
        os.path.join(tests_dir, "unit", mapping[mod]),
        os.path.join(tests_dir, "integration", mapping[mod]),
        os.path.join(tests_dir, "services", mapping[mod]) # Some are here
    ]
    
    src_count = count_files(src_subdir)
    
    checked_dirs = set()
    for d in test_subdirs:
        if os.path.exists(d) and d not in checked_dirs:
            test_count += count_files(d)
            checked_dirs.add(d)
            
    # Hardcoded/Specific cases from the previous report and my reorganization
    if mod == "AI":
        # I remember AI was mostly in services/ and unit/
        pass
    
    total_src += src_count
    total_tests += test_count
    
    print(f"{mod}: Src={src_count}, Tests={test_count}")

# Special cases
print(f"Total Source (.py): {total_src}")
print(f"Total Tests (.py): {count_files(tests_dir)}")

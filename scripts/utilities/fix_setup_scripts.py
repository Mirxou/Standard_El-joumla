import re

files_to_fix = [
    r"c:\Users\aboun\Desktop\Logical Version trae\scripts\utilities\setup_roles_and_perms.py",
    r"c:\Users\aboun\Desktop\Logical Version trae\scripts\utilities\setup_permissions.py"
]

for filepath in files_to_fix:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace the INSERT statements
    new_content = re.sub(
        r"INSERT OR IGNORE INTO role_permissions \(role_id, permission_id, granted_at, granted_by\)\s*VALUES \(([\d\?]+), \?, \?, 1\)",
        r"INSERT OR IGNORE INTO role_permissions (role_id, permission_id)\n               VALUES (\1, ?)",
        content
    )
    
    # Also we need to fix the values tuple passed to execute_insert
    # e.g. (perm_id, datetime.now()) -> (perm_id,)
    # e.g. (perm_map[perm_code], datetime.now()) -> (perm_map[perm_code],)
    new_content = re.sub(
        r"\((perm_id|perm_map\[perm_code\]),\s*datetime\.now\(\)\)",
        r"(\1,)",
        new_content
    )

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
    else:
        print(f"No changes for {filepath}")

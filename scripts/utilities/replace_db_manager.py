from pathlib import Path

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the double replacement issue
    new_content = content.replace('LocalLocalDatabaseManager', 'LocalDatabaseManager')
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

def main():
    utilities_dir = Path(r'c:\Users\aboun\Desktop\Logical Version trae\scripts\utilities')
    for filepath in utilities_dir.glob('*.py'):
        if filepath.name != 'replace_db_manager.py':
            process_file(filepath)
    
    print("Fix complete.")

if __name__ == '__main__':
    main()

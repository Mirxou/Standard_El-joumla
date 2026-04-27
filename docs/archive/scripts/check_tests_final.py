#!/usr/bin/env python3
import sys, os, ast
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

test_files = []
for root, dirs, files in os.walk('tests/unit'):
    for file in files:
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(os.path.join(root, file))

errors = []
for file_path in sorted(test_files):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print(f'✅ {file_path}')
    except SyntaxError as e:
        errors.append((file_path, str(e)))
        print(f'❌ {file_path}: {e}')
    except Exception as e:
        errors.append((file_path, str(e)))
        print(f'⚠️ {file_path}: {e}')

print()
print(f'📊 النتيجة: {len(errors)} أخطاء من {len(test_files)} ملف')

if errors:
    for file_path, error in errors:
        print(f'❌ {file_path}')
        print(f'   {error[:100]}')
    sys.exit(1)
else:
    print('🎉 0 أخطاء - جميع الملفات صحيحة!')
    sys.exit(0)

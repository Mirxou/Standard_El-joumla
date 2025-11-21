"""
فحص نهائي لجميع المكتبات المطلوبة
"""

from importlib.metadata import version

print('=' * 60)
print('✅ فحص المكتبات الأساسية - Libraries Check')
print('=' * 60)

libraries = [
    'argon2-cffi',
    'pyotp',
    'cryptography',
    'pydantic',
    'PySide6',
    'email-validator'
]

all_ok = True

for lib in libraries:
    try:
        v = version(lib)
        print(f'  ✅ {lib:20} v{v}')
    except Exception as e:
        print(f'  ❌ {lib:20} - NOT FOUND')
        all_ok = False

print('=' * 60)

if all_ok:
    print('🎉 جميع المكتبات موجودة - All libraries installed!')
    print('✅ النظام جاهز 100% للإنتاج - System 100% Ready')
else:
    print('⚠️  بعض المكتبات مفقودة - Some libraries missing')
    print('شغّل: pip install -r requirements.txt')

print('=' * 60)

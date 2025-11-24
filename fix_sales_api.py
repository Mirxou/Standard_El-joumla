#!/usr/bin/env python3
import re

file_path = 'tests/test_sales_api.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# أضف @requires_server قبل كل دالة test_ (ما عدا الأولى التي أضفناها يدوياً)
content = re.sub(
    r'\ndef (test_(?!update_order_status))',
    r'\n@requires_server\ndef \1',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ تم إضافة @requires_server لجميع دوال الاختبار في test_sales_api.py')

#!/usr/bin/env python3
import re

file_path = 'tests/test_reports_api.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# أضف @requires_server قبل كل دالة test_
content = re.sub(
    r'\ndef (test_\d+_)',
    r'\n@requires_server\ndef \1',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ تم إضافة @requires_server لجميع دوال الاختبار')

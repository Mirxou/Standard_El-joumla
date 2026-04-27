import sqlite3
import os

# الاتصال بقاعدة البيانات
db_path = 'erp_system.db'
if not os.path.exists(db_path):
    db_path = 'data/logical_release.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# عرض الجداول الموجودة
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('الجداول الموجودة:')
for table in tables:
    print(f'  - {table[0]}')

conn.close()




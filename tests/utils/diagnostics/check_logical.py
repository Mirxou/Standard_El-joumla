import sqlite3

conn = sqlite3.connect('data/logical_release.db')
cursor = conn.cursor()

cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="ai_models"')
result = cursor.fetchone()

if result:
    cursor.execute('PRAGMA table_info(ai_models)')
    columns = cursor.fetchall()
    print(f'جدول ai_models موجود ويحتوي على {len(columns)} عمود:')
    for i, col in enumerate(columns):
        print(f'{i}: {col[1]}')
else:
    print('جدول ai_models غير موجود')

conn.close()




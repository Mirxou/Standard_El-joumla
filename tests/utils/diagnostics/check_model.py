import sqlite3

conn = sqlite3.connect('data/logical_release.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM ai_models ORDER BY rowid DESC LIMIT 1')
row = cursor.fetchone()

if row:
    print('Row data:')
    for i, val in enumerate(row):
        print(f'{i}: {val} (type: {type(val)})')

conn.close()




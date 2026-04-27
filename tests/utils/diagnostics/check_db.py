import sqlite3

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_models'")
result = cursor.fetchone()
print('Table exists:', result is not None)

if result:
    cursor.execute('PRAGMA table_info(ai_models)')
    columns = cursor.fetchall()
    print('Columns:', [col[1] for col in columns])

conn.close()




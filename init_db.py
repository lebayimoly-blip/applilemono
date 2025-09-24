import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT,
    date TEXT,
    comment TEXT,
    photo TEXT
)
''')

conn.commit()
conn.close()

print("✅ Table 'events' créée avec succès.")

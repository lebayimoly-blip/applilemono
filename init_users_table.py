import sqlite3

conn = sqlite3.connect('database.db')  # adapte le nom si nécessaire
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT,
    password TEXT,
    role TEXT
)
''')

conn.commit()
conn.close()
print("✅ Table 'users' créée ou déjà existante.")

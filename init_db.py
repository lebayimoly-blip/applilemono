import sqlite3

conn = sqlite3.connect('vehicles.db')  # adapte le nom si nécessaire
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT NOT NULL,
    description TEXT NOT NULL,
    photo TEXT,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    agent TEXT NOT NULL
)
''')

conn.commit()
conn.close()

print("✅ Table 'incidents' créée avec succès.")

import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE incidents ADD COLUMN created_at TEXT')
    print("✅ Colonne 'created_at' ajoutée avec succès.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Erreur : {e}")

conn.commit()
conn.close()

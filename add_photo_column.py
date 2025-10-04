import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE incidents ADD COLUMN photo TEXT')
    print("✅ Colonne 'photo' ajoutée à la table 'incidents'.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Erreur : {e}")

conn.commit()
conn.close()

import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE vehicles ADD COLUMN last_maintenance TEXT')
    print("✅ Colonne 'last_maintenance' ajoutée à la table 'vehicles'.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Erreur : {e}")

conn.commit()
conn.close()

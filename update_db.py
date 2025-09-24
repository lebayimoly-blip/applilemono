import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Ajoute la colonne 'photo' si elle n'existe pas
try:
    cursor.execute('ALTER TABLE vehicles ADD COLUMN photo TEXT')
    print("✅ Colonne 'photo' ajoutée à la table 'vehicles'.")
except sqlite3.OperationalError:
    print("⚠️ La colonne 'photo' existe déjà.")

conn.commit()
conn.close()

import sqlite3

# Identifiant et mot de passe haché
username = "lebayi moly"
hashed_password = "pbkdf2:sha256:600000$uYf5ZKxv$e6e3f6c6d5f3b2a1a4e2d1c3f7e8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6"

# Connexion à la base
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Création de la table si elle n'existe pas
cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY,
    password TEXT
)
''')

# Mise à jour ou insertion
cursor.execute("INSERT OR REPLACE INTO admins (username, password) VALUES (?, ?)", (username, hashed_password))

conn.commit()
conn.close()

print("✅ Administrateur 'lebayi moly' ajouté ou mis à jour avec succès.")

import sqlite3
from werkzeug.security import generate_password_hash

# Connexion à la base de données (elle sera créée si elle n'existe pas)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Création de la table des administrateurs
cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

# Création de la table des véhicules
cursor.execute('''
CREATE TABLE IF NOT EXISTS vehicles (
    plate TEXT PRIMARY KEY,
    owner TEXT,
    insurance_expiry TEXT,
    history TEXT
)
''')

# Ajout d'un administrateur par défaut
cursor.execute('''
INSERT OR IGNORE INTO admins (username, password)
VALUES (?, ?)
''', ('admin', generate_password_hash('admin123')))

# Sauvegarde et fermeture
conn.commit()
conn.close()

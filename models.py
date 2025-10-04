import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

# Connexion à la base de données (elle sera créée si elle n'existe pas)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Activation du support des dates/horaires
conn.execute("PRAGMA foreign_keys = ON")

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

# Création de la table des incidents
cursor.execute('''
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    photo TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    vehicle_plate TEXT,
    FOREIGN KEY(vehicle_plate) REFERENCES vehicles(plate) ON DELETE CASCADE
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

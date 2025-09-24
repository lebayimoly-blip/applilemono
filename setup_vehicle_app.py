import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

# Connexion à la base
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 🔐 Table admins
cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY,
    password TEXT
)
''')

# Ajout du compte lebayi moly
username = "lebayi moly"
mot_de_passe = "Google99."
hashed_password = generate_password_hash(mot_de_passe)

cursor.execute("DELETE FROM admins WHERE username = ?", (username,))
cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hashed_password))

# 🚗 Supprimer et recréer la table vehicles
cursor.execute("DROP TABLE IF EXISTS vehicles")

cursor.execute('''
CREATE TABLE vehicles (
    plate TEXT PRIMARY KEY,
    owner TEXT,
    insurance_expiry TEXT,
    history TEXT,
    brand TEXT,
    model TEXT,
    first_registration TEXT
)
''')

vehicles = [
    ("AB123CD", "Jean Mba", "2025-12-31", "Aucun incident", "Toyota", "Corolla", "2020-06-15"),
    ("XY456EF", "Amina Diallo", "2024-08-20", "Révision en 2023", "Hyundai", "Tucson", "2019-03-10"),
    ("GH789IJ", "Marc Okou", "2023-11-01", "Changement de freins", "Peugeot", "208", "2018-09-05")
]

cursor.executemany('''
INSERT INTO vehicles (plate, owner, insurance_expiry, history, brand, model, first_registration)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', vehicles)

# 📅 Table events
cursor.execute('''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT,
    date TEXT,
    comment TEXT,
    photo TEXT
)
''')

events = [
    ("AB123CD", "2023-11-10 10:00:00", "Révision technique complète", "AB123CD_revision.jpg"),
    ("XY456EF", "2024-05-22 14:30:00", "Changement de pneus", "XY456EF_pneus.jpg"),
    ("GH789IJ", "2023-10-01 09:15:00", "Contrôle des freins", "GH789IJ_freins.jpg")
]

cursor.executemany('''
INSERT INTO events (plate, date, comment, photo)
VALUES (?, ?, ?, ?)
''', events)

conn.commit()
conn.close()

print("✅ Base de données initialisée avec succès.")
print("👤 Compte admin : lebayi moly / Google99.")
print("🚗 3 véhicules et 3 événements ajoutés.")

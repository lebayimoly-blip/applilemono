import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('database.db')  # adapte le nom si nécessaire
cursor = conn.cursor()

# Récupération de tous les utilisateurs
users = cursor.execute('SELECT * FROM users').fetchall()

print("📋 Liste des utilisateurs :\n")

# Affichage avec distinction du super admin
for user in users:
    user_id = user[0]
    username = user[1]
    email = user[2]
    password = user[3]
    role = user[4]

    # Détection du super utilisateur
    titre = "SUPER ADMIN" if username.lower() == "lebayi moly" and role.lower() == "admin" else role.upper()

    print(f"🆔 ID : {user_id} | 👤 Nom : {username} | 📧 Email : {email} | 🔐 Mot de passe : {password} | 🎓 Rôle : {titre}")

# Fermeture de la connexion
conn.close()

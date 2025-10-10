import sqlite3
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
from app import app  # Assure-toi que app est bien importé

with app.app_context():
    # Connexion à l'ancienne base SQLite
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Récupérer les anciens utilisateurs
    cursor.execute("SELECT username, password FROM admins")
    old_users = cursor.fetchall()

    # Migrer vers SQLAlchemy
    for username, raw_password in old_users:
        # Vérifie si l'utilisateur existe déjà
        if not User.query.filter_by(username=username).first():
            user = User(
                username=username,
                email=f"{username.replace(' ', '_')}@example.com",
                role='admin',
                password=generate_password_hash(raw_password)  # hashage
            )
            db.session.add(user)
            print(f"✅ Migré : {username}")
        else:
            print(f"ℹ️ Déjà présent : {username}")

    db.session.commit()
    conn.close()
    print("🎉 Migration terminée")

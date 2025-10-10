from models import User
from extensions import db
from flask import Flask
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    if not User.query.filter_by(username='lebayi moly').first():
        super_admin = User(
            username='lebayi moly',
            email='lebayi@lab.com',
            role='admin',
            password=generate_password_hash('Google99.')
        )
        db.session.add(super_admin)
        db.session.commit()
        print("✅ Super admin recréé avec succès.")
    else:
        print("ℹ️ Le compte existe déjà.")

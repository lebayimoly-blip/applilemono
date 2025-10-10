from models import User
from extensions import db
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # adapte si tu es sur PostgreSQL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"👤 {user.username} | 📧 {user.email} | 🎭 {user.role}")

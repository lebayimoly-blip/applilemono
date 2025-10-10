from extensions import db
from werkzeug.security import generate_password_hash

# 🧑 Utilisateur
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(128), nullable=False)

    @staticmethod
    def create_default_admin():
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()


# 🚗 Véhicule
class Vehicle(db.Model):
    plate = db.Column(db.String, primary_key=True)
    owner = db.Column(db.String, nullable=False)
    brand = db.Column(db.String, nullable=True)
    model = db.Column(db.String, nullable=True)
    insurance_expiry = db.Column(db.String, nullable=True)
    first_registration = db.Column(db.String, nullable=True)
    last_maintenance = db.Column(db.String, nullable=True)
    maintenance_date = db.Column(db.String, nullable=True)
    history = db.Column(db.Text, nullable=True)
    photo = db.Column(db.String, nullable=True)


# ⚠️ Incident
class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String, nullable=True)
    timestamp = db.Column(db.String, nullable=False)
    vehicle_plate = db.Column(db.String, db.ForeignKey('vehicle.plate'), nullable=False)

    vehicle = db.relationship('Vehicle', backref=db.backref('incidents', cascade='all, delete'))

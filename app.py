from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from extensions import db
from models import User, Vehicle, Incident
from werkzeug.utils import secure_filename
import pandas as pd
import os
from datetime import datetime

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = 'ton_secret_key'  # Remplace par une vraie clé secrète

# Configuration de SQLAlchemy (PostgreSQL via Render ou SQLite local)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db.init_app(app)

# Création des tables et ajout de l'admin par défaut
with app.app_context():
    db.create_all()
    User.create_default_admin()

# 🔐 Connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error = "Veuillez remplir tous les champs."
        else:
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['admin'] = user.username
                session['role'] = user.role
                return redirect('/search' if user.role == 'agent' else '/dashboard')
            error = "Identifiants incorrects"

    return render_template('login.html', error=error)

# 🏠 Page d'accueil
@app.route('/')
def home():
    return redirect('/login')

# 📊 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/')
    return render_template('dashboard.html', admin=session['admin'], role=session['role'])

# 🚗 Ajout ou modification de véhicule
@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_or_edit_vehicle():
    if 'admin' not in session:
        return redirect('/')
    message = None

    if request.method == 'POST':
        plate = request.form['plate']
        owner = request.form['owner']
        brand = request.form['brand']
        model = request.form['model']
        insurance_expiry = request.form['insurance_expiry']
        first_registration = request.form['first_registration']
        last_maintenance = request.form['last_maintenance']
        photo_file = request.files.get('photo')

        photo_filename = None
        if photo_file and photo_file.filename != '':
            photo_filename = f"{plate}_{secure_filename(photo_file.filename)}"
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)

        vehicle = Vehicle.query.filter_by(plate=plate).first()
        if vehicle:
            vehicle.owner = owner
            vehicle.brand = brand
            vehicle.model = model
            vehicle.insurance_expiry = insurance_expiry
            vehicle.first_registration = first_registration
            vehicle.last_maintenance = last_maintenance
            vehicle.photo = photo_filename
            message = "✅ Véhicule mis à jour avec succès."
        else:
            new_vehicle = Vehicle(
                plate=plate,
                owner=owner,
                brand=brand,
                model=model,
                insurance_expiry=insurance_expiry,
                first_registration=first_registration,
                last_maintenance=last_maintenance,
                photo=photo_filename
            )
            db.session.add(new_vehicle)
            message = "✅ Véhicule ajouté avec succès."

        db.session.commit()

    return render_template('add_vehicle.html', message=message)

@app.route('/vehicle/<plate>', methods=['GET', 'POST'])
def vehicle_detail(plate):
    if 'admin' not in session:
        return redirect('/')

    vehicle = Vehicle.query.filter_by(plate=plate).first()
    if not vehicle:
        return "Véhicule introuvable", 404

    message = None

    if request.method == 'POST':
        new_date = request.form.get('last_maintenance')
        if new_date:
            vehicle.last_maintenance = new_date
            message = "✅ Date d’entretien mise à jour."

        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            photo_filename = f"{plate}_{secure_filename(photo_file.filename)}"
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)
            vehicle.photo = photo_filename
            message = "✅ Photo du véhicule mise à jour."

        db.session.commit()

    incidents = Incident.query.filter_by(vehicle_plate=plate).all()

    return render_template('vehicle_detail.html', vehicle=vehicle, incidents=incidents, message=message)

@app.route('/import_excel', methods=['GET', 'POST'])
def import_excel():
    if 'admin' not in session or session['admin'] != "lebayi moly":
        return redirect('/')

    message = None
    duplicates = []
    format_errors = []
    expected_columns = ['plate', 'owner', 'insurance_expiry', 'history', 'brand', 'model', 'first_registration']

    if request.method == 'POST':
        file = request.files['excel_file']
        if file and file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)

                missing = [col for col in expected_columns if col not in df.columns]
                if missing:
                    message = f"⚠️ Colonnes manquantes : {', '.join(missing)}"
                    return render_template('import_excel.html', message=message)

                internal_duplicates = df['plate'][df['plate'].duplicated()].tolist()
                if internal_duplicates:
                    format_errors.append(f"Plaques dupliquées dans le fichier : {', '.join(internal_duplicates)}")

                for col in ['insurance_expiry', 'first_registration']:
                    if not pd.to_datetime(df[col], errors='coerce').notna().all():
                        format_errors.append(f"⚠️ Dates invalides dans la colonne '{col}'")

                if format_errors:
                    return render_template('import_excel.html', message="⚠️ Erreurs de format détectées", format_errors=format_errors)

                existing_plates = [v.plate for v in Vehicle.query.all()]
                for _, row in df.iterrows():
                    if row['plate'] in existing_plates:
                        duplicates.append(row['plate'])
                    else:
                        new_vehicle = Vehicle(
                            plate=row['plate'],
                            owner=row['owner'],
                            insurance_expiry=row['insurance_expiry'],
                            history=row.get('history', ''),
                            brand=row.get('brand', ''),
                            model=row.get('model', ''),
                            first_registration=row.get('first_registration', '')
                        )
                        db.session.add(new_vehicle)

                db.session.commit()

                if duplicates:
                    message = f"⚠️ Importation partielle : plaques déjà existantes : {', '.join(duplicates)}"
                else:
                    message = "✅ Importation réussie."

            except Exception as e:
                message = f"⚠️ Erreur lors de l'importation : {str(e)}"
        else:
            message = "⚠️ Format de fichier non supporté. Utilisez un fichier .xlsx"

    return render_template('import_excel.html', message=message, format_errors=format_errors, duplicates=duplicates)

# 📈 Statistiques
@app.route('/admin/stats')
def admin_stats():
    if 'admin' not in session:
        return redirect('/')

    total_vehicles = Vehicle.query.count()

    return render_template('stats.html', total_vehicles=total_vehicles)


# 🔎 Recherche
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'admin' not in session:
        return redirect('/')

    result = None
    if request.method == 'POST':
        plate = request.form.get('plate', '').strip().lower()
        result = Vehicle.query.filter(db.func.lower(Vehicle.plate) == plate).first()

    return render_template('search.html', result=result)


# 👤 Ajout utilisateur
from werkzeug.security import generate_password_hash

@app.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if session.get('role') != 'admin':
        return "⛔ Accès réservé aux administrateurs"

    message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not username or not password or not role:
            message = "⚠️ Tous les champs sont requis."
        elif User.query.filter_by(username=username).first():
            message = "⚠️ Nom d'utilisateur déjà existant."
        else:
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                role=role,
                email=f"{username}@example.com"  # ou formulaire email
            )
            db.session.add(new_user)
            db.session.commit()
            message = "✅ Utilisateur ajouté avec succès."

    return render_template('add_user.html', message=message)


# 🚪 Déconnexion
@app.route('/logout')
def logout():
    session.pop('admin', None)
    session.pop('role', None)
    return redirect('/')


# 📝 Ajout d’un incident
@app.route('/add_incident', methods=['GET', 'POST'])
def add_incident():
    if 'admin' not in session:
        return redirect('/')

    if request.method == 'POST':
        description = request.form.get('description')
        photo = request.form.get('photo')  # à gérer si tu veux uploader
        vehicle_plate = request.form.get('vehicle_plate')

        if not description or not vehicle_plate:
            return render_template('add_incident.html', error="Tous les champs obligatoires doivent être remplis.")

        incident = Incident(
            description=description,
            photo=photo,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            vehicle_plate=vehicle_plate
        )
        db.session.add(incident)
        db.session.commit()
        return redirect('/admin/incidents')

    return render_template('add_incident.html')

# 👥 Gestion des utilisateurs
@app.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    if 'admin' not in session or session['admin'] != 'lebayi moly':
        return redirect('/')

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if user_id:
            user = User.query.get(user_id)
            if user:
                user.username = username
                user.email = email
                user.role = role
                if password:
                    user.password = generate_password_hash(password)
        else:
            new_user = User(
                username=username,
                email=email,
                role=role,
                password=generate_password_hash(password)
            )
            db.session.add(new_user)

        db.session.commit()

    users = User.query.all()
    return render_template('manage_users.html', users=users)


# ❌ Suppression d’un utilisateur
@app.route('/admin/users/delete/<int:user_id>')
def delete_user(user_id):
    if 'admin' not in session or session['admin'] != 'lebayi moly':
        return redirect('/')

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect('/admin/users')


# 🚗 Liste des véhicules pour modification
@app.route('/modify_vehicle')
def modify_vehicle():
    vehicles = Vehicle.query.with_entities(Vehicle.plate, Vehicle.model).all()
    return render_template('modify_vehicle.html', vehicles=vehicles)


# 🚗 Sélection d’un véhicule
@app.route('/select_vehicle', methods=['POST'])
def select_vehicle():
    plate = request.form['plate']
    return redirect(url_for('vehicle_detail_modify', plate=plate))


# 🚗 Récupération d’un véhicule
def get_vehicle_by_plate(plate):
    return Vehicle.query.filter_by(plate=plate).first()


# 🛠️ Édition d’un véhicule
@app.route('/edit_vehicle/<plate>', methods=['GET', 'POST'])
def edit_vehicle(plate):
    if request.method == 'POST':
        pass  # à compléter si nécessaire

    vehicle = get_vehicle_by_plate(plate)
    if vehicle:
        return render_template('edit_vehicle.html', vehicle=vehicle)
    else:
        return "Véhicule introuvable", 404


# 🛠️ Modification complète d’un véhicule
@app.route('/vehicle/modify/<plate>', methods=['GET', 'POST'])
def vehicle_detail_modify(plate):
    vehicle = Vehicle.query.filter_by(plate=plate).first()
    if not vehicle:
        return "Véhicule introuvable", 404

    if request.method == 'POST':
        vehicle.owner = request.form['owner']
        vehicle.insurance_expiry = request.form['insurance_expiry']
        vehicle.history = request.form['history']
        vehicle.brand = request.form['brand']
        vehicle.model = request.form['model']
        vehicle.first_registration = request.form['first_registration']
        vehicle.maintenance_date = request.form.get('maintenance_date')

        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            photo_filename = secure_filename(photo_file.filename)
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)
            vehicle.photo = photo_filename

        db.session.commit()

    return render_template('vehicle_detail_modify.html', vehicle=vehicle)


# 🛠️ Initialisation manuelle de la base
@app.route('/init-db')
def init_db():
    db.create_all()
    return "✅ Base PostgreSQL initialisée avec succès !"


# 👥 Liste brute des utilisateurs
@app.route('/users')
def list_users():
    users = User.query.all()
    return "<br>".join([f"{u.username} ({u.email})" for u in users])


# 🔐 Réinitialisation du mot de passe
@app.route('/reset-lebayi')
def reset_lebayi():
    user = User.query.filter_by(username='lebayi moly').first()
    if user:
        user.password = generate_password_hash('Google99.')
        db.session.commit()
        return "✅ Mot de passe réinitialisé pour 'lebayi moly'"
    else:
        return "❌ Utilisateur introuvable"


# 🚀 Lancement de l'app
if __name__ == '__main__':
    print("🚀 Application Flask en cours de démarrage...")
    app.run(debug=True)

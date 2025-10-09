from datetime import datetime  # Ajouté en haut du fichier
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os


app = Flask(__name__)
app.secret_key = 'ton_secret_key'  # Remplace par une vraie clé secrète

# 📦 Connexion à la base
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# 🔐 Page de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['admin'] = user['username']
            session['role'] = user['role']
            if session['role'] == 'agent':
                return redirect('/search')
            else:
                return redirect('/dashboard')
        else:
            return render_template('login.html', error="Identifiants incorrects")
    return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
def home():
    return redirect('/login')


# 📊 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/')
    
    return render_template('dashboard.html', admin=session['admin'], role=session['role'])

# 🚗 Ajout de véhicule avec photo
@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_or_edit_vehicle():
    message = None
    conn = get_db_connection()

    if request.method == 'POST':
        plate = request.form['plate']
        owner = request.form['owner']
        brand = request.form['brand']
        model = request.form['model']
        insurance_expiry = request.form['insurance_expiry']
        first_registration = request.form['first_registration']
        last_maintenance = request.form['last_maintenance']
        photo_file = request.files.get('photo')

        # Vérifie si le véhicule existe déjà
        existing = conn.execute('SELECT * FROM vehicles WHERE plate = ?', (plate,)).fetchone()

        photo_filename = None
        if photo_file and photo_file.filename != '':
            photo_filename = f"{plate}_{photo_file.filename}"
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)

        if existing:
            # Mise à jour
            conn.execute('''
                UPDATE vehicles SET owner=?, brand=?, model=?, insurance_expiry=?, 
                first_registration=?, last_maintenance=?, photo=?
                WHERE plate=?
            ''', (owner, brand, model, insurance_expiry, first_registration, last_maintenance, photo_filename, plate))
            message = "✅ Véhicule mis à jour avec succès."
        else:
            # Ajout
            conn.execute('''
                INSERT INTO vehicles (plate, owner, brand, model, insurance_expiry, 
                first_registration, last_maintenance, photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plate, owner, brand, model, insurance_expiry, first_registration, last_maintenance, photo_filename))
            message = "✅ Véhicule ajouté avec succès."

        conn.commit()
        conn.close()

    else:
        conn.close()

    return render_template('add_vehicle.html', message=message)

# 🔍 Fiche véhicule avec photo


@app.route('/vehicle/<plate>', methods=['GET', 'POST'])
def vehicle_detail(plate):
    if 'admin' not in session:
        return redirect('/')

    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicles WHERE plate = ?', (plate,)).fetchone()

    if vehicle is None:
        conn.close()
        return "Véhicule introuvable", 404

    message = None

    if request.method == 'POST':
        # Mise à jour de la date d’entretien
        new_date = request.form.get('last_maintenance')
        if new_date:
            conn.execute('UPDATE vehicles SET last_maintenance = ? WHERE plate = ?', (new_date, plate))
            conn.commit()
            message = "✅ Date d’entretien mise à jour."

        # Mise à jour de la photo du véhicule
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            photo_filename = f"{plate}_{photo_file.filename}"
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)
            conn.execute('UPDATE vehicles SET photo = ? WHERE plate = ?', (photo_filename, plate))
            conn.commit()
            message = "✅ Photo du véhicule mise à jour."

    incidents = conn.execute('SELECT * FROM incidents WHERE plate = ?', (plate,)).fetchall()
    conn.close()

    return render_template('vehicle_detail.html', vehicle=vehicle, incidents=incidents, message=message)

# 📥 Import Excel
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
                if not all(col in df.columns for col in expected_columns):
                    missing = [col for col in expected_columns if col not in df.columns]
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
                conn = get_db_connection()
                existing_plates = [row['plate'] for row in conn.execute('SELECT plate FROM vehicles').fetchall()]
                for _, row in df.iterrows():
                    if row['plate'] in existing_plates:
                        duplicates.append(row['plate'])
                    else:
                        conn.execute('''
                            INSERT INTO vehicles (plate, owner, insurance_expiry, history, brand, model, first_registration)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row['plate'], row['owner'], row['insurance_expiry'],
                            row.get('history', ''), row.get('brand', ''),
                            row.get('model', ''), row.get('first_registration', '')
                        ))
                conn.commit()
                conn.close()
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

    conn = get_db_connection()

    total_vehicles = conn.execute(
        'SELECT COUNT(*) FROM vehicles'
    ).fetchone()[0]

    conn.close()

    return render_template(
        'stats.html',
        total_vehicles=total_vehicles
    )


# 🔎 Recherche
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'admin' not in session:
        return redirect('/')
    result = None
    if request.method == 'POST':
        plate = request.form.get('plate', '').strip().lower()
        conn = get_db_connection()
        result = conn.execute('SELECT * FROM vehicles WHERE LOWER(plate) = ?', (plate,)).fetchone()
        conn.close()
    return render_template('search.html', result=result)

# 👤 Ajout utilisateur
@app.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if session.get('role') != 'admin':
        return "⛔ Accès réservé aux administrateurs"
    message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
            conn.commit()
            conn.close()
            message = "✅ Utilisateur ajouté avec succès."
        except sqlite3.IntegrityError:
            message = "⚠️ Nom d'utilisateur déjà existant."
    return render_template('add_user.html', message=message)

# 🚪 Déconnexion
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

# 📝 Ajout d’un incident
@app.route('/add_incident', methods=['GET', 'POST'])
def add_incident():
    if 'admin' not in session:
        return redirect('/')
    
    conn = get_db_connection()
    vehicles = conn.execute('SELECT plate FROM vehicles').fetchall()
    message = None

    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        selected_plate = request.form.get('plate')
        photo_file = request.files.get('photo')
        photo_filename = None

        if photo_file and photo_file.filename != '':
            photo_filename = f"{selected_plate}_{photo_file.filename}"
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)

        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            conn.execute(
                'INSERT INTO incidents (plate, description, created_at, photo) VALUES (?, ?, ?, ?)',
                (selected_plate, description, created_at, photo_filename)
            )
            conn.commit()
            message = "✅ Incident enregistré avec succès."
        except Exception as e:
            message = f"⚠️ Erreur : {str(e)}"
    
    conn.close()
    return render_template('add_incident.html', vehicles=vehicles, message=message)

@app.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    if 'admin' not in session or session['admin'] != 'lebayi moly':
        return redirect('/')

    conn = get_db_connection()

    # Ajouter ou modifier un utilisateur
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if user_id:  # Modification
            conn.execute('''
                UPDATE users SET username=?, email=?, password=?, role=? WHERE id=?
            ''', (username, email, password, role, user_id))
        else:  # Ajout
            conn.execute('''
                INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)
            ''', (username, email, password, role))

        conn.commit()

    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('manage_users.html', users=users)
@app.route('/admin/users/delete/<int:user_id>')
def delete_user(user_id):
    if 'admin' not in session or session['admin'] != 'lebayi moly':
        return redirect('/')

    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/users')
import sqlite3

def get_all_vehicles():
    conn = sqlite3.connect('database.db')  # remplace par le nom réel de ta base
    cursor = conn.cursor()
    cursor.execute("SELECT plate, model FROM vehicles")
    rows = cursor.fetchall()
    conn.close()
    return [{'plate': row[0], 'model': row[1]} for row in rows]

@app.route('/modify_vehicle')
def modify_vehicle():
    vehicles = get_all_vehicles()
    return render_template('modify_vehicle.html', vehicles=vehicles)

@app.route('/select_vehicle', methods=['POST'])
def select_vehicle():
    plate = request.form['plate']
    return redirect(url_for('vehicle_detail_modify', plate=plate))  # ✅ nouvelle fiche

import sqlite3

def get_vehicle_by_plate(plate):
    conn = sqlite3.connect('database.db')  # remplace par ton nom de base si différent
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE plate = ?", (plate,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'plate': row[0],
            'owner': row[1],
            'insurance_expiry': row[2],
            'history': row[3],
            'brand': row[4],
            'model': row[5],
            'first_registration': row[6]
        }
    else:
        return None
@app.route('/edit_vehicle/<plate>', methods=['GET', 'POST'])
def edit_vehicle(plate):
    if request.method == 'POST':
        # mise à jour ici si nécessaire
        pass

    vehicle = get_vehicle_by_plate(plate)
    if vehicle:
        return render_template('edit_vehicle.html', vehicle=vehicle)
    else:
        return "Véhicule introuvable", 404

@app.route('/vehicle/modify/<plate>', methods=['GET', 'POST'])
def vehicle_detail_modify(plate):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        owner = request.form['owner']
        insurance_expiry = request.form['insurance_expiry']
        history = request.form['history']
        brand = request.form['brand']
        model = request.form['model']
        first_registration = request.form['first_registration']
        maintenance_date = request.form.get('maintenance_date')

        # Gestion de la photo
        photo_file = request.files.get('photo')
        photo_filename = None
        if photo_file and photo_file.filename:
            photo_filename = secure_filename(photo_file.filename)
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)

        # Mise à jour SQL
        cursor.execute("""
            UPDATE vehicles
            SET owner = ?, insurance_expiry = ?, history = ?, brand = ?, model = ?, first_registration = ?, maintenance_date = ?, photo = ?
            WHERE plate = ?
        """, (owner, insurance_expiry, history, brand, model, first_registration, maintenance_date, photo_filename, plate))
        conn.commit()

    # Récupération des données
    cursor.execute("SELECT * FROM vehicles WHERE plate = ?", (plate,))
    row = cursor.fetchone()
    conn.close()

    if row:
        vehicle = {
            'plate': row[0],
            'owner': row[1],
            'insurance_expiry': row[2],
            'history': row[3],
            'brand': row[4],
            'model': row[5],
            'first_registration': row[6],
            'maintenance_date': row[7],
            'photo': row[8]
        }
        return render_template('vehicle_detail_modify.html', vehicle=vehicle)
    else:
        return "Véhicule introuvable", 404


# 🚀 Lancement de l'app
if __name__ == '__main__':
    print("🚀 Application Flask en cours de démarrage...")
    app.run(debug=True)

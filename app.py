from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os

app = Flask(__name__)
app.secret_key = 'ton_secret_key'  # Remplace par une vraie clé secrète

# 📦 Connexion à la base
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# 🔐 Page de login (modifiée pour accepter POST)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['admin'] = username
            session['role'] = user['role']  # ✅ stocke le rôle
            return redirect('/dashboard')

        return render_template('login.html', message="❌ Identifiants incorrects")

    return render_template('login.html')




# 📊 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/')
    return render_template('dashboard.html')

# 🚗 Ajout de véhicule avec photo
@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if 'admin' not in session:
        return redirect('/')

    message = None
    if request.method == 'POST':
        plate = request.form['plate']
        owner = request.form['owner']
        insurance_expiry = request.form['insurance_expiry']
        history = request.form.get('history', '')
        brand = request.form.get('brand', '')
        model = request.form.get('model', '')
        first_registration = request.form.get('first_registration', '')
        photo_file = request.files.get('photo')

        photo_filename = None
        if photo_file and photo_file.filename != '':
            photo_filename = f"{plate}_{photo_file.filename}"
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)

        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO vehicles (plate, owner, insurance_expiry, history, brand, model, first_registration, photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plate, owner, insurance_expiry, history, brand, model, first_registration, photo_filename))
            conn.commit()
            conn.close()
            message = "✅ Véhicule ajouté avec succès."
        except sqlite3.IntegrityError:
            message = "⚠️ Plaque déjà existante."

    return render_template('add_vehicle.html', message=message)

# 🔍 Fiche véhicule avec photo
@app.route('/vehicle/<plate>')
def vehicle_detail(plate):
    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicles WHERE plate = ?', (plate,)).fetchone()
    conn.close()
    if vehicle is None:
        return "Véhicule introuvable", 404
    return render_template('vehicle_detail.html', vehicle=vehicle)

# 🖼️ Modifier la photo du véhicule
@app.route('/vehicle/<plate>/edit_photo', methods=['GET', 'POST'])
def edit_vehicle_photo(plate):
    if 'admin' not in session:
        return redirect('/')

    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicles WHERE plate = ?', (plate,)).fetchone()

    if vehicle is None:
        conn.close()
        return "Véhicule introuvable", 404

    message = None
    if request.method == 'POST':
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            photo_filename = f"{plate}_{photo_file.filename}"
            photo_path = os.path.join('static/uploads', photo_filename)
            photo_file.save(photo_path)

            conn.execute('UPDATE vehicles SET photo = ? WHERE plate = ?', (photo_filename, plate))
            conn.commit()
            message = "✅ Photo mise à jour avec succès."

    conn.close()
    return render_template('edit_photo.html', vehicle=vehicle, message=message)
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

                # Vérification des colonnes
                if not all(col in df.columns for col in expected_columns):
                    missing = [col for col in expected_columns if col not in df.columns]
                    message = f"⚠️ Colonnes manquantes : {', '.join(missing)}"
                    return render_template('import_excel.html', message=message)

                # Vérification des doublons internes
                internal_duplicates = df['plate'][df['plate'].duplicated()].tolist()
                if internal_duplicates:
                    format_errors.append(f"Plaques dupliquées dans le fichier : {', '.join(internal_duplicates)}")

                # Vérification des types de données
                for col in ['insurance_expiry', 'first_registration']:
                    if not pd.to_datetime(df[col], errors='coerce').notna().all():
                        format_errors.append(f"⚠️ Dates invalides dans la colonne '{col}'")

                # Si erreurs de format, on les affiche
                if format_errors:
                    return render_template('import_excel.html', message="⚠️ Erreurs de format détectées", format_errors=format_errors)

                # Vérification des doublons avec la base
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
@app.route('/admin/stats')
def admin_stats():
    if 'admin' not in session:
        return redirect('/')

    # Exemple de statistiques fictives
    conn = get_db_connection()
    total_vehicles = conn.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]
    conn.close()

    return render_template('admin_stats.html', total_vehicles=total_vehicles)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'admin' not in session:
        return redirect('/')

    result = None
    if request.method == 'POST':
        plate = request.form.get('plate', '').strip().lower()

        conn = get_db_connection()
        result = conn.execute(
            'SELECT * FROM vehicles WHERE LOWER(plate) = ?',
            (plate,)
        ).fetchone()
        conn.close()

    return render_template('search.html', result=result)

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
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (username, password, role))
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

# 🚀 Lancement de l'app
if __name__ == '__main__':
    app.run(debug=True)

import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

plate_to_check = '12345'  # Remplace par la plaque du véhicule concerné

rows = cursor.execute('SELECT * FROM incidents WHERE plate = ?', (plate_to_check,)).fetchall()

if rows:
    for row in rows:
        print("📋 Incident trouvé :")
        print("Description :", row[1])  # selon l'ordre des colonnes
        print("Date :", row[2])
        print("Photo :", row[3] if len(row) > 3 else "Aucune")
        print("-" * 30)
else:
    print("❌ Aucun incident trouvé pour ce véhicule.")

conn.close()

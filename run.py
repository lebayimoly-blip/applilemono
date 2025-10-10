from app import create_app, db
import models  # ← important pour que les tables soient connues

app = create_app()

with app.app_context():
    db.create_all()

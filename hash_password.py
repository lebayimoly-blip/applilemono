from werkzeug.security import generate_password_hash

mot_de_passe = "Google99."
hash = generate_password_hash(mot_de_passe)
print("Mot de passe haché :")
print(hash)

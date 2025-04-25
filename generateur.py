from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Génère les clés
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
pem_private = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
pem_public = private_key.public_key().public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

# Enregistre les fichiers
with open('private_key.pem', 'wb') as f: f.write(pem_private)
with open('public_key.pem', 'wb') as f: f.write(pem_public)
print("Clés générées avec succès !")
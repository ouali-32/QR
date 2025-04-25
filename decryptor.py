from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64

PRIVATE_KEY_PATH = r"private_key.pem"

def load_private_key():
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # ou votre mot de passe si la clé est protégée
            backend=default_backend()
        )

def decrypt(encrypted_b64, private_key):
    # Correction du padding base64
    encrypted_b64 = encrypted_b64.strip().replace(' ', '').replace('\n', '')
    missing_padding = len(encrypted_b64) % 4
    if missing_padding:
        encrypted_b64 += '=' * (4 - missing_padding)

    try:
        encrypted = base64.urlsafe_b64decode(encrypted_b64)
    except Exception as e:
        raise ValueError("Erreur lors du décodage base64 : données invalides") from e

    # Vérification de la longueur
    expected_length = private_key.key_size // 8
    if len(encrypted) != expected_length:
        raise ValueError("Données corrompues. Contactez l'administrateur.")

    # Déchiffrement
    return private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).decode()

if __name__ == '__main__':
    encrypted_data = input("Données chiffrées complètes (après ||) : ").strip()
    private_key = load_private_key()
    try:
        print("Résultat :", decrypt(encrypted_data, private_key))
    except ValueError as ve:
        print(f"❌ ERREUR CRITIQUE : {str(ve)}")
        print("📌 Causes possibles :")
        print("- Données tronquées lors du scan")
        print("- Mismatch clé publique/privée")
        print("- Données corrompues ou modifiées")

import requests
from decryptor import decrypt
from cryptography.hazmat.primitives import serialization

# Configuration
API_URL = "http://localhost:5000"
SECRET_WORD = "elias bidrou"

# Charger la clé privée désérialisée
with open("private_key.pem", "rb") as f:
    PRIVATE_KEY = serialization.load_pem_private_key(f.read(), password=None)

print("1. Génération du QR code...")
response = requests.post(
    f"{API_URL}/generate",
    json={"data": SECRET_WORD, "user_id": 123, "expiration_days": 1}
)

if response.status_code == 200:
    with open("qr_ouali.png", "wb") as f:
        f.write(response.content)
    print("✅ QR code généré : qr_ouali.png")
    
    print("\n2. Vérification du QR code...")
    with open("qr_ouali.png", "rb") as f:
        verify_response = requests.post(f"{API_URL}/verify", files={"file": f})
    
    if verify_response.status_code == 200:
        encrypted_data = verify_response.json()["encrypted_data"]
        print("🔒 Données chiffrées :", encrypted_data)
        
        print("\n3. Déchiffrement avec votre clé privée...")
        decrypted = decrypt(encrypted_data, PRIVATE_KEY)  # ✅ Objet clé valide
        print(f"🔑 Résultat : {decrypted} {'✅' if decrypted == SECRET_WORD else '❌'}")
    else:
        print("❌ Erreur vérification :", verify_response.text)
else:
    print("❌ Erreur génération :", response.text)
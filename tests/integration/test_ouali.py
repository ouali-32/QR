import requests
import time
from decryptor import decrypt
from cryptography.hazmat.primitives import serialization

# Configuration
API_URL = "http://localhost:5000"
SECRET_WORD = "elias bidrou"

def wait_for_server():
    """Attend que le serveur soit prêt"""
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_URL}/", timeout=5)
            if response.status_code == 200:
                return True
        except:
            time.sleep(2)
            print(f"⏳ Attente du serveur... (tentative {i+1}/{max_retries})")
    raise Exception("Serveur non disponible après plusieurs tentatives")

def test_qr_flow():
    # Charger la clé privée
    with open("private_key.pem", "rb") as f:
        PRIVATE_KEY = serialization.load_pem_private_key(f.read(), password=None)
    
    # 1. Attendre le serveur
    wait_for_server()
    
    # 2. Génération QR
    print("1. Génération du QR code...")
    try:
        response = requests.post(
            f"{API_URL}/generate",
            json={"data": SECRET_WORD, "expiration_days": 1},
            timeout=10
        )
        response.raise_for_status()
        
        with open("qr_ouali.png", "wb") as f:
            f.write(response.content)
        print("✅ QR code généré : qr_ouali.png")
        
        # 3. Vérification
        print("\n2. Vérification du QR code...")
        with open("qr_ouali.png", "rb") as f:
            verify_response = requests.post(
                f"{API_URL}/verify",
                files={"file": f},
                timeout=10
            )
        verify_response.raise_for_status()
        
        encrypted_data = verify_response.json()["encrypted_data"]
        print("🔒 Données chiffrées :", encrypted_data[:50] + "...")
        
        # 4. Déchiffrement
        print("\n3. Déchiffrement...")
        decrypted = decrypt(encrypted_data, PRIVATE_KEY)
        print(f"🔑 Résultat : {decrypted} {'✅' if decrypted == SECRET_WORD else '❌'}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur HTTP: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print("Détails:", e.response.text)
        raise

if __name__ == "__main__":
    test_qr_flow()
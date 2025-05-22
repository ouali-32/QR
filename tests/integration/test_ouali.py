import requests
import time
import os
import sys
import subprocess
import signal
import atexit
from decryptor import decrypt
from cryptography.hazmat.primitives import serialization

# Configuration
API_URL = "http://localhost:5000"
SECRET_WORD = "elias bidrou"
SERVER_PROCESS = None

def start_server():
    """Démarre le serveur Flask en arrière-plan"""
    global SERVER_PROCESS
    
    # Chemin vers le fichier principal de l'application
    app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "appV2_2.py")
    
    print("🚀 Démarrage du serveur Flask...")
    
    # Démarrer le serveur en arrière-plan
    if sys.platform == 'win32':
        # Pour Windows
        SERVER_PROCESS = subprocess.Popen(
            ["python", app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # Pour Linux/Mac
        SERVER_PROCESS = subprocess.Popen(
            ["python", app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
    
    # Enregistrer la fonction pour arrêter le serveur à la fin
    atexit.register(stop_server)

def stop_server():
    """Arrête le serveur Flask"""
    global SERVER_PROCESS
    if SERVER_PROCESS:
        print("🛑 Arrêt du serveur Flask...")
        if sys.platform == 'win32':
            # Pour Windows
            SERVER_PROCESS.terminate()
        else:
            # Pour Linux/Mac
            os.killpg(os.getpgid(SERVER_PROCESS.pid), signal.SIGTERM)
        
        # Attendre que le processus se termine
        SERVER_PROCESS.wait(timeout=5)
        print("✅ Serveur arrêté")

def wait_for_server():
    """Attend que le serveur soit prêt"""
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_URL}/", timeout=5)
            if response.status_code == 200:
                print("✅ Serveur prêt!")
                return True
        except:
            time.sleep(2)
            print(f"⏳ Attente du serveur... (tentative {i+1}/{max_retries})")
    raise Exception("Serveur non disponible après plusieurs tentatives")

def test_qr_flow():
    # Chemin absolu vers la clé privée
    private_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "private_key.pem")
    
    # Charger la clé privée
    with open(private_key_path, "rb") as f:
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
        
        # Chemin absolu pour le QR code généré
        qr_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "qr_ouali.png")
        
        with open(qr_path, "wb") as f:
            f.write(response.content)
        print(f"✅ QR code généré : {qr_path}")
        
        # 3. Vérification
        print("\n2. Vérification du QR code...")
        with open(qr_path, "rb") as f:
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
    try:
        # Démarrer le serveur avant les tests
        start_server()
        
        # Attendre un peu pour que le serveur ait le temps de démarrer
        time.sleep(3)
        
        # Exécuter les tests
        test_qr_flow()
        print("\n✅ Tous les tests ont réussi!")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")
        sys.exit(1)
    finally:
        # Arrêter le serveur (sera également appelé par atexit)
        stop_server()

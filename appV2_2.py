from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
import qrcode
import base64
import os
import uuid
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from pyzbar.pyzbar import decode
from PIL import Image
import time
from sqlalchemy.exc import OperationalError

# Initialisation de l'application
app = Flask(__name__)

# Configuration MySQL Docker
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://qr_user:qr_password@db/qr_secure?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy avec l'application
db = SQLAlchemy(app)

class QRCode(db.Model):
    __tablename__ = 'qr_codes'
    id = db.Column(db.String(36), primary_key=True)
    encrypted_data = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

def wait_for_db():
    """Attend que la base de données soit disponible"""
    max_retries = 5
    for _ in range(max_retries):
        try:
            with app.app_context():  # Contexte d'application explicite
                db.engine.connect()
            return True
        except OperationalError:
            time.sleep(5)
    return False

# Initialisation de la base de données
with app.app_context():
    if not wait_for_db():
        print("❌ Impossible de se connecter à la base de données")
        exit(1)
    db.create_all()

# Chargement de la clé publique
key_path = "public_key.pem"
try:
    with app.app_context():
        with open(key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
except FileNotFoundError:
    print(f"❌ Fichier {key_path} introuvable")
    exit(1)

@app.route('/generate', methods=['POST'])
def generate_qr():
    """Génère un QR code chiffré"""
    with app.app_context():  # Contexte pour les opérations DB
        data = request.json.get('data')
        if not data:
            return jsonify({"error": "Données manquantes"}), 400

        encrypted = public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        encrypted_b64 = base64.urlsafe_b64encode(encrypted).decode()

        qr_id = str(uuid.uuid4())
        new_qr = QRCode(
            id=qr_id,
            encrypted_data=encrypted_b64,
            expires_at=datetime.utcnow() + timedelta(days=request.json.get('expiration_days', 30))
        )
        
        db.session.add(new_qr)
        db.session.commit()

        img = qrcode.make(f"{qr_id}||{encrypted_b64}")
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

@app.route('/verify', methods=['POST'])
def verify_qr():
    """Vérifie un QR code scanné"""
    with app.app_context():  # Contexte pour les opérations DB
        img = Image.open(request.files['file'].stream)
        decoded = decode(img)
        if not decoded:
            return jsonify({"error": "Aucun QR code détecté"}), 400
            
        qr_id, encrypted_b64 = decoded[0].data.decode().split('||')
        
        qr = QRCode.query.get(qr_id)
        if not qr or qr.encrypted_data != encrypted_b64:
            return jsonify({"error": "QR invalide"}), 400
        
        return jsonify({
            "status": "valid",
            "encrypted_data": encrypted_b64,
            "qr_id": qr_id
        })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
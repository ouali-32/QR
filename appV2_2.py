from flask import Flask, request, jsonify, send_file, render_template
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/qr_secure?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# === Modèles ===

class QRCode(db.Model):
    __tablename__ = 'qr_codes'
    id = db.Column(db.String(36), primary_key=True)
    encrypted_data = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    encrypted_token = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# === Attente de la base de données (Docker startup) ===
def wait_for_db():
    max_retries = 5
    for _ in range(max_retries):
        try:
            with app.app_context():
                db.engine.connect()
            return True
        except OperationalError:
            time.sleep(5)
    return False

# === Initialisation DB ===
with app.app_context():
    if not wait_for_db():
        print("❌ Impossible de se connecter à la base de données")
        exit(1)
    db.create_all()

# === Chargement de la clé publique RSA ===
key_path = "C:\\Users\\ouali\\Desktop\\qr-app\\public_key.pem"
try:
    with open(key_path, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
except FileNotFoundError:
    print(f"❌ Fichier {key_path} introuvable")
    exit(1)

# === Interface Web (HTML) ===
@app.route('/')
def home():
    return render_template("index.html")

# === Routes API ===

@app.route('/generate', methods=['POST'])
def generate_qr():
    """Génère un QR code chiffré classique (non lié à un user)"""
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
    """Vérifie un QR code généré avec /generate"""
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

@app.route('/register', methods=['POST'])
def register():
    """Inscription d’un nouvel utilisateur avec génération de QR code de connexion"""
    username = request.form.get('username') or request.json.get('username')
    if not username:
        return jsonify({'error': 'Nom d’utilisateur requis'}), 400

    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({'error': 'Nom d’utilisateur déjà utilisé'}), 409

    token = f"USER:{username}:{str(uuid.uuid4())}"
    encrypted = public_key.encrypt(
        token.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    encrypted_b64 = base64.urlsafe_b64encode(encrypted).decode()

    user = User(username=username, encrypted_token=encrypted_b64)
    db.session.add(user)
    db.session.commit()

    img = qrcode.make(encrypted_b64)
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/login_qr', methods=['POST'])
def login_qr():
    """Connexion via scan de QR code utilisateur"""
    img = Image.open(request.files['file'].stream)
    decoded = decode(img)
    if not decoded:
        return jsonify({"error": "QR invalide"}), 400

    encrypted_b64 = decoded[0].data.decode()
    user = User.query.filter_by(encrypted_token=encrypted_b64).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    return jsonify({
        "status": "authenticated",
        "username": user.username,
        "user_id": user.id
    })

# === Lancement de l'application ===
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

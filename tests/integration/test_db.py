from appV2_2 import db, QRCode, app
from datetime import datetime, timedelta

def test_db_connection():
    with app.app_context():  # Contexte Flask obligatoire
        # 1. Création d'un QRCode de test
        qr = QRCode(
            id="test-id-123",
            encrypted_data="test-data-xyz",  # Chaîne fermée correctement
            expires_at=datetime.utcnow() + timedelta(days=1)  # Parenthèses fermées
        )  # Parenthèse fermée pour QRCode()

        # 2. Insertion en base
        db.session.add(qr)
        db.session.commit()

        # 3. Vérification
        assert QRCode.query.get("test-id-123") is not None  # Vérif avec le bon ID

        # 4. Nettoyage
        db.session.delete(qr)
        db.session.commit()
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Parenthèse fermante ajoutée

from appV2_2 import db, QRCode, app  # Import corrigé
from datetime import datetime, timedelta

def test_db_connection():
    with app.app_context():  # Contexte Flask requis
        # Test de création d'entrée
        qr = QRCode(
            id="test-id-123",
            encrypted_data="test-data-xyz",
            expires_at=datetime.utcnow() + timedelta(days=1)  # Parenthèse fermante ajoutée
        )  # Parenthèse fermante ajoutée
        
        db.session.add(qr)
        db.session.commit()
        
        # Vérification
        assert QRCode.query.get("test-id-123") is not None
        
        # Nettoyage
        db.session.delete(qr)
        db.session.commit()
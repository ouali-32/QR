# tests/integration/test_db.py
from appV2_2 import db, QRCode
from datetime import datetime, timedelta

def test_db_connection():
    # Test de création d'entrée
    qr = QRCode(
        id="test-id",
        encrypted_data="test-data",
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    
    db.session.add(qr)
    db.session.commit()
    
    # Vérification
    assert QRCode.query.get("test-id") is not None
    
    # Nettoyage
    db.session.delete(qr)
    db.session.commit()
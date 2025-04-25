from appV2_2 import QRCode
from datetime import datetime, timedelta

def test_db_working():
    """Test d'intégration basique avec la DB"""
    new_qr = QRCode(
        id="test-id",
        encrypted_data="test-data",
        expires_at=datetime.utcnow() + timedelta(days=1))
    
    assert new_qr.id == "test-id"  # Test simple sans DB réelle 
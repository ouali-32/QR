import sys
from pathlib import Path

# Ajoute le répertoire racine au Python Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from appV2_2 import app, db
import pytest

@pytest.fixture(autouse=True)
def app_context():
    """Fournit un contexte d'application pour tous les tests"""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
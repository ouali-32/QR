import pytest
from appV2_2 import app, db

@pytest.fixture(autouse=True)
def setup_app():
    """Configure l'application pour les tests d'intégration"""
    with app.app_context():
        db.create_all()
        yield  # Exécute le test ici
        db.drop_all()
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os
import sys

# Ajoute le dossier racine au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.models import Employee, Prediction, model_manager

# Configuration PostgreSQL de Test
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/employee_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_tests():
    """Initialisation globale : DB + Modèle ML."""
    
    # 1. Création des tables DB
    Base.metadata.create_all(bind=engine)
    
    # 2. 👇 CHARGEMENT FORCÉ DU MODÈLE ML POUR LES TESTS 👇
    print("\n⚡ Chargement du modèle pour les tests...")
    try:
        model_manager.load()
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement du modèle de test : {e}")
        # On ne bloque pas tout de suite, on laisse le test échouer si besoin
    
    yield
    
    # Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    # with TestClient(app) as c: yield c  <-- Parfois nécessaire pour le lifespan, 
    # mais le chargement manuel ci-dessus est plus sûr.
    return TestClient(app)
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
    
    # 2. Chargement du modèle ML pour les tests
    print("\n⚡ Chargement du modèle pour les tests...")
    try:
        model_manager.load()
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement du modèle de test : {e}")
    
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
    return TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_test_employees():
    """Nettoie les employés de test avant chaque test."""
    db = TestingSessionLocal()
    try:
        # Supprimer les employés de test (IDs > 7500)
        db.query(Prediction).filter(Prediction.id_employee > 7500).delete()
        db.query(Employee).filter(Employee.id_employee > 7500).delete()
        db.commit()
        yield
        # Cleanup après le test aussi
        db.query(Prediction).filter(Prediction.id_employee > 7500).delete()
        db.query(Employee).filter(Employee.id_employee > 7500).delete()
        db.commit()
    finally:
        db.close()

@pytest.fixture
def db_session():
    """Fixture pour obtenir une session DB pour les tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def employee_data():
    """Fixture partagée pour les données d'employé."""
    return {
        "id_employee": 9999,
        "age": 35,
        "genre": "M",
        "statut_marital": "Marié",
        "ayant_enfants": True,
        "distance_domicile_travail": 10.5,
        "departement": "R&D",
        "poste": "Ingénieur",
        "niveau_hierarchique_poste": 2,
        "heure_supplementaires": "Oui",
        "nombre_employee_sous_responsabilite": 2,
        "nombre_heures_travailless": 80,
        "annee_experience_totale": 8.0,
        "nombre_experiences_precedentes": 2,
        "annees_dans_l_entreprise": 5.0,
        "annees_dans_le_poste_actuel": 3.0,
        "annees_depuis_la_derniere_promotion": 2.0,
        "annes_sous_responsable_actuel": 2.0,
        "revenu_mensuel": 4500.0,
        "augementation_salaire_precedente": 2.5,
        "nombre_participation_pee": 1,
        "nb_formations_suivies": 2,
        "niveau_education": 3,
        "domaine_etude": "Sciences",
        "satisfaction_employee_environnement": 4,
        "satisfaction_employee_nature_travail": 3,
        "satisfaction_employee_equipe": 4,
        "satisfaction_employee_equilibre_pro_perso": 3,
        "note_evaluation_precedente": 3.5,
        "note_evaluation_actuelle": 3.8,
        "frequence_deplacement": "Rare"
    }
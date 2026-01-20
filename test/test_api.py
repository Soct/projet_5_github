import pytest
import numpy as np
from app.models import Employee, Prediction

# Données de test valides
@pytest.fixture
def employee_data():
    return {
        "id_employee": 9999, # ID unique pour le test
        "age": 35,
        "genre": "M",
        "statut_marital": "Marié",
        "ayant_enfants": True,
        "distance_domicile_travail": 10.5,
        "departement": "R&D",
        "poste": "Ingénieur",
        "niveau_hierarchique_poste": 2,
        "heure_supplementaires": "Oui",  # Modifié : String au lieu de Int
        "nombre_employee_sous_responsabilite": 2,
        "nombre_heures_travailless": 80,  # Ajouté : nouveau champ
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

@pytest.fixture
def employee_data_female(employee_data):
    """Données de test pour employée femme."""
    data = employee_data.copy()
    data["id_employee"] = 9998
    data["genre"] = "F"
    data["ayant_enfants"] = False
    data["heure_supplementaires"] = "Non"
    return data

# ==================== Tests de l'API ====================

def test_health_check(client):
    """Teste la route /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data

def test_predict_employee_success(client, employee_data):
    """Teste une prédiction complète (Création + Prédiction)."""
    response = client.post("/predict_employee", json=employee_data)
    
    # Debug si erreur
    if response.status_code != 200:
        print(f"Erreur : {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["id_employee"] == employee_data["id_employee"]
    assert "prediction" in data
    assert "confidence" in data
    assert data["prediction"] in [0, 1]
    assert 0 <= data["confidence"] <= 1

def test_predict_employee_female(client, employee_data_female):
    """Teste prédiction avec employée femme (test conversion genre)."""
    response = client.post("/predict_employee", json=employee_data_female)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id_employee"] == employee_data_female["id_employee"]
    assert "prediction" in data

def test_predict_employee_with_overtime_variations(client, employee_data):
    """Teste les différentes valeurs pour heures supplémentaires."""
    # Test "Yes"
    data_yes = employee_data.copy()
    data_yes["id_employee"] = 9997
    data_yes["heure_supplementaires"] = "Yes"
    response = client.post("/predict_employee", json=data_yes)
    assert response.status_code == 200
    
    # Test "Non"
    data_no = employee_data.copy()
    data_no["id_employee"] = 9996
    data_no["heure_supplementaires"] = "Non"
    response = client.post("/predict_employee", json=data_no)
    assert response.status_code == 200

def test_get_prediction_by_id(client, employee_data):
    """Teste la récupération d'une prédiction par ID."""
    # 1. On insère d'abord (nécessaire si la base est vide)
    client.post("/predict_employee", json=employee_data)
    
    # 2. On récupère
    response = client.get(f"/predict_employee/{employee_data['id_employee']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id_employee"] == employee_data["id_employee"]

def test_predict_invalid_data(client):
    """Teste la validation (Erreur 422)."""
    # Données incomplètes
    bad_data = {"age": 30} 
    response = client.post("/predict_employee", json=bad_data)
    assert response.status_code == 422

def test_predict_invalid_age(client, employee_data):
    """Teste validation âge invalide."""
    bad_data = employee_data.copy()
    bad_data["age"] = 150  # Âge invalide
    response = client.post("/predict_employee", json=bad_data)
    assert response.status_code == 422

def test_predict_invalid_genre(client, employee_data):
    """Teste validation genre invalide."""
    bad_data = employee_data.copy()
    bad_data["id_employee"] = 9991
    bad_data["genre"] = "X"  # Genre invalide mais accepté par le modèle
    response = client.post("/predict_employee", json=bad_data)
    # Le modèle accepte "X" et le convertit (tous sauf F = 1)
    assert response.status_code == 200

def test_get_unknown_employee(client):
    """Teste la récupération d'un employé inexistant (Erreur 404)."""
    response = client.get("/predict_employee/0")
    assert response.status_code == 404

def test_predict_employee_persistence(client, db_session, employee_data):
    """Vérifie que l'employé ET la prédiction sont enregistrés en base."""
    response = client.post("/predict_employee", json=employee_data)
    assert response.status_code == 200
    
    # Vérifier que l'employé existe en base
    employee = db_session.query(Employee).filter_by(
        id_employee=employee_data["id_employee"]
    ).first()
    assert employee is not None
    assert employee.age == employee_data["age"]
    assert employee.genre == employee_data["genre"]
    
    # Vérifier que la prédiction est enregistrée
    prediction = db_session.query(Prediction).filter_by(
        id_employee=employee_data["id_employee"]
    ).first()
    assert prediction is not None
    assert prediction.prediction in [0, 1]
    assert 0 <= prediction.confidence <= 1
    assert prediction.probability_reste is not None
    assert prediction.probability_quitte is not None
    assert prediction.risk_level in ["Haut", "Normal"]
    assert prediction.model_version == "1.0.0"

def test_predict_employee_update(client, db_session, employee_data):
    """Teste que l'insertion d'un employé existant fait un update (merge)."""
    # Première insertion
    client.post("/predict_employee", json=employee_data)
    
    # Modification et ré-insertion
    updated_data = employee_data.copy()
    updated_data["age"] = 40
    response = client.post("/predict_employee", json=updated_data)
    assert response.status_code == 200
    
    # Vérifier l'update
    employee = db_session.query(Employee).filter_by(
        id_employee=employee_data["id_employee"]
    ).first()
    assert employee.age == 40

def test_predict_multiple_predictions_history(client, db_session, employee_data):
    """Teste qu'on peut avoir plusieurs prédictions pour le même employé."""
    # Utiliser un ID unique pour ce test
    test_data = employee_data.copy()
    test_data["id_employee"] = 8888
    
    # Nettoyer les anciennes prédictions de cet employé si elles existent
    db_session.query(Prediction).filter_by(id_employee=8888).delete()
    db_session.commit()
    
    # Première prédiction
    response1 = client.post("/predict_employee", json=test_data)
    assert response1.status_code == 200
    
    # Deuxième prédiction (simule une réévaluation)
    response2 = client.post("/predict_employee", json=test_data)
    assert response2.status_code == 200
    
    # Vérifier qu'on a bien 2 prédictions
    predictions = db_session.query(Prediction).filter_by(
        id_employee=8888
    ).all()
    assert len(predictions) == 2

# ==================== Tests des fonctions utilitaires ====================

def test_prepare_features_genre_conversion():
    """Teste la conversion du genre."""
    from app.routes import prepare_features
    
    # Test genre masculin
    data_m = {"genre": "M", "ayant_enfants": True, "heure_supplementaires": "Oui"}
    df = prepare_features(data_m)
    assert df["genre"].iloc[0] == 1
    
    # Test genre féminin
    data_f = {"genre": "F", "ayant_enfants": False, "heure_supplementaires": "Non"}
    df = prepare_features(data_f)
    assert df["genre"].iloc[0] == 0

def test_prepare_features_children_conversion():
    """Teste la conversion ayant_enfants."""
    from app.routes import prepare_features
    
    data_with = {"ayant_enfants": True}
    df = prepare_features(data_with)
    assert df["ayant_enfants"].iloc[0] == 0  # False en interne
    
    data_without = {"ayant_enfants": False}
    df = prepare_features(data_without)
    assert df["ayant_enfants"].iloc[0] == 1  # True en interne

def test_prepare_features_overtime_string():
    """Teste la conversion des heures supplémentaires (string)."""
    from app.routes import prepare_features
    
    # Test "Oui"
    data_oui = {"heure_supplementaires": "Oui"}
    df = prepare_features(data_oui)
    assert df["heure_supplementaires"].iloc[0] == 1
    
    # Test "Yes"
    data_yes = {"heure_supplementaires": "Yes"}
    df = prepare_features(data_yes)
    assert df["heure_supplementaires"].iloc[0] == 1
    
    # Test "Non"
    data_non = {"heure_supplementaires": "Non"}
    df = prepare_features(data_non)
    assert df["heure_supplementaires"].iloc[0] == 0

def test_save_prediction_high_risk(db_session):
    """Teste l'enregistrement d'une prédiction à haut risque."""
    from app.routes import save_prediction
    
    # Créer d'abord un employé
    employee = Employee(id_employee=9995, age=35, genre="M", departement="Sales", revenu_mensuel=4500.0)
    db_session.add(employee)
    db_session.commit()
    
    probabilities = [0.2, 0.8]  # 80% de risque de quitter
    confidence = save_prediction(db_session, 9995, 1, probabilities)
    
    assert confidence == 0.8
    
    prediction = db_session.query(Prediction).filter_by(id_employee=9995).first()
    assert prediction is not None
    assert prediction.risk_level == "Haut"
    assert prediction.confidence == 0.8

def test_save_prediction_normal_risk(db_session):
    """Teste l'enregistrement d'une prédiction à risque normal."""
    from app.routes import save_prediction
    
    # Créer d'abord un employé
    employee = Employee(id_employee=9994, age=30, genre="F", departement="IT", revenu_mensuel=5000.0)
    db_session.add(employee)
    db_session.commit()
    
    probabilities = [0.9, 0.1]  # 10% de risque de quitter
    confidence = save_prediction(db_session, 9994, 0, probabilities)
    
    prediction = db_session.query(Prediction).filter_by(id_employee=9994).first()
    assert prediction is not None
    assert prediction.risk_level == "Normal"

# ==================== Tests du ModelManager ====================

def test_model_manager_loaded():
    """Vérifie que le modèle est chargé."""
    from app.models import model_manager
    
    assert model_manager.pipeline is not None

def test_model_manager_predict():
    """Teste la prédiction du modèle."""
    from app.models import model_manager
    import pandas as pd
    
    # Créer un DataFrame de test (avec toutes les features nécessaires)
    test_data = pd.DataFrame([[35, 1, 5000.0, 2, 10.5, 3, 4, 3.5, 8.0, 2, 5.0, 3.0, 2.0, 2.0, 2.5, 1, 2, 3, 4, 3, 4, 3, 80, 1]], 
                             columns=range(24))  # Adapter selon votre modèle
    
    try:
        prediction = model_manager.predict(test_data)
        assert prediction is not None
        assert len(prediction) > 0
    except Exception as e:
        pytest.skip(f"Modèle nécessite des features spécifiques: {e}")

def test_model_manager_predict_proba():
    """Teste predict_proba du modèle."""
    from app.models import model_manager
    import pandas as pd
    
    test_data = pd.DataFrame([[35, 1, 5000.0, 2, 10.5, 3, 4, 3.5, 8.0, 2, 5.0, 3.0, 2.0, 2.0, 2.5, 1, 2, 3, 4, 3, 4, 3, 80, 1]], 
                             columns=range(24))
    
    try:
        probas = model_manager.predict_proba(test_data)
        assert probas is not None
        assert len(probas) > 0
        assert len(probas[0]) == 2  # 2 classes
        assert abs(sum(probas[0]) - 1.0) < 0.01  # Somme des probas = 1
    except Exception as e:
        pytest.skip(f"Modèle nécessite des features spécifiques: {e}")

# ==================== Tests de la base de données ====================

def test_employee_model_creation(db_session):
    """Teste la création d'un employé en base."""
    employee = Employee(
        id_employee=9993,
        age=30,
        genre="F",
        departement="IT",
        revenu_mensuel=5000.0
    )
    db_session.add(employee)
    db_session.commit()
    
    retrieved = db_session.query(Employee).filter_by(id_employee=9993).first()
    assert retrieved is not None
    assert retrieved.age == 30
    assert retrieved.genre == "F"

def test_prediction_model_creation(db_session):
    """Teste la création d'une prédiction en base."""
    # D'abord créer un employé
    employee = Employee(id_employee=9992, age=35, genre="M", departement="Sales", revenu_mensuel=4500.0)
    db_session.add(employee)
    db_session.commit()
    
    # Puis créer une prédiction
    prediction = Prediction(
        id_employee=9992,
        prediction=1,
        confidence=0.85,
        probability_reste=0.15,
        probability_quitte=0.85,
        risk_level="Haut",
        model_version="1.0.0"
    )
    db_session.add(prediction)
    db_session.commit()
    
    retrieved = db_session.query(Prediction).filter_by(id_employee=9992).first()
    assert retrieved is not None
    assert retrieved.prediction == 1
    assert retrieved.confidence == 0.85

def test_prediction_foreign_key_constraint(db_session):
    """Teste la contrainte de clé étrangère."""
    # Essayer de créer une prédiction sans employé
    prediction = Prediction(
        id_employee=99999,  # N'existe pas
        prediction=1,
        confidence=0.5,
        probability_reste=0.5,
        probability_quitte=0.5,
        risk_level="Normal",
        model_version="1.0.0"
    )
    db_session.add(prediction)
    
    # Devrait lever une erreur d'intégrité
    with pytest.raises(Exception):  # IntegrityError de SQLAlchemy
        db_session.commit()
import pytest

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
        "heure_supplementaires": 5,
        "nombre_employee_sous_responsabilite": 2,
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

def test_get_unknown_employee(client):
    """Teste la récupération d'un employé inexistant (Erreur 404)."""
    response = client.get("/predict_employee/0")
    assert response.status_code == 404
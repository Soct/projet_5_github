"""Tests pour le module routes.py"""
import pytest
from app.routes import prepare_features, save_prediction
from app.models import Employee, Prediction


class TestPrepareFeatures:
    """Tests pour la fonction prepare_features."""
    
    def test_prepare_features_all_conversions(self):
        """Teste toutes les conversions de prepare_features."""
        data = {
            "genre": "F",
            "ayant_enfants": True,
            "heure_supplementaires": "Oui",
            "age": 30,
            "revenu_mensuel": 5000.0
        }
        df = prepare_features(data)
        
        assert df["genre"].iloc[0] == 0  # F = 0
        assert df["ayant_enfants"].iloc[0] == 0  # True devient 0
        assert df["heure_supplementaires"].iloc[0] == 1  # "Oui" = 1
        assert df["age"].iloc[0] == 30
        assert df["revenu_mensuel"].iloc[0] == 5000.0
    
    def test_prepare_features_genre_male(self):
        """Teste la conversion genre masculin."""
        data = {"genre": "M"}
        df = prepare_features(data)
        assert df["genre"].iloc[0] == 1
    
    def test_prepare_features_no_children(self):
        """Teste ayant_enfants = False."""
        data = {"ayant_enfants": False}
        df = prepare_features(data)
        assert df["ayant_enfants"].iloc[0] == 1
    
    def test_prepare_features_overtime_no(self):
        """Teste heures supplémentaires = Non."""
        data = {"heure_supplementaires": "non"}
        df = prepare_features(data)
        assert df["heure_supplementaires"].iloc[0] == 0
    
    def test_prepare_features_overtime_number(self):
        """Teste heures supplémentaires avec un nombre."""
        data = {"heure_supplementaires": 5}
        df = prepare_features(data)
        assert df["heure_supplementaires"].iloc[0] == 1
    
    def test_prepare_features_overtime_zero(self):
        """Teste heures supplémentaires = 0."""
        data = {"heure_supplementaires": 0}
        df = prepare_features(data)
        assert df["heure_supplementaires"].iloc[0] == 0
    
    def test_prepare_features_preserves_other_fields(self):
        """Teste que les autres champs sont préservés."""
        data = {
            "genre": "M",
            "ayant_enfants": True,
            "heure_supplementaires": "Oui",
            "custom_field": "test_value",
            "numeric_field": 42
        }
        df = prepare_features(data)
        
        assert "custom_field" in df.columns
        assert df["custom_field"].iloc[0] == "test_value"
        assert df["numeric_field"].iloc[0] == 42


class TestSavePrediction:
    """Tests pour la fonction save_prediction."""
    
    def test_save_prediction_returns_confidence(self, db_session):
        """Teste que save_prediction retourne la confidence."""
        # Créer un employé
        employee = Employee(
            id_employee=7774,
            age=40,
            genre="M",
            departement="Finance",
            revenu_mensuel=7000.0
        )
        db_session.add(employee)
        db_session.commit()
        
        probabilities = [0.3, 0.7]
        confidence = save_prediction(db_session, 7774, 1, probabilities)
        
        assert confidence == 0.7
    
    def test_save_prediction_risk_level_high(self, db_session):
        """Teste le calcul du risk_level pour haut risque."""
        employee = Employee(
            id_employee=7773,
            age=25,
            genre="F",
            departement="HR",
            revenu_mensuel=3500.0
        )
        db_session.add(employee)
        db_session.commit()
        
        # Prédiction = 1 et confidence > 0.7 => "Haut"
        probabilities = [0.15, 0.85]
        save_prediction(db_session, 7773, 1, probabilities)
        
        prediction = db_session.query(Prediction).filter_by(id_employee=7773).first()
        assert prediction.risk_level == "Haut"
    
    def test_save_prediction_risk_level_normal_low_confidence(self, db_session):
        """Teste le risk_level pour faible risque."""
        employee = Employee(
            id_employee=7772,
            age=45,
            genre="M",
            departement="Operations",
            revenu_mensuel=5500.0
        )
        db_session.add(employee)
        db_session.commit()
        
        # Prédiction = 1 mais confidence < 0.7 => "Normal"
        probabilities = [0.4, 0.6]
        save_prediction(db_session, 7772, 1, probabilities)
        
        prediction = db_session.query(Prediction).filter_by(id_employee=7772).first()
        assert prediction.risk_level == "Normal"
    
    def test_save_prediction_risk_level_normal_prediction_0(self, db_session):
        """Teste le risk_level pour prédiction = 0."""
        employee = Employee(
            id_employee=7771,
            age=50,
            genre="F",
            departement="Legal",
            revenu_mensuel=8000.0
        )
        db_session.add(employee)
        db_session.commit()
        
        # Prédiction = 0 => "Normal"
        probabilities = [0.95, 0.05]
        save_prediction(db_session, 7771, 0, probabilities)
        
        prediction = db_session.query(Prediction).filter_by(id_employee=7771).first()
        assert prediction.risk_level == "Normal"
    
    def test_save_prediction_stores_probabilities(self, db_session):
        """Teste que les probabilités sont bien enregistrées."""
        employee = Employee(
            id_employee=7770,
            age=33,
            genre="M",
            departement="Marketing",
            revenu_mensuel=4800.0
        )
        db_session.add(employee)
        db_session.commit()
        
        probabilities = [0.35, 0.65]
        save_prediction(db_session, 7770, 1, probabilities)
        
        prediction = db_session.query(Prediction).filter_by(id_employee=7770).first()
        assert prediction.probability_reste == 0.35
        assert prediction.probability_quitte == 0.65
    
    def test_save_prediction_stores_model_version(self, db_session):
        """Teste que la version du modèle est enregistrée."""
        employee = Employee(
            id_employee=7769,
            age=38,
            genre="F",
            departement="Quality",
            revenu_mensuel=5200.0
        )
        db_session.add(employee)
        db_session.commit()
        
        probabilities = [0.5, 0.5]
        save_prediction(db_session, 7769, 1, probabilities)
        
        prediction = db_session.query(Prediction).filter_by(id_employee=7769).first()
        assert prediction.model_version == "1.0.0"


class TestPredictByIdEdgeCases:
    """Tests pour les cas limites de predict_by_id."""
    
    def test_predict_by_id_with_special_characters(self, client, db_session, employee_data):
        """Teste la prédiction avec des caractères spéciaux dans les champs."""
        special_data = employee_data.copy()
        special_data["id_employee"] = 7768
        special_data["departement"] = "R&D"
        special_data["poste"] = "Chef d'équipe"
        
        # Créer l'employé
        response = client.post("/predict_employee", json=special_data)
        assert response.status_code == 200
        
        # Récupérer
        response = client.get(f"/predict_employee/7768")
        assert response.status_code == 200
    
    def test_predict_with_boundary_values(self, client, employee_data):
        """Teste avec des valeurs limites."""
        boundary_data = employee_data.copy()
        boundary_data["id_employee"] = 7767
        boundary_data["age"] = 18  # Valeur minimale
        boundary_data["revenu_mensuel"] = 0.01  # Très petit
        
        response = client.post("/predict_employee", json=boundary_data)
        assert response.status_code == 200

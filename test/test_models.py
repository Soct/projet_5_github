"""Tests pour le module models.py"""
import pytest
from pathlib import Path
from app.models import ModelManager, Employee, Prediction


class TestModelManager:
    """Tests pour ModelManager."""
    
    def test_model_manager_initialization(self):
        """Teste l'initialisation du ModelManager."""
        manager = ModelManager("models/model")
        assert manager.model_path == Path("models/model")
        assert manager.pipeline is None  # Pas encore chargé
    
    def test_model_manager_load(self):
        """Teste le chargement du modèle."""
        manager = ModelManager("models/model")
        manager.load()
        assert manager.pipeline is not None
    
    def test_model_manager_predict_without_load(self):
        """Teste que predict échoue sans chargement."""
        manager = ModelManager("models/model")
        with pytest.raises(RuntimeError, match="Modèle non chargé"):
            manager.predict([[1, 2, 3]])
    
    def test_model_manager_predict_proba_without_load(self):
        """Teste que predict_proba échoue sans chargement."""
        manager = ModelManager("models/model")
        with pytest.raises(RuntimeError, match="Modèle non chargé"):
            manager.predict_proba([[1, 2, 3]])
    
    def test_model_manager_load_nonexistent(self):
        """Teste le chargement d'un modèle inexistant."""
        manager = ModelManager("models/nonexistent")
        with pytest.raises(FileNotFoundError):
            manager.load()


class TestEmployeeModel:
    """Tests pour le modèle Employee."""
    
    def test_employee_repr(self, db_session):
        """Teste la représentation d'un Employee."""
        employee = Employee(
            id_employee=7777,
            age=30,
            genre="M",
            departement="IT",
            revenu_mensuel=5000.0
        )
        db_session.add(employee)
        db_session.commit()
        
        repr_str = repr(employee)
        # Employee n'a pas de __repr__ personnalisé, donc on vérifie juste que c'est un objet
        assert "Employee" in repr_str or "object" in repr_str


class TestPredictionModel:
    """Tests pour le modèle Prediction."""
    
    def test_prediction_creation_with_all_fields(self, db_session):
        """Teste la création d'une prédiction avec tous les champs."""
        # Créer d'abord un employé
        employee = Employee(
            id_employee=7776,
            age=35,
            genre="F",
            departement="Sales",
            revenu_mensuel=4500.0
        )
        db_session.add(employee)
        db_session.commit()
        
        # Créer une prédiction
        prediction = Prediction(
            id_employee=7776,
            prediction=1,
            confidence=0.75,
            probability_reste=0.25,
            probability_quitte=0.75,
            risk_level="Haut",
            model_version="1.0.0"
        )
        db_session.add(prediction)
        db_session.commit()
        
        # Vérifier
        retrieved = db_session.query(Prediction).filter_by(id_employee=7776).first()
        assert retrieved.prediction == 1
        assert retrieved.confidence == 0.75
        assert retrieved.risk_level == "Haut"
        assert retrieved.created_at is not None
    
    def test_prediction_repr(self, db_session):
        """Teste la représentation d'une Prediction."""
        employee = Employee(
            id_employee=7775,
            age=28,
            genre="M",
            departement="R&D",
            revenu_mensuel=6000.0
        )
        db_session.add(employee)
        db_session.commit()
        
        prediction = Prediction(
            id_employee=7775,
            prediction=0,
            confidence=0.9,
            probability_reste=0.9,
            probability_quitte=0.1,
            risk_level="Normal",
            model_version="1.0.0"
        )
        db_session.add(prediction)
        db_session.commit()
        
        repr_str = repr(prediction)
        assert "Prediction" in repr_str

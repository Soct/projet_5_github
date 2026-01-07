import pickle
from pathlib import Path
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class ModelManager:
    """Gestionnaire du modèle ML."""
    
    def __init__(self, model_path: str = "models/model.pkl"):
        self.model_path = Path(model_path)
        self.pipeline = None
    
    def load(self):
        """Charge le modèle en mémoire."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modèle non trouvé : {self.model_path}")
        
        with open(self.model_path, 'rb') as f:
            self.pipeline = pickle.load(f)
        
        print(f"✅ Modèle chargé depuis {self.model_path}")
    
    def predict(self, features):
        """Fait une prédiction."""
        if self.pipeline is None:
            raise RuntimeError("Modèle non chargé")
        
        return self.pipeline.predict(features)
    
    def predict_proba(self, features):
        """Retourne les probabilités pour chaque classe."""
        if self.pipeline is None:
            raise RuntimeError("Modèle non chargé")
        
        return self.pipeline.predict_proba(features)

# Instance globale
model_manager = ModelManager()

# --- Modèles SQLAlchemy ---

class Employee(Base):
    __tablename__ = "employees"
    
    id_employee = Column(Integer, primary_key=True, index=True)
    age = Column(Integer)
    genre = Column(String(1))
    statut_marital = Column(String(50))
    ayant_enfants = Column(Boolean)
    revenu_mensuel = Column(Float)
    departement = Column(String(100))
    poste = Column(String(100))
    niveau_hierarchique_poste = Column(Integer)
    nombre_experiences_precedentes = Column(Integer)
    annee_experience_totale = Column(Float)
    annees_dans_l_entreprise = Column(Float)
    annees_dans_le_poste_actuel = Column(Float)
    annees_depuis_la_derniere_promotion = Column(Float)
    annes_sous_responsable_actuel = Column(Float)
    satisfaction_employee_environnement = Column(Integer)
    satisfaction_employee_nature_travail = Column(Integer)
    satisfaction_employee_equipe = Column(Integer)
    satisfaction_employee_equilibre_pro_perso = Column(Integer)
    note_evaluation_precedente = Column(Float)
    note_evaluation_actuelle = Column(Float)
    heure_supplementaires = Column(Integer)
    augementation_salaire_precedente = Column(Float)
    nombre_participation_pee = Column(Integer)
    nb_formations_suivies = Column(Integer)
    nombre_employee_sous_responsabilite = Column(Integer)
    distance_domicile_travail = Column(Float)
    niveau_education = Column(Integer)
    domaine_etude = Column(String(100))
    frequence_deplacement = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    id_employee = Column(Integer, ForeignKey("employees.id_employee"), index=True)
    prediction = Column(Integer)
    confidence = Column(Float)
    risk_level = Column(String(20))
    probability_reste = Column(Float)
    probability_quitte = Column(Float)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
import pickle
import joblib
import os
from pathlib import Path
from huggingface_hub import hf_hub_download
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class ModelManager:
    """Gestionnaire du modèle ML."""
    
    def __init__(self, model_path: str = "models/model"):
        self.model_path = Path(model_path)
        self.pipeline = None
        self.hf_repo = os.getenv("HF_MODEL_REPO")  # Format: username/repo-name
    
    def load(self):
        """Charge le modèle en mémoire (depuis HF Hub si configuré, sinon local)."""
        # Si HF_MODEL_REPO est configuré et non vide, télécharger depuis HF Hub
        if self.hf_repo and self.hf_repo.strip():
            try:
                print(f"📥 Téléchargement du modèle depuis {self.hf_repo}...")
                model_file = hf_hub_download(
                    repo_id=self.hf_repo,
                    filename="model",
                    repo_type="model"
                )
                
                # Vérifier si c'est un pointeur Git LFS
                with open(model_file, 'rb') as f:
                    header = f.read(100)
                    if header.startswith(b'version https://git-lfs.github.com'):
                        raise ValueError(
                            "Le fichier téléchargé est un pointeur Git LFS, pas le modèle réel. "
                            "Vérifiez la configuration Git LFS sur Hugging Face."
                        )
                
                self.pipeline = joblib.load(model_file)
                print(f"✅ Modèle chargé depuis HF Hub: {self.hf_repo}")
                return
            except Exception as e:
                print(f"⚠️  Erreur téléchargement HF: {e}")
                print(f"⚠️  Basculement vers chargement local...")
        
        # Charger depuis le fichier local
        if not self.model_path.exists():
            # Créer le dossier models/ s'il n'existe pas
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            raise FileNotFoundError(
                f"Modèle non trouvé : {self.model_path}\n"
                f"Assurez-vous que le fichier existe ou configurez HF_MODEL_REPO correctement.\n"
                f"HF_MODEL_REPO actuel: {self.hf_repo or 'non configuré'}"
            )
        
        # Vérifier si le fichier local est un pointeur Git LFS
        with open(self.model_path, 'rb') as f:
            header = f.read(100)
            if header.startswith(b'version https://git-lfs.github.com'):
                raise ValueError(
                    f"Le fichier {self.model_path} est un pointeur Git LFS, pas le modèle réel.\n"
                    f"Exécutez: git lfs pull\n"
                    f"Contenu du fichier: {header.decode('utf-8', errors='ignore')}"
                )
        
        # Essayer de charger avec joblib (compatible avec scikit-learn)
        try:
            self.pipeline = joblib.load(self.model_path)
            print(f"✅ Modèle chargé depuis {self.model_path}")
        except (KeyError, ValueError, pickle.UnpicklingError) as e:
            # Fallback : essayer avec pickle si joblib échoue
            print(f"⚠️  Erreur joblib: {e}")
            print(f"⚠️  Tentative avec pickle...")
            try:
                with open(self.model_path, 'rb') as f:
                    self.pipeline = pickle.load(f)
                print(f"✅ Modèle chargé depuis {self.model_path} (pickle)")
            except Exception as e2:
                # Afficher les premiers octets pour le diagnostic
                with open(self.model_path, 'rb') as f:
                    first_bytes = f.read(200)
                    print(f"🔍 Premiers octets du fichier (hex): {first_bytes.hex()[:100]}")
                    print(f"🔍 Premiers octets du fichier (texte): {first_bytes[:100]}")
                
                raise RuntimeError(
                    f"Impossible de charger le modèle depuis {self.model_path}\n"
                    f"Erreur joblib: {e}\n"
                    f"Erreur pickle: {e2}\n"
                    f"Le modèle peut avoir été créé avec une version incompatible de Python/scikit-learn,\n"
                    f"ou le fichier est corrompu/pointeur Git LFS."
                ) from e2
    
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
    heure_supplementaires = Column(String(10))
    nombre_heures_travailless = Column(Integer)
    augementation_salaire_precedente = Column(Float)
    nombre_participation_pee = Column(Integer)
    nb_formations_suivies = Column(Integer)
    nombre_employee_sous_responsabilite = Column(Integer)
    distance_domicile_travail = Column(Float)
    niveau_education = Column(Integer)
    domaine_etude = Column(String(100))
    frequence_deplacement = Column(String(50))
    a_quitte_l_entreprise = Column(String(10))
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
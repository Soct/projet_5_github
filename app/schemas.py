from pydantic import BaseModel, Field, ConfigDict

class EmployeeInput(BaseModel):
    """Schéma pour les données d'un employé à prédire."""
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id_employee": 12345,
            "age": 35,
            "genre": "M",
            "statut_marital": "Marié",
            "ayant_enfants": True,
            "distance_domicile_travail": 25.5,
            "departement": "IT",
            "poste": "Développeur Senior",
            "niveau_hierarchique_poste": 3,
            "heure_supplementaires": "Oui",
            "nombre_employee_sous_responsabilite": 0,
            "nombre_heures_travailless": 80,
            "annee_experience_totale": 10.0,
            "nombre_experiences_precedentes": 2,
            "annees_dans_l_entreprise": 5.0,
            "annees_dans_le_poste_actuel": 2.0,
            "annees_depuis_la_derniere_promotion": 1.5,
            "annes_sous_responsable_actuel": 3.0,
            "revenu_mensuel": 3500.0,
            "augementation_salaire_precedente": 3.5,
            "nombre_participation_pee": 5,
            "nb_formations_suivies": 3,
            "niveau_education": 2,
            "domaine_etude": "Informatique",
            "satisfaction_employee_environnement": 4,
            "satisfaction_employee_nature_travail": 4,
            "satisfaction_employee_equipe": 5,
            "satisfaction_employee_equilibre_pro_perso": 3,
            "note_evaluation_precedente": 8.5,
            "note_evaluation_actuelle": 8.7,
            "frequence_deplacement": "Occasionnel"
        }
    })
    
    # Informations personnelles
    id_employee: int = Field(..., description="ID unique de l'employé")
    age: int = Field(..., ge=18, le=80, description="Âge de l'employé (18-80)")
    genre: str = Field(..., description="Genre (M ou F)")
    
    # Situation familiale et logement
    statut_marital: str = Field(..., description="Statut marital")
    ayant_enfants: bool = Field(..., description="A des enfants (true/false)")
    distance_domicile_travail: float = Field(..., ge=0, description="Distance domicile-travail en km")
    
    # Informations de poste actuel
    departement: str = Field(..., description="Département")
    poste: str = Field(..., description="Intitulé du poste")
    niveau_hierarchique_poste: int = Field(..., ge=1, description="Niveau hiérarchique (1-5)")
    heure_supplementaires: str = Field(..., description="Heures supplémentaires (Oui/Non)")
    nombre_employee_sous_responsabilite: int = Field(..., ge=0, description="Nombre d'employés sous responsabilité")
    nombre_heures_travailless: int = Field(..., ge=0, description="Nombre d'heures travaillées")
    
    # Expérience professionnelle
    annee_experience_totale: float = Field(..., ge=0, description="Années d'expérience totale")
    nombre_experiences_precedentes: int = Field(..., ge=0, description="Nombre de postes précédents")
    annees_dans_l_entreprise: float = Field(..., ge=0, description="Années dans l'entreprise")
    annees_dans_le_poste_actuel: float = Field(..., ge=0, description="Années dans le poste actuel")
    annees_depuis_la_derniere_promotion: float = Field(..., ge=0, description="Années depuis promotion")
    annes_sous_responsable_actuel: float = Field(..., ge=0, description="Années sous responsable")
    
    # Compensation et avantages
    revenu_mensuel: float = Field(..., ge=0, description="Salaire mensuel")
    augementation_salaire_precedente: float = Field(..., description="Augmentation précédente (%)")
    nombre_participation_pee: int = Field(..., ge=0, description="Participation PEE")
    
    # Formation et développement
    nb_formations_suivies: int = Field(..., ge=0, description="Formations suivies")
    niveau_education: int = Field(..., description="Niveau d'études (codé)")
    domaine_etude: str = Field(..., description="Domaine d'études")
    
    # Satisfaction et évaluation
    satisfaction_employee_environnement: int = Field(..., ge=1, le=5, description="Satisfaction environnement (1-5)")
    satisfaction_employee_nature_travail: int = Field(..., ge=1, le=5, description="Satisfaction travail (1-5)")
    satisfaction_employee_equipe: int = Field(..., ge=1, le=5, description="Satisfaction équipe (1-5)")
    satisfaction_employee_equilibre_pro_perso: int = Field(..., ge=1, le=5, description="Satisfaction équilibre (1-5)")
    note_evaluation_precedente: float = Field(..., ge=0, le=10, description="Évaluation précédente (0-10)")
    note_evaluation_actuelle: float = Field(..., ge=0, le=10, description="Évaluation actuelle (0-10)")
    
    # Mobilité
    frequence_deplacement: str = Field(..., description="Fréquence de déplacement")
    
    # Cible (optionnel - utilisé pour le training)
    a_quitte_l_entreprise: str | None = Field(None, description="A quitté l'entreprise (Oui/Non)")


class PredictionOutput(BaseModel):
    """Schéma pour la réponse de prédiction."""
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id_employee": 12345,
            "prediction": 0,
            "confidence": 0.92
        }
    })
    
    id_employee: int = Field(..., description="ID de l'employé")
    prediction: int = Field(..., description="Prédiction : 0 = reste, 1 = quitte")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance (0.0-1.0)")


class HealthResponse(BaseModel):
    """Schéma pour le healthcheck."""
    
    status: str = Field(..., description="État du service")
    model_loaded: bool = Field(..., description="Si le modèle est chargé")
    version: str = Field(..., description="Version du modèle")

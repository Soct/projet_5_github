from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from app.models import model_manager, Employee, Prediction
from app.schemas import EmployeeInput, PredictionOutput
from app.database import get_db

router = APIRouter(tags=["predictions"])

def save_prediction(db: Session, id_employee: int, prediction: int, probabilities: list):
    """Fonction utilitaire pour enregistrer le résultat en base."""
    confidence = float(np.max(probabilities))
    new_prediction = Prediction(
        id_employee=id_employee,
        prediction=int(prediction),
        confidence=confidence,
        probability_reste=float(probabilities[0]),
        probability_quitte=float(probabilities[1]),
        risk_level="Haut" if (prediction == 1 and confidence > 0.7) else "Normal",
        model_version="1.0.0"
    )
    db.add(new_prediction)
    db.commit()
    return confidence

def prepare_features(data_dict: dict) -> pd.DataFrame:
    """
    Prépare le DataFrame pour le modèle ML.
    """
    # 1. On travaille sur une copie
    features = data_dict.copy()
    

    if 'genre' in features:
        features['genre'] = 0 if features['genre'] == 'F' else 1
    
    if 'ayant_enfants' in features:
        features['ayant_enfants'] = 0 if features['ayant_enfants'] else 1
        
    if 'heure_supplementaires' in features:
        val = features['heure_supplementaires']
        # Conversion "Oui"/"Non" -> 1/0
        if isinstance(val, str):
            features['heure_supplementaires'] = 1 if val.strip().lower() in ['oui', 'yes'] else 0
        else:
            features['heure_supplementaires'] = 1 if (val and val > 0) else 0

    # 4. Création du DataFrame
    df = pd.DataFrame([features])
    
    return df

@router.post("/predict_employee", response_model=PredictionOutput)
async def predict_employee(data: EmployeeInput, db: Session = Depends(get_db)):
    try:
        # --- ÉTAPE 1 : Sauvegarde de l'employé ---
        # Conversion Pydantic -> Dict -> Objet SQLAlchemy
        employee_data = data.model_dump() 
        
        new_employee = Employee(**employee_data)
        
        db.merge(new_employee)
        db.commit()

        # --- ÉTAPE 2 : Prédiction ---
        # On utilise la fonction commune pour préparer les données
        df = prepare_features(employee_data)
        
        # Debug : Affiche les colonnes pour vérifier si ça correspond au modèle
        # print(f"Colonnes envoyées au modèle : {df.columns.tolist()}")

        prediction = model_manager.predict(df)[0]
        probabilities = model_manager.predict_proba(df)[0]
        
        # --- ÉTAPE 3 : Archivage ---
        confidence = save_prediction(db, data.id_employee, prediction, probabilities)
        
        return PredictionOutput(
            id_employee=data.id_employee,
            prediction=int(prediction),
            confidence=confidence
        )

    except Exception as e:
        db.rollback()
        print(f"\n🛑 ERREUR POST /predict_employee : {str(e)}") # S'affichera dans pytest -s
        raise HTTPException(status_code=400, detail=f"Erreur lors du traitement : {str(e)}")

@router.get("/predict_employee/{id_employee}", response_model=PredictionOutput)
async def predict_by_id(id_employee: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id_employee == id_employee).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employé non trouvé")

    try:
        # Conversion SQLAlchemy -> Dict
        # On exclut les champs techniques (metadata, created_at...)
        employee_dict = {
            col.name: getattr(employee, col.name) 
            for col in Employee.__table__.columns 
            if col.name != "created_at" # Exclure les dates/metadata non utilisées
        }

        # --- Prédiction ---
        # On réutilise EXACTEMENT la même fonction de préparation
        df = prepare_features(employee_dict)

        prediction = model_manager.predict(df)[0]
        probabilities = model_manager.predict_proba(df)[0]
        
        confidence = save_prediction(db, id_employee, prediction, probabilities)

        return PredictionOutput(
            id_employee=id_employee,
            prediction=int(prediction),
            confidence=confidence
        )
    except Exception as e:
        db.rollback()
        print(f"\n🛑 ERREUR GET /predict_employee/{id_employee} : {str(e)}") # S'affichera dans pytest -s
        raise HTTPException(status_code=500, detail=str(e))
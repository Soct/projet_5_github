from fastapi import APIRouter, HTTPException, status
import logging

from .schemas import PredictRequest, PredictResponse
from .models import predict as model_predict

logger = logging.getLogger(__name__)

router = APIRouter()



@router.post("/predict", response_model=PredictResponse, tags=["predictions"])
async def predict(request: PredictRequest):
    """
    Endpoint de prédiction
    
    Reçoit une liste de features et retourne une prédiction
    
    - **features**: Liste de valeurs numériques (floats ou ints)
    
    Returns:
        PredictResponse avec la prédiction et la confiance
    """
    try:
        logger.info(f"Prédiction reçue pour {len(request.features)} features")
        
        result = model_predict(request.features)
        
        logger.info(f"Prédiction effectuée: {result['prediction']}")
        
        return PredictResponse(
            prediction=result["prediction"],
            confidence=result.get("confidence")
        )
    
    except ValueError as ve:
        logger.error(f"Erreur de validation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la prédiction"
        )

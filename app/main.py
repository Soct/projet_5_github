from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.models import model_manager
from app.routes import router
from app.database import init_db

# Événement de démarrage
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code au démarrage
    print("🚀 Démarrage de l'API...")
    model_manager.load()  # ← Charger le modèle une seule fois
    init_db()
    yield
    # Code à l'arrêt
    print("🛑 Arrêt de l'API...")

# Créer l'app
app = FastAPI(
    title="Classification API",
    description="API de prédiction avec modèle XGBoost",
    version="1.0.0",
    lifespan=lifespan
)

# Inclure les routes
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API de classification"}

@app.get("/health")
def health_check():
    # On vérifie si le pipeline est chargé dans l'instance du manager
    is_loaded = model_manager.pipeline is not None
    
    return {
        "status": "ok", 
        "message": "API opérationnelle",
        "model_loaded": is_loaded,
        "version": "1.0.0" 
    }

# Pour lancer : uvicorn app.main:app --reload

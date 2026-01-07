from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# URL de la base de données
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:mysecretpassword@localhost:5432/employee_db"
)

# Créer le moteur
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

# Fonction pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
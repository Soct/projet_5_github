from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def wait_for_db(max_retries=30, delay=1):
    """Wait for database to be ready."""
    for attempt in range(max_retries):
        try:
            # Try to connect
            connection = engine.connect()
            connection.close()
            logger.info("✅ Base de données prête!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⏳ Attente de la base de données (tentative {attempt + 1}/{max_retries})...")
                time.sleep(delay)
            else:
                logger.error(f"❌ Impossible de se connecter à la base de données après {max_retries} tentatives")
                raise
    return False

def init_db():
    """Create all tables."""
    wait_for_db()
    Base.metadata.create_all(bind=engine)
"""Script de migration pour mettre à jour le schéma de la base de données."""
from sqlalchemy import text
from app.database import engine

def migrate_database():
    """Ajoute les colonnes manquantes à la table employees."""
    migrations = [
        # Ajouter nombre_heures_travailless si elle n'existe pas
        """
        ALTER TABLE employees 
        ADD COLUMN IF NOT EXISTS nombre_heures_travailless INTEGER;
        """,
        
        # Modifier heure_supplementaires en VARCHAR si c'est un INTEGER
        """
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'employees' 
                AND column_name = 'heure_supplementaires' 
                AND data_type = 'integer'
            ) THEN
                ALTER TABLE employees 
                ALTER COLUMN heure_supplementaires TYPE VARCHAR(10) 
                USING CASE 
                    WHEN heure_supplementaires = 1 THEN 'Oui'
                    WHEN heure_supplementaires = 0 THEN 'Non'
                    ELSE NULL 
                END;
            END IF;
        END $$;
        """,
        
        # Ajouter a_quitte_l_entreprise en VARCHAR si elle n'existe pas
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'employees' 
                AND column_name = 'a_quitte_l_entreprise'
            ) THEN
                ALTER TABLE employees 
                ADD COLUMN a_quitte_l_entreprise VARCHAR(10);
            END IF;
        END $$;
        """
    ]
    
    with engine.connect() as conn:
        for migration in migrations:
            try:
                conn.execute(text(migration))
                conn.commit()
                print(f"✅ Migration exécutée avec succès")
            except Exception as e:
                print(f"⚠️  Erreur migration: {e}")
                conn.rollback()
    
    print("✅ Migration terminée")

if __name__ == "__main__":
    migrate_database()

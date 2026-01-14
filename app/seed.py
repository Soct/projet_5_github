#!/usr/bin/env python3
"""
Script de seed pour importer/mettre à jour des données employés depuis un CSV.
Usage: python seed.py [--csv-file path/to/file.csv] [--update] [--batch-size 1000]
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier parent (racine du projet) au PYTHONPATH
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Remonte d'un niveau depuis app/
sys.path.insert(0, str(project_root))

# Maintenant les imports fonctionnent
import argparse
import pandas as pd
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import logging

# Importez vos modèles existants
from app.schemas import EmployeeInput 
# from your_database import Employee, engine  # Vos modèles SQLAlchemy

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmployeeSeeder:
    """Classe pour gérer l'import/mise à jour des données employés."""
    
    def __init__(self, database_url: str, batch_size: int = 1000):
        """
        Initialise le seeder.
        
        Args:
            database_url: URL de connexion à la base de données
            batch_size: Taille des lots pour l'insertion
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.batch_size = batch_size
        
    def validate_csv_data(self, df: pd.DataFrame) -> List[EmployeeInput]:
        """
        Valide les données du CSV avec Pydantic.
        
        Args:
            df: DataFrame pandas avec les données
            
        Returns:
            Liste des objets EmployeeInput validés
        """
        validated_data = []
        errors = []
        
        logger.info(f"Validation de {len(df)} enregistrements...")
        
        for index, row in df.iterrows():
            try:
                # Convertir la ligne en dictionnaire et nettoyer les NaN
                row_dict = row.to_dict()
                
                # Remplacer les NaN par None ou des valeurs par défaut
                for key, value in row_dict.items():
                    if pd.isna(value):
                        if key in ['ayant_enfants']:
                            row_dict[key] = False
                        elif isinstance(value, (int, float)):
                            row_dict[key] = 0
                        else:
                            row_dict[key] = None
                
                # Convertir ayant_enfants de Y/N à True/False
                if 'ayant_enfants' in row_dict and isinstance(row_dict['ayant_enfants'], str):
                    row_dict['ayant_enfants'] = row_dict['ayant_enfants'].strip().upper() == 'Y'
                
                # Nettoyer augementation_salaire_precedente (retirer le % et convertir en float)
                if 'augementation_salaire_precedente' in row_dict and isinstance(row_dict['augementation_salaire_precedente'], str):
                    row_dict['augementation_salaire_precedente'] = float(row_dict['augementation_salaire_precedente'].replace('%', '').strip())
                
                # Validation avec Pydantic
                employee = EmployeeInput(**row_dict)
                validated_data.append(employee)
                
            except ValidationError as e:
                error_msg = f"Ligne {index + 1}: {e}"
                errors.append(error_msg)
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Ligne {index + 1}: Erreur inattendue - {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Validation terminée: {len(validated_data)} valides, {len(errors)} erreurs")
        
        if errors:
            logger.warning("Erreurs de validation détectées:")
            for error in errors[:10]:  # Afficher les 10 premières erreurs
                logger.warning(f"  {error}")
            if len(errors) > 10:
                logger.warning(f"  ... et {len(errors) - 10} autres erreurs")
        
        return validated_data
    
    def insert_employees(self, employees: List[EmployeeInput], update_existing: bool = False):
        """
        Insère ou met à jour les employés en base.
        
        Args:
            employees: Liste des employés validés
            update_existing: Si True, met à jour les enregistrements existants
        """
        session = self.SessionLocal()
        
        try:
            total_inserted = 0
            total_updated = 0
            total_errors = 0
            
            # Traitement par lots
            for i in range(0, len(employees), self.batch_size):
                batch = employees[i:i + self.batch_size]
                logger.info(f"Traitement du lot {i//self.batch_size + 1} ({len(batch)} enregistrements)")
                
                for employee in batch:
                    try:
                        if update_existing:
                            # Vérifier si l'employé existe
                            existing = session.execute(
                                text("SELECT id_employee FROM employees WHERE id_employee = :id"),
                                {"id": employee.id_employee}
                            ).fetchone()
                            
                            if existing:
                                # Mise à jour
                                self._update_employee(session, employee)
                                total_updated += 1
                            else:
                                # Insertion
                                self._insert_employee(session, employee)
                                total_inserted += 1
                        else:
                            # Insertion uniquement
                            self._insert_employee(session, employee)
                            total_inserted += 1
                            
                    except SQLAlchemyError as e:
                        logger.error(f"Erreur SQL pour employé {employee.id_employee}: {e}")
                        total_errors += 1
                        session.rollback()
                        continue
                
                # Commit du lot
                session.commit()
                logger.info(f"Lot {i//self.batch_size + 1} traité avec succès")
            
            logger.info(f"Import terminé: {total_inserted} insérés, {total_updated} mis à jour, {total_errors} erreurs")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def _insert_employee(self, session, employee: EmployeeInput):
        """Insère un nouvel employé."""
        # Exemple d'insertion SQL brute (adaptez selon votre modèle)
        insert_query = text("""
            INSERT INTO employees (
                id_employee, age, genre, statut_marital, ayant_enfants,
                distance_domicile_travail, departement, poste, niveau_hierarchique_poste,
                heure_supplementaires, nombre_employee_sous_responsabilite, nombre_heures_travailless,
                annee_experience_totale, nombre_experiences_precedentes,
                annees_dans_l_entreprise, annees_dans_le_poste_actuel,
                annees_depuis_la_derniere_promotion, annes_sous_responsable_actuel,
                revenu_mensuel, augementation_salaire_precedente, nombre_participation_pee,
                nb_formations_suivies, niveau_education, domaine_etude,
                satisfaction_employee_environnement, satisfaction_employee_nature_travail,
                satisfaction_employee_equipe, satisfaction_employee_equilibre_pro_perso,
                note_evaluation_precedente, note_evaluation_actuelle, frequence_deplacement,
                a_quitte_l_entreprise
            ) VALUES (
                :id_employee, :age, :genre, :statut_marital, :ayant_enfants,
                :distance_domicile_travail, :departement, :poste, :niveau_hierarchique_poste,
                :heure_supplementaires, :nombre_employee_sous_responsabilite, :nombre_heures_travailless,
                :annee_experience_totale, :nombre_experiences_precedentes,
                :annees_dans_l_entreprise, :annees_dans_le_poste_actuel,
                :annees_depuis_la_derniere_promotion, :annes_sous_responsable_actuel,
                :revenu_mensuel, :augementation_salaire_precedente, :nombre_participation_pee,
                :nb_formations_suivies, :niveau_education, :domaine_etude,
                :satisfaction_employee_environnement, :satisfaction_employee_nature_travail,
                :satisfaction_employee_equipe, :satisfaction_employee_equilibre_pro_perso,
                :note_evaluation_precedente, :note_evaluation_actuelle, :frequence_deplacement,
                :a_quitte_l_entreprise
            )
        """)
        
        session.execute(insert_query, employee.model_dump())
    
    def _update_employee(self, session, employee: EmployeeInput):
        """Met à jour un employé existant."""
        update_query = text("""
            UPDATE employees SET
                age = :age, genre = :genre, statut_marital = :statut_marital,
                ayant_enfants = :ayant_enfants, distance_domicile_travail = :distance_domicile_travail,
                departement = :departement, poste = :poste, niveau_hierarchique_poste = :niveau_hierarchique_poste,
                heure_supplementaires = :heure_supplementaires,
                nombre_employee_sous_responsabilite = :nombre_employee_sous_responsabilite,
                nombre_heures_travailless = :nombre_heures_travailless,
                annee_experience_totale = :annee_experience_totale,
                nombre_experiences_precedentes = :nombre_experiences_precedentes,
                annees_dans_l_entreprise = :annees_dans_l_entreprise,
                annees_dans_le_poste_actuel = :annees_dans_le_poste_actuel,
                annees_depuis_la_derniere_promotion = :annees_depuis_la_derniere_promotion,
                annes_sous_responsable_actuel = :annes_sous_responsable_actuel,
                revenu_mensuel = :revenu_mensuel, augementation_salaire_precedente = :augementation_salaire_precedente,
                nombre_participation_pee = :nombre_participation_pee, nb_formations_suivies = :nb_formations_suivies,
                niveau_education = :niveau_education, domaine_etude = :domaine_etude,
                satisfaction_employee_environnement = :satisfaction_employee_environnement,
                satisfaction_employee_nature_travail = :satisfaction_employee_nature_travail,
                satisfaction_employee_equipe = :satisfaction_employee_equipe,
                satisfaction_employee_equilibre_pro_perso = :satisfaction_employee_equilibre_pro_perso,
                note_evaluation_precedente = :note_evaluation_precedente,
                note_evaluation_actuelle = :note_evaluation_actuelle,
                frequence_deplacement = :frequence_deplacement,
                a_quitte_l_entreprise = :a_quitte_l_entreprise
            WHERE id_employee = :id_employee
        """)
        
        session.execute(update_query, employee.model_dump())
    
    def get_stats(self) -> dict:
        """Retourne des statistiques sur la base de données."""
        session = self.SessionLocal()
        try:
            result = session.execute(text("SELECT COUNT(*) as total FROM employees")).fetchone()
            return {"total_employees": result.total if result else 0}
        finally:
            session.close()


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Import/mise à jour des données employés depuis CSV")
    parser.add_argument("--csv-file", default="employees.csv", help="Chemin vers le fichier CSV")
    parser.add_argument("--update", action="store_true", help="Met à jour les enregistrements existants")
    parser.add_argument("--batch-size", type=int, default=1000, help="Taille des lots pour l'insertion")
    parser.add_argument("--database-url", default="sqlite:///employees.db", help="URL de la base de données")
    parser.add_argument("--dry-run", action="store_true", help="Validation uniquement, sans insertion")
    
    args = parser.parse_args()
    
    # Vérifier que le fichier CSV existe
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        logger.error(f"Fichier CSV non trouvé: {csv_path}")
        sys.exit(1)
    
    try:
        # Charger le CSV
        logger.info(f"Chargement du fichier CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"CSV chargé: {len(df)} lignes, {len(df.columns)} colonnes")
        
        # Initialiser le seeder
        logger.info("Initialisation du seeder...")
        seeder = EmployeeSeeder(args.database_url, args.batch_size)
        logger.info("Seeder initialisé avec succès")
        
        # Afficher les stats avant
        logger.info("Récupération des statistiques avant import...")
        #stats_before = seeder.get_stats()
        #logger.info(f"Employés en base avant import: {stats_before['total_employees']}")
        
        # Valider les données
        validated_employees = seeder.validate_csv_data(df)
        
        if not validated_employees:
            logger.error("Aucune donnée valide trouvée. Arrêt du processus.")
            sys.exit(1)
        
        if args.dry_run:
            logger.info(f"Mode dry-run: {len(validated_employees)} enregistrements seraient traités")
            return
        
        # Insérer/mettre à jour les données
        seeder.insert_employees(validated_employees, args.update)
        
        # Afficher les stats après
        stats_after = seeder.get_stats()
        logger.info(f"Employés en base après import: {stats_after['total_employees']}")
        
        logger.info("Import terminé avec succès!")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

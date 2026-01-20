# API de Prédiction de Turnover - Système de Classification ML

API RESTful développée avec FastAPI pour prédire le risque de départ des employés en utilisant un modèle XGBoost. L'application intègre une base de données PostgreSQL pour le stockage et le logging des prédictions, et est containerisée avec Docker pour faciliter le déploiement.

## Table des matières

- [Architecture du Projet](#architecture-du-projet)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Base de Données](#base-de-données)
- [Utilisation de l'API](#utilisation-de-lapi)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Sécurité](#sécurité)
- [Gestion des Données](#gestion-des-données)

---

## Architecture du Projet

### Structure des fichiers

```
projet_5_github/
├── app/                          # Code source de l'application
│   ├── main.py                   # Point d'entrée FastAPI avec lifespan
│   ├── api.py                    # Configuration de l'API
│   ├── routes.py                 # Endpoints de prédiction
│   ├── models.py                 # Modèles SQLAlchemy
│   ├── schemas.py                # Schémas Pydantic (validation)
│   ├── database.py               # Configuration DB avec retry logic
│   ├── seed.py                   # Script d'initialisation des données
│   └── migrate.py                # Gestion des migrations
├── database/
│   └── schema.sql                # Schéma PostgreSQL avec relations
├── models/
│   └── model                     # Modèle XGBoost entraîné
├── test/
│   ├── conftest.py               # Configuration pytest
│   └── test_api.py               # Tests unitaires et fonctionnels
├── .github/workflows/
│   └── ci.yml                    # Pipeline CI/CD automatisé
├── docker-compose.yml            # Orchestration des services
├── Dockerfile                    # Image de l'application
├── pyproject.toml                # Dépendances et configuration Python
└── README.md                     # Documentation

```

### Stack Technique

- **API Framework** : FastAPI 0.128+ (async, haute performance)
- **ML Framework** : XGBoost 3.0.0 + scikit-learn 1.7.2
- **Base de données** : PostgreSQL 16-alpine
- **ORM** : SQLAlchemy 2.0+ avec modèles déclaratifs
- **Validation** : Pydantic 2.12+ pour la sécurité des données
- **Tests** : Pytest 9.0+ avec couverture de code
- **Containerisation** : Docker + Docker Compose
- **Gestionnaire de paquets** : UV (build moderne et rapide)
- **CI/CD** : GitHub Actions

---

## Prérequis

### Système requis

- **Docker** : version 20.10+
- **Docker Compose** : version 2.0+
- **Python** : 3.12+ (pour développement local)
- **UV** : gestionnaire de paquets (installation automatique via Docker)

### Ports utilisés

- `5432` : PostgreSQL
- `8000` : API FastAPI

---

## Installation

### Option 1 : Installation avec Docker (Recommandée)

Cette méthode garantit un environnement isolé et reproductible.

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-username/projet_5_github.git
cd projet_5_github

# 2. Vérifier que PostgreSQL local n'utilise pas le port 5432
sudo systemctl stop postgresql  # Si installé localement
sudo systemctl disable postgresql

# 3. Lancer tous les services (DB + API + Seed)
docker compose up -d

# 4. Vérifier que les services sont actifs
docker compose ps

# 5. Consulter les logs
docker compose logs -f app
```

**L'API sera accessible sur** : http://localhost:7860

### Option 2 : Installation locale (Développement)

```bash
# 1. Installer UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Créer un environnement virtuel et installer les dépendances
uv sync

# 3. Démarrer PostgreSQL (avec Docker ou localement)
docker run -d \
  --name postgres_dev \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=employee_db \
  -p 5432:5432 \
  postgres:16-alpine

# 4. Initialiser la base de données
uv run python -c "from app.database import init_db; init_db()"

# 5. Charger les données
uv run python app/seed.py --csv-file data_merge.csv --update \
  --database-url postgresql://postgres:mysecretpassword@localhost:5432/employee_db

# 6. Lancer l'API
uv run uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

---

## Configuration

### Gestion des environnements

Le projet supporte plusieurs environnements via des variables d'environnement :

#### Développement (local)

```env
# .env.development
DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/employee_db
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

#### Test (CI/CD)

Les tests utilisent automatiquement un service PostgreSQL isolé dans GitHub Actions :

```yaml
services:
  db:
    image: postgres:16-alpine
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: mysecretpassword
      POSTGRES_DB: employee_db_test
```

#### Production

Variables gérées via secrets Docker/Kubernetes :

```env
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Gestion des secrets

**Sécurité des credentials :**

1. **Jamais** de secrets dans le code source
2. Utilisation de variables d'environnement
3. Secrets stockés dans GitHub Actions Secrets
4. Hachage bcrypt pour les mots de passe utilisateurs
5. Connexions DB avec certificats SSL en production

**Secrets requis pour le CI/CD :**

```bash
# Dans GitHub Settings > Secrets and variables > Actions
HF_TOKEN=hf_xxxxxxxxxxxxx
HF_USERNAME=votre-username
HF_SPACE_NAME=nom-du-space
DB_PASSWORD=mot-de-passe-sécurisé
```

---

## Base de Données

### Architecture des données

Le système utilise PostgreSQL avec deux tables principales :

#### Table `employees`

Stocke les caractéristiques complètes des employés :

```sql
CREATE TABLE employees (
    id_employee SERIAL PRIMARY KEY,
    age INT NOT NULL CHECK (age >= 18 AND age <= 100),
    genre VARCHAR(1) NOT NULL CHECK (genre IN ('M', 'F')),
    statut_marital VARCHAR(50),
    ayant_enfants BOOLEAN,
    revenu_mensuel FLOAT CHECK (revenu_mensuel > 0),
    departement VARCHAR(100),
    poste VARCHAR(100),
    -- ... 25+ autres champs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_genre CHECK (genre IN ('M', 'F'))
);
```

**Contraintes d'intégrité** :
- Clé primaire auto-incrémentée
- Validation des types (âge, genre, revenu)
- Timestamps automatiques
- Index sur `id_employee` pour performances

#### Table `predictions`

Enregistre chaque interaction utilisateur avec le modèle ML :

```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    id_employee INT NOT NULL,
    prediction INT NOT NULL CHECK (prediction IN (0, 1)),
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    risk_level VARCHAR(20),
    probability_reste FLOAT,
    probability_quitte FLOAT,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_employee) REFERENCES employees(id_employee) 
        ON DELETE CASCADE
);
```

**Relations** :
- Clé étrangère vers `employees` avec CASCADE
- Permet de tracker l'historique complet des prédictions
- Indexé sur `id_employee` et `created_at` pour les requêtes analytiques

### Schéma relationnel

```
┌─────────────────┐         ┌──────────────────┐
│   employees     │ 1     ∞ │   predictions    │
├─────────────────┤◄────────┤──────────────────┤
│ id_employee (PK)│         │ id (PK)          │
│ age             │         │ id_employee (FK) │
│ genre           │         │ prediction       │
│ departement     │         │ confidence       │
│ ...             │         │ created_at       │
└─────────────────┘         └──────────────────┘
```

### Initialisation de la base

Le script `database/schema.sql` est exécuté automatiquement au démarrage du conteneur PostgreSQL :

```yaml
# docker-compose.yml
db:
  image: postgres:16-alpine
  volumes:
    - ./database/schema.sql:/docker-entrypoint-initdb.d/init.sql
```

### Injection des données

Le script `app/seed.py` permet d'importer/mettre à jour les données depuis CSV :

```bash
# Chargement initial
uv run ./app/seed.py \
  --csv-file data_merge.csv \
  --database-url postgresql://postgres:mysecretpassword@db:5432/employee_db

# Mise à jour (upsert)
uv run ./app/seed.py \
  --csv-file data_merge.csv \
  --update \
  --batch-size 1000 \
  --database-url postgresql://postgres:mysecretpassword@db:5432/employee_db
```

**Fonctionnalités du seeder** :
- Validation Pydantic des données avant insertion
- Gestion des erreurs avec retry logic (30 tentatives)
- Insertion par batch pour performance
- Mode upsert (update si existe)
- Logging détaillé des opérations

### Gestion du volume et performances

**Scalabilité** :
- Index sur colonnes fréquemment requêtées
- Partitionnement par date possible pour `predictions`
- Connection pooling via SQLAlchemy (pool_pre_ping=True)
- Batch processing (1000 enregistrements/lot)

**Volumétrie actuelle** :
- ~1470 employés
---

## Utilisation de l'API

### Documentation interactive

FastAPI génère automatiquement une documentation OpenAPI :

- **Swagger UI** : http://localhost:7860/docs
- **ReDoc** : http://localhost:7860/redoc

### Endpoints disponibles

#### 1. Racine de l'API

```bash
GET /

# Réponse
{
  "message": "Bienvenue sur l'API de classification"
}
```

#### 2. Prédiction pour un nouvel employé

```bash
POST /predict_employee

# Headers
Content-Type: application/json

# Body (exemple complet)
{
  "id_employee": 123,
  "age": 35,
  "genre": "M",
  "statut_marital": "Married",
  "ayant_enfants": true,
  "revenu_mensuel": 5000.0,
  "departement": "Sales",
  "poste": "Manager",
  "niveau_hierarchique_poste": 3,
  "heure_supplementaires": "Yes",
  "distance_domicile_travail": 10.5,
  "annees_dans_l_entreprise": 5.0,
  "satisfaction_employee_environnement": 4,
  "note_evaluation_actuelle": 3.5,
  ...
}

# Réponse
{
  "id_employee": 123,
  "prediction": 1,
  "confidence": 0.87
}
```

**Codes de retour** :
- `200` : Prédiction réussie
- `400` : Données invalides (validation Pydantic)
- `500` : Erreur serveur

#### 3. Prédiction par ID employé existant

```bash
GET /predict_employee/{id_employee}

# Exemple
curl http://localhost:7860/predict_employee/42

# Réponse
{
  "id_employee": 42,
  "prediction": 0,
  "confidence": 0.92
}
```

**Codes de retour** :
- `200` : Employé trouvé et prédit
- `404` : Employé non trouvé
- `500` : Erreur serveur

### Validation des données

Toutes les entrées sont validées par Pydantic avant traitement :

```python
# app/schemas.py
class EmployeeInput(BaseModel):
    id_employee: int
    age: int = Field(ge=18, le=100)
    genre: str = Field(pattern=r'^[MF]$')
    revenu_mensuel: float = Field(gt=0)
    # ... autres validations
```

**Erreurs de validation** :

```json
{
  "detail": [
    {
      "loc": ["body", "age"],
      "msg": "ensure this value is greater than or equal to 18",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

### Logging des interactions

Chaque prédiction est automatiquement enregistrée dans la table `predictions` :

```python
# app/routes.py
def save_prediction(db, id_employee, prediction, probabilities):
    new_prediction = Prediction(
        id_employee=id_employee,
        prediction=int(prediction),
        confidence=float(np.max(probabilities)),
        probability_reste=float(probabilities[0]),
        probability_quitte=float(probabilities[1]),
        risk_level="Haut" if prediction == 1 else "Normal",
        model_version="1.0.0"
    )
    db.add(new_prediction)
    db.commit()
```

---

## Tests

### Framework de tests

Le projet utilise **Pytest** avec couverture de code automatique :

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-report=html"
testpaths = ["test"]
python_files = "test_*.py"
```

### Exécution des tests

```bash
# Tous les tests avec couverture
uv run pytest

# Tests spécifiques
uv run pytest test/test_api.py::test_predict_employee

# Mode verbose
uv run pytest -v -s

# Rapport de couverture HTML
uv run pytest --cov-report=html
# Ouvrir htmlcov/index.html
```

### Cas de tests couverts

#### Tests unitaires

```python
# test/test_api.py
def test_predict_employee_valid_data(client):
    """Test prédiction avec données valides"""
    response = client.post("/predict_employee", json=valid_employee)
    assert response.status_code == 200
    assert "prediction" in response.json()

def test_predict_employee_invalid_age(client):
    """Test validation âge < 18"""
    response = client.post("/predict_employee", json={
        "age": 15,  # Invalide
        ...
    })
    assert response.status_code == 422
```

#### Tests fonctionnels

```python
def test_prediction_persistence(client, db):
    """Vérifie que la prédiction est enregistrée en base"""
    response = client.post("/predict_employee", json=valid_employee)
    
    # Vérifier en base
    prediction = db.query(Prediction).filter_by(
        id_employee=valid_employee["id_employee"]
    ).first()
    assert prediction is not None
    assert prediction.confidence > 0
```

#### Tests d'intégrité

```python
def test_database_constraints(db):
    """Test des contraintes DB (FK, CHECK, etc.)"""
    with pytest.raises(IntegrityError):
        # Tentative d'insertion avec FK invalide
        db.add(Prediction(id_employee=99999, ...))
        db.commit()
```

### Couverture de code

**Objectif** : > 80% de couverture

```bash
# Après exécution des tests
Name                  Stmts   Miss  Cover   Missing
---------------------------------------------------
app/api.py               12      0   100%
app/database.py          45      3    93%   67-69
app/models.py            38      2    95%
app/routes.py            87      5    94%   45, 78, 102
app/schemas.py           25      0   100%
---------------------------------------------------
TOTAL                   207     10    95%
```

### Tests dans le pipeline CI/CD

Les tests s'exécutent automatiquement sur chaque push/PR :

```yaml
# .github/workflows/ci.yml
jobs:
  tests:
    runs-on: ubuntu-latest
    services:
      db:  # PostgreSQL isolé pour les tests
        image: postgres:16-alpine
        options: --health-cmd pg_isready
    steps:
      - run: uv run pytest
```

---

## Déploiement

### Pipeline CI/CD automatisé

Le projet utilise **GitHub Actions** pour l'intégration et le déploiement continus :

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ "master" ]
  pull_request:
    branches: [ "master" ]

jobs:
  tests:
    # 1. Exécution des tests avec PostgreSQL
    # 2. Validation du code
    # 3. Rapport de couverture

  sync-to-hub:
    needs: tests  # Déploiement seulement si tests OK
    # 1. Synchronisation vers Hugging Face Spaces
    # 2. Déploiement automatique
```

### Workflow de déploiement

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Git Push    │─────►│ Run Tests    │─────►│ Deploy to HF │
│  (master)    │      │ (pytest)     │      │ Spaces       │
└──────────────┘      └──────────────┘      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ Tests Failed │
                      │ Stop Pipeline│
                      └──────────────┘
```

### Déploiement automatique sur Hugging Face Spaces

L'application est déployée automatiquement sur Hugging Face Spaces après validation des tests unitaires :

**Architecture de production** :
- **Frontend/API** : Hugging Face Spaces (Docker)
- **Base de données** : Supabase (PostgreSQL hébergé)
- **Déclenchement** : Push sur branche `master` après succès des tests

**Workflow automatisé** :

```yaml
# .github/workflows/ci.yml
jobs:
  tests:
    # 1. Exécution des tests avec PostgreSQL
    
  sync-to-hub:
    needs: tests  # Ne s'exécute que si tests passent
    steps:
      - name: Synchroniser vers HF Space
        run: |
          git clone https://$HF_USERNAME:$HF_TOKEN@huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME
          # Copie des fichiers et push automatique
```

**Configuration requise** :

Secrets GitHub nécessaires :
- `HF_TOKEN` : Token d'authentification Hugging Face
- `HF_USERNAME` : Nom d'utilisateur HF
- `HF_SPACE_NAME` : Nom du Space

Variables d'environnement Hugging Face Space :
```bash
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/postgres
ENVIRONMENT=production
```

**Avantages de Supabase** :
- Base de données PostgreSQL gérée
- Backups automatiques
- Scaling automatique
- Interface d'administration
- API REST générée automatiquement

---

## Sécurité

### Authentification et contrôle d'accès

#### Méthodes implémentées

1. **Variables d'environnement sécurisées**
   ```python
   # app/database.py
   DATABASE_URL = os.getenv("DATABASE_URL", "")
   # Jamais de credentials hardcodés
   ```

 

2. **Validation stricte des entrées**
   - Pydantic valide toutes les données
   - Prévention des injections SQL via SQLAlchemy ORM
   - Typage fort (Python 3.12+)

### Bonnes pratiques de sécurité

**Gestion des secrets** :
- Variables d'environnement pour les credentials
- Fichier `.env` exclu du contrôle de version (`.gitignore`)
- Secrets GitHub Actions pour le CI/CD
- Secrets Hugging Face pour la production

**Sécurité de la base de données** :
- Connexions PostgreSQL via variables d'environnement
- Pas de credentials hardcodés dans le code
- Supabase en production (connexions SSL, backups automatiques)
- Connection pooling avec `pool_pre_ping=True`

**Validation des données** :
- Validation stricte via schémas Pydantic
- Contraintes CHECK dans PostgreSQL
- Typage fort Python 3.12+
- Prévention des injections SQL via SQLAlchemy ORM


**Notes importantes** :
- L'application actuelle n'implémente pas d'authentification utilisateur
- Les mots de passe de base de données sont gérés via variables d'environnement
- En production sur HF Spaces, la connexion Supabase utilise SSL

---

## Gestion des Données

### Processus de stockage

#### 1. Ingestion des données

```
CSV Source ──► Validation Pydantic ──► Batch Processing ──► PostgreSQL
                      │                      │
                      ▼                      ▼
              Error Logging         Transaction Commit
```

**Script d'ingestion** :
```bash
uv run ./app/seed.py \
  --csv-file data_merge.csv \
  --update \
  --batch-size 1000 \
  --database-url postgresql://postgres:mysecretpassword@db:5432/employee_db
```

**Validation automatique** :
- Typage strict des colonnes
- Vérification des contraintes métier
- Rejet des doublons

#### 2. Stockage des prédictions

Chaque appel API → Insertion automatique dans `predictions` :

```sql
INSERT INTO predictions (
    id_employee, prediction, confidence, 
    probability_reste, probability_quitte, model_version
) VALUES (...);
```

### Processus de traitement

#### Pipeline de données

```
┌─────────────┐   ┌──────────────┐   ┌─────────────┐
│  Employees  │──►│  FastAPI     │──►│ Predictions │
│  (Input)    │   │  Processing  │   │ (Output)    │
└─────────────┘   └──────────────┘   └─────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ XGBoost Model│
                  │  Inference   │
                  └──────────────┘
```

#### Transformation des données

```python
# app/routes.py - prepare_features()
1. Conversion genre (F→0, M→1)
2. Normalisation booléens
3. Encodage variables catégorielles
4. Création DataFrame pandas
5. Prédiction XGBoost
```

### Besoins analytiques

#### Tableaux de bord suggérés

**1. Dashboard RH - Monitoring du turnover**

```sql
-- Taux de risque par département
SELECT 
    e.departement,
    COUNT(*) as total_predictions,
    SUM(CASE WHEN p.prediction = 1 THEN 1 ELSE 0 END) as at_risk,
    ROUND(AVG(p.confidence), 2) as avg_confidence
FROM predictions p
JOIN employees e ON p.id_employee = e.id_employee
WHERE p.created_at >= NOW() - INTERVAL '30 days'
GROUP BY e.departement
ORDER BY at_risk DESC;
```

**2. Dashboard Analytique - Performance du modèle**

```sql
-- Évolution de la confiance du modèle
SELECT 
    DATE(created_at) as date,
    AVG(confidence) as avg_confidence,
    COUNT(*) as predictions_count
FROM predictions
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**3. Dashboard Opérationnel - Employés à risque**

```sql
-- Liste des employés high-risk à contacter
SELECT 
    e.id_employee,
    e.departement,
    e.poste,
    e.annees_dans_l_entreprise,
    p.confidence as risk_score,
    p.created_at as derniere_evaluation
FROM employees e
JOIN predictions p ON e.id_employee = p.id_employee
WHERE p.prediction = 1 
  AND p.confidence > 0.75
  AND p.id = (
      SELECT MAX(id) FROM predictions WHERE id_employee = e.id_employee
  )
ORDER BY p.confidence DESC;
```

### Maintenance et archivage

#### Stratégie de rétention

```sql
-- Archivage des anciennes prédictions (>1 an)
CREATE TABLE predictions_archive (
    LIKE predictions INCLUDING ALL
);

INSERT INTO predictions_archive 
SELECT * FROM predictions 
WHERE created_at < NOW() - INTERVAL '1 year';

DELETE FROM predictions 
WHERE created_at < NOW() - INTERVAL '1 year';
```

#### Backup automatisé

```bash
# Script de backup journalier
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -h localhost -U postgres employee_db | gzip > backup_$DATE.sql.gz
```

---

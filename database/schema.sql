-- Schéma de base de données pour l'application de prédiction
-- PostgreSQL

-- Table des employés (snapshot pour chaque prédiction)
CREATE TABLE IF NOT EXISTS employees (
    id_employee SERIAL PRIMARY KEY,
    age INT NOT NULL,
    genre VARCHAR(1) NOT NULL,
    statut_marital VARCHAR(50),
    ayant_enfants BOOLEAN,
    revenu_mensuel FLOAT,
    departement VARCHAR(100),
    poste VARCHAR(100),
    niveau_hierarchique_poste INT,
    nombre_experiences_precedentes INT,
    annee_experience_totale FLOAT,
    annees_dans_l_entreprise FLOAT,
    annees_dans_le_poste_actuel FLOAT,
    annees_depuis_la_derniere_promotion FLOAT,
    annes_sous_responsable_actuel FLOAT,
    satisfaction_employee_environnement INT,
    satisfaction_employee_nature_travail INT,
    satisfaction_employee_equipe INT,
    satisfaction_employee_equilibre_pro_perso INT,
    note_evaluation_precedente FLOAT,
    note_evaluation_actuelle FLOAT,
    heure_supplementaires VARCHAR(10),
    nombre_heures_travailless INT,
    augementation_salaire_precedente FLOAT,
    nombre_participation_pee INT,
    nb_formations_suivies INT,
    nombre_employee_sous_responsabilite INT,
    distance_domicile_travail FLOAT,
    niveau_education INT,
    domaine_etude VARCHAR(100),
    frequence_deplacement VARCHAR(50),
    a_quitte_l_entreprise VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des prédictions
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    id_employee INT NOT NULL,
    prediction INT NOT NULL,
    confidence FLOAT NOT NULL,
    risk_level VARCHAR(20),
    probability_reste FLOAT,
    probability_quitte FLOAT,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_employee) REFERENCES employees(id_employee)
);

-- Table d'audit (pour tracking)
CREATE TABLE IF NOT EXISTS prediction_audit (
    id SERIAL PRIMARY KEY,
    prediction_id INT NOT NULL,
    action VARCHAR(50),
    user_id VARCHAR(100),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

-- Index pour performance
CREATE INDEX idx_predictions_employee ON predictions(id_employee);
CREATE INDEX idx_predictions_created ON predictions(created_at);
CREATE INDEX idx_predictions_confidence ON predictions(confidence);
CREATE INDEX idx_audit_prediction ON prediction_audit(prediction_id);

-- Vue pour les statistiques
CREATE OR REPLACE VIEW prediction_stats AS
SELECT
    COUNT(*) as total_predictions,
    AVG(confidence) as avg_confidence,
    ROUND(100.0 * SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as churn_rate,
    MIN(created_at) as first_prediction,
    MAX(created_at) as last_prediction
FROM predictions;

-- Vue pour les prédictions par département
CREATE OR REPLACE VIEW predictions_by_department AS
SELECT
    e.departement,
    COUNT(p.id) as total_predictions,
    SUM(CASE WHEN p.prediction = 1 THEN 1 ELSE 0 END) as churn_predictions,
    ROUND(100.0 * SUM(CASE WHEN p.prediction = 1 THEN 1 ELSE 0 END) / COUNT(p.id), 2) as churn_percentage,
    AVG(p.confidence) as avg_confidence
FROM predictions p
JOIN employees e ON p.id_employee = e.id_employee
GROUP BY e.departement
ORDER BY churn_predictions DESC;

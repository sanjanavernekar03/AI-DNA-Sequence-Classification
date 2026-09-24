-- ==============================================================================
-- AI-POWERED DNA SEQUENCE CLASSIFICATION AND PREDICTION SYSTEM
-- Database Schema Definition (MySQL)
-- ==============================================================================
-- ------------------------------------------------------------------------------
-- 
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    date_of_birth DATE NULL,
    gender TEXT NULL,
    phone TEXT NULL,
    country TEXT NULL,
    state TEXT NULL,
    city VARCHAR(255) NULL,
    address TEXT NULL,
    postal_code TEXT NULL,
    latitude REAL NULL,
    longitude REAL NULL,
    blood_group VARCHAR(10) NULL,
    height REAL NULL,
    weight REAL NULL,
    role VARCHAR(255) DEFAULT 'researcher',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS dna_sequences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sequence_name TEXT NOT NULL,
    sequence TEXT NOT NULL,
    sequence_length INTEGER NOT NULL,
    source_type VARCHAR(255) DEFAULT 'manual', -- 'manual', 'fasta_upload', 'sample'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- 

-- ------------------------------------------------------------------------------
--
-- ------------------------------------------------------------------------------
-- ---------------------------
CREATE TABLE IF NOT EXISTS classification_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sequence_id INTEGER DEFAULT NULL,
    sequence_name VARCHAR(255) DEFAULT 'DNA Sequence',
    model_name VARCHAR(255) NOT NULL DEFAULT 'RandomForestClassifier_kmer',
    predicted_class TEXT NOT NULL,
    confidence REAL NOT NULL,
    features_json TEXT DEFAULT NULL,
    probabilities_json TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sequence_id) REFERENCES dna_sequences(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------------------------
-- 
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS disease_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sequence_id INTEGER DEFAULT NULL,
    sequence_name VARCHAR(255) DEFAULT 'DNA Sequence',
    model_name VARCHAR(255) NOT NULL DEFAULT 'GenomicRiskGradientBoosting',
    predicted_category TEXT NOT NULL,
    probability REAL NOT NULL,
    risk_category TEXT NOT NULL, -- 'Low', 'Moderate', 'High', 'Elevated'
    features_json TEXT DEFAULT NULL,
    probabilities_json TEXT DEFAULT NULL,
    disclaimer_notice TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sequence_id) REFERENCES dna_sequences(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------------------------
-- 
CREATE TABLE IF NOT EXISTS visualizations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sequence_id INTEGER DEFAULT NULL,
    sequence_name VARCHAR(255) DEFAULT 'DNA Sequence',
    visualization_type TEXT NOT NULL,
    chart_config_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sequence_id) REFERENCES dna_sequences(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS complete_analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sequence_id INTEGER DEFAULT NULL,
    reference_sequence_id INTEGER DEFAULT NULL,
    sequence_name TEXT NOT NULL,
    status VARCHAR(255) DEFAULT 'COMPLETED', -- 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'
    sequence_analysis_id INTEGER DEFAULT NULL,
    similarity_analysis_id INTEGER DEFAULT NULL,
    mutation_analysis_id INTEGER DEFAULT NULL,
    classification_id INTEGER DEFAULT NULL,
    disease_prediction_id INTEGER DEFAULT NULL,
    summary_metrics_json TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sequence_id) REFERENCES dna_sequences(id) ON DELETE SET NULL,
    FOREIGN KEY (reference_sequence_id) REFERENCES dna_sequences(id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    report_uuid VARCHAR(255) NOT NULL UNIQUE,
    analysis_id INTEGER DEFAULT NULL,
    analysis_type TEXT NOT NULL, -- 'sequence', 'similarity', 'mutation', 'classification', 'disease', 'visualization', 'complete'
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS hospitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    external_place_id VARCHAR(255) NULL UNIQUE,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(255) NULL,
    state TEXT NULL,
    country TEXT NULL,
    postal_code TEXT NULL,
    latitude REAL NULL,
    longitude REAL NULL,
    phone TEXT NULL,
    opening_hours TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    specialty VARCHAR(255) NOT NULL,
    qualification TEXT NOT NULL,
    experience_years INTEGER NOT NULL DEFAULT 5,
    availability_days VARCHAR(255) NOT NULL DEFAULT 'Monday - Friday',
    available_slots_json TEXT NOT NULL,
    consultation_type VARCHAR(255) NOT NULL DEFAULT 'In-person & Video',
    photo_url TEXT NULL,
    is_demo_data INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- 
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    hospital_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time VARCHAR(255) NOT NULL,
    reason_for_visit TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    patient_email VARCHAR(255) NOT NULL,
    phone TEXT NOT NULL,
    notes TEXT NULL,
    consultation_fee DECIMAL(10,2) NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'Confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
--
CREATE TABLE IF NOT EXISTS health_guidance_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    health_problem TEXT NOT NULL,
    language VARCHAR(255) DEFAULT 'en',
    guidance_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
--
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_seq_user ON dna_sequences (user_id);
CREATE INDEX idx_seq_created ON dna_sequences (created_at);
CREATE INDEX idx_clf_user ON classification_results (user_id);
CREATE INDEX idx_dis_user ON disease_predictions (user_id);
CREATE INDEX idx_vis_user ON visualizations (user_id);
CREATE INDEX idx_cmp_user ON complete_analyses (user_id);
CREATE INDEX idx_rep_user ON reports (user_id);
CREATE INDEX idx_rep_uuid ON reports (report_uuid);
CREATE INDEX idx_hosp_city ON hospitals (city);
CREATE INDEX idx_hosp_place ON hospitals (external_place_id);
CREATE INDEX idx_doc_hosp ON doctors (hospital_id);
CREATE INDEX idx_doc_spec ON doctors (specialty);
CREATE INDEX idx_appt_user ON appointments (user_id);
CREATE INDEX idx_appt_doc_date ON appointments (doctor_id, appointment_date, appointment_time);
CREATE INDEX idx_hgh_user ON health_guidance_history (user_id);
CREATE INDEX idx_chat_user ON chat_history (user_id);

-- ================================================================


CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(150) NOT NULL DEFAULT 'Admin',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS admin_activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT,
    action VARCHAR(255) NOT NULL,
    target_type VARCHAR(255),
    target_id INT,
    details TEXT,
    ip_address VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS admin_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(150) NOT NULL UNIQUE,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

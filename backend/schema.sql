-- AutoGST Pro — PostgreSQL Schema
-- Run this ONLY if you prefer manual setup over SQLAlchemy auto-create

CREATE DATABASE autogst_pro;
\c autogst_pro;

-- ENUMS
CREATE TYPE user_role AS ENUM ('admin', 'user', 'accountant');
CREATE TYPE transaction_type AS ENUM ('income', 'expense');
CREATE TYPE gst_type AS ENUM ('CGST', 'SGST', 'IGST', 'UTGST', 'exempt');
CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'critical');

-- USERS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'user' NOT NULL,
    gstin VARCHAR(15),
    pan VARCHAR(10),
    business_name VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- CATEGORIES
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type transaction_type NOT NULL,
    gst_rate NUMERIC(5,2) DEFAULT 0.0,
    hsn_sac_code VARCHAR(20),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- UPLOADED FILES
CREATE TABLE uploaded_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    content_type VARCHAR(100),
    ocr_text TEXT,
    ocr_status VARCHAR(50) DEFAULT 'pending',
    ocr_confidence FLOAT,
    parsed_data JSONB,
    parsing_method VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TRANSACTIONS
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id),
    file_id INTEGER REFERENCES uploaded_files(id),
    description TEXT NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    transaction_type transaction_type NOT NULL,
    transaction_date DATE NOT NULL,
    gst_type gst_type DEFAULT 'CGST',
    gst_rate NUMERIC(5,2) DEFAULT 0.0,
    cgst_amount NUMERIC(15,2) DEFAULT 0.0,
    sgst_amount NUMERIC(15,2) DEFAULT 0.0,
    igst_amount NUMERIC(15,2) DEFAULT 0.0,
    total_gst NUMERIC(15,2) DEFAULT 0.0,
    taxable_amount NUMERIC(15,2) DEFAULT 0.0,
    total_amount NUMERIC(15,2) DEFAULT 0.0,
    party_name VARCHAR(255),
    party_gstin VARCHAR(15),
    invoice_number VARCHAR(100),
    hsn_sac_code VARCHAR(20),
    ml_category VARCHAR(100),
    ml_confidence FLOAT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score FLOAT,
    source VARCHAR(50) DEFAULT 'manual',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- ALERTS
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity alert_severity DEFAULT 'info',
    category VARCHAR(100),
    is_read BOOLEAN DEFAULT FALSE,
    related_transaction_id INTEGER REFERENCES transactions(id),
    alert_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- GST RETURNS
CREATE TABLE gst_returns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    return_type VARCHAR(20) NOT NULL,
    period_month INTEGER NOT NULL,
    period_year INTEGER NOT NULL,
    total_taxable_value NUMERIC(15,2) DEFAULT 0.0,
    total_cgst NUMERIC(15,2) DEFAULT 0.0,
    total_sgst NUMERIC(15,2) DEFAULT 0.0,
    total_igst NUMERIC(15,2) DEFAULT 0.0,
    total_tax NUMERIC(15,2) DEFAULT 0.0,
    net_gst_liability NUMERIC(15,2) DEFAULT 0.0,
    input_tax_credit NUMERIC(15,2) DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'draft',
    report_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- TAX CALCULATIONS
CREATE TABLE tax_calculations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_year VARCHAR(10) NOT NULL,
    regime VARCHAR(20) NOT NULL,
    gross_income NUMERIC(15,2) DEFAULT 0.0,
    salary_income NUMERIC(15,2) DEFAULT 0.0,
    business_income NUMERIC(15,2) DEFAULT 0.0,
    other_income NUMERIC(15,2) DEFAULT 0.0,
    standard_deduction NUMERIC(15,2) DEFAULT 0.0,
    section_80c NUMERIC(15,2) DEFAULT 0.0,
    section_80d NUMERIC(15,2) DEFAULT 0.0,
    section_80g NUMERIC(15,2) DEFAULT 0.0,
    hra_exemption NUMERIC(15,2) DEFAULT 0.0,
    total_deductions NUMERIC(15,2) DEFAULT 0.0,
    taxable_income NUMERIC(15,2) DEFAULT 0.0,
    income_tax NUMERIC(15,2) DEFAULT 0.0,
    surcharge NUMERIC(15,2) DEFAULT 0.0,
    cess NUMERIC(15,2) DEFAULT 0.0,
    total_tax_liability NUMERIC(15,2) DEFAULT 0.0,
    effective_tax_rate FLOAT DEFAULT 0.0,
    calculation_details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- INDEXES
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_is_read ON alerts(is_read);
CREATE INDEX idx_uploaded_files_user_id ON uploaded_files(user_id);

-- SAMPLE CATEGORIES INSERT
INSERT INTO categories (name, type, gst_rate, hsn_sac_code) VALUES
    ('Sales Revenue', 'income', 18.00, '9999'),
    ('Consulting Income', 'income', 18.00, '9983'),
    ('Product Sales', 'income', 12.00, '8471'),
    ('Office Rent', 'expense', 18.00, '9972'),
    ('Software & Tools', 'expense', 18.00, '8523'),
    ('Salaries & Payroll', 'expense', 0.00, NULL),
    ('Travel & Transport', 'expense', 5.00, '9964'),
    ('Marketing', 'expense', 18.00, '9983'),
    ('Office Supplies', 'expense', 12.00, '4820'),
    ('Professional Services', 'expense', 18.00, '9982')
ON CONFLICT (name) DO NOTHING;

-- init.sql
-- Create Database Schema for Pharmaceutical Analytics

-- 1. Drugs Table - Core pharmaceutical products
CREATE TABLE IF NOT EXISTS drugs (
    drug_id SERIAL PRIMARY KEY,
    drug_code VARCHAR(20) UNIQUE NOT NULL,
    drug_name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    manufacturer VARCHAR(150) NOT NULL,
    drug_class VARCHAR(100),
    category VARCHAR(50) CHECK (category IN ('Prescription', 'OTC', 'Controlled')),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price > 0),
    cost_price DECIMAL(10,2),
    stock_quantity INT NOT NULL DEFAULT 0,
    min_stock_level INT DEFAULT 10,
    max_stock_level INT DEFAULT 1000,
    expiry_date DATE,
    storage_conditions VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Sales Table - Pharmacy sales transactions
CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    drug_id INT REFERENCES drugs(drug_id) ON DELETE RESTRICT,
    sale_date DATE NOT NULL,
    sale_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    pharmacy_id INT NOT NULL,
    pharmacy_name VARCHAR(150),
    salesperson_id INT,
    payment_method VARCHAR(30) CHECK (payment_method IN ('Cash', 'Credit Card', 'Insurance', 'Digital')),
    insurance_provider VARCHAR(100),
    prescription_id VARCHAR(50)
);

-- 3. Patients Table - Patient demographics (simplified)
CREATE TABLE IF NOT EXISTS patients (
    patient_id SERIAL PRIMARY KEY,
    patient_code VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    age INT GENERATED ALWAYS AS (EXTRACT(YEAR FROM age(CURRENT_DATE, date_of_birth))) STORED,
    gender VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    email VARCHAR(150),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    primary_condition VARCHAR(200),
    insurance_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Prescriptions Table - Doctor prescriptions
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    prescription_code VARCHAR(50) UNIQUE NOT NULL,
    patient_id INT REFERENCES patients(patient_id) ON DELETE CASCADE,
    drug_id INT REFERENCES drugs(drug_id) ON DELETE RESTRICT,
    doctor_name VARCHAR(200) NOT NULL,
    doctor_license VARCHAR(100),
    hospital_clinic VARCHAR(200),
    date_prescribed DATE NOT NULL,
    date_dispensed DATE,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    duration_days INT NOT NULL,
    refills_allowed INT DEFAULT 0,
    refills_used INT DEFAULT 0,
    status VARCHAR(20) CHECK (status IN ('Active', 'Completed', 'Cancelled', 'Expired')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Inventory Transactions - Track stock movements
CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id SERIAL PRIMARY KEY,
    drug_id INT REFERENCES drugs(drug_id) ON DELETE RESTRICT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_type VARCHAR(20) CHECK (transaction_type IN ('Purchase', 'Sale', 'Return', 'Adjustment', 'Transfer', 'Expired')),
    quantity_change INT NOT NULL,
    previous_quantity INT,
    new_quantity INT,
    reference_id VARCHAR(100),
    reference_type VARCHAR(50),
    performed_by INT,
    notes TEXT
);

-- 6. Suppliers Table - Drug manufacturers/suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(150),
    email VARCHAR(150),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    lead_time_days INT DEFAULT 7,
    reliability_rating DECIMAL(3,2) CHECK (reliability_rating BETWEEN 0 AND 5),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Data Quality Logs - For monitoring pipeline
CREATE TABLE IF NOT EXISTS data_quality_logs (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    quality_check VARCHAR(200) NOT NULL,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    records_checked INT,
    issues_found INT,
    issue_details JSONB,
    status VARCHAR(20) CHECK (status IN ('Pass', 'Fail', 'Warning')),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_drug_name ON drugs (drug_name);
CREATE INDEX IF NOT EXISTS idx_manufacturer ON drugs (manufacturer);
CREATE INDEX IF NOT EXISTS idx_category ON drugs (category);
CREATE INDEX IF NOT EXISTS idx_expiry_date ON drugs (expiry_date);

CREATE INDEX IF NOT EXISTS idx_sale_date ON sales (sale_date);
CREATE INDEX IF NOT EXISTS idx_pharmacy_id ON sales (pharmacy_id);
CREATE INDEX IF NOT EXISTS idx_sale_drug_id ON sales (drug_id);
CREATE INDEX IF NOT EXISTS idx_payment_method ON sales (payment_method);

CREATE INDEX IF NOT EXISTS idx_patient_name ON patients (last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_city_state ON patients (city, state);
CREATE INDEX IF NOT EXISTS idx_age ON patients (age);

CREATE INDEX IF NOT EXISTS idx_prescription_patient_id ON prescriptions (patient_id);
CREATE INDEX IF NOT EXISTS idx_prescription_drug_id ON prescriptions (drug_id);
CREATE INDEX IF NOT EXISTS idx_date_prescribed ON prescriptions (date_prescribed);
CREATE INDEX IF NOT EXISTS idx_status ON prescriptions (status);

CREATE INDEX IF NOT EXISTS idx_inventory_drug_id ON inventory_transactions (drug_id);
CREATE INDEX IF NOT EXISTS idx_transaction_date ON inventory_transactions (transaction_date);
CREATE INDEX IF NOT EXISTS idx_transaction_type ON inventory_transactions (transaction_type);

-- Function to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_last_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for drugs table
CREATE TRIGGER update_drugs_last_updated BEFORE UPDATE ON drugs
    FOR EACH ROW EXECUTE FUNCTION update_last_updated_column();

-- View for low stock alert
CREATE OR REPLACE VIEW low_stock_alert AS
SELECT 
    d.drug_id,
    d.drug_code,
    d.drug_name,
    d.manufacturer,
    d.stock_quantity,
    d.min_stock_level,
    d.unit_price,
    ROUND((d.stock_quantity * 100.0 / d.min_stock_level), 2) as stock_percentage,
    CASE 
        WHEN d.stock_quantity <= d.min_stock_level THEN 'CRITICAL'
        WHEN d.stock_quantity <= (d.min_stock_level * 1.5) THEN 'LOW'
        ELSE 'OK'
    END as stock_status
FROM drugs d
WHERE d.stock_quantity <= (d.min_stock_level * 1.5)
ORDER BY stock_percentage ASC;

-- View for monthly sales summary
CREATE OR REPLACE VIEW monthly_sales_summary AS
SELECT 
    DATE_TRUNC('month', s.sale_date) as month,
    COUNT(DISTINCT s.sale_id) as total_transactions,
    COUNT(DISTINCT s.drug_id) as unique_drugs_sold,
    SUM(s.quantity) as total_quantity_sold,
    SUM(s.total_amount) as total_revenue,
    AVG(s.total_amount) as avg_transaction_value,
    MAX(s.total_amount) as max_transaction_value
FROM sales s
GROUP BY DATE_TRUNC('month', s.sale_date)
ORDER BY month DESC;

-- Insert sample data
INSERT INTO drugs (drug_code, drug_name, generic_name, manufacturer, drug_class, category, unit_price, cost_price, stock_quantity, min_stock_level, expiry_date) VALUES
('PAN500', 'Panadol Extra', 'Paracetamol 500mg', 'GSK', 'Analgesic', 'OTC', 5.99, 3.50, 150, 50, '2025-12-31'),
('AMP250', 'Amoxicillin Capsules', 'Amoxicillin 250mg', 'Pfizer', 'Antibiotic', 'Prescription', 12.50, 8.00, 75, 30, '2024-10-15'),
('LIS20', 'Lisinopril Tablets', 'Lisinopril 20mg', 'AstraZeneca', 'Antihypertensive', 'Prescription', 25.75, 18.00, 200, 40, '2026-03-31'),
('MET500', 'Metformin Hydrochloride', 'Metformin 500mg', 'Merck', 'Antidiabetic', 'Prescription', 8.25, 5.00, 300, 60, '2025-08-30'),
('IBU400', 'Ibuprofen Tablets', 'Ibuprofen 400mg', 'Johnson & Johnson', 'NSAID', 'OTC', 7.50, 4.20, 25, 40, '2024-12-31');

INSERT INTO patients (patient_code, first_name, last_name, date_of_birth, gender, email, phone, city, state, primary_condition, insurance_id) VALUES
('PAT001', 'John', 'Smith', '1985-03-15', 'Male', 'john.smith@email.com', '+1-555-0101', 'New York', 'NY', 'Hypertension', 'INS12345'),
('PAT002', 'Maria', 'Garcia', '1978-07-22', 'Female', 'maria.g@email.com', '+1-555-0102', 'Los Angeles', 'CA', 'Type 2 Diabetes', 'INS12346'),
('PAT003', 'Robert', 'Johnson', '1992-11-30', 'Male', 'rob.j@email.com', '+1-555-0103', 'Chicago', 'IL', 'Chronic Pain', 'INS12347'),
('PAT004', 'Sarah', 'Williams', '1980-05-18', 'Female', 'sarah.w@email.com', '+1-555-0104', 'Houston', 'TX', 'Hypertension', 'INS12348');

INSERT INTO sales (transaction_id, drug_id, sale_date, quantity, unit_price, discount, tax_amount, total_amount, pharmacy_id, pharmacy_name, payment_method) VALUES
('SALE001', 1, '2024-01-15', 10, 5.99, 0.50, 0.60, 60.00, 101, 'City Pharmacy', 'Credit Card'),
('SALE002', 2, '2024-01-15', 5, 12.50, 0.00, 6.25, 68.75, 101, 'City Pharmacy', 'Insurance'),
('SALE003', 3, '2024-01-16', 8, 25.75, 2.00, 19.00, 204.00, 102, 'Health Plus', 'Cash'),
('SALE004', 1, '2024-01-17', 15, 5.99, 1.50, 8.24, 97.35, 103, 'MediCare', 'Credit Card'),
('SALE005', 4, '2024-01-18', 20, 8.25, 0.00, 16.50, 181.50, 101, 'City Pharmacy', 'Insurance');

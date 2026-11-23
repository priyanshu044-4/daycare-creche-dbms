-- ====================================================================
-- EARLYROOTS HOME-BASED CRECHE MANAGEMENT SYSTEM (DBMS MINI PROJECT)
-- Database DDL Schema (MySQL / MariaDB Compatible)
-- Engine: InnoDB | Character Set: utf8mb4
-- ====================================================================

CREATE DATABASE IF NOT EXISTS daycare_db;
USE daycare_db;

-- Disable foreign key checks during creation/reset
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS fee_plans;
DROP TABLE IF EXISTS daily_activities;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS allergies_medical;
DROP TABLE IF EXISTS child_guardians;
DROP TABLE IF EXISTS guardians;
DROP TABLE IF EXISTS children;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS rooms;

SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------------------------
-- 1. ROOMS TABLE (Home Care Spaces: Nursery Nook, Play Den, Veranda)
-- --------------------------------------------------------------------
CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(100) NOT NULL UNIQUE,
    age_group VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    room_type VARCHAR(50) DEFAULT 'Home Living Area',
    CONSTRAINT chk_room_capacity CHECK (capacity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 2. STAFF TABLE (Creche Host, Helpers/Didis, Home Cook, Visiting Nurse)
-- --------------------------------------------------------------------
CREATE TABLE staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role ENUM('Creche Host', 'Care Assistant', 'Visiting Nurse', 'Home Cook', 'Lead Educator', 'Caregiver') NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) UNIQUE,
    qualification VARCHAR(100),
    assigned_room_id INT NULL,
    hire_date DATE NOT NULL,
    salary DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT chk_staff_salary CHECK (salary >= 0),
    CONSTRAINT fk_staff_room FOREIGN KEY (assigned_room_id) 
        REFERENCES rooms(room_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 3. CHILDREN TABLE (Core Student Entity)
-- --------------------------------------------------------------------
CREATE TABLE children (
    child_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    dob DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NULL,
    room_id INT NOT NULL,
    enrollment_date DATE NOT NULL,
    status ENUM('Active', 'Graduated', 'Withdrawn', 'On Leave') NOT NULL DEFAULT 'Active',
    emergency_contact_phone VARCHAR(20) NOT NULL,
    notes TEXT NULL,
    CONSTRAINT fk_children_room FOREIGN KEY (room_id) 
        REFERENCES rooms(room_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 4. GUARDIANS TABLE (Parents & Authorized Guardians)
-- --------------------------------------------------------------------
CREATE TABLE guardians (
    guardian_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    relationship ENUM('Mother', 'Father', 'Guardian', 'Grandparent', 'Other') NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NULL,
    address VARCHAR(255) NOT NULL,
    occupation VARCHAR(100) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 5. CHILD_GUARDIANS (Many-to-Many Associative Entity)
-- --------------------------------------------------------------------
CREATE TABLE child_guardians (
    child_id INT NOT NULL,
    guardian_id INT NOT NULL,
    is_primary_contact TINYINT(1) NOT NULL DEFAULT 0,
    pickup_authorized TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (child_id, guardian_id),
    CONSTRAINT fk_cg_child FOREIGN KEY (child_id) 
        REFERENCES children(child_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cg_guardian FOREIGN KEY (guardian_id) 
        REFERENCES guardians(guardian_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 6. ALLERGIES & MEDICAL TABLE (Health Protocols)
-- --------------------------------------------------------------------
CREATE TABLE allergies_medical (
    allergy_id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    allergen_type VARCHAR(50) NOT NULL,
    allergen_name VARCHAR(100) NOT NULL,
    severity ENUM('Mild', 'Moderate', 'Severe') NOT NULL,
    action_plan TEXT NULL,
    CONSTRAINT fk_allergies_child FOREIGN KEY (child_id) 
        REFERENCES children(child_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 7. ATTENDANCE TABLE (Daily Check-in / Check-out)
-- --------------------------------------------------------------------
CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    check_in_time TIME NULL,
    check_out_time TIME NULL,
    status ENUM('Present', 'Absent', 'Excused', 'Late') NOT NULL,
    temperature_f DECIMAL(4,1) NULL,
    checked_in_by_staff_id INT NULL,
    remarks VARCHAR(255) NULL,
    UNIQUE KEY uk_child_attendance (child_id, attendance_date),
    CONSTRAINT fk_attendance_child FOREIGN KEY (child_id) 
        REFERENCES children(child_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_attendance_staff FOREIGN KEY (checked_in_by_staff_id) 
        REFERENCES staff(staff_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 8. DAILY ACTIVITIES TABLE (Meals, Naps, Play, Incidents)
-- --------------------------------------------------------------------
CREATE TABLE daily_activities (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    activity_date DATE NOT NULL,
    activity_type ENUM('Meal', 'Nap', 'Diaper/Potty', 'Play/Learning', 'Incident', 'Medication') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NULL,
    description TEXT NOT NULL,
    staff_id INT NULL,
    CONSTRAINT fk_activities_child FOREIGN KEY (child_id) 
        REFERENCES children(child_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_activities_staff FOREIGN KEY (staff_id) 
        REFERENCES staff(staff_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 9. FEE PLANS TABLE (Tuition Subscriptions)
-- --------------------------------------------------------------------
CREATE TABLE fee_plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    frequency ENUM('Monthly', 'Quarterly', 'Annual') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    CONSTRAINT chk_fee_amount CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 10. INVOICES TABLE (Billing Records)
-- --------------------------------------------------------------------
CREATE TABLE invoices (
    invoice_id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    plan_id INT NOT NULL,
    billing_period VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    net_amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('Pending', 'Partially Paid', 'Paid', 'Overdue', 'Cancelled') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_inv_net_amount CHECK (net_amount >= 0),
    CONSTRAINT fk_invoices_child FOREIGN KEY (child_id) 
        REFERENCES children(child_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_invoices_plan FOREIGN KEY (plan_id) 
        REFERENCES fee_plans(plan_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 11. PAYMENTS TABLE (Transaction Ledger)
-- --------------------------------------------------------------------
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_mode ENUM('Cash', 'UPI', 'Card', 'NetBanking', 'Cheque') NOT NULL,
    transaction_ref VARCHAR(100) NULL,
    receipt_number VARCHAR(50) UNIQUE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_payment_amount CHECK (amount_paid > 0),
    CONSTRAINT fk_payments_invoice FOREIGN KEY (invoice_id) 
        REFERENCES invoices(invoice_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 12. AUDIT LOGS TABLE (DBMS System Auditing)
-- --------------------------------------------------------------------
CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    action_type VARCHAR(20) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INT NULL,
    details TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- PERFORMANCE INDEXES
-- --------------------------------------------------------------------
CREATE INDEX idx_child_room ON children(room_id);
CREATE INDEX idx_child_status ON children(status);
CREATE INDEX idx_attendance_lookup ON attendance(attendance_date, child_id);
CREATE INDEX idx_invoices_status_child ON invoices(status, child_id);
CREATE INDEX idx_payments_date ON payments(payment_date);

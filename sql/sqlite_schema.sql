-- ====================================================================
-- EARLYROOTS HOME-BASED CRECHE MANAGEMENT SYSTEM
-- Standalone SQLite DDL Schema, Views & Triggers
-- ====================================================================

PRAGMA foreign_keys = ON;

-- 1. Rooms Table (Home Care Spaces)
CREATE TABLE IF NOT EXISTS rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT NOT NULL UNIQUE,
    age_group TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK(capacity > 0),
    room_type TEXT DEFAULT 'Home Living Area'
);

-- 2. Staff Table (Creche Host & Care Helpers / Didis)
CREATE TABLE IF NOT EXISTS staff (
    staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Creche Host', 'Care Assistant', 'Visiting Nurse', 'Home Cook', 'Lead Educator', 'Caregiver')),
    phone TEXT NOT NULL,
    email TEXT UNIQUE,
    qualification TEXT,
    assigned_room_id INTEGER REFERENCES rooms(room_id) ON DELETE SET NULL,
    hire_date DATE NOT NULL,
    salary REAL CHECK(salary >= 0)
);

-- 3. Children Table
CREATE TABLE IF NOT EXISTS children (
    child_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob DATE NOT NULL,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    blood_group TEXT CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    room_id INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE RESTRICT,
    enrollment_date DATE NOT NULL,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Graduated', 'Withdrawn', 'On Leave')),
    emergency_contact_phone TEXT NOT NULL,
    notes TEXT
);

-- 4. Guardians Table
CREATE TABLE IF NOT EXISTS guardians (
    guardian_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    relationship TEXT NOT NULL CHECK(relationship IN ('Mother', 'Father', 'Guardian', 'Grandparent', 'Other')),
    phone TEXT NOT NULL,
    email TEXT,
    address TEXT NOT NULL,
    occupation TEXT
);

-- 5. Child_Guardians Linking Table (Many-to-Many)
CREATE TABLE IF NOT EXISTS child_guardians (
    child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE CASCADE,
    guardian_id INTEGER NOT NULL REFERENCES guardians(guardian_id) ON DELETE CASCADE,
    is_primary_contact INTEGER DEFAULT 0 CHECK(is_primary_contact IN (0, 1)),
    pickup_authorized INTEGER DEFAULT 1 CHECK(pickup_authorized IN (0, 1)),
    PRIMARY KEY (child_id, guardian_id)
);

-- 6. Allergies & Medical Conditions
CREATE TABLE IF NOT EXISTS allergies_medical (
    allergy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE CASCADE,
    allergen_type TEXT NOT NULL,
    allergen_name TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('Mild', 'Moderate', 'Severe')),
    action_plan TEXT
);

-- 7. Daily Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in_time TEXT,
    check_out_time TEXT,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Excused', 'Late')),
    temperature_f REAL,
    checked_in_by_staff_id INTEGER REFERENCES staff(staff_id) ON DELETE SET NULL,
    remarks TEXT,
    UNIQUE(child_id, attendance_date)
);

-- 8. Daily Activities Table
CREATE TABLE IF NOT EXISTS daily_activities (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    activity_type TEXT NOT NULL CHECK(activity_type IN ('Meal', 'Nap', 'Diaper/Potty', 'Play/Learning', 'Incident', 'Medication')),
    start_time TEXT NOT NULL,
    end_time TEXT,
    description TEXT NOT NULL,
    staff_id INTEGER REFERENCES staff(staff_id) ON DELETE SET NULL
);

-- 9. Fee Plans Table
CREATE TABLE IF NOT EXISTS fee_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name TEXT NOT NULL UNIQUE,
    description TEXT,
    frequency TEXT NOT NULL CHECK(frequency IN ('Monthly', 'Quarterly', 'Annual')),
    amount REAL NOT NULL CHECK(amount > 0)
);

-- 10. Invoices Table
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE RESTRICT,
    plan_id INTEGER NOT NULL REFERENCES fee_plans(plan_id) ON DELETE RESTRICT,
    billing_period TEXT NOT NULL,
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    discount_amount REAL DEFAULT 0.0 CHECK(discount_amount >= 0),
    net_amount REAL NOT NULL CHECK(net_amount >= 0),
    due_date DATE NOT NULL,
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Partially Paid', 'Paid', 'Overdue', 'Cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    amount_paid REAL NOT NULL CHECK(amount_paid > 0),
    payment_date DATE NOT NULL,
    payment_mode TEXT NOT NULL CHECK(payment_mode IN ('Cash', 'UPI', 'Card', 'NetBanking', 'Cheque')),
    transaction_ref TEXT,
    receipt_number TEXT UNIQUE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- Database Triggers
-- --------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_child_audit_insert;
CREATE TRIGGER trg_child_audit_insert
AFTER INSERT ON children
BEGIN
    INSERT INTO audit_logs (action_type, table_name, record_id, details)
    VALUES ('INSERT', 'children', NEW.child_id, 
            'Enrolled new child: ' || NEW.first_name || ' ' || NEW.last_name || ' into Room ID ' || NEW.room_id);
END;

DROP TRIGGER IF EXISTS trg_payment_update_invoice;
CREATE TRIGGER trg_payment_update_invoice
AFTER INSERT ON payments
BEGIN
    UPDATE invoices
    SET status = CASE 
        WHEN (SELECT COALESCE(SUM(amount_paid), 0) FROM payments WHERE invoice_id = NEW.invoice_id) >= net_amount 
            THEN 'Paid'
        ELSE 'Partially Paid'
    END
    WHERE invoice_id = NEW.invoice_id;

    INSERT INTO audit_logs (action_type, table_name, record_id, details)
    VALUES ('INSERT', 'payments', NEW.payment_id,
            'Payment of ₹' || NEW.amount_paid || ' recorded for Invoice #' || NEW.invoice_id || ' via ' || NEW.payment_mode);
END;

DROP TRIGGER IF EXISTS trg_enforce_room_capacity;
CREATE TRIGGER trg_enforce_room_capacity
BEFORE INSERT ON children
WHEN (
    SELECT COUNT(*) FROM children 
    WHERE room_id = NEW.room_id AND status = 'Active'
) >= (SELECT capacity FROM rooms WHERE room_id = NEW.room_id)
BEGIN
    SELECT RAISE(ABORT, 'Cannot enroll child: Target room has reached its maximum capacity!');
END;

-- --------------------------------------------------------------------
-- Database Views
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS view_children_directory;
CREATE VIEW view_children_directory AS
SELECT 
    c.child_id,
    c.first_name || ' ' || c.last_name AS child_name,
    c.first_name,
    c.last_name,
    c.dob,
    c.gender,
    c.blood_group,
    c.status,
    c.enrollment_date,
    c.emergency_contact_phone,
    c.notes,
    r.room_id,
    r.room_name,
    r.age_group AS room_age_group,
    COALESCE(g.first_name || ' ' || g.last_name, 'None Assigned') AS primary_guardian_name,
    COALESCE(g.relationship, 'N/A') AS guardian_relation,
    COALESCE(g.phone, 'N/A') AS guardian_phone,
    (SELECT COUNT(*) FROM allergies_medical a WHERE a.child_id = c.child_id) AS allergy_count
FROM children c
JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN child_guardians cg ON c.child_id = cg.child_id AND cg.is_primary_contact = 1
LEFT JOIN guardians g ON cg.guardian_id = g.guardian_id;

DROP VIEW IF EXISTS view_room_summary;
CREATE VIEW view_room_summary AS
SELECT 
    r.room_id,
    r.room_name,
    r.age_group,
    r.capacity,
    r.room_type,
    COUNT(DISTINCT c.child_id) AS current_enrolled,
    (r.capacity - COUNT(DISTINCT c.child_id)) AS available_slots,
    ROUND((COUNT(DISTINCT c.child_id) * 100.0 / r.capacity), 1) AS occupancy_percentage,
    COALESCE(s.first_name || ' ' || s.last_name, 'Unassigned') AS lead_educator
FROM rooms r
LEFT JOIN children c ON r.room_id = c.room_id AND c.status = 'Active'
LEFT JOIN staff s ON r.room_id = s.assigned_room_id AND s.role IN ('Creche Host', 'Care Assistant', 'Lead Educator')
GROUP BY r.room_id;

DROP VIEW IF EXISTS view_pending_dues;
CREATE VIEW view_pending_dues AS
SELECT 
    i.invoice_id,
    i.billing_period,
    i.net_amount,
    COALESCE(SUM(p.amount_paid), 0) AS total_paid,
    (i.net_amount - COALESCE(SUM(p.amount_paid), 0)) AS balance_due,
    i.due_date,
    i.status AS invoice_status,
    c.child_id,
    c.first_name || ' ' || c.last_name AS child_name,
    g.first_name || ' ' || g.last_name AS guardian_name,
    g.phone AS guardian_phone,
    g.email AS guardian_email
FROM invoices i
JOIN children c ON i.child_id = c.child_id
LEFT JOIN payments p ON i.invoice_id = p.invoice_id
LEFT JOIN child_guardians cg ON c.child_id = cg.child_id AND cg.is_primary_contact = 1
LEFT JOIN guardians g ON cg.guardian_id = g.guardian_id
WHERE i.status IN ('Pending', 'Partially Paid', 'Overdue')
GROUP BY i.invoice_id;

DROP VIEW IF EXISTS view_daily_attendance_today;
CREATE VIEW view_daily_attendance_today AS
SELECT 
    c.child_id,
    c.first_name || ' ' || c.last_name AS child_name,
    r.room_name,
    COALESCE(a.attendance_date, DATE('now')) AS date,
    COALESCE(a.status, 'Not Marked') AS status,
    a.check_in_time,
    a.check_out_time,
    a.temperature_f,
    a.remarks
FROM children c
JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN attendance a ON c.child_id = a.child_id AND a.attendance_date = DATE('now')
WHERE c.status = 'Active';

DROP VIEW IF EXISTS view_daily_activity_feed;
CREATE VIEW view_daily_activity_feed AS
SELECT 
    da.activity_id,
    da.activity_date,
    da.start_time,
    da.end_time,
    da.activity_type,
    da.description,
    c.child_id,
    c.first_name || ' ' || c.last_name AS child_name,
    r.room_name,
    COALESCE(s.first_name || ' ' || s.last_name, 'Staff') AS logged_by
FROM daily_activities da
JOIN children c ON da.child_id = c.child_id
JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN staff s ON da.staff_id = s.staff_id
ORDER BY da.activity_date DESC, da.start_time DESC;

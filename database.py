import sqlite3
import pymysql
import os
from datetime import datetime, date
from config import Config

_cached_db_type = None

def check_mysql_connection():
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            connect_timeout=1
        )
        conn.close()
        return True
    except Exception:
        return False

def get_active_db_type():
    global _cached_db_type
    if _cached_db_type is not None:
        return _cached_db_type
        
    if Config.DB_TYPE == "MYSQL":
        _cached_db_type = "MYSQL"
    elif Config.DB_TYPE == "SQLITE":
        _cached_db_type = "SQLITE"
    else: # AUTO
        _cached_db_type = "MYSQL" if check_mysql_connection() else "SQLITE"
        
    return _cached_db_type

class DatabaseManager:
    def __init__(self):
        self.db_type = get_active_db_type()
        
    def get_connection(self):
        self.db_type = get_active_db_type()
        if self.db_type == "MYSQL":
            conn_admin = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor
            )
            with conn_admin.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB};")
            conn_admin.close()

            return pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        else:
            conn = sqlite3.connect(Config.SQLITE_PATH)
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            return conn

    def query(self, sql, params=None, fetch_one=False, fetch_all=True, commit=False):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if self.db_type == "MYSQL" and params:
                sql = sql.replace("?", "%s")
                
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            if commit or self.db_type == "SQLITE":
                conn.commit()

            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result and self.db_type == "SQLITE" else result
            if fetch_all:
                results = cursor.fetchall()
                if self.db_type == "SQLITE":
                    return [dict(row) for row in results]
                return results
            return cursor.lastrowid
        finally:
            conn.close()

    def execute_script(self, script_text):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if self.db_type == "SQLITE":
                cursor.executescript(script_text)
                conn.commit()
            else:
                statements = script_text.split(";")
                for stmt in statements:
                    stmt_clean = stmt.strip()
                    if stmt_clean:
                        cursor.execute(stmt_clean)
                conn.commit()
        finally:
            conn.close()

db = DatabaseManager()

def init_database(force_recreate=False):
    db_type = get_active_db_type()
    if db_type == "SQLITE":
        init_sqlite(force_recreate)
    else:
        init_mysql()

def init_sqlite(force_recreate=False):
    if force_recreate and os.path.exists(Config.SQLITE_PATH):
        try:
            os.remove(Config.SQLITE_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(Config.SQLITE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Tables DDL for Home-Based Creche
    cursor.executescript("""
    -- 1. Home Care Spaces (Nursery Nook, Play Den, Activity Veranda, Play Yard)
    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT NOT NULL UNIQUE,
        age_group TEXT NOT NULL,
        capacity INTEGER NOT NULL CHECK(capacity > 0),
        room_type TEXT DEFAULT 'Home Living Area'
    );

    -- 2. Caregivers & Helpers (Creche Host, Care Assistant / Didi, Home Cook, Visiting Nurse)
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

    -- 3. Children (Enrolled in Home Creche)
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

    -- 4. Guardians / Parents
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

    -- 5. Child-Guardian Linkage (Many-to-Many with pickup authorization)
    CREATE TABLE IF NOT EXISTS child_guardians (
        child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE CASCADE,
        guardian_id INTEGER NOT NULL REFERENCES guardians(guardian_id) ON DELETE CASCADE,
        is_primary_contact INTEGER DEFAULT 0 CHECK(is_primary_contact IN (0, 1)),
        pickup_authorized INTEGER DEFAULT 1 CHECK(pickup_authorized IN (0, 1)),
        PRIMARY KEY (child_id, guardian_id)
    );

    -- 6. Allergies & Home Care Protocols
    CREATE TABLE IF NOT EXISTS allergies_medical (
        allergy_id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE CASCADE,
        allergen_type TEXT NOT NULL,
        allergen_name TEXT NOT NULL,
        severity TEXT NOT NULL CHECK(severity IN ('Mild', 'Moderate', 'Severe')),
        action_plan TEXT
    );

    -- 7. Daily Attendance & Check-in / Check-out
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

    -- 8. Daily Home Activities (Home-cooked meals, nap times, story circles, potty tracking)
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

    -- 9. Home Creche Fee Plans
    CREATE TABLE IF NOT EXISTS fee_plans (
        plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_name TEXT NOT NULL UNIQUE,
        description TEXT,
        frequency TEXT NOT NULL CHECK(frequency IN ('Monthly', 'Quarterly', 'Annual')),
        amount REAL NOT NULL CHECK(amount > 0)
    );

    -- 10. Invoices (Care Invoices)
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

    -- 11. Payments (Ledger)
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

    -- 12. Audit Logs (Trigger trail)
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        table_name TEXT NOT NULL,
        record_id INTEGER,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Triggers DDL
    cursor.executescript("""
    DROP TRIGGER IF EXISTS trg_child_audit_insert;
    CREATE TRIGGER trg_child_audit_insert
    AFTER INSERT ON children
    BEGIN
        INSERT INTO audit_logs (action_type, table_name, record_id, details)
        VALUES ('INSERT', 'children', NEW.child_id, 
                'Enrolled child: ' || NEW.first_name || ' ' || NEW.last_name || ' into Home Care Area ' || NEW.room_id);
    END;

    DROP TRIGGER IF EXISTS trg_child_audit_update;
    CREATE TRIGGER trg_child_audit_update
    AFTER UPDATE ON children
    BEGIN
        INSERT INTO audit_logs (action_type, table_name, record_id, details)
        VALUES ('UPDATE', 'children', NEW.child_id, 
                'Updated child record. Status: ' || NEW.status || ', Care Area: ' || NEW.room_id);
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
        SELECT RAISE(ABORT, 'Cannot enroll child: Target home care space has reached maximum cozy capacity!');
    END;
    """)

    # Views DDL
    cursor.executescript("""
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
    LEFT JOIN staff s ON r.room_id = s.assigned_room_id
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
        COALESCE(s.first_name || ' ' || s.last_name, 'Creche Helper') AS logged_by
    FROM daily_activities da
    JOIN children c ON da.child_id = c.child_id
    JOIN rooms r ON c.room_id = r.room_id
    LEFT JOIN staff s ON da.staff_id = s.staff_id
    ORDER BY da.activity_date DESC, da.start_time DESC;
    """)

    conn.commit()
    conn.close()
    seed_sqlite()

def init_mysql():
    sql_dir = os.path.join(os.path.dirname(__file__), "sql")
    schema_path = os.path.join(sql_dir, "mysql_schema.sql")
    views_path = os.path.join(sql_dir, "mysql_views.sql")
    triggers_path = os.path.join(sql_dir, "mysql_triggers.sql")
    procedures_path = os.path.join(sql_dir, "mysql_procedures.sql")
    data_path = os.path.join(sql_dir, "mysql_seed_data.sql")
    
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        for path in [schema_path, views_path, triggers_path, procedures_path, data_path]:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    stmts = content.split(";")
                    for stmt in stmts:
                        s = stmt.strip()
                        if s:
                            cursor.execute(s)
        conn.commit()
    finally:
        conn.close()

def seed_sqlite():
    conn = sqlite3.connect(Config.SQLITE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # 1. Home Creche Spaces (Cozy Residential Home Setup)
    cursor.executemany("INSERT INTO rooms (room_name, age_group, capacity, room_type) VALUES (?, ?, ?, ?)", [
        ('Nursery Nook', '0-12 months', 4, 'Crib & Feeding Room'),
        ('Toddler Play Den', '1-2 years', 6, 'Soft Floor Play Living Area'),
        ('Activity Veranda', '2-3.5 years', 6, 'Dining & Story Space'),
        ('Sunshine Backyard Yard', '3.5-5 years', 6, 'Safe Lawn & Motor Play')
    ])

    # 2. Staff (Creche Mother, Assistants, Visiting Doctor/Nurse, Home Cook)
    cursor.executemany("""
    INSERT INTO staff (first_name, last_name, role, phone, email, qualification, assigned_room_id, hire_date, salary)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Sunita', 'Deshmukh', 'Creche Host', '9820112233', 'sunita.aunty@earlyroots.in', 'Home Creche Founder & Certified Nanny', 1, '2022-01-15', 50000),
        ('Anita', 'Menon', 'Care Assistant', '9820112234', 'anita.m@earlyroots.in', 'Early Child Care Certificate', 2, '2022-03-01', 28000),
        ('Lakshmi', 'Bai', 'Care Assistant', '9820112239', 'lakshmi.didi@earlyroots.in', 'Loving Attendant & First Aid Trained', 1, '2023-09-01', 22000),
        ('Geeta', 'Devi', 'Care Assistant', '9820112240', 'geeta.didi@earlyroots.in', 'Child Caretaker & Activity Helper', 3, '2023-11-15', 22000),
        ('Sister Mary', 'Joseph', 'Visiting Nurse', '9820112238', 'mary.nurse@earlyroots.in', 'Visiting Pediatric Nurse (Weekly Health Check)', None, '2022-08-01', 25000),
        ('Parvati', 'Devi', 'Home Cook', '9820112241', 'parvati.cook@earlyroots.in', 'Specialist in Nutritious Baby & Toddler Meals', None, '2022-05-01', 20000)
    ])

    # 3. Guardians (Neighbourhood Parents & Contacts)
    cursor.executemany("""
    INSERT INTO guardians (first_name, last_name, relationship, phone, email, address, occupation)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Rajesh', 'Sharma', 'Father', '9811223301', 'rajesh.sharma@gmail.com', 'Flat 402, Green Glen Layout, Bellandur, Bengaluru', 'Senior Software Architect'),
        ('Sunita', 'Sharma', 'Mother', '9811223302', 'sunita.sharma@yahoo.co.in', 'Flat 402, Green Glen Layout, Bellandur, Bengaluru', 'Pediatric Specialist'),
        ('Vikram', 'Verma', 'Father', '9811223303', 'vikram.v@techcorp.in', 'A-12, Sector 54, Golf Course Road, Gurugram', 'Investment Banking Director'),
        ('Pooja', 'Verma', 'Mother', '9811223304', 'pooja.verma@gmail.com', 'A-12, Sector 54, Golf Course Road, Gurugram', 'Urban Landscape Architect'),
        ('Amit', 'Patel', 'Father', '9811223305', 'amit.patel@rediffmail.com', '14 Sunrise Apartments, Bandra West, Mumbai', 'Chartered Accountant'),
        ('Priya', 'Iyer', 'Mother', '9811223306', 'priya.iyer@gmail.com', 'Plot 88, Anna Nagar West, Chennai', 'Data Science Lead'),
        ('Suresh', 'Reddy', 'Father', '9811223307', 'suresh.reddy@hyderabad.net', '202 Jubilee Hills, Road No. 36, Hyderabad', 'Civil Engineering Consultant'),
        ('Neha', 'Sen', 'Mother', '9811223308', 'neha.sen@gmail.com', 'Block CD, Sector 1, Salt Lake, Kolkata', 'Associate Professor'),
        ('Ramesh', 'Nair', 'Father', '9811223309', 'ramesh.nair@outlook.com', '77 Panampilly Nagar, Kochi, Kerala', 'Marketing Director'),
        ('Deepa', 'Gupta', 'Mother', '9811223310', 'deepa.gupta@gmail.com', 'B-4, Vasant Kunj, New Delhi', 'High Court Advocate')
    ])

    # 4. Children (Intimate Home Creche Group)
    cursor.executemany("""
    INSERT INTO children (first_name, last_name, dob, gender, blood_group, room_id, enrollment_date, status, emergency_contact_phone, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Aarav', 'Sharma', '2026-03-15', 'Male', 'O+', 1, '2026-06-01', 'Active', '9811223301', 'Prefers rocking crib with baby rattle'),
        ('Ananya', 'Sharma', '2024-05-20', 'Female', 'O+', 3, '2025-01-10', 'Active', '9811223301', 'Very cheerful, loves coloring with Auntie'),
        ('Vihaan', 'Verma', '2025-08-11', 'Male', 'B+', 2, '2026-02-01', 'Active', '9811223303', 'Fascinated by wooden puzzle blocks'),
        ('Isha', 'Verma', '2023-11-04', 'Female', 'A+', 4, '2024-07-15', 'Active', '9811223304', 'Enjoys evening story sessions on the porch'),
        ('Advait', 'Patel', '2026-01-10', 'Male', 'A-', 1, '2026-04-01', 'Active', '9811223305', 'Formula fed every 3 hours as per mother notes'),
        ('Diya', 'Iyer', '2025-02-14', 'Female', 'B-', 2, '2025-09-01', 'Active', '9811223306', 'Sensitive to sudden noises; likes soft chimes'),
        ('Kabir', 'Reddy', '2024-10-30', 'Male', 'AB+', 3, '2025-04-10', 'Active', '9811223307', 'Enjoys stacking clay cups and building houses'),
        ('Meera', 'Sen', '2026-05-18', 'Female', 'AB+', 1, '2026-08-01', 'Active', '9811223308', 'Takes small teething ring before afternoon rest'),
        ('Reyansh', 'Nair', '2023-09-12', 'Male', 'O-', 4, '2024-03-01', 'Active', '9811223309', 'Loves lawn slide and playing ball with caregiver'),
        ('Saanvi', 'Gupta', '2025-04-22', 'Female', 'A+', 2, '2025-11-01', 'Active', '9811223310', 'Grandparents authorized for 6 PM pickup')
    ])

    # 5. Child-Guardian Relationships
    cursor.executemany("""
    INSERT INTO child_guardians (child_id, guardian_id, is_primary_contact, pickup_authorized)
    VALUES (?, ?, ?, ?)
    """, [
        (1, 1, 1, 1), (1, 2, 0, 1),
        (2, 1, 1, 1), (2, 2, 0, 1),
        (3, 3, 1, 1), (3, 4, 0, 1),
        (4, 3, 0, 1), (4, 4, 1, 1),
        (5, 5, 1, 1),
        (6, 6, 1, 1),
        (7, 7, 1, 1),
        (8, 8, 1, 1),
        (9, 9, 1, 1),
        (10, 10, 1, 1)
    ])

    # 6. Allergies & Medical Care Notes
    cursor.executemany("""
    INSERT INTO allergies_medical (child_id, allergen_type, allergen_name, severity, action_plan)
    VALUES (?, ?, ?, ?, ?)
    """, [
        (1, 'Food', 'Cow Milk Protein (Lactose)', 'Moderate', 'Use soy/almond milk formula prepared separately in home kitchen'),
        (2, 'Food', 'Peanuts & Tree Nuts', 'Severe', 'Strict nut-free snacks; keep EpiPen in first-aid shelf'),
        (3, 'Environmental', 'Dust Mites & Pollen', 'Mild', 'Keep play mat vacuumed; give prescribed cetirizine syrup if sneezing'),
        (6, 'Food', 'Egg Albumin', 'Severe', 'Pure vegetarian home food only; notify home cook Parvati'),
        (7, 'Medicine', 'Penicillin & Amoxicillin', 'Severe', 'Medical alert band worn; call visiting doctor immediately if sick'),
        (9, 'Food', 'Gluten / Wheat', 'Moderate', 'Provide homemade gluten-free ragi or rice khichdi')
    ])

    # 7. Home Creche Care Fee Plans (in INR ₹)
    cursor.executemany("""
    INSERT INTO fee_plans (plan_name, description, frequency, amount)
    VALUES (?, ?, ?, ?)
    """, [
        ('Full-Day Home Creche (8am - 6pm)', 'Complete day stay: 3 home-cooked meals, warm sponge, nap time, and developmental play', 'Monthly', 12500.0),
        ('Half-Day Home Stay (8am - 1pm)', 'Morning playgroup, rhymes, homemade breakfast, and lunch with Sunita Auntie', 'Monthly', 7500.0),
        ('After-School Home Care (1pm - 6pm)', 'Homely lunch, resting nap, homework support, and evening milk & snacks', 'Monthly', 6500.0),
        ('Flexible Care & Play (Hourly / Drop-In)', 'Drop-in home care with playtime, meals, and sibling care', 'Monthly', 9000.0)
    ])

    # 8. Invoices (in INR ₹)
    today_ym = datetime.now().strftime("%B %Y")
    cursor.executemany("""
    INSERT INTO invoices (child_id, plan_id, billing_period, total_amount, discount_amount, net_amount, due_date, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, 1, today_ym, 12500.0, 0.0, 12500.0, '2026-11-28', 'Paid'),
        (2, 2, today_ym, 7500.0, 500.0, 7000.0, '2026-11-28', 'Paid'),
        (3, 2, today_ym, 7500.0, 0.0, 7500.0, '2026-11-28', 'Partially Paid'),
        (4, 3, today_ym, 6500.0, 0.0, 6500.0, '2026-11-20', 'Overdue'),
        (5, 1, today_ym, 12500.0, 0.0, 12500.0, '2026-11-28', 'Paid'),
        (6, 2, today_ym, 7500.0, 0.0, 7500.0, '2026-11-25', 'Pending'),
        (7, 2, today_ym, 7500.0, 0.0, 7500.0, '2026-11-28', 'Pending'),
        (8, 1, today_ym, 12500.0, 1000.0, 11500.0, '2026-11-28', 'Paid'),
        (9, 3, today_ym, 6500.0, 0.0, 6500.0, '2026-11-15', 'Overdue'),
        (10, 2, today_ym, 7500.0, 0.0, 7500.0, '2026-11-28', 'Paid')
    ])

    # 9. Payments
    cursor.executemany("""
    INSERT INTO payments (invoice_id, amount_paid, payment_date, payment_mode, transaction_ref, receipt_number)
    VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (1, 12500.0, '2026-11-02', 'UPI', 'UPI/2026/GPay/98123', 'REC-001'),
        (2, 7000.0, '2026-11-03', 'UPI', 'UPI/2026/PhonePe/77612', 'REC-002'),
        (3, 4000.0, '2026-11-04', 'NetBanking', 'HDFC-IMPS-88412', 'REC-003'),
        (5, 12500.0, '2026-11-05', 'UPI', 'UPI/2026/Paytm/33120', 'REC-004'),
        (8, 11500.0, '2026-11-02', 'Card', 'TXN-ICICI-77112', 'REC-005'),
        (10, 7500.0, '2026-11-06', 'Cash', 'CASH-REC-101', 'REC-006')
    ])

    # 10. Daily Attendance
    today_str = date.today().isoformat()
    cursor.executemany("""
    INSERT INTO attendance (child_id, attendance_date, check_in_time, check_out_time, status, temperature_f, checked_in_by_staff_id, remarks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, today_str, '08:15', None, 'Present', 98.4, 1, 'Dropped off by mother with diaper bag'),
        (2, today_str, '08:30', None, 'Present', 98.2, 1, 'Greeted Sunita Auntie warmly, took toy truck'),
        (3, today_str, '08:45', None, 'Present', 98.6, 2, 'Normal temperature, settled on play rug'),
        (4, today_str, None, None, 'Absent', None, 1, 'Mother informed: Attending wedding'),
        (5, today_str, '08:20', None, 'Present', 98.1, 3, 'Handed over warm formula milk flask'),
        (6, today_str, '09:05', None, 'Late', 98.5, 2, 'Traffic delay on main road'),
        (7, today_str, '08:40', None, 'Present', 98.3, 1, 'Enjoyed morning rhyme session with Didi'),
        (8, today_str, '08:10', None, 'Present', 98.0, 3, 'Morning diaper checked, tucked into crib'),
        (9, today_str, None, None, 'Excused', None, 1, 'Doctor checkup in morning; will drop post lunch'),
        (10, today_str, '08:50', None, 'Present', 98.4, 2, 'Playing happily with soft doll')
    ])

    # 11. Daily Activities (Home cooked meals & home creche care)
    cursor.executemany("""
    INSERT INTO daily_activities (child_id, activity_date, activity_type, start_time, end_time, description, staff_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, today_str, 'Meal', '09:00', '09:25', 'Drank 150ml warm soy milk peacefully on caregiver lap', 3),
        (1, today_str, 'Nap', '10:00', '11:15', 'Quiet nap in Nursery Nook crib #1 with soft lullaby', 3),
        (2, today_str, 'Play/Learning', '09:30', '10:30', 'Coloring animal shapes with wax crayons on living room carpet', 1),
        (3, today_str, 'Meal', '09:15', '09:45', 'Ate warm homemade Moong Dal Khichdi prepared by Parvati Didi', 4),
        (5, today_str, 'Diaper/Potty', '09:30', '09:40', 'Diaper changed, fresh clothes put on', 3),
        (6, today_str, 'Play/Learning', '09:30', '10:15', 'Building block tower and stacking rings with friends', 2),
        (7, today_str, 'Meal', '10:00', '10:25', 'Finished bowl of mashed ripe banana and soft Idli with ghee', 1),
        (10, today_str, 'Play/Learning', '09:15', '10:00', 'Story recitation on veranda carpet: "The Monkey and the Crocodile"', 1)
    ])

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database(force_recreate=True)
    print(f"Database successfully initialized for Home-Based Creche in {get_active_db_type()} mode!")

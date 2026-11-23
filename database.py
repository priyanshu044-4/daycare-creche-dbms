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

    # Tables DDL
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT NOT NULL UNIQUE,
        age_group TEXT NOT NULL,
        capacity INTEGER NOT NULL CHECK(capacity > 0),
        room_type TEXT DEFAULT 'Classroom'
    );

    CREATE TABLE IF NOT EXISTS staff (
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Administrator', 'Lead Educator', 'Caregiver', 'Nurse', 'Cook')),
        phone TEXT NOT NULL,
        email TEXT UNIQUE,
        qualification TEXT,
        assigned_room_id INTEGER REFERENCES rooms(room_id) ON DELETE SET NULL,
        hire_date DATE NOT NULL,
        salary REAL CHECK(salary >= 0)
    );

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

    CREATE TABLE IF NOT EXISTS child_guardians (
        child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE CASCADE,
        guardian_id INTEGER NOT NULL REFERENCES guardians(guardian_id) ON DELETE CASCADE,
        is_primary_contact INTEGER DEFAULT 0 CHECK(is_primary_contact IN (0, 1)),
        pickup_authorized INTEGER DEFAULT 1 CHECK(pickup_authorized IN (0, 1)),
        PRIMARY KEY (child_id, guardian_id)
    );

    CREATE TABLE IF NOT EXISTS allergies_medical (
        allergy_id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL REFERENCES children(child_id) ON DELETE CASCADE,
        allergen_type TEXT NOT NULL,
        allergen_name TEXT NOT NULL,
        severity TEXT NOT NULL CHECK(severity IN ('Mild', 'Moderate', 'Severe')),
        action_plan TEXT
    );

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

    CREATE TABLE IF NOT EXISTS fee_plans (
        plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_name TEXT NOT NULL UNIQUE,
        description TEXT,
        frequency TEXT NOT NULL CHECK(frequency IN ('Monthly', 'Quarterly', 'Annual')),
        amount REAL NOT NULL CHECK(amount > 0)
    );

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
                'Enrolled child: ' || NEW.first_name || ' ' || NEW.last_name || ' into Room ID ' || NEW.room_id);
    END;

    DROP TRIGGER IF EXISTS trg_child_audit_update;
    CREATE TRIGGER trg_child_audit_update
    AFTER UPDATE ON children
    BEGIN
        INSERT INTO audit_logs (action_type, table_name, record_id, details)
        VALUES ('UPDATE', 'children', NEW.child_id, 
                'Updated child record. Status: ' || NEW.status || ', Room: ' || NEW.room_id);
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
        SELECT RAISE(ABORT, 'Cannot enroll child: Target classroom has reached its maximum sanctioned capacity!');
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
        COUNT(c.child_id) AS current_enrolled,
        (r.capacity - COUNT(c.child_id)) AS available_slots,
        ROUND((COUNT(c.child_id) * 100.0 / r.capacity), 1) AS occupancy_percentage,
        COALESCE(s.first_name || ' ' || s.last_name, 'Unassigned') AS lead_educator
    FROM rooms r
    LEFT JOIN children c ON r.room_id = c.room_id AND c.status = 'Active'
    LEFT JOIN staff s ON r.room_id = s.assigned_room_id AND s.role = 'Lead Educator'
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

    # 1. Rooms (Indian Preschool Pods)
    cursor.executemany("INSERT INTO rooms (room_name, age_group, capacity, room_type) VALUES (?, ?, ?, ?)", [
        ('Shishu Vatika', '0-12 months', 8, 'Infant Nest'),
        ('Nanhe Kadam', '1-2 years', 12, 'Toddler Playgroup'),
        ('Bal Vatika', '2-3.5 years', 15, 'Nursery Learning Pod'),
        ('Tarang Prep', '3.5-5 years', 18, 'Kindergarten Activity Lab')
    ])

    # 2. Staff (Indian Educators, Nurse & Caregivers)
    cursor.executemany("""
    INSERT INTO staff (first_name, last_name, role, phone, email, qualification, assigned_room_id, hire_date, salary)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Sunita', 'Deshmukh', 'Administrator', '9820112233', 'sunita.admin@kilkari.in', 'M.Ed Early Childhood Education', None, '2022-01-15', 55000),
        ('Anita', 'Menon', 'Lead Educator', '9820112234', 'anita.m@kilkari.in', 'B.Ed & Montessori Certified', 1, '2022-03-01', 42000),
        ('Rajeshwari', 'Pillai', 'Lead Educator', '9820112235', 'rajeshwari.p@kilkari.in', 'Diploma in Child Psychology', 2, '2022-06-10', 40000),
        ('Meenakshi', 'Sundaram', 'Lead Educator', '9820112236', 'meenakshi.s@kilkari.in', 'B.Sc Child Development', 3, '2023-01-10', 41000),
        ('Farhan', 'Akhtar', 'Lead Educator', '9820112237', 'farhan.a@kilkari.in', 'B.A Primary Education', 4, '2023-04-15', 39000),
        ('Sister Mary', 'Joseph', 'Nurse', '9820112238', 'mary.nurse@kilkari.in', 'Registered Pediatric Nurse (B.Sc Nursing)', None, '2022-08-01', 45000),
        ('Lakshmi', 'Bai', 'Caregiver', '9820112239', 'lakshmi.b@kilkari.in', 'Certified Child Care Attendant', 2, '2023-09-01', 30000),
        ('Geeta', 'Devi', 'Caregiver', '9820112240', 'geeta.d@kilkari.in', 'CPR & First Aid Certified', 1, '2023-11-15', 30000)
    ])

    # 3. Guardians (Indian Parents & Metro Addresses)
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

    # 4. Children (Indian First & Last Names)
    cursor.executemany("""
    INSERT INTO children (first_name, last_name, dob, gender, blood_group, room_id, enrollment_date, status, emergency_contact_phone, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Aarav', 'Sharma', '2026-03-15', 'Male', 'O+', 1, '2026-06-01', 'Active', '9811223301', 'Needs soft lullaby before nap time'),
        ('Ananya', 'Sharma', '2024-05-20', 'Female', 'O+', 3, '2025-01-10', 'Active', '9811223301', 'Very cheerful, loves coloring rangoli patterns'),
        ('Vihaan', 'Verma', '2025-08-11', 'Male', 'B+', 2, '2026-02-01', 'Active', '9811223303', 'Fascinated by wooden puzzle blocks'),
        ('Isha', 'Verma', '2023-11-04', 'Female', 'A+', 4, '2024-07-15', 'Active', '9811223304', 'Enjoys Panchatantra story sessions'),
        ('Advait', 'Patel', '2026-01-10', 'Male', 'A-', 1, '2026-04-01', 'Active', '9811223305', 'Formula fed every 3 hours as per schedule'),
        ('Diya', 'Iyer', '2025-02-14', 'Female', 'B-', 2, '2025-09-01', 'Active', '9811223306', 'Sensitive to sudden loud claps or noise'),
        ('Kabir', 'Reddy', '2024-10-30', 'Male', 'AB+', 3, '2025-04-10', 'Active', '9811223307', 'Enjoys stacking clay cups and blocks'),
        ('Meera', 'Sen', '2026-05-18', 'Female', 'AB+', 1, '2026-08-01', 'Active', '9811223308', 'Takes small teething ring before afternoon rest'),
        ('Reyansh', 'Nair', '2023-09-12', 'Male', 'O-', 4, '2024-03-01', 'Active', '9811223309', 'Loves rhymes and outdoor slide'),
        ('Saanvi', 'Gupta', '2025-04-22', 'Female', 'A+', 2, '2025-11-01', 'Active', '9811223310', 'Grandparents authorized for evening pickup')
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

    # 6. Allergies & Medical Notes
    cursor.executemany("""
    INSERT INTO allergies_medical (child_id, allergen_type, allergen_name, severity, action_plan)
    VALUES (?, ?, ?, ?, ?)
    """, [
        (1, 'Food', 'Cow Milk Protein (Lactose)', 'Moderate', 'Use soy/almond milk formula strictly'),
        (2, 'Food', 'Peanuts & Tree Nuts', 'Severe', 'Keep EpiPen handy, call Apollo emergency'),
        (3, 'Environmental', 'Dust Mites & Pollen', 'Mild', 'Keep play mat clean, administer cetirizine syrup if sneezing'),
        (6, 'Food', 'Egg Albumin', 'Severe', 'Strict egg-free diet, notify creche kitchen cook'),
        (7, 'Medicine', 'Penicillin & Amoxicillin', 'Severe', 'Medical alert band worn; inform attending doctor immediately'),
        (9, 'Food', 'Gluten / Wheat', 'Moderate', 'Provide gluten-free ragi or rice snacks and khichdi')
    ])

    # 7. Fee Plans (in INR ₹)
    cursor.executemany("""
    INSERT INTO fee_plans (plan_name, description, frequency, amount)
    VALUES (?, ?, ?, ?)
    """, [
        ('Shishu Full-Day Infant Care', 'Full daycare with nutrition, warm oil massage, diapering, and nap logs (8am-6pm)', 'Monthly', 14500.0),
        ('Nanhe Kadam Toddler Playgroup', 'Structured motor skills, sensory play, fresh hot lunch, and nap (8am-5pm)', 'Monthly', 11500.0),
        ('Bal Vatika Half-Day Program', 'Morning early learning, music, and socialization (8:30am-12:30pm)', 'Monthly', 7500.0),
        ('Tarang Pre-K Extended Day', 'School readiness curriculum with evening activity club (8am-6pm)', 'Monthly', 12500.0)
    ])

    # 8. Invoices (in INR ₹)
    today_ym = datetime.now().strftime("%B %Y")
    cursor.executemany("""
    INSERT INTO invoices (child_id, plan_id, billing_period, total_amount, discount_amount, net_amount, due_date, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, 1, today_ym, 14500.0, 0.0, 14500.0, '2026-11-28', 'Paid'),
        (2, 3, today_ym, 7500.0, 500.0, 7000.0, '2026-11-28', 'Paid'),
        (3, 2, today_ym, 11500.0, 0.0, 11500.0, '2026-11-28', 'Partially Paid'),
        (4, 4, today_ym, 12500.0, 0.0, 12500.0, '2026-11-20', 'Overdue'),
        (5, 1, today_ym, 14500.0, 0.0, 14500.0, '2026-11-28', 'Paid'),
        (6, 2, today_ym, 11500.0, 0.0, 11500.0, '2026-11-25', 'Pending'),
        (7, 3, today_ym, 7500.0, 0.0, 7500.0, '2026-11-28', 'Pending'),
        (8, 1, today_ym, 14500.0, 1000.0, 13500.0, '2026-11-28', 'Paid'),
        (9, 4, today_ym, 12500.0, 0.0, 12500.0, '2026-11-15', 'Overdue'),
        (10, 2, today_ym, 11500.0, 0.0, 11500.0, '2026-11-28', 'Paid')
    ])

    # 9. Payments (UPI / NetBanking / Cards in ₹)
    cursor.executemany("""
    INSERT INTO payments (invoice_id, amount_paid, payment_date, payment_mode, transaction_ref, receipt_number)
    VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (1, 14500.0, '2026-11-02', 'UPI', 'UPI/2026/GPay/98123', 'REC-001'),
        (2, 7000.0, '2026-11-03', 'UPI', 'UPI/2026/PhonePe/77612', 'REC-002'),
        (3, 6000.0, '2026-11-04', 'NetBanking', 'HDFC-IMPS-88412', 'REC-003'),
        (5, 14500.0, '2026-11-05', 'UPI', 'UPI/2026/Paytm/33120', 'REC-004'),
        (8, 13500.0, '2026-11-02', 'Card', 'TXN-ICICI-77112', 'REC-005'),
        (10, 11500.0, '2026-11-06', 'Cash', 'CASH-REC-101', 'REC-006')
    ])

    # 10. Attendance Today
    today_str = date.today().isoformat()
    cursor.executemany("""
    INSERT INTO attendance (child_id, attendance_date, check_in_time, check_out_time, status, temperature_f, checked_in_by_staff_id, remarks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, today_str, '08:15', None, 'Present', 98.4, 2, 'Arrived cheerfully with mother'),
        (2, today_str, '08:30', None, 'Present', 98.2, 4, 'Carrying drawing book'),
        (3, today_str, '08:45', None, 'Present', 98.6, 3, 'Temperature checked, normal'),
        (4, today_str, None, None, 'Absent', None, 5, 'Family out of station for wedding'),
        (5, today_str, '08:20', None, 'Present', 98.1, 2, 'Handed over warm formula flask'),
        (6, today_str, '09:05', None, 'Late', 98.5, 3, 'Traffic delay on Western Express Highway'),
        (7, today_str, '08:40', None, 'Present', 98.3, 4, 'Participating actively in morning prayer'),
        (8, today_str, '08:10', None, 'Present', 98.0, 2, 'Morning diaper check completed'),
        (9, today_str, None, None, 'Excused', None, 5, 'Pediatric vaccination appointment'),
        (10, today_str, '08:50', None, 'Present', 98.4, 3, 'Brought favourite soft toy')
    ])

    # 11. Activities (Indian Food & Child Activities)
    cursor.executemany("""
    INSERT INTO daily_activities (child_id, activity_date, activity_type, start_time, end_time, description, staff_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, today_str, 'Meal', '09:00', '09:25', 'Drank 150ml warm soy milk formula peacefully', 8),
        (1, today_str, 'Nap', '10:00', '11:15', 'Restful morning sleep in Shishu crib #2', 8),
        (2, today_str, 'Play/Learning', '09:30', '10:30', 'Clay modeling and Diya painting activity', 4),
        (3, today_str, 'Meal', '09:15', '09:45', 'Ate warm Moong Dal Khichdi with pure cow ghee', 7),
        (5, today_str, 'Diaper/Potty', '09:30', '09:40', 'Diaper change, rash cream applied', 2),
        (6, today_str, 'Play/Learning', '09:30', '10:15', 'Sensory sand play and alphabet puzzle circle', 3),
        (7, today_str, 'Meal', '10:00', '10:25', 'Finished mashed banana and soft Idli with ghee', 4),
        (10, today_str, 'Play/Learning', '09:15', '10:00', 'Panchatantra story recitation: "The Clever Hare"', 3)
    ])

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database(force_recreate=True)
    print(f"Database successfully re-initialized with Indian names and INR currency in {get_active_db_type()} mode!")

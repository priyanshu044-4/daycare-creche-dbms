from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, date
import random
from config import Config
from database import db, init_database, get_active_db_type

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database is initialized at start
try:
    init_database()
except Exception as e:
    print(f"Database init warning: {e}")

@app.context_processor
def inject_db_info():
    return {
        "active_db": get_active_db_type(),
        "current_year": datetime.now().year,
        "today_date": date.today().isoformat()
    }

# --------------------------------------------------------------------
# HTML Page Routes
# --------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/children")
def children_page():
    rooms = db.query("SELECT room_id, room_name, age_group, capacity FROM rooms ORDER BY room_id")
    guardians = db.query("SELECT guardian_id, first_name, last_name, relationship, phone FROM guardians ORDER BY first_name")
    return render_template("children.html", rooms=rooms, guardians=guardians)

@app.route("/guardians")
def guardians_page():
    return render_template("guardians.html")

@app.route("/rooms-staff")
def rooms_staff_page():
    return render_template("rooms_staff.html")

@app.route("/attendance")
def attendance_page():
    rooms = db.query("SELECT room_id, room_name FROM rooms ORDER BY room_id")
    return render_template("attendance.html", rooms=rooms)

@app.route("/activities")
def activities_page():
    children = db.query("SELECT child_id, first_name || ' ' || last_name AS name FROM children WHERE status = 'Active' ORDER BY first_name")
    staff = db.query("SELECT staff_id, first_name || ' ' || last_name AS name FROM staff ORDER BY first_name")
    return render_template("activities.html", children=children, staff=staff)

@app.route("/billing")
def billing_page():
    children = db.query("SELECT child_id, first_name || ' ' || last_name AS name FROM children WHERE status = 'Active' ORDER BY first_name")
    plans = db.query("SELECT plan_id, plan_name, amount FROM fee_plans ORDER BY amount")
    return render_template("billing.html", children=children, plans=plans)

@app.route("/sql-console")
def sql_console_page():
    return render_template("sql_console.html")

# --------------------------------------------------------------------
# REST API Endpoints
# --------------------------------------------------------------------

# 1. Dashboard Metrics API
@app.route("/api/stats")
def api_stats():
    total_children = db.query("SELECT COUNT(*) AS cnt FROM children WHERE status = 'Active'", fetch_one=True)["cnt"]
    present_today = db.query(
        "SELECT COUNT(*) AS cnt FROM attendance WHERE attendance_date = DATE('now') AND status IN ('Present', 'Late')", 
        fetch_one=True
    )["cnt"]
    total_staff = db.query("SELECT COUNT(*) AS cnt FROM staff", fetch_one=True)["cnt"]
    total_rooms = db.query("SELECT COUNT(*) AS cnt FROM rooms", fetch_one=True)["cnt"]
    
    # Financial metrics
    pending_amount = db.query(
        "SELECT COALESCE(SUM(net_amount), 0) AS total FROM invoices WHERE status IN ('Pending', 'Partially Paid', 'Overdue')",
        fetch_one=True
    )["total"]

    # Room occupancy for chart
    room_occupancy = db.query("SELECT room_name, current_enrolled, capacity, occupancy_percentage FROM view_room_summary")
    
    # Today attendance stats
    attendance_stats = db.query("""
        SELECT 
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present,
            SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) AS late,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS absent,
            SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) AS excused
        FROM attendance 
        WHERE attendance_date = DATE('now')
    """, fetch_one=True)

    # Recent Audit Logs
    recent_logs = db.query("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 6")

    return jsonify({
        "total_children": total_children,
        "present_today": present_today,
        "total_staff": total_staff,
        "total_rooms": total_rooms,
        "pending_amount": pending_amount,
        "room_occupancy": room_occupancy,
        "attendance_stats": attendance_stats,
        "recent_logs": recent_logs
    })

# 2. Children API
@app.route("/api/children", methods=["GET", "POST"])
def api_children():
    if request.method == "GET":
        status_filter = request.args.get("status")
        room_filter = request.args.get("room_id")
        
        sql = "SELECT * FROM view_children_directory WHERE 1=1"
        params = []
        if status_filter:
            sql += " AND status = ?"
            params.append(status_filter)
        if room_filter:
            sql += " AND room_id = ?"
            params.append(room_filter)
            
        sql += " ORDER BY child_id DESC"
        data = db.query(sql, params if params else None)
        return jsonify(data)
    
    elif request.method == "POST":
        data = request.json or {}
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        dob = data.get("dob")
        gender = data.get("gender")
        blood_group = data.get("blood_group")
        room_id = int(data.get("room_id"))
        guardian_id = data.get("guardian_id")
        emergency_phone = data.get("emergency_contact_phone", "").strip()
        notes = data.get("notes", "").strip()

        if not first_name or not last_name or not dob or not room_id or not emergency_phone:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            # Trigger 'trg_enforce_room_capacity' will automatically abort if room is full!
            child_id = db.query("""
                INSERT INTO children (first_name, last_name, dob, gender, blood_group, room_id, enrollment_date, status, emergency_contact_phone, notes)
                VALUES (?, ?, ?, ?, ?, ?, DATE('now'), 'Active', ?, ?)
            """, [first_name, last_name, dob, gender, blood_group, room_id, emergency_phone, notes], commit=True)

            # Link Guardian if provided
            if guardian_id and int(guardian_id) > 0:
                db.query("""
                    INSERT INTO child_guardians (child_id, guardian_id, is_primary_contact, pickup_authorized)
                    VALUES (?, ?, 1, 1)
                """, [child_id, int(guardian_id)], commit=True)

            return jsonify({"success": True, "message": f"Child {first_name} {last_name} enrolled successfully!", "child_id": child_id})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route("/api/children/<int:child_id>", methods=["GET", "DELETE"])
def api_child_detail(child_id):
    if request.method == "GET":
        child = db.query("SELECT * FROM view_children_directory WHERE child_id = ?", [child_id], fetch_one=True)
        if not child:
            return jsonify({"error": "Child not found"}), 404
            
        allergies = db.query("SELECT * FROM allergies_medical WHERE child_id = ?", [child_id])
        guardians = db.query("""
            SELECT g.*, cg.is_primary_contact, cg.pickup_authorized 
            FROM guardians g
            JOIN child_guardians cg ON g.guardian_id = cg.guardian_id
            WHERE cg.child_id = ?
        """, [child_id])
        invoices = db.query("SELECT * FROM invoices WHERE child_id = ? ORDER BY invoice_id DESC", [child_id])
        recent_attendance = db.query("SELECT * FROM attendance WHERE child_id = ? ORDER BY attendance_date DESC LIMIT 7", [child_id])

        return jsonify({
            "child": child,
            "allergies": allergies,
            "guardians": guardians,
            "invoices": invoices,
            "recent_attendance": recent_attendance
        })
    elif request.method == "DELETE":
        try:
            db.query("DELETE FROM children WHERE child_id = ?", [child_id], commit=True)
            return jsonify({"success": True, "message": f"Child record #{child_id} deleted successfully."})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# 3. Guardians API
@app.route("/api/guardians", methods=["GET", "POST"])
def api_guardians():
    if request.method == "GET":
        guardians = db.query("""
            SELECT 
                g.*,
                COUNT(cg.child_id) AS linked_children_count
            FROM guardians g
            LEFT JOIN child_guardians cg ON g.guardian_id = cg.guardian_id
            GROUP BY g.guardian_id
            ORDER BY g.first_name
        """)
        return jsonify(guardians)
    elif request.method == "POST":
        data = request.json or {}
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        relationship = data.get("relationship")
        phone = data.get("phone", "").strip()
        email = data.get("email", "").strip()
        address = data.get("address", "").strip()
        occupation = data.get("occupation", "").strip()

        if not first_name or not last_name or not phone or not address:
            return jsonify({"error": "First Name, Last Name, Phone, and Address are required."}), 400

        try:
            gid = db.query("""
                INSERT INTO guardians (first_name, last_name, relationship, phone, email, address, occupation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [first_name, last_name, relationship, phone, email, address, occupation], commit=True)
            return jsonify({"success": True, "message": "Guardian registered successfully!", "guardian_id": gid})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# 4. Rooms & Staff API
@app.route("/api/rooms", methods=["GET", "POST"])
def api_rooms():
    if request.method == "GET":
        rooms = db.query("SELECT * FROM view_room_summary")
        return jsonify(rooms)
    elif request.method == "POST":
        data = request.json or {}
        name = data.get("room_name")
        age_group = data.get("age_group")
        capacity = int(data.get("capacity", 10))
        room_type = data.get("room_type", "Classroom")
        try:
            rid = db.query("INSERT INTO rooms (room_name, age_group, capacity, room_type) VALUES (?, ?, ?, ?)",
                           [name, age_group, capacity, room_type], commit=True)
            return jsonify({"success": True, "message": "Room created successfully!", "room_id": rid})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route("/api/staff", methods=["GET", "POST"])
def api_staff():
    if request.method == "GET":
        staff_members = db.query("""
            SELECT 
                s.*, 
                r.room_name 
            FROM staff s
            LEFT JOIN rooms r ON s.assigned_room_id = r.room_id
            ORDER BY s.staff_id
        """)
        return jsonify(staff_members)
    elif request.method == "POST":
        data = request.json or {}
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        role = data.get("role")
        phone = data.get("phone")
        email = data.get("email")
        qualification = data.get("qualification")
        room_id = data.get("assigned_room_id") or None
        salary = float(data.get("salary", 0))

        try:
            sid = db.query("""
                INSERT INTO staff (first_name, last_name, role, phone, email, qualification, assigned_room_id, hire_date, salary)
                VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'), ?)
            """, [first_name, last_name, role, phone, email, qualification, room_id, salary], commit=True)
            return jsonify({"success": True, "message": "Staff member registered successfully!", "staff_id": sid})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# 5. Attendance API
@app.route("/api/attendance", methods=["GET", "POST"])
def api_attendance():
    if request.method == "GET":
        att_date = request.args.get("date", date.today().isoformat())
        room_id = request.args.get("room_id")

        sql = """
            SELECT 
                c.child_id,
                c.first_name || ' ' || c.last_name AS child_name,
                r.room_name,
                r.room_id,
                COALESCE(a.attendance_date, ?) AS attendance_date,
                COALESCE(a.status, 'Not Marked') AS status,
                a.check_in_time,
                a.check_out_time,
                a.temperature_f,
                a.remarks,
                a.attendance_id
            FROM children c
            JOIN rooms r ON c.room_id = r.room_id
            LEFT JOIN attendance a ON c.child_id = a.child_id AND a.attendance_date = ?
            WHERE c.status = 'Active'
        """
        params = [att_date, att_date]
        if room_id:
            sql += " AND r.room_id = ?"
            params.append(room_id)
        sql += " ORDER BY r.room_id, c.first_name"

        records = db.query(sql, params)
        return jsonify(records)

    elif request.method == "POST":
        data = request.json or {}
        child_id = data.get("child_id")
        att_date = data.get("attendance_date", date.today().isoformat())
        status = data.get("status", "Present")
        check_in = data.get("check_in_time")
        check_out = data.get("check_out_time")
        temp = data.get("temperature_f")
        remarks = data.get("remarks", "")

        if not check_in and status in ("Present", "Late"):
            check_in = datetime.now().strftime("%H:%M")

        try:
            # Upsert into attendance
            db.query("""
                INSERT INTO attendance (child_id, attendance_date, check_in_time, check_out_time, status, temperature_f, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(child_id, attendance_date) DO UPDATE SET
                    status = excluded.status,
                    check_in_time = COALESCE(excluded.check_in_time, attendance.check_in_time),
                    check_out_time = COALESCE(excluded.check_out_time, attendance.check_out_time),
                    temperature_f = COALESCE(excluded.temperature_f, attendance.temperature_f),
                    remarks = COALESCE(excluded.remarks, attendance.remarks)
            """, [child_id, att_date, check_in, check_out, status, temp, remarks], commit=True)
            return jsonify({"success": True, "message": "Attendance recorded successfully!"})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# 6. Daily Activities API
@app.route("/api/activities", methods=["GET", "POST"])
def api_activities():
    if request.method == "GET":
        activities = db.query("SELECT * FROM view_daily_activity_feed LIMIT 50")
        return jsonify(activities)
    elif request.method == "POST":
        data = request.json or {}
        child_id = data.get("child_id")
        act_date = data.get("activity_date", date.today().isoformat())
        act_type = data.get("activity_type")
        start_time = data.get("start_time", datetime.now().strftime("%H:%M"))
        end_time = data.get("end_time")
        desc = data.get("description", "")
        staff_id = data.get("staff_id") or None

        try:
            aid = db.query("""
                INSERT INTO daily_activities (child_id, activity_date, activity_type, start_time, end_time, description, staff_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [child_id, act_date, act_type, start_time, end_time, desc, staff_id], commit=True)
            return jsonify({"success": True, "message": "Activity logged successfully!", "activity_id": aid})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# 7. Invoices & Payments API
@app.route("/api/invoices", methods=["GET", "POST"])
def api_invoices():
    if request.method == "GET":
        invoices = db.query("""
            SELECT 
                i.*,
                c.first_name || ' ' || c.last_name AS child_name,
                fp.plan_name,
                COALESCE((SELECT SUM(amount_paid) FROM payments p WHERE p.invoice_id = i.invoice_id), 0) AS amount_paid
            FROM invoices i
            JOIN children c ON i.child_id = c.child_id
            JOIN fee_plans fp ON i.plan_id = fp.plan_id
            ORDER BY i.invoice_id DESC
        """)
        return jsonify(invoices)
    elif request.method == "POST":
        data = request.json or {}
        child_id = data.get("child_id")
        plan_id = data.get("plan_id")
        period = data.get("billing_period", datetime.now().strftime("%B %Y"))
        total = float(data.get("total_amount", 0))
        discount = float(data.get("discount_amount", 0))
        net = total - discount
        due_date = data.get("due_date", date.today().isoformat())

        try:
            inv_id = db.query("""
                INSERT INTO invoices (child_id, plan_id, billing_period, total_amount, discount_amount, net_amount, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, [child_id, plan_id, period, total, discount, net, due_date], commit=True)
            return jsonify({"success": True, "message": "Invoice created successfully!", "invoice_id": inv_id})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route("/api/payments", methods=["POST"])
def api_record_payment():
    data = request.json or {}
    invoice_id = data.get("invoice_id")
    amount = float(data.get("amount_paid", 0))
    pay_mode = data.get("payment_mode", "Cash")
    trans_ref = data.get("transaction_ref", "")
    receipt_no = f"REC-{datetime.now().strftime('%y%m%d')}-{random.randint(1000, 9999)}"

    if not invoice_id or amount <= 0:
        return jsonify({"error": "Valid invoice ID and positive payment amount are required."}), 400

    try:
        # Note: Trigger 'trg_payment_update_invoice' automatically fires AFTER INSERT!
        pid = db.query("""
            INSERT INTO payments (invoice_id, amount_paid, payment_date, payment_mode, transaction_ref, receipt_number)
            VALUES (?, ?, DATE('now'), ?, ?, ?)
        """, [invoice_id, amount, pay_mode, trans_ref, receipt_no], commit=True)

        return jsonify({
            "success": True, 
            "message": f"Payment of ₹{amount:,.2f} recorded! Receipt: {receipt_no}", 
            "payment_id": pid,
            "receipt_number": receipt_no
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# 8. Interactive SQL Query Runner API
@app.route("/api/sql/execute", methods=["POST"])
def api_sql_execute():
    data = request.json or {}
    query_text = data.get("sql", "").strip()

    if not query_text:
        return jsonify({"error": "Empty SQL query provided"}), 400

    try:
        # Prevent harmful shell escapes
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query_text)
        
        # Check if query returned rows (e.g., SELECT or PRAGMA or SHOW)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            raw_rows = cursor.fetchall()
            
            # Format rows
            rows = []
            for row in raw_rows:
                if isinstance(row, dict):
                    rows.append(list(row.values()))
                else:
                    rows.append(list(row))
                    
            conn.commit()
            conn.close()
            return jsonify({
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "message": f"Query executed successfully ({len(rows)} rows returned)."
            })
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return jsonify({
                "success": True,
                "columns": ["Result"],
                "rows": [[f"Statement executed successfully. Rows affected: {affected}"]],
                "row_count": affected,
                "message": f"Command executed successfully. {affected} row(s) affected."
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Preset Queries Endpoint
@app.route("/api/sql/presets")
def api_sql_presets():
    presets = [
        {
            "id": 1,
            "title": "Comprehensive Children Directory (Multi-table View)",
            "description": "Demonstrates joined view of children, rooms, primary guardians, and calculated allergy counts.",
            "sql": "SELECT * FROM view_children_directory LIMIT 10;"
        },
        {
            "id": 2,
            "title": "Room Utilization & Occupancy Rate",
            "description": "Calculates current enrollment vs room capacity and lead caregiver assignment.",
            "sql": "SELECT * FROM view_room_summary;"
        },
        {
            "id": 3,
            "title": "Unpaid / Pending Invoices with Parent Contact",
            "description": "Shows children with overdue fees, parent phone/email, and total balance due.",
            "sql": "SELECT * FROM view_pending_dues;"
        },
        {
            "id": 4,
            "title": "Multi-Table INNER & LEFT JOIN with Aggregation",
            "description": "Fetches child details, enrolled room, tuition fee plan, and total payments received.",
            "sql": """SELECT 
    c.child_id,
    c.first_name || ' ' || c.last_name AS child_name,
    r.room_name,
    fp.plan_name,
    fp.amount AS plan_rate,
    COALESCE(SUM(p.amount_paid), 0) AS total_paid_to_date
FROM children c
JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN invoices i ON c.child_id = i.child_id
LEFT JOIN fee_plans fp ON i.plan_id = fp.plan_id
LEFT JOIN payments p ON i.invoice_id = p.invoice_id
GROUP BY c.child_id, r.room_name, fp.plan_name, fp.amount
ORDER BY c.child_id;"""
        },
        {
            "id": 5,
            "title": "Subquery with HAVING: High-Capacity Rooms",
            "description": "Filters rooms whose active child count exceeds 50% capacity.",
            "sql": """SELECT 
    r.room_name,
    r.capacity,
    COUNT(c.child_id) AS enrolled_count,
    ROUND(COUNT(c.child_id) * 100.0 / r.capacity, 1) AS pct_full
FROM rooms r
LEFT JOIN children c ON r.room_id = c.room_id AND c.status = 'Active'
GROUP BY r.room_id, r.room_name, r.capacity
HAVING COUNT(c.child_id) > 1
ORDER BY pct_full DESC;"""
        },
        {
            "id": 6,
            "title": "Correlated Subquery: Children with Severe Allergies",
            "description": "Uses EXISTS to find children requiring urgent medical vigilance.",
            "sql": """SELECT 
    c.child_id,
    c.first_name || ' ' || c.last_name AS child_name,
    c.blood_group,
    c.emergency_contact_phone
FROM children c
WHERE EXISTS (
    SELECT 1 FROM allergies_medical a
    WHERE a.child_id = c.child_id AND a.severity = 'Severe'
);"""
        },
        {
            "id": 7,
            "title": "Database Audit Logs (Trigger Output)",
            "description": "Inspects automated audit trail generated by database triggers.",
            "sql": "SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 15;"
        }
    ]
    return jsonify(presets)

# Reset Database to Seed Data
@app.route("/api/db-reset", methods=["POST"])
def api_db_reset():
    try:
        init_database(force_recreate=True)
        return jsonify({"success": True, "message": "Database reset and re-seeded with demo data!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    print(f"Starting Daycare Management System on http://127.0.0.1:5000 [Mode: {get_active_db_type()}]")
    app.run(host="127.0.0.1", port=5000, debug=True)

# EarlyRoots: Daycare & Creche Management System
### A Full-Featured Relational Database Management Systems (DBMS) Mini Project

> **Topic:** Daycare / Creche Management System  
> **Brand Name:** EarlyRoots (🌱)  
> **Frontend:** HTML5, CSS3, Modern JavaScript (Vanilla ES6, Fetch API)  
> **Backend:** Python Flask  
> **Database:** Dual-Engine Support (MySQL / MariaDB and Zero-Setup Embedded SQLite)  
> **Currency:** Indian Rupee (₹ INR)  
> **DBMS Core Concepts:** Primary & Foreign Keys, 1NF-3NF Normalization, Multi-Table JOINs, Virtual Views, Database Triggers, Stored Procedures, ACID Transactions, and Audit Trail.

---

## 🌟 Key Project Highlights

1. **Dual Database Engine Architecture:**
   - **Out-of-the-Box Mode (SQLite):** Runs immediately on any computer with Python installed—no database setup or server daemon required!
   - **University Lab Mode (MySQL):** Full MySQL schema with `ENGINE=InnoDB`, `DELIMITER //` triggers, stored procedures, and sample seed scripts ready for phpMyAdmin or MySQL Workbench.
   - The app auto-detects MySQL on port 3306 or gracefully uses SQLite, displaying the active database status in the UI!
2. **Database Triggers in Action:**
   - `trg_enforce_room_capacity`: Prevents overbooking rooms beyond licensed capacity.
   - `trg_payment_update_invoice`: Automatically calculates cumulative payments and updates invoice statuses (`Paid` / `Partially Paid`).
   - `trg_child_audit_insert` & `trg_child_audit_update`: Automatically populates the `audit_logs` table.
3. **5 Analytical & Operational Views:**
   - `view_children_directory`, `view_room_summary`, `view_pending_dues`, `view_daily_attendance_today`, `view_daily_activity_feed`.
4. **Interactive SQL Query Console (Evaluator's Favorite):**
   - Built-in web SQL editor where teachers and students can run custom SQL queries live, select from preset academic queries, and inspect query output tables in real time!
5. **Comprehensive Academic Report:**
   - Complete project documentation in `DBMS_PROJECT_REPORT.md` including ER Diagram (Mermaid), Normalization proofs (1NF to 3NF/BCNF), Relational mapping, and Top 20 Viva Voce Q&A!

---

## 📁 Project Directory Structure

```text
DBMS Project/
├── run.py                      # One-click launcher script (initializes DB & opens browser)
├── app.py                      # Flask Application Server (REST APIs & routes)
├── database.py                 # Unified database abstraction layer (MySQL & SQLite)
├── config.py                   # App configuration & DB connection parameters
├── test_app.py                 # Automated test suite (validates pages & triggers)
├── requirements.txt            # Python dependencies (flask, pymysql)
│
├── sql/                        # Complete SQL Scripts for submission & lab import
│   ├── mysql_schema.sql        # MySQL Tables, Foreign Keys, Constraints, Indexes
│   ├── mysql_triggers.sql      # MySQL Triggers (Capacity check, Payment sync, Audit)
│   ├── mysql_procedures.sql    # MySQL Stored Procedures (Enroll, Payment, Profile)
│   ├── mysql_views.sql         # MySQL Views (Directory, Utilization, Dues, Attendance)
│   ├── mysql_seed_data.sql     # Rich sample dataset for MySQL
│   ├── sqlite_schema.sql       # Standalone SQLite schema for SQLite Browser
│   └── complex_queries.sql     # 10+ Complex queries (JOINs, Subqueries, Having)
│
├── static/                     # Frontend Assets
│   ├── css/
│   │   └── style.css           # Modern daycare UI styling (Responsive & Accessible)
│   └── js/
│       └── app.js              # Client-side SPA logic (CRUD, Modals, Live SQL Console)
│
├── templates/                  # HTML Templates
│   ├── base.html               # Main layout with navigation sidebar & DB status badge
│   ├── index.html              # Dashboard with metrics, room occupancy & audit logs
│   ├── children.html           # Children directory, filters & enrollment modal
│   ├── guardians.html          # Parents/Guardians & emergency authorization
│   ├── rooms_staff.html        # Classroom capacities & educator staff directory
│   ├── attendance.html         # Daily check-in / check-out tracker & logs
│   ├── activities.html         # Daily meals, naps, play & incident timeline
│   ├── billing.html            # Tuition plans, invoices & trigger payment recorder
│   └── sql_console.html        # Interactive SQL Query Console & Schema inspector
│
├── DBMS_PROJECT_REPORT.md      # Comprehensive academic project report & Viva Q&A
└── README.md                   # Setup guide and documentation
```

---

## 🚀 Quick Start Guide (Zero-Setup Mode)

### Step 1: Open Terminal in the Project Directory
```powershell
cd "c:\Users\priya\OneDrive\Desktop\DBMS Project"
```

### Step 2: Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If dependencies are not yet installed in a new clone: `pip install -r requirements.txt`)*

### Step 3: Run the Application
```powershell
python run.py
```
The application will automatically:
1. Initialize the database and load rich sample records.
2. Launch the Flask web server on `http://127.0.0.1:5000`.
3. Open your default web browser directly to the dashboard!

---

## 🐬 Running with MySQL / XAMPP (Optional / Lab Submission)

If your college professor or lab evaluator specifically requires running against a live **MySQL** database:

1. Start your MySQL Server (via **XAMPP**, **WampServer**, or **MySQL Workbench**).
2. Open `config.py` and set your credentials:
   ```python
   MYSQL_HOST = "localhost"
   MYSQL_PORT = 3306
   MYSQL_USER = "root"
   MYSQL_PASSWORD = ""      # Your MySQL root password (often blank in XAMPP)
   MYSQL_DB = "daycare_db"
   ```
3. Import the SQL scripts in `sql/` into MySQL:
   - Run `sql/mysql_schema.sql`
   - Run `sql/mysql_views.sql`
   - Run `sql/mysql_triggers.sql`
   - Run `sql/mysql_procedures.sql`
   - Run `sql/mysql_seed_data.sql`
4. Run `python run.py`. The system will automatically detect MySQL and display **"MYSQL Active"** in the sidebar footer!

---

## 🧪 Testing the Project

You can run the built-in automated test suite anytime:
```powershell
python test_app.py
```
This tests all 8 web pages, REST API endpoints, and verifies that database triggers fire and update invoice statuses accurately.

---

## 🎓 University Lab Evaluation & Viva Voce

- Read `DBMS_PROJECT_REPORT.md` for complete academic documentation, including the **Mermaid ER Diagram**, **Normalization Proofs (1NF to 3NF)**, **Functional Dependencies**, and **Top 20 Viva Questions & Answers**.
- Open the **Live SQL Console** tab in the web app during your demo to execute any query or test preset DBMS queries right in front of your evaluator!

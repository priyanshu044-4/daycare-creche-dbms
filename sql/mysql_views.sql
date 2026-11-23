-- ====================================================================
-- DAYCARE / CRECHE MANAGEMENT SYSTEM
-- MySQL Database Views (Virtual Tables for Reporting & Analytics)
-- ====================================================================

USE daycare_db;

-- --------------------------------------------------------------------
-- VIEW 1: Comprehensive Children Directory
-- Combines child details, room info, primary guardian, and allergy count
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS view_children_directory;
CREATE VIEW view_children_directory AS
SELECT 
    c.child_id,
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    c.first_name,
    c.last_name,
    c.dob,
    TIMESTAMPDIFF(YEAR, c.dob, CURDATE()) AS age_years,
    c.gender,
    c.blood_group,
    c.status,
    c.enrollment_date,
    c.emergency_contact_phone,
    c.notes,
    r.room_id,
    r.room_name,
    r.age_group AS room_age_group,
    COALESCE(CONCAT(g.first_name, ' ', g.last_name), 'None Assigned') AS primary_guardian_name,
    COALESCE(g.relationship, 'N/A') AS guardian_relation,
    COALESCE(g.phone, 'N/A') AS guardian_phone,
    COALESCE(g.email, 'N/A') AS guardian_email,
    (SELECT COUNT(*) FROM allergies_medical a WHERE a.child_id = c.child_id) AS allergy_count
FROM children c
JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN child_guardians cg ON c.child_id = cg.child_id AND cg.is_primary_contact = 1
LEFT JOIN guardians g ON cg.guardian_id = g.guardian_id;

-- --------------------------------------------------------------------
-- VIEW 2: Room Capacity & Utilization Summary
-- Tracks occupancy percentage, available slots, and assigned lead teacher
-- --------------------------------------------------------------------
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
    COALESCE(CONCAT(s.first_name, ' ', s.last_name), 'Unassigned') AS lead_educator
FROM rooms r
LEFT JOIN children c ON r.room_id = c.room_id AND c.status = 'Active'
LEFT JOIN staff s ON r.room_id = s.assigned_room_id AND s.role = 'Lead Educator'
GROUP BY r.room_id, r.room_name, r.age_group, r.capacity, r.room_type, s.first_name, s.last_name;

-- --------------------------------------------------------------------
-- VIEW 3: Pending & Overdue Invoices with Guardian Contacts
-- Aggregates payments against invoices and shows outstanding balances
-- --------------------------------------------------------------------
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
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    g.first_name,
    g.last_name,
    CONCAT(g.first_name, ' ', g.last_name) AS guardian_name,
    g.phone AS guardian_phone,
    g.email AS guardian_email
FROM invoices i
JOIN children c ON i.child_id = c.child_id
LEFT JOIN payments p ON i.invoice_id = p.invoice_id
LEFT JOIN child_guardians cg ON c.child_id = cg.child_id AND cg.is_primary_contact = 1
LEFT JOIN guardians g ON cg.guardian_id = g.guardian_id
WHERE i.status IN ('Pending', 'Partially Paid', 'Overdue')
GROUP BY i.invoice_id, i.billing_period, i.net_amount, i.due_date, i.status, c.child_id, c.first_name, c.last_name, g.first_name, g.last_name, g.phone, g.email;

-- --------------------------------------------------------------------
-- VIEW 4: Today's Daily Attendance Status
-- Real-time view of attendance for active children
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS view_daily_attendance_today;
CREATE VIEW view_daily_attendance_today AS
SELECT 
    c.child_id,
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    r.room_name,
    COALESCE(a.attendance_date, CURDATE()) AS date,
    COALESCE(a.status, 'Not Marked') AS status,
    a.check_in_time,
    a.check_out_time,
    a.temperature_f,
    a.remarks
FROM children c
JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN attendance a ON c.child_id = a.child_id AND a.attendance_date = CURDATE()
WHERE c.status = 'Active';

-- --------------------------------------------------------------------
-- VIEW 5: Daily Activity Feed
-- Real-time timeline of child activities
-- --------------------------------------------------------------------
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
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    r.room_name,
    COALESCE(CONCAT(s.first_name, ' ', s.last_name), 'Staff') AS logged_by
FROM daily_activities da
JOIN children c ON da.child_id = c.child_id
JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN staff s ON da.staff_id = s.staff_id
ORDER BY da.activity_date DESC, da.start_time DESC;

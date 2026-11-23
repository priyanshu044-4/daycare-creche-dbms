-- ====================================================================
-- DAYCARE / CRECHE MANAGEMENT SYSTEM
-- Complex DBMS Queries Demonstration (For Viva, Evaluation & Reports)
-- ====================================================================

USE daycare_db;

-- --------------------------------------------------------------------
-- QUERY 1: Multi-Table JOIN (Children, Rooms, Primary Guardians, Fee Plans)
-- Retrieves comprehensive child enrollment profile with tuition plan
-- --------------------------------------------------------------------
SELECT 
    c.child_id,
    CONCAT(c.first_name, ' ', c.last_name) AS student_name,
    c.dob,
    r.room_name,
    CONCAT(g.first_name, ' ', g.last_name) AS guardian_name,
    g.relationship,
    g.phone AS emergency_phone,
    fp.plan_name,
    fp.amount AS monthly_tuition
FROM children c
INNER JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN child_guardians cg ON c.child_id = cg.child_id AND cg.is_primary_contact = 1
LEFT JOIN guardians g ON cg.guardian_id = g.guardian_id
LEFT JOIN invoices inv ON c.child_id = inv.child_id
LEFT JOIN fee_plans fp ON inv.plan_id = fp.plan_id
WHERE c.status = 'Active'
ORDER BY r.room_name, c.first_name;

-- --------------------------------------------------------------------
-- QUERY 2: GROUP BY with HAVING (Room Occupancy vs Maximum Capacity)
-- Identifies rooms operating above 50% capacity
-- --------------------------------------------------------------------
SELECT 
    r.room_id,
    r.room_name,
    r.capacity AS max_limit,
    COUNT(c.child_id) AS total_enrolled,
    ROUND((COUNT(c.child_id) * 100.0 / r.capacity), 2) AS occupancy_pct
FROM rooms r
LEFT JOIN children c ON r.room_id = c.room_id AND c.status = 'Active'
GROUP BY r.room_id, r.room_name, r.capacity
HAVING COUNT(c.child_id) > 0
ORDER BY occupancy_pct DESC;

-- --------------------------------------------------------------------
-- QUERY 3: Nested Subquery with Aggregation (High-Value Invoices)
-- Finds invoices whose net amount is strictly higher than average invoice amount
-- --------------------------------------------------------------------
SELECT 
    i.invoice_id,
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    i.billing_period,
    i.net_amount,
    i.status
FROM invoices i
JOIN children c ON i.child_id = c.child_id
WHERE i.net_amount > (
    SELECT AVG(net_amount) 
    FROM invoices
)
ORDER BY i.net_amount DESC;

-- --------------------------------------------------------------------
-- QUERY 4: Correlated Subquery (Children with Severe Allergies)
-- Identifies children who have at least one 'Severe' allergy alert
-- --------------------------------------------------------------------
SELECT 
    c.child_id,
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    c.blood_group,
    c.emergency_contact_phone,
    r.room_name
FROM children c
JOIN rooms r ON c.room_id = r.room_id
WHERE EXISTS (
    SELECT 1 
    FROM allergies_medical a
    WHERE a.child_id = c.child_id 
      AND a.severity = 'Severe'
);

-- --------------------------------------------------------------------
-- QUERY 5: Left Outer Join with Coalesce & Balance Computation
-- Calculates total unpaid fee dues per parent
-- --------------------------------------------------------------------
SELECT 
    CONCAT(g.first_name, ' ', g.last_name) AS parent_name,
    g.phone,
    g.email,
    COUNT(DISTINCT c.child_id) AS enrolled_children_count,
    SUM(i.net_amount) AS total_billed,
    COALESCE(SUM(p.amount_paid), 0) AS total_paid,
    (SUM(i.net_amount) - COALESCE(SUM(p.amount_paid), 0)) AS balance_outstanding
FROM guardians g
JOIN child_guardians cg ON g.guardian_id = cg.guardian_id
JOIN children c ON cg.child_id = c.child_id
JOIN invoices i ON c.child_id = i.child_id
LEFT JOIN payments p ON i.invoice_id = p.invoice_id
GROUP BY g.guardian_id, g.first_name, g.last_name, g.phone, g.email
HAVING balance_outstanding > 0
ORDER BY balance_outstanding DESC;

-- --------------------------------------------------------------------
-- QUERY 6: Daily Attendance Breakdown by Room (Cross-Tabulation)
-- Aggregates present, late, absent, and percentage attendance per classroom
-- --------------------------------------------------------------------
SELECT 
    r.room_name,
    COUNT(c.child_id) AS active_children,
    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
    SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) AS late_count,
    SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
    ROUND((SUM(CASE WHEN a.status IN ('Present', 'Late') THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(c.child_id), 0)), 1) AS attendance_rate_pct
FROM rooms r
JOIN children c ON r.room_id = c.room_id AND c.status = 'Active'
LEFT JOIN attendance a ON c.child_id = a.child_id AND a.attendance_date = CURDATE()
GROUP BY r.room_id, r.room_name;

-- --------------------------------------------------------------------
-- QUERY 7: Staff Workload & Room Assignment Analysis
-- Evaluates child-to-staff educator ratios in each room
-- --------------------------------------------------------------------
SELECT 
    r.room_name,
    r.age_group,
    CONCAT(s.first_name, ' ', s.last_name) AS lead_teacher,
    s.qualification,
    COUNT(c.child_id) AS assigned_children,
    CONCAT(COUNT(c.child_id), ' : 1') AS child_teacher_ratio
FROM rooms r
LEFT JOIN staff s ON r.room_id = s.assigned_room_id AND s.role = 'Lead Educator'
LEFT JOIN children c ON r.room_id = c.room_id AND c.status = 'Active'
GROUP BY r.room_id, r.room_name, r.age_group, s.first_name, s.last_name, s.qualification;

-- --------------------------------------------------------------------
-- QUERY 8: Activity Monitoring - Incident and Health Reports
-- Lists all critical incidents and medical logs
-- --------------------------------------------------------------------
SELECT 
    da.activity_date,
    da.start_time,
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    r.room_name,
    da.activity_type,
    da.description,
    CONCAT(st.first_name, ' ', st.last_name) AS logged_by_staff
FROM daily_activities da
JOIN children c ON da.child_id = c.child_id
JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN staff st ON da.staff_id = st.staff_id
WHERE da.activity_type IN ('Incident', 'Medication')
ORDER BY da.activity_date DESC, da.start_time DESC;

-- --------------------------------------------------------------------
-- QUERY 9: Set Operations (UNION) - Emergency Communication Directory
-- Unifies primary guardians and emergency secondary contacts
-- --------------------------------------------------------------------
SELECT 
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    CONCAT(g.first_name, ' ', g.last_name) AS contact_person,
    g.relationship,
    g.phone AS contact_number,
    'Primary Guardian' AS contact_role
FROM children c
JOIN child_guardians cg ON c.child_id = cg.child_id AND cg.is_primary_contact = 1
JOIN guardians g ON cg.guardian_id = g.guardian_id

UNION

SELECT 
    CONCAT(c.first_name, ' ', c.last_name) AS child_name,
    'Designated Emergency Phone' AS contact_person,
    'Emergency Hotline' AS relationship,
    c.emergency_contact_phone AS contact_number,
    'Direct Registry Record' AS contact_role
FROM children c
ORDER BY child_name, contact_role;

-- --------------------------------------------------------------------
-- QUERY 10: Audit Log Examination
-- Reviews recent database modifications, trigger outputs, and mutations
-- --------------------------------------------------------------------
SELECT 
    log_id,
    action_type,
    table_name,
    record_id,
    details,
    created_at
FROM audit_logs
ORDER BY log_id DESC
LIMIT 20;

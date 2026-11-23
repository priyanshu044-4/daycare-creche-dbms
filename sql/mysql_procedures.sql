-- ====================================================================
-- DAYCARE / CRECHE MANAGEMENT SYSTEM
-- MySQL Stored Procedures (Encapsulated Business Operations & Transactions)
-- ====================================================================

USE daycare_db;

DELIMITER //

-- --------------------------------------------------------------------
-- PROCEDURE 1: sp_EnrollChild
-- Atomically registers a child, associates primary guardian, and logs action
-- --------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_EnrollChild//
CREATE PROCEDURE sp_EnrollChild(
    IN p_first_name VARCHAR(50),
    IN p_last_name VARCHAR(50),
    IN p_dob DATE,
    IN p_gender VARCHAR(10),
    IN p_blood_group VARCHAR(5),
    IN p_room_id INT,
    IN p_guardian_id INT,
    IN p_emergency_phone VARCHAR(20),
    IN p_notes TEXT,
    OUT p_new_child_id INT
)
BEGIN
    DECLARE exit handler for sqlexception
    BEGIN
        -- Rollback on any SQL error
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Insert Child record
    INSERT INTO children (
        first_name, last_name, dob, gender, blood_group, 
        room_id, enrollment_date, status, emergency_contact_phone, notes
    ) VALUES (
        p_first_name, p_last_name, p_dob, p_gender, p_blood_group,
        p_room_id, CURDATE(), 'Active', p_emergency_phone, p_notes
    );

    SET p_new_child_id = LAST_INSERT_ID();

    -- 2. Link with Guardian (as primary contact)
    IF p_guardian_id IS NOT NULL AND p_guardian_id > 0 THEN
        INSERT INTO child_guardians (child_id, guardian_id, is_primary_contact, pickup_authorized)
        VALUES (p_new_child_id, p_guardian_id, 1, 1);
    END IF;

    COMMIT;
END//

-- --------------------------------------------------------------------
-- PROCEDURE 2: sp_RecordPayment
-- Records fee payment, generates unique receipt code, handled within ACID transaction
-- --------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_RecordPayment//
CREATE PROCEDURE sp_RecordPayment(
    IN p_invoice_id INT,
    IN p_amount DECIMAL(10,2),
    IN p_payment_date DATE,
    IN p_payment_mode VARCHAR(20),
    IN p_trans_ref VARCHAR(100),
    OUT p_receipt_no VARCHAR(50),
    OUT p_payment_id INT
)
BEGIN
    DECLARE v_receipt_prefix VARCHAR(10);
    DECLARE exit handler for sqlexception
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Generate unique receipt number: REC-<TIMESTAMP>-<RAND>
    SET p_receipt_no = CONCAT('REC-', DATE_FORMAT(NOW(), '%y%m%d'), '-', FLOOR(1000 + (RAND() * 9000)));

    -- Insert payment record
    INSERT INTO payments (
        invoice_id, amount_paid, payment_date, payment_mode, transaction_ref, receipt_number
    ) VALUES (
        p_invoice_id, p_amount, p_payment_date, p_payment_mode, p_trans_ref, p_receipt_no
    );

    SET p_payment_id = LAST_INSERT_ID();

    COMMIT;
END//

-- --------------------------------------------------------------------
-- PROCEDURE 3: sp_GetDailyAttendanceSummary
-- Aggregates present, absent, late, and excused counts for a specific date
-- --------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_GetDailyAttendanceSummary//
CREATE PROCEDURE sp_GetDailyAttendanceSummary(
    IN p_date DATE
)
BEGIN
    SELECT 
        r.room_name,
        COUNT(c.child_id) AS total_enrolled,
        SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
        SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
        SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) AS late_count,
        SUM(CASE WHEN a.status = 'Excused' THEN 1 ELSE 0 END) AS excused_count,
        SUM(CASE WHEN a.status IS NULL THEN 1 ELSE 0 END) AS unrecorded_count
    FROM rooms r
    JOIN children c ON r.room_id = c.room_id AND c.status = 'Active'
    LEFT JOIN attendance a ON c.child_id = a.child_id AND a.attendance_date = p_date
    GROUP BY r.room_id, r.room_name;
END//

-- --------------------------------------------------------------------
-- PROCEDURE 4: sp_GetChildFullProfile
-- Returns consolidated profile details for a given child
-- --------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_GetChildFullProfile//
CREATE PROCEDURE sp_GetChildFullProfile(
    IN p_child_id INT
)
BEGIN
    -- Query 1: Child & Room details
    SELECT 
        c.*, 
        r.room_name, 
        r.age_group AS room_age_group
    FROM children c
    JOIN rooms r ON c.room_id = r.room_id
    WHERE c.child_id = p_child_id;

    -- Query 2: Associated Guardians
    SELECT 
        g.*, 
        cg.is_primary_contact, 
        cg.pickup_authorized
    FROM guardians g
    JOIN child_guardians cg ON g.guardian_id = cg.guardian_id
    WHERE cg.child_id = p_child_id;

    -- Query 3: Active Allergies & Medical alerts
    SELECT * 
    FROM allergies_medical 
    WHERE child_id = p_child_id;

    -- Query 4: Billing Summary
    SELECT 
        COUNT(invoice_id) AS total_invoices,
        COALESCE(SUM(net_amount), 0) AS total_billed,
        COALESCE(SUM(CASE WHEN status = 'Paid' THEN net_amount ELSE 0 END), 0) AS total_settled
    FROM invoices 
    WHERE child_id = p_child_id;
END//

DELIMITER ;

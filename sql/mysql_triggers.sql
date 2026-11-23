-- ====================================================================
-- DAYCARE / CRECHE MANAGEMENT SYSTEM
-- MySQL Database Triggers (Automated Business Logic & Auditing)
-- ====================================================================

USE daycare_db;

DELIMITER //

-- --------------------------------------------------------------------
-- TRIGGER 1: Enforce Room Capacity Before Child Enrollment
-- Prevents overfilling rooms beyond approved capacity
-- --------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_enforce_room_capacity//
CREATE TRIGGER trg_enforce_room_capacity
BEFORE INSERT ON children
FOR EACH ROW
BEGIN
    DECLARE current_count INT;
    DECLARE max_capacity INT;

    SELECT COUNT(*) INTO current_count
    FROM children
    WHERE room_id = NEW.room_id AND status = 'Active';

    SELECT capacity INTO max_capacity
    FROM rooms
    WHERE room_id = NEW.room_id;

    IF current_count >= max_capacity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Enrollment Error: Target home care space has reached its maximum cozy capacity!';
    END IF;
END//

-- --------------------------------------------------------------------
-- TRIGGER 2: Audit Log on New Child Registration
-- Automatically logs new student enrollment
-- --------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_child_audit_insert//
CREATE TRIGGER trg_child_audit_insert
AFTER INSERT ON children
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (action_type, table_name, record_id, details)
    VALUES (
        'INSERT', 
        'children', 
        NEW.child_id, 
        CONCAT('Enrolled child: ', NEW.first_name, ' ', NEW.last_name, ' into Room ID ', NEW.room_id)
    );
END//

-- --------------------------------------------------------------------
-- TRIGGER 3: Audit Log on Child Record Update
-- Tracks room re-assignments or status changes
-- --------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_child_audit_update//
CREATE TRIGGER trg_child_audit_update
AFTER UPDATE ON children
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (action_type, table_name, record_id, details)
    VALUES (
        'UPDATE', 
        'children', 
        NEW.child_id, 
        CONCAT('Updated child status to: ', NEW.status, ', Room ID: ', NEW.room_id)
    );
END//

-- --------------------------------------------------------------------
-- TRIGGER 4: Automatically Update Invoice Status Upon Payment
-- Computes cumulative payments and updates invoice to Paid or Partially Paid
-- --------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_payment_update_invoice//
CREATE TRIGGER trg_payment_update_invoice
AFTER INSERT ON payments
FOR EACH ROW
BEGIN
    DECLARE total_paid DECIMAL(10,2);
    DECLARE net_inv_amount DECIMAL(10,2);

    -- Calculate total payments received for this invoice
    SELECT COALESCE(SUM(amount_paid), 0) INTO total_paid
    FROM payments
    WHERE invoice_id = NEW.invoice_id;

    -- Fetch total invoice bill amount
    SELECT net_amount INTO net_inv_amount
    FROM invoices
    WHERE invoice_id = NEW.invoice_id;

    -- Update invoice status
    IF total_paid >= net_inv_amount THEN
        UPDATE invoices SET status = 'Paid' WHERE invoice_id = NEW.invoice_id;
    ELSEIF total_paid > 0 THEN
        UPDATE invoices SET status = 'Partially Paid' WHERE invoice_id = NEW.invoice_id;
    END IF;

    -- Record in audit logs
    INSERT INTO audit_logs (action_type, table_name, record_id, details)
    VALUES (
        'INSERT',
        'payments',
        NEW.payment_id,
        CONCAT('Recorded payment of ₹', NEW.amount_paid, ' for Invoice #', NEW.invoice_id, ' (Mode: ', NEW.payment_mode, ')')
    );
END//

DELIMITER ;

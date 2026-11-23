-- ====================================================================
-- KILKARI CRECHE & DAYCARE MANAGEMENT SYSTEM
-- Sample Data Insertion Script (MySQL Compatible with Indian Names & INR)
-- ====================================================================

USE daycare_db;

-- 1. Insert Classrooms / Pods (Indian Preschool naming)
INSERT INTO rooms (room_name, age_group, capacity, room_type) VALUES
('Shishu Vatika', '0-12 months', 8, 'Infant Nest'),
('Nanhe Kadam', '1-2 years', 12, 'Toddler Playgroup'),
('Bal Vatika', '2-3.5 years', 15, 'Nursery Learning Pod'),
('Tarang Prep', '3.5-5 years', 18, 'Kindergarten Activity Lab');

-- 2. Insert Staff Members (Indian Educators & Healthcare Staff)
INSERT INTO staff (first_name, last_name, role, phone, email, qualification, assigned_room_id, hire_date, salary) VALUES
('Sunita', 'Deshmukh', 'Administrator', '9820112233', 'sunita.admin@kilkari.in', 'M.Ed Early Childhood Education', NULL, '2022-01-15', 55000.00),
('Anita', 'Menon', 'Lead Educator', '9820112234', 'anita.m@kilkari.in', 'B.Ed & Montessori Certified', 1, '2022-03-01', 42000.00),
('Rajeshwari', 'Pillai', 'Lead Educator', '9820112235', 'rajeshwari.p@kilkari.in', 'Diploma in Child Psychology', 2, '2022-06-10', 40000.00),
('Meenakshi', 'Sundaram', 'Lead Educator', '9820112236', 'meenakshi.s@kilkari.in', 'B.Sc Child Development', 3, '2023-01-10', 41000.00),
('Farhan', 'Akhtar', 'Lead Educator', '9820112237', 'farhan.a@kilkari.in', 'B.A Primary Education', 4, '2023-04-15', 39000.00),
('Sister Mary', 'Joseph', 'Nurse', '9820112238', 'mary.nurse@kilkari.in', 'Registered Pediatric Nurse (B.Sc Nursing)', NULL, '2022-08-01', 45000.00),
('Lakshmi', 'Bai', 'Caregiver', '9820112239', 'lakshmi.b@kilkari.in', 'Certified Child Care Attendant', 2, '2023-09-01', 30000.00),
('Geeta', 'Devi', 'Caregiver', '9820112240', 'geeta.d@kilkari.in', 'CPR & First Aid Certified', 1, '2023-11-15', 30000.00);

-- 3. Insert Guardians / Parents (Indian Names & Metro Addresses)
INSERT INTO guardians (first_name, last_name, relationship, phone, email, address, occupation) VALUES
('Rajesh', 'Sharma', 'Father', '9811223301', 'rajesh.sharma@gmail.com', 'Flat 402, Green Glen Layout, Bellandur, Bengaluru', 'Senior Software Architect'),
('Sunita', 'Sharma', 'Mother', '9811223302', 'sunita.sharma@yahoo.co.in', 'Flat 402, Green Glen Layout, Bellandur, Bengaluru', 'Pediatric Specialist'),
('Vikram', 'Verma', 'Father', '9811223303', 'vikram.v@techcorp.in', 'A-12, Sector 54, Golf Course Road, Gurugram', 'Investment Banking Director'),
('Pooja', 'Verma', 'Mother', '9811223304', 'pooja.verma@gmail.com', 'A-12, Sector 54, Golf Course Road, Gurugram', 'Urban Landscape Architect'),
('Amit', 'Patel', 'Father', '9811223305', 'amit.patel@rediffmail.com', '14 Sunrise Apartments, Bandra West, Mumbai', 'Chartered Accountant'),
('Priya', 'Iyer', 'Mother', '9811223306', 'priya.iyer@gmail.com', 'Plot 88, Anna Nagar West, Chennai', 'Data Science Lead'),
('Suresh', 'Reddy', 'Father', '9811223307', 'suresh.reddy@hyderabad.net', '202 Jubilee Hills, Road No. 36, Hyderabad', 'Civil Engineering Consultant'),
('Neha', 'Sen', 'Mother', '9811223308', 'neha.sen@gmail.com', 'Block CD, Sector 1, Salt Lake, Kolkata', 'Associate Professor'),
('Ramesh', 'Nair', 'Father', '9811223309', 'ramesh.nair@outlook.com', '77 Panampilly Nagar, Kochi, Kerala', 'Marketing Director'),
('Deepa', 'Gupta', 'Mother', '9811223310', 'deepa.gupta@gmail.com', 'B-4, Vasant Kunj, New Delhi', 'High Court Advocate');

-- 4. Insert Children (Indian Names)
INSERT INTO children (first_name, last_name, dob, gender, blood_group, room_id, enrollment_date, status, emergency_contact_phone, notes) VALUES
('Aarav', 'Sharma', '2026-03-15', 'Male', 'O+', 1, '2026-06-01', 'Active', '9811223301', 'Needs soft lullaby before nap time'),
('Ananya', 'Sharma', '2024-05-20', 'Female', 'O+', 3, '2025-01-10', 'Active', '9811223301', 'Very cheerful, loves coloring rangoli patterns'),
('Vihaan', 'Verma', '2025-08-11', 'Male', 'B+', 2, '2026-02-01', 'Active', '9811223303', 'Fascinated by wooden puzzle blocks'),
('Isha', 'Verma', '2023-11-04', 'Female', 'A+', 4, '2024-07-15', 'Active', '9811223304', 'Enjoys Panchatantra story sessions'),
('Advait', 'Patel', '2026-01-10', 'Male', 'A-', 1, '2026-04-01', 'Active', '9811223305', 'Formula fed every 3 hours as per schedule'),
('Diya', 'Iyer', '2025-02-14', 'Female', 'B-', 2, '2025-09-01', 'Active', '9811223306', 'Sensitive to sudden loud claps or noise'),
('Kabir', 'Reddy', '2024-10-30', 'Male', 'AB+', 3, '2025-04-10', 'Active', '9811223307', 'Enjoys stacking clay cups and blocks'),
('Meera', 'Sen', '2026-05-18', 'Female', 'AB+', 1, '2026-08-01', 'Active', '9811223308', 'Takes small teething ring before afternoon rest'),
('Reyansh', 'Nair', '2023-09-12', 'Male', 'O-', 4, '2024-03-01', 'Active', '9811223309', 'Loves rhymes and outdoor slide'),
('Saanvi', 'Gupta', '2025-04-22', 'Female', 'A+', 2, '2025-11-01', 'Active', '9811223310', 'Grandparents authorized for evening pickup');

-- 5. Child-Guardian Relationships
INSERT INTO child_guardians (child_id, guardian_id, is_primary_contact, pickup_authorized) VALUES
(1, 1, 1, 1), (1, 2, 0, 1),
(2, 1, 1, 1), (2, 2, 0, 1),
(3, 3, 1, 1), (3, 4, 0, 1),
(4, 3, 0, 1), (4, 4, 1, 1),
(5, 5, 1, 1),
(6, 6, 1, 1),
(7, 7, 1, 1),
(8, 8, 1, 1),
(9, 9, 1, 1),
(10, 10, 1, 1);

-- 6. Allergies & Medical Notes
INSERT INTO allergies_medical (child_id, allergen_type, allergen_name, severity, action_plan) VALUES
(1, 'Food', 'Cow Milk Protein (Lactose)', 'Moderate', 'Use soy/almond milk formula strictly'),
(2, 'Food', 'Peanuts & Tree Nuts', 'Severe', 'Keep EpiPen handy, call Apollo emergency'),
(3, 'Environmental', 'Dust Mites & Pollen', 'Mild', 'Keep play mat clean, administer cetirizine syrup if sneezing'),
(6, 'Food', 'Egg Albumin', 'Severe', 'Strict egg-free diet, notify creche kitchen cook'),
(7, 'Medicine', 'Penicillin & Amoxicillin', 'Severe', 'Medical alert band worn; inform attending doctor immediately'),
(9, 'Food', 'Gluten / Wheat', 'Moderate', 'Provide gluten-free ragi or rice snacks and khichdi');

-- 7. Fee Plans (in INR ₹)
INSERT INTO fee_plans (plan_name, description, frequency, amount) VALUES
('Shishu Full-Day Infant Care', 'Full daycare with nutrition, warm oil massage, diapering, and nap logs (8am-6pm)', 'Monthly', 14500.00),
('Nanhe Kadam Toddler Playgroup', 'Structured motor skills, sensory play, fresh hot lunch, and nap (8am-5pm)', 'Monthly', 11500.00),
('Bal Vatika Half-Day Program', 'Morning early learning, music, and socialization (8:30am-12:30pm)', 'Monthly', 7500.00),
('Tarang Pre-K Extended Day', 'School readiness curriculum with evening activity club (8am-6pm)', 'Monthly', 12500.00);

-- 8. Invoices (in INR ₹)
INSERT INTO invoices (child_id, plan_id, billing_period, total_amount, discount_amount, net_amount, due_date, status) VALUES
(1, 1, 'November 2026', 14500.00, 0.00, 14500.00, '2026-11-28', 'Paid'),
(2, 3, 'November 2026', 7500.00, 500.00, 7000.00, '2026-11-28', 'Paid'),
(3, 2, 'November 2026', 11500.00, 0.00, 11500.00, '2026-11-28', 'Partially Paid'),
(4, 4, 'November 2026', 12500.00, 0.00, 12500.00, '2026-11-20', 'Overdue'),
(5, 1, 'November 2026', 14500.00, 0.00, 14500.00, '2026-11-28', 'Paid'),
(6, 2, 'November 2026', 11500.00, 0.00, 11500.00, '2026-11-25', 'Pending'),
(7, 3, 'November 2026', 7500.00, 0.00, 7500.00, '2026-11-28', 'Pending'),
(8, 1, 'November 2026', 14500.00, 1000.00, 13500.00, '2026-11-28', 'Paid'),
(9, 4, 'November 2026', 12500.00, 0.00, 12500.00, '2026-11-15', 'Overdue'),
(10, 2, 'November 2026', 11500.00, 0.00, 11500.00, '2026-11-28', 'Paid');

-- 9. Payments (UPI / NetBanking / Cards in ₹)
INSERT INTO payments (invoice_id, amount_paid, payment_date, payment_mode, transaction_ref, receipt_number) VALUES
(1, 14500.00, '2026-11-02', 'UPI', 'UPI/2026/GPay/98123', 'REC-001'),
(2, 7000.00, '2026-11-03', 'UPI', 'UPI/2026/PhonePe/77612', 'REC-002'),
(3, 6000.00, '2026-11-04', 'NetBanking', 'HDFC-IMPS-88412', 'REC-003'),
(5, 14500.00, '2026-11-05', 'UPI', 'UPI/2026/Paytm/33120', 'REC-004'),
(8, 13500.00, '2026-11-02', 'Card', 'TXN-ICICI-77112', 'REC-005'),
(10, 11500.00, '2026-11-06', 'Cash', 'CASH-REC-101', 'REC-006');

-- 10. Daily Attendance
INSERT INTO attendance (child_id, attendance_date, check_in_time, check_out_time, status, temperature_f, checked_in_by_staff_id, remarks) VALUES
(1, CURDATE(), '08:15:00', NULL, 'Present', 98.4, 2, 'Arrived cheerfully with mother'),
(2, CURDATE(), '08:30:00', NULL, 'Present', 98.2, 4, 'Carrying drawing book'),
(3, CURDATE(), '08:45:00', NULL, 'Present', 98.6, 3, 'Temperature checked, normal'),
(4, CURDATE(), NULL, NULL, 'Absent', NULL, 5, 'Family out of station for wedding'),
(5, CURDATE(), '08:20:00', NULL, 'Present', 98.1, 2, 'Handed over warm formula flask'),
(6, CURDATE(), '09:05:00', NULL, 'Late', 98.5, 3, 'Traffic delay on Western Express Highway'),
(7, CURDATE(), '08:40:00', NULL, 'Present', 98.3, 4, 'Participating actively in morning prayer'),
(8, CURDATE(), '08:10:00', NULL, 'Present', 98.0, 2, 'Morning diaper check completed'),
(9, CURDATE(), NULL, NULL, 'Excused', NULL, 5, 'Pediatric vaccination appointment'),
(10, CURDATE(), '08:50:00', NULL, 'Present', 98.4, 3, 'Brought favourite soft toy');

-- 11. Daily Activities (Indian Nutrition & Activities)
INSERT INTO daily_activities (child_id, activity_date, activity_type, start_time, end_time, description, staff_id) VALUES
(1, CURDATE(), 'Meal', '09:00:00', '09:25:00', 'Drank 150ml warm soy milk formula peacefully', 8),
(1, CURDATE(), 'Nap', '10:00:00', '11:15:00', 'Restful morning sleep in Shishu crib #2', 8),
(2, CURDATE(), 'Play/Learning', '09:30:00', '10:30:00', 'Clay modeling and Diya painting activity', 4),
(3, CURDATE(), 'Meal', '09:15:00', '09:45:00', 'Ate warm Moong Dal Khichdi with pure cow ghee', 7),
(5, CURDATE(), 'Diaper/Potty', '09:30:00', '09:40', 'Diaper change, rash cream applied', 2),
(6, CURDATE(), 'Play/Learning', '09:30:00', '10:15:00', 'Sensory sand play and alphabet puzzle circle', 3),
(7, CURDATE(), 'Meal', '10:00:00', '10:25:00', 'Finished mashed banana and soft Idli with ghee', 4),
(10, CURDATE(), 'Play/Learning', '09:15:00', '10:00:00', 'Panchatantra story recitation: "The Clever Hare"', 3);

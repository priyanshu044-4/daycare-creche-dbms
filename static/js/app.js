/**
 * KILKARI CRECHE & DAYCARE MANAGEMENT SYSTEM
 * Frontend JavaScript Application Logic
 * Supports Indian Names & INR (₹) Currency
 */

// ---------------- Toast Notifications ----------------
function showToast(message, type = "success") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === "success" ? "✓" : "⚠"}</span>
    <div>${message}</div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ---------------- Modal Helpers ----------------
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

// Close modals when clicking outside modal-box
window.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("active");
  }
});

// ---------------- Dashboard Page Logic ----------------
async function loadDashboard() {
  const statsContainer = document.getElementById("dashboard-stats");
  if (!statsContainer) return;

  try {
    const res = await fetch("/api/stats");
    const data = await res.json();

    document.getElementById("stat-children").innerText = data.total_children;
    document.getElementById("stat-present").innerText = data.present_today;
    document.getElementById("stat-staff").innerText = data.total_staff;
    document.getElementById("stat-dues").innerText = "₹" + Number(data.pending_amount).toLocaleString("en-IN");

    // Room Occupancy List
    const roomContainer = document.getElementById("dashboard-rooms");
    if (roomContainer && data.room_occupancy) {
      roomContainer.innerHTML = data.room_occupancy.map(r => `
        <div style="margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 600; margin-bottom: 4px;">
            <span>${r.room_name} (${r.age_group || ""})</span>
            <span>${r.current_enrolled} / ${r.capacity} (${r.occupancy_percentage}%)</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar ${r.occupancy_percentage >= 80 ? 'warning' : ''}" style="width: ${Math.min(r.occupancy_percentage, 100)}%;"></div>
          </div>
          <div style="font-size: 12px; color: var(--gray-500);">Lead Educator: ${r.lead_educator}</div>
        </div>
      `).join("");
    }

    // Recent Audit Logs (Triggers Demo)
    const logsContainer = document.getElementById("dashboard-logs");
    if (logsContainer && data.recent_logs) {
      logsContainer.innerHTML = data.recent_logs.map(log => `
        <tr>
          <td><span class="badge ${log.action_type === 'INSERT' ? 'badge-success' : 'badge-info'}">${log.action_type}</span></td>
          <td><strong>${log.table_name}</strong></td>
          <td>${log.details}</td>
          <td style="font-size: 12px; color: var(--gray-500);">${log.created_at}</td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Dashboard load failed:", err);
  }
}

// ---------------- Children Management ----------------
async function loadChildren() {
  const tableBody = document.getElementById("children-table-body");
  if (!tableBody) return;

  const status = document.getElementById("filter-status")?.value || "";
  const roomId = document.getElementById("filter-room")?.value || "";

  let url = "/api/children?";
  if (status) url += `status=${encodeURIComponent(status)}&`;
  if (roomId) url += `room_id=${encodeURIComponent(roomId)}&`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    if (data.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px;">No children found matching criteria.</td></tr>`;
      return;
    }

    tableBody.innerHTML = data.map(c => `
      <tr>
        <td><strong>#${c.child_id}</strong></td>
        <td>
          <div style="font-weight: 600; color: var(--gray-900); font-size: 15px;">${c.child_name}</div>
          <div style="font-size: 12px; color: var(--gray-500);">DOB: ${c.dob} (Blood: ${c.blood_group || 'N/A'})</div>
        </td>
        <td><span class="badge badge-info">${c.room_name}</span></td>
        <td>
          <div style="font-weight: 500;">${c.primary_guardian_name}</div>
          <div style="font-size: 12px; color: var(--gray-500);">${c.guardian_phone} (${c.guardian_relation})</div>
        </td>
        <td>
          ${c.allergy_count > 0 
            ? `<span class="badge badge-danger">⚠ ${c.allergy_count} Alert(s)</span>` 
            : `<span class="badge badge-success">No Known Alerts</span>`}
        </td>
        <td><span class="badge ${c.status === 'Active' ? 'badge-success' : 'badge-gray'}">${c.status}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewChildDetails(${c.child_id})">Profile</button>
          <button class="btn btn-danger btn-sm" onclick="deleteChild(${c.child_id}, '${c.child_name}')">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading children:", err);
  }
}

async function viewChildDetails(childId) {
  try {
    const res = await fetch(`/api/children/${childId}`);
    const data = await res.json();
    if (data.error) {
      showToast(data.error, "error");
      return;
    }

    const c = data.child;
    document.getElementById("modal-child-name").innerText = `${c.child_name} (ID #${c.child_id})`;
    document.getElementById("modal-child-info").innerHTML = `
      <div class="form-grid-3" style="background: var(--gray-50); padding: 14px; border-radius: 8px; margin-bottom: 16px; border: 1px solid var(--gray-200);">
        <div><strong>DOB:</strong> ${c.dob}</div>
        <div><strong>Gender:</strong> ${c.gender}</div>
        <div><strong>Blood Group:</strong> ${c.blood_group || 'Not specified'}</div>
        <div><strong>Classroom:</strong> ${c.room_name}</div>
        <div><strong>Enrollment:</strong> ${c.enrollment_date}</div>
        <div><strong>Emergency Contact:</strong> +91 ${c.emergency_contact_phone}</div>
      </div>
    `;

    // Guardians
    const gContainer = document.getElementById("modal-child-guardians");
    gContainer.innerHTML = data.guardians.map(g => `
      <li style="margin-bottom: 8px; font-size: 14px; background: #fffdfa; padding: 10px; border-radius: 6px; border: 1px solid var(--gray-200);">
        <strong>${g.first_name} ${g.last_name}</strong> (${g.relationship}) - Phone: <strong>+91 ${g.phone}</strong> | Authorized Pickup: <strong>${g.pickup_authorized ? 'Yes' : 'No'}</strong>
        <div style="font-size: 12px; color: var(--gray-500); margin-top: 2px;">Address: ${g.address}</div>
      </li>
    `).join("") || "<li>No guardian linked.</li>";

    // Allergies
    const aContainer = document.getElementById("modal-child-allergies");
    aContainer.innerHTML = data.allergies.map(a => `
      <div style="background: var(--danger-light); border-left: 4px solid var(--danger); padding: 10px; margin-bottom: 8px; border-radius: 4px;">
        <strong style="color: var(--danger);">${a.allergen_name}</strong> (${a.allergen_type} - Severity: ${a.severity})
        <div style="font-size: 13px; color: var(--gray-700); margin-top: 3px;"><strong>Action Protocol:</strong> ${a.action_plan || 'Consult creche nurse'}</div>
      </div>
    `).join("") || "<p style='color: var(--gray-500);'>No known allergies or medical restrictions recorded.</p>";

    openModal("modal-view-child");
  } catch (err) {
    showToast("Failed to fetch child profile", "error");
  }
}

async function handleEnrollChild(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    first_name: form.first_name.value,
    last_name: form.last_name.value,
    dob: form.dob.value,
    gender: form.gender.value,
    blood_group: form.blood_group.value,
    room_id: form.room_id.value,
    guardian_id: form.guardian_id.value,
    emergency_contact_phone: form.emergency_contact_phone.value,
    notes: form.notes.value
  };

  try {
    const res = await fetch("/api/children", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, "success");
      form.reset();
      closeModal("modal-enroll-child");
      loadChildren();
    } else {
      showToast(result.error || "Enrollment failed", "error");
    }
  } catch (err) {
    showToast("Network error submitting form", "error");
  }
}

async function deleteChild(childId, childName) {
  if (!confirm(`Are you sure you want to withdraw ${childName} (Child ID #${childId})? Linked records will be cascaded.`)) {
    return;
  }
  try {
    const res = await fetch(`/api/children/${childId}`, { method: "DELETE" });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, "success");
      loadChildren();
    } else {
      showToast(result.error, "error");
    }
  } catch (err) {
    showToast("Error deleting child", "error");
  }
}

// ---------------- Guardians Management ----------------
async function loadGuardians() {
  const tableBody = document.getElementById("guardians-table-body");
  if (!tableBody) return;

  try {
    const res = await fetch("/api/guardians");
    const data = await res.json();

    tableBody.innerHTML = data.map(g => `
      <tr>
        <td><strong>#${g.guardian_id}</strong></td>
        <td>
          <div style="font-weight: 600; font-size: 15px;">${g.first_name} ${g.last_name}</div>
          <div style="font-size: 12px; color: var(--gray-500);">${g.occupation || 'N/A'}</div>
        </td>
        <td><span class="badge badge-info">${g.relationship}</span></td>
        <td><strong>+91 ${g.phone}</strong></td>
        <td>${g.email || 'N/A'}</td>
        <td style="max-width: 240px; font-size: 13px;">${g.address}</td>
        <td><span class="badge badge-success">${g.linked_children_count} child(ren)</span></td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading guardians:", err);
  }
}

async function handleAddGuardian(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    first_name: form.first_name.value,
    last_name: form.last_name.value,
    relationship: form.relationship.value,
    phone: form.phone.value,
    email: form.email.value,
    address: form.address.value,
    occupation: form.occupation.value
  };

  try {
    const res = await fetch("/api/guardians", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, "success");
      form.reset();
      closeModal("modal-add-guardian");
      loadGuardians();
    } else {
      showToast(result.error || "Failed to add guardian", "error");
    }
  } catch (err) {
    showToast("Network error submitting form", "error");
  }
}

// ---------------- Attendance Logic ----------------
async function loadAttendance() {
  const tableBody = document.getElementById("attendance-table-body");
  if (!tableBody) return;

  const attDate = document.getElementById("attendance-date")?.value || "";
  const roomId = document.getElementById("attendance-room")?.value || "";

  let url = `/api/attendance?date=${encodeURIComponent(attDate)}&`;
  if (roomId) url += `room_id=${encodeURIComponent(roomId)}`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    tableBody.innerHTML = data.map(r => `
      <tr>
        <td><strong>#${r.child_id}</strong></td>
        <td><strong style="font-size: 15px;">${r.child_name}</strong></td>
        <td><span class="badge badge-info">${r.room_name}</span></td>
        <td>
          <span class="badge ${
            r.status === 'Present' ? 'badge-success' :
            r.status === 'Late' ? 'badge-warning' :
            r.status === 'Absent' ? 'badge-danger' : 'badge-gray'
          }">
            ${r.status}
          </span>
        </td>
        <td>${r.check_in_time || '--:--'}</td>
        <td>${r.check_out_time || '--:--'}</td>
        <td>${r.temperature_f ? r.temperature_f + '°F' : 'N/A'}</td>
        <td>
          <button class="btn btn-success btn-sm" onclick="quickMarkAttendance(${r.child_id}, 'Present')">Present</button>
          <button class="btn btn-warning btn-sm" onclick="quickMarkAttendance(${r.child_id}, 'Late')">Late</button>
          <button class="btn btn-danger btn-sm" onclick="quickMarkAttendance(${r.child_id}, 'Absent')">Absent</button>
          <button class="btn btn-secondary btn-sm" onclick="checkOutChild(${r.child_id})">Out</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading attendance:", err);
  }
}

async function quickMarkAttendance(childId, status) {
  const attDate = document.getElementById("attendance-date")?.value || "";
  const now = new Date().toTimeString().slice(0, 5);

  try {
    const res = await fetch("/api/attendance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        child_id: childId,
        attendance_date: attDate,
        status: status,
        check_in_time: status !== "Absent" ? now : null,
        temperature_f: status !== "Absent" ? 98.4 : null
      })
    });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, "success");
      loadAttendance();
    } else {
      showToast(result.error, "error");
    }
  } catch (err) {
    showToast("Error updating attendance", "error");
  }
}

async function checkOutChild(childId) {
  const attDate = document.getElementById("attendance-date")?.value || "";
  const now = new Date().toTimeString().slice(0, 5);

  try {
    const res = await fetch("/api/attendance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        child_id: childId,
        attendance_date: attDate,
        status: "Present",
        check_out_time: now
      })
    });
    const result = await res.json();
    if (res.ok) {
      showToast("Checked out at " + now, "success");
      loadAttendance();
    } else {
      showToast(result.error, "error");
    }
  } catch (err) {
    showToast("Error recording checkout", "error");
  }
}

// ---------------- Daily Activities ----------------
async function loadActivities() {
  const feed = document.getElementById("activity-feed");
  if (!feed) return;

  try {
    const res = await fetch("/api/activities");
    const data = await res.json();

    feed.innerHTML = data.map(act => `
      <div style="background: var(--white); border: 1px solid #f0e6dc; border-radius: 10px; padding: 18px; margin-bottom: 14px; display: flex; gap: 16px; align-items: flex-start; box-shadow: var(--shadow-sm);">
        <div style="font-size: 26px; padding: 12px; background: #faf5ee; border-radius: 10px;">
          ${act.activity_type === 'Meal' ? '🥣' :
            act.activity_type === 'Nap' ? '💤' :
            act.activity_type === 'Play/Learning' ? '🎨' :
            act.activity_type === 'Diaper/Potty' ? '🧻' : '⚠'}
        </div>
        <div style="flex: 1;">
          <div style="display: flex; justify-content: space-between;">
            <strong style="color: #1e1b4b; font-size: 16px;">${act.child_name} - ${act.activity_type}</strong>
            <span style="font-size: 12px; color: var(--gray-500);">${act.activity_date} at ${act.start_time}</span>
          </div>
          <p style="color: #44403c; margin: 8px 0; font-size: 14px; line-height: 1.5;">${act.description}</p>
          <div style="font-size: 12px; color: var(--gray-500);">Classroom: <strong>${act.room_name}</strong> | Logged by: <strong>${act.logged_by}</strong></div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading activities:", err);
  }
}

async function handleLogActivity(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    child_id: form.child_id.value,
    activity_type: form.activity_type.value,
    start_time: form.start_time.value,
    end_time: form.end_time.value || null,
    description: form.description.value,
    staff_id: form.staff_id.value
  };

  try {
    const res = await fetch("/api/activities", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, "success");
      form.reset();
      closeModal("modal-log-activity");
      loadActivities();
    } else {
      showToast(result.error, "error");
    }
  } catch (err) {
    showToast("Error submitting activity", "error");
  }
}

// ---------------- Billing & Invoices (INR ₹) ----------------
async function loadBilling() {
  const tableBody = document.getElementById("invoices-table-body");
  if (!tableBody) return;

  try {
    const res = await fetch("/api/invoices");
    const data = await res.json();

    tableBody.innerHTML = data.map(inv => {
      const balance = inv.net_amount - inv.amount_paid;
      return `
        <tr>
          <td><strong>#INV-${inv.invoice_id}</strong></td>
          <td><strong style="font-size: 15px;">${inv.child_name}</strong></td>
          <td>${inv.plan_name}</td>
          <td>${inv.billing_period}</td>
          <td><strong style="color:#1e1b4b;">₹${Number(inv.net_amount).toLocaleString("en-IN")}</strong></td>
          <td style="color:#15803d; font-weight:600;">₹${Number(inv.amount_paid).toLocaleString("en-IN")}</td>
          <td>
            <span class="badge ${
              inv.status === 'Paid' ? 'badge-success' :
              inv.status === 'Overdue' ? 'badge-danger' : 'badge-warning'
            }">${inv.status}</span>
          </td>
          <td>${inv.due_date}</td>
          <td>
            ${inv.status !== 'Paid' ? `
              <button class="btn btn-primary btn-sm" onclick="openPaymentModal(${inv.invoice_id}, ${balance}, '${inv.child_name}')">Pay Fee</button>
            ` : `<span style="font-size: 12px; color: var(--success); font-weight: 700;">✓ Settled</span>`}
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading billing:", err);
  }
}

function openPaymentModal(invoiceId, balanceDue, childName) {
  document.getElementById("pay-invoice-id").value = invoiceId;
  document.getElementById("pay-child-name").innerText = `${childName} (Invoice #INV-${invoiceId})`;
  document.getElementById("pay-amount").value = balanceDue.toFixed(2);
  openModal("modal-record-payment");
}

async function handleRecordPayment(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    invoice_id: form.invoice_id.value,
    amount_paid: form.amount_paid.value,
    payment_mode: form.payment_mode.value,
    transaction_ref: form.transaction_ref.value
  };

  try {
    const res = await fetch("/api/payments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, "success");
      form.reset();
      closeModal("modal-record-payment");
      loadBilling();
    } else {
      showToast(result.error, "error");
    }
  } catch (err) {
    showToast("Payment recording failed", "error");
  }
}

async function handleCreateInvoice(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    child_id: form.child_id.value,
    plan_id: form.plan_id.value,
    billing_period: form.billing_period.value,
    total_amount: form.total_amount.value,
    discount_amount: form.discount_amount.value || 0,
    due_date: form.due_date.value
  };

  try {
    const res = await fetch("/api/invoices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, "success");
      form.reset();
      closeModal("modal-create-invoice");
      loadBilling();
    } else {
      showToast(result.error, "error");
    }
  } catch (err) {
    showToast("Error creating invoice", "error");
  }
}

// ---------------- SQL Console Runner ----------------
async function loadSqlPresets() {
  const select = document.getElementById("sql-presets-select");
  if (!select) return;

  try {
    const res = await fetch("/api/sql/presets");
    const presets = await res.json();

    select.innerHTML = '<option value="">-- Choose a Preset Academic DBMS Query --</option>' + 
      presets.map(p => `<option value="${p.id}">${p.title}</option>`).join("");

    window._sqlPresets = presets;
  } catch (err) {
    console.error("Presets loading error:", err);
  }
}

function handlePresetSelect(event) {
  const selectedId = parseInt(event.target.value);
  if (!selectedId || !window._sqlPresets) return;

  const preset = window._sqlPresets.find(p => p.id === selectedId);
  if (preset) {
    document.getElementById("sql-query-input").value = preset.sql;
    document.getElementById("sql-query-desc").innerText = preset.description;
  }
}

async function executeSql() {
  const query = document.getElementById("sql-query-input").value.trim();
  const outputBox = document.getElementById("sql-output-box");
  const metaBox = document.getElementById("sql-meta-box");

  if (!query) {
    showToast("Please enter an SQL query to execute", "error");
    return;
  }

  outputBox.innerHTML = "<p style='padding: 16px; color: var(--gray-500);'>Executing SQL statement...</p>";

  try {
    const res = await fetch("/api/sql/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql: query })
    });
    const result = await res.json();

    if (!res.ok || result.error) {
      outputBox.innerHTML = `
        <div style="padding: 16px; color: var(--danger); background: var(--danger-light); font-family: monospace;">
          <strong>SQL Error:</strong> ${result.error}
        </div>
      `;
      metaBox.innerText = "Execution failed";
      return;
    }

    metaBox.innerText = result.message;

    // Render Table
    let tableHtml = `<table class="data-table"><thead><tr>`;
    result.columns.forEach(col => {
      tableHtml += `<th>${col}</th>`;
    });
    tableHtml += `</tr></thead><tbody>`;

    if (result.rows.length === 0) {
      tableHtml += `<tr><td colspan="${result.columns.length}" style="text-align: center; padding: 20px;">(0 rows returned)</td></tr>`;
    } else {
      result.rows.forEach(row => {
        tableHtml += `<tr>`;
        row.forEach(cell => {
          tableHtml += `<td>${cell !== null ? cell : '<em style="color:var(--gray-300)">NULL</em>'}</td>`;
        });
        tableHtml += `</tr>`;
      });
    }
    tableHtml += `</tbody></table>`;
    outputBox.innerHTML = tableHtml;
  } catch (err) {
    outputBox.innerHTML = `<div style="padding: 16px; color: var(--danger);">Network or execution error</div>`;
  }
}

async function resetDatabase() {
  if (!confirm("Are you sure you want to reset the database and re-seed Indian demo data?")) {
    return;
  }
  try {
    const res = await fetch("/api/db-reset", { method: "POST" });
    const result = await res.json();
    if (res.ok) {
      showToast(result.message, "success");
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(result.error, "error");
    }
  } catch (err) {
    showToast("Reset failed", "error");
  }
}

// ---------------- Initialization on DOM Ready ----------------
document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
  loadChildren();
  loadGuardians();
  loadAttendance();
  loadActivities();
  loadBilling();
  loadSqlPresets();
});

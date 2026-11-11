"use strict";

// Match this URL with frontend-defended/login.js.
// Local: http://localhost:8000
// Azure: https://cs4489-defended-v1.azurewebsites.net
const API_BASE_URL = window.location.origin;

let currentUser = null;
let csrfToken = null;

const notice = document.getElementById("notice");
const customersBody = document.getElementById("customersBody");

function setNotice(text, error = false) {
  notice.textContent = text;
  notice.classList.toggle("error", error);
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    ...options,
  });

  let body = {};
  try { body = await response.json(); } catch { /* No body */ }

  if (!response.ok) {
    const err = new Error(
      response.status === 401 ? "Not authenticated" :
      response.status === 403 ? "Access denied" :
      response.status === 422 ? "Invalid input" :
      "Request failed"
    );
    err.status = response.status;
    throw err;
  }
  return body;
}

function appendCell(row, value) {
  const cell = document.createElement("td");
  // Safer than innerHTML: database content is always rendered as text.
  cell.textContent = value == null ? "—" : String(value);
  row.appendChild(cell);
}

async function loadCustomers() {
  const tenantId = Number(document.getElementById("tenantIdInput").value);
  if (!Number.isInteger(tenantId) || tenantId < 1) {
    setNotice("Enter a valid tenant ID.", true);
    return;
  }
  try {
    const body = await api(`/api/customers/${tenantId}`);
    customersBody.replaceChildren();
    for (const customer of body.customers) {
      const row = document.createElement("tr");
      for (const field of ["id", "full_name", "email", "phone", "ssn_last4"]) {
        appendCell(row, customer[field]);
      }
      customersBody.appendChild(row);
    }
    if (!body.customers.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 5;
      cell.textContent = "No customers found";
      row.appendChild(cell);
      customersBody.appendChild(row);
    }
    setNotice(`Loaded ${body.customers.length} customers for tenant ${tenantId}.`);
  } catch (err) {
    customersBody.replaceChildren();
    setNotice(`Customer request: HTTP ${err.status || "network"} — ${err.message}`, true);
  }
}

async function loadReport() {
  try {
    const report = await api("/api/admin/tenant-report");
    document.getElementById("adminReportOutput").textContent =
      JSON.stringify(report, null, 2);
    setNotice("Admin report loaded.");
  } catch (err) {
    setNotice(`Admin report: HTTP ${err.status || "network"} — ${err.message}`, true);
  }
}

async function savePhone() {
  const customerId = Number(document.getElementById("customerIdInput").value);
  const phone = document.getElementById("phoneInput").value.trim();
  if (!Number.isInteger(customerId) || customerId < 1) {
    setNotice("Enter a valid customer ID.", true);
    return;
  }
  try {
    await api(`/api/customers/${customerId}/phone`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: JSON.stringify({ phone }),
    });
    setNotice("Phone number updated successfully.");
    await loadCustomers();
  } catch (err) {
    setNotice(`Update request: HTTP ${err.status || "network"} — ${err.message}`, true);
  }
}

async function logout() {
  try {
    await api("/auth/logout", {
      method: "POST",
      headers: { "X-CSRF-Token": csrfToken },
    });
  } catch { /* Session might already have expired */ }
  window.location.assign("index.html");
}

async function initialize() {
  try {
    const session = await api("/auth/me");
    currentUser = session.user;
    csrfToken = session.csrf_token;
    document.getElementById("userInfo").textContent =
      `Signed in as ${currentUser.username} (${currentUser.role}) — tenant ${currentUser.tenant_id}`;
    document.getElementById("tenantIdInput").value = currentUser.tenant_id;
    await loadCustomers();
  } catch {
    window.location.replace("index.html");
  }
}

document.getElementById("loadCustomersButton").addEventListener("click", loadCustomers);
document.getElementById("adminReportButton").addEventListener("click", loadReport);
document.getElementById("updatePhoneButton").addEventListener("click", savePhone);
document.getElementById("logoutButton").addEventListener("click", logout);
initialize();

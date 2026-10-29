"use strict";

const API_BASE_URL =
  "https://cs4489-undefended-v1-cjbndzc9h0hvgqf7.westus-01.azurewebsites.net";

const COMPANY_NAMES = { "1": "Alpha Health", "2": "Beta Health" };
const savedUser = sessionStorage.getItem("cs4489_demo_user");
let currentUser = null;

try {
  currentUser = savedUser ? JSON.parse(savedUser) : null;
} catch {
  currentUser = null;
}

if (!currentUser) {
  window.location.replace("index.html");
} else {
  const tenantSelect = document.getElementById("tenantSelect");
  const searchInput = document.getElementById("customerSearch");
  const refreshButton = document.getElementById("loadCustomers");
  const customerRows = document.getElementById("customerRows");
  const customerCount = document.getElementById("customerCount");
  const selectedCompany = document.getElementById("selectedCompany");
  const recordCount = document.getElementById("recordCount");
  const errorMessage = document.getElementById("errorMessage");

  document.getElementById("userName").textContent = currentUser.username || "Account";
  document.getElementById("userRole").textContent = currentUser.role === "admin" ? "Administrator" : "Staff";

  // Preserve the existing tenant-switching behavior for the class demonstration.
  tenantSelect.value = COMPANY_NAMES[String(currentUser.tenant_id)]
    ? String(currentUser.tenant_id) : "1";

  let customers = [];
  let requestNumber = 0;

  function showEmpty(message) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.className = "empty";
    cell.textContent = message;
    row.appendChild(cell);
    customerRows.replaceChildren(row);
  }

  function addCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value == null || value === "" ? "—" : String(value);
    row.appendChild(cell);
  }

  function renderCustomers() {
    const query = searchInput.value.trim().toLowerCase();
    const visible = customers.filter(customer =>
      [customer.full_name, customer.email, customer.phone].some(value =>
        String(value ?? "").toLowerCase().includes(query)
      )
    );

    customerRows.replaceChildren();
    if (visible.length === 0) {
      showEmpty(query ? "No customers match your search." : "No customers found for this company.");
    } else {
      for (const customer of visible) {
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        const nameWrap = document.createElement("div");
        nameWrap.className = "customer-name";
        const avatar = document.createElement("span");
        avatar.className = "avatar";
        avatar.textContent = String(customer.full_name || "?").trim().charAt(0).toUpperCase() || "?";
        const name = document.createElement("span");
        name.textContent = customer.full_name || "Unknown customer";
        nameWrap.append(avatar, name);
        nameCell.appendChild(nameWrap);
        row.appendChild(nameCell);
        addCell(row, customer.email);
        addCell(row, customer.phone);
        addCell(row, customer.ssn_last4);
        customerRows.appendChild(row);
      }
    }
    recordCount.textContent = `Showing ${visible.length} of ${customers.length} customers`;
  }

  async function loadCustomers() {
    const selectedTenant = tenantSelect.value;
    const thisRequest = ++requestNumber;
    selectedCompany.textContent = COMPANY_NAMES[selectedTenant] || "Company";
    errorMessage.hidden = true;
    refreshButton.disabled = true;
    customerCount.textContent = "—";
    recordCount.textContent = "Loading records...";
    showEmpty("Loading customer records...");

    try {
      const response = await fetch(`${API_BASE_URL}/api/customers/${selectedTenant}`);
      const data = await response.json();
      if (!response.ok) throw new Error(`Unable to load customers (HTTP ${response.status}).`);
      if (!Array.isArray(data.customers)) throw new Error("Unexpected customer data received.");
      if (thisRequest !== requestNumber) return;

      customers = data.customers;
      customerCount.textContent = String(customers.length);
      renderCustomers();
    } catch (error) {
      if (thisRequest !== requestNumber) return;
      customers = [];
      customerCount.textContent = "—";
      showEmpty("Customer records are currently unavailable.");
      recordCount.textContent = "Unable to load records";
      errorMessage.textContent = error.message || "Unable to connect to the server.";
      errorMessage.hidden = false;
    } finally {
      if (thisRequest === requestNumber) refreshButton.disabled = false;
    }
  }

  tenantSelect.addEventListener("change", loadCustomers);
  searchInput.addEventListener("input", renderCustomers);
  refreshButton.addEventListener("click", loadCustomers);
  document.getElementById("logoutButton").addEventListener("click", () => {
    sessionStorage.removeItem("cs4489_demo_user");
    window.location.href = "index.html";
  });

  loadCustomers();
}

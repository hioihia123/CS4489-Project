"use strict";

// Use http://127.0.0.1:8000 here when testing against local FastAPI.
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
  const successMessage = document.getElementById("successMessage");

  const adminReportButton = document.getElementById("loadAdminReport");
  const adminReportSection = document.getElementById("adminReportSection");
  const adminReportRows = document.getElementById("adminReportRows");
  const adminReportMessage = document.getElementById("adminReportMessage");

  const editPhoneDialog = document.getElementById("editPhoneDialog");
  const editPhoneForm = document.getElementById("editPhoneForm");
  const editPhoneCustomer = document.getElementById("editPhoneCustomer");
  const editPhoneInput = document.getElementById("editPhoneInput");
  const editPhoneError = document.getElementById("editPhoneError");
  const cancelEditPhone = document.getElementById("cancelEditPhone");
  const saveEditPhone = document.getElementById("saveEditPhone");

  document.getElementById("userName").textContent = currentUser.username || "Account";
  document.getElementById("userRole").textContent =
    currentUser.role === "admin" ? "Administrator" : "Staff";

  // The tenant selector is deliberately unrestricted for this coursework demo.
  tenantSelect.value = COMPANY_NAMES[String(currentUser.tenant_id)]
    ? String(currentUser.tenant_id) : "1";

  let customers = [];
  let requestNumber = 0;
  let editingCustomer = null;

  function showEmpty(message) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
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

  function openPhoneEditor(customer) {
    editingCustomer = customer;
    editPhoneCustomer.textContent = `Update the phone number for ${customer.full_name || "this customer"}.`;
    editPhoneInput.value = customer.phone || "";
    editPhoneError.textContent = "";
    editPhoneDialog.showModal();
    editPhoneInput.focus();
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
      showEmpty(query
        ? "No customers match your search."
        : "No customers found for this company.");
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

        const actionCell = document.createElement("td");
        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.className = "edit-button";
        editButton.textContent = "Edit";
        editButton.addEventListener("click", () => openPhoneEditor(customer));
        actionCell.appendChild(editButton);
        row.appendChild(actionCell);

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

  async function updatePhone(event) {
    event.preventDefault();
    if (!editingCustomer) return;

    const customerId = editingCustomer.id;
    const updatedName = editingCustomer.full_name || "Customer";
    const newPhone = editPhoneInput.value.trim();
    if (newPhone.length < 7 || newPhone.length > 30) {
      editPhoneError.textContent = "Enter a phone number between 7 and 30 characters.";
      return;
    }

    saveEditPhone.disabled = true;
    saveEditPhone.textContent = "Saving...";
    editPhoneError.textContent = "";

    try {
      const response = await fetch(`${API_BASE_URL}/api/customers/${customerId}/phone`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: newPhone })
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : `HTTP ${response.status}`;
        throw new Error(detail);
      }

      editPhoneDialog.close();
      successMessage.hidden = true;
      await loadCustomers();
      if (errorMessage.hidden) {
        successMessage.textContent = `${updatedName}'s phone number was updated.`;
        successMessage.hidden = false;
      }
    } catch (error) {
      editPhoneError.textContent = `Unable to update customer: ${error.message}`;
    } finally {
      saveEditPhone.disabled = false;
      saveEditPhone.textContent = "Save changes";
    }
  }

  async function loadAdminReport() {
    adminReportButton.disabled = true;
    adminReportMessage.textContent = "Loading administration report...";

    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/tenant-report`);
      if (!response.ok) throw new Error(`Report request failed: HTTP ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.companies)) throw new Error("Unexpected report format.");

      adminReportRows.replaceChildren();
      for (const company of data.companies) {
        const row = document.createElement("tr");
        addCell(row, company.company);
        addCell(row, company.customer_count);
        addCell(row, company.user_count);
        adminReportRows.appendChild(row);
      }
      adminReportSection.hidden = false;
      adminReportMessage.textContent = "Administration report loaded successfully.";
    } catch (error) {
      adminReportMessage.textContent = `Unable to load report: ${error.message}`;
    } finally {
      adminReportButton.disabled = false;
    }
  }

  tenantSelect.addEventListener("change", () => {
    successMessage.hidden = true;
    loadCustomers();
  });
  searchInput.addEventListener("input", renderCustomers);
  refreshButton.addEventListener("click", loadCustomers);
  adminReportButton.addEventListener("click", loadAdminReport);
  editPhoneForm.addEventListener("submit", updatePhone);
  cancelEditPhone.addEventListener("click", () => editPhoneDialog.close());
  editPhoneDialog.addEventListener("close", () => { editingCustomer = null; });

  document.getElementById("logoutButton").addEventListener("click", () => {
    sessionStorage.removeItem("cs4489_demo_user");
    window.location.href = "index.html";
  });

  loadCustomers();
}

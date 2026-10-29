"use strict";

const API_BASE_URL =
    "https://cs4489-undefended-v1-cjbndzc9h0hvgqf7.westus-01.azurewebsites.net";

// Get demonstration user information
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

    // Display logged-in user information
    document.getElementById("userInfo").textContent =
        `Logged in as: ${currentUser.username}
         | Tenant: ${currentUser.tenant_id}
         | Role: ${currentUser.role}`;

    // Default to user's own tenant
    document.getElementById("tenantSelect").value =
        String(currentUser.tenant_id);

    // Load customers
    document.getElementById("loadCustomers")
        .addEventListener("click", async () => {

            const tenantId =
                document.getElementById("tenantSelect").value;

            const results =
                document.getElementById("customerResults");

            results.textContent = "Loading...";

            try {

                const response = await fetch(
                    `${API_BASE_URL}/api/customers/${tenantId}`
                );

                const data = await response.json();

                results.textContent =
                    JSON.stringify(data, null, 2);

            } catch (error) {

                results.textContent =
                    `Request failed: ${error.message}`;

            }

        });

    // Logout
    document.getElementById("logoutButton")
        .addEventListener("click", () => {

            sessionStorage.removeItem("cs4489_demo_user");

            window.location.href = "index.html";

        });
}

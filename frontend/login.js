"use strict";

// Supply your backend's origin after adding a POST /auth/login endpoint.
// Example: const API_BASE_URL = "https://your-backend.azurewebsites.net";
const API_BASE_URL = "";

const root = document.documentElement;
const themeToggle = document.getElementById("themeToggle");
const passwordToggle = document.getElementById("passwordToggle");
const passwordInput = document.getElementById("password");
const loginForm = document.getElementById("loginForm");
const submitButton = document.getElementById("submitButton");
const formStatus = document.getElementById("formStatus");

// Only the visual theme is saved. Passwords and account credentials are not.
const savedTheme = localStorage.getItem("cs4389-theme");
if (savedTheme === "light" || savedTheme === "dark") {
  root.dataset.theme = savedTheme;
} else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
  root.dataset.theme = "dark";
}

function updateThemeLabel() {
  const dark = root.dataset.theme === "dark";
  themeToggle.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} mode`);
  document.querySelector('meta[name="theme-color"]').content = dark ? "#0d1321" : "#f5f7fb";
}
updateThemeLabel();

themeToggle.addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  localStorage.setItem("cs4389-theme", next);
  updateThemeLabel();
});

passwordToggle.addEventListener("click", () => {
  const visible = passwordInput.type === "password";
  passwordInput.type = visible ? "text" : "password";
  passwordToggle.setAttribute("aria-pressed", String(visible));
  passwordToggle.setAttribute("aria-label", visible ? "Hide password" : "Show password");
});

function showStatus(message) {
  formStatus.textContent = message;
  formStatus.hidden = false;
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  formStatus.hidden = true;

  if (!API_BASE_URL) {
    showStatus("Login API is not connected yet. The page is ready for backend integration.");
    return;
  }

  const username = document.getElementById("username").value.trim();
  const password = passwordInput.value;
  if (!username || !password) return;

  submitButton.disabled = true;
  try {
    const response = await fetch(`${API_BASE_URL.replace(/\/$/, "")}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      credentials: "omit"
    });

    if (!response.ok) {
      showStatus(response.status === 401 ? "Incorrect username or password." : "Unable to sign in. Please try again.");
      return;
    }

    // Replace with a secure, backend-approved session/redirect flow.
    showStatus("Signed in successfully.");
  } catch {
    showStatus("Could not reach the login server. Please try again.");
  } finally {
    submitButton.disabled = false;
  }
});

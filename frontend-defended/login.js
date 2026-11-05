"use strict";

// Configure this only AFTER deploying the defended FastAPI backend.
// Example: const API_BASE_URL = "https://your-defended-api.azurewebsites.net";
// Never point this page at the deliberately vulnerable API.
const API_BASE_URL = "";

const root = document.documentElement;
const themeToggle = document.getElementById("themeToggle");
const passwordToggle = document.getElementById("passwordToggle");
const passwordInput = document.getElementById("password");
const loginForm = document.getElementById("loginForm");
const submitButton = document.getElementById("submitButton");
const formStatus = document.getElementById("formStatus");

const savedTheme = localStorage.getItem("cs4389-defended-theme");
if (savedTheme === "light" || savedTheme === "dark") {
  root.dataset.theme = savedTheme;
} else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
  root.dataset.theme = "dark";
}

function updateThemeLabel() {
  const dark = root.dataset.theme === "dark";
  themeToggle.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} mode`);
  document.querySelector('meta[name="theme-color"]').content = dark ? "#0c1711" : "#f5f9f6";
}

updateThemeLabel();
themeToggle.addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  localStorage.setItem("cs4389-defended-theme", next);
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
    showStatus("The defended login API has not been connected yet.");
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
      credentials: "include"
    });

    if (!response.ok) {
      // Do not show internal SQL errors, account existence, or stack traces.
      showStatus(response.status === 401 || response.status === 403
        ? "Invalid username or password."
        : "Sign-in is temporarily unavailable. Please try again.");
      return;
    }

    // The defended API must establish a verified server-side session.
    // Do not store passwords, access tokens, or trusted roles in web storage.
    window.location.assign("dashboard.html");
  } catch {
    showStatus("Could not reach the sign-in server. Please try again.");
  } finally {
    submitButton.disabled = false;
  }
});

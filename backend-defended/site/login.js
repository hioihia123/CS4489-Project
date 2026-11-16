"use strict";

const API_BASE_URL = window.location.origin;
const root = document.documentElement;
const themeToggle = document.getElementById("themeToggle");
const passwordToggle = document.getElementById("passwordToggle");
const passwordInput = document.getElementById("password");
const loginForm = document.getElementById("loginForm");
const submitButton = document.getElementById("submitButton");
const formStatus = document.getElementById("formStatus");

const savedTheme = localStorage.getItem("cs4389-defended-theme");

const standardModeButton =
  document.getElementById("standardModeButton");

const adminModeButton =
  document.getElementById("adminModeButton");

const mfaField =
  document.getElementById("mfaField");

const totpInput =
  document.getElementById("totp_code");

let selectedMode = "user";

function setLoginMode(mode) {
  selectedMode = mode;

  const isAdmin = mode === "admin";

  standardModeButton.classList.toggle(
    "active", !isAdmin
  );

  adminModeButton.classList.toggle(
    "active", isAdmin
  );

  standardModeButton.setAttribute(
    "aria-pressed", String(!isAdmin)
  );

  adminModeButton.setAttribute(
    "aria-pressed", String(isAdmin)
  );

  mfaField.hidden = !isAdmin;
  totpInput.disabled = !isAdmin;
  totpInput.required = isAdmin;

  if (!isAdmin) {
    totpInput.value = "";
  }

  formStatus.hidden = true;
}

standardModeButton.addEventListener("click", () => {
  setLoginMode("user");
});

adminModeButton.addEventListener("click", () => {
  setLoginMode("admin");
});

setLoginMode("user");

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

  const totpCode = selectedMode === "admin"  ? totpInput.value.trim()  : null;
  if (!username || !password) return;

  submitButton.disabled = true;
  try {
    const response = await fetch(`${API_BASE_URL.replace(/\/$/, "")}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, totp_code: totpCode || null}),
      credentials: "include"
    });

    if (!response.ok) {

    if (response.status === 429) {
        showStatus(
            "Too many login attempts. Please try again in about a minute."
        );
    }
    else if (
        response.status === 401 ||
        response.status === 403
    ) {
        showStatus(
            "Invalid username or password."
        );
    }
    else {
        showStatus(
            "Sign-in is temporarily unavailable. Please try again."
        );
    }

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

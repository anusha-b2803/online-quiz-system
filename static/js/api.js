const API_URL = "/api";

function setToken(token, role, userId) {
    localStorage.setItem("quiz_token", token);
    localStorage.setItem("user_role", role);
    localStorage.setItem("user_id", userId);
}

function getToken() {
    return localStorage.getItem("quiz_token");
}

function getRole() {
    return localStorage.getItem("user_role");
}

function logout() {
    localStorage.clear();
    window.location.href = "/";
}

async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Unauthorized, maybe expired
        logout();
        return;
    }

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
    }

    return data;
}

// Global Auth Guard
function checkAuth() {
    const token = getToken();
    const path = window.location.pathname;

    if (!token && path !== "/" && path !== "/login" && path !== "/register" && !path.endsWith("index.html") && !path.endsWith("login.html") && !path.endsWith("register.html")) {
        window.location.href = "login.html";
    }
}

document.addEventListener("DOMContentLoaded", checkAuth);

const TOKEN_KEY = "sitePresentationAdminToken";
const BACKEND_BASE_KEY = "sitePresentationAdminBackendBaseUrl";

const normalizeBaseUrl = (value) => (value || "").trim().replace(/\/+$/, "");

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setStoredToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function getBackendBaseUrl() {
  const envBase = import.meta.env.VITE_ADMIN_API_BASE_URL;
  if (envBase) {
    return normalizeBaseUrl(envBase);
  }

  if (window.location.protocol !== "file:") {
    return normalizeBaseUrl(window.location.origin);
  }

  return normalizeBaseUrl(localStorage.getItem(BACKEND_BASE_KEY)) || "http://127.0.0.1:8000";
}

export function setBackendBaseUrl(value) {
  const normalized = normalizeBaseUrl(value);
  if (!normalized) {
    localStorage.removeItem(BACKEND_BASE_KEY);
    return "";
  }
  localStorage.setItem(BACKEND_BASE_KEY, normalized);
  return normalized;
}

async function request(path, options = {}) {
  const response = await fetch(`${getBackendBaseUrl()}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || "Operation impossible.");
  }
  return body;
}

export async function login(email, password) {
  const result = await request("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  setStoredToken(result.access_token);
  return result;
}

export async function getProfile() {
  return request("/api/v1/auth/me", {
    headers: { Authorization: `Bearer ${getStoredToken()}` },
  });
}

export async function getSummary() {
  return request("/api/v1/site-presentation/admin/summary", {
    headers: { Authorization: `Bearer ${getStoredToken()}` },
  });
}

export async function getContent() {
  return request("/api/v1/site-presentation/admin/content", {
    headers: { Authorization: `Bearer ${getStoredToken()}` },
  });
}

export async function saveContent(payload) {
  return request("/api/v1/site-presentation/admin/content", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getStoredToken()}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function listMedia() {
  return request("/api/v1/site-presentation/admin/media", {
    headers: { Authorization: `Bearer ${getStoredToken()}` },
  });
}

export async function uploadImage(file) {
  const formData = new FormData();
  formData.append("image", file);
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/site-presentation/admin/upload-image`, {
    method: "POST",
    headers: { Authorization: `Bearer ${getStoredToken()}` },
    body: formData,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || "Upload impossible.");
  }
  return body;
}

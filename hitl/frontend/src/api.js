// Client API du backend HITL. Le token JWT est conservé en localStorage.

const TOKEN_KEY = "bagids_hitl_token";
const USER_KEY = "bagids_hitl_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}
export function storeSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = new URLSearchParams(form).toString();
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body) {
    payload = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(path, { method, headers, body: payload });
  if (res.status === 401) {
    clearSession();
    window.location.hash = "#/login";
    throw new Error("Session expirée");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || `HTTP ${res.status}`);
  return data;
}

export const api = {
  login: (username, password) =>
    request("/api/auth/login", { method: "POST", form: { username, password } }),
  dashboard: () => request("/api/dashboard"),
  agents: () => request("/api/agents"),
  incidents: (n = 200) => request(`/api/incidents?n=${n}`),
  investigations: (n = 30) => request(`/api/investigations?n=${n}`),
  advisories: (n = 50) => request(`/api/advisories?n=${n}`),
  ledger: (n = 200) => request(`/api/ledger?n=${n}`),
  pending: () => request("/api/pending"),
  decisions: (n = 100) => request(`/api/decisions?n=${n}`),
  decide: (id, approve, reason) =>
    request(`/api/pending/${id}/decide`, { method: "POST", body: { approve, reason } }),
  policy: () => request("/api/policy"),
  setPolicy: (changes) => request("/api/policy", { method: "POST", body: changes }),
  toggleHitl: (enabled) =>
    request("/api/hitl/toggle", { method: "POST", body: { enabled } }),
  governanceLog: (n = 200) => request(`/api/governance/log?n=${n}`),
  // Contrôle de la détection
  detectionStatus: () => request("/api/detection/status"),
  detectionStart: () => request("/api/detection/start", { method: "POST" }),
  detectionStop: () => request("/api/detection/stop", { method: "POST" }),
  detectionMeta: () => request("/api/detection/meta"),
  detectionInject: (flows, labels) =>
    request("/api/detection/inject", { method: "POST", body: { flows, labels } }),
};

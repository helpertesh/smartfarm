/* Shared API client, auth helpers and small utilities. */

// When the frontend is deployed separately (Vercel/Netlify), set this to the backend URL,
// e.g. "https://smartfarm-api.onrender.com". Empty string = same origin.
const API_BASE = window.API_BASE || "";

const Auth = {
  token() { return localStorage.getItem("sf_token"); },
  user() { try { return JSON.parse(localStorage.getItem("sf_user") || "null"); } catch { return null; } },
  save(token, user) { localStorage.setItem("sf_token", token); localStorage.setItem("sf_user", JSON.stringify(user)); },
  clear() { localStorage.removeItem("sf_token"); localStorage.removeItem("sf_user"); },
  logout() { Auth.clear(); window.location.href = "index.html"; },
  require() { if (!Auth.token()) { window.location.href = "index.html"; return false; } return true; },
};

async function api(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  if (auth && Auth.token()) headers["Authorization"] = `Bearer ${Auth.token()}`;
  let payload;
  if (form) {
    payload = new URLSearchParams(form);
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(API_BASE + path, { method, headers, body: payload });
  if (res.status === 401 && auth) { Auth.clear(); window.location.href = "index.html"; throw new Error("Session expired"); }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data);
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return data;
}

/* ---------- Utilities ---------- */
const fmt = {
  money(v, cur = "KSh") { return `${cur} ${Math.round(v || 0).toLocaleString()}`; },
  num(v, d = 0) { return (v ?? 0).toLocaleString(undefined, { maximumFractionDigits: d }); },
  date(s) { if (!s) return ""; const d = new Date(s); return d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }); },
  shortDate(s) { const d = new Date(s); return d.toLocaleDateString(undefined, { weekday: "short", day: "numeric" }); },
  dayName(s) { return new Date(s).toLocaleDateString(undefined, { weekday: "short" }); },
  today() { return new Date().toISOString().slice(0, 10); },
};

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

function levelIcon(level) {
  return { info: "ℹ️", success: "✅", warning: "⚠️", danger: "🚨" }[level] || "•";
}

function alertHtml(a) {
  return `<div class="alert ${esc(a.level)}"><div class="ico">${levelIcon(a.level)}</div>
    <div class="body"><strong>${esc(a.title)}</strong>${esc(a.message)}</div></div>`;
}

function notice(el, msg, type = "error") {
  if (!el) return;
  el.className = `notice ${type}`;
  el.textContent = msg;
  el.classList.remove("hidden");
}

function option(value, label, selected) {
  return `<option value="${esc(value)}" ${selected ? "selected" : ""}>${esc(label)}</option>`;
}

/* Remember the farmer's selected farm across pages. */
const FarmStore = {
  key: "sf_farm_id",
  get() { return Number(localStorage.getItem(FarmStore.key)) || null; },
  set(id) { localStorage.setItem(FarmStore.key, String(id)); },
  async pick(farms) {
    if (!farms.length) return null;
    const saved = FarmStore.get();
    const found = farms.find((f) => f.id === saved);
    const chosen = found || farms[0];
    FarmStore.set(chosen.id);
    return chosen;
  },
};

function farmSelector(farms, current, onChange) {
  const sel = document.createElement("select");
  sel.style.width = "auto";
  sel.innerHTML = farms.map((f) => option(f.id, `${f.name} · ${f.location_name}`, f.id === current)).join("");
  sel.addEventListener("change", () => { FarmStore.set(Number(sel.value)); onChange(Number(sel.value)); });
  return sel;
}

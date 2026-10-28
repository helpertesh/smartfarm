/* Shared app shell: sidebar navigation, auth guard, theme toggle. */

const NAV = [
  { page: "dashboard", href: "dashboard.html", icon: "🏠", label: "Dashboard" },
  { page: "farms", href: "farms.html", icon: "🚜", label: "My farms" },
  { page: "advisory", href: "advisory.html", icon: "🌾", label: "Crop advisory" },
  { page: "calendar", href: "calendar.html", icon: "📅", label: "Crop calendar" },
  { page: "diseases", href: "diseases.html", icon: "🦠", label: "Crop health" },
  { page: "market", href: "market.html", icon: "💰", label: "Market prices" },
  { page: "analytics", href: "analytics.html", icon: "📊", label: "Farm analytics" },
  { page: "inputs", href: "inputs.html", icon: "📦", label: "Farm inputs" },
  { page: "admin", href: "admin.html", icon: "🛠️", label: "Admin panel", admin: true },
];

function applyTheme() {
  const t = localStorage.getItem("sf_theme");
  if (t) document.documentElement.setAttribute("data-theme", t);
}
applyTheme();

function toggleTheme() {
  const cur = document.documentElement.getAttribute("data-theme");
  const next = cur === "dark" ? "light" : "dark";
  localStorage.setItem("sf_theme", next);
  applyTheme();
}

function renderShell() {
  if (!Auth.require()) return;
  const user = Auth.user() || {};
  const page = document.body.dataset.page;
  const side = document.getElementById("sidebar");
  if (!side) return;
  side.innerHTML = `
    <div class="brand"><span class="logo">🌱</span> SmartFarm</div>
    <nav class="nav">
      ${NAV.filter((n) => !n.admin || user.role === "admin")
        .map((n) => `<a href="${n.href}" class="${n.page === page ? "active" : ""}"><span class="icon">${n.icon}</span>${n.label}</a>`)
        .join("")}
    </nav>
    <div class="spacer"></div>
    <div class="userbox">
      <strong>${esc(user.full_name || "")}</strong>
      <span class="muted">${esc(user.email || "")}</span>
      <div class="row">
        <button class="btn secondary sm" id="themeBtn" title="Toggle dark mode">🌗 Theme</button>
        <button class="btn secondary sm" id="logoutBtn">Log out</button>
      </div>
    </div>`;
  $("#logoutBtn").addEventListener("click", Auth.logout);
  $("#themeBtn").addEventListener("click", toggleTheme);

  const menuBtn = document.getElementById("menuBtn");
  if (menuBtn) menuBtn.addEventListener("click", () => side.classList.toggle("open"));
  document.addEventListener("click", (e) => {
    if (side.classList.contains("open") && !side.contains(e.target) && e.target !== menuBtn) side.classList.remove("open");
  });
}

document.addEventListener("DOMContentLoaded", renderShell);

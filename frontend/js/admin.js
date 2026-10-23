let crops = [];

async function init() {
  if (Auth.user()?.role !== "admin") { location.href = "dashboard.html"; return; }
  const [c, markets] = await Promise.all([api("/api/advisory/crops"), api("/api/market/markets")]);
  crops = c;
  $("#cropSel").innerHTML = crops.map((x) => option(x.key, `${x.icon} ${x.name}`)).join("");
  $("#marketList").innerHTML = markets.map((m) => `<option value="${esc(m)}">`).join("");
  $("#priceForm").elements.date.value = fmt.today();
  $("#priceForm").addEventListener("submit", savePrice);
  loadStats();
  loadUsers();
}

async function loadStats() {
  const s = await api("/api/admin/stats");
  $("#stats").innerHTML = `
    <div class="card stat"><span class="label">Users</span><span class="value">${s.users}</span></div>
    <div class="card stat"><span class="label">Farms</span><span class="value">${s.farms}</span></div>
    <div class="card stat"><span class="label">Active crop plans</span><span class="value">${s.active_crop_plans}</span></div>
    <div class="card stat"><span class="label">Price records</span><span class="value">${s.market_prices}</span></div>`;
  $("#popular").innerHTML = s.popular_crops.length
    ? `<table>${s.popular_crops.map((p) => { const c = crops.find((x) => x.key === p.crop_key); return `<tr><td>${c?.icon || ""} ${esc(c?.name || p.crop_key)}</td><td class="num">${p.count}</td></tr>`; }).join("")}</table>`
    : `<p class="tiny">No active crop plans yet.</p>`;
}

async function savePrice(e) {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target).entries());
  f.price_per_kg = Number(f.price_per_kg);
  try { await api("/api/market", { method: "POST", body: f }); notice($("#msg"), "Price saved.", "ok"); loadStats(); }
  catch (err) { notice($("#msg"), err.message); }
}

async function loadUsers() {
  const users = await api("/api/admin/users");
  const me = Auth.user()?.id;
  $("#users").innerHTML = `<table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th></th></tr></thead><tbody>` + users.map((u) => `
    <tr>
      <td>${esc(u.full_name)}${u.id === me ? ' <span class="tiny">(you)</span>' : ""}</td>
      <td class="muted small">${esc(u.email)}</td>
      <td><span class="badge ${u.role === "admin" ? "info" : ""}">${u.role}</span></td>
      <td class="num">${u.id !== me ? `<a href="#" class="small" data-role="${u.id}" data-to="${u.role === "admin" ? "farmer" : "admin"}">make ${u.role === "admin" ? "farmer" : "admin"}</a>` : ""}</td>
    </tr>`).join("") + `</tbody></table>`;
  $$("[data-role]").forEach((a) => a.addEventListener("click", async (e) => { e.preventDefault(); await api(`/api/admin/users/${a.dataset.role}/role?role=${a.dataset.to}`, { method: "PATCH" }); loadUsers(); }));
}

init().catch(console.error);

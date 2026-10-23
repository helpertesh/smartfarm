let farms = [], farm = null, crops = [], cats = {}, charts = {};
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

function baseOptions(extra = {}) {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${c.dataset.label ? c.dataset.label + ": " : ""}${fmt.money(c.parsed.y ?? c.parsed.x)}` } } },
    scales: {
      x: { grid: { display: false }, ticks: { color: cssVar("--text-3"), font: { size: 11 } }, border: { display: false } },
      y: { grid: { color: cssVar("--border") }, ticks: { color: cssVar("--text-3"), font: { size: 11 } }, border: { display: false }, beginAtZero: true },
    },
    ...extra,
  };
}

async function init() {
  [farms, crops, cats] = await Promise.all([api("/api/farms"), api("/api/advisory/crops"), api("/api/analytics/categories")]);
  if (!farms.length) { $("#stats").innerHTML = `<div class="empty" style="grid-column:1/-1">Add a farm first. <a href="farms.html?first=1">Add farm</a></div>`; return; }
  farm = await FarmStore.pick(farms);
  $("#farmPicker").prepend(farmSelector(farms, farm.id, (id) => { farm = farms.find((f) => f.id === id); loadAll(); }));
  const y = new Date().getFullYear();
  $("#yearSel").innerHTML = [y, y - 1, y - 2].map((v) => option(v, v, v === y)).join("");
  $("#yearSel").addEventListener("change", loadAll);
  $("#cropSel").innerHTML = crops.map((c) => option(c.key, `${c.icon} ${c.name}`)).join("");
  $("#kindSel").addEventListener("change", fillCats); fillCats();
  $("#txForm").elements.date.value = fmt.today();
  $("#hvForm").elements.date.value = fmt.today();
  $$(".tabs button").forEach((b) => b.addEventListener("click", () => {
    $$(".tabs button").forEach((x) => x.classList.toggle("active", x === b));
    $("#txForm").classList.toggle("hidden", b.dataset.tab !== "tx");
    $("#hvForm").classList.toggle("hidden", b.dataset.tab !== "hv");
  }));
  $("#txForm").addEventListener("submit", saveTx);
  $("#hvForm").addEventListener("submit", saveHv);
  loadAll();
}

function fillCats() {
  const kind = $("#kindSel").value;
  $("#catSel").innerHTML = cats[kind].map((c) => option(c, c[0].toUpperCase() + c.slice(1))).join("");
}

async function saveTx(e) {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target).entries());
  f.farm_id = farm.id; f.amount = Number(f.amount);
  try { await api("/api/analytics/transactions", { method: "POST", body: f }); notice($("#msg"), "Transaction saved.", "ok"); e.target.elements.amount.value = ""; loadAll(); }
  catch (err) { notice($("#msg"), err.message); }
}

async function saveHv(e) {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target).entries());
  f.farm_id = farm.id; f.quantity_kg = Number(f.quantity_kg);
  try { await api("/api/analytics/harvests", { method: "POST", body: f }); notice($("#msg"), "Harvest saved.", "ok"); e.target.elements.quantity_kg.value = ""; loadAll(); }
  catch (err) { notice($("#msg"), err.message); }
}

function draw(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart($(`#${id}`), config);
}

async function loadAll() {
  const year = $("#yearSel").value;
  const s = await api(`/api/analytics/summary?farm_id=${farm.id}&year=${year}`);
  $("#stats").innerHTML = `
    <div class="card stat"><span class="label">Revenue ${year}</span><span class="value">${fmt.money(s.revenue)}</span></div>
    <div class="card stat"><span class="label">Expenses ${year}</span><span class="value">${fmt.money(s.expenses)}</span></div>
    <div class="card stat"><span class="label">Profit</span><span class="value" style="color:${s.profit >= 0 ? "var(--success)" : "var(--danger)"}">${fmt.money(s.profit)}</span></div>
    <div class="card stat"><span class="label">Harvest value (est.)</span><span class="value">${fmt.money(s.estimated_harvest_value)}</span><span class="delta">${fmt.num(s.harvest_by_crop.reduce((a, h) => a + h.quantity_kg, 0))} kg at latest prices</span></div>`;

  const s1 = cssVar("--series-1"), s2 = cssVar("--series-2");
  draw("monthly", {
    type: "bar",
    data: { labels: MONTHS, datasets: [
      { label: "Income", data: s.monthly.map((m) => m.income), backgroundColor: s1, borderRadius: 4, borderSkipped: "bottom", maxBarThickness: 18 },
      { label: "Expenses", data: s.monthly.map((m) => m.expense), backgroundColor: s2, borderRadius: 4, borderSkipped: "bottom", maxBarThickness: 18 },
    ] },
    options: baseOptions({ interaction: { mode: "index", intersect: false } }),
  });

  draw("byCat", {
    type: "bar",
    data: { labels: s.expenses_by_category.map((c) => c.category), datasets: [{ label: "Expenses", data: s.expenses_by_category.map((c) => c.amount), backgroundColor: s2, borderRadius: 4, borderSkipped: "left", maxBarThickness: 18 }] },
    options: baseOptions({ indexAxis: "y" }),
  });

  draw("harvestChart", {
    type: "bar",
    data: { labels: s.harvest_by_crop.map((h) => h.crop_name), datasets: [{ label: "Harvest", data: s.harvest_by_crop.map((h) => h.quantity_kg), backgroundColor: s1, borderRadius: 4, borderSkipped: "left", maxBarThickness: 18 }] },
    options: baseOptions({ indexAxis: "y", plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${fmt.num(c.parsed.x)} kg` } } } }),
  });
  $("#harvestTable").innerHTML = s.harvest_by_crop.length
    ? `<table><thead><tr><th>Crop</th><th class="num">Kg</th><th class="num">Est. value</th></tr></thead><tbody>${s.harvest_by_crop.map((h) => `<tr><td>${h.icon} ${esc(h.crop_name)}</td><td class="num">${fmt.num(h.quantity_kg)}</td><td class="num">${fmt.money(h.est_value)}</td></tr>`).join("")}</tbody></table>`
    : `<p class="tiny">No harvests recorded for ${year}.</p>`;

  const tx = await api(`/api/analytics/transactions?farm_id=${farm.id}`);
  $("#txList").innerHTML = tx.length ? `<table><thead><tr><th>Date</th><th>Type</th><th>Category</th><th>Description</th><th class="num">Amount</th><th></th></tr></thead><tbody>` +
    tx.slice(0, 25).map((t) => `<tr><td>${fmt.date(t.date)}</td><td><span class="badge ${t.kind === "income" ? "success" : "warning"}">${t.kind}</span></td><td>${esc(t.category)}</td><td class="muted">${esc(t.description || "")}</td><td class="num">${fmt.money(t.amount)}</td><td class="num"><a href="#" data-del="${t.id}" class="small">delete</a></td></tr>`).join("") + `</tbody></table>`
    : `<div class="empty">No transactions yet.</div>`;
  $$("[data-del]").forEach((a) => a.addEventListener("click", async (e) => { e.preventDefault(); if (confirm("Delete this transaction?")) { await api(`/api/analytics/transactions/${a.dataset.del}`, { method: "DELETE" }); loadAll(); } }));
}

init().catch(console.error);

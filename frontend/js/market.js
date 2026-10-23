let crops = [], markets = [], trendChart = null;

function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

async function init() {
  [crops, markets] = await Promise.all([api("/api/advisory/crops"), api("/api/market/markets")]);
  $("#marketSel").innerHTML = markets.map((m) => option(m, m)).join("");
  $("#compareSel").innerHTML = crops.map((c) => option(c.key, `${c.icon} ${c.name}`)).join("");
  $("#marketSel").addEventListener("change", loadTable);
  $("#compareSel").addEventListener("change", loadCompare);
  loadTable();
  loadCompare();
}

async function loadTable() {
  const m = $("#marketSel").value;
  $("#marketTitle").textContent = m;
  const rows = await api(`/api/market/latest?market=${encodeURIComponent(m)}`);
  $("#priceTable tbody").innerHTML = rows.map((r) => {
    const c = crops.find((x) => x.key === r.crop_key);
    return `<tr><td>${c?.icon || ""} ${esc(r.crop_name)}</td><td class="num"><strong>${r.price_per_kg}</strong></td><td class="num tiny">${fmt.date(r.date)}</td><td class="num"><a href="#" class="small" data-cmp="${r.crop_key}">compare</a></td></tr>`;
  }).join("");
  $$("[data-cmp]").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); $("#compareSel").value = a.dataset.cmp; loadCompare(); }));
}

async function loadCompare() {
  const key = $("#compareSel").value;
  const rows = await api(`/api/market/compare/${key}`);
  const best = rows[0];
  $("#compare").innerHTML = rows.length ? `<table>${rows.map((r, i) => `<tr><td>${i === 0 ? "🏆 " : ""}${esc(r.market)}</td><td class="num"><strong>${r.price_per_kg}</strong></td></tr>`).join("")}</table>
    <p class="tiny" style="margin-top:8px">Best price: ${esc(best.market)} at KSh ${best.price_per_kg}/kg, ${(best.price_per_kg - rows[rows.length - 1].price_per_kg).toFixed(0)} more than the lowest.</p>` : `<div class="empty">No prices.</div>`;

  const hist = await api(`/api/market/history/${key}?market=${encodeURIComponent($("#marketSel").value)}`);
  const labels = hist.map((h) => fmt.date(h.date));
  const data = hist.map((h) => h.price_per_kg);
  if (trendChart) trendChart.destroy();
  trendChart = new Chart($("#trend"), {
    type: "line",
    data: { labels, datasets: [{ label: `${crops.find((c) => c.key === key)?.name} · ${$("#marketSel").value}`, data, borderColor: cssVar("--series-1"), backgroundColor: cssVar("--series-1"), borderWidth: 2, pointRadius: 4, tension: 0.25 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` KSh ${c.parsed.y}/kg` } } },
      scales: {
        x: { grid: { display: false }, ticks: { color: cssVar("--text-3"), maxTicksLimit: 5, font: { size: 11 } } },
        y: { grid: { color: cssVar("--border") }, ticks: { color: cssVar("--text-3"), font: { size: 11 } }, border: { display: false } },
      },
    },
  });
}

init().catch(console.error);

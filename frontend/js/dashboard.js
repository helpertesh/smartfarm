let farms = [];
let farm = null;

async function init() {
  const user = Auth.user();
  $("#greeting").textContent = `Welcome back, ${user?.full_name?.split(" ")[0] || "farmer"}. Here is what matters today.`;
  farms = await api("/api/farms");
  if (!farms.length) { $("#noFarm").classList.remove("hidden"); return; }
  farm = await FarmStore.pick(farms);
  $("#farmPicker").appendChild(farmSelector(farms, farm.id, (id) => { farm = farms.find((f) => f.id === id); loadAll(); }));
  $("#content").classList.remove("hidden");
  loadAll();
}

function loadAll() {
  loadWeather();
  loadAdvisory();
  loadActivities();
  loadAlerts();
  loadIrrigation();
  loadMarket();
  loadPerformance();
}

async function loadWeather() {
  const box = $("#weather");
  const recs = $("#weatherRecs");
  try {
    const w = await api(`/api/weather/farm/${farm.id}`);
    const c = w.current;
    $("#weatherPlace").textContent = `${farm.location_name} · updated ${new Date(c.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
    box.innerHTML = `
      <div class="weather-now">
        <div class="big">${c.weather.icon}</div>
        <div>
          <div class="temp">${Math.round(c.temperature)}°C</div>
          <div class="muted">${esc(c.weather.label)}</div>
        </div>
      </div>
      <div class="weather-meta">
        <span>🌧 ${c.rain_probability_24h ?? 0}% chance of rain (24h)</span>
        <span>💧 Humidity ${c.humidity}%</span>
        <span>💨 Wind ${Math.round(c.wind_kmh)} km/h</span>
        <span>☔ Last 3 days: ${w.past_rain_mm_3d} mm</span>
      </div>
      <div class="forecast">
        ${w.forecast.map((d, i) => `
          <div class="day">
            <div>${i === 0 ? "Today" : fmt.dayName(d.date)}</div>
            <div class="ico">${d.weather.icon}</div>
            <div class="t">${Math.round(d.temp_max)}° <span class="muted">${Math.round(d.temp_min)}°</span></div>
            <div class="r">${d.rain_probability ?? 0}%</div>
          </div>`).join("")}
      </div>`;
    recs.innerHTML = w.recommendations.map(alertHtml).join("");
  } catch (e) {
    box.innerHTML = `<div class="empty">${esc(e.message)}</div>`;
  }
}

async function loadAdvisory() {
  const el = $("#advisory");
  try {
    const d = await api(`/api/advisory/farm/${farm.id}`);
    const top = d.recommendations.slice(0, 4);
    el.innerHTML = `<p class="tiny">${esc(d.season_name)} · ${esc(farm.soil_type)} soil</p>` +
      top.map((r) => `
        <div class="crop-rec" style="padding:10px 0">
          <div class="ico">${r.icon}</div>
          <div class="grow" style="flex:1">
            <div style="display:flex;justify-content:space-between"><strong>${esc(r.name)}</strong><span class="badge ${r.score >= 80 ? "success" : r.score >= 60 ? "info" : "warning"}">${esc(r.suitability)}</span></div>
            <div class="score" style="margin-top:6px"><span style="width:${r.score}%"></span></div>
          </div>
        </div>`).join("");
  } catch (e) { el.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

async function loadActivities() {
  const el = $("#activities");
  try {
    const acts = await api(`/api/calendar/activities/upcoming?days=14`);
    const plans = await api(`/api/calendar/plans?farm_id=${farm.id}`);
    const planIds = new Set(plans.map((p) => p.id));
    const mine = acts.filter((a) => planIds.has(a.crop_plan_id)).slice(0, 6);
    if (!mine.length) { el.innerHTML = `<div class="empty">No upcoming activities. <a href="calendar.html">Plan a crop</a>.</div>`; return; }
    const today = fmt.today();
    el.innerHTML = `<ul class="list">` + mine.map((a) => {
      const plan = plans.find((p) => p.id === a.crop_plan_id);
      const diff = Math.round((new Date(a.due_date) - new Date(today)) / 86400000);
      const when = diff < 0 ? `<span class="badge danger">${-diff}d overdue</span>` : diff === 0 ? `<span class="badge warning">Today</span>` : `<span class="badge">in ${diff}d</span>`;
      return `<li><span>${plan?.crop_icon || "🌱"}</span><div class="grow"><div class="title">${esc(a.title)}</div><div class="sub">${esc(plan?.crop_name || "")} · ${fmt.date(a.due_date)}</div></div>${when}</li>`;
    }).join("") + `</ul>`;
  } catch (e) { el.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

async function loadAlerts() {
  const el = $("#alerts");
  try {
    const alerts = await api(`/api/alerts?farm_id=${farm.id}`);
    if (!alerts.length) { el.innerHTML = `<div class="alert success"><div class="ico">✅</div><div class="body"><strong>All clear</strong>No alerts for this farm right now.</div></div>`; return; }
    el.innerHTML = alerts.slice(0, 5).map(alertHtml).join("");
  } catch (e) { el.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

async function loadIrrigation() {
  const el = $("#irrigation");
  try {
    const items = await api(`/api/irrigation/farm/${farm.id}`);
    if (!items.length) { el.innerHTML = `<div class="empty">Add an active crop plan to get irrigation advice.</div>`; return; }
    el.innerHTML = items.map((i) => `
      <div class="alert ${i.recommend ? "warning" : "success"}">
        <div class="ico">${i.recommend ? "💧" : "🚫"}</div>
        <div class="body"><strong>${esc(i.crop)} · ${esc(i.stage)}</strong>${esc(i.message)}<div class="tiny" style="margin-top:4px">${esc(i.reasons[0] || "")}</div></div>
      </div>`).join("");
  } catch (e) { el.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

async function loadMarket() {
  const el = $("#market");
  try {
    const markets = await api(`/api/market/markets`);
    const m = markets[0];
    const prices = await api(`/api/market/latest?market=${encodeURIComponent(m)}`);
    el.innerHTML = `<p class="tiny">${esc(m)}</p><table>` + prices.slice(0, 6).map((p) => `<tr><td>${esc(p.crop_name)}</td><td class="num"><strong>KSh ${p.price_per_kg}</strong>/kg</td></tr>`).join("") + `</table>`;
  } catch (e) { el.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

async function loadPerformance() {
  const el = $("#performance");
  try {
    const s = await api(`/api/analytics/summary?farm_id=${farm.id}`);
    el.innerHTML = `
      <div class="grid cols-3" style="gap:10px">
        <div class="stat"><span class="label">Revenue</span><span class="value sm">${fmt.money(s.revenue)}</span></div>
        <div class="stat"><span class="label">Expenses</span><span class="value sm">${fmt.money(s.expenses)}</span></div>
        <div class="stat"><span class="label">Profit</span><span class="value sm" style="color:${s.profit >= 0 ? "var(--success)" : "var(--danger)"}">${fmt.money(s.profit)}</span></div>
      </div>
      <h3 style="margin-top:16px">Harvest ${s.year}</h3>
      ${s.harvest_by_crop.length ? `<table>${s.harvest_by_crop.slice(0, 4).map((h) => `<tr><td>${h.icon} ${esc(h.crop_name)}</td><td class="num">${fmt.num(h.quantity_kg)} kg</td></tr>`).join("")}</table>` : `<p class="tiny">No harvests recorded yet.</p>`}`;
  } catch (e) { el.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

init().catch((e) => console.error(e));

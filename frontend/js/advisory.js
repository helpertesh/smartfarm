let farms = [];
const cap = (s) => s ? s[0].toUpperCase() + s.slice(1) : "";

async function init() {
  const [opts, crops] = await Promise.all([api("/api/advisory/options"), api("/api/advisory/crops")]);
  farms = await api("/api/farms");
  $("#soilSel").innerHTML = opts.soil_types.map((s) => option(s, cap(s))).join("");
  $("#waterSel").innerHTML = opts.water_sources.map((s) => option(s, cap(s))).join("");
  $("#seasonSel").innerHTML = opts.seasons.map((s) => option(s.key, s.name, s.key === opts.current_season)).join("");
  $("#farmSel").innerHTML += farms.map((f) => option(f.id, `${f.name} · ${f.location_name}`, f.id === FarmStore.get())).join("");
  $("#farmSel").addEventListener("change", fillFromFarm);
  $("#advForm").addEventListener("submit", (e) => { e.preventDefault(); run(); });
  $("#library").innerHTML = crops.map((c) => `
    <div class="card" style="padding:14px">
      <div style="font-size:28px">${c.icon}</div>
      <strong>${esc(c.name)}</strong>
      <div class="tiny">${esc(cap(c.category))} · ${c.duration_days} days · ${esc(c.water_need)} water</div>
      <a class="small" href="calendar.html?crop=${c.key}">Plan this crop →</a>
    </div>`).join("");
  fillFromFarm();
  if ($("#farmSel").value) run();
}

function fillFromFarm() {
  const id = Number($("#farmSel").value);
  const f = farms.find((x) => x.id === id);
  if (!f) return;
  const el = $("#advForm").elements;
  el.soil_type.value = f.soil_type;
  el.water_source.value = f.water_source;
  el.farm_size_acres.value = f.size_acres;
}

async function run() {
  const el = $("#advForm").elements;
  const body = {
    soil_type: el.soil_type.value,
    season: el.season.value,
    water_source: el.water_source.value,
    farm_size_acres: Number(el.farm_size_acres.value) || null,
    altitude_m: el.altitude_m.value ? Number(el.altitude_m.value) : null,
  };
  const out = $("#results");
  out.innerHTML = `<div class="empty">Thinking…</div>`;
  try {
    const d = await api("/api/advisory/recommend", { method: "POST", body });
    $("#ctx").textContent = `${d.season_name} · ${cap(body.soil_type)} soil · ${cap(body.water_source)}`;
    out.innerHTML = d.recommendations.map((r) => `
      <div class="crop-rec">
        <div class="ico">${r.icon}</div>
        <div style="flex:1;min-width:0">
          <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
            <strong>${esc(r.name)}</strong>
            <span class="badge ${r.score >= 80 ? "success" : r.score >= 60 ? "info" : r.score >= 40 ? "warning" : "danger"}">${esc(r.suitability)} · ${r.score}</span>
          </div>
          <div class="score" style="margin:6px 0"><span style="width:${r.score}%"></span></div>
          <ul>
            ${r.reasons.map((x) => `<li>✓ ${esc(x)}</li>`).join("")}
            ${r.warnings.map((x) => `<li style="color:var(--warning)">⚠ ${esc(x)}</li>`).join("")}
          </ul>
          <a class="small" href="calendar.html?crop=${r.key}">Plan ${esc(r.name)} →</a>
        </div>
      </div>`).join("");
  } catch (e) { out.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

init().catch(console.error);

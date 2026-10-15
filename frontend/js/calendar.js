let farms = [], farm = null, crops = [];

async function init() {
  [farms, crops] = await Promise.all([api("/api/farms"), api("/api/advisory/crops")]);
  if (!farms.length) { $("#plans").innerHTML = `<div class="empty">Add a farm first. <a href="farms.html?first=1">Add farm</a></div>`; return; }
  farm = await FarmStore.pick(farms);
  $("#farmPicker").appendChild(farmSelector(farms, farm.id, (id) => { farm = farms.find((f) => f.id === id); loadPlans(); }));
  const pre = new URLSearchParams(location.search).get("crop");
  $("#cropSel").innerHTML = crops.map((c) => option(c.key, `${c.icon} ${c.name} (${c.duration_days} days)`, c.key === pre)).join("");
  const form = $("#planForm");
  form.elements.planting_date.value = fmt.today();
  form.addEventListener("submit", createPlan);
  form.elements.crop_key.addEventListener("change", preview);
  form.elements.planting_date.addEventListener("change", preview);
  preview();
  loadPlans();
}

async function preview() {
  const el = $("#planForm").elements;
  if (!el.planting_date.value) return;
  const d = await api(`/api/calendar/preview?crop_key=${el.crop_key.value}&planting_date=${el.planting_date.value}`);
  $("#preview").innerHTML = `<ul class="timeline">` + d.activities.map((a) => `<li><div class="when">Day ${a.day_offset} · ${fmt.date(a.due_date)}</div><div>${esc(a.title)}</div></li>`).join("") + `</ul>`;
}

async function createPlan(e) {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target).entries());
  f.farm_id = farm.id; f.area_acres = Number(f.area_acres);
  try {
    await api("/api/calendar/plans", { method: "POST", body: f });
    notice($("#formMsg"), "Crop plan created with its activity calendar.", "ok");
    loadPlans();
  } catch (err) { notice($("#formMsg"), err.message); }
}

async function loadPlans() {
  const box = $("#plans");
  const plans = await api(`/api/calendar/plans?farm_id=${farm.id}`);
  if (!plans.length) { box.innerHTML = `<div class="empty">No crop plans for ${esc(farm.name)} yet.</div>`; return; }
  const today = fmt.today();
  box.innerHTML = plans.map((p) => {
    const done = p.activities.filter((a) => a.completed).length;
    const next = p.activities.find((a) => !a.completed);
    const pct = Math.round((done / p.activities.length) * 100);
    return `
    <div class="card" style="margin-bottom:14px;padding:16px" data-plan="${p.id}">
      <div class="card-head">
        <div><h3>${p.crop_icon} ${esc(p.crop_name)} <span class="badge ${p.status === "active" ? "success" : ""}">${esc(p.status)}</span></div>
        <div class="tiny">Planted ${fmt.date(p.planting_date)} · ${p.area_acres} acres</div></div>
        <div class="toolbar">
          <button class="btn secondary sm" data-irr="${p.id}">💧 Irrigation</button>
          ${p.status === "active" ? `<button class="btn secondary sm" data-status="${p.id}" data-val="harvested">Mark harvested</button>` : ""}
          <button class="btn danger sm" data-del="${p.id}">Delete</button>
        </div>
      </div>
      <div class="score" style="margin-bottom:6px"><span style="width:${pct}%"></span></div>
      <div class="tiny" style="margin-bottom:10px">${done}/${p.activities.length} activities done${next ? ` · next: <strong>${esc(next.title)}</strong> on ${fmt.date(next.due_date)}` : ""}</div>
      <div id="irr-${p.id}"></div>
      <details ${p.status === "active" ? "open" : ""}>
        <summary class="small" style="cursor:pointer;color:var(--primary)">Show schedule</summary>
        <ul class="timeline" style="margin-top:12px">
          ${p.activities.map((a) => `
            <li class="${a.completed ? "done" : a.due_date === today ? "today" : ""}">
              <label style="display:flex;gap:10px;align-items:flex-start;cursor:pointer;margin:0;color:var(--text);font-weight:400">
                <input type="checkbox" data-act="${a.id}" ${a.completed ? "checked" : ""} style="width:auto;margin-top:4px" />
                <span>
                  <span class="when">Day ${a.day_offset} · ${fmt.date(a.due_date)} ${a.due_date < today && !a.completed ? `<span class="badge danger">overdue</span>` : ""}</span><br />
                  <strong style="${a.completed ? "text-decoration:line-through;color:var(--text-3)" : ""}">${esc(a.title)}</strong>
                  <div class="small muted">${esc(a.description || "")}</div>
                </span>
              </label>
            </li>`).join("")}
        </ul>
      </details>
    </div>`;
  }).join("");

  $$("input[data-act]").forEach((cb) => cb.addEventListener("change", async () => { await api(`/api/calendar/activities/${cb.dataset.act}/toggle`, { method: "PATCH" }); loadPlans(); }));
  $$("[data-del]").forEach((b) => b.addEventListener("click", async () => { if (confirm("Delete this crop plan?")) { await api(`/api/calendar/plans/${b.dataset.del}`, { method: "DELETE" }); loadPlans(); } }));
  $$("[data-status]").forEach((b) => b.addEventListener("click", async () => { await api(`/api/calendar/plans/${b.dataset.status}`, { method: "PATCH", body: { status: b.dataset.val } }); loadPlans(); }));
  $$("[data-irr]").forEach((b) => b.addEventListener("click", () => irrigation(Number(b.dataset.irr))));
}

async function irrigation(planId) {
  const box = $(`#irr-${planId}`);
  box.innerHTML = `
    <div class="card" style="padding:14px;margin-bottom:12px;background:var(--surface-2)">
      <div class="form-row">
        <div class="field"><label>Soil moisture % (optional, from sensor or feel test)</label><input type="number" min="0" max="100" id="sm-${planId}" placeholder="e.g. 35" /></div>
        <div class="field"><label>Days since last irrigation (optional)</label><input type="number" min="0" id="li-${planId}" placeholder="e.g. 2" /></div>
      </div>
      <button class="btn sm" id="irrGo-${planId}">Get irrigation advice</button>
      <div id="irrOut-${planId}" style="margin-top:10px"></div>
    </div>`;
  const run = async () => {
    const sm = $(`#sm-${planId}`).value, li = $(`#li-${planId}`).value;
    const out = $(`#irrOut-${planId}`);
    out.innerHTML = `<span class="muted">Checking weather…</span>`;
    try {
      const r = await api("/api/irrigation/advice", { method: "POST", body: { crop_plan_id: planId, soil_moisture_pct: sm ? Number(sm) : null, last_irrigation_days_ago: li ? Number(li) : null } });
      out.innerHTML = `<div class="alert ${r.recommend ? "warning" : "success"}"><div class="ico">${r.recommend ? "💧" : "🚫"}</div><div class="body"><strong>${esc(r.message)}</strong>
        <div class="small">Stage: ${esc(r.stage)} (day ${r.days_since_planting}) · water need ≈ ${r.water_demand_mm} mm/day</div>
        <ul style="margin:6px 0 0;padding-left:18px" class="small">${r.reasons.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div></div>`;
    } catch (e) { out.innerHTML = `<span class="notice error">${esc(e.message)}</span>`; }
  };
  $(`#irrGo-${planId}`).addEventListener("click", run);
  run();
}

init().catch(console.error);

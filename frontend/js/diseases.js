let crops = [], symptoms = [], diseases = [];

async function init() {
  [crops, symptoms, diseases] = await Promise.all([api("/api/advisory/crops"), api("/api/diseases/symptoms"), api("/api/diseases")]);
  $("#cropSel").innerHTML = crops.map((c) => option(c.key, `${c.icon} ${c.name}`)).join("");
  $("#symptoms").innerHTML = symptoms.map((s) => `<label><input type="checkbox" name="symptoms" value="${s.key}" /> ${esc(s.label)}</label>`).join("");
  $("#libFilter").innerHTML += crops.map((c) => option(c.key, c.name)).join("");
  $("#libFilter").addEventListener("change", renderLibrary);
  $("#dxForm").addEventListener("submit", (e) => { e.preventDefault(); diagnose(); });
  renderLibrary();
}

async function diagnose() {
  const crop = $("#cropSel").value;
  const picked = $$("input[name=symptoms]:checked").map((c) => c.value);
  const out = $("#results");
  if (!picked.length) { out.innerHTML = `<div class="empty">Select at least one symptom.</div>`; return; }
  try {
    const d = await api("/api/diseases/diagnose", { method: "POST", body: { crop_key: crop, symptoms: picked } });
    $("#ctx").textContent = `${d.crop} · ${d.symptoms.join(", ")}`;
    if (!d.results.length) { out.innerHTML = `<div class="empty">No matching disease found for these symptoms. Try adding more symptoms or consult an extension officer.</div>`; return; }
    out.innerHTML = d.results.map((r, i) => `
      <div class="card" style="padding:16px;margin-bottom:12px;${i === 0 ? "border-color:var(--primary)" : ""}">
        <div class="card-head" style="margin-bottom:6px">
          <h3>${i === 0 ? "⚠️ " : ""}${esc(r.name)} <span class="badge ${r.type === "pest" ? "warning" : r.type === "nutrient" ? "info" : "danger"}">${esc(r.type)}</span></h3>
          <span class="badge ${r.confidence >= 0.75 ? "success" : r.confidence >= 0.5 ? "info" : ""}">${Math.round(r.confidence * 100)}% match</span>
        </div>
        <p>${esc(r.description)}</p>
        <p class="small muted"><strong>Favourable conditions:</strong> ${esc(r.conditions)}</p>
        <p class="small muted"><strong>Matched symptoms:</strong> ${r.matched_symptoms.map(esc).join(", ")}</p>
        <strong class="small">Recommended actions</strong>
        <ol class="small" style="margin:4px 0 0;padding-left:20px">${r.actions.map((a) => `<li>${esc(a)}</li>`).join("")}</ol>
      </div>`).join("");
  } catch (e) { out.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}

function renderLibrary() {
  const f = $("#libFilter").value;
  const items = f ? diseases.filter((d) => d.crops.includes(f)) : diseases;
  $("#library").innerHTML = items.map((d) => `
    <div class="card" style="padding:14px">
      <h3>${esc(d.name)} <span class="badge ${d.type === "pest" ? "warning" : d.type === "nutrient" ? "info" : "danger"}">${esc(d.type)}</span></h3>
      <p class="small">${esc(d.description)}</p>
      <p class="tiny">Affects: ${d.crop_names.map(esc).join(", ")}</p>
      <details><summary class="small" style="cursor:pointer;color:var(--primary)">What to do</summary>
        <ul class="small" style="padding-left:18px;margin:6px 0 0">${d.actions.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></details>
    </div>`).join("");
}

init().catch(console.error);

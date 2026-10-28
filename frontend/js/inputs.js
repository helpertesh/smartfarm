let farms = [], farm = null, opts = { categories: [], units: [] };

async function init() {
  [farms, opts] = await Promise.all([api("/api/farms"), api("/api/inputs/options")]);
  if (!farms.length) { $("#stats").innerHTML = `<div class="empty" style="grid-column:1/-1">Add a farm first. <a href="farms.html?first=1">Add farm</a></div>`; return; }
  farm = await FarmStore.pick(farms);
  $("#farmPicker").prepend(farmSelector(farms, farm.id, (id) => { farm = farms.find((f) => f.id === id); load(); }));
  $("#catSel").innerHTML = opts.categories.map((c) => option(c, c[0].toUpperCase() + c.slice(1))).join("");
  $("#unitSel").innerHTML = opts.units.map((u) => option(u, u)).join("");
  $("#addForm").addEventListener("submit", add);
  load();
}

async function add(e) {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target).entries());
  f.farm_id = farm.id; f.quantity = Number(f.quantity); f.reorder_level = Number(f.reorder_level);
  try {
    await api("/api/inputs", { method: "POST", body: f });
    notice($("#addMsg"), `${f.name} added.`, "ok");
    e.target.elements.name.value = ""; e.target.elements.quantity.value = "";
    load();
  } catch (err) { notice($("#addMsg"), err.message); }
}

async function adjust(item, sign) {
  const input = $(`[data-amt="${item.id}"]`);
  const amt = Number(input.value);
  if (!amt || amt <= 0) { notice($("#msg"), "Enter an amount first."); input.focus(); return; }
  const quantity = Math.max(0, item.quantity + sign * amt);
  try { await api(`/api/inputs/${item.id}`, { method: "PATCH", body: { quantity } }); $("#msg").classList.add("hidden"); load(); }
  catch (err) { notice($("#msg"), err.message); }
}

function statusBadge(i) {
  if (i.quantity === 0) return `<span class="badge danger">out of stock</span>`;
  if (i.low) return `<span class="badge warning">low</span>`;
  return `<span class="badge success">ok</span>`;
}

async function load() {
  const items = await api(`/api/inputs?farm_id=${farm.id}`);
  const low = items.filter((i) => i.low);
  $("#stats").innerHTML = `
    <div class="card stat"><span class="label">Items tracked</span><span class="value">${items.length}</span></div>
    <div class="card stat"><span class="label">Running low</span><span class="value" style="color:${low.length ? "var(--warning)" : "var(--success)"}">${low.length}</span></div>
    <div class="card stat"><span class="label">Out of stock</span><span class="value" style="color:${items.some((i) => i.quantity === 0) ? "var(--danger)" : "var(--success)"}">${items.filter((i) => i.quantity === 0).length}</span></div>`;

  if (!items.length) { $("#list").innerHTML = `<div class="empty">Nothing recorded yet. Add your first input below.</div>`; return; }
  $("#list").innerHTML = `<table><thead><tr><th>Input</th><th>Category</th><th class="num">In store</th><th class="num">Alert at</th><th>Status</th><th>Use / restock</th><th></th></tr></thead><tbody>` +
    items.map((i) => `<tr>
      <td><strong>${esc(i.name)}</strong></td>
      <td class="muted">${esc(i.category)}</td>
      <td class="num">${fmt.num(i.quantity, 1)} ${esc(i.unit)}</td>
      <td class="num muted">${fmt.num(i.reorder_level, 1)} ${esc(i.unit)}</td>
      <td>${statusBadge(i)}</td>
      <td><div class="toolbar">
        <input type="number" min="0" step="0.1" placeholder="amount" data-amt="${i.id}" style="width:90px" />
        <button class="btn secondary sm" data-use="${i.id}">− Use</button>
        <button class="btn secondary sm" data-add="${i.id}">+ Restock</button>
      </div></td>
      <td class="num"><a href="#" data-del="${i.id}" class="small">delete</a></td>
    </tr>`).join("") + `</tbody></table>`;

  const byId = Object.fromEntries(items.map((i) => [i.id, i]));
  $$("[data-use]").forEach((b) => b.addEventListener("click", () => adjust(byId[b.dataset.use], -1)));
  $$("[data-add]").forEach((b) => b.addEventListener("click", () => adjust(byId[b.dataset.add], 1)));
  $$("[data-del]").forEach((a) => a.addEventListener("click", async (e) => {
    e.preventDefault();
    if (confirm(`Delete ${byId[a.dataset.del].name}?`)) { await api(`/api/inputs/${a.dataset.del}`, { method: "DELETE" }); load(); }
  }));
}

init().catch(console.error);

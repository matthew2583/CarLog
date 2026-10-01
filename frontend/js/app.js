let tab = "cars";
let editItem = null;
let cars = [];
let rows = [];
let kinds = [];
let filters = { car_id: "", kind: "", date_from: "", date_to: "" };

const carName = (id) => {
  const c = cars.find((c) => c.id === id);
  return c ? c.brand + " " + c.model : "#" + id;
};

const TABS = {
  cars: {
    label: "Автомобили",
    path: "/cars",
    cols: [
      ["brand", "Марка"], ["model", "Модель"],
      ["year", "Год"], ["mileage", "Пробег, км"],
    ],
    fields: () => [
      { name: "brand", label: "Марка", type: "text", required: true, attrs: 'maxlength="50"' },
      { name: "model", label: "Модель", type: "text", required: true, attrs: 'maxlength="50"' },
      { name: "year", label: "Год выпуска", type: "number", attrs: `min="1950" max="${new Date().getFullYear() + 1}"` },
      { name: "mileage", label: "Пробег, км", type: "number", attrs: 'min="0" max="2000000"' },
    ],
  },
  records: {
    label: "Записи",
    path: "/records",
    cols: [
      ["date", "Дата"],
      ["car_id", "Автомобиль", (r) => carName(r.car_id)],
      ["kind", "Тип"],
      ["cost", "Цена", (r) => money(r.cost)],
      ["note", "Заметка"],
    ],
    fields: () => [
      { name: "car_id", label: "Автомобиль", type: "select", required: true,
        options: cars.map((c) => [c.id, c.brand + " " + c.model]) },
      { name: "date", label: "Дата", type: "date", required: true, def: today(), attrs: `max="${today()}"` },
      { name: "kind", label: "Тип", type: "select", required: true,
        options: kinds.map((k) => [k, k]) },
      { name: "cost", label: "Цена", type: "number", attrs: 'min="0" step="0.01"' },
      { name: "note", label: "Заметка", type: "text", attrs: 'maxlength="500"' },
    ],
  },
};

async function run(fn) {
  try {
    clearError();
    await fn();
  } catch (err) {
    showError(err.message);
  }
}

function showAuth() {
  el("auth-view").hidden = false;
  el("main-view").hidden = true;
  el("user").hidden = true;
}

async function showApp() {
  el("auth-view").hidden = true;
  el("main-view").hidden = false;
  el("user").hidden = false;
  el("username").textContent = session.username || "";
  await run(async () => { kinds = await api.get("/kinds"); });
  drawTabs();
  refresh();
}

function logout() {
  session.clear();
  tab = "cars";
  editItem = null;
  el("stats").innerHTML = "";
  clearError();
  showAuth();
}

async function refresh() {
  await run(async () => {
    cars = await api.get("/cars");
    rows = tab === "cars" ? cars : await api.get("/records" + qs(filters));
    drawFilters();
    drawTable();
    drawForm();
  });
}


function drawTabs() {
  const nav = el("tabs");
  nav.innerHTML = "";
  for (const k in TABS) {
    const b = document.createElement("button");
    b.textContent = TABS[k].label;
    b.className = k === tab ? "active" : "";
    b.onclick = () => {
      tab = k;
      editItem = null;
      el("stats").innerHTML = "";
      drawTabs();
      refresh();
    };
    nav.appendChild(b);
  }
}

const option = (v, label, cur) =>
  `<option value="${esc(v)}"${String(v) === String(cur) ? " selected" : ""}>${esc(label)}</option>`;

function drawFilters() {
  const box = el("filters");
  if (tab !== "records") { box.innerHTML = ""; return; }
  box.innerHTML = `
    <label><span>Автомобиль</span><select name="car_id">
      ${option("", "Все", filters.car_id)}
      ${cars.map((c) => option(c.id, c.brand + " " + c.model, filters.car_id)).join("")}
    </select></label>
    <label><span>Тип</span><select name="kind">
      ${option("", "Все", filters.kind)}
      ${kinds.map((k) => option(k, k, filters.kind)).join("")}
    </select></label>
    <label><span>С</span><input type="date" name="date_from" value="${esc(filters.date_from)}"></label>
    <label><span>По</span><input type="date" name="date_to" value="${esc(filters.date_to)}"></label>
    <button type="button" class="btn btn-cancel" data-action="reset">Сбросить</button>`;
}

function drawTable() {
  const t = TABS[tab];
  el("table-head").innerHTML =
    "<tr>" + t.cols.map((c) => `<th>${c[1]}</th>`).join("") + "<th></th></tr>";

  el("table-body").innerHTML = rows.length
    ? rows.map((r) =>
        "<tr>" +
        t.cols.map((c) => `<td>${esc(c[2] ? c[2](r) : r[c[0]])}</td>`).join("") +
        '<td class="actions">' +
        (tab === "cars"
          ? `<button class="btn btn-sm btn-info" data-action="stats" data-id="${r.id}">Статистика</button> `
          : "") +
        `<button class="btn btn-sm btn-ok" data-action="edit" data-id="${r.id}">✎</button> ` +
        `<button class="btn btn-sm btn-del" data-action="del" data-id="${r.id}">✕</button>` +
        "</td></tr>"
      ).join("")
    : `<tr><td colspan="${t.cols.length + 1}">Пусто</td></tr>`;
}

function fieldHtml(f, val) {
  let input;
  if (f.type === "select") {
    input =
      `<select name="${f.name}"${f.required ? " required" : ""}>` +
      f.options.map(([v, l]) => option(v, l, val)).join("") +
      "</select>";
  } else {
    input = `<input name="${f.name}" type="${f.type}" ${f.attrs || ""}${f.required ? " required" : ""} value="${esc(val)}">`;
  }
  return `<label><span>${f.label}</span>${input}</label>`;
}

function drawForm() {
  const form = el("form");
  if (tab === "records" && !cars.length) {
    form.innerHTML = "<p>Сначала добавьте автомобиль на вкладке «Автомобили».</p>";
    return;
  }
  let h = `<h3>${editItem ? "Редактировать" : "Добавить"}</h3>`;
  for (const f of TABS[tab].fields()) h += fieldHtml(f, editItem ? editItem[f.name] : f.def);
  h += `<div class="form-actions"><button type="submit" class="btn btn-ok">${editItem ? "Сохранить" : "Добавить"}</button>`;
  if (editItem) h += '<button type="button" class="btn btn-cancel" data-action="cancel">Отмена</button>';
  h += "</div>";
  form.innerHTML = h;
}


async function showStats(id) {
  await run(async () => {
    const [car, s] = await Promise.all([
      api.get("/cars/" + id),
      api.get(`/cars/${id}/stats`),
    ]);
    let h = `<div class="card"><h3>Статистика: ${esc(car.brand)} ${esc(car.model)}
      <button class="btn btn-cancel btn-sm" data-action="close-stats">✕</button></h3>`;
    if (!s.records_count) {
      h += "<p>Записей пока нет.</p>";
    } else {
      h += `<p>Записей: <b>${s.records_count}</b> ·
            Всего потрачено: <b>${money(s.total_cost)}</b> ·
            В среднем за месяц: <b>${money(s.avg_per_month)}</b> ·
            Последняя запись: <b>${esc(s.last_record_date)}</b></p>
        <h4>По типам</h4>
        <table><tr><th>Тип</th><th>Записей</th><th>Сумма</th></tr>
        ${s.by_kind.map((k) => `<tr><td>${esc(k.kind)}</td><td>${k.count}</td><td>${money(k.total)}</td></tr>`).join("")}</table>
        <h4>По месяцам</h4>
        <table><tr><th>Месяц</th><th>Сумма</th></tr>
        ${s.by_month.map((m) => `<tr><td>${esc(m.month)}</td><td>${money(m.total)}</td></tr>`).join("")}</table>`;
    }
    el("stats").innerHTML = h + "</div>";
  });
}


async function startEdit(id) {
  await run(async () => {
    editItem = await api.get(`${TABS[tab].path}/${id}`); 
    drawForm();
    el("form").scrollIntoView({ behavior: "smooth" });
  });
}

async function submit(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = {};
  for (const f of TABS[tab].fields()) {
    const v = fd.get(f.name);
    if (v === null || v === "") continue; 
    body[f.name] = f.type === "number" || f.name === "car_id" ? Number(v) : v;
  }
  const path = TABS[tab].path;
  await run(async () => {
    if (editItem) await api.put(`${path}/${editItem.id}`, body);
    else await api.post(path, body);
    editItem = null;
    await refresh();
  });
}

async function remove(id) {
  const msg = tab === "cars" ? "Удалить автомобиль и все его записи?" : "Удалить запись?";
  if (!confirm(msg)) return;
  await run(async () => {
    await api.del(`${TABS[tab].path}/${id}`);
    if (editItem && editItem.id === id) editItem = null;
    await refresh();
  });
}


el("form").onsubmit = submit;
el("form").onclick = (e) => {
  if (e.target.dataset.action === "cancel") { editItem = null; drawForm(); }
};

el("table-body").onclick = (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  const id = Number(b.dataset.id);
  if (b.dataset.action === "edit") startEdit(id);
  else if (b.dataset.action === "del") remove(id);
  else if (b.dataset.action === "stats") showStats(id);
};

el("filters").onchange = (e) => {
  filters[e.target.name] = e.target.value;
  refresh();
};
el("filters").onclick = (e) => {
  if (e.target.dataset.action === "reset") {
    filters = { car_id: "", kind: "", date_from: "", date_to: "" };
    refresh();
  }
};

el("stats").onclick = (e) => {
  if (e.target.dataset.action === "close-stats") el("stats").innerHTML = "";
};

el("logout").onclick = logout;
window.addEventListener("unauthorized", showAuth);


if (session.token) showApp();
else showAuth();
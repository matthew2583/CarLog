const API = "http://localhost:8000";

const TABS = {
  cars: {
    label: "Автомобили", url: API + "/cars",
    cols: ["id","brand","model","year","mileage"],
    head: ["ID","Марка","Модель","Год","Пробег"],
    form: [["brand","Марка","text",1],["model","Модель","text",1],
           ["year","Год","number"],["mileage","Пробег","number"]]
  },
  records: {
    label: "Записи", url: API + "/records",
    cols: ["id","car_id","date","kind","cost","note"],
    head: ["ID","ID авто","Дата","Тип","Цена","Заметка"],
    form: [["car_id","ID авто","number",1],["date","Дата","date",1],
           ["kind","Тип","text",1],["cost","Цена","number"],["note","Заметка","text"]]
  }
};

let tab = "cars", editId = null;

function drawTabs() {
  const nav = document.getElementById("tabs");
  nav.innerHTML = "";
  for (const k in TABS) {
    const b = document.createElement("button");
    b.textContent = TABS[k].label;
    b.className = k === tab ? "active" : "";
    b.onclick = () => { tab = k; editId = null; drawTabs(); drawForm(); load(); };
    nav.appendChild(b);
  }
}

async function load() {
  const c = TABS[tab];
  const data = await (await fetch(c.url)).json();
  document.getElementById("table-head").innerHTML =
    "<tr>" + c.head.map(h => "<th>"+h+"</th>").join("") + "<th></th></tr>";
  document.getElementById("table-body").innerHTML = data.length
    ? data.map(r =>
        "<tr>" + c.cols.map(k => "<td>"+(r[k]??"")+"</td>").join("") +
        '<td><button onclick="edit('+r.id+')">✎</button> ' +
        '<button onclick="del('+r.id+')">✕</button></td></tr>').join("")
    : '<tr><td colspan="'+(c.cols.length+1)+'">Пусто</td></tr>';
}

function drawForm(val) {
  const c = TABS[tab];
  let h = "<h3>"+(editId ? "Редактировать" : "Добавить")+"</h3>";
  for (const [name,label,type,req] of c.form)
    h += '<label><span>'+label+'</span><input name="'+name+'" type="'+type+'"'+
         (req?' required':'')+' value="'+(val?val[name]??"":"")+'"></label>';
  h += '<button type="submit" class="btn btn-ok">'+(editId?"Сохранить":"Добавить")+'</button> ';
  if (editId) h += '<button type="button" class="btn btn-cancel" onclick="editId=null;drawForm()">Отмена</button>';
  const f = document.getElementById("form");
  f.innerHTML = h;
  f.onsubmit = submit;
}

async function submit(e) {
  e.preventDefault();
  const c = TABS[tab], fd = new FormData(document.getElementById("form")), body = {};
  for (const [name,,type] of c.form) {
    let v = fd.get(name);
    if (type==="number" && v) v = Number(v);
    body[name] = v === "" ? null : v;
  }
  const res = await fetch(editId ? c.url+"/"+editId : c.url, {
    method: editId ? "PUT" : "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });
  if (!res.ok) { alert("Ошибка: "+((await res.json().catch(()=>({}))).detail||res.status)); return; }
  editId = null; drawForm(); load();
}

async function edit(id) {
  editId = id;
  drawForm(await (await fetch(TABS[tab].url+"/"+id)).json());
}

async function del(id) {
  if (confirm("Удалить #"+id+"?")) { await fetch(TABS[tab].url+"/"+id,{method:"DELETE"}); load(); }
}

drawTabs(); drawForm(); load();

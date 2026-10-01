const el = (id) => document.getElementById(id);

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));

const money = (v) => Number(v).toFixed(2);

const today = () => new Date().toLocaleDateString("sv-SE");

function showError(msg) {
  const box = el("error");
  box.textContent = msg;
  box.hidden = false;
}

function clearError() {
  el("error").hidden = true;
}
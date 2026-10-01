const TOKEN_KEY = "carlog_token";
const USER_KEY = "carlog_user";

const session = {
  get token() { return localStorage.getItem(TOKEN_KEY); },
  get username() { return localStorage.getItem(USER_KEY); },
  save(token, username) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, username);
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function errorMessage(data, status) {
  if (!data || !data.detail) return "Ошибка " + status;
  if (typeof data.detail === "string") return data.detail;
  return data.detail
    .map((d) => {
      const field = (d.loc || []).slice(1).join(".");
      const msg = String(d.msg).replace("Value error, ", "");
      return field ? field + ": " + msg : msg;
    })
    .join("; ");
}

async function request(method, path, body) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (session.token) headers["Authorization"] = "Bearer " + session.token;

  let res;
  try {
    res = await fetch(CONFIG.API_URL + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Сервер недоступен");
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && session.token) {
      session.clear();
      window.dispatchEvent(new Event("unauthorized"));
    }
    throw new ApiError(res.status, errorMessage(data, res.status));
  }
  return data;
}

const api = {
  get: (path) => request("GET", path),
  post: (path, body) => request("POST", path, body),
  put: (path, body) => request("PUT", path, body),
  del: (path) => request("DELETE", path),
};

function qs(params) {
  const s = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v)
  ).toString();
  return s ? "?" + s : "";
}
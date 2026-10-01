el("auth-form").onsubmit = async (e) => {
  e.preventDefault();
  const action = e.submitter.dataset.action;
  const fd = new FormData(e.target);
  const username = fd.get("username").trim();
  try {
    clearError();
    const data = await api.post("/auth/" + action, {
      username,
      password: fd.get("password"),
    });
    session.save(data.access_token, username);
    e.target.reset();
    showApp();
  } catch (err) {
    showError(err.message);
  }
};
let currentSubreddit = null;

// ── Bootstrap ──────────────────────────────────────────────────────────────

async function init() {
  const me = await apiFetch("/api/auth/me");
  if (!me) { window.location.href = "/index.html"; return; }

  document.getElementById("user-email").textContent = me.email;
  document.getElementById("logout-btn").addEventListener("click", logout);
  document.getElementById("open-add-modal").addEventListener("click", openModal);
  document.getElementById("close-modal").addEventListener("click", closeModal);
  document.getElementById("confirm-add").addEventListener("click", addSubreddit);
  document.getElementById("modal-overlay").addEventListener("click", e => { if (e.target === e.currentTarget) closeModal(); });
  document.getElementById("subreddit-input").addEventListener("keydown", e => { if (e.key === "Enter") addSubreddit(); });
  document.getElementById("refresh-btn").addEventListener("click", () => { if (currentSubreddit) loadDigest(currentSubreddit, true); });
  document.getElementById("email-btn").addEventListener("click", sendEmail);

  await loadSubreddits();
}

// ── Auth ───────────────────────────────────────────────────────────────────

async function logout() {
  await apiFetch("/api/auth/logout", { method: "POST" });
  window.location.href = "/index.html";
}

// ── Subreddits ─────────────────────────────────────────────────────────────

async function loadSubreddits() {
  const subs = await apiFetch("/api/subreddits");
  if (!subs) return;
  renderSubredditList(subs);
  if (subs.length === 0) showEmptyState();
}

function renderSubredditList(subs) {
  const list = document.getElementById("subreddit-list");
  list.innerHTML = "";
  subs.forEach(({ subreddit }) => {
    const li = document.createElement("li");
    li.dataset.subreddit = subreddit;
    if (subreddit === currentSubreddit) li.classList.add("active");
    li.innerHTML = `
      <span class="subreddit-name">r/${subreddit}</span>
      <button class="remove-btn" title="Remove" data-subreddit="${subreddit}">&#215;</button>
    `;
    li.querySelector(".subreddit-name").addEventListener("click", () => selectSubreddit(subreddit));
    li.querySelector(".remove-btn").addEventListener("click", e => { e.stopPropagation(); removeSubreddit(subreddit); });
    list.appendChild(li);
  });
}

async function selectSubreddit(name) {
  currentSubreddit = name;
  document.querySelectorAll(".subreddit-list li").forEach(el => el.classList.toggle("active", el.dataset.subreddit === name));
  await loadDigest(name);
}

async function addSubreddit() {
  const input = document.getElementById("subreddit-input");
  const errorEl = document.getElementById("add-error");
  const name = input.value.trim().replace(/^r\//i, "");
  errorEl.classList.add("hidden");

  if (!name) return;

  const btn = document.getElementById("confirm-add");
  btn.textContent = "Adding…";
  btn.disabled = true;

  const result = await apiFetch("/api/subreddits", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subreddit: name }),
  });

  btn.textContent = "Add";
  btn.disabled = false;

  if (result && result.subreddit) {
    closeModal();
    input.value = "";
    await loadSubreddits();
    selectSubreddit(result.subreddit);
  } else if (result && result.detail) {
    errorEl.textContent = result.detail;
    errorEl.classList.remove("hidden");
  }
}

async function removeSubreddit(name) {
  const ok = await apiFetch(`/api/subreddits/${name}`, { method: "DELETE" });
  if (ok) {
    if (currentSubreddit === name) {
      currentSubreddit = null;
      showEmptyState();
    }
    await loadSubreddits();
    showToast(`r/${name} removed`, "success");
  }
}

// ── Digest ─────────────────────────────────────────────────────────────────

async function loadDigest(subreddit, forceRefresh = false) {
  setLoading(true);

  if (forceRefresh) {
    await apiFetch(`/api/digest/${subreddit}`, { method: "DELETE" });
  }

  const data = await apiFetch(`/api/digest/${subreddit}`);
  setLoading(false);

  if (!data) return;
  renderDigest(subreddit, data);
}

function renderDigest(subreddit, data) {
  document.getElementById("empty-state").classList.add("hidden");
  document.getElementById("digest-area").classList.remove("hidden");

  document.getElementById("digest-title").textContent = `r/${subreddit}`;

  const cachedNote = data.cached ? " (cached)" : " (fresh)";
  const date = new Date(data.generated_at + "Z").toLocaleString();
  document.getElementById("digest-meta").textContent = `Top posts · last 24h · Generated ${date}${cachedNote}`;

  const list = document.getElementById("post-list");
  list.innerHTML = "";

  if (!data.posts.length) {
    list.innerHTML = '<p style="color:#878a8c;">No posts found in the last 24 hours.</p>';
    return;
  }

  data.posts.forEach(post => {
    const card = document.createElement("div");
    card.className = "post-card";

    const flair = post.flair ? `<span class="post-flair">${post.flair}</span>` : "";
    const body = post.selftext
      ? `<p class="post-body">${post.selftext.slice(0, 300)}${post.selftext.length > 300 ? "…" : ""}</p>`
      : "";

    card.innerHTML = `
      <a href="${post.permalink}" target="_blank" rel="noopener" class="post-title">${post.title}</a>
      <div class="post-meta">
        <span>▲ ${post.score.toLocaleString()}</span>
        <span>💬 ${post.num_comments.toLocaleString()} comments</span>
        <span>u/${post.author}</span>
        ${flair}
      </div>
      ${body}
    `;
    list.appendChild(card);
  });
}

async function sendEmail() {
  if (!currentSubreddit) return;
  const btn = document.getElementById("email-btn");
  btn.textContent = "Sending…";
  btn.disabled = true;

  const result = await apiFetch(`/api/digest/${currentSubreddit}/email`, { method: "POST" });
  btn.textContent = "✉ Send to Email";
  btn.disabled = false;

  if (result && result.ok) {
    showToast(`Digest sent to ${result.sent_to}`, "success");
  } else {
    showToast(result?.detail || "Failed to send email", "error");
  }
}

// ── UI helpers ─────────────────────────────────────────────────────────────

function showEmptyState() {
  document.getElementById("empty-state").classList.remove("hidden");
  document.getElementById("digest-area").classList.add("hidden");
  document.getElementById("loading").classList.add("hidden");
}

function setLoading(on) {
  document.getElementById("loading").classList.toggle("hidden", !on);
  document.getElementById("digest-area").classList.toggle("hidden", on);
  document.getElementById("empty-state").classList.add("hidden");
}

function openModal() {
  document.getElementById("modal-overlay").classList.remove("hidden");
  document.getElementById("add-error").classList.add("hidden");
  setTimeout(() => document.getElementById("subreddit-input").focus(), 50);
}

function closeModal() {
  document.getElementById("modal-overlay").classList.add("hidden");
  document.getElementById("subreddit-input").value = "";
}

function showToast(msg, type = "") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast${type ? " " + type : ""}`;
  setTimeout(() => el.classList.add("hidden"), 3500);
}

// ── API helper ─────────────────────────────────────────────────────────────

async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, { credentials: "include", ...options });
    if (res.status === 401) { window.location.href = "/index.html"; return null; }
    return await res.json();
  } catch {
    showToast("Network error", "error");
    return null;
  }
}

// ── Start ──────────────────────────────────────────────────────────────────
init();

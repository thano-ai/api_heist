(() => {
  const API = window.location.origin.includes("5500")
    ? "http://127.0.0.1:5000"
    : "";

  const STORAGE_KEY = "api-heist-academy-state-v2";

  const state = {
    rulesAccepted: false,
    teamName: null,
    members: [],
    assignedChallenge: null,
    totalPoints: 0,
    challengesMeta: [],
    sessionChallenges: {},
    flagsFound: [],
    challengeStartedAt: null,
    session: {
      remainingSeconds: 100 * 60,
      running: false,
      ended: false,
      nextChallenge: 1,
    },
    pollId: null,
    pendingTeamName: null,
  };

  const $ = (sel) => document.querySelector(sel);
  const views = {
    rules: $("#view-rules"),
    register: $("#view-register"),
    handoff: $("#view-handoff"),
    ended: $("#view-ended"),
    roadmap: $("#view-roadmap"),
    challenge: $("#view-challenge"),
    leaderboard: $("#view-leaderboard"),
  };

  function saveLocal() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        rulesAccepted: state.rulesAccepted,
        teamName: state.teamName,
        members: state.members,
        assignedChallenge: state.assignedChallenge,
        totalPoints: state.totalPoints,
        flagsFound: state.flagsFound,
      })
    );
  }

  function loadLocal() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    } catch {
      return null;
    }
  }

  function clearLocal() {
    localStorage.removeItem(STORAGE_KEY);
  }

  async function api(path, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    if (state.teamName) headers["X-Team-Name"] = state.teamName;
    const res = await fetch(`${API}${path}`, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok && data.error) {
      const err = new Error(data.error);
      err.data = data;
      throw err;
    }
    return { res, data };
  }

  function showView(name) {
    Object.entries(views).forEach(([key, el]) => {
      if (el) el.classList.toggle("hidden", key !== name);
    });
  }

  function toast(msg, ms = 3200) {
    const el = $("#toast");
    el.textContent = msg;
    el.classList.remove("hidden");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.add("hidden"), ms);
  }

  function openModal(title, bodyHtml, { hideClose = false } = {}) {
    $("#modal-title").textContent = title;
    $("#modal-body").innerHTML = bodyHtml;
    $("#modal-close-btn").classList.toggle("hidden", hideClose);
    $("#modal").classList.remove("hidden");
  }

  function closeModal() {
    $("#modal").classList.add("hidden");
  }

  function formatTime(total) {
    const s = Math.max(0, Math.floor(total));
    const m = String(Math.floor(s / 60)).padStart(2, "0");
    const r = String(s % 60).padStart(2, "0");
    return `${m}:${r}`;
  }

  function applySession(session) {
    if (!session) return;
    state.session = {
      remainingSeconds: Number(session.remainingSeconds) || 0,
      running: Boolean(session.running),
      ended: Boolean(session.ended),
      nextChallenge:
        session.nextChallenge == null ? null : Number(session.nextChallenge),
    };
    if (session.challenges) {
      const mapped = {};
      Object.entries(session.challenges).forEach(([key, value]) => {
        mapped[Number(key)] = value;
      });
      state.sessionChallenges = mapped;
    }
    updateHud();
    // Callers decide navigation when session.ended
  }

  function updateHud() {
    const hasTeam = Boolean(state.teamName);
    const teamWrap = $("#hud-team-wrap");
    const pointsWrap = $("#hud-points-wrap");
    if (teamWrap) teamWrap.classList.toggle("hidden", !hasTeam);
    if (pointsWrap) pointsWrap.classList.toggle("hidden", !hasTeam);
    if (hasTeam) {
      const teamEl = $("#hud-team");
      const pointsEl = $("#hud-points");
      if (teamEl) teamEl.textContent = state.teamName;
      if (pointsEl) pointsEl.textContent = state.totalPoints;
    }
    const timerEl = $("#hud-timer");
    if (timerEl) timerEl.textContent = formatTime(state.session.remainingSeconds);
    const st = $("#hud-timer-state");
    if (st) {
      if (state.session.ended) {
        st.textContent = "Ended";
        st.className = "timer-state ended";
      } else if (state.session.running) {
        st.textContent = "Running";
        st.className = "timer-state running";
      } else {
        st.textContent = "Paused";
        st.className = "timer-state";
      }
    }
    const hud = $("#session-hud");
    if (hud) hud.classList.toggle("urgent", state.session.remainingSeconds <= 300);
  }

  function endGame() {
    stopPolling();
    state.session.ended = true;
    state.session.running = false;
    updateHud();
    toast("Session time is over. The game has stopped.");
    showView("ended");
  }

  async function refreshSession() {
    const { data } = await api("/api/game/session");
    applySession(data);
    if (data.ended) endGame();
    return data;
  }

  function startPolling() {
    stopPolling();
    state.pollId = setInterval(async () => {
      try {
        await refreshSession();
      } catch {
        /* ignore transient errors */
      }
    }, 1000);
  }

  function stopPolling() {
    if (state.pollId) clearInterval(state.pollId);
    state.pollId = null;
  }

  async function resumeTimer() {
    if (state.session.ended) return;
    const { data } = await api("/api/game/session/resume", { method: "POST", body: "{}" });
    applySession(data);
  }

  async function pauseTimer() {
    const { data } = await api("/api/game/session/pause", { method: "POST", body: "{}" });
    applySession(data);
  }

  function celebrate() {
    const burst = document.createElement("div");
    burst.style.cssText =
      "position:fixed;inset:0;pointer-events:none;z-index:80;overflow:hidden";
    for (let i = 0; i < 24; i += 1) {
      const bit = document.createElement("i");
      const left = Math.random() * 100;
      const color = ["#f0a06a", "#a8d4ec", "#f5d76e", "#fffefb"][i % 4];
      bit.style.cssText = `
        position:absolute;left:${left}%;top:-10px;width:8px;height:10px;
        border-radius:3px;background:${color};opacity:0.9;
        animation:fall ${1 + Math.random()}s ease-out forwards;
      `;
      burst.appendChild(bit);
    }
    const style = document.createElement("style");
    style.textContent =
      "@keyframes fall{to{transform:translateY(110vh) rotate(520deg);opacity:0}}";
    burst.appendChild(style);
    document.body.appendChild(burst);
    setTimeout(() => burst.remove(), 1600);
  }

  function allPathSolved() {
    return Array.from({ length: 10 }, (_, i) => i + 1).every(
      (id) => state.sessionChallenges[id]?.solved
    );
  }

  function resolveAssigned() {
    const n = Number(state.assignedChallenge);
    if (Number.isFinite(n) && n >= 1) return n;
    const next = Number(state.session?.nextChallenge);
    if (Number.isFinite(next) && next >= 1) return next;
    return null;
  }

  async function ensureAssignment() {
    if (!state.teamName) return resolveAssigned();

    // Prefer existing assignment if that challenge is still open
    let current = resolveAssigned();
    const shared = current ? state.sessionChallenges[current] : null;
    if (current && !shared?.solved) {
      state.assignedChallenge = current;
      saveLocal();
      return current;
    }

    // Ask server to assign the next open challenge
    try {
      const { data } = await api("/api/game/claim", {
        method: "POST",
        body: JSON.stringify({ teamName: state.teamName }),
      });
      applySession(data.session);
      state.assignedChallenge = Number(data.assignedChallenge);
      saveLocal();
      return state.assignedChallenge;
    } catch (err) {
      console.warn("claim failed, using session nextChallenge", err);
      current = Number(state.session?.nextChallenge);
      if (Number.isFinite(current) && current >= 1) {
        state.assignedChallenge = current;
        saveLocal();
        return current;
      }
      return null;
    }
  }

  function renderRoadmap() {
    const list = $("#roadmap-list");
    if (!list) return;
    list.innerHTML = "";
    const assigned = resolveAssigned();

    const banner = $("#assignment-banner");
    if (banner) {
      banner.textContent = assigned
        ? `Your team owns challenge ${assigned}. Click Start challenge to begin (timer runs while you solve).`
        : "No challenge assigned yet. Re-register your team or refresh the page.";
    }

    state.challengesMeta.forEach((meta) => {
      const id = Number(meta.id);
      const shared = state.sessionChallenges[id] || {};
      const isAssigned = assigned === id;
      const locked = !shared.solved && !isAssigned;
      const card = document.createElement("div");
      card.className = "level-card";
      if (locked) card.classList.add("locked");
      if (shared.solved) card.classList.add("solved");
      if (isAssigned && !shared.solved) card.classList.add("active");
      const status = shared.solved
        ? `Solved${shared.solvedBy ? ` · ${shared.solvedBy}` : ""}`
        : isAssigned
          ? "Your challenge"
          : "Waiting";
      card.innerHTML = `
        <div class="level-top">
          <span>Level ${id}: ${String(meta.title).split("(")[0].trim()}</span>
          <span class="lock">${status}</span>
        </div>
        <p>${meta.codename}</p>
        <span class="pts">+${meta.points} pts${shared.solved ? ` · ${shared.pointsEarned || 0} earned` : ""}</span>
      `;
      if (isAssigned && !shared.solved) {
        const start = document.createElement("button");
        start.type = "button";
        start.className = "btn btn-primary";
        start.style.marginTop = "0.75rem";
        start.textContent = "Start challenge";
        start.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          openChallenge(id);
        });
        card.appendChild(start);
      }
      list.appendChild(card);
    });

    const boss = $("#final-boss-card");
    if (!boss) return;
    const bossSolved = !!state.sessionChallenges[11]?.solved;
    boss.classList.toggle("locked", !allPathSolved());
    boss.classList.toggle("solved", bossSolved);
    const bossLock = boss.querySelector(".lock");
    if (bossLock) {
      bossLock.textContent = bossSolved ? "Solved" : allPathSolved() ? "Open" : "Locked";
    }
  }

  async function openChallenge(id) {
    id = Number(id);
    if (state.session.ended) {
      endGame();
      return;
    }
    const meta = state.challengesMeta.find((c) => Number(c.id) === id);
    if (!meta) {
      toast("Challenge data not loaded. Refresh the page and try again.");
      return;
    }
    state.challengeStartedAt = Date.now();
    try {
      await resumeTimer();
    } catch (err) {
      toast(err.message || "Cannot start timer");
      if (err.data?.session?.ended) endGame();
      return;
    }
    saveLocal();
    renderChallenge(meta);
    showView("challenge");
  }

  function renderChallenge(meta) {
    const shared = state.sessionChallenges[meta.id] || {};
    const elapsed = Math.floor((Date.now() - state.challengeStartedAt) / 1000);
    const locked = state.session.ended || shared.solved;
    const root = $("#challenge-detail");
    root.innerHTML = `
      <h2>Level ${meta.id}: ${meta.title}</h2>
      <p class="muted">Students: ${(state.members || []).join(", ") || "—"}</p>
      <hr class="rule" />
      <div class="block">
        <h3>Description</h3>
        <p>${meta.description}</p>
      </div>
      <div class="block">
        <h3>Objective</h3>
        <p>${meta.objective}</p>
      </div>
      <div class="block">
        <h3>API endpoint</h3>
        <code class="endpoint">${meta.endpoint}</code>
        <p class="muted" style="margin-top:0.5rem">Base: <code>${window.location.origin}/api</code> · Header <code>X-Team-Name: ${state.teamName}</code></p>
      </div>
      <div class="block hints">
        <div class="hint-row">
          <strong>Hint 1 (free)</strong>
          <p id="hint-free">${meta.free_hint}</p>
        </div>
        <div class="hint-row">
          <strong>Hint 2 (−5 points)</strong>
          <p id="hint-paid">Hidden until revealed.</p>
          <button class="btn btn-ghost" id="reveal-hint" ${locked ? "disabled" : ""}>Reveal hint</button>
        </div>
      </div>
      <div class="block">
        <h3>Submit flag</h3>
        <form class="flag-form" id="flag-form">
          <input name="flag" type="text" placeholder="FLAG{...}" ${locked ? "disabled" : ""} required />
          <button class="btn btn-primary" type="submit" ${locked ? "disabled" : ""}>Submit flag</button>
        </form>
      </div>
      <div class="meta-bar">
        <span>Challenge timer: <strong id="chal-time">${formatTime(elapsed)}</strong></span>
        <span>Status: <span class="status-dot ${shared.solved ? "ok" : ""}"></span> ${shared.solved ? "Solved" : "Open"}</span>
      </div>
    `;

    $("#reveal-hint")?.addEventListener("click", () => revealPaidHint(meta.id));
    $("#flag-form")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (state.session.ended) {
        endGame();
        return;
      }
      const flag = new FormData(e.target).get("flag");
      await submitFlag(meta.id, String(flag || "").trim());
    });

    clearInterval(renderChallenge._tick);
    renderChallenge._tick = setInterval(() => {
      if (shared.solved || !state.challengeStartedAt || state.session.ended) return;
      const t = Math.floor((Date.now() - state.challengeStartedAt) / 1000);
      const el = $("#chal-time");
      if (el) el.textContent = formatTime(t);
    }, 1000);
  }

  async function revealPaidHint(challengeId) {
    if (state.session.ended) {
      endGame();
      return;
    }
    try {
      const { data } = await api("/api/game/hint", {
        method: "POST",
        body: JSON.stringify({
          teamName: state.teamName,
          challengeId,
          hintIndex: 1,
        }),
      });
      const el = $("#hint-paid");
      if (el) el.textContent = data.hint;
      const btn = $("#reveal-hint");
      if (btn) btn.disabled = true;
      if (data.pointsDeducted) toast(`Hint revealed (−${data.pointsDeducted} pts on solve)`);
    } catch (err) {
      toast(err.message || "Could not reveal hint");
      if (err.data?.session?.ended) endGame();
    }
  }

  async function submitFlag(challengeId, flag) {
    const elapsed = Math.floor((Date.now() - (state.challengeStartedAt || Date.now())) / 1000);
    try {
      const { data } = await api("/api/game/submit-flag", {
        method: "POST",
        body: JSON.stringify({
          teamName: state.teamName,
          challengeId,
          flag,
          timeSeconds: elapsed,
        }),
      });
      if (!data.success) {
        toast(data.message || "Incorrect flag");
        return;
      }
      applySession(data.session);
      state.totalPoints += data.points_earned || 0;
      if (flag && !state.flagsFound.includes(flag)) state.flagsFound.push(flag);
      saveLocal();
      celebrate();
      toast(data.message || "Challenge complete!");

      $("#handoff-title").textContent =
        challengeId === 11 ? "Final boss complete" : `Challenge ${challengeId} complete`;
      $("#handoff-body").textContent =
        challengeId === 11
          ? "Great work. Check the scoreboard."
          : "Session timer is paused. Pass the device to the next team so they can register for the next challenge.";
      showView(challengeId === 11 ? "leaderboard" : "handoff");
      if (challengeId === 11) await renderLeaderboard();
    } catch (err) {
      toast(err.message || "Submit failed");
      if (err.data?.session?.ended) endGame();
    }
  }

  async function renderLeaderboard() {
    const { data } = await api("/api/game/leaderboard");
    applySession(data.session);
    const list = $("#leaderboard-list");
    list.innerHTML = "";
    data.teams.forEach((team, idx) => {
      const li = document.createElement("li");
      if (idx === 0) li.classList.add("rank-1");
      const members = (team.members || []).join(", ");
      li.innerHTML = `
        <span>${idx + 1}.</span>
        <span>${team.name}${members ? `<br><small class="muted">${members}</small>` : ""}${
          team.assigned_challenge ? `<br><small class="muted">Challenge ${team.assigned_challenge}</small>` : ""
        }</span>
        <span>${team.points} pts</span>
        <span>${formatTime(team.total_time_seconds || 0)}</span>
      `;
      list.appendChild(li);
    });
    if (!data.teams.length) {
      list.innerHTML = "<li><span></span><span>No teams yet</span><span></span><span></span></li>";
    }
    const stats = data.stats || {};
    $("#leaderboard-stats").innerHTML = `
      <div>Path progress: ${stats.challengesSolved || 0} / ${stats.challengesTotal || 10} challenges</div>
      <div>Fastest solve: ${
        stats.fastestSolve
          ? `${stats.fastestSolve.team} (${formatTime(stats.fastestSolve.seconds)})`
          : "—"
      }</div>
      <div>Most hints used: ${
        stats.mostHints ? `${stats.mostHints.team} (${stats.mostHints.hints} hints)` : "—"
      }</div>
      <div>Session time left: ${formatTime(state.session.remainingSeconds)}${
        state.session.ended ? " (ended)" : state.session.running ? " (running)" : " (paused)"
      }</div>
    `;
  }

  function openStudentsModal(teamName) {
    state.pendingTeamName = teamName;
    $("#students-team-label").textContent = teamName;
    const wrap = $("#student-fields");
    wrap.innerHTML = "";
    addStudentField("");
    $("#students-modal").classList.remove("hidden");
  }

  function closeStudentsModal() {
    $("#students-modal").classList.add("hidden");
  }

  function addStudentField(value = "") {
    const wrap = $("#student-fields");
    const row = document.createElement("div");
    row.className = "student-row";
    const input = document.createElement("input");
    input.type = "text";
    input.name = "student";
    input.placeholder = "Student name";
    input.maxLength = 60;
    input.value = value;
    input.autocomplete = "name";
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "btn btn-ghost btn-remove";
    remove.setAttribute("aria-label", "Remove");
    remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      if (wrap.children.length <= 1) {
        toast("Keep at least one student field");
        return;
      }
      row.remove();
    });
    row.appendChild(input);
    row.appendChild(remove);
    wrap.appendChild(row);
    input.focus();
  }

  async function finishRegistration(teamName, members) {
    if (!teamName) {
      toast("Team name missing. Go back and enter it again.");
      return;
    }
    const submitBtn = $("#students-form button[type='submit']");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Starting…";
    }
    try {
      const { data } = await api("/api/game/register", {
        method: "POST",
        body: JSON.stringify({ teamName, members }),
      });
      state.teamName = data.team.name;
      state.members = members;
      state.assignedChallenge = Number(
        data.assignedChallenge ?? data.team.assigned_challenge
      );
      if (!Number.isFinite(state.assignedChallenge) || state.assignedChallenge < 1) {
        state.assignedChallenge = null;
      }
      state.totalPoints = data.team.points || 0;
      state.rulesAccepted = true;
      applySession(data.session);
      saveLocal();
      closeStudentsModal();
      await ensureAssignment();
      showView("roadmap");
      renderRoadmap();
      toast(data.message || `Registered for challenge ${state.assignedChallenge}`);
      // Stay on roadmap — students click Start challenge themselves
    } catch (err) {
      console.error(err);
      toast(err.message || "Registration failed");
      if (err.data?.session?.ended) {
        closeStudentsModal();
        endGame();
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Continue to challenge";
      }
    }
  }

  function resetToNextTeam() {
    state.teamName = null;
    state.members = [];
    state.assignedChallenge = null;
    state.totalPoints = 0;
    state.challengeStartedAt = null;
    saveLocal();
    updateHud();
    showView("register");
    refreshAssignPreview();
  }

  async function refreshAssignPreview() {
    try {
      const session = await refreshSession();
      const el = $("#assign-preview");
      if (!el) return;
      if (session.ended) {
        el.textContent = "Session has ended.";
      } else if (session.nextChallenge == null) {
        el.textContent = "All challenges are complete.";
      } else if (session.nextChallenge === 11) {
        el.textContent = "Next up: Final boss.";
      } else {
        el.textContent = `Next open challenge on the shared path: Level ${session.nextChallenge}.`;
      }
    } catch {
      /* ignore */
    }
  }

  function bindActions() {
    $("#register-form").addEventListener("submit", (e) => {
      e.preventDefault();
      if (state.session.ended) {
        endGame();
        return;
      }
      const name = $("#team-input").value.trim();
      if (!name) return;
      openStudentsModal(name);
    });

    $("#add-student-btn").addEventListener("click", () => addStudentField(""));

    $("#students-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const inputs = [...$("#student-fields").querySelectorAll("input")];
      const members = inputs.map((i) => i.value.trim()).filter(Boolean);
      if (!members.length) {
        toast("Add at least one student name");
        return;
      }
      await finishRegistration(state.pendingTeamName, members);
    });

    document.body.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const action = btn.dataset.action;

      if (action === "accept-rules") {
        state.rulesAccepted = true;
        saveLocal();
        await refreshAssignPreview();
        showView("register");
      }
      if (action === "cancel-students") {
        closeStudentsModal();
      }
      if (action === "next-team") {
        resetToNextTeam();
      }
      if (action === "back-roadmap") {
        if (!state.session.ended) await pauseTimer();
        showView("roadmap");
        renderRoadmap();
      }
      if (action === "back-from-leaderboard") {
        if (state.session.ended) {
          showView("ended");
          return;
        }
        if (state.teamName) {
          showView("roadmap");
          renderRoadmap();
        } else {
          showView("register");
        }
      }
      if (action === "open-leaderboard") {
        await renderLeaderboard();
        showView("leaderboard");
      }
      if (action === "close-modal") closeModal();
      if (action === "hints-help") {
        openModal(
          "Scoring",
          `<ul>
            <li>Each challenge: <strong>15 pts</strong></li>
            <li>Free hint: no deduction</li>
            <li>Paid hint: <strong>−5 pts</strong> (10 pts on solve)</li>
            <li>Session clock: <strong>100 minutes</strong> total (pauses between challenges)</li>
          </ul>`
        );
      }
      if (action === "open-requests") {
        const meta = state.challengesMeta.map((c) => `${c.id}. ${c.endpoint}`);
        openModal(
          "Challenge endpoints",
          `<p>Point Postman / Burp at <code>http://127.0.0.1:5000</code></p>
           <pre>${meta.join("\n")}\n11. POST /api/ultimate-challenge</pre>`
        );
      }
      if (action === "full-reset") {
        if (
          !confirm(
            "Clear the whole session?\n\nThis resets the 100-minute timer, all teams, scores, and challenge progress. You will start from the rules page again."
          )
        ) {
          return;
        }
        try {
          await api("/api/game/restart", {
            method: "POST",
            body: JSON.stringify({ fullReset: true }),
          });
        } catch (err) {
          console.warn("reset API failed, clearing local state anyway", err);
        }
        stopPolling();
        clearLocal();
        toast("Session cleared. Starting over…");
        setTimeout(() => location.reload(), 400);
      }
    });

    $("#final-boss-card").addEventListener("click", async () => {
      if (state.session.ended) {
        endGame();
        return;
      }
      if (!allPathSolved()) {
        toast("Solve challenges 1–10 on the shared path first.");
        return;
      }
      if (state.assignedChallenge !== 11 && state.session.nextChallenge !== 11) {
        // Allow any registered team once path is clear
      }
      try {
        await resumeTimer();
      } catch (err) {
        toast(err.message);
        return;
      }
      openModal(
        "Final boss",
        `<p>Submit all 10 flags together via Postman, then paste the final flag:</p>
         <pre>POST /api/ultimate-challenge
{"flags": [ ...all 10 flags... ]}</pre>
         <form id="boss-form" class="flag-form">
           <input name="flag" placeholder="FLAG{Ult1m4te_...}" required />
           <button class="btn btn-primary" type="submit">Submit final flag</button>
         </form>`
      );
      $("#boss-form")?.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const flag = new FormData(ev.target).get("flag");
        // Ensure team is assigned to 11 for submit
        state.assignedChallenge = 11;
        await submitFlag(11, String(flag).trim());
        closeModal();
      });
    });
  }

  async function boot() {
    bindActions();
    startPolling();
    const { data } = await api("/api/challenges");
    state.challengesMeta = data.challenges;
    await refreshSession();

    if (state.session.ended) {
      showView("ended");
      return;
    }

    const saved = loadLocal();
    if (saved?.rulesAccepted && saved?.teamName) {
      state.rulesAccepted = true;
      state.teamName = saved.teamName;
      state.members = saved.members || [];
      state.assignedChallenge = saved.assignedChallenge;
      state.totalPoints = saved.totalPoints || 0;
      state.flagsFound = saved.flagsFound || [];
      try {
        const { data: st } = await api(`/api/game/state/${encodeURIComponent(state.teamName)}`);
        applySession(st.session);
        state.totalPoints = st.team.points;
        state.members = st.team.members || state.members;
        const rawAssigned = st.team.assigned_challenge ?? state.assignedChallenge;
        state.assignedChallenge =
          rawAssigned != null && Number(rawAssigned) >= 1 ? Number(rawAssigned) : null;
        await ensureAssignment();
        updateHud();
        renderRoadmap();
        showView("roadmap");
      } catch {
        clearLocal();
        showView("rules");
      }
    } else if (saved?.rulesAccepted) {
      state.rulesAccepted = true;
      showView("register");
      refreshAssignPreview();
    } else {
      showView("rules");
    }
  }

  boot().catch((err) => {
    console.error(err);
    toast("Failed to reach API. Is the server running on :5000?");
  });
})();

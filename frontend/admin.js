const Admin = {
  reports: {
    users: [],
    events: [],
    bugs: [],
  },
};

function adminToast(message) {
  const el = document.getElementById("adminToast");
  if (!el) return;
  el.textContent = message;
  el.hidden = false;
  clearTimeout(window.__adminToastTimer);
  window.__adminToastTimer = setTimeout(() => {
    el.hidden = true;
  }, 2500);
}

function escapeAdmin(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function adminStatusLabel(status) {
  const labels = {
    new: "Nowe",
    in_review: "Do obserwacji",
    resolved: "Rozwiązane",
    rejected: "Odrzucone",
    archived: "Archiwum",
    accepted: "Przyjęte",
    in_progress: "W trakcie",
    fixed: "Naprawione",
    not_reproducible: "Nie do odtworzenia",
  };
  return labels[String(status || "new")] || String(status || "new");
}

function adminStatusBadge(status) {
  const safe = escapeAdmin(status || "new");
  return `<span class="statusBadge" data-status="${safe}">${escapeAdmin(adminStatusLabel(status))}</span>`;
}

function setAdminCount(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = String(value || 0);
}

function adminEmpty(text) {
  return `<div class="adminEmpty">${escapeAdmin(text)}</div>`;
}


function adminNextReportStep(reportType, ticket, currentStatus) {
  const flows = {
    user: {
      new: "in_review",
      in_review: "resolved",
      resolved: "archived",
    },
    event: {
      new: "in_review",
      in_review: "resolved",
      resolved: "archived",
    },
    bug: {
      new: "accepted",
      accepted: "in_progress",
      in_progress: "fixed",
      fixed: "archived",
    },
  };

  const next = flows?.[reportType]?.[currentStatus];

  if (!next) {
    adminToast("Brak kolejnego kroku workflow.");
    return;
  }

  adminSetReportStatus(reportType, ticket, next);
}

function adminWorkflowButton(reportType, ticket, currentStatus) {
  const labels = {
    in_review: "Do obserwacji",
    resolved: "Rozwiąż",
    archived: "Archiwizuj",
    accepted: "Przyjmij",
    in_progress: "W trakcie",
    fixed: "Naprawione",
  };

  const flows = {
    user: {
      new: "in_review",
      in_review: "resolved",
      resolved: "archived",
    },
    event: {
      new: "in_review",
      in_review: "resolved",
      resolved: "archived",
    },
    bug: {
      new: "accepted",
      accepted: "in_progress",
      in_progress: "fixed",
      fixed: "archived",
    },
  };

  const next = flows?.[reportType]?.[currentStatus];

  if (!next) return "";

  return `
    <button
      class="tableAction"
      type="button"
      onclick="adminNextReportStep('${reportType}','${escapeAdmin(ticket)}','${escapeAdmin(currentStatus)}')"
    >
      ${labels[next] || "Dalej"}
    </button>
  `;
}


function renderUserReports(items) {
  const box = document.getElementById("adminUserReports");
  setAdminCount("adminUserCount", items.length);
  if (!box) return;
  if (!items.length) {
    box.innerHTML = adminEmpty("Brak zgłoszeń użytkowników.");
    return;
  }

  box.innerHTML = `
    <table class="adminTable">
      <thead>
        <tr>
          <th>Ticket</th>
          <th>Problem</th>
          <th>Użytkownik</th>
          <th>Status</th>
          <th>Data</th>
          <th>Akcje</th>
        </tr>
      </thead>
      <tbody>
        ${items.map((r) => `
          <tr>
            <td><strong>${escapeAdmin(r.ticket || "UR")}</strong></td>
            <td>${escapeAdmin(r.reason_label || r.reason || "Bez powodu")}</td>
            <td>user #${escapeAdmin(r.reported_user_id)}<br><span>zgł. #${escapeAdmin(r.reporter_user_id)}</span></td>
            <td>${adminStatusBadge(r.status || "new")}</td>
            <td>${escapeAdmin(r.created_at || "—")}</td>
            <td>
              <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <button class="tableAction" type="button" onclick="openUserPreview(\'${escapeAdmin(r.reported_user_id)}\', \'${escapeAdmin(r.ticket || "")}\', \'${escapeAdmin(r.status || "new")}\')">Podgląd</button>

              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderEventReports(items) {
  const box = document.getElementById("adminEventReports");
  setAdminCount("adminEventCount", items.length);
  if (!box) return;
  if (!items.length) {
    box.innerHTML = adminEmpty("Brak zgłoszeń wydarzeń.");
    return;
  }

  box.innerHTML = `
    <table class="adminTable">
      <thead>
        <tr>
          <th>Ticket</th>
          <th>Wydarzenie</th>
          <th>Problem</th>
          <th>Status</th>
          <th>Data</th>
          <th>Akcje</th>
        </tr>
      </thead>
      <tbody>
        ${items.map((r) => `
          <tr>
            <td><strong>${escapeAdmin(r.ticket || "ER")}</strong></td>
            <td>${escapeAdmin(r.event_title || "Wydarzenie")}<br><span>event #${escapeAdmin(r.event_id)}</span></td>
            <td>${escapeAdmin(r.reason_label || r.reason || "—")}</td>
            <td>${adminStatusBadge(r.status || "new")}</td>
            <td>${escapeAdmin(r.created_at || "—")}</td>
            <td>
              <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <button class="tableAction" type="button" onclick="openEventPreview(\'${escapeAdmin(r.event_id)}\', \'${escapeAdmin(r.ticket || "")}\', \'${escapeAdmin(r.status || "new")}\')">Podgląd</button>

              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderBugReports(items) {
  const box = document.getElementById("adminBugReports");
  setAdminCount("adminBugCount", items.length);
  if (!box) return;
  if (!items.length) {
    box.innerHTML = adminEmpty("Brak zgłoszeń błędów.");
    return;
  }

  box.innerHTML = `
    <table class="adminTable">
      <thead>
        <tr>
          <th>Ticket</th>
          <th>Widok</th>
          <th>Opis</th>
          <th>Status</th>
          <th>Data</th>
          <th>Akcje</th>
        </tr>
      </thead>
      <tbody>
        ${items.map((r) => `
          <tr>
            <td><strong>Bug #${escapeAdmin(r.ticket || r.id || "—")}</strong></td>
            <td>${escapeAdmin(r.current_view || "—")}<br><span>${escapeAdmin(r.role || "—")}</span></td>
            <td>${escapeAdmin(r.message || r.description || r.body || "Brak opisu.")}</td>
            <td>${adminStatusBadge(r.status || "new")}</td>
            <td>${escapeAdmin(r.created_at || r.createdAt || r.date || "—")}</td>
            <td>
              <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <button class="tableAction" type="button" onclick="openBugPreview('${escapeAdmin(r.ticket || r.id || "")}')">Podgląd</button>
                ${adminWorkflowButton("bug", r.ticket || r.id || "", r.status || "new")}
              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

async function reloadAdminReports() {
  const selectedStatus = document.getElementById("adminStatusFilter")?.value || "all";

  try {
    const [userRes, eventRes, bugRes] = await Promise.all([
      window.apiFetch("/admin/user-reports"),
      window.apiFetch("/admin/event-reports"),
      window.apiFetch("/admin/bug-reports"),
    ]);

    const filterItems = (items) => selectedStatus === "all"
      ? items
      : items.filter((r) => String(r.status || "new") === selectedStatus);

    Admin.reports.users = filterItems(Array.isArray(userRes?.data) ? userRes.data : []);
    Admin.reports.events = filterItems(Array.isArray(eventRes?.data) ? eventRes.data : []);
    Admin.reports.bugs = filterItems(Array.isArray(bugRes?.data) ? bugRes.data : []);

    renderUserReports(Admin.reports.users);
    renderEventReports(Admin.reports.events);
    renderBugReports(Admin.reports.bugs);
  } catch (e) {
    console.error("reloadAdminReports error", e);
    adminToast(e?.userMessage || "Nie udało się pobrać zgłoszeń.");
  }
}





async function adminSetReportStatus(reportType, ticket, status, extra = {}) {
  try {
    await window.apiFetch(`/admin/reports/${encodeURIComponent(reportType)}/${encodeURIComponent(ticket)}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status,
        moderator_note: extra.moderator_note || "",
        moderator_message: extra.moderator_message || "",
      }),
    });

    adminToast("Status zgłoszenia zapisany.");
    await reloadAdminReports();
  } catch (e) {
    console.error("adminSetReportStatus error", e);
    adminToast(e?.userMessage || "Nie udało się zapisać statusu zgłoszenia.");
  }
}


async function adminSendUserWarning(userId, reportTicket) {
  console.log("adminSendUserWarning clicked", { userId, reportTicket });
  try {
    const action = document.getElementById("userWarningAction")?.value || "warning_profile";

    const labels = {
      warning_profile: "Ostrzeżenie dotyczące profilu",
      warning_content: "Ostrzeżenie dotyczące treści",
      warning_behavior: "Ostrzeżenie dotyczące zachowania",
    };

    console.log("sending warning request", action);

    const res = await window.apiFetch(`/admin/reports/user/${encodeURIComponent(reportTicket)}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        label: labels[action] || action,
      }),
    });

    console.log("warning request success", res);

    adminToast("Ostrzeżenie zapisane.");
    await reloadAdminReports();
    openUserPreview(userId, reportTicket, "in_review");
  } catch (e) {
    console.error("adminSendUserWarning error", e);
    adminToast(e?.userMessage || "Nie udało się zapisać ostrzeżenia.");
  }
}

async function adminSetUserReportDecision(userId, reportTicket, status) {
  await adminSetReportStatus("user", reportTicket, status);
  await reloadAdminReports();
  openUserPreview(userId, reportTicket, status);
}

async function adminSetEventReportDecision(eventId, reportTicket, status) {
  await adminSetReportStatus("event", reportTicket, status);
  await reloadAdminReports();
  openEventPreview(eventId, reportTicket, status);
}

async function adminNotifyEventWatchers(eventId, reportTicket, reportStatus = "new") {
  try {
    await window.apiFetch(`/admin/events/${encodeURIComponent(eventId)}/notify-watchers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticket: reportTicket,
        type: "admin_event_under_review",
      }),
    });

    adminToast("Powiadomiono zapisanych i obserwujących.");
    await reloadAdminReports();
    openEventPreview(eventId, reportTicket, reportStatus);
  } catch (e) {
    console.error("adminNotifyEventWatchers error", e);
    adminToast(e?.userMessage || "Nie udało się wysłać powiadomienia.");
  }
}

async function adminSetEventStatus(eventId, status) {
  try {
    await window.apiFetch(`/admin/events/${encodeURIComponent(eventId)}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });

    adminToast(status === "archived" ? "Wydarzenie zarchiwizowane." : "Wydarzenie przywrócone.");
    await openEventPreview(eventId);
    await reloadAdminReports();
  } catch (e) {
    console.error("adminSetEventStatus error", e);
    adminToast(e?.userMessage || "Nie udało się zmienić statusu wydarzenia.");
  }
}

async function adminSetUserStatus(userId, status) {
  try {
    await window.apiFetch(`/admin/users/${userId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });

    adminToast(status === "blocked" ? "Użytkownik zablokowany." : "Użytkownik odblokowany.");

    await reloadAdminReports();
    await openUserPreview(userId);
  } catch (e) {
    console.error("adminSetUserStatus error", e);
    adminToast(e?.userMessage || "Nie udało się zmienić statusu użytkownika.");
  }
}


function openAdminDrawer(html) {
  const drawer = document.getElementById("adminDrawer");
  const content = document.getElementById("adminDrawerContent");

  if (!drawer || !content) return;

  content.innerHTML = html;
  drawer.removeAttribute("hidden");
}

function closeAdminDrawer() {
  document.getElementById("adminDrawer")?.setAttribute("hidden", "hidden");
}

document.getElementById("adminDrawerClose")?.addEventListener("click", closeAdminDrawer);
document.getElementById("adminDrawerBackdrop")?.addEventListener("click", closeAdminDrawer);


async function adminAddBugNote(ticket) {
  const note = document.getElementById("bugStandaloneNote")?.value || "";

  if (!String(note).trim()) {
    adminToast("Wpisz notatkę.");
    return;
  }

  try {
    await window.apiFetch(`/admin/reports/bug/${encodeURIComponent(ticket)}/note`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note }),
    });

    adminToast("Notatka dodana.");
    await reloadAdminReports();
    openBugPreview(ticket);
  } catch (e) {
    console.error("adminAddBugNote error", e);
    adminToast(e?.userMessage || "Nie udało się dodać notatki.");
  }
}

async function adminSubmitBugDecision(ticket, status = "accepted") {
  const moderatorNote = document.getElementById("bugModeratorNote")?.value || "";

  await adminSetReportStatus("bug", ticket, status, {
    moderator_note: moderatorNote,
  });

  await reloadAdminReports();
  openBugPreview(ticket);
}

function adminHistoryEntryLabel(h) {
  if (h.type === "note") return "Notatka admina";
  if (h.type === "warning") return "Ostrzeżenie wysłane";
  if (h.type === "notify_watchers") return "Powiadomienie zapisanych";
  if (String(h.to_status || "").toLowerCase() === "archived") return "Archiwum wewnętrzne";
  return "Zmiana statusu";
}

function renderAdminHistory(history, limit = null) {
  const items = Array.isArray(history) ? history.slice().reverse() : [];
  const visibleItems = Number.isInteger(limit) ? items.slice(0, limit) : items;

  if (!items.length) {
    return `<div class="adminHistoryCard">
      <div class="adminHistoryTitle">Brak historii moderacji</div>
      <div class="adminHistoryMeta">Decyzje i notatki adminów pojawią się tutaj po zapisaniu.</div>
    </div>`;
  }

  return visibleItems.map((h) => {
    const kind = adminHistoryEntryLabel(h);

    if (h.type === "note") {
      return `
        <div class="adminHistoryCard">
          <div class="adminHistoryKind">${escapeAdmin(kind)}</div>
          <div class="adminHistoryTitle">${escapeAdmin(h.note || "Notatka wewnętrzna")}</div>
          <div class="adminHistoryMeta">${escapeAdmin(h.at || "—")} · Admin #${escapeAdmin(h.admin_id || "—")}</div>
        </div>
      `;
    }

    if (h.type === "warning") {
      return `
        <div class="adminHistoryCard">
          <div class="adminHistoryKind">${escapeAdmin(kind)}</div>
          <div class="adminHistoryTitle">Wysłano ostrzeżenie do użytkownika</div>
          <div class="adminHistoryMeta"><strong>Typ ostrzeżenia:</strong> ${escapeAdmin(h.label || h.action || "—")}</div>
          <div class="adminHistoryMeta"><strong>Kod akcji:</strong> ${escapeAdmin(h.action || "—")}</div>
          <div class="adminHistoryMeta">${escapeAdmin(h.at || "—")} · Admin #${escapeAdmin(h.admin_id || "—")}</div>
        </div>
      `;
    }

    if (h.type === "notify_watchers") {
      return `
        <div class="adminHistoryCard">
          <div class="adminHistoryKind">${escapeAdmin(kind)}</div>
          <div class="adminHistoryTitle">Poinformowano zapisanych i obserwujących wydarzenie</div>
          <div class="adminHistoryMeta"><strong>Typ komunikatu:</strong> ${escapeAdmin(h.notification_type || "—")}</div>
          <div class="adminHistoryMeta"><strong>Liczba odbiorców:</strong> ${escapeAdmin(h.notified_count ?? "—")}</div>
          <div class="adminHistoryMeta">${escapeAdmin(h.at || "—")} · Admin #${escapeAdmin(h.admin_id || "—")}</div>
        </div>
      `;
    }

    return `
      <div class="adminHistoryCard">
        <div class="adminHistoryKind">${escapeAdmin(kind)}</div>
        <div class="adminHistoryTitle">${escapeAdmin(adminStatusLabel(h.from_status || "new"))} → ${escapeAdmin(adminStatusLabel(h.to_status || "new"))}</div>
        <div class="adminHistoryMeta">${escapeAdmin(h.at || "—")} · Admin #${escapeAdmin(h.admin_id || "—")}</div>
        ${h.moderator_note ? `<div class="adminHistoryMeta"><strong>Notatka:</strong> ${escapeAdmin(h.moderator_note)}</div>` : ""}
        ${h.moderator_message ? `<div class="adminHistoryMeta"><strong>Wiadomość:</strong> ${escapeAdmin(h.moderator_message)}</div>` : ""}
      </div>
    `;
  }).join("");
}

async function openUserReportHistory(userId, reportTicket, reportStatus = "new") {
  try {
    const res = await window.apiFetch(`/admin/users/${userId}/preview${reportTicket ? `?ticket=${encodeURIComponent(reportTicket)}` : ""}`);
    const u = res?.data || {};
    const history = u.selected_report?.history || [];

    openAdminDrawer(`
      <div class="adminPreviewActions">
        <button class="adminGhostAction" type="button" onclick="openUserPreview('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','${escapeAdmin(reportStatus)}')">
          ← Wróć do podglądu użytkownika
        </button>
      </div>

      <div class="adminPreviewCard">
        <div class="adminHistoryHeader">
          <h3>Pełna historia moderacji</h3>
          <span class="adminHistoryCount">${escapeAdmin(history.length)} wpisów</span>
        </div>
        ${renderAdminHistory(history)}
      </div>
    `);
  } catch (e) {
    console.error("openUserReportHistory error", e);
    adminToast("Nie udało się pobrać historii moderacji.");
  }
}

async function openEventReportHistory(eventId, reportTicket, reportStatus = "new") {
  try {
    const res = await window.apiFetch(`/admin/events/${eventId}/preview${reportTicket ? `?ticket=${encodeURIComponent(reportTicket)}` : ""}`);
    const ev = res?.data || {};
    const history = ev.selected_report?.history || [];

    openAdminDrawer(`
      <div class="adminPreviewActions">
        <button class="adminGhostAction" type="button" onclick="openEventPreview('${escapeAdmin(eventId)}','${escapeAdmin(reportTicket)}','${escapeAdmin(reportStatus)}')">
          ← Wróć do podglądu wydarzenia
        </button>
      </div>

      <div class="adminPreviewCard">
        <div class="adminHistoryHeader">
          <h3>Pełna historia zgłoszenia wydarzenia</h3>
          <span class="adminHistoryCount">${escapeAdmin(history.length)} wpisów</span>
        </div>
        ${renderAdminHistory(history)}
      </div>
    `);
  } catch (e) {
    console.error("openEventReportHistory error", e);
    adminToast("Nie udało się pobrać historii zgłoszenia wydarzenia.");
  }
}

async function openBugReporterContext(ticket) {
  try {
    const res = await window.apiFetch(`/admin/bug-reports/${encodeURIComponent(ticket)}/reporter-context`);
    const ctx = res?.data || {};

    openAdminDrawer(`
      <div class="adminPreviewActions">
        <button class="adminGhostAction" type="button" onclick="openBugPreview('${escapeAdmin(ticket)}')">
          ← Wróć do zgłoszenia
        </button>
      </div>

      <div class="adminUserHero">
        <div class="adminUserHeroLeft">
          ${
            ctx.profile?.avatar_url
              ? `<img class="adminUserAvatar" src="${String(ctx.profile.avatar_url).startsWith("http") ? ctx.profile.avatar_url : `${window.API_BASE_URL}${ctx.profile.avatar_url}`}" alt="${escapeAdmin(ctx.profile?.nick || "Użytkownik")}" />`
              : `<div class="adminUserAvatar adminUserAvatarFallback">U</div>`
          }

          <div>
            <div class="adminUserName">${escapeAdmin(ctx.profile?.nick || ctx.user?.email || "Użytkownik")}</div>
            <div class="adminUserEmail">${escapeAdmin(ctx.user?.email || "—")} · #${escapeAdmin(ctx.user?.id || "—")}</div>
            <div class="adminUserMetaRow">
              <span class="adminUserRole">${escapeAdmin(ctx.user?.role || "—")}</span>
              ${adminStatusBadge(ctx.user?.status || "—")}
            </div>
          </div>
        </div>
      </div>

      <div class="adminPreviewCard">
        <h3>Kontekst zgłaszającego</h3>

        <div class="adminInfoList">
          <div><span>ID użytkownika</span><strong>${escapeAdmin(ctx.user?.id || "—")}</strong></div>
          <div><span>Email</span><strong>${escapeAdmin(ctx.user?.email || "—")}</strong></div>
          <div><span>Nick</span><strong>${escapeAdmin(ctx.profile?.nick || "—")}</strong></div>
          <div><span>Lokalizacja profilu</span><strong>${escapeAdmin(ctx.profile?.city || "—")}</strong></div>
          <div><span>Ostatnie współrzędne</span><strong>${escapeAdmin(ctx.profile?.location_lat ?? "—")}, ${escapeAdmin(ctx.profile?.location_lng ?? "—")}</strong></div>
          <div><span>Status</span><strong>${escapeAdmin(ctx.user?.status || "—")}</strong></div>
        </div>
      </div>

      <div class="adminPreviewCard">
        <h3>Audit log</h3>

        ${
          Array.isArray(ctx.audit_logs) && ctx.audit_logs.length
            ? ctx.audit_logs.map((log) => `
                <div class="adminHistoryCard">
                  <div class="adminHistoryTitle">${escapeAdmin(log.action || "—")}</div>
                  <div class="adminHistoryMeta">${escapeAdmin(log.created_at || "—")}</div>
                  <div class="adminHistoryMeta">${escapeAdmin(log.details || "—")}</div>
                </div>
              `).join("")
            : `<div class="adminEmpty">Brak audit logów.</div>`
        }
      </div>
    `);
  } catch (e) {
    console.error("openBugReporterContext error", e);
    adminToast("Nie udało się pobrać kontekstu zgłaszającego.");
  }
}

function openBugPreview(ticket) {
  const bug = (Admin.reports.bugs || []).find((r) => String(r.ticket || r.id || "") === String(ticket || ""));

  if (!bug) {
    adminToast("Nie znaleziono zgłoszenia błędu.");
    return;
  }

  openAdminDrawer(`
    <div class="adminUserHero">
      <div class="adminUserHeroLeft">
        <div class="adminUserAvatar adminUserAvatarFallback">B</div>

        <div>
          <div class="adminUserName">Bug #${escapeAdmin(bug.ticket || bug.id || "—")}</div>
          <div class="adminUserEmail">${escapeAdmin(bug.current_view || "Nieznany widok")} · ${escapeAdmin(bug.role || "—")}</div>

          <div class="adminUserMetaRow">
            ${adminStatusBadge(bug.status || "new")}
            <span class="adminUserRole">bug report</span>
          </div>

          <div class="adminPreviewActions">
            <button class="adminGhostAction" type="button" onclick="openBugReporterContext('${escapeAdmin(bug.ticket || bug.id || "")}')">
              Kontekst zgłaszającego
            </button>
          </div>
        </div>
      </div>

      <div class="adminUserQuickStats">
        <div class="adminQuickStat">
          <span>Status</span>
          <strong>${escapeAdmin(adminStatusLabel(bug.status || "new"))}</strong>
        </div>
        <div class="adminQuickStat">
          <span>Data</span>
          <strong>${escapeAdmin(bug.created_at || bug.createdAt || bug.date || "—")}</strong>
        </div>
      </div>
    </div>

    <div class="adminPreviewGrid">
      <div class="adminPreviewCard">
        <h3>Szczegóły błędu</h3>
        <div class="adminInfoList">
          <div><span>Ticket</span><strong>${escapeAdmin(bug.ticket || bug.id || "—")}</strong></div>
          <div><span>Widok</span><strong>${escapeAdmin(bug.current_view || "—")}</strong></div>
          <div><span>Rola</span><strong>${escapeAdmin(bug.role || "—")}</strong></div>
          <div><span>Użytkownik</span><strong>${escapeAdmin(bug.user_email || bug.email || bug.user_id || "—")}</strong></div>
        </div>
      </div>

      <div class="adminPreviewCard">
        <h3>Decyzja moderatora</h3>

        <div class="adminModerationBox">
          ${
            String(bug.status || "new") === "archived"
              ? `<div class="adminDecisionGrid">
                  <button class="adminDecisionButton adminDecisionPositive" type="button" onclick="adminSubmitBugDecision('${escapeAdmin(bug.ticket || bug.id || "")}','accepted')">
                    <strong>Przywróć do obsługi</strong>
                    <span>Zgłoszenie wróci na listę aktywnych spraw.</span>
                  </button>
                </div>`
              : `<div class="adminDecisionGrid">
                  <button class="adminDecisionButton ${String(bug.status || "new") === "accepted" ? "adminDecisionCurrent" : ""}" type="button" ${String(bug.status || "new") === "accepted" ? "disabled" : `onclick="adminSubmitBugDecision('${escapeAdmin(bug.ticket || bug.id || "")}','accepted')"`}>
                    <strong>${String(bug.status || "new") === "accepted" ? "Aktualnie: przyjęte" : "Przyjmij"}</strong>
                    <span>Zgłoszenie przyjęte do obsługi.</span>
                  </button>

                  <button class="adminDecisionButton ${String(bug.status || "new") === "in_progress" ? "adminDecisionCurrent" : ""}" type="button" ${String(bug.status || "new") === "in_progress" ? "disabled" : `onclick="adminSubmitBugDecision('${escapeAdmin(bug.ticket || bug.id || "")}','in_progress')"`}>
                    <strong>${String(bug.status || "new") === "in_progress" ? "Aktualnie: w trakcie" : "W trakcie"}</strong>
                    <span>Problem jest analizowany.</span>
                  </button>

                  <button class="adminDecisionButton adminDecisionPositive ${String(bug.status || "new") === "resolved" ? "adminDecisionCurrent" : ""}" type="button" ${String(bug.status || "new") === "resolved" ? "disabled" : `onclick="adminSubmitBugDecision('${escapeAdmin(bug.ticket || bug.id || "")}','resolved')"`}>
                    <strong>${String(bug.status || "new") === "resolved" ? "Aktualnie: rozwiązane" : "Rozwiązane"}</strong>
                    <span>Zamknij zgłoszenie jako rozwiązane.</span>
                  </button>

                  <button class="adminDecisionButton ${String(bug.status || "new") === "not_reproducible" ? "adminDecisionCurrent" : ""}" type="button" ${String(bug.status || "new") === "not_reproducible" ? "disabled" : `onclick="adminSubmitBugDecision('${escapeAdmin(bug.ticket || bug.id || "")}','not_reproducible')"`}>
                    <strong>${String(bug.status || "new") === "not_reproducible" ? "Aktualnie: nie odtworzono" : "Nie odtworzono"}</strong>
                    <span>Nie udało się potwierdzić błędu.</span>
                  </button>

                  <button class="adminDecisionButton adminDecisionMuted" type="button" onclick="adminSubmitBugDecision('${escapeAdmin(bug.ticket || bug.id || "")}','archived')">
                    <strong>Archiwizuj</strong>
                    <span>Schowaj bez dalszej obsługi.</span>
                  </button>
                </div>`
          }

          <div class="adminSystemHint">
            Powiadomienie do zgłaszającego będzie wysyłane automatycznie według wybranego statusu.
          </div>
        </div>
      </div>
    </div>

    <div class="adminPreviewCard">
      <h3>Opis zgłoszenia</h3>
      <div class="adminBio">${escapeAdmin(bug.message || bug.description || bug.body || "Brak opisu.")}</div>
    </div>

    <div class="adminPreviewCard">
      <h3>Dodaj notatkę wewnętrzną</h3>
      <textarea class="adminFieldTextarea" id="bugStandaloneNote" rows="3" placeholder="Widoczne tylko dla adminów/supportu. Nie zmienia statusu zgłoszenia."></textarea>
      <div class="adminPreviewActions">
        <button class="adminPrimaryAction" type="button" onclick="adminAddBugNote('${escapeAdmin(bug.ticket || bug.id || "")}')">
          Dodaj notatkę
        </button>
      </div>
    </div>

    <div class="adminPreviewCard">
      <h3>Historia / notatki adminów</h3>
      ${renderAdminHistory(bug.history)}
    </div>
  `);
}

async function openEventPreview(eventId, reportTicket = "", reportStatus = "new") {
  try {
    const res = await window.apiFetch(`/admin/events/${eventId}/preview${reportTicket ? `?ticket=${encodeURIComponent(reportTicket)}` : ""}`);
    const ev = res?.data || {};

    openAdminDrawer(`
      <div class="adminUserHero">
        <div class="adminUserHeroLeft">
          ${
            ev.organizer_logo_url
              ? `<img class="adminUserAvatar" src="${String(ev.organizer_logo_url).startsWith("http") ? ev.organizer_logo_url : `${window.API_BASE_URL}${ev.organizer_logo_url}`}" alt="${escapeAdmin(ev.organizer_name || "Organizator")}" />`
              : ev.event_cover_url
                ? `<img class="adminUserAvatar" src="${String(ev.event_cover_url).startsWith("http") ? ev.event_cover_url : `${window.API_BASE_URL}${ev.event_cover_url}`}" alt="${escapeAdmin(ev.title || "Event")}" />`
                : `<div class="adminUserAvatar adminUserAvatarFallback">E</div>`
          }

          <div>
            <div class="adminUserName">${escapeAdmin(ev.title || "Wydarzenie")}</div>
            <div class="adminUserEmail">${escapeAdmin(ev.organizer_name || "Organizator")} · ${escapeAdmin(ev.organizer_email || "—")} · #${escapeAdmin(ev.partner_user_id || "—")}</div>

            <div class="adminUserMetaRow">
              ${adminStatusBadge(ev.status || "—")}
              <span class="adminUserRole">${escapeAdmin(ev.interest_tag || "event")}</span>
            </div>
          </div>
        </div>

        <div class="adminUserQuickStats">
          <div class="adminQuickStat">
            <strong>${escapeAdmin(ev.reports_total || 0)}</strong>
            <span>Zgłoszeń</span>
          </div>

          <div class="adminQuickStat">
            <strong>${escapeAdmin(ev.signups_count || 0)}</strong>
            <span>Zapisani</span>
          </div>
        </div>
      </div>

      <div class="adminPreviewGrid">
        <div class="adminPreviewCard">
          <h3>Dane wydarzenia</h3>

          <div class="adminInfoList">
            <div><span>Miasto</span><strong>${escapeAdmin(ev.city || "—")}</strong></div>
            <div><span>Miejsce</span><strong>${escapeAdmin(ev.where || "—")}</strong></div>
            <div><span>Start</span><strong>${escapeAdmin(ev.start_at || "—")}</strong></div>
            <div><span>Koniec</span><strong>${escapeAdmin(ev.end_at || "—")}</strong></div>
          </div>
        </div>

        <div class="adminPreviewCard">
          <h3>Statystyki</h3>

          <div class="adminInfoList">
            <div><span>Otwarte zgłoszenia</span><strong>${escapeAdmin(ev.reports_open || 0)}</strong></div>
            <div><span>Obserwujący</span><strong>${escapeAdmin(ev.saves_count || 0)}</strong></div>
            <div><span>Limit miejsc</span><strong>${escapeAdmin(ev.capacity || "—")}</strong></div>
            <div><span>Status</span><strong>${escapeAdmin(ev.status || "—")}</strong></div>
          </div>
        </div>
      </div>

      <div class="adminPreviewCard">
        <h3>Opis wydarzenia</h3>
        <div class="adminBio">${escapeAdmin(ev.description || "Brak opisu wydarzenia.")}</div>
      </div>

      <div class="adminPreviewBottomGrid">
        <div class="adminPreviewCard">
          <h3>Akcje wydarzenia</h3>

          <div class="adminActionStack">
            <button class="${String(ev.status || "").toLowerCase() === "archived" ? "adminPrimaryAction" : "adminDangerAction"}" type="button" onclick="adminSetEventStatus('${escapeAdmin(ev.id)}','${String(ev.status || "").toLowerCase() === "archived" ? "published" : "archived"}')">
              ${String(ev.status || "").toLowerCase() === "archived" ? "Przywróć wydarzenie" : "Zarchiwizuj wydarzenie"}
            </button>

            <button class="adminPrimaryAction" type="button" onclick="adminNotifyEventWatchers('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','${escapeAdmin(reportStatus)}')">
              Powiadom zapisanych
            </button>
          </div>

          <div class="adminSystemHint">
            Archiwizacja wydarzenia dotyczy samego wydarzenia. Powiadomienie zapisanych zostaje osobną akcją.
          </div>

          ${
            reportTicket
              ? `<div class="adminSectionDivider"></div><h3>Decyzja zgłoszenia</h3>`
              : ""
          }

          ${
            reportTicket
              ? String(reportStatus || "new") === "archived"
                ? `<div class="adminDecisionGrid">
                    <button class="adminDecisionButton" type="button" onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','in_review')">
                      <strong>Przywróć do sprawdzenia</strong>
                      <span>Zgłoszenie wróci do aktywnej obsługi.</span>
                    </button>
                  </div>`
                : `<div class="adminDecisionGrid">
                    <button class="adminDecisionButton ${String(reportStatus || "new") === "in_review" ? "adminDecisionCurrent" : ""}" type="button" ${String(reportStatus || "new") === "in_review" ? "disabled" : `onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','in_review')"`}>
                      <strong>${String(reportStatus || "new") === "in_review" ? "Aktualnie: sprawdzamy" : "Sprawdzamy"}</strong>
                      <span>Zgłoszenie wydarzenia jest analizowane.</span>
                    </button>
                    <button class="adminDecisionButton ${String(reportStatus || "new") === "resolved" ? "adminDecisionCurrent" : ""}" type="button" ${String(reportStatus || "new") === "resolved" ? "disabled" : `onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','resolved')"`}>
                      <strong>${String(reportStatus || "new") === "resolved" ? "Aktualnie: zasadne" : "Zasadne / rozwiązane"}</strong>
                      <span>Zgłoszenie potwierdzone. Wydarzenie można zarchiwizować osobną akcją wyżej.</span>
                    </button>
                    <button class="adminDecisionButton ${String(reportStatus || "new") === "rejected" ? "adminDecisionCurrent" : ""}" type="button" ${String(reportStatus || "new") === "rejected" ? "disabled" : `onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','rejected')"`}>
                      <strong>${String(reportStatus || "new") === "rejected" ? "Aktualnie: odrzucone" : "Odrzuć"}</strong>
                      <span>Brak podstaw do działania.</span>
                    </button>
                    <button class="adminDecisionButton adminDecisionMuted" type="button" onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','archived')">
                      <strong>Archiwum</strong>
                      <span>Tylko porządkowanie wewnętrzne.</span>
                    </button>
                  </div>`
              : ""
          }
        </div>

        <div class="adminPreviewCard">
          <div class="adminHistoryHeader">
            <h3>Historia zgłoszenia</h3>
            ${
              reportTicket
                ? `<button class="adminGhostMiniButton" type="button" onclick="openEventReportHistory('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','${escapeAdmin(reportStatus)}')">Zobacz wszystko</button>`
                : ""
            }
          </div>

          ${
            reportTicket
              ? renderAdminHistory(ev.selected_report?.history, 5)
              : `<div class="adminHistoryCard">
                  <div class="adminHistoryTitle">Zgłoszenia wydarzenia</div>
                  <div class="adminHistoryMeta">Łącznie: ${escapeAdmin(ev.reports_total || 0)}</div>
                  <div class="adminHistoryMeta">Otwarte: ${escapeAdmin(ev.reports_open || 0)}</div>
                </div>`
          }
        </div>
      </div>
    `);
  } catch (e) {
    console.error("openEventPreview error", e);
    adminToast("Nie udało się pobrać podglądu wydarzenia.");
  }
}


async function openUserPreview(userId, reportTicket = '', reportStatus = 'new') {
  try {
    const res = await window.apiFetch(`/admin/users/${userId}/preview${reportTicket ? `?ticket=${encodeURIComponent(reportTicket)}` : ""}`);
    const u = res?.data || {};

    openAdminDrawer(`
  <div class="adminUserHero">
    <div class="adminUserHeroLeft">
      ${
        u.avatar_url
          ? `<img class="adminUserAvatar" src="${String(u.avatar_url).startsWith("http") ? u.avatar_url : `${window.API_BASE_URL}${u.avatar_url}`}" alt="${escapeAdmin(u.nick || "User")}" />`
          : `<div class="adminUserAvatar adminUserAvatarFallback">${escapeAdmin((u.nick || "U").charAt(0).toUpperCase())}</div>`
      }

      <div>
        <div class="adminUserName">${escapeAdmin(u.nick || "Użytkownik")}</div>
        <div class="adminUserEmail">${escapeAdmin(u.email || "—")}</div>

        <div class="adminUserMetaRow">
          ${adminStatusBadge(u.status || "active")}
          <span class="adminUserRole">${escapeAdmin(u.role || "user")}</span>
        </div>
      </div>
    </div>

    <div class="adminUserQuickStats">
      <div class="adminQuickStat">
        <strong>${escapeAdmin(u.reports_total || 0)}</strong>
        <span>Zgłoszeń</span>
      </div>

      <div class="adminQuickStat">
        <strong>${escapeAdmin(u.reports_open || 0)}</strong>
        <span>Otwarte</span>
      </div>
    </div>
  </div>

  <div class="adminPreviewGrid">
    <div class="adminPreviewCard">
      <h3>Dane konta</h3>

      <div class="adminInfoList">
        <div>
          <span>Ostatnia lokalizacja</span>
          <strong>${escapeAdmin(u.city || "Brak danych")}</strong>
        </div>

        <div>
          <span>Data urodzenia</span>
          <strong>${escapeAdmin(u.dob || "—")}</strong>
        </div>

        <div>
          <span>Utworzono</span>
          <strong>${escapeAdmin(u.created_at || "—")}</strong>
        </div>
      </div>
    </div>

    <div class="adminPreviewCard">
      <h3>Zainteresowania</h3>

      <div class="adminTags">
        ${(u.interests || []).map(tag => `<span>${escapeAdmin(tag)}</span>`).join("") || "<span>Brak</span>"}
      </div>
    </div>
  </div>

  <div class="adminPreviewCard">
    <h3>Bio</h3>

    <div class="adminBio">
      ${escapeAdmin(u.bio || "Brak bio użytkownika.")}
    </div>
  </div>

  <div class="adminPreviewBottomGrid">

    <div class="adminPreviewCard">
      <h3>Szybkie akcje</h3>

      <div class="adminActionStack">
        ${String(u.status || "active") === "blocked"
          ? `<button class="adminPrimaryAction" type="button" onclick="adminSetUserStatus('${escapeAdmin(u.id)}','active')">Odblokuj użytkownika</button>`
          : `<button class="adminDangerAction" type="button" onclick="adminSetUserStatus('${escapeAdmin(u.id)}','blocked')">Zablokuj użytkownika</button>`
        }

        ${
          reportTicket
            ? `<div class="adminWarnBox">
                <label class="adminFieldLabel" for="userWarningAction">Ostrzeżenie dla użytkownika</label>
                <select class="adminFieldInput" id="userWarningAction">
                  <option value="warning_profile">Profil narusza zasady</option>
                  <option value="warning_content">Treść narusza zasady</option>
                  <option value="warning_behavior">Zachowanie narusza zasady</option>
                </select>
                <button class="adminPrimaryAction" type="button" onclick="adminSendUserWarning('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}')">
                  Wyślij ostrzeżenie
                </button>
                <div class="adminWarnHint">Ostrzeżenie zapisze się w historii moderacji. Powiadomienie in-app dodamy w kolejnym etapie.</div>
              </div>`
            : ""
        }
      </div>

      ${
        reportTicket
          ? `<div class="adminSectionDivider"></div><h3>Decyzja zgłoszenia</h3>`
          : ""
      }

      ${
        reportTicket
          ? String(reportStatus || "new") === "archived"
            ? `<div class="adminDecisionGrid">
                <button class="adminDecisionButton" type="button" onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','in_review')">
                  <strong>Przywróć do sprawdzenia</strong>
                  <span>Zgłoszenie wróci do aktywnej obsługi.</span>
                </button>
              </div>`
            : `<div class="adminDecisionGrid">
                <button class="adminDecisionButton ${String(reportStatus || "new") === "in_review" ? "adminDecisionCurrent" : ""}" type="button" ${String(reportStatus || "new") === "in_review" ? "disabled" : `onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','in_review')"`}>
                  <strong>${String(reportStatus || "new") === "in_review" ? "Aktualnie: sprawdzamy" : "Sprawdzamy"}</strong>
                  <span>Zgłoszenie jest analizowane.</span>
                </button>
                <button class="adminDecisionButton ${String(reportStatus || "new") === "resolved" ? "adminDecisionCurrent" : ""}" type="button" ${String(reportStatus || "new") === "resolved" ? "disabled" : `onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','resolved')"`}>
                  <strong>${String(reportStatus || "new") === "resolved" ? "Aktualnie: zasadne" : "Zasadne"}</strong>
                  <span>Zgłoszenie potwierdzone i rozwiązane.</span>
                </button>
                <button class="adminDecisionButton ${String(reportStatus || "new") === "rejected" ? "adminDecisionCurrent" : ""}" type="button" ${String(reportStatus || "new") === "rejected" ? "disabled" : `onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','rejected')"`}>
                  <strong>${String(reportStatus || "new") === "rejected" ? "Aktualnie: odrzucone" : "Odrzuć"}</strong>
                  <span>Brak podstaw do działania.</span>
                </button>
                <button class="adminDecisionButton adminDecisionMuted" type="button" onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','archived')">
                  <strong>Archiwum</strong>
                  <span>Tylko porządkowanie wewnętrzne.</span>
                </button>
              </div>`
          : ""
      }

      <div class="adminSystemHint">
        Wszystkie akcje administratora będą zapisywane w logach systemowych.
      </div>
    </div>

    <div class="adminPreviewCard">
      <div class="adminHistoryHeader">
        <h3>Historia zgłoszeń</h3>

        <button class="adminGhostMiniButton" type="button" onclick="openUserReportHistory('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','${escapeAdmin(reportStatus)}')">
          Zobacz wszystko
        </button>
      </div>

      ${renderAdminHistory(u.selected_report?.history, 5)}
    </div>

  </div>

  <div class="adminPreviewCard">
    <h3>Informacje systemowe</h3>

    <div class="adminInfoList">
      <div>
        <span>ID użytkownika</span>
        <strong>${escapeAdmin(u.id || "—")}</strong>
      </div>

      <div>
        <span>Rola</span>
        <strong>${escapeAdmin(u.role || "—")}</strong>
      </div>

      <div>
        <span>Status konta</span>
        <strong>${escapeAdmin(u.status || "—")}</strong>
      </div>
    </div>
  </div>
`);

  } catch (e) {
    console.error("openUserPreview error", e);
    adminToast("Nie udało się pobrać podglądu użytkownika.");
  }
}


document.getElementById("adminRefreshBtn")?.addEventListener("click", reloadAdminReports);
document.getElementById("adminStatusFilter")?.addEventListener("change", reloadAdminReports);

document.getElementById("adminLogoutBtn")?.addEventListener("click", () => {
  localStorage.removeItem("usly_token");
  adminToast("Wylogowano lokalnie.");
});


async function adminLogin(email, password) {
  const res = await window.apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, expected_role: "admin" }),
  });

  if (!res?.success || !res?.data?.access_token) {
    throw new Error("LOGIN_FAILED");
  }

  localStorage.setItem("usly_token", res.data.access_token);
  document.getElementById("adminLoginView")?.setAttribute("hidden", "hidden");
  document.getElementById("adminDashboardView")?.removeAttribute("hidden");

  adminToast("Zalogowano do panelu administratora.");
  await reloadAdminReports();
}

document.getElementById("adminLoginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("adminLoginEmail")?.value?.trim();
  const password = document.getElementById("adminLoginPassword")?.value || "";

  try {
    await adminLogin(email, password);
  } catch (err) {
    console.error("admin login error", err);
    adminToast(err?.userMessage || "Nie udało się zalogować.");
  }
});

(function restoreAdminSession(){
  const token = localStorage.getItem("usly_token");
  if (!token) return;

  document.getElementById("adminLoginView")?.setAttribute("hidden", "hidden");
  document.getElementById("adminDashboardView")?.removeAttribute("hidden");

  reloadAdminReports().catch(() => {});
})();


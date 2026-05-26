const Admin = {
  reports: {
    users: [],
    events: [],
    bugs: [],
  },
  users: [],
  events: [],
  me: null,
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

function adminLevel() {
  return String(Admin.me?.admin_level || "owner").toLowerCase();
}

function adminCanView(view) {
  const level = adminLevel();
  if (level === "owner") return true;
  if (level === "operations") return ["reports", "users", "events"].includes(view);
  if (level === "moderation" || level === "support") return view === "reports";
  return view === "reports";
}

function adminCanFinalizeReportDecision() {
  const level = adminLevel();
  return level === "owner" || level === "operations";
}

function adminCanManageUsers() {
  const level = adminLevel();
  return level === "owner" || level === "operations";
}

function adminCanManageEvents() {
  const level = adminLevel();
  return level === "owner" || level === "operations";
}

function adminCanDeleteAccounts() {
  return adminLevel() === "owner";
}

function defaultAdminView() {
  return adminCanView("dashboard") ? "dashboard" : "reports";
}

function refreshAdminNavAccess() {
  document.querySelectorAll("[data-admin-view]").forEach((btn) => {
    const view = btn.dataset.adminView || "reports";
    const allowed = adminCanView(view);
    btn.disabled = !allowed;
    btn.classList.toggle("adminNavDisabled", !allowed);
    btn.title = allowed ? "" : "Brak dostępu na tym poziomie admina";
  });
}

function renderAdminActor() {
  const el = document.getElementById("adminCurrentActor");
  if (!el) return;
  const me = Admin.me || {};
  const name = me.admin_display_name || me.email || "Admin";
  const level = me.admin_level || me.role || "admin";
  el.textContent = `${name} · ${level}`;
  refreshAdminNavAccess();
}

async function loadCurrentAdmin() {
  try {
    const res = await apiFetch("/auth/me");
    Admin.me = res?.data || res || null;
    renderAdminActor();
  } catch (e) {
    console.error("loadCurrentAdmin error", e);
    Admin.me = null;
    renderAdminActor();
  }
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
    pending_owner_approval: "Do akceptacji ownera",
    resolved: "Rozwiązane",
    rejected: "Odrzucone",
    archived: "Archiwum",
    accepted: "Przyjęte",
    in_progress: "W trakcie",
    fixed: "Naprawione",
    not_reproducible: "Nie do odtworzenia",
    active: "Aktywne",
    blocked: "Zablokowane",
    deleted: "Usunięte",
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

function renderAdminEvents(items) {
  const box = document.getElementById("adminEventsList");
  setAdminCount("adminEventsCount", items.length);

  if (!box) return;

  if (!items.length) {
    box.innerHTML = adminEmpty("Brak wydarzeń.");
    return;
  }

  box.innerHTML = `
    <table class="adminTable">
      <thead>
        <tr>
          <th>ID</th>
          <th>Wydarzenie</th>
          <th>Organizator</th>
          <th>Status</th>
          <th>Termin</th>
          <th>Miasto</th>
          <th>Zapisani</th>
          <th>Obserwujący</th>
          <th>Akcje</th>
        </tr>
      </thead>
      <tbody>
        ${items.map((ev) => `
          <tr>
            <td><strong>#${escapeAdmin(ev.id)}</strong></td>
            <td>${escapeAdmin(ev.title || "Wydarzenie")}<br><span>${escapeAdmin(ev.interest_tag || "—")}</span></td>
            <td>${escapeAdmin(ev.organizer_name || "—")}<br><span>${escapeAdmin(ev.organizer_email || "—")}</span></td>
            <td>${adminStatusBadge(ev.status || "draft")}</td>
            <td>${escapeAdmin(ev.start_at || "—")}</td>
            <td>${escapeAdmin([ev.city, ev.where].filter(Boolean).join(", ") || "—")}</td>
            <td>${escapeAdmin(ev.signups_count || 0)} / ${escapeAdmin(ev.capacity || "∞")}</td>
            <td>${escapeAdmin(ev.saves_count || 0)}</td>
            <td>
              <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <button class="tableAction" type="button" onclick="openEventPreview('${escapeAdmin(ev.id)}')">Podgląd</button>
              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

async function reloadAdminEvents() {
  try {
    const res = await window.apiFetch("/admin/events");
    const items = Array.isArray(res?.data?.items) ? res.data.items : [];
    const query = String(document.getElementById("adminEventSearch")?.value || "").trim().toLowerCase();
    const statusFilter = String(document.getElementById("adminEventsStatusFilter")?.value || "all");

    Admin.events = items;

    const filtered = items.filter((ev) => {
      const haystack = [
        ev.id,
        ev.title,
        ev.organizer_name,
        ev.organizer_email,
        ev.city,
        ev.where,
        ev.interest_tag,
        ev.status,
      ].map(v => String(v || "").toLowerCase()).join(" ");

      if (query && !haystack.includes(query)) return false;
      if (statusFilter !== "all" && String(ev.status || "") !== statusFilter) return false;

      return true;
    });

    renderAdminEvents(filtered);
  } catch (e) {
    console.error("reloadAdminEvents error", e);
    adminToast(e?.userMessage || "Nie udało się pobrać wydarzeń.");
  }
}

function renderAdminUsers(items) {
  const box = document.getElementById("adminUsersList");
  setAdminCount("adminUsersCount", items.length);

  if (!box) return;

  if (!items.length) {
    box.innerHTML = adminEmpty("Brak użytkowników.");
    return;
  }

  box.innerHTML = `
    <table class="adminTable">
      <thead>
        <tr>
          <th>ID</th>
          <th>Użytkownik</th>
          <th>Rola</th>
          <th>Status</th>
          <th>Pakiet</th>
          <th>Miasto</th>
          <th>Data ur.</th>
          <th>Utworzono</th>
          <th>Akcje</th>
        </tr>
      </thead>
      <tbody>
        ${items.map((u) => `
          <tr>
            <td><strong>#${escapeAdmin(u.id)}</strong></td>
            <td>${escapeAdmin(u.display_name || u.email || "—")}<br><span>${escapeAdmin(u.email || "—")}</span></td>
            <td>${escapeAdmin(u.role || "—")}</td>
            <td>${adminStatusBadge(u.status || "active")}</td>
            <td>${escapeAdmin(u.plan || "free")}<br><span>${escapeAdmin(u.plan_source || "manual")}</span></td>
            <td>${escapeAdmin(u.city || "—")}</td>
            <td>${escapeAdmin(u.dob || "—")}</td>
            <td>${escapeAdmin(u.created_at || "—")}</td>
            <td>
              <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <button class="tableAction" type="button" onclick="openUserPreview('${escapeAdmin(u.id)}')">Podgląd</button>
              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

async function reloadAdminUsers() {
  try {
    const res = await window.apiFetch("/admin/users");
    const items = Array.isArray(res?.data?.items) ? res.data.items : [];
    const query = String(document.getElementById("adminUserSearch")?.value || "").trim().toLowerCase();
    const roleFilter = String(document.getElementById("adminUsersRoleFilter")?.value || "all");
    const statusFilter = String(document.getElementById("adminUsersStatusFilter")?.value || "all");
    const planFilter = String(document.getElementById("adminUsersPlanFilter")?.value || "all");

    Admin.users = items;

    const filtered = items.filter((u) => {
      const haystack = [
        u.id,
        u.email,
        u.display_name,
        u.role,
        u.status,
        u.plan,
        u.city,
      ].map(v => String(v || "").toLowerCase()).join(" ");

      if (query && !haystack.includes(query)) return false;
      if (roleFilter !== "all" && String(u.role || "") !== roleFilter) return false;
      if (statusFilter !== "all" && String(u.status || "") !== statusFilter) return false;
      if (planFilter !== "all" && String(u.plan || "") !== planFilter) return false;

      return true;
    });

    renderAdminUsers(filtered);
  } catch (e) {
    console.error("reloadAdminUsers error", e);
    adminToast(e?.userMessage || "Nie udało się pobrać użytkowników.");
  }
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
  if (status === "pending_owner_approval" && !String(extra.moderator_note || "").trim()) {
    adminToast("Dodaj notatkę dla ownera przed przekazaniem sprawy.");
    return;
  }

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


async function adminAddReportNote(reportType, ticket, textareaId, reopen = null) {
  const note = document.getElementById(textareaId)?.value || "";

  if (!String(note).trim()) {
    adminToast("Wpisz notatkę.");
    return;
  }

  try {
    await window.apiFetch(`/admin/reports/${encodeURIComponent(reportType)}/${encodeURIComponent(ticket)}/note`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note }),
    });

    adminToast("Notatka dodana.");
    await reloadAdminReports();

    if (typeof reopen === "function") {
      await reopen();
    }
  } catch (e) {
    console.error("adminAddReportNote error", e);
    adminToast(e?.userMessage || "Nie udało się dodać notatki.");
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
  const moderator_note = status === "pending_owner_approval"
    ? String(document.getElementById("userOwnerApprovalNote")?.value || "").trim()
    : "";

  await adminSetReportStatus("user", reportTicket, status, { moderator_note });
  await reloadAdminReports();
  openUserPreview(userId, reportTicket, status);
}

async function adminSetEventReportDecision(eventId, reportTicket, status) {
  const moderator_note = status === "pending_owner_approval"
    ? String(document.getElementById("eventOwnerApprovalNote")?.value || "").trim()
    : "";

  await adminSetReportStatus("event", reportTicket, status, { moderator_note });
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
    await reloadAdminEvents();
  } catch (e) {
    console.error("adminSetEventStatus error", e);
    adminToast(e?.userMessage || "Nie udało się zmienić statusu wydarzenia.");
  }
}

async function adminSendUserResetLink(userId) {
  try {
    const res = await window.apiFetch(`/admin/users/${encodeURIComponent(userId)}/send-reset-link`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (res?.data?.emailed) {
      adminToast("Link resetu hasła wysłany.");
    } else {
      adminToast("Link resetu utworzony, ale mail nie został wysłany.");
    }

    await openUserPreview(userId);
  } catch (e) {
    console.error("adminSendUserResetLink error", e);
    adminToast(e?.userMessage || "Nie udało się wysłać linku resetu.");
  }
}

async function adminResetUserPassword(userId) {
  const input = document.getElementById("adminTempPasswordInput");
  const newPassword = String(input?.value || "").trim();

  if (newPassword.length < 6) {
    adminToast("Hasło musi mieć minimum 6 znaków.");
    return;
  }

  try {
    await window.apiFetch(`/admin/users/${encodeURIComponent(userId)}/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_password: newPassword }),
    });

    if (input) input.value = "";
    adminToast("Hasło tymczasowe ustawione.");
    await openUserPreview(userId);
  } catch (e) {
    console.error("adminResetUserPassword error", e);
    adminToast(e?.userMessage || "Nie udało się ustawić hasła.");
  }
}

async function adminUpdateUserPlan(userId) {
  const plan = document.getElementById("adminUserPlanSelect")?.value || "free";
  const planSource = document.getElementById("adminUserPlanSourceSelect")?.value || "manual";
  const planStatus = document.getElementById("adminUserPlanStatusSelect")?.value || "active";

  try {
    await window.apiFetch(`/admin/users/${encodeURIComponent(userId)}/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan,
        plan_source: planSource,
        plan_status: planStatus,
      }),
    });

    adminToast("Pakiet użytkownika zaktualizowany.");
    await reloadAdminUsers();
    await openUserPreview(userId);
  } catch (e) {
    console.error("adminUpdateUserPlan error", e);
    adminToast(e?.userMessage || "Nie udało się zmienić pakietu.");
  }
}

async function adminDeleteUserAccount(userId) {
  const confirmed = window.confirm("Czy na pewno usunąć konto? Email zostanie zwolniony do ponownej rejestracji, a konto oznaczone jako usunięte.");
  if (!confirmed) return;

  try {
    await window.apiFetch(`/admin/users/${encodeURIComponent(userId)}/delete-account`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    adminToast("Konto usunięte.");
    await reloadAdminUsers();
    await openUserPreview(userId);
  } catch (e) {
    console.error("adminDeleteUserAccount error", e);
    adminToast(e?.userMessage || "Nie udało się usunąć konta.");
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

    await reloadAdminUsers();
    if (typeof reloadAdminDashboard === "function") await reloadAdminDashboard();
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


function openCreateUserDrawer() {
  openAdminDrawer(`
    <div class="adminPreviewCard">
      <h2>Utwórz konto</h2>
      <p class="adminSystemHint">Konto utworzone z panelu admina powinno docelowo przejść potwierdzenie mailowe. Na tym etapie ustawiamy hasło tymczasowe i zapisujemy akcję w logach.</p>

      <div class="adminActionStack">
        <label class="adminFieldLabel" for="adminCreateUserEmail">Email</label>
        <input class="adminFieldInput" id="adminCreateUserEmail" type="email" placeholder="email@domena.pl" />

        <label class="adminFieldLabel" for="adminCreateUserRole">Rola</label>
        <select class="adminFieldInput" id="adminCreateUserRole">
          <option value="user">Towarzysz</option>
          <option value="partner">Organizator</option>
          <option value="admin">Admin</option>
        </select>

        <label class="adminFieldLabel" for="adminCreateUserDob">Data urodzenia</label>
        <input class="adminFieldInput" id="adminCreateUserDob" type="date" />
        <div class="adminWarnHint">Data urodzenia jest wymagana dla Towarzysza. Dla Organizatora/Admina może zostać pusta.</div>

        <div class="adminInlineNotice">
          <strong>Dane admina</strong>
          <span>Uzupełnij tylko, jeśli tworzysz konto z rolą Admin. Tworzenie adminów jest dostępne wyłącznie dla ownera.</span>
        </div>

        <label class="adminFieldLabel" for="adminCreateAdminDisplayName">Nazwa admina</label>
        <input class="adminFieldInput" id="adminCreateAdminDisplayName" type="text" placeholder="np. Support Marta" />

        <label class="adminFieldLabel" for="adminCreateAdminLevel">Poziom dostępu admina</label>
        <select class="adminFieldInput" id="adminCreateAdminLevel">
          <option value="">Wybierz poziom</option>
          <option value="owner">Owner — pełny dostęp</option>
          <option value="operations">Operations — użytkownicy, wydarzenia, plany, zgłoszenia</option>
          <option value="support">Support — zgłoszenia i obsługa</option>
        </select>

        <label class="adminFieldLabel" for="adminCreateUserPassword">Hasło tymczasowe</label>
        <input class="adminFieldInput" id="adminCreateUserPassword" type="text" placeholder="Minimum 6 znaków" />

        <button class="adminPrimaryAction" type="button" onclick="adminCreateUserAccount()">
          Utwórz konto
        </button>
      </div>
    </div>
  `);
}

async function adminCreateUserAccount() {
  const email = String(document.getElementById("adminCreateUserEmail")?.value || "").trim();
  const role = String(document.getElementById("adminCreateUserRole")?.value || "user");
  const dob = String(document.getElementById("adminCreateUserDob")?.value || "").trim();
  const password = String(document.getElementById("adminCreateUserPassword")?.value || "").trim();
  const admin_display_name = String(document.getElementById("adminCreateAdminDisplayName")?.value || "").trim();
  const admin_level = String(document.getElementById("adminCreateAdminLevel")?.value || "").trim();

  if (!email || !email.includes("@")) {
    adminToast("Podaj poprawny email.");
    return;
  }

  if (password.length < 6) {
    adminToast("Hasło musi mieć minimum 6 znaków.");
    return;
  }

  if (role === "user" && !dob) {
    adminToast("Data urodzenia jest wymagana dla Towarzysza.");
    return;
  }

  if (role === "admin" && !admin_display_name) {
    adminToast("Podaj nazwę admina, np. Support Marta.");
    return;
  }

  if (role === "admin" && !admin_level) {
    adminToast("Wybierz poziom dostępu admina.");
    return;
  }

  try {
    const res = await window.apiFetch("/admin/users/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, role, dob, password, admin_display_name, admin_level }),
    });

    adminToast("Konto utworzone.");
    await reloadAdminUsers();

    const id = res?.data?.id;
    if (id) {
      await openUserPreview(id);
    } else {
      closeAdminDrawer();
    }
  } catch (e) {
    console.error("adminCreateUserAccount error", e);
    adminToast(e?.userMessage || "Nie udało się utworzyć konta.");
  }
}


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
  await openBugPreview(ticket);
}

function adminHistoryEntryLabel(h) {
  if (h.type === "note") return "Notatka admina";
  if (h.type === "warning") return "Ostrzeżenie wysłane";
  if (h.type === "notify_watchers") return "Powiadomienie zapisanych";
  if (String(h.to_status || "").toLowerCase() === "archived") return "Archiwum wewnętrzne";
  return "Zmiana statusu";
}

function adminHistoryActorLabel(h) {
  const name = h.admin_display_name || (h.admin_id ? `Admin #${h.admin_id}` : "Admin");
  const level = h.admin_level ? ` · ${h.admin_level}` : "";
  return `${name}${level}`;
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
          <div class="adminHistoryMeta">${escapeAdmin(h.at || "—")} · ${escapeAdmin(adminHistoryActorLabel(h))}</div>
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
          <div class="adminHistoryMeta">${escapeAdmin(h.at || "—")} · ${escapeAdmin(adminHistoryActorLabel(h))}</div>
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
          <div class="adminHistoryMeta">${escapeAdmin(h.at || "—")} · ${escapeAdmin(adminHistoryActorLabel(h))}</div>
        </div>
      `;
    }

    return `
      <div class="adminHistoryCard">
        <div class="adminHistoryKind">${escapeAdmin(kind)}</div>
        <div class="adminHistoryTitle">${escapeAdmin(adminStatusLabel(h.from_status || "new"))} → ${escapeAdmin(adminStatusLabel(h.to_status || "new"))}</div>
        <div class="adminHistoryMeta">${escapeAdmin(h.at || "—")} · ${escapeAdmin(adminHistoryActorLabel(h))}</div>
        ${h.moderator_note ? `<div class="adminHistoryMeta"><strong>Notatka:</strong> ${escapeAdmin(h.moderator_note)}</div>` : ""}
        ${h.moderator_message ? `<div class="adminHistoryMeta"><strong>Wiadomość:</strong> ${escapeAdmin(h.moderator_message)}</div>` : ""}
      </div>
    `;
  }).join("");
}

async function openUserAccountHistory(userId) {
  try {
    const res = await window.apiFetch(`/admin/users/${encodeURIComponent(userId)}/preview`);
    const u = res?.data || {};
    const history = Array.isArray(u.account_history) ? u.account_history : [];

    openAdminDrawer(`
      <div class="adminPreviewCard">
        <div class="adminHistoryTop">
          <button class="adminGhostMiniButton" type="button" onclick="openUserPreview('${escapeAdmin(userId)}')">← Wróć do profilu</button>
          <h2>Pełna historia konta</h2>
          <p class="adminSystemHint">${escapeAdmin(u.email || "—")} • ${escapeAdmin(u.role || "—")} • ${escapeAdmin(u.status || "—")}</p>
        </div>

        ${
          history.length
            ? history.map((h) => `
                <div class="adminHistoryCard">
                  <div class="adminHistoryKind">${escapeAdmin(h.action || "Akcja")}</div>
                  <div class="adminHistoryMeta">${escapeAdmin(h.created_at || "—")}</div>
                  <div class="adminHistoryMeta">${escapeAdmin(h.details || "—")}</div>
                </div>
              `).join("")
            : `<div class="adminHistoryCard">
                <div class="adminHistoryTitle">Brak historii konta</div>
                <div class="adminHistoryMeta">Akcje administracyjne pojawią się tutaj.</div>
              </div>`
        }
      </div>
    `);
  } catch (e) {
    console.error("openUserAccountHistory error", e);
    adminToast("Nie udało się pobrać historii konta.");
  }
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

async function openEventFullHistory(eventId) {
  try {
    const res = await window.apiFetch(`/admin/events/${encodeURIComponent(eventId)}/preview`);
    const ev = res?.data || {};
    const history = Array.isArray(ev.event_history) ? ev.event_history : [];

    openAdminDrawer(`
      <div class="adminPreviewCard">
        <div class="adminHistoryTop">
          <button class="adminGhostMiniButton" type="button" onclick="openEventPreview('${escapeAdmin(eventId)}')">← Wróć do wydarzenia</button>
          <h2>Pełna historia wydarzenia</h2>
          <p class="adminSystemHint">${escapeAdmin(ev.title || "Wydarzenie")} • ${escapeAdmin(history.length)} wpisów</p>
        </div>

        ${
          history.length
            ? history.map((h) => `
                <div class="adminHistoryCard">
                  <div class="adminHistoryKind">${escapeAdmin(h.action || "Akcja")}</div>
                  <div class="adminHistoryMeta">${escapeAdmin(h.created_at || "—")}</div>
                  <div class="adminHistoryMeta">${escapeAdmin(h.details || "—")}</div>
                </div>
              `).join("")
            : `<div class="adminHistoryCard">
                <div class="adminHistoryTitle">Brak historii wydarzenia</div>
              </div>`
        }
      </div>
    `);
  } catch (e) {
    console.error("openEventFullHistory error", e);
    adminToast("Nie udało się pobrać historii wydarzenia.");
  }
}

async function openEventPeopleList(eventId, kind = "signups") {
  try {
    const res = await window.apiFetch(`/admin/events/${encodeURIComponent(eventId)}/preview`);
    const ev = res?.data || {};
    const list = kind === "saves" ? (ev.saves || []) : (ev.signups || []);
    const title = kind === "saves" ? "Obserwujący wydarzenie" : "Zapisani na wydarzenie";

    openAdminDrawer(`
      <div class="adminPreviewCard">
        <div class="adminHistoryTop">
          <button class="adminGhostMiniButton" type="button" onclick="openEventPreview('${escapeAdmin(eventId)}')">← Wróć do wydarzenia</button>
          <h2>${escapeAdmin(title)}</h2>
          <p class="adminSystemHint">${escapeAdmin(ev.title || "Wydarzenie")} • ${escapeAdmin(list.length)} osób</p>
        </div>

        ${
          list.length
            ? `<table class="adminTable">
                <thead>
                  <tr>
                    <th>User ID</th>
                    <th>Użytkownik</th>
                    <th>Status</th>
                    <th>Miasto</th>
                    <th>Data</th>
                    <th>Akcje</th>
                  </tr>
                </thead>
                <tbody>
                  ${list.map((person) => `
                    <tr>
                      <td><strong>#${escapeAdmin(person.user_id || "—")}</strong></td>
                      <td>${escapeAdmin(person.nick || "Użytkownik")}<br><span>${escapeAdmin(person.email || "—")}</span></td>
                      <td>${adminStatusBadge(person.status || "active")}</td>
                      <td>${escapeAdmin(person.city || "—")}</td>
                      <td>${escapeAdmin(person.created_at || "—")}</td>
                      <td><button class="tableAction" type="button" onclick="openUserPreview('${escapeAdmin(person.user_id)}','','','${escapeAdmin(ev.id)}')">Podgląd</button></td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>`
            : `<div class="adminHistoryCard">
                <div class="adminHistoryTitle">Brak osób</div>
                <div class="adminHistoryMeta">Ta lista jest jeszcze pusta.</div>
              </div>`
        }
      </div>
    `);
  } catch (e) {
    console.error("openEventPeopleList error", e);
    adminToast("Nie udało się pobrać listy osób.");
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

    ${
      bug.reporter_user_id || bug.user_id
        ? `<div class="adminPreviewCard">
            <h3>Pomoc przy koncie</h3>
            <div class="adminSystemHint">
              Dostępne tylko dlatego, że zgłoszenie błędu ma kontekst zalogowanego użytkownika. Nie ustawiamy hasła ręcznie — wysyłamy link resetu.
            </div>
            <div class="adminPreviewActions">
              <button class="adminPrimaryAction" type="button" onclick="adminSendUserResetLink('${escapeAdmin(bug.reporter_user_id || bug.user_id)}')">
                Wyślij link resetu hasła
              </button>
            </div>
          </div>`
        : ""
    }

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
  const canFinalizeReportDecision = adminCanFinalizeReportDecision();
  const canManageEvents = adminCanManageEvents();
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
            <div><span>Nazwa wydarzenia</span><strong>${escapeAdmin(ev.title || "—")}</strong></div>
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

      <div class="adminPreviewGrid">
        <div class="adminPreviewCard">
          <div class="adminHistoryHeader">
            <h3>Zapisani</h3>
            <span class="adminHistoryCount">${escapeAdmin(ev.signups_count || 0)} osób</span>
          </div>
          ${(ev.signups || []).slice(0, 5).map((person) => `
            <div class="adminHistoryCard" onclick="openUserPreview('${escapeAdmin(person.user_id)}','','','${escapeAdmin(ev.id)}')" style="cursor:pointer;">
              <div class="adminHistoryTitle">${escapeAdmin(person.nick || "Użytkownik")} • #${escapeAdmin(person.user_id || "—")}</div>
              <div class="adminHistoryMeta">${escapeAdmin(person.email || "—")}</div>
              <div class="adminHistoryMeta">${escapeAdmin(person.created_at || "—")}</div>
            </div>
          `).join("") || `<div class="adminHistoryCard"><div class="adminHistoryTitle">Brak zapisanych</div></div>`}
          ${(ev.signups || []).length > 5 ? `<button class="adminGhostMiniButton" type="button" onclick="openEventPeopleList('${escapeAdmin(ev.id)}','signups')">Zobacz wszystkich</button>` : ""}
        </div>

        <div class="adminPreviewCard">
          <div class="adminHistoryHeader">
            <h3>Obserwujący</h3>
            <span class="adminHistoryCount">${escapeAdmin(ev.saves_count || 0)} osób</span>
          </div>
          ${(ev.saves || []).slice(0, 5).map((person) => `
            <div class="adminHistoryCard" onclick="openUserPreview('${escapeAdmin(person.user_id)}','','','${escapeAdmin(ev.id)}')" style="cursor:pointer;">
              <div class="adminHistoryTitle">${escapeAdmin(person.nick || "Użytkownik")} • #${escapeAdmin(person.user_id || "—")}</div>
              <div class="adminHistoryMeta">${escapeAdmin(person.email || "—")}</div>
              <div class="adminHistoryMeta">${escapeAdmin(person.created_at || "—")}</div>
            </div>
          `).join("") || `<div class="adminHistoryCard"><div class="adminHistoryTitle">Brak obserwujących</div></div>`}
          ${(ev.saves || []).length > 5 ? `<button class="adminGhostMiniButton" type="button" onclick="openEventPeopleList('${escapeAdmin(ev.id)}','saves')">Zobacz wszystkich</button>` : ""}
        </div>
      </div>

      <div class="adminPreviewBottomGrid">
        <div class="adminPreviewCard">
          <h3>${canManageEvents ? "Akcje wydarzenia" : "Uprawnienia supportu"}</h3>

          ${
            canManageEvents
              ? `<div class="adminActionStack">
                  <button class="${String(ev.status || "").toLowerCase() === "archived" ? "adminPrimaryAction" : "adminDangerAction"}" type="button" onclick="adminSetEventStatus('${escapeAdmin(ev.id)}','${String(ev.status || "").toLowerCase() === "archived" ? "published" : "archived"}')">
                    ${String(ev.status || "").toLowerCase() === "archived" ? "Przywróć wydarzenie" : "Zarchiwizuj wydarzenie"}
                  </button>

                  <button class="adminPrimaryAction" type="button" onclick="adminNotifyEventWatchers('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','${escapeAdmin(reportStatus)}')">
                    Powiadom zapisanych
                  </button>
                </div>

                <div class="adminSystemHint">
                  Archiwizacja wydarzenia dotyczy samego wydarzenia. Powiadomienie zapisanych zostaje osobną akcją.
                </div>`
              : `<div class="adminWarnBox">
                  <div class="adminHistoryTitle">Ten poziom admina nie może archiwizować ani przywracać wydarzeń.</div>
                  <div class="adminHistoryMeta">Możesz przeanalizować zgłoszenie, dodać notatkę i przekazać sprawę do akceptacji ownera.</div>
                </div>`
          }

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
                    <button class="adminDecisionButton ${String(reportStatus || "new") === "in_review" ? "adminDecisionCurrent" : ""}" type="button" ${String(reportStatus || "new") === "in_review" || String(reportStatus || "new") === "resolved" || String(reportStatus || "new") === "rejected" ? "disabled" : `onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','in_review')"`}>
                      <strong>${String(reportStatus || "new") === "in_review" ? "Aktualnie: sprawdzamy" : "Sprawdzamy"}</strong>
                      <span>${String(reportStatus || "new") === "resolved" || String(reportStatus || "new") === "rejected" ? "Zgłoszenie jest już zamknięte." : "Zgłoszenie wydarzenia jest analizowane."}</span>
                    </button>
                    ${
                      canFinalizeReportDecision
                        ? `
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
                        `
                        : String(reportStatus || "new") === "pending_owner_approval"
                          ? `<div class="adminWarnBox">
                              <div class="adminHistoryTitle">Sprawa przekazana do ownera</div>
                              <div class="adminHistoryMeta">Ten poziom admina nie może już zamknąć tego zgłoszenia. Poczekaj na decyzję ownera.</div>
                            </div>`
                          : String(reportStatus || "new") === "resolved" || String(reportStatus || "new") === "rejected"
                            ? `<div class="adminWarnBox">
                                <div class="adminHistoryTitle">Zgłoszenie zamknięte</div>
                                <div class="adminHistoryMeta">Po zamknięciu nie można przekazać tej sprawy do ownera bez ponownego otwarcia.</div>
                              </div>`
                            : `
                    <button class="adminDecisionButton" type="button" onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','resolved')">
                      <strong>Zasadne / zamknij</strong>
                      <span>Sprawa bez ciężkiej akcji. Zamyka zgłoszenie po pierwszej weryfikacji.</span>
                    </button>
                    <button class="adminDecisionButton" type="button" onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','rejected')">
                      <strong>Brak podstaw / odrzuć</strong>
                      <span>Nie wymaga dalszych działań ani akceptacji ownera.</span>
                    </button>
                    <div class="adminWarnBox">
                      <label class="adminFieldLabel" for="eventOwnerApprovalNote">Notatka dla ownera</label>
                      <textarea class="adminFieldTextarea" id="eventOwnerApprovalNote" rows="3" placeholder="Opisz, co owner ma zatwierdzić i dlaczego. To pole jest wymagane."></textarea>
                      <div class="adminWarnHint">Użyj tylko, gdy potrzebna jest ciężka akcja, np. archiwizacja wydarzenia lub decyzja sporna.</div>
                    </div>
                    <button class="adminDecisionButton" type="button" onclick="adminSetEventReportDecision('${escapeAdmin(ev.id)}','${escapeAdmin(reportTicket)}','pending_owner_approval')">
                      <strong>Przekaż do akceptacji ownera</strong>
                      <span>Przekaż sprawę do kolejki ownera. Użytkownik nie dostanie jeszcze powiadomienia.</span>
                    </button>
                        `
                    }
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

      <div class="adminPreviewCard">
        <div class="adminHistoryHeader">
          <h3>Historia wydarzenia</h3>
          <span class="adminHistoryCount">${escapeAdmin((ev.event_history || []).length)} wpisów</span>
        </div>
        ${
          Array.isArray(ev.event_history) && ev.event_history.length
            ? ev.event_history.slice(0, 5).map((h) => `
                <div class="adminHistoryCard">
                  <div class="adminHistoryKind">${escapeAdmin(h.action || "Akcja")}</div>
                  <div class="adminHistoryMeta">${escapeAdmin(h.created_at || "—")}</div>
                  <div class="adminHistoryMeta">${escapeAdmin(h.details || "—")}</div>
                </div>
              `).join("")
            : `<div class="adminHistoryCard"><div class="adminHistoryTitle">Brak historii wydarzenia</div></div>`
        }
        ${Array.isArray(ev.event_history) && ev.event_history.length > 5
          ? `<button class="adminGhostMiniButton" type="button" onclick="openEventFullHistory('${escapeAdmin(ev.id)}')">Zobacz wszystko</button>`
          : ""}
      </div>
    `);
  } catch (e) {
    console.error("openEventPreview error", e);
    adminToast("Nie udało się pobrać podglądu wydarzenia.");
  }
}


async function openUserPreview(userId, reportTicket = '', reportStatus = 'new', returnEventId = null) {
  const canFinalizeReportDecision = adminCanFinalizeReportDecision();
  const canManageUsers = adminCanManageUsers();
  const canDeleteAccounts = adminCanDeleteAccounts();
  try {
    const res = await window.apiFetch(`/admin/users/${userId}/preview${reportTicket ? `?ticket=${encodeURIComponent(reportTicket)}` : ""}`);
    const u = res?.data || {};

    openAdminDrawer(`
  ${
    returnEventId
      ? `<div class="adminPreviewActions">
          <button class="adminGhostAction" type="button" onclick="openEventPreview('${escapeAdmin(returnEventId)}')">
            ← Wróć do wydarzenia
          </button>
        </div>`
      : ""
  }

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

        <div class="adminHistoryCard" style="margin-top:14px;">
          <div class="adminHistoryTitle">Zgłoszenia użytkownika</div>
          <div class="adminHistoryMeta">Łącznie: ${escapeAdmin(u.reports_total || 0)}</div>
          <div class="adminHistoryMeta">Otwarte: ${escapeAdmin(u.reports_open || 0)}</div>
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
      <h3>${canManageUsers ? "Szybkie akcje" : "Uprawnienia supportu"}</h3>

      ${
        !canManageUsers
          ? `<div class="adminWarnBox">
              <div class="adminHistoryTitle">Ten poziom admina nie może blokować, usuwać kont ani zmieniać pakietów.</div>
              <div class="adminHistoryMeta">Możesz analizować zgłoszenie, dodać notatkę, wysłać ostrzeżenie i przekazać sprawę do akceptacji ownera.</div>
            </div>`
          : `<div class="adminActionStack">
              ${
                String(u.status || "active") === "blocked"
                  ? `<button class="adminPrimaryAction" type="button" onclick="adminSetUserStatus('${escapeAdmin(u.id)}','active')">Odblokuj użytkownika</button>`
                  : String(u.status || "active") === "deleted"
                    ? `<button class="adminGhostAction" type="button" disabled>Konto usunięte</button>`
                    : `<button class="adminDangerAction" type="button" onclick="adminSetUserStatus('${escapeAdmin(u.id)}','blocked')">Zablokuj użytkownika</button>`
              }

              ${
                canDeleteAccounts && String(u.role || "") !== "admin" && String(u.status || "active") !== "deleted"
                  ? `<button class="adminDangerAction" type="button" onclick="adminDeleteUserAccount('${escapeAdmin(u.id)}')">Usuń konto</button>`
                  : ""
              }

              ${
                String(u.status || "active") !== "deleted"
                  ? `<div class="adminWarnBox">
                      <label class="adminFieldLabel" for="adminUserPlanSelect">Pakiet konta</label>
                      <select class="adminFieldInput" id="adminUserPlanSelect">
                        ${(
                          String(u.role || "user") === "partner"
                            ? [["free","FREE"],["pro","PRO"],["premium","PREMIUM"],["enterprise","ENTERPRISE / wycena indywidualna"]]
                            : [["free","FREE"],["plus","PLUS"],["premium","PREMIUM"],["vip","VIP"]]
                        ).map(([plan, label]) => `<option value="${plan}" ${String(u.plan || "free") === plan ? "selected" : ""}>${label}</option>`).join("")}
                      </select>

                      <label class="adminFieldLabel" for="adminUserPlanSourceSelect">Źródło pakietu</label>
                      <select class="adminFieldInput" id="adminUserPlanSourceSelect">
                        ${[
                          ["manual", "Ręcznie"],
                          ["paid", "Płatny"],
                          ["barter", "Barter"],
                          ["promo", "Promo"],
                          ["test", "Test"],
                        ].map(([source, label]) => `<option value="${source}" ${String(u.plan_source || "manual") === source ? "selected" : ""}>${label}</option>`).join("")}
                      </select>

                      <label class="adminFieldLabel" for="adminUserPlanStatusSelect">Status pakietu</label>
                      <select class="adminFieldInput" id="adminUserPlanStatusSelect">
                        ${["active","inactive","expired","trial"].map(status => `<option value="${status}" ${String(u.plan_status || "active") === status ? "selected" : ""}>${status}</option>`).join("")}
                      </select>

                      <button class="adminPrimaryAction" type="button" onclick="adminUpdateUserPlan('${escapeAdmin(u.id)}')">
                        Zapisz pakiet
                      </button>
                      <div class="adminWarnHint">Użyj np. barter/promo/test, gdy pakiet jest nadany ręcznie przez administrację.</div>
                    </div>

                    <div class="adminWarnBox">
                      <label class="adminFieldLabel" for="adminTempPasswordInput">Hasło tymczasowe</label>
                      <input class="adminFieldInput" id="adminTempPasswordInput" type="text" placeholder="Minimum 6 znaków" />
                      <button class="adminPrimaryAction" type="button" onclick="adminResetUserPassword('${escapeAdmin(u.id)}')">
                        Ustaw hasło tymczasowe
                      </button>
                      <button class="adminGhostAction" type="button" onclick="adminSendUserResetLink('${escapeAdmin(u.id)}')">
                        Wyślij link resetu hasła
                      </button>
                      <div class="adminWarnHint">Ręczne hasło zapisze się w logach. Bezpieczniejsza opcja to wysłanie użytkownikowi linku resetu.</div>
                    </div>`
                  : `<div class="adminWarnBox">
                      <div class="adminHistoryTitle">Konto usunięte</div>
                      <div class="adminHistoryMeta">Edycja pakietu, hasła i resetu jest wyłączona dla usuniętych kont.</div>
                    </div>`
              }
            </div>`
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
                <button class="adminDecisionButton ${String(reportStatus || "new") === "in_review" ? "adminDecisionCurrent" : ""}" type="button" ${String(reportStatus || "new") === "in_review" || String(reportStatus || "new") === "resolved" || String(reportStatus || "new") === "rejected" ? "disabled" : `onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','in_review')"`}>
                  <strong>${String(reportStatus || "new") === "in_review" ? "Aktualnie: sprawdzamy" : "Sprawdzamy"}</strong>
                  <span>${String(reportStatus || "new") === "resolved" || String(reportStatus || "new") === "rejected" ? "Zgłoszenie jest już zamknięte." : "Zgłoszenie jest analizowane."}</span>
                </button>
                ${
                  canFinalizeReportDecision
                    ? `
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
                    `
                    : String(reportStatus || "new") === "pending_owner_approval"
                      ? `<div class="adminWarnBox">
                          <div class="adminHistoryTitle">Sprawa przekazana do ownera</div>
                          <div class="adminHistoryMeta">Ten poziom admina nie może już zamknąć tego zgłoszenia. Poczekaj na decyzję ownera.</div>
                        </div>`
                      : String(reportStatus || "new") === "resolved" || String(reportStatus || "new") === "rejected"
                        ? `<div class="adminWarnBox">
                            <div class="adminHistoryTitle">Zgłoszenie zamknięte</div>
                            <div class="adminHistoryMeta">Po zamknięciu nie można przekazać tej sprawy do ownera bez ponownego otwarcia.</div>
                          </div>`
                        : `
                <button class="adminDecisionButton ${String(reportStatus || "new") === "resolved" ? "adminDecisionCurrent" : ""}" type="button" onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','resolved')">
                  <strong>Zasadne / zamknij</strong>
                  <span>Sprawa bez ciężkiej akcji. Zamyka zgłoszenie po pierwszej weryfikacji.</span>
                </button>
                <button class="adminDecisionButton ${String(reportStatus || "new") === "rejected" ? "adminDecisionCurrent" : ""}" type="button" onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','rejected')">
                  <strong>Brak podstaw / odrzuć</strong>
                  <span>Nie wymaga dalszych działań ani akceptacji ownera.</span>
                </button>
                <div class="adminWarnBox">
                  <label class="adminFieldLabel" for="userOwnerApprovalNote">Notatka dla ownera</label>
                  <textarea class="adminFieldTextarea" id="userOwnerApprovalNote" rows="3" placeholder="Opisz, co owner ma zatwierdzić i dlaczego. To pole jest wymagane."></textarea>
                  <div class="adminWarnHint">Użyj tylko, gdy potrzebna jest ciężka akcja, np. blokada lub usunięcie konta.</div>
                </div>
                <button class="adminDecisionButton" type="button" onclick="adminSetUserReportDecision('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','pending_owner_approval')">
                  <strong>Przekaż do akceptacji ownera</strong>
                  <span>Przekaż sprawę do kolejki ownera. Użytkownik nie dostanie jeszcze powiadomienia.</span>
                </button>
                    `
                }
              </div>`
          : ""
      }

      <div class="adminSystemHint">
        Wszystkie akcje administratora będą zapisywane w logach systemowych.
      </div>
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

  <div class="adminPreviewCard">
    <div class="adminHistoryHeader">
      <h3>Historia zgłoszeń</h3>

      <button class="adminGhostMiniButton" type="button" onclick="openUserReportHistory('${escapeAdmin(userId)}','${escapeAdmin(reportTicket)}','${escapeAdmin(reportStatus)}')">
        Zobacz wszystko
      </button>
    </div>

    ${renderAdminHistory(u.selected_report?.history, 5)}
  </div>

        ${
          canManageUsers
            ? `<div class="adminWarnBox">
          <div class="adminHistoryHeader">
            <h3>Historia pakietu</h3>
            <span class="adminHistoryCount">${escapeAdmin((u.plan_history || []).length)} wpisów</span>
          </div>
          ${
            Array.isArray(u.plan_history) && u.plan_history.length
              ? u.plan_history.map((h) => `
                  <div class="adminHistoryCard">
                    <div class="adminHistoryKind">Zmiana pakietu</div>
                    <div class="adminHistoryMeta">${escapeAdmin(h.created_at || "—")}</div>
                    <div class="adminHistoryMeta">${escapeAdmin(h.details || "—")}</div>
                  </div>
                `).join("")
              : `<div class="adminHistoryCard">
                  <div class="adminHistoryTitle">Brak historii zmian pakietu</div>
                  <div class="adminHistoryMeta">Zmiany wykonane przez administratora pojawią się tutaj.</div>
                </div>`
          }
        </div>

        <div class="adminWarnBox">
          <div class="adminHistoryHeader">
            <h3>Historia konta</h3>
            <span class="adminHistoryCount">${escapeAdmin((u.account_history || []).length)} wpisów</span>
          </div>
          ${
            Array.isArray(u.account_history) && u.account_history.length
              ? `${u.account_history.slice(0, 5).map((h) => `
                  <div class="adminHistoryCard">
                    <div class="adminHistoryKind">${escapeAdmin(h.action || "Akcja")}</div>
                    <div class="adminHistoryMeta">${escapeAdmin(h.created_at || "—")}</div>
                    <div class="adminHistoryMeta">${escapeAdmin(h.details || "—")}</div>
                  </div>
                `).join("")}
                ${u.account_history.length > 5
                  ? `<button class="adminGhostMiniButton" type="button" onclick="openUserAccountHistory('${escapeAdmin(userId)}')">Zobacz wszystko</button>`
                  : ""}`
              : `<div class="adminHistoryCard">
                  <div class="adminHistoryTitle">Brak historii konta</div>
                  <div class="adminHistoryMeta">Akcje administracyjne pojawią się tutaj.</div>
                </div>`
          }
        </div>`
            : ""
        }

`);

  } catch (e) {
    console.error("openUserPreview error", e);
    adminToast("Nie udało się pobrać podglądu użytkownika.");
  }
}


async function reloadAdminDashboard() {
  const summaryBox = document.getElementById("adminDashboardSummary");
  const updatedAt = document.getElementById("adminDashboardUpdatedAt");

  if (summaryBox) summaryBox.innerHTML = adminEmpty("Ładowanie danych dashboardu...");

  try {
    const [usersRes, eventsRes, userReportsRes, eventReportsRes, bugReportsRes] = await Promise.all([
      window.apiFetch("/admin/users"),
      window.apiFetch("/admin/events"),
      window.apiFetch("/admin/user-reports"),
      window.apiFetch("/admin/event-reports"),
      window.apiFetch("/admin/bug-reports"),
    ]);

    const users = Array.isArray(usersRes?.data?.items) ? usersRes.data.items : [];
    const events = Array.isArray(eventsRes?.data?.items) ? eventsRes.data.items : [];
    const userReports = Array.isArray(userReportsRes?.data) ? userReportsRes.data : [];
    const eventReports = Array.isArray(eventReportsRes?.data) ? eventReportsRes.data : [];
    const bugReports = Array.isArray(bugReportsRes?.data) ? bugReportsRes.data : [];

    Admin.users = users;
    Admin.events = events;
    Admin.reports.users = userReports;
    Admin.reports.events = eventReports;
    Admin.reports.bugs = bugReports;

    const rangeValue = String(document.getElementById("adminDashboardRange")?.value || "30");
    const now = new Date();
    const rangeStart = rangeValue === "all" ? null : new Date(now.getTime() - Number(rangeValue) * 24 * 60 * 60 * 1000);
    const toDate = (value) => {
      if (!value) return null;
      const d = new Date(String(value).replace(" ", "T"));
      return Number.isNaN(d.getTime()) ? null : d;
    };
    const inRange = (value) => {
      if (!rangeStart) return true;
      const d = toDate(value);
      return !!d && d >= rangeStart;
    };

    const usersInRange = users.filter(u => inRange(u.created_at));
    const eventsInRange = events.filter(ev => inRange(ev.created_at));
    const reportsInRange = [...userReports, ...eventReports, ...bugReports].filter(r => inRange(r.created_at || r.createdAt || r.date));

    const activeUsers = users.filter(u => String(u.status || "active") === "active");
    const partners = users.filter(u => String(u.role || "") === "partner");
    const admins = users.filter(u => String(u.role || "") === "admin");
    const activeEvents = events.filter(ev => String(ev.status || "") === "published");
    const archivedEvents = events.filter(ev => String(ev.status || "") === "archived");
    const draftEvents = events.filter(ev => String(ev.status || "") === "draft");

    const openReportStatuses = new Set(["new", "in_review", "accepted", "in_progress"]);
    const openReports = [...userReports, ...eventReports, ...bugReports].filter(r => openReportStatuses.has(String(r.status || "new")));

    if (updatedAt) updatedAt.textContent = new Date().toLocaleString("pl-PL");

    if (summaryBox) {
      summaryBox.innerHTML = `
        <div class="adminDashboardBlock">
          <div class="adminMiniSectionTitle">Stan całej aplikacji</div>
          <div class="adminMetricGrid">
            <div class="adminMetricCard"><span>Aktywni użytkownicy</span><strong>${activeUsers.length}</strong></div>
            <div class="adminMetricCard"><span>Organizatorzy</span><strong>${partners.length}</strong></div>
            <div class="adminMetricCard"><span>Admini</span><strong>${admins.length}</strong></div>
            <div class="adminMetricCard"><span>Aktywne wydarzenia</span><strong>${activeEvents.length}</strong></div>
            <div class="adminMetricCard"><span>Szkice wydarzeń</span><strong>${draftEvents.length}</strong></div>
            <div class="adminMetricCard"><span>Archiwum wydarzeń</span><strong>${archivedEvents.length}</strong></div>
            <div class="adminMetricCard"><span>Otwarte zgłoszenia</span><strong>${openReports.length}</strong></div>
            <div class="adminMetricCard"><span>Bug reporty</span><strong>${bugReports.length}</strong></div>
          </div>
        </div>

        <div class="adminDashboardBlock adminDashboardBlockHighlighted">
          <div class="adminMiniSectionTitle">W wybranym okresie: ${rangeValue === "all" ? "cały okres" : `ostatnie ${rangeValue} dni`}</div>
          <div class="adminMetricGrid">
            <div class="adminMetricCard"><span>Nowe konta</span><strong>${usersInRange.length}</strong></div>
            <div class="adminMetricCard"><span>Nowe wydarzenia</span><strong>${eventsInRange.length}</strong></div>
            <div class="adminMetricCard"><span>Zgłoszenia</span><strong>${reportsInRange.length}</strong></div>
          </div>
        </div>
      `;
    }

    
    const userPrices = { free: 0, plus: 19, premium: 39, vip: 79 };
    const partnerPrices = { free: 0, pro: 99, premium: 199, enterprise: 0 };

    const freeSources = new Set(["barter", "free", "trial"]);
    const isPaidAccount = (u) => !freeSources.has(String(u.plan_source || "manual").toLowerCase());

    const growthBox = document.getElementById("adminDashboardGrowth");
    const growthLabel = document.getElementById("adminDashboardGrowthRangeLabel");

    const usersInRangeByRole = {
      user: usersInRange.filter(u => String(u.role || "") === "user"),
      partner: usersInRange.filter(u => String(u.role || "") === "partner"),
    };

    const paidUsersInRange = usersInRangeByRole.user.filter(isPaidAccount);
    const paidPartnersInRange = usersInRangeByRole.partner.filter(isPaidAccount);

    const newUserMrr = paidUsersInRange.reduce((sum, u) => {
      return sum + Number(userPrices[String(u.plan || "free").toLowerCase()] || 0);
    }, 0);

    const newPartnerMrr = paidPartnersInRange.reduce((sum, u) => {
      return sum + Number(partnerPrices[String(u.plan || "free").toLowerCase()] || 0);
    }, 0);

    const totalNewMrr = newUserMrr + newPartnerMrr;

    if (growthLabel) {
      growthLabel.textContent =
        rangeValue === "all"
          ? "Cały okres"
          : `Ostatnie ${rangeValue} dni`;
    }

    if (growthBox) {
      growthBox.innerHTML = `
        <div class="adminRoleSplitGrid">
          <div class="adminRoleCard">
            <div class="adminRoleCardHead">
              <span>Towarzysze</span>
              <strong>${usersInRangeByRole.user.length}</strong>
            </div>

            <div class="adminRoleMetrics">
              <div>
                <span>Nowi płatni</span>
                <strong>${paidUsersInRange.length}</strong>
              </div>

              <div>
                <span>Added MRR</span>
                <strong>${newUserMrr} zł</strong>
              </div>

              <div>
                <span>Free</span>
                <strong>${usersInRangeByRole.user.filter(u => String(u.plan || "free") === "free").length}</strong>
              </div>

              <div>
                <span>Premium+</span>
                <strong>${usersInRangeByRole.user.filter(u => ["premium","vip"].includes(String(u.plan || "").toLowerCase())).length}</strong>
              </div>
            </div>
          </div>

          <div class="adminRoleCard">
            <div class="adminRoleCardHead">
              <span>Organizatorzy</span>
              <strong>${usersInRangeByRole.partner.length}</strong>
            </div>

            <div class="adminRoleMetrics">
              <div>
                <span>Nowi płatni</span>
                <strong>${paidPartnersInRange.length}</strong>
              </div>

              <div>
                <span>Added MRR</span>
                <strong>${newPartnerMrr} zł</strong>
              </div>

              <div>
                <span>Free</span>
                <strong>${usersInRangeByRole.partner.filter(u => String(u.plan || "free") === "free").length}</strong>
              </div>

              <div>
                <span>Premium+</span>
                <strong>${usersInRangeByRole.partner.filter(u => ["premium","enterprise"].includes(String(u.plan || "").toLowerCase())).length}</strong>
              </div>
            </div>
          </div>
        </div>

        <div class="adminRevenueHero">
          <span>Added MRR in selected period</span>
          <strong>${totalNewMrr} zł</strong>
          <small>Current MRR to aktywna baza. Added MRR pokazuje tylko nowy przyrost z wybranego okresu.</small>
        </div>
      `;
    }


const planBox = document.getElementById("adminDashboardPlans");
    const planCount = document.getElementById("adminDashboardPlansCount");
const buildPlanRows = (role, prices) => {
      const roleUsers = users.filter(u => String(u.role || "") === role);
      const rowsByPlan = roleUsers.reduce((acc, u) => {
        const plan = String(u.plan || "free").toLowerCase();
        const source = String(u.plan_source || "manual").toLowerCase();
        const status = String(u.plan_status || "active").toLowerCase();
        const paid = isPaidAccount(u);
        const price = paid ? Number(prices[plan] || 0) : 0;
        const key = `${plan}|${source}|${status}`;
        if (!acc[key]) acc[key] = { plan, source, status, count: 0, revenue: 0 };
        acc[key].count += 1;
        acc[key].revenue += price;
        return acc;
      }, {});

      return Object.values(rowsByPlan).sort((a, b) => b.count - a.count);
    };

    const userPlanRows = buildPlanRows("user", userPrices);
    const partnerPlanRows = buildPlanRows("partner", partnerPrices);
    const monthlyRevenue = [...userPlanRows, ...partnerPlanRows].reduce((sum, row) => sum + row.revenue, 0);

    const usersOnly = users.filter(u => String(u.role || "") === "user");
    const partnersOnly = users.filter(u => String(u.role || "") === "partner");
    const usersOnlyInRange = usersInRange.filter(u => String(u.role || "") === "user");
    const partnersOnlyInRange = usersInRange.filter(u => String(u.role || "") === "partner");

    const roleStats = (roleUsers, roleUsersInRange, prices) => {
      const paid = roleUsers.filter(u => isPaidAccount(u) && Number(prices[String(u.plan || "free").toLowerCase()] || 0) > 0);
      const barter = roleUsers.filter(u => String(u.plan_source || "").toLowerCase() === "barter");
      const free = roleUsers.filter(u => String(u.plan || "free").toLowerCase() === "free");
      const mrr = roleUsers.reduce((sum, u) => {
        const plan = String(u.plan || "free").toLowerCase();
        return sum + (isPaidAccount(u) ? Number(prices[plan] || 0) : 0);
      }, 0);
      const newMrr = roleUsersInRange.reduce((sum, u) => {
        const plan = String(u.plan || "free").toLowerCase();
        return sum + (isPaidAccount(u) ? Number(prices[plan] || 0) : 0);
      }, 0);

      return {
        total: roleUsers.length,
        newCount: roleUsersInRange.length,
        paid: paid.length,
        barter: barter.length,
        free: free.length,
        mrr,
        newMrr,
      };
    };

    const userStats = roleStats(usersOnly, usersOnlyInRange, userPrices);
    const partnerStats = roleStats(partnersOnly, partnersOnlyInRange, partnerPrices);

    const renderRoleCards = () => `
      <div class="adminRoleSplitGrid">
        <div class="adminRoleCard">
          <div class="adminRoleCardHead">
            <span>Towarzysze</span>
            <strong>${userStats.total}</strong>
          </div>
          <div class="adminRoleMetrics">
            <div><span>Nowi w okresie</span><strong>${userStats.newCount}</strong></div>
            <div><span>Płatni</span><strong>${userStats.paid}</strong></div>
            <div><span>Barter</span><strong>${userStats.barter}</strong></div>
            <div><span>Free</span><strong>${userStats.free}</strong></div>
            <div><span>MRR</span><strong>${userStats.mrr} zł</strong></div>
            <div><span>Nowy MRR</span><strong>${userStats.newMrr} zł</strong></div>
          </div>
        </div>

        <div class="adminRoleCard">
          <div class="adminRoleCardHead">
            <span>Organizatorzy</span>
            <strong>${partnerStats.total}</strong>
          </div>
          <div class="adminRoleMetrics">
            <div><span>Nowi w okresie</span><strong>${partnerStats.newCount}</strong></div>
            <div><span>Płatni</span><strong>${partnerStats.paid}</strong></div>
            <div><span>Barter</span><strong>${partnerStats.barter}</strong></div>
            <div><span>Free</span><strong>${partnerStats.free}</strong></div>
            <div><span>MRR</span><strong>${partnerStats.mrr} zł</strong></div>
            <div><span>Nowy MRR</span><strong>${partnerStats.newMrr} zł</strong></div>
          </div>
        </div>
      </div>
    `;

    const renderPlanSection = (title, rows, total) => `
      <div class="adminMiniSectionTitle">${escapeAdmin(title)}</div>
      ${rows.map((row) => {
        const width = total ? Math.max(8, Math.round((row.count / total) * 100)) : 0;
        return `
          <div class="adminChartRow">
            <div>
              <strong>${escapeAdmin(row.plan)}</strong>
              <span>${escapeAdmin(row.source)} / ${escapeAdmin(row.status)} / ${row.revenue} zł MRR</span>
            </div>
            <div class="adminChartBar"><i style="width:${width}%"></i></div>
            <b>${row.count}</b>
          </div>
        `;
      }).join("") || adminEmpty("Brak danych.")}
    `;

    const healthBox = document.getElementById("adminDashboardHealth");
    const healthStatus = document.getElementById("adminDashboardHealthStatus");
    const healthStartedAt = performance.now();

    try {
      await window.apiFetch("/healthz");
      const latency = Math.round(performance.now() - healthStartedAt);
      if (healthStatus) healthStatus.textContent = "Online";
      if (healthBox) {
        healthBox.innerHTML = `
          <div class="adminHealthOk">Backend działa</div>
          <div class="adminHealthRow"><span>Status API</span><strong>Online</strong></div>
          <div class="adminHealthRow"><span>Czas odpowiedzi</span><strong>${latency} ms</strong></div>
          <div class="adminHealthRow"><span>Ostatni odczyt</span><strong>${new Date().toLocaleString("pl-PL")}</strong></div>
        `;
      }
    } catch (healthError) {
      if (healthStatus) healthStatus.textContent = "Problem";
      if (healthBox) {
        healthBox.innerHTML = `
          <div class="adminHealthBad">Backend niedostępny</div>
          <div class="adminHealthRow"><span>Status API</span><strong>Offline / błąd</strong></div>
          <div class="adminHealthRow"><span>Ostatnia próba</span><strong>${new Date().toLocaleString("pl-PL")}</strong></div>
        `;
      }
    }

    const activityBox = document.getElementById("adminDashboardActivity");
    const activityCount = document.getElementById("adminDashboardActivityCount");

    const activityItems = [
      ...users.slice(0, 8).map(u => ({
        type: "user",
        title: `Nowe konto: ${u.display_name || u.email || "Użytkownik"}`,
        meta: `${u.role || "—"} / ${u.plan || "free"} / ${u.plan_source || "manual"}`,
        at: u.created_at,
      })),
      ...events.slice(0, 8).map(ev => ({
        type: "event",
        title: `Nowe wydarzenie: ${ev.title || "Wydarzenie"}`,
        meta: `${ev.status || "—"} / ${ev.city || "—"} / ${ev.organizer_name || "—"}`,
        at: ev.created_at,
      })),
      ...userReports.slice(0, 6).map(r => ({
        type: "report",
        title: `Zgłoszenie użytkownika: ${r.ticket || "UR"}`,
        meta: `${r.status || "new"} / ${r.reason_label || r.reason || "—"}`,
        at: r.created_at || r.updated_at,
      })),
      ...eventReports.slice(0, 6).map(r => ({
        type: "report",
        title: `Zgłoszenie wydarzenia: ${r.ticket || "ER"}`,
        meta: `${r.status || "new"} / ${r.event_title || "—"}`,
        at: r.created_at || r.updated_at,
      })),
      ...bugReports.slice(0, 6).map(r => ({
        type: "bug",
        title: `Bug report: ${r.ticket || r.id || "BUG"}`,
        meta: `${r.status || "new"} / ${r.current_view || r.role || "—"}`,
        at: r.created_at || r.createdAt || r.date,
      })),
    ]
      .filter(item => item.at)
      .sort((a, b) => {
        const da = toDate(a.at);
        const db = toDate(b.at);
        return (db?.getTime() || 0) - (da?.getTime() || 0);
      })
      .slice(0, 12);

    if (activityCount) activityCount.textContent = String(activityItems.length);
    if (activityBox) {
      activityBox.innerHTML = activityItems.length ? `
        <div class="adminActivityFeed">
          ${activityItems.map(item => `
            <div class="adminActivityItem" data-type="${escapeAdmin(item.type)}">
              <div>
                <strong>${escapeAdmin(item.title)}</strong>
                <span>${escapeAdmin(item.meta)}</span>
              </div>
              <time>${escapeAdmin(item.at || "—")}</time>
            </div>
          `).join("")}
        </div>
      ` : adminEmpty("Brak aktywności do wyświetlenia.");
    }

    const mrrTimelineBox = document.getElementById("adminDashboardMrrTimeline");

    const monthKey = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    const monthLabel = (key) => {
      const [year, month] = key.split("-");
      return `${month}.${year}`;
    };
    const daysInMonth = (date) => new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();

    const timelineStart = new Date(now.getFullYear(), now.getMonth() - 11, 1);
    const timelineMonths = Array.from({ length: 12 }, (_, i) => {
      const d = new Date(timelineStart.getFullYear(), timelineStart.getMonth() + i, 1);
      return monthKey(d);
    });

    const timeline = timelineMonths.reduce((acc, key) => {
      acc[key] = { month: key, user: 0, partner: 0, total: 0 };
      return acc;
    }, {});

    users.forEach((u) => {
      if (!isPaidAccount(u)) return;

      const created = toDate(u.created_at);
      if (!created) return;

      const role = String(u.role || "");
      const plan = String(u.plan || "free").toLowerCase();
      const price = role === "user"
        ? Number(userPrices[plan] || 0)
        : role === "partner"
          ? Number(partnerPrices[plan] || 0)
          : 0;

      if (!price) return;

      timelineMonths.forEach((key) => {
        const [year, month] = key.split("-").map(Number);
        const firstDay = new Date(year, month - 1, 1);
        const lastDay = new Date(year, month, 0, 23, 59, 59);

        if (created > lastDay) return;

        let recognized = price;

        if (created >= firstDay && created <= lastDay) {
          const remainingDays = daysInMonth(firstDay) - created.getDate() + 1;
          recognized = Math.round((price * remainingDays) / daysInMonth(firstDay));
        }

        if (role === "user") timeline[key].user += recognized;
        if (role === "partner") timeline[key].partner += recognized;
        timeline[key].total += recognized;
      });
    });

    const timelineRows = Object.values(timeline);
    const maxTimelineValue = Math.max(...timelineRows.map(row => row.total), 1);

    if (mrrTimelineBox) {
      mrrTimelineBox.innerHTML = `
        <div class="adminRevenueHero">
          <span>Estimated recognized monthly revenue</span>
          <strong>${timelineRows[timelineRows.length - 1]?.total || 0} zł</strong>
          <small>Estymacja lokalna: pierwszy miesiąc liczony proporcjonalnie od daty utworzenia konta. Bez realnych webhooków Apple/Google.</small>
        </div>

        <div class="adminTimelineChart">
          ${timelineRows.map(row => {
            const userWidth = Math.round((row.user / maxTimelineValue) * 100);
            const partnerWidth = Math.round((row.partner / maxTimelineValue) * 100);
            return `
              <div class="adminTimelineRow">
                <div class="adminTimelineMonth">${escapeAdmin(monthLabel(row.month))}</div>
                <div class="adminTimelineBars">
                  <div class="adminTimelineBar adminTimelineUser" style="width:${Math.max(userWidth, row.user ? 4 : 0)}%"></div>
                  <div class="adminTimelineBar adminTimelinePartner" style="width:${Math.max(partnerWidth, row.partner ? 4 : 0)}%"></div>
                </div>
                <div class="adminTimelineValue">
                  <strong>${row.total} zł</strong>
                  <span>T: ${row.user} zł / O: ${row.partner} zł</span>
                </div>
              </div>
            `;
          }).join("")}
        </div>

        <div class="adminTimelineAxis">
          <span>0 zł</span>
          <span>${Math.round(maxTimelineValue / 4)} zł</span>
          <span>${Math.round(maxTimelineValue / 2)} zł</span>
          <span>${Math.round((maxTimelineValue * 3) / 4)} zł</span>
          <span>${maxTimelineValue} zł</span>
        </div>

        <div class="adminTimelineLegend">
          <span><i class="adminTimelineDot adminTimelineUserDot"></i>Towarzysze</span>
          <span><i class="adminTimelineDot adminTimelinePartnerDot"></i>Organizatorzy</span>
        </div>
      `;
    }

    if (planCount) planCount.textContent = `${monthlyRevenue} zł MRR`;
    if (planBox) {
      planBox.innerHTML = `
        <div class="adminRevenueHero">
          <span>Szacowany miesięczny przychód</span>
          <strong>${monthlyRevenue} zł</strong>
          <small>Barter i custom/enterprise bez ceny liczone jako 0 zł.</small>
        </div>
        ${renderRoleCards()}
        ${renderPlanSection("Plany Towarzyszy", userPlanRows, usersOnly.length)}
        ${renderPlanSection("Plany Organizatorów", partnerPlanRows, partnersOnly.length)}
      `;
    }
  } catch (e) {
    console.error("reloadAdminDashboard error", e);
    if (summaryBox) summaryBox.innerHTML = adminEmpty("Nie udało się pobrać danych dashboardu.");
    adminToast(e?.userMessage || "Nie udało się pobrać dashboardu.");
  }
}



function showAdminView(view) {
  if (!adminCanView(view)) {
    adminToast("Brak dostępu do tej sekcji dla Twojego poziomu admina.");
    view = "reports";
  }

  const dashboardView = document.getElementById("adminDashboardHomeView");
  const reportsView = document.getElementById("adminReportsView");
  const usersView = document.getElementById("adminUsersView");
  const eventsView = document.getElementById("adminEventsView");

  document.querySelectorAll("[data-admin-view]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.adminView === view);
  });

  if (dashboardView) dashboardView.hidden = view !== "dashboard";
  if (reportsView) reportsView.hidden = view !== "reports";
  if (usersView) usersView.hidden = view !== "users";
  if (eventsView) eventsView.hidden = view !== "events";

  if (view === "dashboard" && typeof reloadAdminDashboard === "function") reloadAdminDashboard().catch(() => {});
  if (view === "reports") reloadAdminReports().catch(() => {});
  if (view === "users") reloadAdminUsers().catch(() => {});
  if (view === "events") reloadAdminEvents().catch(() => {});
}

document.querySelectorAll("[data-admin-view]").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.disabled) {
      adminToast("Brak dostępu do tej sekcji dla Twojego poziomu admina.");
      return;
    }
    showAdminView(btn.dataset.adminView || "reports");
  });
});

document.getElementById("adminStatusFilter")?.addEventListener("change", reloadAdminReports);
document.getElementById("adminCreateUserBtn")?.addEventListener("click", openCreateUserDrawer);
document.getElementById("adminUserSearch")?.addEventListener("input", reloadAdminUsers);
document.getElementById("adminUsersRoleFilter")?.addEventListener("change", reloadAdminUsers);
document.getElementById("adminUsersStatusFilter")?.addEventListener("change", reloadAdminUsers);
document.getElementById("adminUsersPlanFilter")?.addEventListener("change", reloadAdminUsers);


function exportAdminDashboardCsv() {
  try {
    const rows = [];
    const now = new Date().toLocaleString("pl-PL");

    rows.push(["USLY BI DASHBOARD EXPORT"]);
    rows.push(["Generated at", now]);
    rows.push([]);

    const cards = Array.from(document.querySelectorAll(".adminRoleCard"));

    cards.forEach((card) => {
      const title = card.querySelector(".adminRoleCardHead span")?.textContent?.trim() || "Role";
      const total = card.querySelector(".adminRoleCardHead strong")?.textContent?.trim() || "0";

      rows.push([title]);
      rows.push(["Total", total]);

      card.querySelectorAll(".adminRoleMetrics div").forEach((metric) => {
        const label = metric.querySelector("span")?.textContent?.trim() || "";
        const value = metric.querySelector("strong")?.textContent?.trim() || "";
        rows.push([label, value]);
      });

      rows.push([]);
    });

    rows.push(["MRR TIMELINE"]);
    rows.push(["Month", "Total", "Towarzysze", "Organizatorzy"]);

    document.querySelectorAll(".adminTimelineRow").forEach((row) => {
      const month = row.querySelector(".adminTimelineMonth")?.textContent?.trim() || "";
      const total = row.querySelector(".adminTimelineValue strong")?.textContent?.trim() || "";
      const split = row.querySelector(".adminTimelineValue span")?.textContent?.trim() || "";

      rows.push([month, total, split]);
    });

    const csv = rows
      .map(row => row.map(v => `"${String(v || "").replaceAll('"', '""')}"`).join(";"))
      .join("\n");

    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");

    const date = new Date().toISOString().slice(0,10);

    a.href = url;
    a.download = `usly-dashboard-${date}.csv`;

    document.body.appendChild(a);
    a.click();
    a.remove();

    URL.revokeObjectURL(url);

    adminToast("Wyeksportowano dashboard CSV.");
  } catch (e) {
    console.error("exportAdminDashboardCsv error", e);
    adminToast("Nie udało się wyeksportować dashboardu.");
  }
}


document.getElementById("adminEventSearch")?.addEventListener("input", reloadAdminEvents);
document.getElementById("adminEventsStatusFilter")?.addEventListener("change", reloadAdminEvents);
document.getElementById("adminDashboardExportBtn")?.addEventListener("click", exportAdminDashboardCsv);
document.getElementById("adminDashboardRange")?.addEventListener("change", () => {
  if (typeof reloadAdminDashboard === "function") reloadAdminDashboard().catch(() => {});
});

document.getElementById("adminLogoutBtn")?.addEventListener("click", () => {
  localStorage.removeItem("usly_token");

  if (adminAutoRefreshTimer) {
    window.clearInterval(adminAutoRefreshTimer);
    adminAutoRefreshTimer = null;
  }

  document.getElementById("adminDashboardView")?.setAttribute("hidden", "hidden");
  document.getElementById("adminLoginView")?.removeAttribute("hidden");

  adminToast("Wylogowano lokalnie.");
});

let adminAutoRefreshTimer = null;

function startAdminAutoRefresh() {
  if (adminAutoRefreshTimer) return;

  adminAutoRefreshTimer = window.setInterval(() => {
    const token = localStorage.getItem("usly_token");
    const dashboardVisible = !document.getElementById("adminDashboardView")?.hasAttribute("hidden");

    if (!token || !dashboardVisible) return;

    reloadAdminReports().catch((e) => {
      console.error("admin auto refresh error", e);
    });
  }, 20000);
}


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

  await loadCurrentAdmin();
  showAdminView(defaultAdminView());

  adminToast("Zalogowano do panelu administratora.");
  startAdminAutoRefresh();
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

  loadCurrentAdmin().catch(() => {});
  showAdminView(defaultAdminView());

  startAdminAutoRefresh();
})();


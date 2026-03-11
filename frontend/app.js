/* =========================================================
USLY — JS FINAL (v11) — SPÓJNY Z HTML v11 (PL ONLY)
CEL: UI demo + przygotowanie pod backend (spójne ID, stan, hooki)
========================================================= */

/* ------------------------- API Config -------------------------- */
// Prod: ustawimy na URL backendu z Render (osobna domena)
// Local: http://127.0.0.1:8001 (jak dziś uruchamiasz uvicorn)
const API_BASE_URL =
  window.USLY_API_BASE_URL ||
  (location.hostname.includes("onrender.com")
    ? "https://usly-backend-v2.onrender.com"
    : "https://usly-backend-v2.onrender.com");

// expose for api.js (plain scripts)
window.API_BASE_URL = API_BASE_URL;


/* ------------------------- App State -------------------------- */
const App = {
  lang: "pl", // PL only (zgodnie z wymaganiem "brak wersji angielskiej")
  role: "user", // 'user' | 'partner'
  isLoggedIn: false,
  history: ["S0_WELCOME"],
  currentView: "S0_WELCOME",

  // Sub-states / filters
  eventsTab: "nearby", // 'nearby' | 'followed'

  // Profile (demo)
  user: {
    plan: "free", // free | plus | premium | vip
    nick: "Ola_88",
    city: "Warszawa",
    age: 24,
    bio: "",
    interests: ["kawa", "kino", "spacer"],
    prefAgeFrom: 18,
    prefAgeTo: 35,
    geo: { lat: "", lng: "" },
    avatarEmoji: "🙂",
  },

  partner: {
    plan: "free", // free | pro | premium | enterprise
    company: "Kawiarnia Aurora",
    category: "gastro",
    city: "Warszawa",
    about: "",
    logoEmoji: "🏷️",
  },

  // Demo data
  people: [
    { id: "u1", nick: "Maja", city: "Warszawa", age: 26, interests: ["kawa", "joga", "muzyka"], emoji: "🌸" },
    { id: "u2", nick: "Alex", city: "Warszawa", age: 29, interests: ["kino", "gry", "AI"], emoji: "🎧" },
    { id: "u3", nick: "Kasia", city: "Warszawa", age: 24, interests: ["spacer", "psy", "fotografia"], emoji: "📸" },
    { id: "u4", nick: "Tomek", city: "Warszawa", age: 31, interests: ["rower", "góry", "kawa"], emoji: "🚴" },
  ],

  events: [
    {
      id: "e1",
      title: "Koncert na żywo",
      city: "Warszawa",
      when: "Sobota 18:00",
      where: "Centrum",
      interest: "muzyka",
      desc: "Wieczór z muzyką na żywo i luźną atmosferą.",
      paidMode: "paid_fixed",
      price: 49,
      priceFrom: null,
      priceTo: null,
      ticketLink: "https://example.com",
      saved: false,
      interested: false,
      organizer: { id: "p1", name: "Klub Aurora" },
    },
    {
      id: "e2",
      title: "Poranna joga",
      city: "Warszawa",
      when: "Niedziela 09:00",
      where: "Park",
      interest: "joga",
      desc: "Spokojna joga na świeżym powietrzu. Weź matę.",
      paidMode: "free",
      price: 0,
      priceFrom: null,
      priceTo: null,
      ticketLink: "https://example.com",
      saved: false,
      interested: false,
      organizer: { id: "p2", name: "Studio Balance" },
    },
    {
      id: "e3",
      title: "Wieczór planszówek",
      city: "Warszawa",
      when: "Piątek 19:00",
      where: "Kawiarnia",
      interest: "planszówki",
      desc: "Poznaj ludzi przy grach — bez spiny, z uśmiechem.",
      paidMode: "paid_range",
      price: null,
      priceFrom: 15,
      priceTo: 30,
      ticketLink: "https://example.com",
      saved: false,
      interested: false,
      organizer: { id: "p1", name: "Kawiarnia Aurora" },
    },
  ],

  // Group model: interestTag used for filtering by profile interests
  groups: [
    { id: "g1", title: "Kawosze Warszawa", interestTag: "kawa", members: 128, desc: "Nowe kawiarnie, spotkania, degustacje." },
    { id: "g2", title: "Kino i seriale", interestTag: "kino", members: 214, desc: "Polecajki, seanse, dyskusje." },
    { id: "g3", title: "Spacery i miasta", interestTag: "spacer", members: 92, desc: "Trasy, parki, małe odkrycia." },
    { id: "g4", title: "AI & Tech", interestTag: "AI", members: 301, desc: "Nowinki, projekty, dyskusje." },
    { id: "g5", title: "Fotografia", interestTag: "fotografia", members: 175, desc: "Kadry, sprzęt, sesje." },
  ],

  chats: [
    {
      id: "c1",
      with: { id: "u2", nick: "Alex", emoji: "🎧" },
      last: "Jasne, możemy wyskoczyć na kawę 🙂",
      unread: 2,
      messages: [
        { from: "them", text: "Hej! Widziałem, że lubisz kino." },
        { from: "me", text: "Tak! Masz coś do polecenia?" },
        { from: "them", text: "Ostatnio mega siadło mi sci-fi 🙂" },
      ],
    },
    {
      id: "c2",
      with: { id: "u1", nick: "Maja", emoji: "🌸" },
      last: "W sobotę jestem w centrum!",
      unread: 0,
      messages: [
        { from: "them", text: "Cześć! Też lubię jogę." },
        { from: "me", text: "Super! Chodzisz gdzieś na zajęcia?" },
      ],
    },
  ],

  // Working selection
  selectedPersonId: null,
  selectedEventId: null,
  selectedChatId: null,
  selectedGroupId: null,
};

/* ------------------------- DOM Helpers -------------------------- */
const $ = (id) => document.getElementById(id);

function safeSetText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function show(el) { if (el) el.style.display = ""; }
function hide(el) { if (el) el.style.display = "none"; }

/* ------------------------- Navigation -------------------------- */
function go(viewId) {
  if (!viewId) return;
  const current = App.currentView;
  if (current === viewId) return;

  // Hide all
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));

  const next = $(viewId);
  if (!next) {
    toast(`Brak widoku: ${viewId}`);
    return;
  }
  next.classList.add("active");

  App.currentView = viewId;
  App.history.push(viewId);

  if (viewId === "S10_SETTINGS") {
    if ($("setNick")) $("setNick").value = App.user.nick || "";
    if ($("setBio")) $("setBio").value = App.user.bio || "";
    if ($("setCity")) $("setCity").value = App.user.city || "";
    if ($("setPrefAgeFrom")) $("setPrefAgeFrom").value = String(App.user.prefAgeFrom);
    if ($("setPrefAgeTo")) $("setPrefAgeTo").value = String(App.user.prefAgeTo);
    safeSetText("setPrefAgeFromVal", String(App.user.prefAgeFrom));
    safeSetText("setPrefAgeToVal", String(App.user.prefAgeTo));
  }

  // Render after navigation
  renderAll();
}

function back() {
  if (App.history.length <= 1) return go("S0_WELCOME");
  // Remove current
  App.history.pop();
  const prev = App.history[App.history.length - 1] || "S0_WELCOME";

  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  const prevEl = $(prev);
  if (prevEl) prevEl.classList.add("active");
  App.currentView = prev;

  renderAll();
}

/* ------------------------- Toast -------------------------- */
let toastTimer = null;
function toast(message) {
  const el = $("toast");
  if (!el) return;
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2200);
}

/* ------------------------- Modal -------------------------- */
function openModal(title, html) {
  const overlay = $("modalOverlay");
  const body = $("modalBody");
  const ttl = $("modalTitle");
  if (!overlay || !body || !ttl) return;

  ttl.textContent = title || "USLY";
  body.innerHTML = html || "";
  overlay.classList.add("show");
  overlay.setAttribute("aria-hidden", "false");
}

function closeModal() {
  const overlay = $("modalOverlay");
  if (!overlay) return;
  overlay.classList.remove("show");
  overlay.setAttribute("aria-hidden", "true");
}

/* ------------------------- Bug Report (UI -> backend hook) -------------------------- */
// Minimal UI for "Zgłoś błąd" button added in S10_SETTINGS.
// Does not remove/alter any existing behavior.
function openBugReport() {
  openModal("Zgłoś błąd", `
    <div class="tStrong">Zgłoszenie błędu</div>
    <div class="sectionSub mt10">Opisz krótko problem. To trafia do zespołu (na testach).</div>
    <label class="mt12">Co nie działa?</label>
    <textarea id="bugReportText" maxlength="1000" placeholder="Np. Po kliknięciu Zapisz zmiany nic się nie dzieje..."></textarea>
    <div class="charHint"><span id="bugReportCount">0</span>/1000</div>
    <button class="btn mt16" type="button" onclick="submitBugReport()">Wyślij</button>
  `);

  const ta = $("bugReportText");
  const cnt = $("bugReportCount");
  if (ta && cnt) {
    const upd = () => (cnt.textContent = String(ta.value.length));
    ta.addEventListener("input", upd);
    upd();
    // autofocus
    setTimeout(() => ta.focus(), 0);
  }
}

function submitBugReport() {
  const ta = $("bugReportText");
  const message = (ta?.value || "").trim();
  if (!message) {
    toast("Opisz proszę problem");
    return;
  }

  // Backend hook (optional): set window.USLY_API_BASE to enable sending.
  // Example: window.USLY_API_BASE = "https://api.example.com";
  const base = window.USLY_API_BASE;
  if (base) {
    fetch(String(base).replace(/\/$/, "") + "/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "bug",
        message,
        // Minimal context to help diagnose (safe for MVP tests)
        view: App.currentView,
        role: App.role,
      }),
    })
      .then(async (r) => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        toast("Dzięki! Zgłoszenie wysłane.");
        closeModal();
      })
      .catch(() => {
        toast("Nie udało się wysłać (demo)");
        closeModal();
      });
    return;
  }

  // Demo fallback
  toast("Dzięki! Zgłoszenie zapisane (demo)");
  closeModal();
}

/* ------------------------- Role Selection -------------------------- */
function selectRole(role) {
  if (role !== "user" && role !== "partner") return;
  App.role = role;

  // Toggle segmented buttons (where present)
  const pairs = [
    ["roleUserBtn", "rolePartnerBtn"],
    ["roleUserBtnLogin", "rolePartnerBtnLogin"],
    ["roleUserBtn2", "rolePartnerBtn2"],
  ];
  pairs.forEach(([u, p]) => {
    const uEl = $(u), pEl = $(p);
    if (!uEl || !pEl) return;
    if (role === "user") {
      uEl.classList.add("on"); pEl.classList.remove("on");
    } else {
      pEl.classList.add("on"); uEl.classList.remove("on");
    }
  });

  // Labels
  safeSetText("roleLabelLogin", role === "user" ? "Towarzysz" : "Organizator");
  safeSetText("roleLabelRegister", role === "user" ? "Towarzysz" : "Organizator");
  safeSetText("regSubLine", role === "user"
    ? "Stwórz konto Towarzysza i ustaw profil."
    : "Stwórz konto Organizatora i ustaw profil.");

  // Show/Hide registration blocks
  const userBox = $("regUserBox");
  const partnerBox = $("regPartnerBox");
  if (userBox && partnerBox) {
    if (role === "user") { show(userBox); hide(partnerBox); }
    else { hide(userBox); show(partnerBox); }
  }

  // Settings sections
  const settingsUser = $("settingsUserBox");
  const settingsPartner = $("settingsPartnerBox");
  if (settingsUser && settingsPartner) {
    if (role === "user") { show(settingsUser); hide(settingsPartner); }
    else { hide(settingsUser); show(settingsPartner); }
  }

  // Plans sections
  const plansUserOnly = $("plansUserOnly");
  const plansPartnerOnly = $("plansPartnerOnly");
  if (plansUserOnly && plansPartnerOnly) {
    if (role === "user") { show(plansUserOnly); hide(plansPartnerOnly); }
    else { hide(plansUserOnly); show(plansPartnerOnly); }
  }

  // Update tabbars visibility (still controlled by login class + role)
  updateTabbars();

  // Re-render pills etc.
  renderAll();
}

/* ------------------------- Login / Signup (Demo) -------------------------- */
async function loginPrimary() {
  const email = $("loginId")?.value?.trim();
  const password = $("loginPass")?.value?.trim();

  if (!email || !password) {
    toast("Podaj email i hasło");
    return;
  }

  try {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!data?.success || !data?.data?.access_token) {
      toast(data?.error?.message || "Błąd logowania");
      return;
    }

    localStorage.setItem("usly_token", data.data.access_token);

    const me = await apiFetch("/auth/me");
    App.role = me?.role === "partner" ? "partner" : "user";
    App.isLoggedIn = true;

    if (App.role === "user") {
      const profile = await apiFetch("/users/me");
      if (profile?.success && profile?.data) {
        App.user.nick = profile.data.nick || App.user.nick;
        App.user.city = profile.data.miasto || App.user.city;
        App.user.bio = profile.data.bio || "";
        App.user.interests = Array.isArray(profile.data.zainteresowania) ? profile.data.zainteresowania : [];
        App.user.prefAgeFrom = profile.data.age_min ?? App.user.prefAgeFrom;
        App.user.prefAgeTo = profile.data.age_max ?? App.user.prefAgeTo;
      }
    }

    $("appRoot")?.classList.add("isLoggedIn");
updateTabbars();

if (App.role === "user") {
  await Promise.all([loadNearbyPeople(), loadEvents(), loadGroups()]);
}

renderAll();

toast("Zalogowano");
if (App.role === "user") go("S4_NEARBY");
else go("S9_PARTNER");
  } catch (err) {
    toast(err?.userMessage || "Błąd logowania");
  }
}

function loginSocial(provider) {
  toast("Logowanie społecznościowe będzie dostępne wkrótce");
}

function signupSocial(provider) {
  toast("Rejestracja społecznościowa będzie dostępna wkrótce");
}

function logout() {
  App.isLoggedIn = false;
  $("appRoot")?.classList.remove("isLoggedIn");

  // Reset tabbars display (both hidden until login)
  hide($("tabbarUser"));
  hide($("tabbarPartner"));

  toast("Wylogowano");
  App.history = ["S0_WELCOME"];
  go("S0_WELCOME");
}

function openForgot() {
  openModal("Odzyskiwanie hasła", `
    <div class="tStrong">Reset hasła</div>
    <div class="sectionSub">W wersji demo nie wysyłamy maili. W backendzie: token resetu + email.</div>
    <label class="mt12">Email</label>
    <input type="email" placeholder="np. ola@email.com" />
    <button class="btn mt16" type="button" onclick="toast('Wysłano link (demo)')">Wyślij link</button>
  `);
}

/* ------------------------- Registration -------------------------- */
async function registerPrimary() {
  const terms = $("acceptTerms")?.checked;
  const rodo = $("acceptRodo")?.checked;
  if (!terms || !rodo) {
    toast("Zaznacz wymagane zgody (*)");
    return;
  }

  const email = $("regEmail")?.value?.trim();
  const pass = $("regPass")?.value?.trim();
  if (!email || !pass || pass.length < 8) {
    toast("Uzupełnij email i hasło (min. 8 znaków)");
    return;
  }

  let dob = "";

  if (App.role === "user") {
    const city = $("regCity")?.value?.trim();
    const nick = $("regNick")?.value?.trim();
    const from = Number($("regPrefAgeFrom")?.value || 16);
    const to = Number($("regPrefAgeTo")?.value || 99);

    const dobEl = $("regBirthDate");
    const errEl = $("ageError");
    dob = (dobEl?.value || "").trim();

    function showAgeError(msg) {
      if (errEl) {
        errEl.style.display = "block";
        errEl.textContent = msg;
      }
      toast(msg);
    }

    function hideAgeError() {
      if (errEl) errEl.style.display = "none";
    }

    if (!dob) {
      showAgeError("Podaj datę urodzenia.");
      return;
    }

    const birth = new Date(dob);
    if (Number.isNaN(birth.getTime())) {
      showAgeError("Nieprawidłowa data urodzenia.");
      return;
    }

    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;

    if (age < 16) {
      showAgeError("Nie możesz się zarejestrować – wymagane jest ukończone 16 lat.");
      return;
    }

    hideAgeError();

    if (!city || !nick) {
      toast("Uzupełnij datę urodzenia, miasto i nick");
      return;
    }

    App.user.city = city;
    App.user.age = age;
    App.user.dob = dob;
    App.user.nick = nick;
    App.user.prefAgeFrom = Math.min(from, to);
    App.user.prefAgeTo = Math.max(from, to);
  } else {
    const company = $("regCompany")?.value?.trim();
    const category = $("regCategory")?.value;
    const city = $("regCityPartner")?.value;
    const dobEl = $("regBirthDatePartner");
    dob = (dobEl?.value || "").trim();

    if (!dob) {
      toast("Podaj datę urodzenia.");
      return;
    }

    if (!company || !city) {
      toast("Uzupełnij nazwę i miasto organizatora");
      return;
    }

    App.partner.company = company;
    App.partner.category = category || "inne";
    App.partner.city = city || "Warszawa";
    App.partner.about = $("regOrgAbout")?.value?.trim() || "";
  }

  try {
    const data = await apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password: pass,
        dob,
        role: App.role === "partner" ? "partner" : "user",
        accept_terms: true,
      }),
    });

    if (!data?.success || !data?.data?.id) {
      toast(data?.error?.message || "Nie udało się utworzyć konta");
      return;
    }

    const loginData = await apiFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password: pass }),
    });

    if (!loginData?.success || !loginData?.data?.access_token) {
      toast("Konto utworzone, ale nie udało się zalogować automatycznie");
      go("S1_LOGIN");
      return;
    }

    localStorage.setItem("usly_token", loginData.data.access_token);
    App.isLoggedIn = true;
    $("appRoot")?.classList.add("isLoggedIn");
    updateTabbars();

    toast("Konto utworzone i zalogowano");
    if (App.role === "user") go("S3_PROFILE_SETUP");
    else go("S9_PARTNER");
  } catch (err) {
    toast(err?.userMessage || "Nie udało się utworzyć konta");
  }
}

/* ------------------------- Plans -------------------------- */
function setUserPlan(plan) {
  const allowed = ["free", "plus", "premium", "vip"];
  if (!allowed.includes(plan)) return;

  App.user.plan = plan;

  // Update segmented UI wherever exists
  const btnIds = [
    "uplan_free", "uplan_plus", "uplan_premium", "uplan_vip",
    "uplan_free_set", "uplan_plus_set", "uplan_premium_set", "uplan_vip_set",
  ];
  btnIds.forEach(id => {
    const b = $(id);
    if (!b) return;
    const isOn = b.dataset.plan === plan;
    b.classList.toggle("on", isOn);
    b.classList.toggle("active", isOn);
  });

  // Plan pills
  safeSetText("planPillSetup", plan.toUpperCase());
  toast(`Wybrano plan: ${plan.toUpperCase()}`);
  renderAll();
}

function setPartnerPlan(plan) {
  const allowed = ["free", "pro", "premium", "enterprise"];
  if (!allowed.includes(plan)) return;

  App.partner.plan = plan;

  const btnIds = [
    "pplan_free", "pplan_pro", "pplan_premium", "pplan_enterprise",
    "pplan_free_set", "pplan_pro_set", "pplan_premium_set", "pplan_enterprise_set",
  ];
  btnIds.forEach(id => {
    const b = $(id);
    if (!b) return;
    const isOn = b.dataset.plan === plan;
    b.classList.toggle("on", isOn);
    b.classList.toggle("active", isOn);
  });

  safeSetText("partnerPlanPill", plan.toUpperCase());
  toast(`Wybrano plan: ${plan.toUpperCase()}`);
  renderAll();
}

/* ------------------------- Settings -------------------------- */
async function saveSettings() {
  const nick = $("setNick")?.value?.trim() || App.user.nick;
  const bio = $("setBio")?.value?.trim() || "";
  const city = $("setCity")?.value?.trim() || App.user.city;

  const f = Number($("setPrefAgeFrom")?.value || App.user.prefAgeFrom);
  const t = Number($("setPrefAgeTo")?.value || App.user.prefAgeTo);
  const ageMin = Math.min(f, t);
  const ageMax = Math.max(f, t);

  try {
    const data = await apiFetch("/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nick: nick,
        miasto: city,
        bio: bio,
        zainteresowania: Array.isArray(App.user.interests) ? App.user.interests : [],
        age_min: ageMin,
        age_max: ageMax,
      }),
    });

    if (!data?.success || !data?.data) {
      toast(data?.error?.message || "Nie udało się zapisać ustawień");
      return;
    }

    App.user.nick = data.data.nick || nick;
    App.user.bio = data.data.bio || bio;
    App.user.city = data.data.miasto || city;
    App.user.prefAgeFrom = data.data.age_min ?? ageMin;
    App.user.prefAgeTo = data.data.age_max ?? ageMax;

    toast("Zapisano ustawienia");
    renderAll();
  } catch (err) {
    toast(err?.userMessage || "Nie udało się zapisać ustawień");
  }
}

function savePartnerSettings() {
  App.partner.company = $("setOrgCompany")?.value?.trim() || App.partner.company;
  App.partner.category = $("setOrgCategory")?.value || App.partner.category;
  App.partner.city = $("setOrgCity")?.value || App.partner.city;
  App.partner.about = $("setOrgAbout")?.value?.trim() || "";

  toast("Zapisano ustawienia organizatora (demo)");
  renderAll();
}

/* ------------------------- Terms / Privacy -------------------------- */
function openTerms() {
  window.open("legal/terms_pl.docx", "_blank");
}

function openRodo() {
  window.open("legal/privacy_pl.docx", "_blank");
}

/* ------------------------- Avatar / Photo hooks -------------------------- */
function openAddPhoto() {
  openModal("Dodaj zdjęcie", `
    <div class="tStrong">Upload zdjęcia</div>
    <div class="sectionSub mt10">Demo UI. Backend: upload + storage + URL w profilu.</div>
    <input type="file" accept="image/*" class="mt12" />
    <button class="btn mt16" type="button" onclick="toast('Zapisano (demo)'); closeModal();">Zapisz</button>
  `);
}

function openAvatarAI() {
  openModal("Stwórz awatar", `
    <div class="tStrong">Awatar AI</div>
    <div class="sectionSub mt10">Demo UI. Backend: prompt → generator → zapis awatara.</div>
    <label class="mt12">Opis awatara</label>
    <input id="aiAvatarPrompt" type="text" placeholder="np. neonowy, minimalistyczny, uśmiechnięty" />
    <button class="btn mt16" type="button" onclick="toast('Awatar utworzony (demo)'); closeModal();">Generuj</button>
  `);
}

/* ------------------------- Profile Setup -------------------------- */
async function finishProfileSetup() {
  const city = $("setupCity")?.value || App.user.city;
  const bio = $("setupBio")?.value?.trim() || "";

  try {
    const data = await apiFetch("/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        miasto: city,
        bio: bio,
      }),
    });

    if (!data?.success || !data?.data) {
      toast(data?.error?.message || "Nie udało się zapisać profilu");
      return;
    }

    App.user.city = data.data.miasto || city;
    App.user.bio = data.data.bio || bio;

    toast("Profil zapisany");
    go("S4_NEARBY");
  } catch (err) {
    toast(err?.userMessage || "Nie udało się zapisać profilu");
  }
}

/* ------------------------- Nearby / Map -------------------------- */
function openMapMarker(type, index) {
  if (type === "person") {
    const person = App.people[index];
    if (!person) return;
    App.selectedPersonId = person.id;
    openPerson(person.id);
  } else {
    const ev = App.events[index];
    if (!ev) return;
    openEvent(ev.id);
  }
}

/* ------------------------- Person Profile -------------------------- */
function openPerson(personId) {
  const p = App.people.find(x => x.id === personId);
  if (!p) return;

  App.selectedPersonId = personId;

  safeSetText("personTitle", p.nick);
  safeSetText("personNick", p.nick);
  safeSetText("personMeta", `${p.city} • ${p.age} lat`);
  const avatar = $("personAvatar");
  if (avatar) avatar.textContent = p.emoji || "🙂";

  const chips = $("personInterests");
  if (chips) {
    chips.innerHTML = "";
    p.interests.forEach(tag => chips.appendChild(makeChip(`#${tag}`, null)));
  }

  go("S5_PERSON_PROFILE");
}

function openPersonMenu() {
  openModal("Opcje", `
    <button class="btn secondary" type="button" onclick="toast('Zgłoszono (demo)'); closeModal();">Zgłoś</button>
    <button class="btn danger mt12" type="button" onclick="toast('Zablokowano (demo)'); closeModal();">Zablokuj</button>
  `);
}

function startChatFromProfile() {
  const pid = App.selectedPersonId;
  if (!pid) return;
  const p = App.people.find(x => x.id === pid);
  if (!p) return;

  // Create or open existing chat
  let chat = App.chats.find(c => c.with.id === pid);
  if (!chat) {
    chat = {
      id: `c${Date.now()}`,
      with: { id: pid, nick: p.nick, emoji: p.emoji },
      last: "",
      unread: 0,
      messages: [{ from: "them", text: "Hej! 🙂" }],
    };
    App.chats.unshift(chat);
  }

  App.selectedChatId = chat.id;
  openChat(chat.id);
}

function addFriendFromProfile() {
  toast("Dodano do znajomych (demo)");
}

/* ------------------------- Chats -------------------------- */
function openChat(chatId) {
  const chat = App.chats.find(c => c.id === chatId);
  if (!chat) return;
  App.selectedChatId = chatId;

  safeSetText("chatTitle", chat.with.nick);

  // Mark read
  chat.unread = 0;

  renderChatThread();
  go("S6B_CHAT_THREAD");
}

function renderChatThread() {
  const chat = App.chats.find(c => c.id === App.selectedChatId);
  const box = $("chatBubbles");
  if (!box || !chat) return;

  box.innerHTML = "";
  chat.messages.forEach(m => {
    const div = document.createElement("div");
    div.className = `bubble ${m.from === "me" ? "me" : "them"}`;
    div.textContent = m.text;
    box.appendChild(div);
  });

  // Scroll bottom
  setTimeout(() => {
    box.parentElement?.scrollTo({ top: box.parentElement.scrollHeight, behavior: "smooth" });
  }, 0);
}

function sendChat() {
  const inp = $("chatInput");
  const text = inp?.value?.trim();
  if (!text) return;

  const chat = App.chats.find(c => c.id === App.selectedChatId);
  if (!chat) return;

  chat.messages.push({ from: "me", text });
  chat.last = text;
  inp.value = "";

  renderChatThread();
  renderChatList();
}

function openChatMenu() {
  openModal("Menu czatu", `
    <button class="btn secondary" type="button" onclick="toast('Wyciszono (demo)'); closeModal();">Wycisz</button>
    <button class="btn danger mt12" type="button" onclick="toast('Zablokowano (demo)'); closeModal();">Zablokuj</button>
  `);
}

/* ------------------------- Events -------------------------- */
function setEventsTab(tab) {
  if (tab !== "nearby" && tab !== "followed") return;
  App.eventsTab = tab;

  $("eventsTabNearby")?.classList.toggle("on", tab === "nearby");
  $("eventsTabFollowed")?.classList.toggle("on", tab === "followed");

  renderEventsList();
}

function openEvent(eventId) {
  const ev = App.events.find(e => e.id === eventId);
  if (!ev) return;
  App.selectedEventId = eventId;

  safeSetText("eventTitleTop", ev.title);
  safeSetText("evTitle", ev.title);
  safeSetText("evMeta", `${ev.city} • ${ev.when} • ${ev.where}`);

  const chips = $("evInterestChips");
  if (chips) {
    chips.innerHTML = "";
    chips.appendChild(makeChip(`#${ev.interest}`, null));
  }

  safeSetText("evDesc", ev.desc);

  // ticket display
  const typeEl = $("evTicketType");
  const pricePill = $("evTicketPricePill");
  const lineEl = $("evTicketPriceLine");
  const linkEl = $("evTicketLink");

  if (ev.paidMode === "free") {
    if (typeEl) typeEl.textContent = "Bezpłatne";
    if (pricePill) pricePill.textContent = "0 zł";
    if (lineEl) lineEl.textContent = "Wejście bezpłatne — sprawdź szczegóły u organizatora.";
  } else if (ev.paidMode === "paid_fixed") {
    if (typeEl) typeEl.textContent = "Płatne — cena stała";
    if (pricePill) pricePill.textContent = `${ev.price} zł`;
    if (lineEl) lineEl.textContent = `Cena: ${ev.price} zł (zakup / rezerwacja poza aplikacją).`;
  } else {
    if (typeEl) typeEl.textContent = "Płatne — przedział";
    if (pricePill) pricePill.textContent = `${ev.priceFrom}–${ev.priceTo} zł`;
    if (lineEl) lineEl.textContent = `Cena: ${ev.priceFrom}–${ev.priceTo} zł (zakup / rezerwacja poza aplikacją).`;
  }

  if (linkEl) linkEl.href = ev.ticketLink || "#";

  // Badge (plan) - demo: show user's plan
  safeSetText("evBadge", App.user.plan.toUpperCase());

  go("S7B_EVENT_DETAIL");
}

function toggleSaveEvent() {
  const ev = App.events.find(e => e.id === App.selectedEventId);
  if (!ev) return;
  ev.saved = !ev.saved;
  toast(ev.saved ? "Zapisano wydarzenie" : "Usunięto z zapisanych");
  renderEventsList();
  renderNearby();
}

function toggleInterestedEvent() {
  const ev = App.events.find(e => e.id === App.selectedEventId);
  if (!ev) return;
  ev.interested = !ev.interested;
  toast(ev.interested ? "Dodano jako zainteresowany" : "Usunięto zainteresowanie");
  renderEventsList();
  renderNearby();
}

function openShare() {
  openModal("Udostępnij", `
    <div class="tStrong">Udostępnianie</div>
    <div class="sectionSub mt10">W wersji produkcyjnej: deep link / share sheet.</div>
    <button class="btn mt16" type="button" onclick="toast('Skopiowano link (demo)'); closeModal();">Skopiuj link</button>
  `);
}

function openEventMenu() {
  openModal("Opcje wydarzenia", `
    <button class="btn secondary" type="button" onclick="toast('Zgłoszono (demo)'); closeModal();">Zgłoś</button>
    <button class="btn danger mt12" type="button" onclick="toast('Ukryto (demo)'); closeModal();">Ukryj</button>
  `);
}

function openChatWithOrganizer() {
  const ev = App.events.find(e => e.id === App.selectedEventId);
  if (!ev) return;
  toast(`Czat z organizatorem: ${ev.organizer.name} (demo)`);
}

/* ------------------------- Groups -------------------------- */
function openGroup(groupId) {
  const g = App.groups.find(x => x.id === groupId);
  if (!g) return;
  App.selectedGroupId = groupId;

  safeSetText("groupTitle", g.title);

  // Demo messages
  const box = $("groupBubbles");
  if (box) {
    box.innerHTML = "";
    const msgs = [
      { from: "them", text: `Witaj w grupie „${g.title}”!` },
      { from: "them", text: `Temat: #${g.interestTag}.` },
      { from: "me", text: "Cześć wszystkim! 🙂" },
    ];
    msgs.forEach(m => {
      const div = document.createElement("div");
      div.className = `bubble ${m.from === "me" ? "me" : "them"}`;
      div.textContent = m.text;
      box.appendChild(div);
    });
  }

  go("S8B_GROUP_THREAD");
}

function sendGroup() {
  const inp = $("groupInput");
  const text = inp?.value?.trim();
  if (!text) return;

  const box = $("groupBubbles");
  if (!box) return;

  const div = document.createElement("div");
  div.className = "bubble me";
  div.textContent = text;
  box.appendChild(div);
  inp.value = "";

  setTimeout(() => {
    box.parentElement?.scrollTo({ top: box.parentElement.scrollHeight, behavior: "smooth" });
  }, 0);
}

function openGroupMenu() {
  openModal("Menu grupy", `
    <button class="btn secondary" type="button" onclick="toast('Wyciszono (demo)'); closeModal();">Wycisz</button>
    <button class="btn danger mt12" type="button" onclick="toast('Opuszczono grupę (demo)'); closeModal();">Opuść</button>
  `);
}

// Punkt 9: dodanie znajomego do grupy, nawet jeśli jej nie widzi (hook)
function openInviteFriendToGroup() {
  const g = App.groups.find(x => x.id === App.selectedGroupId);
  if (!g) return;

  const similarFriends = suggestPeopleByInterest(g.interestTag).slice(0, 6);

  openModal("Dodaj znajomego do grupy", `
    <div class="tStrong">Wybierz znajomego</div>
    <div class="sectionSub mt10">
      Docelowo: backend sprawdza uprawnienia i dodaje / wysyła zaproszenie.
    </div>
    <div class="mt16">
      ${similarFriends.map(p => `
        <div class="listItem" style="margin-bottom:10px; cursor:default;">
          <div class="listTop">
            <div class="listLeft">
              <div class="listAvatar">${p.emoji}</div>
              <div style="min-width:0;">
                <div class="listTitle">${p.nick}</div>
                <div class="listMeta">Wspólne: ${commonInterests(p).slice(0,3).map(x => `#${x}`).join(" ")}</div>
              </div>
            </div>
            <div class="listRight">
              <button class="btn small" type="button" onclick="toast('Dodano (demo)'); closeModal();">Dodaj</button>
            </div>
          </div>
        </div>
      `).join("")}
    </div>
  `);
}

/* ------------------------- Organizer: create / events list -------------------------- */
function publishPartnerEvent() {
  if (App.role !== "partner") {
    toast("To jest dostępne tylko dla organizatora");
    return;
  }

  const title = $("peTitle")?.value?.trim();
  const city = $("peCity")?.value?.trim();
  const when = $("peWhen")?.value?.trim();
  const where = $("peWhere")?.value?.trim();
  const interest = $("peInterest")?.value?.trim();
  const desc = $("peDesc")?.value?.trim();

  if (!title || !city || !when || !where || !interest) {
    toast("Uzupełnij: nazwa, miasto, kiedy, gdzie, hashtag");
    return;
  }

  const paidMode = $("pePaidMode")?.value || "free";
  const price = Number($("pePrice")?.value || 0);
  const priceFrom = Number($("pePriceFrom")?.value || 0);
  const priceTo = Number($("pePriceTo")?.value || 0);
  const ticketLink = $("peTicketLink")?.value?.trim() || "https://example.com";

  const ev = {
    id: `e${Date.now()}`,
    title, city, when, where,
    interest: interest.replace(/^#/, ""),
    desc: desc || "—",
    paidMode,
    price: paidMode === "paid_fixed" ? price : (paidMode === "free" ? 0 : null),
    priceFrom: paidMode === "paid_range" ? priceFrom : null,
    priceTo: paidMode === "paid_range" ? priceTo : null,
    ticketLink,
    saved: false,
    interested: false,
    organizer: { id: "p_me", name: App.partner.company },
  };

  App.events.unshift(ev);

  toast("Opublikowano wydarzenie (demo)");
  // Clear minimal
  ["peTitle","peCity","peWhen","peWhere","peInterest","peDesc","pePrice","pePriceFrom","pePriceTo","peTicketLink"].forEach(id => {
    const el = $(id);
    if (el) el.value = "";
  });

  go("S9_PARTNER_EVENTS");
}

/* ------------------------- Notifications -------------------------- */
function renderNotifications() {
  const list = $("notifList");
  if (!list) return;

  // Demo notifications
  const items = [];
  if (App.role === "user") {
    items.push({ title: "Nowa propozycja osoby", body: "Ktoś z podobnymi # jest w okolicy." });
    items.push({ title: "Wydarzenie jutro", body: "Masz zapisane wydarzenie — sprawdź godzinę." });
  } else {
    items.push({ title: "Nowe zainteresowanie", body: "Ktoś oznaczył się jako zainteresowany Twoim wydarzeniem." });
    items.push({ title: "Nowa wiadomość", body: "Użytkownik napisał do Ciebie." });
  }

  list.innerHTML = items.map(n => `
    <div class="listItem" style="cursor:default;">
      <div class="listTitle">${n.title}</div>
      <div class="listBody">${n.body}</div>
    </div>
  `).join("");
}

/* ------------------------- Rendering Lists -------------------------- */
function renderNearby() {
  // People list in nearby tab
  const pList = $("nearbyPeopleList");
  if (pList) {
    const q = ($("nearbyPeopleSearch")?.value || "").trim().toLowerCase();
    const people = App.people
      .filter(p => !q || p.nick.toLowerCase().includes(q))
      .slice(0, 12);

    pList.innerHTML = people.map(p => `
      <div class="listItem" onclick="openPerson('${p.id}')">
        <div class="listTop">
          <div class="listLeft">
            <div class="listAvatar">${p.emoji}</div>
            <div style="min-width:0;">
              <div class="listTitle">${p.nick}</div>
              <div class="listMeta">${p.city} • ${p.age} lat</div>
            </div>
          </div>
          <div class="listRight">
            <div class="listTag">${sharedScore(p)}% wspólne</div>
          </div>
        </div>
        <div class="listBody">${p.interests.slice(0,3).map(t => `#${t}`).join(" ")}</div>
      </div>
    `).join("");
  }

  // Events list in nearby tab
  const eList = $("nearbyEventsList");
  if (eList) {
    const events = App.events.slice(0, 8);
    eList.innerHTML = events.map(ev => `
      <div class="listItem" onclick="openEvent('${ev.id}')">
        <div class="listTop">
          <div class="listLeft">
            <div class="listAvatar">🎫</div>
            <div style="min-width:0;">
              <div class="listTitle">${ev.title}</div>
              <div class="listMeta">${ev.city} • ${ev.when} • ${ev.where}</div>
            </div>
          </div>
          <div class="listRight">
            <div class="listTag ${ev.paidMode === 'free' ? '' : 'paid'}">
              ${ev.paidMode === "free" ? "Bezpłatne" : "Płatne"}
            </div>
          </div>
        </div>
        <div class="listBody">#${ev.interest} • ${ev.saved ? "Zapisane" : "—"} • ${ev.interested ? "Zainteresowany" : "—"}</div>
      </div>
    `).join("");
  }
}

function renderEventsList() {
  const list = $("eventsList");
  if (!list) return;

  const q = ($("eventsSearch")?.value || "").trim().toLowerCase();

  let events = App.events.slice();
  if (App.eventsTab === "followed") {
    // Demo: "followed" = saved or interested
    events = events.filter(e => e.saved || e.interested);
  }

  if (q) {
    const qClean = q.replace("#", "");
    events = events.filter(e =>
      e.title.toLowerCase().includes(q) ||
      e.interest.toLowerCase().includes(qClean)
    );
  }

  list.innerHTML = events.map(ev => `
    <div class="listItem" onclick="openEvent('${ev.id}')">
      <div class="listTop">
        <div class="listLeft">
          <div class="listAvatar">🎫</div>
          <div style="min-width:0;">
            <div class="listTitle">${ev.title}</div>
            <div class="listMeta">${ev.city} • ${ev.when} • ${ev.where}</div>
          </div>
        </div>
        <div class="listRight">
          <div class="listTag ${ev.paidMode === 'free' ? '' : 'paid'}">
            ${ev.paidMode === "free" ? "0 zł" : priceLabel(ev)}
          </div>
        </div>
      </div>
      <div class="listBody">#${ev.interest} • ${ev.saved ? "Zapisane" : "—"} • ${ev.interested ? "Zainteresowany" : "—"}</div>
    </div>
  `).join("");
}

function renderGroups() {
  const list = $("groupList");
  if (!list) return;

  const q = ($("groupSearch")?.value || "").trim().toLowerCase().replace("#", "");

  // Filter by profile interests (punkt 8)
  const userInterests = (App.user.interests || []).map(x => x.toLowerCase());
  let groups = App.groups.filter(g => userInterests.includes(g.interestTag.toLowerCase()));
  if (q) groups = groups.filter(g => g.title.toLowerCase().includes(q) || g.interestTag.toLowerCase().includes(q));

  list.innerHTML = groups.map(g => `
    <div class="listItem" onclick="openGroup('${g.id}')">
      <div class="listTop">
        <div class="listLeft">
          <div class="listAvatar">👥</div>
          <div style="min-width:0;">
            <div class="listTitle">${g.title}</div>
            <div class="listMeta">#${g.interestTag} • ${g.members} osób</div>
          </div>
        </div>
        <div class="listRight">
          <div class="listTag">${g.members}</div>
        </div>
      </div>
      <div class="listBody">${g.desc}</div>
    </div>
  `).join("");

  // Suggestions: people by any of user's interests
  const sug = $("groupPeopleSuggestions");
  if (sug) {
    const ranked = App.people
      .map(p => ({ p, score: commonInterests(p).length }))
      .sort((a,b) => b.score - a.score)
      .filter(x => x.score > 0)
      .slice(0, 6);

    sug.innerHTML = ranked.map(x => `
      <div class="listItem" onclick="openPerson('${x.p.id}')">
        <div class="listTop">
          <div class="listLeft">
            <div class="listAvatar">${x.p.emoji}</div>
            <div style="min-width:0;">
              <div class="listTitle">${x.p.nick}</div>
              <div class="listMeta">Wspólne: ${commonInterests(x.p).slice(0,3).map(t => `#${t}`).join(" ")}</div>
            </div>
          </div>
          <div class="listRight">
            <div class="listTag">${Math.min(99, x.score * 25)}%</div>
          </div>
        </div>
      </div>
    `).join("");
  }
}

function renderChatList() {
  const list = $("chatList");
  if (!list) return;

  const q = ($("chatSearch")?.value || "").trim().toLowerCase();
  const chats = App.chats.filter(c => !q || c.with.nick.toLowerCase().includes(q));

  list.innerHTML = chats.map(c => `
    <div class="listItem ${c.unread ? "unread" : ""}" onclick="openChat('${c.id}')">
      <div class="listTop">
        <div class="listLeft">
          <div class="listAvatar">${c.with.emoji || "💬"}</div>
          <div style="min-width:0;">
            <div class="listTitle">${c.with.nick}</div>
            <div class="listMeta">${c.last || "—"}</div>
          </div>
        </div>
        <div class="listRight">
          ${c.unread ? `<div class="badgeMini">${c.unread}</div>` : ``}
        </div>
      </div>
    </div>
  `).join("");

  // update badge
  const unread = App.chats.reduce((sum,c) => sum + (c.unread || 0), 0);
  const badge = $("badgeChats");
  if (badge) {
    if (unread > 0) {
      badge.style.display = "inline-flex";
      badge.textContent = String(unread);
    } else {
      badge.style.display = "none";
    }
  }
}

function renderPartnerEvents() {
  const list = $("partnerEventsList");
  if (!list) return;

  // In demo: partner sees all events that have organizer name matching company OR all events
  const company = App.partner.company || "";
  const events = App.events.filter(e => e.organizer?.name?.toLowerCase().includes(company.toLowerCase()) || e.organizer?.id === "p_me");

  list.innerHTML = events.map(ev => `
    <div class="listItem" onclick="openEvent('${ev.id}')">
      <div class="listTop">
        <div class="listLeft">
          <div class="listAvatar">🗓️</div>
          <div style="min-width:0;">
            <div class="listTitle">${ev.title}</div>
            <div class="listMeta">${ev.city} • ${ev.when}</div>
          </div>
        </div>
        <div class="listRight">
          <div class="listTag ${ev.paidMode === 'free' ? '' : 'paid'}">${ev.paidMode === "free" ? "0 zł" : priceLabel(ev)}</div>
        </div>
      </div>
      <div class="listBody">#${ev.interest} • Zainteresowani: ${ev.interested ? "1+" : "0"}</div>
    </div>
  `).join("");
}

function renderPartnerMsgList() {
  const list = $("partnerMsgList");
  if (!list) return;

  // Demo: partner messages = reuse chats (placeholder)
  const q = ($("partnerMsgSearch")?.value || "").trim().toLowerCase();
  const chats = App.chats.filter(c => !q || c.with.nick.toLowerCase().includes(q));

  list.innerHTML = chats.map(c => `
    <div class="listItem" onclick="toast('Otwórz wątek (demo)')">
      <div class="listTop">
        <div class="listLeft">
          <div class="listAvatar">${c.with.emoji || "✉️"}</div>
          <div style="min-width:0;">
            <div class="listTitle">${c.with.nick}</div>
            <div class="listMeta">${c.last || "—"}</div>
          </div>
        </div>
      </div>
    </div>
  `).join("");

  // badge
  const badge = $("badgePartnerMsgs");
  if (badge) {
    // demo: sum of unread
    const unread = App.chats.reduce((sum,c) => sum + (c.unread || 0), 0);
    if (unread > 0) {
      badge.style.display = "inline-flex";
      badge.textContent = String(unread);
    } else {
      badge.style.display = "none";
    }
  }
}

/* ------------------------- Interests (chips + suggestions) -------------------------- */
/**
 * We support 3 areas:
 * - Registration user: regInterestInput + regInterestChips + regInterestTypeahead
 * - Profile setup: interestInput + interestChips + interestTypeahead
 * - Settings: setInterestInput + setInterestChips + setInterestTypeahead
 *
 * Input behavior:
 * - User types (optionally with #)
 * - Press Enter or comma => add chip
 * - Clicking suggestion => add chip
 */
function initInterestInputs() {
  const configs = [
    { inputId: "regInterestInput", chipsId: "regInterestChips", taId: "regInterestTypeahead", target: "user" },
    { inputId: "interestInput", chipsId: "interestChips", taId: "interestTypeahead", target: "user" },
    { inputId: "setInterestInput", chipsId: "setInterestChips", taId: "setInterestTypeahead", target: "user" },
    { inputId: "peInterest", chipsId: null, taId: null, target: "event" }, // organizer create uses datalist only
  ];

  const suggestions = getInterestSuggestionsFromDatalist();

  configs.forEach(cfg => {
    const input = $(cfg.inputId);
    if (!input) return;

    // Key handlers
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === "," ) {
        e.preventDefault();
        const val = input.value.trim();
        const cleaned = normalizeTag(val);
        if (!cleaned) return;
        if (cfg.target === "user") addUserInterest(cleaned, cfg.chipsId);
        input.value = "";
        hideTypeahead(cfg.taId);
        renderAll();
      }
      if (e.key === "Escape") hideTypeahead(cfg.taId);
    });

    input.addEventListener("input", () => {
      if (!cfg.taId) return; // no typeahead needed
      const q = normalizeTag(input.value.trim());
      if (!q) { hideTypeahead(cfg.taId); return; }
      const items = suggestions
        .filter(s => s.toLowerCase().startsWith(q.toLowerCase()))
        .slice(0, 12);
      renderTypeahead(cfg.taId, items, (picked) => {
        addUserInterest(picked, cfg.chipsId);
        input.value = "";
        hideTypeahead(cfg.taId);
        renderAll();
      });
    });
  });

  // initial chips render
  renderInterestChips("regInterestChips");
  renderInterestChips("interestChips");
  renderInterestChips("setInterestChips");
}

function getInterestSuggestionsFromDatalist() {
  const dl = $("interestsDatalist");
  if (!dl) return [];
  const opts = Array.from(dl.querySelectorAll("option")).map(o => (o.getAttribute("value") || "").trim()).filter(Boolean);
  // Unique
  return Array.from(new Set(opts));
}

function normalizeTag(val) {
  if (!val) return "";
  return val.replace(/^#/, "").trim().replace(/\s+/g, " ").slice(0, 40);
}

function addUserInterest(tag, chipsId) {
  const t = normalizeTag(tag);
  if (!t) return;
  const exists = App.user.interests.some(x => x.toLowerCase() === t.toLowerCase());
  if (exists) {
    toast("To zainteresowanie już jest dodane");
    return;
  }
  App.user.interests.push(t);
  renderInterestChips(chipsId);
  toast(`Dodano #${t}`);
}

function removeUserInterest(tag, chipsId) {
  const t = normalizeTag(tag);
  App.user.interests = App.user.interests.filter(x => x.toLowerCase() !== t.toLowerCase());
  renderInterestChips(chipsId);
  toast(`Usunięto #${t}`);
}

function renderInterestChips(chipsId) {
  const box = $(chipsId);
  if (!box) return;

  box.innerHTML = "";
  App.user.interests.forEach(t => {
    const chip = makeChip(`#${t}`, () => removeUserInterest(t, chipsId));
    box.appendChild(chip);
  });
}

function makeChip(text, onRemove) {
  const span = document.createElement("div");
  span.className = "chip";
  span.textContent = text;
  if (onRemove) {
    span.title = "Kliknij, aby usunąć";
    span.addEventListener("click", onRemove);
  }
  return span;
}

function renderTypeahead(taId, items, onPick) {
  const box = $(taId);
  if (!box) return;
  if (!items.length) { hideTypeahead(taId); return; }

  box.classList.add("open");
  box.innerHTML = items.map(x => `<div class="taItem" data-val="${escapeHtml(x)}">#${escapeHtml(x)}</div>`).join("");

  Array.from(box.querySelectorAll(".taItem")).forEach(item => {
    item.addEventListener("click", () => {
      const val = item.getAttribute("data-val") || "";
      onPick?.(val);
    });
  });
}

function hideTypeahead(taId) {
  const box = $(taId);
  if (!box) return;
  box.classList.remove("open");
  box.innerHTML = "";
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

/* ------------------------- Age sliders -------------------------- */
function initAgeSliders() {
  // Registration
  const regFrom = $("regPrefAgeFrom");
  const regTo = $("regPrefAgeTo");
  const regFromVal = $("regPrefAgeFromVal");
  const regToVal = $("regPrefAgeToVal");

  if (regFrom && regTo) {
    const upd = () => {
      const f = Number(regFrom.value || 16);
      const t = Number(regTo.value || 99);
      if (regFromVal) regFromVal.textContent = String(f);
      if (regToVal) regToVal.textContent = String(t);
    };
    regFrom.addEventListener("input", upd);
    regTo.addEventListener("input", upd);
    upd();
  }

  // Settings
  const setFrom = $("setPrefAgeFrom");
  const setTo = $("setPrefAgeTo");
  const setFromVal = $("setPrefAgeFromVal");
  const setToVal = $("setPrefAgeToVal");

  if (setFrom && setTo) {
    const upd2 = () => {
      const f = Number(setFrom.value || 16);
      const t = Number(setTo.value || 99);
      if (setFromVal) setFromVal.textContent = String(f);
      if (setToVal) setToVal.textContent = String(t);
    };
    setFrom.addEventListener("input", upd2);
    setTo.addEventListener("input", upd2);
    upd2();
  }
}

/* ------------------------- Char counters -------------------------- */
function initCharCounters() {
  // Setup bio
  const setupBio = $("setupBio");
  if (setupBio) {
    setupBio.addEventListener("input", () => safeSetText("bioCount", String(setupBio.value.length)));
    safeSetText("bioCount", String(setupBio.value.length));
  }

  // Settings bio
  const setBio = $("setBio");
  if (setBio) {
    setBio.addEventListener("input", () => safeSetText("setBioCount", String(setBio.value.length)));
    safeSetText("setBioCount", String(setBio.value.length));
  }

  // Partner about
  const regOrgAbout = $("regOrgAbout");
  if (regOrgAbout) {
    regOrgAbout.addEventListener("input", () => safeSetText("regOrgAboutCount", String(regOrgAbout.value.length)));
    safeSetText("regOrgAboutCount", String(regOrgAbout.value.length));
  }
  const setOrgAbout = $("setOrgAbout");
  if (setOrgAbout) {
    setOrgAbout.addEventListener("input", () => safeSetText("setOrgAboutCount", String(setOrgAbout.value.length)));
    safeSetText("setOrgAboutCount", String(setOrgAbout.value.length));
  }
}

/* ------------------------- Geolocation (punkt 12) -------------------------- */
function initGeolocation() {
  // REQUIRED: bind by id="btnUseLocation" without inline onclick
  const btn = $("btnUseLocation");
  if (!btn) return;

  btn.addEventListener("click", useCurrentLocationForCity);
}

// Global function name as requested (punkt 12)
function useCurrentLocationForCity() {
  if (!navigator.geolocation) {
    toast("Geolokalizacja niedostępna w tej przeglądarce");
    return;
  }

  toast("Pobieram lokalizację…");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;

      // Save to hidden fields (backend-ready)
      const latEl = $("regGeoLat");
      const lngEl = $("regGeoLng");
      if (latEl) latEl.value = String(lat);
      if (lngEl) lngEl.value = String(lng);

      App.user.geo.lat = String(lat);
      App.user.geo.lng = String(lng);

      // Demo: we won't reverse-geocode (backend/API later)
      // For now: set city to placeholder if empty
      const city = $("regCity");
      if (city && !city.value.trim() && App.role === "user") {
        city.value = "Warszawa";
      }

      toast("Lokalizacja zapisana (demo)");
    },
    () => toast("Nie udało się pobrać lokalizacji (brak zgody?)"),
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 120000 }
  );
}

/* ------------------------- Tabbar + Active states -------------------------- */
function updateTabbars() {
  const userBar = $("tabbarUser");
  const partnerBar = $("tabbarPartner");

  if (!App.isLoggedIn) {
    hide(userBar);
    hide(partnerBar);
    return;
  }

  // Show only relevant bar
  if (App.role === "user") {
    show(userBar);
    hide(partnerBar);
  } else {
    hide(userBar);
    show(partnerBar);
  }

  // Active tab highlight based on current view
  setActiveTabs();
}

function setActiveTabs() {
  // clear
  document.querySelectorAll(".tabbar button").forEach(b => b.classList.remove("active", "on"));

  const v = App.currentView;

  // User tabs
  if (App.role === "user") {
    if (v.startsWith("S4")) $("tabNearby")?.classList.add("active");
    else if (v.startsWith("S6")) $("tabChats")?.classList.add("active");
    else if (v.startsWith("S7")) $("tabEvents")?.classList.add("active");
    else if (v.startsWith("S8")) $("tabGroups")?.classList.add("active");
    else if (v.startsWith("S10")) $("tabSettingsUser")?.classList.add("active");
  } else {
    // Partner tabs
    if (v === "S9_PARTNER") $("ptabDash")?.classList.add("active");
    else if (v === "S9_PARTNER_CREATE") $("ptabCreate")?.classList.add("active");
    else if (v === "S9_PARTNER_EVENTS") $("ptabMyEvents")?.classList.add("active");
    else if (v === "S9_PARTNER_MESSAGES") $("ptabMsgs")?.classList.add("active");
    else if (v.startsWith("S10")) $("ptabSettings")?.classList.add("active");
  }
}

/* ------------------------- Helpers: matching interests -------------------------- */
function commonInterests(person) {
  const a = (App.user.interests || []).map(x => x.toLowerCase());
  const b = (person.interests || []).map(x => x.toLowerCase());
  return a.filter(x => b.includes(x));
}

function sharedScore(person) {
  const common = commonInterests(person).length;
  const base = Math.max(1, App.user.interests.length);
  return Math.min(99, Math.round((common / base) * 100));
}

function suggestPeopleByInterest(tag) {
  const t = tag.toLowerCase();
  return App.people.filter(p => (p.interests || []).map(x => x.toLowerCase()).includes(t));
}

function priceLabel(ev) {
  if (ev.paidMode === "paid_fixed") return `${ev.price} zł`;
  if (ev.paidMode === "paid_range") return `${ev.priceFrom}–${ev.priceTo} zł`;
  return "0 zł";
}

function mapApiPersonToViewModel(p) {
  return {
    id: String(p.user_id),
    nick: p.nick || "Uzytkownik",
    city: p.miasto || "",
    age: p.age_min || p.age_max || 0,
    emoji: "🙂",
    interests: Array.isArray(p.zainteresowania) ? p.zainteresowania : [],
    bio: p.bio || "",
    avatarUrl: p.avatar_url || "",
  };
}

function mapApiGroupToViewModel(g) {
  return {
    id: String(g.id),
    title: g.title || "Grupa",
    interestTag: g.interest_tag || "",
    members: Number(g.members_count || 0),
    desc: g.description || "",
  };
}

function mapApiEventToViewModel(e) {
  const start = e?.start_at ? new Date(e.start_at) : null;
  const when =
    start && !Number.isNaN(start.getTime())
      ? start.toLocaleString("pl-PL", {
          day: "2-digit",
          month: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        })
      : "Termin wkrótce";

  return {
    id: String(e.id),
    title: e.title || "Wydarzenie",
    city: e.city || "",
    when: when,
    where: e.city || "",
    interest: "wydarzenie",
    desc: e.description || "",
    paidMode: e.pricing_type || "free",
    price: typeof e.price_fixed === "number" ? Math.round(e.price_fixed / 100) : null,
    priceFrom: typeof e.price_min === "number" ? Math.round(e.price_min / 100) : null,
    priceTo: typeof e.price_max === "number" ? Math.round(e.price_max / 100) : null,
    ticketLink: e.payment_link || "#",
    saved: false,
    interested: false,
    organizer: { id: String(e.partner_user_id || ""), name: "Organizator" },
  };
}


async function loadNearbyPeople() {
  try {
    const data = await apiFetch("/users/nearby?limit=20");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    App.people = items.map(mapApiPersonToViewModel);
    return true;
  } catch (err) {
    console.error("loadNearbyPeople failed", err);
    return false;
  }
}

async function loadEvents() {
  try {
    const data = await apiFetch("/events?limit=20");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    App.events = items.map(mapApiEventToViewModel);
    return true;
  } catch (err) {
    console.error("loadEvents failed", err);
    return false;
  }
}

async function loadGroups() {
  try {
    const data = await apiFetch("/groups?limit=20");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    App.groups = items.map(mapApiGroupToViewModel);
    return true;
  } catch (err) {
    console.error("loadGroups failed", err);
    return false;
  }
}

/* ------------------------- Render All -------------------------- */
function renderAll() {
  // Keep role labels consistent
  safeSetText("roleLabelLogin", App.role === "user" ? "Towarzysz" : "Organizator");
  safeSetText("roleLabelRegister", App.role === "user" ? "Towarzysz" : "Organizator");

  // Plan pills
  safeSetText("planPillSetup", App.user.plan.toUpperCase());
  safeSetText("partnerPlanPill", App.partner.plan.toUpperCase());

  // Partner plan line in dashboard
  const planLine = $("partnerPlanLine");
  if (planLine) {
    planLine.textContent = `${App.partner.company} • ${App.partner.plan.toUpperCase()}`;
  }

  // Setup avatar
  const userAvatar = $("userAvatar");
  if (userAvatar) userAvatar.textContent = App.user.avatarEmoji || "🙂";

  // Fill settings inputs moved out of renderAll to avoid overwriting unsaved form edits

  // Settings range values
  if ($("setPrefAgeFrom")) $("setPrefAgeFrom").value = String(App.user.prefAgeFrom);
  if ($("setPrefAgeTo")) $("setPrefAgeTo").value = String(App.user.prefAgeTo);
  safeSetText("setPrefAgeFromVal", String(App.user.prefAgeFrom));
  safeSetText("setPrefAgeToVal", String(App.user.prefAgeTo));

  // Partner settings
  if ($("setOrgCompany")) $("setOrgCompany").value = App.partner.company || "";
  if ($("setOrgCategory")) $("setOrgCategory").value = App.partner.category || "inne";
  if ($("setOrgCity")) $("setOrgCity").value = App.partner.city || "Warszawa";
  if ($("setOrgAbout")) $("setOrgAbout").value = App.partner.about || "";

  // Interest chips in visible sections
  renderInterestChips("interestChips");
  renderInterestChips("setInterestChips");
  renderInterestChips("regInterestChips");

  // Lists
  if (App.currentView === "S4_NEARBY") renderNearby();
  if (App.currentView === "S7_EVENTS") renderEventsList();
  if (App.currentView === "S8_GROUPS") renderGroups();
  if (App.currentView === "S6_CHATS_LIST") renderChatList();
  if (App.currentView === "S6B_CHAT_THREAD") renderChatThread();
  if (App.currentView === "S9_PARTNER_EVENTS") renderPartnerEvents();
  if (App.currentView === "S9_PARTNER_MESSAGES") renderPartnerMsgList();
  if (App.currentView === "S12_NOTIFICATIONS") renderNotifications();

  // tabbar active
  updateTabbars();
}

/* ------------------------- Search bindings -------------------------- */
function initSearchBindings() {
  $("nearbyPeopleSearch")?.addEventListener("input", renderNearby);
  $("eventsSearch")?.addEventListener("input", renderEventsList);
  $("groupSearch")?.addEventListener("input", renderGroups);
  $("chatSearch")?.addEventListener("input", renderChatList);
  $("partnerMsgSearch")?.addEventListener("input", renderPartnerMsgList);
}

/* ------------------------- App Init -------------------------- */
function init() {
  // Start view
  go("S0_WELCOME");

  // init hooks
  initGeolocation();
  initAgeSliders();
  initCharCounters();
  initInterestInputs();
  initSearchBindings();

  // Default role toggle UI
  selectRole(App.role);

  // Default plan selections (sync)
  setUserPlan(App.user.plan);
  setPartnerPlan(App.partner.plan);

  // Default events tab
  setEventsTab(App.eventsTab);

  // Default: logged out
  $("appRoot")?.classList.toggle("isLoggedIn", App.isLoggedIn);
  // initAuthMvp(); // martwy debug auth flow

  Promise.all([loadNearbyPeople(), loadEvents(), loadGroups()]).finally(() => {
    renderAll();
  });
}


function initAuthMvp() {

  console.log("AUTH MVP INIT");
  const elEmail = document.getElementById("login-email");
  const elPassword = document.getElementById("login-password");

  const btnLogin = document.getElementById("btn-login");
  const btnMe = document.getElementById("btn-me");
  const btnLogout = document.getElementById("btn-logout");

  const elStatus = document.getElementById("auth-status");

  function setStatus(msg, obj = null) {
    if (!elStatus) return;

    if (obj) {
      elStatus.textContent = msg + "\n" + JSON.stringify(obj, null, 2);
    } else {
      elStatus.textContent = msg;
    }
  }

  function getToken() {
    return localStorage.getItem("usly_token");
  }

  function setToken(token) {
    localStorage.setItem("usly_token", token);
  }

  function clearToken() {
    localStorage.removeItem("usly_token");
  }

  // Globalny auto-logout po 401/403 z apiFetch()
  window.addEventListener("auth:logout", (e) => {
      // api.js już czyści token, ale tu czyścimy też na wszelki wypadek
      try { clearToken(); } catch (_) {}

      const st = e && e.detail && e.detail.status ? e.detail.status : "?";
      setStatus("⛔ Wylogowano automatycznie (HTTP " + st + ") — zaloguj się ponownie");
    });

  // --- LOGIN ---

  if (btnLogin) {
    btnLogin.addEventListener("click", async () => {

      const email = elEmail?.value.trim();
      const password = elPassword?.value.trim();

      if (!email || !password) {
        setStatus("❌ Podaj email i hasło");
        return;
      }

      setStatus("⏳ Logowanie...");
      try {
        const data = await apiFetch("/auth/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        });
        
        if (!data?.success) {
          setStatus("❌ " + (data?.message || "Login error"), data);
          return;
        }
        const token = data.data.access_token;
        
        setToken(token);

        setStatus("✅ Zalogowano. Token zapisany.");

      } catch (err) {
        console.error(err);
        setStatus("❌ " + (err.userMessage || "Błąd logowania"));
      }

    });
  }

  // --- ME ---

  if (btnMe) {
      btnMe.addEventListener("click", async () => {

        const token = getToken();

        if (!token) {
          setStatus("❌ Brak tokena — zaloguj się");
          return;
        }

        setStatus("⏳ Pobieranie /auth/me...");

        try {
          const data = await apiFetch("/auth/me");
          setStatus("✅ /auth/me OK", data);

        } catch (err) {
          console.error(err);

          // 401/403 obsługuje apiFetch() -> emituje auth:logout i ustawia globalny komunikat
          if (err && (err.status === 401 || err.status === 403)) {
            return;
          }

          setStatus("❌ " + (err.userMessage || "Błąd"), err.data || err.message);
        }

      });
    }

    // --- LOGOUT ---

  if (btnLogout) {
    btnLogout.addEventListener("click", () => {
      clearToken();
      setStatus("👋 Wylogowano (token usunięty)");
    });
  }

}

// Run when DOM ready
document.addEventListener("DOMContentLoaded", init);

// ===============================
// AUTH MVP
// ===============================


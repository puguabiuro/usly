/**
 * USLY - API helper (plain JS, bez bundlera)
 * Cel: jedno miejsce do fetch + obsługa 401/403 + spójne błędy
 *
 * - Jeśli backend zwróci 401/403 -> czyścimy token i emitujemy event "auth:logout"
 * - Jeśli response nie-OK -> rzucamy błąd z .status i .data
 */

(function () {
  const TOKEN_KEY = "usly_token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  function emitLogout(status, data) {
    window.dispatchEvent(
      new CustomEvent("auth:logout", { detail: { status, data } })
    );
  }

  async function readJsonSafe(res) {
    const text = await res.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch {
      return { message: text };
    }
  }

  async function apiFetch(path, options = {}) {
    if (typeof window.API_BASE_URL !== "string" || !window.API_BASE_URL) {
      throw new Error("API_BASE_URL is not set");
    }

    const headers = new Headers(options.headers || {});
    if (!headers.has("Accept")) headers.set("Accept", "application/json");
    if (!headers.has("Accept-Language")) {
      headers.set("Accept-Language", navigator.language || "pl");
    }

    const token = getToken();
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const url = `${window.API_BASE_URL}${path}`;
    let res;
    try {
      res = await fetch(url, { ...options, headers });
    } catch (e) {
      const err = new Error("Network error");
      err.status = 0;
      err.data = null;
      err.userMessage = humanizeError(0, null);
      throw err;
    }
    if (res.status === 401 || res.status === 403) {
      const data = await readJsonSafe(res);
      clearToken();
      emitLogout(res.status, data);

      const err = new Error("Unauthorized");
      err.status = res.status;
      err.data = data;
        err.userMessage = humanizeError(res.status, data);
      throw err;
    }

    if (!res.ok) {
      const data = await readJsonSafe(res);
      const msg =
        (data && (data.message || data.detail)) ||
        res.statusText ||
        "Request failed";
      const err = new Error(msg);
      err.status = res.status;
      err.data = data;
      err.userMessage = humanizeError(res.status, data);
      throw err;
    }

    if (res.status === 204) return null;
    return await res.json();
  }
  function getLang() {
    const raw = (navigator.language || "pl").toLowerCase();
    if (raw.startsWith("pl")) return "pl";
    return "en";
  }

  const MESSAGES = {
    pl: {
    INVALID_TOKEN: "Twoja sesja wygasła. Zaloguj się ponownie.",
    INVALID_CREDENTIALS: "Nieprawidłowy email lub hasło.",
      UNAUTHORIZED: "Brak dostępu. Zaloguj się ponownie.",
      NETWORK_ERROR: "Błąd sieci lub backend jest offline.",
      UNKNOWN_ERROR: "Coś poszło nie tak. Spróbuj ponownie.",
    },
    en: {
    INVALID_TOKEN: "Your session has expired. Please log in again.",
    INVALID_CREDENTIALS: "Invalid email or password.",
      UNAUTHORIZED: "Unauthorized. Please log in again.",
      NETWORK_ERROR: "Network error or backend is offline.",
      UNKNOWN_ERROR: "Something went wrong. Please try again.",
    },
  };

  function humanizeError(status, data) {
    const lang = getLang();
    const dict = MESSAGES[lang] || MESSAGES.en;

    if (status === 0) return dict.NETWORK_ERROR;

    const code = (data && (data.error_code || data.code || (data.error && data.error.code) || data.detail)) || null;
    if (code && dict[code]) return dict[code];

    if ((status === 401 || status === 403) && dict.UNAUTHORIZED) {
      return dict.UNAUTHORIZED;
    }

    const msg = data && (data.message || data.detail);
    if (typeof msg === "string" && msg.trim()) return msg;

    return dict.UNKNOWN_ERROR;
  }

  window.apiFetch = apiFetch;
})();
